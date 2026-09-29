import os
import sys
import threading
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.controllers import auth_controller, contas_controller, interno_controller, transferencias_controller
from app.models.conta import ContaStore
from app.services.event_log import RegistroEventos
from app.services.handlers import aplicar_credito, processar_alerta, processar_confirmacao
from app.services.mensageria import Consumidor, Publicador
from app.services.relogio_vetorial import RelogioVetorial


def criar_app() -> FastAPI:
    id_agencia = int(os.environ.get("AGENCIA_ID", "0"))
    agencia_cfg = next((a for a in config.AGENCIAS if a["id"] == id_agencia), None)
    if agencia_cfg is None:
        print(f"Agência {id_agencia} não configurada em config.py")
        sys.exit(1)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Publicador: uma conexao dedicada, reaproveitada por todas as
        # rotas que publicam (transferir, saldo baixo, confirmacoes).
        app.state.publicador = Publicador()

        # Consumidores: cada um roda numa thread daemon propria, com sua
        # propria conexao com o broker (ver services/mensageria.py).
        consumidores = [
            Consumidor(
                config.fila_creditos(id_agencia),
                lambda msg: aplicar_credito(app, msg),
                nome=f"agencia-{id_agencia}-creditos",
            ),
            Consumidor(
                config.fila_confirmacoes(id_agencia),
                lambda msg: processar_confirmacao(app, msg),
                nome=f"agencia-{id_agencia}-confirmacoes",
            ),
            Consumidor(
                config.fila_alertas(id_agencia),
                lambda msg: processar_alerta(app, msg),
                nome=f"agencia-{id_agencia}-alertas",
            ),
        ]
        for consumidor in consumidores:
            consumidor.iniciar()
        app.state.consumidores = consumidores

        yield

        for consumidor in consumidores:
            consumidor.parar()
        app.state.publicador.fechar()

    app = FastAPI(title=f"ICEIBank - Agência {id_agencia}", lifespan=lifespan)

    # Libera o frontend (rodando em outra origem, ex. localhost:5173 do Vite)
    # a chamar esta API. Sem credenciais/cookies (usa Bearer token no header),
    # entao allow_origins="*" nao traz risco de CSRF via cookie.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.id_agencia = id_agencia
    app.state.relogio = RelogioVetorial(id_agencia, config.NUMERO_AGENCIAS)
    app.state.registro = RegistroEventos(f"agencia-{id_agencia}", id_agencia)
    app.state.contas = ContaStore()

    # Estado em memoria introduzido no Sprint 2:
    # - lock: protege contas/relogio/transferencias contra a corrida entre
    #   as requisicoes HTTP (rodando em threads do threadpool do uvicorn) e
    #   as threads dos consumidores de mensageria, que tambem mutam conta.
    # - transferencias: status (PENDENTE/CONFIRMADA/FALHOU) de cada
    #   transferencia entre agencias publicada por ESTA agencia.
    # - creditos_aplicados: dedupe de credito remoto (mensagens podem ser
    #   reentregues pelo broker se o ack se perder).
    # - notificacoes: alertas de saldo baixo ja consumidos, por conta
    #   (funcionalidade adicional).
    app.state.lock = threading.RLock()
    app.state.transferencias = {}
    app.state.creditos_aplicados = set()
    app.state.notificacoes = {}

    app.include_router(auth_controller.router)
    app.include_router(contas_controller.router)
    app.include_router(transferencias_controller.router)
    app.include_router(interno_controller.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})

    return app


app = criar_app()


if __name__ == "__main__":
    agencia_cfg = next(a for a in config.AGENCIAS if a["id"] == app.state.id_agencia)
    porta = urlparse(agencia_cfg["url"]).port
    print(f"[Agência {app.state.id_agencia}] ouvindo na porta {porta}")
    uvicorn.run(app, host="0.0.0.0", port=porta)

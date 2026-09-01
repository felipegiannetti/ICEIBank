import os
import sys
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app import config
from app.controllers import contas_controller
from app.models.conta import ContaStore
from app.services.event_log import RegistroEventos
from app.services.lamport_clock import RelogioLamport


def criar_app() -> FastAPI:
    id_agencia = int(os.environ.get("AGENCIA_ID", "0"))
    agencia_cfg = next((a for a in config.AGENCIAS if a["id"] == id_agencia), None)
    if agencia_cfg is None:
        print(f"Agência {id_agencia} não configurada em config.py")
        sys.exit(1)

    app = FastAPI(title=f"ICEIBank - Agência {id_agencia}")
    app.state.id_agencia = id_agencia
    app.state.relogio = RelogioLamport()
    app.state.registro = RegistroEventos(f"agencia-{id_agencia}")
    app.state.contas = ContaStore()

    app.include_router(contas_controller.router)

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

import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.controllers import contas_controller
from app.models.conta import Conta, ContaStore
from app.security import criar_token, hash_senha
from app.services.event_log import RegistroEventos
from app.services.relogio_vetorial import RelogioVetorial


def _criar_app_teste(pasta_dados: Path) -> FastAPI:
    """App minimalista so com o router de contas - sem lifespan de
    RabbitMQ/Bully, para testar /contas/{id}/sincronizar isoladamente (ver
    plano da Sprint 3: testes novos nao devem exigir RabbitMQ no ar)."""
    app = FastAPI()
    app.state.id_agencia = 0
    app.state.relogio = RelogioVetorial(0, 3)
    with patch("app.services.event_log.PASTA_DADOS", pasta_dados):
        app.state.registro = RegistroEventos("teste-sincronizacao", 0)
    app.state.contas = ContaStore()
    app.state.lock = threading.RLock()
    app.include_router(contas_controller.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})

    return app


class TestSincronizacaoOfflineFirst(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.app = _criar_app_teste(Path(self._tmpdir.name))
        self.client = TestClient(self.app)
        self.app.state.contas.criar(Conta(id=7, nome_aluno="Teste", senha_hash=hash_senha("senha123"), saldo=100.0))
        token, _ = criar_token(7)
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        self._tmpdir.cleanup()

    def _vetor_conhecido(self) -> list[int]:
        return self.client.get("/contas/7", headers=self.headers).json()["vetor_atual"]

    def test_vetor_igual_aplica_deposito(self):
        vetor = self._vetor_conhecido()
        resposta = self.client.post(
            "/contas/7/sincronizar",
            json={"tipo": "DEPOSITO", "valor": 50, "vetor_conhecido": vetor},
            headers=self.headers,
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["saldo"], 150.0)

    def test_vetor_igual_aplica_saque(self):
        vetor = self._vetor_conhecido()
        resposta = self.client.post(
            "/contas/7/sincronizar",
            json={"tipo": "SAQUE", "valor": 30, "vetor_conhecido": vetor},
            headers=self.headers,
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["saldo"], 70.0)

    def test_vetor_diferente_devolve_409_com_campos_esperados(self):
        vetor_antigo = self._vetor_conhecido()
        # Simula uma mudanca que aconteceu na agencia enquanto o app estava offline.
        self.client.post("/contas/7/depositar", json={"valor": 10}, headers=self.headers)

        resposta = self.client.post(
            "/contas/7/sincronizar",
            json={"tipo": "DEPOSITO", "valor": 50, "vetor_conhecido": vetor_antigo},
            headers=self.headers,
        )
        self.assertEqual(resposta.status_code, 409)
        corpo = resposta.json()
        for campo in ("erro", "vetor_conhecido", "vetor_atual", "conta_atual"):
            self.assertIn(campo, corpo)
        self.assertEqual(corpo["conta_atual"]["saldo"], 110.0)

    def test_sincronizar_de_novo_com_vetor_atual_funciona_apos_conflito(self):
        vetor_antigo = self._vetor_conhecido()
        self.client.post("/contas/7/depositar", json={"valor": 10}, headers=self.headers)

        conflito = self.client.post(
            "/contas/7/sincronizar",
            json={"tipo": "DEPOSITO", "valor": 50, "vetor_conhecido": vetor_antigo},
            headers=self.headers,
        )
        vetor_atual = conflito.json()["vetor_atual"]

        resposta = self.client.post(
            "/contas/7/sincronizar",
            json={"tipo": "DEPOSITO", "valor": 50, "vetor_conhecido": vetor_atual},
            headers=self.headers,
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["saldo"], 160.0)

    def test_saque_sem_saldo_devolve_400(self):
        vetor = self._vetor_conhecido()
        resposta = self.client.post(
            "/contas/7/sincronizar",
            json={"tipo": "SAQUE", "valor": 10_000, "vetor_conhecido": vetor},
            headers=self.headers,
        )
        self.assertEqual(resposta.status_code, 400)

    def test_tipo_invalido_e_rejeitado_pela_validacao(self):
        resposta = self.client.post(
            "/contas/7/sincronizar",
            json={"tipo": "TRANSFERENCIA", "valor": 10, "vetor_conhecido": [0, 0, 0]},
            headers=self.headers,
        )
        self.assertEqual(resposta.status_code, 422)


if __name__ == "__main__":
    unittest.main()

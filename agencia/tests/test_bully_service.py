import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.bully_service import ServicoBully
from app.services.relogio_vetorial import RelogioVetorial

AGENCIAS = [
    {"id": 0, "url": "http://localhost:4000"},
    {"id": 1, "url": "http://localhost:4001"},
    {"id": 2, "url": "http://localhost:4002"},
]


class RegistroFalso:
    """Substitui RegistroEventos nos testes - sem tocar o disco, so guarda
    os eventos numa lista para os testes inspecionarem."""

    def __init__(self):
        self.eventos = []

    def registrar(self, tipo, vetor, detalhes):
        evento = {"tipo": tipo, "vetor": vetor, "detalhes": detalhes}
        self.eventos.append(evento)
        return evento

    def tipos(self):
        return [e["tipo"] for e in self.eventos]


def criar_app_falso(id_agencia: int, numero_agencias: int = 3) -> SimpleNamespace:
    app = SimpleNamespace()
    app.state = SimpleNamespace()
    app.state.relogio = RelogioVetorial(id_agencia, numero_agencias)
    app.state.registro = RegistroFalso()
    return app


class TestServicoBully(unittest.TestCase):
    def test_torna_se_lider_quando_nenhuma_agencia_de_id_maior_responde(self):
        # Agencia 2 e a de maior ID - nao ha nenhuma acima dela para perguntar.
        app = criar_app_falso(id_agencia=2)
        bully = ServicoBully(app, id_agencia=2, agencias=AGENCIAS)

        with patch.object(bully, "_post", return_value=MagicMock(status_code=200)) as post_mock:
            bully.iniciar_eleicao()

        self.assertEqual(bully.lider_atual(), 2)
        self.assertFalse(bully.eleicao_em_andamento())
        self.assertIn("TORNOU_LIDER", app.state.registro.tipos())
        # Anuncia para as outras 2 agencias (0 e 1).
        self.assertEqual(post_mock.call_count, 2)

    def test_nao_se_torna_lider_quando_agencia_de_id_maior_responde(self):
        # Agencia 0: agencias 1 e 2 tem ID maior e respondem 200 -> uma delas
        # conduz a eleicao, agencia 0 so espera.
        app = criar_app_falso(id_agencia=0)
        bully = ServicoBully(app, id_agencia=0, agencias=AGENCIAS)

        with patch.object(bully, "_post", return_value=MagicMock(status_code=200)):
            bully.iniciar_eleicao()

        self.assertIsNone(bully.lider_atual())
        self.assertFalse(bully.eleicao_em_andamento())
        self.assertNotIn("TORNOU_LIDER", app.state.registro.tipos())

    def test_receber_eleicao_registra_evento_e_responde_com_id_e_vetor(self):
        app = criar_app_falso(id_agencia=1)
        bully = ServicoBully(app, id_agencia=1, agencias=AGENCIAS)

        with patch.object(bully, "_post", return_value=MagicMock(status_code=200)):
            resultado = bully.receber_eleicao(0, [1, 0, 0])

        self.assertEqual(resultado["id_agencia"], 1)
        self.assertIn("ELEICAO_RECEBIDA", app.state.registro.tipos())

    def test_receber_eleicao_de_id_menor_dispara_propria_eleicao(self):
        app = criar_app_falso(id_agencia=1)
        bully = ServicoBully(app, id_agencia=1, agencias=AGENCIAS)

        with patch.object(bully, "iniciar_eleicao") as mock_iniciar:
            bully.receber_eleicao(0, [1, 0, 0])
            # iniciar_eleicao roda numa thread separada - espera ela ser chamada.
            for _ in range(40):
                if mock_iniciar.called:
                    break
                time.sleep(0.025)

        self.assertTrue(mock_iniciar.called)

    def test_receber_coordenador_atualiza_lider_atual_e_zera_eleicao_em_andamento(self):
        app = criar_app_falso(id_agencia=0)
        bully = ServicoBully(app, id_agencia=0, agencias=AGENCIAS)
        bully._eleicao_em_andamento = True  # simula uma eleicao em andamento

        bully.receber_coordenador(2, [1, 1, 1])

        self.assertEqual(bully.lider_atual(), 2)
        self.assertFalse(bully.eleicao_em_andamento())
        self.assertIn("LIDER_ANUNCIADO", app.state.registro.tipos())

    def test_duas_chamadas_concorrentes_a_iniciar_eleicao_nao_duplicam(self):
        app = criar_app_falso(id_agencia=0)
        bully = ServicoBully(app, id_agencia=0, agencias=AGENCIAS)

        chamou_post = threading.Event()

        def _post_lento(url, caminho, corpo):
            chamou_post.set()
            time.sleep(0.2)
            return MagicMock(status_code=200)

        with patch.object(bully, "_post", side_effect=_post_lento):
            thread1 = threading.Thread(target=bully.iniciar_eleicao)
            thread1.start()
            self.assertTrue(chamou_post.wait(timeout=1))  # agora a 1a eleicao esta "em andamento"

            bully.iniciar_eleicao()  # 2a chamada concorrente - deve retornar na hora, sem registrar nada
            thread1.join(timeout=2)

        self.assertEqual(app.state.registro.tipos().count("ELEICAO_INICIADA"), 1)


if __name__ == "__main__":
    unittest.main()

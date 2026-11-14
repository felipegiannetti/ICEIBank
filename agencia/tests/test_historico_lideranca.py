import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.historico_lideranca import construir_historico


def _escrever_jsonl(caminho: Path, eventos: list[dict]) -> None:
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for evento in eventos:
            arquivo.write(json.dumps(evento) + "\n")


class TestHistoricoLideranca(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._pasta = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_filtra_so_os_tipos_de_evento_de_bully_e_ordena_por_hora(self):
        _escrever_jsonl(
            self._pasta / "eventos-agencia-0.jsonl",
            [
                {"agencia": "agencia-0", "tipo": "ELEICAO_INICIADA", "timestamp_vetorial": [1, 0, 0], "hora_parede": "2026-01-01T10:00:02Z", "detalhes": {"id_agencia": 0}},
                {"agencia": "agencia-0", "tipo": "CRIAR_CONTA", "timestamp_vetorial": [2, 0, 0], "hora_parede": "2026-01-01T10:00:03Z", "detalhes": {"id": 1}},
                {"agencia": "agencia-0", "tipo": "TORNOU_LIDER", "timestamp_vetorial": [3, 0, 0], "hora_parede": "2026-01-01T10:00:05Z", "detalhes": {"id_agencia": 0}},
            ],
        )
        _escrever_jsonl(
            self._pasta / "eventos-agencia-1.jsonl",
            [
                {"agencia": "agencia-1", "tipo": "ELEICAO_RECEBIDA", "timestamp_vetorial": [1, 1, 0], "hora_parede": "2026-01-01T10:00:01Z", "detalhes": {"de_agencia": 0}},
                {"agencia": "agencia-1", "tipo": "LIDER_ANUNCIADO", "timestamp_vetorial": [3, 2, 0], "hora_parede": "2026-01-01T10:00:06Z", "detalhes": {"lider": 0}},
            ],
        )

        with patch("app.services.historico_lideranca.PASTA_DADOS", self._pasta):
            historico = construir_historico()

        self.assertEqual(len(historico["eventos"]), 4)  # CRIAR_CONTA nao entra
        self.assertEqual([e["tipo"] for e in historico["eventos"]][0], "ELEICAO_RECEBIDA")  # a mais antiga primeiro
        self.assertEqual(len(historico["linha_do_tempo_lideres"]), 1)
        self.assertEqual(historico["linha_do_tempo_lideres"][0]["detalhes"]["id_agencia"], 0)

    def test_sem_eventos_devolve_listas_vazias(self):
        with patch("app.services.historico_lideranca.PASTA_DADOS", self._pasta):
            historico = construir_historico()

        self.assertEqual(historico["eventos"], [])
        self.assertEqual(historico["linha_do_tempo_lideres"], [])


if __name__ == "__main__":
    unittest.main()

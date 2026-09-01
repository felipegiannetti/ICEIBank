import json
from datetime import datetime, timezone
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent.parent / "data"


class RegistroEventos:
    def __init__(self, nome_agencia: str):
        self.nome_agencia = nome_agencia
        PASTA_DADOS.mkdir(parents=True, exist_ok=True)
        self.caminho_arquivo = PASTA_DADOS / f"eventos-{nome_agencia}.jsonl"

    def registrar(self, tipo: str, timestamp_lamport: int, detalhes: dict) -> dict:
        evento = {
            "agencia": self.nome_agencia,
            "tipo": tipo,
            "timestamp_lamport": timestamp_lamport,
            "hora_parede": datetime.now(timezone.utc).isoformat(),
            "detalhes": detalhes,
        }
        with open(self.caminho_arquivo, "a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(evento, ensure_ascii=False) + "\n")
        print(f"[Lamport {timestamp_lamport}] {tipo} {detalhes}")
        return evento

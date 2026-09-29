import json
from datetime import datetime, timezone
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent.parent / "data"


class RegistroEventos:
    def __init__(self, nome_agencia: str, id_agencia: int):
        self.nome_agencia = nome_agencia
        self.id_agencia = id_agencia
        PASTA_DADOS.mkdir(parents=True, exist_ok=True)
        self.caminho_arquivo = PASTA_DADOS / f"eventos-{nome_agencia}.jsonl"

    def registrar(self, tipo: str, timestamp_vetorial: list[int], detalhes: dict) -> dict:
        evento = {
            "agencia": self.nome_agencia,
            "tipo": tipo,
            "timestamp_vetorial": timestamp_vetorial,
            "hora_parede": datetime.now(timezone.utc).isoformat(),
            "detalhes": detalhes,
        }
        with open(self.caminho_arquivo, "a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(evento, ensure_ascii=False) + "\n")
        print(f"[Vetor {timestamp_vetorial}] {tipo} {detalhes}")
        return evento

    def listar_eventos(self, id_conta: int, tipo: str | None = None, limit: int | None = None) -> list[dict]:
        """Historico de uma conta - so precisa ler o proprio arquivo desta
        agencia, ja que, pelo particionamento, so a agencia dona de uma conta
        grava eventos referenciando ela (id, id_origem, id_destino ou
        id_conta, dependendo do tipo de evento)."""
        if not self.caminho_arquivo.exists():
            return []

        eventos = []
        for linha in self.caminho_arquivo.read_text(encoding="utf-8").strip().split("\n"):
            if not linha:
                continue
            evento = json.loads(linha)
            detalhes = evento.get("detalhes", {})
            ids_no_evento = {
                detalhes.get("id"),
                detalhes.get("id_origem"),
                detalhes.get("id_destino"),
                detalhes.get("id_conta"),
            }
            if id_conta not in ids_no_evento:
                continue
            if tipo is not None and evento["tipo"] != tipo:
                continue
            eventos.append(evento)

        # O vetor nao e totalmente ordenado (dois vetores podem ser
        # concorrentes), mas a componente da propria agencia
        # (timestamp_vetorial[id_agencia]) e sempre monotonicamente
        # crescente para eventos desta agencia - e por isso uma ordenacao
        # valida do mais recente para o mais antigo dentro do proprio log.
        eventos.sort(key=lambda e: e["timestamp_vetorial"][self.id_agencia], reverse=True)
        if limit is not None:
            eventos = eventos[:limit]
        return eventos

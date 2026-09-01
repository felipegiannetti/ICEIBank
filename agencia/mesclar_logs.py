import json
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent / "data"


def carregar_eventos() -> list[dict]:
    eventos = []
    for arquivo in sorted(PASTA_DADOS.glob("*.jsonl")):
        linhas = arquivo.read_text(encoding="utf-8").strip().split("\n")
        for linha in linhas:
            if linha:
                eventos.append(json.loads(linha))
    return eventos


def main():
    eventos = carregar_eventos()
    eventos.sort(key=lambda e: e["timestamp_lamport"])

    print("=== Linha do tempo unificada (ordenada por relogio de Lamport) ===")
    for evento in eventos:
        print(
            f"[Lamport {evento['timestamp_lamport']}] ({evento['hora_parede']}) "
            f"{evento['agencia']} - {evento['tipo']} {json.dumps(evento['detalhes'], ensure_ascii=False)}"
        )


if __name__ == "__main__":
    main()

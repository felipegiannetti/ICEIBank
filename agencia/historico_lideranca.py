"""Script standalone (Sprint 3, Parte C) - reconstroi a linha do tempo de
liderancas a partir dos logs .jsonl das 3 agencias.

Equivalente ao historico-lideranca.js do roteiro (codigo Node de
referencia); mesmo estilo dos outros scripts standalone do projeto
(mesclar_logs.py).

Uso (depois de ja ter reproduzido a eleicao inicial e o failover):

    python historico_lideranca.py
"""

from app.services.historico_lideranca import construir_historico


def imprimir_historico(historico: dict) -> None:
    print("=== Histórico de eventos de eleição ===")
    for evento in historico["eventos"]:
        print(
            f"({evento['hora_parede']}) [{evento['agencia']}] {evento['tipo']} "
            f"vetor={evento['timestamp_vetorial']} {evento['detalhes']}"
        )

    print("\n=== Linha do tempo de líderes ===")
    if not historico["linha_do_tempo_lideres"]:
        print("(nenhuma agência se tornou líder ainda - suba as 3 agências e espere a eleição inicial)")
    for evento in historico["linha_do_tempo_lideres"]:
        print(f"A partir de {evento['hora_parede']}: Agência {evento['detalhes']['id_agencia']} é a líder")


def main() -> None:
    imprimir_historico(construir_historico())


if __name__ == "__main__":
    main()

import json
import sys
from pathlib import Path

from app.services.relogio_vetorial import RelacaoVetores, comparar_vetores

PASTA_DADOS = Path(__file__).resolve().parent / "data"

# Tipos de evento que representam o lado "debito" e o lado "credito remoto"
# de uma mesma transferencia entre agencias - usados pela opcao --causais
# para casar os dois eventos pelo id_transferencia e confirmar que o par
# NUNCA aparece entre os concorrentes (tarefa 8.2, item 3).
TIPO_DEBITO_REMOTO = "TRANSFERENCIA_PUBLICADA"
TIPO_CREDITO_REMOTO = "TRANSFERENCIA_CREDITO_REMOTO"


def carregar_eventos() -> list[dict]:
    eventos = []
    for arquivo in sorted(PASTA_DADOS.glob("*.jsonl")):
        if arquivo.name == "auditoria.jsonl":
            continue
        linhas = arquivo.read_text(encoding="utf-8").strip().split("\n")
        for linha in linhas:
            if linha:
                eventos.append(json.loads(linha))
    return eventos


def imprimir_linha_do_tempo(eventos: list[dict]) -> None:
    print("=== Linha do tempo unificada (ordenada por hora de parede) ===")
    for evento in eventos:
        print(
            f"[Vetor {evento['timestamp_vetorial']}] ({evento['hora_parede']}) "
            f"{evento['agencia']} - {evento['tipo']} {json.dumps(evento['detalhes'], ensure_ascii=False)}"
        )


def imprimir_pares_concorrentes(eventos: list[dict]) -> None:
    print("\n=== Pares de eventos CONCORRENTES entre agencias diferentes ===")
    encontrou = False
    for i in range(len(eventos)):
        for j in range(i + 1, len(eventos)):
            e1, e2 = eventos[i], eventos[j]
            if e1["agencia"] == e2["agencia"]:
                continue
            relacao = comparar_vetores(e1["timestamp_vetorial"], e2["timestamp_vetorial"])
            if relacao == RelacaoVetores.CONCORRENTES:
                encontrou = True
                print(
                    f"[{e1['agencia']}] {e1['tipo']} ({e1['timestamp_vetorial']})"
                    f"  x  [{e2['agencia']}] {e2['tipo']} ({e2['timestamp_vetorial']})"
                )
    if not encontrou:
        print("(nenhum par concorrente encontrado nesta execucao - gere mais eventos em paralelo e rode de novo)")


def imprimir_pares_causais(eventos: list[dict]) -> None:
    """Casa debito<->credito remoto pelo id_transferencia e mostra a
    relacao entre eles - deve dar sempre ANTES (o debito, causa, tem que
    aparecer antes do credito, efeito), nunca CONCORRENTES."""
    por_id: dict[str, dict[str, dict]] = {}
    for evento in eventos:
        detalhes = evento.get("detalhes", {})
        id_transferencia = detalhes.get("id_transferencia")
        if not id_transferencia:
            continue
        if evento["tipo"] == TIPO_DEBITO_REMOTO:
            por_id.setdefault(id_transferencia, {})["debito"] = evento
        elif evento["tipo"] == TIPO_CREDITO_REMOTO:
            por_id.setdefault(id_transferencia, {})["credito"] = evento

    print("\n=== Pares causais (debito -> credito remoto da mesma transferencia) ===")
    encontrou = False
    for id_transferencia, par in por_id.items():
        if "debito" not in par or "credito" not in par:
            continue
        encontrou = True
        debito, credito = par["debito"], par["credito"]
        relacao = comparar_vetores(debito["timestamp_vetorial"], credito["timestamp_vetorial"])
        print(
            f"transferencia {id_transferencia}: "
            f"[{debito['agencia']}] DEBITO ({debito['timestamp_vetorial']})"
            f"  ->  [{credito['agencia']}] CREDITO_REMOTO ({credito['timestamp_vetorial']})"
            f"  =>  {relacao.value}"
        )
    if not encontrou:
        print("(nenhuma transferencia entre agencias encontrada - faca uma e rode de novo)")


def main() -> None:
    eventos = carregar_eventos()
    eventos.sort(key=lambda e: e["hora_parede"])

    imprimir_linha_do_tempo(eventos)
    imprimir_pares_concorrentes(eventos)

    if "--causais" in sys.argv:
        imprimir_pares_causais(eventos)


if __name__ == "__main__":
    main()

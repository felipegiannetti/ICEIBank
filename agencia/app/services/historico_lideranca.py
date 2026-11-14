"""Reconstroi a linha do tempo de liderancas (Sprint 3, Parte C) a partir
dos logs .jsonl das 3 agencias - mesmo padrao de leitura usado em
mesclar_logs.py, so que filtrando pelos tipos de evento do algoritmo de
Bully em vez de mesclar tudo."""

import json
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent.parent / "data"

TIPOS_EVENTOS_BULLY = {
    "ELEICAO_INICIADA",
    "ELEICAO_RECEBIDA",
    "TORNOU_LIDER",
    "LIDER_ANUNCIADO",
    "LIDER_NAO_RESPONDEU",
}


def carregar_eventos_bully() -> list[dict]:
    eventos = []
    for arquivo in sorted(PASTA_DADOS.glob("eventos-agencia-*.jsonl")):
        linhas = arquivo.read_text(encoding="utf-8").strip().split("\n")
        for linha in linhas:
            if not linha:
                continue
            evento = json.loads(linha)
            if evento["tipo"] in TIPOS_EVENTOS_BULLY:
                eventos.append(evento)
    return eventos


def construir_historico() -> dict:
    eventos = sorted(carregar_eventos_bully(), key=lambda e: e["hora_parede"])
    linha_do_tempo_lideres = [e for e in eventos if e["tipo"] == "TORNOU_LIDER"]
    return {"eventos": eventos, "linha_do_tempo_lideres": linha_do_tempo_lideres}

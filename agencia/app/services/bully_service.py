"""Algoritmo de Bully (GARCIA-MOLINA, H. Elections in a Distributed
Computing System. IEEE Transactions on Computers, 1982) - elege sempre a
agencia de maior id entre as que estao ativas.

O ServicoBully tem um lock PROPRIO (self._lock), separado de
app.state.lock: este servico nunca toca em contas/transferencias, e os
controllers de conta nunca tocam no estado do lider - os dois locks nunca
precisam ser aninhados, o que elimina o risco de deadlock entre eles.
"""

from __future__ import annotations

import threading
from typing import Optional

import httpx
from fastapi import FastAPI

from app import config


class ServicoBully:
    def __init__(self, app: FastAPI, id_agencia: int, agencias: list[dict]):
        self._app = app
        self.id_agencia = id_agencia
        self._agencias = agencias
        self._lock = threading.Lock()
        self._lider_atual: Optional[int] = None
        self._eleicao_em_andamento = False

    # --- estado (lido/escrito sempre sob self._lock) ---------------------

    def lider_atual(self) -> Optional[int]:
        with self._lock:
            return self._lider_atual

    def eleicao_em_andamento(self) -> bool:
        with self._lock:
            return self._eleicao_em_andamento

    # --- infra HTTP ---------------------------------------------------
    # Isolados em metodos proprios para que os testes (test_bully_service.py)
    # possam substitui-los (unittest.mock.patch.object) sem depender de rede
    # real nem de um servidor HTTP de verdade no ar.

    def _post(self, url: str, caminho: str, corpo: dict) -> httpx.Response:
        return httpx.post(f"{url}{caminho}", json=corpo, timeout=config.BULLY_TIMEOUT_HTTP)

    def _get(self, url: str, caminho: str) -> httpx.Response:
        return httpx.get(f"{url}{caminho}", timeout=config.BULLY_TIMEOUT_HTTP)

    def _outras_agencias(self) -> list[dict]:
        return [a for a in self._agencias if a["id"] != self.id_agencia]

    def _agencias_com_id_maior(self) -> list[dict]:
        return [a for a in self._agencias if a["id"] > self.id_agencia]

    # --- algoritmo de eleicao -------------------------------------------

    def iniciar_eleicao(self) -> None:
        with self._lock:
            if self._eleicao_em_andamento:
                return
            self._eleicao_em_andamento = True

        state = self._app.state
        vetor = state.relogio.evento_local()
        state.registro.registrar("ELEICAO_INICIADA", vetor, {"id_agencia": self.id_agencia})

        alguem_respondeu = False
        for agencia in self._agencias_com_id_maior():
            try:
                vetor_envio = state.relogio.ao_enviar()
                resposta = self._post(
                    agencia["url"], "/bully/eleicao", {"id_agencia": self.id_agencia, "vetor": vetor_envio}
                )
                if resposta.status_code == 200:
                    alguem_respondeu = True
            except httpx.HTTPError:
                # agencia fora do ar ou nao respondeu a tempo - ignora e segue
                continue

        if not alguem_respondeu:
            self._tornar_se_lider()
        else:
            with self._lock:
                self._eleicao_em_andamento = False
            # alguem de ID maior respondeu: e essa agencia quem vai concluir
            # a propria eleicao e anunciar o resultado via /bully/coordenador

    def _tornar_se_lider(self) -> None:
        state = self._app.state
        with self._lock:
            self._lider_atual = self.id_agencia
            self._eleicao_em_andamento = False

        vetor = state.relogio.evento_local()
        state.registro.registrar("TORNOU_LIDER", vetor, {"id_agencia": self.id_agencia})

        for agencia in self._outras_agencias():
            try:
                vetor_envio = state.relogio.ao_enviar()
                self._post(agencia["url"], "/bully/coordenador", {"id_agencia": self.id_agencia, "vetor": vetor_envio})
            except httpx.HTTPError:
                # agencia fora do ar - vai descobrir a lider no proximo
                # heartbeat (ou ao consultar /bully/lider dela mesma)
                continue

    def receber_eleicao(self, id_agencia_solicitante: int, vetor_recebido: list[int]) -> dict:
        state = self._app.state
        vetor = state.relogio.ao_receber(vetor_recebido)
        state.registro.registrar(
            "ELEICAO_RECEBIDA", vetor, {"de_agencia": id_agencia_solicitante, "minha_id": self.id_agencia}
        )
        # Quem recebeu tem ID maior que quem perguntou - tambem e candidata,
        # entao inicia a propria eleicao numa thread separada (o 200 desta
        # resposta HTTP ja serve de "OK" implicito para quem perguntou).
        threading.Thread(target=self.iniciar_eleicao, daemon=True).start()
        return {"id_agencia": self.id_agencia, "vetor": vetor}

    def receber_coordenador(self, id_agencia_lider: int, vetor_recebido: list[int]) -> None:
        state = self._app.state
        vetor = state.relogio.ao_receber(vetor_recebido)
        with self._lock:
            self._lider_atual = id_agencia_lider
            self._eleicao_em_andamento = False
        state.registro.registrar("LIDER_ANUNCIADO", vetor, {"lider": id_agencia_lider, "agencia": self.id_agencia})

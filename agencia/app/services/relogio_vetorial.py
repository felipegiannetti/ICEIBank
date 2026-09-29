import threading
from enum import Enum


class RelogioVetorial:
    """Relogio vetorial: um vetor de contadores, um por agencia.

    Resolve a limitacao do relogio de Lamport (Sprint 1) - com Lamport, dois
    eventos com timestamps diferentes podem ou nao ser causalmente
    relacionados, sem garantia. Com um vetor, dois timestamps permitem
    determinar com certeza se um "aconteceu antes" do outro ou se sao
    genuinamente concorrentes (ver comparar_vetores abaixo).
    """

    def __init__(self, id_agencia: int, numero_agencias: int):
        self.id_agencia = id_agencia
        self._vetor = [0] * numero_agencias
        self._lock = threading.Lock()

    def evento_local(self) -> list[int]:
        with self._lock:
            self._vetor[self.id_agencia] += 1
            return list(self._vetor)

    def ao_enviar(self) -> list[int]:
        with self._lock:
            self._vetor[self.id_agencia] += 1
            return list(self._vetor)

    def ao_receber(self, vetor_recebido: list[int]) -> list[int]:
        with self._lock:
            for i in range(len(self._vetor)):
                self._vetor[i] = max(self._vetor[i], vetor_recebido[i])
            self._vetor[self.id_agencia] += 1
            return list(self._vetor)


class RelacaoVetores(str, Enum):
    ANTES = "ANTES"
    DEPOIS = "DEPOIS"
    IGUAIS = "IGUAIS"
    CONCORRENTES = "CONCORRENTES"


def comparar_vetores(v1: list[int], v2: list[int]) -> RelacaoVetores:
    """Compara dois vetores posicao a posicao.

    - v1 <= v2 em toda posicao (e diferentes): o evento de v1 aconteceu ANTES.
    - v2 <= v1 em toda posicao (e diferentes): o evento de v1 aconteceu DEPOIS.
    - nem v1 <= v2 nem v2 <= v1: os eventos sao CONCORRENTES - nenhum
      influenciou o outro, sao independentes.
    """
    v1_menor_ou_igual = all(v1[i] <= v2[i] for i in range(len(v1)))
    v2_menor_ou_igual = all(v2[i] <= v1[i] for i in range(len(v1)))

    if v1_menor_ou_igual and v2_menor_ou_igual:
        return RelacaoVetores.IGUAIS
    if v1_menor_ou_igual:
        return RelacaoVetores.ANTES
    if v2_menor_ou_igual:
        return RelacaoVetores.DEPOIS
    return RelacaoVetores.CONCORRENTES

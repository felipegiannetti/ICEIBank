from dataclasses import dataclass
from typing import Optional


@dataclass
class Conta:
    id: int
    nome_aluno: str
    senha_hash: str
    saldo: float = 0.0


class ContaStore:
    """Armazenamento em memoria das contas desta agencia (sem banco de dados, por design do Sprint 1)."""

    def __init__(self):
        self._contas: dict[int, Conta] = {}

    def existe(self, id_conta: int) -> bool:
        return id_conta in self._contas

    def obter(self, id_conta: int) -> Optional[Conta]:
        return self._contas.get(id_conta)

    def criar(self, conta: Conta) -> None:
        self._contas[conta.id] = conta

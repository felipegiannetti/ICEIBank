from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from app.config import DEFAULT_LIMITE_DIARIO


class LimiteExcedidoError(Exception):
    def __init__(self, limite: float, usado: float, tentado: float):
        self.limite = limite
        self.usado = usado
        self.tentado = tentado
        super().__init__(
            f"Limite diário de saque/transferência excedido. "
            f"Limite: {limite}, já utilizado hoje: {usado}, tentado: {tentado}."
        )


@dataclass
class Conta:
    id: int
    nome_aluno: str
    senha_hash: str
    saldo: float = 0.0
    limite_diario: float = DEFAULT_LIMITE_DIARIO
    uso_diario: float = 0.0
    data_uso_diario: date = field(default_factory=date.today)

    def resetar_uso_diario_se_necessario(self) -> None:
        hoje = date.today()
        if self.data_uso_diario != hoje:
            self.uso_diario = 0.0
            self.data_uso_diario = hoje

    def consumir_limite_diario(self, valor: float) -> None:
        """Chamado no debito de um saque ou de uma transferencia (nao se
        aplica a deposito nem ao credito de uma transferencia recebida)."""
        self.resetar_uso_diario_se_necessario()
        if self.uso_diario + valor > self.limite_diario:
            raise LimiteExcedidoError(self.limite_diario, self.uso_diario, valor)
        self.uso_diario += valor

    def estornar_limite_diario(self, valor: float) -> None:
        """Desfaz o consumo do limite diario de uma operacao que precisou
        ser revertida (ex.: a publicacao da transferencia na mensageria
        falhou de forma confirmada). Nao mexe em saldo - isso e
        responsabilidade de quem chama."""
        self.uso_diario = max(0.0, self.uso_diario - valor)


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

from pydantic import BaseModel, ConfigDict, Field


class CriarContaRequest(BaseModel):
    id: int
    nome_aluno: str
    senha: str = Field(min_length=4)
    saldo_inicial: float = 0.0


class ContaResponse(BaseModel):
    """Formato de apresentacao (JSON) de uma conta - a "View" desta API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_aluno: str
    saldo: float
    vetor_atual: list[int] | None = None


class ValorRequest(BaseModel):
    valor: float = Field(gt=0)


class SincronizarRequest(BaseModel):
    """Sprint 3 - offline-first: o app manda a operacao pendente junto com o
    vetor que ele conhecia da conta na ultima leitura (vetor_conhecido)."""

    tipo: str = Field(pattern="^(DEPOSITO|SAQUE)$")
    valor: float = Field(gt=0)
    vetor_conhecido: list[int]


class EventoHistoricoResponse(BaseModel):
    tipo: str
    timestamp_vetorial: list[int]
    hora_parede: str
    detalhes: dict


class HistoricoResponse(BaseModel):
    conta_id: int
    eventos: list[EventoHistoricoResponse]


class LimiteResponse(BaseModel):
    id: int
    limite_diario: float
    uso_diario_atual: float
    restante_hoje: float


class AtualizarLimiteRequest(BaseModel):
    novo_limite: float = Field(gt=0)


class NotificacaoResponse(BaseModel):
    id_conta: int
    saldo_atual: float
    limite: float
    criado_em: str


class NotificacoesResponse(BaseModel):
    conta_id: int
    notificacoes: list[NotificacaoResponse]

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


class ValorRequest(BaseModel):
    valor: float = Field(gt=0)


class EventoHistoricoResponse(BaseModel):
    tipo: str
    timestamp_lamport: int
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

from pydantic import BaseModel, Field


class TransferenciaRequest(BaseModel):
    id_origem: int
    id_destino: int
    valor: float = Field(gt=0)


class TransferenciaResponse(BaseModel):
    mensagem: str


class CreditarRemotoRequest(BaseModel):
    valor: float = Field(gt=0)
    timestamp_vetorial: list[int]
    origem_agencia: int


class CreditoRemotoResponse(BaseModel):
    mensagem: str
    saldo_atual: float

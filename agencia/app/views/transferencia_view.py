from pydantic import BaseModel, Field


class TransferenciaRequest(BaseModel):
    id_origem: int
    id_destino: int
    valor: float = Field(gt=0)


class TransferenciaResponse(BaseModel):
    mensagem: str
    # None numa transferencia local (concluida de forma sincrona, na hora).
    # Preenchido numa transferencia entre agencias, que agora e assincrona -
    # a resposta so confirma que a mensagem foi publicada, nao que o
    # credito ja foi aplicado do outro lado.
    id_transferencia: str | None = None
    status: str


class StatusTransferenciaResponse(BaseModel):
    id_transferencia: str
    id_origem: int
    id_destino: int
    valor: float
    status: str
    motivo: str | None = None

from pydantic import BaseModel


class MensagemMortaResponse(BaseModel):
    id_transferencia: str
    id_conta: int
    valor: float
    origem_agencia: int
    vetor_envio: list[int]


class DlqResponse(BaseModel):
    fila: str
    mensagens: list[MensagemMortaResponse]


class ReprocessarDlqResponse(BaseModel):
    fila: str
    aplicadas: int

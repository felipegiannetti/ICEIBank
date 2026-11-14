from pydantic import BaseModel


class EleicaoRequest(BaseModel):
    id_agencia: int
    vetor: list[int]


class EleicaoResponse(BaseModel):
    id_agencia: int
    vetor: list[int]


class CoordenadorRequest(BaseModel):
    id_agencia: int
    vetor: list[int]


class LiderResponse(BaseModel):
    id_agencia: int
    lider_atual: int | None

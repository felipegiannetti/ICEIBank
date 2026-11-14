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


class ForcarEleicaoResponse(BaseModel):
    mensagem: str


class AgenciaAtivaResponse(BaseModel):
    id: int
    url: str
    ativa: bool


class AgenciasAtivasResponse(BaseModel):
    agencias: list[AgenciaAtivaResponse]


class EventoLiderancaResponse(BaseModel):
    agencia: str
    tipo: str
    timestamp_vetorial: list[int]
    hora_parede: str
    detalhes: dict


class HistoricoLiderancaResponse(BaseModel):
    eventos: list[EventoLiderancaResponse]
    linha_do_tempo_lideres: list[EventoLiderancaResponse]

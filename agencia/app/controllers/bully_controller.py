from fastapi import APIRouter, Request

from app.views.bully_view import CoordenadorRequest, EleicaoRequest, EleicaoResponse, LiderResponse

router = APIRouter(prefix="/bully", tags=["bully"])


@router.post("/eleicao", response_model=EleicaoResponse)
def receber_eleicao(body: EleicaoRequest, request: Request):
    # Rota propositalmente SEM autenticacao - e trafego agencia-a-agencia e
    # o roteiro usa isso como ponto de discussao (ver RESPOSTAS.md, Parte A,
    # pergunta sobre seguranca do endpoint de eleicao).
    bully = request.app.state.bully
    resultado = bully.receber_eleicao(body.id_agencia, body.vetor)
    return EleicaoResponse(**resultado)


@router.post("/coordenador")
def receber_coordenador(body: CoordenadorRequest, request: Request):
    bully = request.app.state.bully
    bully.receber_coordenador(body.id_agencia, body.vetor)
    return {"ok": True}


@router.get("/lider", response_model=LiderResponse)
def consultar_lider(request: Request):
    bully = request.app.state.bully
    return LiderResponse(id_agencia=bully.id_agencia, lider_atual=bully.lider_atual())

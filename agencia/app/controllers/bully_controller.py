import threading

from fastapi import APIRouter, Request

from app.services.historico_lideranca import construir_historico
from app.views.bully_view import (
    AgenciasAtivasResponse,
    CoordenadorRequest,
    EleicaoRequest,
    EleicaoResponse,
    ForcarEleicaoResponse,
    HistoricoLiderancaResponse,
    LiderResponse,
)

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


@router.post("/eleicao/forcar", response_model=ForcarEleicaoResponse)
def forcar_eleicao(request: Request):
    """Funcionalidade adicional: eleicao sob demanda. Dispara a eleicao numa
    thread separada e responde na hora - a eleicao em si pode levar ate
    alguns segundos (depende de quantas agencias nao respondem a tempo)."""
    bully = request.app.state.bully
    threading.Thread(target=bully.iniciar_eleicao, daemon=True).start()
    return ForcarEleicaoResponse(mensagem="Nova eleição disparada.")


@router.get("/agencias-ativas", response_model=AgenciasAtivasResponse)
def agencias_ativas(request: Request):
    """Funcionalidade adicional: quais das 3 agências estão respondendo
    agora, não só quem é a líder."""
    bully = request.app.state.bully
    return AgenciasAtivasResponse(agencias=bully.agencias_ativas())


@router.get("/historico", response_model=HistoricoLiderancaResponse)
def historico_lideranca(request: Request):
    """Funcionalidade adicional: histórico de líderes na tela. Reaproveita a
    mesma lógica de domínio usada pelo script historico_lideranca.py."""
    return HistoricoLiderancaResponse(**construir_historico())

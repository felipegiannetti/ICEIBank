from fastapi import APIRouter, Depends, Request

from app.config import fila_dlq
from app.security import verificar_segredo_interno
from app.services.handlers import aplicar_credito
from app.services.mensageria import espiar_fila, reprocessar_fila
from app.views.interno_view import DlqResponse, ReprocessarDlqResponse

router = APIRouter(prefix="/interno", tags=["interno"], dependencies=[Depends(verificar_segredo_interno)])


@router.get("/dlq", response_model=DlqResponse)
def ver_dlq(request: Request):
    """Funcionalidade adicional: dead-letter queue. Mostra (sem remover) as
    mensagens que falharam ao ser processadas - hoje, o unico motivo e
    'conta nao encontrada' (ver services/handlers.aplicar_credito), o
    cenario descrito na Parte C: a agencia de destino reiniciou antes de
    consumir a mensagem, entao a conta que deveria receber o credito nao
    existe mais quando a mensagem finalmente chega."""
    state = request.app.state
    nome_fila = fila_dlq(state.id_agencia)
    mensagens = espiar_fila(nome_fila)
    return DlqResponse(fila=nome_fila, mensagens=mensagens)


@router.post("/dlq/reprocessar", response_model=ReprocessarDlqResponse)
def reprocessar_dlq(request: Request):
    """Tenta reaplicar cada mensagem parada na DLQ desta agencia - util
    depois de recriar a conta que faltava (o cenario de resiliencia da
    Parte C). Mensagens que ainda falharem (ex.: a conta continua sem
    existir) voltam para a fila."""
    app = request.app
    state = app.state
    nome_fila = fila_dlq(state.id_agencia)
    aplicadas = reprocessar_fila(nome_fila, lambda mensagem: aplicar_credito(app, mensagem))
    return ReprocessarDlqResponse(fila=nome_fila, aplicadas=aplicadas)

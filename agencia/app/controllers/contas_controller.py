from fastapi import APIRouter, HTTPException, Request

from app.config import agencia_responsavel
from app.models.conta import Conta
from app.views.conta_view import ContaResponse, CriarContaRequest, ValorRequest

router = APIRouter(prefix="/contas", tags=["contas"])


@router.post("", response_model=ContaResponse, status_code=201)
def criar_conta(body: CriarContaRequest, request: Request):
    state = request.app.state
    if agencia_responsavel(body.id) != state.id_agencia:
        raise HTTPException(status_code=400, detail=f"Conta {body.id} não pertence a esta agência.")
    if state.contas.existe(body.id):
        raise HTTPException(status_code=409, detail="Conta já existe.")

    ts = state.relogio.evento_local()
    conta = Conta(id=body.id, nome_aluno=body.nome_aluno, saldo=body.saldo_inicial)
    state.contas.criar(conta)
    state.registro.registrar(
        "CRIAR_CONTA", ts, {"id": body.id, "nome_aluno": body.nome_aluno, "saldo_inicial": body.saldo_inicial}
    )
    return conta


@router.get("/{id_conta}", response_model=ContaResponse)
def consultar_saldo(id_conta: int, request: Request):
    state = request.app.state
    conta = state.contas.obter(id_conta)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")
    return conta


@router.post("/{id_conta}/depositar", response_model=ContaResponse)
def depositar(id_conta: int, body: ValorRequest, request: Request):
    state = request.app.state
    conta = state.contas.obter(id_conta)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")

    ts = state.relogio.evento_local()
    conta.saldo += body.valor
    state.registro.registrar("DEPOSITO", ts, {"id": id_conta, "valor": body.valor, "novo_saldo": conta.saldo})
    return conta


@router.post("/{id_conta}/sacar", response_model=ContaResponse)
def sacar(id_conta: int, body: ValorRequest, request: Request):
    state = request.app.state
    conta = state.contas.obter(id_conta)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")
    if conta.saldo < body.valor:
        raise HTTPException(status_code=400, detail="Saldo insuficiente.")

    ts = state.relogio.evento_local()
    conta.saldo -= body.valor
    state.registro.registrar("SAQUE", ts, {"id": id_conta, "valor": body.valor, "novo_saldo": conta.saldo})
    return conta

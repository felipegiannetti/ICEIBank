from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import agencia_responsavel
from app.models.conta import Conta, LimiteExcedidoError
from app.security import exigir_dono, hash_senha
from app.services.handlers import verificar_e_alertar_saldo_baixo
from app.views.conta_view import (
    AtualizarLimiteRequest,
    ContaResponse,
    CriarContaRequest,
    HistoricoResponse,
    LimiteResponse,
    NotificacoesResponse,
    ValorRequest,
)

router = APIRouter(prefix="/contas", tags=["contas"])


@router.post("", response_model=ContaResponse, status_code=201)
def criar_conta(body: CriarContaRequest, request: Request):
    # Rota publica (sem JWT): e o "cadastro" que define a senha usada depois
    # em /auth/login. Exigir token aqui criaria um paradoxo de bootstrap -
    # nao existe token antes de existir a primeira conta. Ver RESPOSTAS.md.
    state = request.app.state
    if agencia_responsavel(body.id) != state.id_agencia:
        raise HTTPException(status_code=400, detail=f"Conta {body.id} não pertence a esta agência.")

    with state.lock:
        if state.contas.existe(body.id):
            raise HTTPException(status_code=409, detail="Conta já existe.")

        ts = state.relogio.evento_local()
        conta = Conta(
            id=body.id, nome_aluno=body.nome_aluno, senha_hash=hash_senha(body.senha), saldo=body.saldo_inicial
        )
        state.contas.criar(conta)
        state.registro.registrar(
            "CRIAR_CONTA", ts, {"id": body.id, "nome_aluno": body.nome_aluno, "saldo_inicial": body.saldo_inicial}
        )
        return conta


@router.get("/{id_conta}", response_model=ContaResponse)
def consultar_saldo(id_conta: int, request: Request, _: int = Depends(exigir_dono)):
    state = request.app.state
    conta = state.contas.obter(id_conta)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")
    return conta


@router.post("/{id_conta}/depositar", response_model=ContaResponse)
def depositar(id_conta: int, body: ValorRequest, request: Request, _: int = Depends(exigir_dono)):
    state = request.app.state
    with state.lock:
        conta = state.contas.obter(id_conta)
        if not conta:
            raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")

        ts = state.relogio.evento_local()
        conta.saldo += body.valor
        state.registro.registrar("DEPOSITO", ts, {"id": id_conta, "valor": body.valor, "novo_saldo": conta.saldo})
        return conta


@router.post("/{id_conta}/sacar", response_model=ContaResponse)
def sacar(id_conta: int, body: ValorRequest, request: Request, _: int = Depends(exigir_dono)):
    state = request.app.state
    with state.lock:
        conta = state.contas.obter(id_conta)
        if not conta:
            raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")
        if conta.saldo < body.valor:
            raise HTTPException(status_code=400, detail="Saldo insuficiente.")

        try:
            conta.consumir_limite_diario(body.valor)
        except LimiteExcedidoError as erro:
            ts_falha = state.relogio.evento_local()
            state.registro.registrar(
                "SAQUE_REJEITADO_LIMITE",
                ts_falha,
                {
                    "id": id_conta,
                    "valor": body.valor,
                    "limite_diario": conta.limite_diario,
                    "uso_diario": conta.uso_diario,
                },
            )
            raise HTTPException(status_code=400, detail=str(erro))

        saldo_antes = conta.saldo
        ts = state.relogio.evento_local()
        conta.saldo -= body.valor
        state.registro.registrar("SAQUE", ts, {"id": id_conta, "valor": body.valor, "novo_saldo": conta.saldo})
        verificar_e_alertar_saldo_baixo(request.app, conta, saldo_antes)
        return conta


@router.get("/{id_conta}/historico", response_model=HistoricoResponse)
def historico(
    id_conta: int,
    request: Request,
    limit: int | None = None,
    tipo: str | None = None,
    _: int = Depends(exigir_dono),
):
    state = request.app.state
    if not state.contas.existe(id_conta):
        raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")

    eventos = state.registro.listar_eventos(id_conta, tipo=tipo, limit=limit)
    return HistoricoResponse(conta_id=id_conta, eventos=eventos)


@router.get("/{id_conta}/limite", response_model=LimiteResponse)
def consultar_limite(id_conta: int, request: Request, _: int = Depends(exigir_dono)):
    state = request.app.state
    conta = state.contas.obter(id_conta)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")

    conta.resetar_uso_diario_se_necessario()
    return LimiteResponse(
        id=conta.id,
        limite_diario=conta.limite_diario,
        uso_diario_atual=conta.uso_diario,
        restante_hoje=conta.limite_diario - conta.uso_diario,
    )


@router.put("/{id_conta}/limite", response_model=LimiteResponse)
def atualizar_limite(id_conta: int, body: AtualizarLimiteRequest, request: Request, _: int = Depends(exigir_dono)):
    state = request.app.state
    with state.lock:
        conta = state.contas.obter(id_conta)
        if not conta:
            raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")

        conta.limite_diario = body.novo_limite
        ts = state.relogio.evento_local()
        state.registro.registrar("LIMITE_ATUALIZADO", ts, {"id": id_conta, "novo_limite": body.novo_limite})

        conta.resetar_uso_diario_se_necessario()
        return LimiteResponse(
            id=conta.id,
            limite_diario=conta.limite_diario,
            uso_diario_atual=conta.uso_diario,
            restante_hoje=conta.limite_diario - conta.uso_diario,
        )


@router.get("/{id_conta}/notificacoes", response_model=NotificacoesResponse)
def notificacoes(id_conta: int, request: Request, _: int = Depends(exigir_dono)):
    """Funcionalidade adicional: notificacao de saldo baixo. As notificacoes
    chegam de forma assincrona (via mensageria - ver services/handlers.py,
    processar_alerta), entao esta rota so le o que ja foi consumido e
    guardado em memoria ate agora."""
    state = request.app.state
    with state.lock:
        lista = list(state.notificacoes.get(id_conta, []))
    return NotificacoesResponse(conta_id=id_conta, notificacoes=lista)

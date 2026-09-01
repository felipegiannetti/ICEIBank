import httpx
from fastapi import APIRouter, HTTPException, Request

from app.config import AGENCIAS, agencia_responsavel
from app.views.transferencia_view import (
    CreditarRemotoRequest,
    CreditoRemotoResponse,
    TransferenciaRequest,
    TransferenciaResponse,
)

router = APIRouter(tags=["transferencias"])


@router.post("/transferencias", response_model=TransferenciaResponse)
async def transferir(body: TransferenciaRequest, request: Request):
    state = request.app.state

    conta_origem = state.contas.obter(body.id_origem)
    if not conta_origem:
        raise HTTPException(status_code=404, detail="Conta de origem não encontrada nesta agência.")
    if conta_origem.saldo < body.valor:
        raise HTTPException(status_code=400, detail="Saldo insuficiente.")

    agencia_destino = agencia_responsavel(body.id_destino)

    # O debito e sempre local, pois esta agencia e a dona da conta de origem.
    ts_debito = state.relogio.evento_local()
    conta_origem.saldo -= body.valor
    state.registro.registrar(
        "TRANSFERENCIA_DEBITO",
        ts_debito,
        {"id_origem": body.id_origem, "id_destino": body.id_destino, "valor": body.valor},
    )

    if agencia_destino == state.id_agencia:
        # Caso simples: mesma agencia, credita direto - sem ao_enviar/ao_receber,
        # pois nao ha nenhuma mensagem cruzando a fronteira entre processos.
        conta_destino = state.contas.obter(body.id_destino)
        if not conta_destino:
            conta_origem.saldo += body.valor
            raise HTTPException(status_code=404, detail="Conta de destino não encontrada.")

        ts_credito = state.relogio.evento_local()
        conta_destino.saldo += body.valor
        state.registro.registrar(
            "TRANSFERENCIA_CREDITO",
            ts_credito,
            {"id_origem": body.id_origem, "id_destino": body.id_destino, "valor": body.valor},
        )
        return TransferenciaResponse(mensagem="Transferência concluída (mesma agência).")

    # Caso entre agencias: chama a agencia de destino diretamente via REST.
    ts_envio = state.relogio.ao_enviar()
    url_destino = next(a["url"] for a in AGENCIAS if a["id"] == agencia_destino)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resposta = await client.post(
                f"{url_destino}/contas/{body.id_destino}/creditar-remoto",
                json={
                    "valor": body.valor,
                    "timestamp_lamport": ts_envio,
                    "origem_agencia": state.id_agencia,
                },
            )
            resposta.raise_for_status()
        return TransferenciaResponse(mensagem="Transferência concluída (entre agências).")
    except httpx.HTTPError as erro:
        # LIMITACAO CONHECIDA: se esta chamada falhar, o debito ja aplicado acima
        # NAO e revertido - o dinheiro "desaparece" temporariamente. Resolver isso
        # de forma correta (garantir atomicidade mesmo sob falha) e o assunto do
        # Sprint 4, com uma transacao distribuida de verdade (2PC/Saga). Por
        # enquanto, so registramos a inconsistencia no log.
        ts_falha = state.relogio.evento_local()
        state.registro.registrar(
            "TRANSFERENCIA_FALHOU",
            ts_falha,
            {"id_origem": body.id_origem, "id_destino": body.id_destino, "valor": body.valor, "erro": str(erro)},
        )
        raise HTTPException(
            status_code=502,
            detail="Falha ao contatar agência de destino. Débito já aplicado - inconsistência conhecida (ver Sprint 4).",
        )


@router.post("/contas/{id_conta}/creditar-remoto", response_model=CreditoRemotoResponse)
async def creditar_remoto(id_conta: int, body: CreditarRemotoRequest, request: Request):
    state = request.app.state

    # Ao RECEBER uma mensagem de outra agencia, o relogio de Lamport e
    # atualizado com base no timestamp recebido - e a regra 3 do algoritmo.
    ts = state.relogio.ao_receber(body.timestamp_lamport)

    conta = state.contas.obter(id_conta)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada nesta agência.")

    conta.saldo += body.valor
    state.registro.registrar(
        "TRANSFERENCIA_CREDITO_REMOTO",
        ts,
        {"id_conta": id_conta, "valor": body.valor, "origem_agencia": body.origem_agencia},
    )
    return CreditoRemotoResponse(mensagem="Crédito remoto aplicado.", saldo_atual=conta.saldo)

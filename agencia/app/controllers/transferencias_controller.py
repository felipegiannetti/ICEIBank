import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import agencia_responsavel
from app.models.conta import LimiteExcedidoError
from app.security import get_id_conta_autenticada
from app.services.handlers import verificar_e_alertar_saldo_baixo
from app.services.mensageria import MensageriaIndisponivel
from app.views.transferencia_view import StatusTransferenciaResponse, TransferenciaRequest, TransferenciaResponse

router = APIRouter(tags=["transferencias"])


@router.post("/transferencias", response_model=TransferenciaResponse)
def transferir(
    body: TransferenciaRequest, request: Request, id_autenticado: int = Depends(get_id_conta_autenticada)
):
    if body.id_origem != id_autenticado:
        raise HTTPException(status_code=403, detail="Você só pode transferir a partir da sua própria conta.")

    state = request.app.state

    with state.lock:
        conta_origem = state.contas.obter(body.id_origem)
        if not conta_origem:
            raise HTTPException(status_code=404, detail="Conta de origem não encontrada nesta agência.")
        if conta_origem.saldo < body.valor:
            raise HTTPException(status_code=400, detail="Saldo insuficiente.")

        try:
            conta_origem.consumir_limite_diario(body.valor)
        except LimiteExcedidoError as erro:
            vetor_falha = state.relogio.evento_local()
            state.registro.registrar(
                "TRANSFERENCIA_REJEITADA_LIMITE",
                vetor_falha,
                {
                    "id_origem": body.id_origem,
                    "id_destino": body.id_destino,
                    "valor": body.valor,
                    "limite_diario": conta_origem.limite_diario,
                    "uso_diario": conta_origem.uso_diario,
                },
            )
            raise HTTPException(status_code=400, detail=str(erro))

        agencia_destino = agencia_responsavel(body.id_destino)

        # O debito e sempre local, pois esta agencia e a dona da conta de origem.
        saldo_antes_debito = conta_origem.saldo
        vetor_debito = state.relogio.evento_local()
        conta_origem.saldo -= body.valor
        state.registro.registrar(
            "TRANSFERENCIA_DEBITO",
            vetor_debito,
            {"id_origem": body.id_origem, "id_destino": body.id_destino, "valor": body.valor},
        )
        verificar_e_alertar_saldo_baixo(request.app, conta_origem, saldo_antes_debito)

        if agencia_destino == state.id_agencia:
            # Caso simples: mesma agencia, credita direto - sem ao_enviar/ao_receber,
            # pois nao ha nenhuma mensagem cruzando a fronteira entre processos.
            conta_destino = state.contas.obter(body.id_destino)
            if not conta_destino:
                conta_origem.saldo += body.valor
                conta_origem.estornar_limite_diario(body.valor)
                raise HTTPException(status_code=404, detail="Conta de destino não encontrada.")

            vetor_credito = state.relogio.evento_local()
            conta_destino.saldo += body.valor
            state.registro.registrar(
                "TRANSFERENCIA_CREDITO",
                vetor_credito,
                {"id_origem": body.id_origem, "id_destino": body.id_destino, "valor": body.valor},
            )
            return TransferenciaResponse(mensagem="Transferência concluída (mesma agência).", status="CONCLUIDA")

        # Caso entre agencias: em vez de chamar a outra agencia diretamente
        # (Sprint 1), publicamos um evento na exchange do RabbitMQ. A agencia
        # de destino consome quando estiver disponivel - mesmo que esteja
        # fora do ar agora, a mensagem fica retida na fila (durable) e e
        # entregue quando ela voltar.
        id_transferencia = str(uuid.uuid4())
        vetor_envio = state.relogio.ao_enviar()
        try:
            state.publicador.publicar(
                f"agencia.{agencia_destino}.creditar",
                {
                    "id_transferencia": id_transferencia,
                    "id_conta": body.id_destino,
                    "valor": body.valor,
                    "vetor_envio": vetor_envio,
                    "origem_agencia": state.id_agencia,
                },
            )
        except MensageriaIndisponivel as erro:
            # Diferente do Sprint 1 (onde uma chamada REST podia falhar por
            # timeout, deixando o resultado incerto), aqui a publicacao com
            # confirm_delivery so falha quando temos CERTEZA de que a
            # mensagem nao saiu - entao podemos estornar com seguranca o
            # debito e o consumo do limite diario, sem risco de duplicar
            # dinheiro se a mensagem tiver sido entregue de qualquer jeito.
            conta_origem.saldo += body.valor
            conta_origem.estornar_limite_diario(body.valor)
            vetor_falha = state.relogio.evento_local()
            state.registro.registrar(
                "TRANSFERENCIA_FALHOU",
                vetor_falha,
                {
                    "id_origem": body.id_origem,
                    "id_destino": body.id_destino,
                    "valor": body.valor,
                    "erro": str(erro),
                },
            )
            raise HTTPException(
                status_code=503,
                detail="Serviço de mensageria indisponível. A transferência não foi publicada e o débito foi estornado.",
            )

        state.registro.registrar(
            "TRANSFERENCIA_PUBLICADA",
            vetor_envio,
            {
                "id_transferencia": id_transferencia,
                "id_origem": body.id_origem,
                "id_destino": body.id_destino,
                "valor": body.valor,
            },
        )
        state.transferencias[id_transferencia] = {
            "id_origem": body.id_origem,
            "id_destino": body.id_destino,
            "valor": body.valor,
            "status": "PENDENTE",
            "motivo": None,
        }
        return TransferenciaResponse(
            mensagem="Transferência publicada para a agência de destino (entrega assíncrona).",
            id_transferencia=id_transferencia,
            status="PENDENTE",
        )


@router.get("/transferencias/{id_transferencia}", response_model=StatusTransferenciaResponse)
def consultar_status_transferencia(
    id_transferencia: str, request: Request, id_autenticado: int = Depends(get_id_conta_autenticada)
):
    state = request.app.state
    with state.lock:
        transferencia = state.transferencias.get(id_transferencia)
        if not transferencia:
            raise HTTPException(status_code=404, detail="Transferência não encontrada.")
        if transferencia["id_origem"] != id_autenticado:
            raise HTTPException(status_code=403, detail="Você não tem permissão para ver esta transferência.")
        return StatusTransferenciaResponse(id_transferencia=id_transferencia, **transferencia)

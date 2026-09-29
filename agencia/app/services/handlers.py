"""Handlers de dominio para as mensagens do RabbitMQ.

Ficam fora dos controllers porque sao chamados de tres lugares diferentes:
os consumidores em background (thread propria, ligados em main.py), o
endpoint de reprocessamento da dead-letter queue (extra: DLQ, mesma
mensagem, mesmo handler) e os proprios controllers HTTP (verificacao de
saldo baixo apos um debito).
"""

from datetime import datetime, timezone

from fastapi import FastAPI

from app import config
from app.services.mensageria import MensageriaIndisponivel


def publicar_confirmacao(app: FastAPI, id_agencia_origem: int, id_transferencia: str, sucesso: bool, motivo: str | None) -> None:
    state = app.state
    vetor_envio = state.relogio.ao_enviar()
    try:
        state.publicador.publicar(
            config.routing_key_confirmacao(id_agencia_origem),
            {
                "id_transferencia": id_transferencia,
                "sucesso": sucesso,
                "motivo": motivo,
                "vetor_envio": vetor_envio,
            },
        )
    except MensageriaIndisponivel as erro:
        # A confirmacao e best-effort: se o broker cair bem neste instante,
        # a origem so vai descobrir o resultado se/quando reprocessarmos ou
        # se ela consultar o extrato da agencia de destino manualmente.
        print(f"[mensageria] falha ao publicar confirmacao de {id_transferencia}: {erro}")


def aplicar_credito(app: FastAPI, mensagem: dict) -> bool:
    """Handler da fila de credito (agencia.N.creditar) - tambem reaproveitado
    pelo endpoint de reprocessamento da DLQ (extra: dead-letter queue), ja
    que a mensagem tem exatamente o mesmo formato."""
    state = app.state
    id_transferencia = mensagem["id_transferencia"]
    id_conta = mensagem["id_conta"]
    valor = mensagem["valor"]
    vetor_envio = mensagem["vetor_envio"]
    origem_agencia = mensagem["origem_agencia"]

    with state.lock:
        vetor = state.relogio.ao_receber(vetor_envio)

        if id_transferencia in state.creditos_aplicados:
            # Mensagem duplicada (ex.: reentrega apos a agencia cair antes
            # de confirmar o ack) - o credito ja foi aplicado, so reconfirma.
            publicar_confirmacao(app, origem_agencia, id_transferencia, True, "credito ja aplicado (duplicado)")
            return True

        conta = state.contas.obter(id_conta)
        if not conta:
            # Cenario da Parte C: a agencia reiniciou (contas em memoria) e a
            # conta que deveria receber o credito nao existe mais. Registra
            # a falha, confirma (sucesso=False) para a origem, e devolve
            # False - o Consumidor faz nack(requeue=False), que a topologia
            # (mensageria.declarar_topologia) redireciona para a DLQ.
            state.registro.registrar(
                "CREDITO_REMOTO_FALHOU",
                vetor,
                {
                    "id_transferencia": id_transferencia,
                    "id_conta": id_conta,
                    "valor": valor,
                    "origem_agencia": origem_agencia,
                    "motivo": "conta nao encontrada",
                },
            )
            publicar_confirmacao(app, origem_agencia, id_transferencia, False, "conta nao encontrada")
            return False

        conta.saldo += valor
        state.creditos_aplicados.add(id_transferencia)
        state.registro.registrar(
            "TRANSFERENCIA_CREDITO_REMOTO",
            vetor,
            {"id_transferencia": id_transferencia, "id_conta": id_conta, "valor": valor, "origem_agencia": origem_agencia},
        )
        publicar_confirmacao(app, origem_agencia, id_transferencia, True, None)
        return True


def processar_confirmacao(app: FastAPI, mensagem: dict) -> bool:
    """Handler da fila de confirmacao (agencia.N.confirmacao), consumida
    pela agencia de ORIGEM da transferencia."""
    state = app.state
    id_transferencia = mensagem["id_transferencia"]
    sucesso = mensagem["sucesso"]
    motivo = mensagem.get("motivo")
    vetor_envio = mensagem["vetor_envio"]

    with state.lock:
        vetor = state.relogio.ao_receber(vetor_envio)
        transferencia = state.transferencias.get(id_transferencia)
        if transferencia is not None:
            transferencia["status"] = "CONFIRMADA" if sucesso else "FALHOU"
            transferencia["motivo"] = motivo

        detalhes = {"id_transferencia": id_transferencia, "motivo": motivo}
        if transferencia is not None:
            # Inclui id_origem/id_destino para que este evento apareca no
            # extrato da conta de origem (listar_eventos correlaciona pelo
            # id da conta presente em "detalhes" - ver event_log.py).
            detalhes["id_origem"] = transferencia["id_origem"]
            detalhes["id_destino"] = transferencia["id_destino"]

        state.registro.registrar("TRANSFERENCIA_CONFIRMADA" if sucesso else "CREDITO_FALHOU", vetor, detalhes)
    return True


def processar_alerta(app: FastAPI, mensagem: dict) -> bool:
    """Handler da fila de alertas (alerta.saldo_baixo.N) - a propria
    agencia publica e consome o alerta dela mesma; o ponto de ter isso como
    mensagem (em vez de uma chamada direta) e permitir que qualquer outro
    consumidor (ex.: o auditor, extra de fila de auditoria) tambem veja o
    evento sem a agencia precisar saber que ele existe."""
    state = app.state
    with state.lock:
        state.notificacoes.setdefault(mensagem["id_conta"], []).append(mensagem)
    return True


def verificar_e_alertar_saldo_baixo(app: FastAPI, conta, saldo_antes: float) -> None:
    """Chamado depois de qualquer debito (saque, ou o lado de origem de uma
    transferencia). So publica no CRUZAMENTO da fronteira (estava >= limite,
    ficou < limite) - nao a cada operacao, para nao inundar a fila."""
    state = app.state
    if not (saldo_antes >= config.SALDO_BAIXO_LIMITE > conta.saldo):
        return

    vetor_envio = state.relogio.ao_enviar()
    mensagem = {
        "id_conta": conta.id,
        "saldo_atual": conta.saldo,
        "limite": config.SALDO_BAIXO_LIMITE,
        "vetor_envio": vetor_envio,
        "criado_em": datetime.now(timezone.utc).isoformat(),
    }
    try:
        state.publicador.publicar(config.routing_key_alerta(state.id_agencia), mensagem)
        state.registro.registrar(
            "ALERTA_SALDO_BAIXO_PUBLICADO", vetor_envio, {"id_conta": conta.id, "saldo_atual": conta.saldo}
        )
    except MensageriaIndisponivel as erro:
        print(f"[mensageria] falha ao publicar alerta de saldo baixo da conta {conta.id}: {erro}")

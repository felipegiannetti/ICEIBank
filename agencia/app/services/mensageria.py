"""Camada de mensageria (RabbitMQ/pika) - Publish/Subscribe entre agencias.

Topologia (ver README para o desenho completo):

    exchange topic "iceibank.eventos"
      agencia.N.creditar     -> fila-agencia-N               (credito remoto)
      agencia.N.confirmacao  -> fila-confirmacoes-agencia-N   (confirmacao de entrega)
      alerta.saldo_baixo.N   -> fila-alertas-agencia-N        (notificacao de saldo baixo)
    exchange topic "iceibank.dlx"
      agencia.N.morta        -> dlq-agencia-N                 (dead-letter)

Toda agencia declara essa topologia inteira (as 3 agencias, nao so a
propria) ao subir - a operacao e idempotente (declare e so garante que
existe, nao recria nada) e garante que uma mensagem publicada para uma
agencia que ainda nao subiu (ou que caiu) fica retida na fila em vez de
ser rejeitada por "ninguem para receber".
"""

import json
import threading
import time
from typing import Callable

import pika
from pika.exceptions import AMQPError

from app import config


class MensageriaIndisponivel(Exception):
    """Levantada quando uma publicacao nao pode ser confirmada - o broker
    esta fora do ar, ou a mensagem nao pode ser roteada para nenhuma fila."""


def _parametros_conexao() -> pika.URLParameters:
    if not config.RABBITMQ_URL:
        raise RuntimeError(
            "Defina a variavel de ambiente RABBITMQ_URL (ou crie agencia/.env "
            "a partir de agencia/.env.example) com a URL AMQP da sua instancia "
            "antes de iniciar a agencia."
        )
    parametros = pika.URLParameters(config.RABBITMQ_URL)
    parametros.heartbeat = 30
    parametros.blocked_connection_timeout = 10
    return parametros


def conectar() -> pika.BlockingConnection:
    return pika.BlockingConnection(_parametros_conexao())


def declarar_topologia(canal) -> None:
    canal.exchange_declare(exchange=config.EXCHANGE_EVENTOS, exchange_type="topic", durable=True)
    canal.exchange_declare(exchange=config.EXCHANGE_DLX, exchange_type="topic", durable=True)

    for id_agencia in range(config.NUMERO_AGENCIAS):
        fila_creditos = config.fila_creditos(id_agencia)
        canal.queue_declare(
            queue=fila_creditos,
            durable=True,
            arguments={
                # Mensagens rejeitadas com requeue=False (ex.: conta nao
                # encontrada - ver _aplicar_credito) caem aqui em vez de
                # serem descartadas.
                "x-dead-letter-exchange": config.EXCHANGE_DLX,
                "x-dead-letter-routing-key": config.routing_key_morta(id_agencia),
            },
        )
        canal.queue_bind(
            queue=fila_creditos, exchange=config.EXCHANGE_EVENTOS, routing_key=config.routing_key_credito(id_agencia)
        )

        canal.queue_declare(queue=config.fila_dlq(id_agencia), durable=True)
        canal.queue_bind(
            queue=config.fila_dlq(id_agencia), exchange=config.EXCHANGE_DLX, routing_key=config.routing_key_morta(id_agencia)
        )

        canal.queue_declare(queue=config.fila_confirmacoes(id_agencia), durable=True)
        canal.queue_bind(
            queue=config.fila_confirmacoes(id_agencia),
            exchange=config.EXCHANGE_EVENTOS,
            routing_key=config.routing_key_confirmacao(id_agencia),
        )

        canal.queue_declare(queue=config.fila_alertas(id_agencia), durable=True)
        canal.queue_bind(
            queue=config.fila_alertas(id_agencia),
            exchange=config.EXCHANGE_EVENTOS,
            routing_key=config.routing_key_alerta(id_agencia),
        )


def declarar_fila_auditoria(canal) -> str:
    """So o auditor.py chama isso - nao faz parte da topologia que as
    agencias declaram, e especifica da funcionalidade adicional de
    auditoria. routing_key "#" casa com qualquer coisa publicada na
    exchange (credito, confirmacao, alerta)."""
    declarar_topologia(canal)
    nome_fila = "fila-auditoria"
    canal.queue_declare(queue=nome_fila, durable=True)
    canal.queue_bind(queue=nome_fila, exchange=config.EXCHANGE_EVENTOS, routing_key="#")
    return nome_fila


class Publicador:
    """Conexao dedicada para publicar mensagens, com confirmacao de entrega
    (publisher confirms) e mandatory=True - se uma mensagem nao puder ser
    roteada para nenhuma fila, isso vira um erro explicito (UnroutableError)
    em vez de ser silenciosamente descartada."""

    def __init__(self):
        self._lock = threading.Lock()
        self._conexao: pika.BlockingConnection | None = None
        self._canal = None

    def _conectar(self) -> None:
        self._conexao = conectar()
        self._canal = self._conexao.channel()
        self._canal.confirm_delivery()
        declarar_topologia(self._canal)

    def _garantir_conexao(self) -> None:
        if self._conexao is None or not self._conexao.is_open:
            self._conectar()

    def publicar(self, routing_key: str, mensagem: dict) -> None:
        corpo = json.dumps(mensagem, ensure_ascii=False).encode("utf-8")
        with self._lock:
            for tentativa in (1, 2):
                try:
                    self._garantir_conexao()
                    self._canal.basic_publish(
                        exchange=config.EXCHANGE_EVENTOS,
                        routing_key=routing_key,
                        body=corpo,
                        properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
                        mandatory=True,
                    )
                    return
                except AMQPError as erro:
                    if tentativa == 2:
                        raise MensageriaIndisponivel(str(erro)) from erro
                    # Conexao pode ter caido - fecha e tenta reconectar uma vez.
                    try:
                        if self._conexao is not None:
                            self._conexao.close()
                    except Exception:
                        pass
                    self._conexao = None

    def fechar(self) -> None:
        with self._lock:
            if self._conexao is not None and self._conexao.is_open:
                try:
                    self._conexao.close()
                except Exception:
                    pass


class Consumidor:
    """Roda em uma thread daemon propria, com sua propria conexao (conexoes
    do pika/BlockingConnection nao sao thread-safe para compartilhar).
    Reconecta com um pequeno backoff se a conexao cair."""

    def __init__(self, fila: str, ao_receber: Callable[[dict], bool], nome: str | None = None):
        """ao_receber recebe o dict da mensagem e retorna True (ack) ou
        False (nack sem requeue - a mensagem vai para a dead-letter, se a
        fila tiver uma configurada; senao e descartada)."""
        self.fila = fila
        self.ao_receber = ao_receber
        self.nome = nome or f"consumidor-{fila}"
        self._thread: threading.Thread | None = None
        self._parar = threading.Event()
        self._conexao: pika.BlockingConnection | None = None
        self._canal = None

    def iniciar(self) -> None:
        self._thread = threading.Thread(target=self._rodar, name=self.nome, daemon=True)
        self._thread.start()

    def _rodar(self) -> None:
        while not self._parar.is_set():
            try:
                self._conexao = conectar()
                self._canal = self._conexao.channel()
                declarar_topologia(self._canal)
                self._canal.basic_qos(prefetch_count=1)

                def callback(canal, method, _properties, body):
                    try:
                        mensagem = json.loads(body.decode("utf-8"))
                        sucesso = bool(self.ao_receber(mensagem))
                    except Exception as erro:  # noqa: BLE001 - qualquer falha no handler não pode matar o consumidor
                        print(f"[{self.nome}] erro ao processar mensagem: {erro}")
                        sucesso = False
                    if sucesso:
                        canal.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        canal.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                self._canal.basic_consume(queue=self.fila, on_message_callback=callback)
                print(f"[{self.nome}] ouvindo a fila '{self.fila}'")
                self._canal.start_consuming()
            except Exception as erro:  # noqa: BLE001 - loop de reconexao, precisa sobreviver a qualquer excecao
                if self._parar.is_set():
                    break
                print(f"[{self.nome}] conexao perdida ({erro}); tentando de novo em 3s...")
                time.sleep(3)

    def parar(self) -> None:
        self._parar.set()
        conexao = self._conexao
        canal = self._canal
        if conexao is not None and conexao.is_open and canal is not None:
            try:
                conexao.add_callback_threadsafe(canal.stop_consuming)
            except Exception:
                pass


def espiar_fila(nome_fila: str, limite: int = 20) -> list[dict]:
    """Le ate `limite` mensagens de uma fila SEM removê-las - usado pelo
    endpoint de inspecao da DLQ.

    Como cada mensagem so e devolvida a fila (nack com requeue=True) DEPOIS
    de todas terem sido lidas, uma mesma mensagem nunca e "espiada" duas
    vezes numa mesma chamada (se devolvessemos uma a uma, a proxima leitura
    pegaria de volta a que acabou de ser recolocada, e o resultado seria a
    mesma mensagem repetida ate o limite)."""
    mensagens = []
    tags_pendentes = []
    with conectar() as conexao:
        canal = conexao.channel()
        # Descobre quantas mensagens existem de verdade, para nao dar mais
        # voltas do que o necessario na fila.
        declaracao = canal.queue_declare(queue=nome_fila, passive=True)
        total = min(limite, declaracao.method.message_count)

        for _ in range(total):
            method, _properties, body = canal.basic_get(queue=nome_fila, auto_ack=False)
            if method is None:
                break
            mensagens.append(json.loads(body.decode("utf-8")))
            tags_pendentes.append(method.delivery_tag)

        for tag in tags_pendentes:
            canal.basic_nack(delivery_tag=tag, requeue=True)
    return mensagens


def reprocessar_fila(nome_fila: str, tentar_aplicar: Callable[[dict], bool], limite: int = 50) -> int:
    """Tenta reaplicar, uma unica vez cada, as mensagens que estao numa fila
    (a DLQ, no nosso caso) via `tentar_aplicar`. As que ainda falharem sao
    devolvidas a fila (nack+requeue) so no final, pelo mesmo motivo do
    espiar_fila: devolver uma a uma faria a proxima leitura pegar de volta a
    que acabou de ser recolocada. Retorna quantas foram aplicadas com sucesso."""
    aplicadas = 0
    with conectar() as conexao:
        canal = conexao.channel()
        declaracao = canal.queue_declare(queue=nome_fila, passive=True)
        total = min(limite, declaracao.method.message_count)

        tags_para_devolver = []
        for _ in range(total):
            method, _properties, body = canal.basic_get(queue=nome_fila, auto_ack=False)
            if method is None:
                break
            mensagem = json.loads(body.decode("utf-8"))
            if tentar_aplicar(mensagem):
                canal.basic_ack(delivery_tag=method.delivery_tag)
                aplicadas += 1
            else:
                tags_para_devolver.append(method.delivery_tag)

        for tag in tags_para_devolver:
            canal.basic_nack(delivery_tag=tag, requeue=True)
    return aplicadas

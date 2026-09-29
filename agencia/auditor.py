"""Funcionalidade adicional: fila de auditoria.

Um consumidor independente das 3 agencias - nao participa do relogio
vetorial nem tem particao de contas, so escuta TUDO que e publicado na
exchange "iceibank.eventos" (routing key "#") e mantem um log central,
imprimindo no console e gravando em data/auditoria.jsonl.

Roda separado das agencias:

    python auditor.py

Precisa da mesma RABBITMQ_URL configurada em agencia/.env (ou na variavel
de ambiente) - reaproveita app.config, entao carrega o mesmo .env.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.services.mensageria import conectar, declarar_fila_auditoria

CAMINHO_LOG = Path(__file__).resolve().parent / "data" / "auditoria.jsonl"


def registrar(routing_key: str, mensagem: dict) -> None:
    linha = {
        "routing_key": routing_key,
        "recebido_em": datetime.now(timezone.utc).isoformat(),
        "mensagem": mensagem,
    }
    CAMINHO_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(CAMINHO_LOG, "a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")
    print(f"[auditoria] ({routing_key}) {mensagem}")


def main() -> None:
    if not config.RABBITMQ_URL:
        raise SystemExit(
            "Defina RABBITMQ_URL (ou crie agencia/.env a partir de agencia/.env.example) antes de rodar o auditor."
        )

    with conectar() as conexao:
        canal = conexao.channel()
        nome_fila = declarar_fila_auditoria(canal)
        canal.basic_qos(prefetch_count=1)

        def callback(ch, method, _properties, body):
            mensagem = json.loads(body.decode("utf-8"))
            registrar(method.routing_key, mensagem)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        canal.basic_consume(queue=nome_fila, on_message_callback=callback)
        print(f"[auditor] ouvindo TODOS os eventos publicados em '{config.EXCHANGE_EVENTOS}' (fila '{nome_fila}')")
        print("[auditor] Ctrl+C para parar")
        try:
            canal.start_consuming()
        except KeyboardInterrupt:
            canal.stop_consuming()


if __name__ == "__main__":
    main()

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega agencia/.env se existir (nao versionado - ver .env.example).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# TODO: substitua pelo seu OFFSET pessoal (dois ultimos digitos da
# matricula/RA), necessario apenas se for rodar em uma maquina
# compartilhada do laboratorio.
OFFSET = 0

NUMERO_AGENCIAS = 3
PORTA_BASE = 4000 + OFFSET

AGENCIAS = [
    {"id": 0, "url": f"http://localhost:{PORTA_BASE}"},
    {"id": 1, "url": f"http://localhost:{PORTA_BASE + 1}"},
    {"id": 2, "url": f"http://localhost:{PORTA_BASE + 2}"},
]

# Segredos - lidos do ambiente, com defaults apenas para desenvolvimento local.
JWT_SECRET_KEY = os.environ.get("ICEI_JWT_SECRET", "dev-secret-troque-em-producao-tamanho-minimo-32-bytes")
JWT_EXPIRE_MINUTES = int(os.environ.get("ICEI_JWT_EXPIRE_MINUTES", "30"))
INTERNAL_SHARED_SECRET = os.environ.get("ICEI_INTERNAL_SECRET", "dev-internal-secret-troque-em-producao")

DEFAULT_LIMITE_DIARIO = 1000.0

# Sprint 2 - mensageria (RabbitMQ). Sem valor padrao: preferimos falhar
# rapido e com uma mensagem clara a conectar "por acidente" em algum broker
# que nao e o do aluno.
RABBITMQ_URL = os.environ.get("RABBITMQ_URL")

# Topologia (ver README para o desenho completo): uma exchange "topic"
# principal para credito entre agencias, confirmacoes e alertas; uma
# exchange "direct" auxiliar para onde vao as mensagens mortas (dead-letter).
EXCHANGE_EVENTOS = "iceibank.eventos"
EXCHANGE_DLX = "iceibank.dlx"

# Funcionalidade adicional - notificacao de saldo baixo: abaixo deste valor,
# a agencia publica um alerta (so no cruzamento, nao a cada operacao).
SALDO_BAIXO_LIMITE = float(os.environ.get("ICEI_SALDO_BAIXO_LIMITE", "50"))


def agencia_responsavel(id_conta: int) -> int:
    return id_conta % NUMERO_AGENCIAS


def fila_creditos(id_agencia: int) -> str:
    return f"fila-agencia-{id_agencia}"


def fila_confirmacoes(id_agencia: int) -> str:
    return f"fila-confirmacoes-agencia-{id_agencia}"


def fila_alertas(id_agencia: int) -> str:
    return f"fila-alertas-agencia-{id_agencia}"


def fila_dlq(id_agencia: int) -> str:
    return f"dlq-agencia-{id_agencia}"


def routing_key_credito(id_agencia: int) -> str:
    return f"agencia.{id_agencia}.creditar"


def routing_key_confirmacao(id_agencia: int) -> str:
    return f"agencia.{id_agencia}.confirmacao"


def routing_key_alerta(id_agencia: int) -> str:
    return f"alerta.saldo_baixo.{id_agencia}"


def routing_key_morta(id_agencia: int) -> str:
    return f"agencia.{id_agencia}.morta"

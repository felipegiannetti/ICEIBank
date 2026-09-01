import os

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
JWT_SECRET_KEY = os.environ.get("ICEI_JWT_SECRET", "dev-secret-troque-em-producao")
JWT_EXPIRE_MINUTES = int(os.environ.get("ICEI_JWT_EXPIRE_MINUTES", "30"))
INTERNAL_SHARED_SECRET = os.environ.get("ICEI_INTERNAL_SECRET", "dev-internal-secret-troque-em-producao")

DEFAULT_LIMITE_DIARIO = 1000.0


def agencia_responsavel(id_conta: int) -> int:
    return id_conta % NUMERO_AGENCIAS

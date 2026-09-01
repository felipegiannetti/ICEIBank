from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config

bearer_scheme = HTTPBearer(auto_error=False)


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def criar_token(id_conta: int) -> tuple[str, int]:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(id_conta),
        "iat": agora,
        "exp": agora + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm="HS256")
    return token, config.JWT_EXPIRE_MINUTES * 60


def get_id_conta_autenticada(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if credenciais is None:
        raise HTTPException(status_code=401, detail="Token ausente.")
    try:
        payload = jwt.decode(credenciais.credentials, config.JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido.")
    return int(payload["sub"])


def exigir_dono(id_conta: int, id_autenticado: int = Depends(get_id_conta_autenticada)) -> int:
    """Dependencia para rotas com {id_conta} no path: o token tem que ser desta mesma conta."""
    if id_conta != id_autenticado:
        raise HTTPException(status_code=403, detail="Você não tem permissão para operar nesta conta.")
    return id_autenticado


def verificar_segredo_interno(request: Request) -> None:
    """Usado apenas na chamada agencia-a-agencia (creditar-remoto) - nao ha
    uma "conta" fazendo essa chamada, entao ela nao usa JWT de usuario."""
    segredo = request.headers.get("X-Internal-Secret")
    if segredo != config.INTERNAL_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Chamada interna não autorizada.")

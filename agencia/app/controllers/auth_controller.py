from fastapi import APIRouter, HTTPException, Request

from app.security import criar_token, verificar_senha
from app.views.auth_view import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request):
    state = request.app.state
    conta = state.contas.obter(body.id_conta)
    if not conta or not verificar_senha(body.senha, conta.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    token, expira_em_segundos = criar_token(conta.id)
    return LoginResponse(access_token=token, token_type="bearer", expires_in=expira_em_segundos)

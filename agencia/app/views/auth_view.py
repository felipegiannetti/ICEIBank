from pydantic import BaseModel


class LoginRequest(BaseModel):
    id_conta: int
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

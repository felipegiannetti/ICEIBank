from pydantic import BaseModel, ConfigDict, Field


class CriarContaRequest(BaseModel):
    id: int
    nome_aluno: str
    senha: str = Field(min_length=4)
    saldo_inicial: float = 0.0


class ContaResponse(BaseModel):
    """Formato de apresentacao (JSON) de uma conta - a "View" desta API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_aluno: str
    saldo: float


class ValorRequest(BaseModel):
    valor: float = Field(gt=0)

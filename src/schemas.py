"""Schemas de entrada e saída da API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DocumentKind = Literal["cpf", "cnpj", "cep", "uf", "pis"]


class DocumentRequest(BaseModel):
    """Corpo comum a todos os endpoints de validação."""

    model_config = ConfigDict(extra="forbid")

    value: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="Documento a validar. Pontuação usual é aceita.",
        examples=["529.982.247-25"],
    )


class ValidationResponse(BaseModel):
    """Resposta de validação local."""

    valid: bool
    document: DocumentKind
    normalized: str
    message: str


class Address(BaseModel):
    """Endereço retornado pelo ViaCEP."""

    cep: str = ""
    street: str | None = None
    complement: str | None = None
    unit: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None
    region: str | None = None
    ibge: str | None = None
    ddd: str | None = None


class CepResponse(ValidationResponse):
    """Resposta do CEP, com origem da informação e endereço opcional."""

    document: Literal["cep"] = "cep"
    source: Literal["viacep", "local"] = "local"
    address: Address | None = None


class HealthResponse(BaseModel):
    """Resposta do endpoint de saúde."""

    status: str
    version: str

"""Aplicação FastAPI da API CEP Valida."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.schemas import (
    Address,
    CepResponse,
    DocumentRequest,
    HealthResponse,
    ValidationResponse,
)
from src.middleware import RateLimitMiddleware
from src.services import viacep
from src.validators.cep import validate_cep
from src.validators.cnpj import validate_cnpj
from src.validators.cpf import validate_cpf
from src.validators.pis import validate_pis
from src.validators.uf import validate_uf

VERSION = "1.0.0"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="API CEP Valida",
    version=VERSION,
    description="Validação local de CPF, CNPJ, CEP e UF, com consulta de endereço no ViaCEP.",
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["saude"])
def health() -> HealthResponse:
    """Confirma que o servidor está no ar."""
    return HealthResponse(status="ok", version=VERSION)


@app.post("/validate/cpf", response_model=ValidationResponse, tags=["validacao"])
def validate_cpf_endpoint(body: DocumentRequest) -> ValidationResponse:
    """Valida um CPF pelo algoritmo oficial."""
    result = validate_cpf(body.value)
    return ValidationResponse(
        valid=result.valid,
        document="cpf",
        normalized=result.normalized,
        message=result.message,
    )


@app.post("/validate/cnpj", response_model=ValidationResponse, tags=["validacao"])
def validate_cnpj_endpoint(body: DocumentRequest) -> ValidationResponse:
    """Valida um CNPJ pelo algoritmo oficial."""
    result = validate_cnpj(body.value)
    return ValidationResponse(
        valid=result.valid,
        document="cnpj",
        normalized=result.normalized,
        message=result.message,
    )


@app.post("/validate/pis", response_model=ValidationResponse, tags=["validacao"])
def validate_pis_endpoint(body: DocumentRequest) -> ValidationResponse:
    """Valida um PIS/PASEP pelo algoritmo oficial."""
    result = validate_pis(body.value)
    return ValidationResponse(
        valid=result.valid,
        document="pis",
        normalized=result.normalized,
        message=result.message,
    )


@app.post("/validate/uf", response_model=ValidationResponse, tags=["validacao"])
def validate_uf_endpoint(body: DocumentRequest) -> ValidationResponse:
    """Valida uma sigla de unidade federativa."""
    result = validate_uf(body.value)
    return ValidationResponse(
        valid=result.valid,
        document="uf",
        normalized=result.normalized,
        message=result.message,
    )


@app.post("/validate/cep", response_model=CepResponse, tags=["validacao"])
def validate_cep_endpoint(body: DocumentRequest) -> CepResponse:
    """Valida o formato do CEP e tenta enriquecer o resultado com o ViaCEP."""
    result = validate_cep(body.value)
    if not result.valid:
        return CepResponse(valid=False, normalized=result.normalized, message=result.message)

    lookup = viacep.lookup_cep(result.normalized.replace("-", ""))
    if lookup.status == "unavailable":
        return CepResponse(
            valid=True,
            normalized=result.normalized,
            source="local",
            message="formato de CEP válido; ViaCEP indisponível, endereço não consultado",
        )
    if lookup.status == "not_found":
        return CepResponse(
            valid=False,
            normalized=result.normalized,
            source="viacep",
            message="formato de CEP válido, mas o CEP não foi encontrado no ViaCEP",
        )
    return CepResponse(
        valid=True,
        normalized=result.normalized,
        source="viacep",
        message="CEP válido e encontrado no ViaCEP",
        address=Address(**lookup.address or {}),
    )


if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

"""Consulta ao ViaCEP com timeout curto, retry com backoff e fallback."""

import os
from dataclasses import dataclass
from typing import Literal

import requests
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

DEFAULT_BASE_URL = "https://viacep.com.br/ws"
DEFAULT_TIMEOUT = 3.0
MAX_ATTEMPTS = 3

LookupStatus = Literal["found", "not_found", "unavailable"]


@dataclass(frozen=True)
class CepLookup:
    """Resultado de uma consulta de CEP."""

    status: LookupStatus
    address: dict[str, str] | None = None


def _base_url() -> str:
    return os.getenv("VIA_CEP_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _timeout() -> float:
    try:
        return max(1.0, float(os.getenv("VIA_CEP_TIMEOUT", str(DEFAULT_TIMEOUT))))
    except ValueError:
        return DEFAULT_TIMEOUT


def _request_cep(cep_digits: str) -> dict:
    response = requests.get(f"{_base_url()}/{cep_digits}/json/", timeout=_timeout())
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("resposta do ViaCEP não é um objeto JSON")
    return payload


def _to_address(payload: dict) -> dict[str, str | None]:
    return {
        "cep": payload.get("cep") or "",
        "street": payload.get("logradouro") or None,
        "complement": payload.get("complemento") or None,
        "unit": payload.get("unidade") or None,
        "neighborhood": payload.get("bairro") or None,
        "city": payload.get("localidade") or None,
        "state": payload.get("uf") or None,
        "region": payload.get("regiao") or None,
        "ibge": payload.get("ibge") or None,
        "ddd": payload.get("ddd") or None,
    }


def lookup_cep(cep_digits: str) -> CepLookup:
    """Consulta o ViaCEP; nunca propaga falha de rede ao chamador."""
    retryer = Retrying(
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=0.15, max=1),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    try:
        payload = retryer(_request_cep, cep_digits)
    except (requests.RequestException, ValueError):
        return CepLookup(status="unavailable")
    if payload.get("erro"):
        return CepLookup(status="not_found")
    return CepLookup(status="found", address=_to_address(payload))

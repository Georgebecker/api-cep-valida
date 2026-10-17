"""Consulta ao ViaCEP com timeout curto, retry com backoff e fallback."""

import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Literal

import requests
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

DEFAULT_BASE_URL = "https://viacep.com.br/ws"
DEFAULT_TIMEOUT = 3.0
DEFAULT_CACHE_TTL = 300.0
MAX_ATTEMPTS = 3
MAX_CACHE_ENTRIES = 1024

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


def _cache_ttl() -> float:
    try:
        return max(0.0, float(os.getenv("VIA_CEP_CACHE_TTL", str(DEFAULT_CACHE_TTL))))
    except ValueError:
        return DEFAULT_CACHE_TTL


_CACHE: OrderedDict[str, tuple[float, CepLookup]] = OrderedDict()
_CACHE_LOCK = Lock()


def clear_cache() -> None:
    """Esvazia o cache em memória (usado pelos testes)."""
    with _CACHE_LOCK:
        _CACHE.clear()


def _cache_get(cep_digits: str) -> CepLookup | None:
    with _CACHE_LOCK:
        entry = _CACHE.get(cep_digits)
        if entry is None:
            return None
        expires_at, result = entry
        if time.monotonic() >= expires_at:
            _CACHE.pop(cep_digits, None)
            return None
        _CACHE.move_to_end(cep_digits)
        return result


def _cache_set(cep_digits: str, result: CepLookup) -> None:
    ttl = _cache_ttl()
    if ttl <= 0 or result.status == "unavailable" or MAX_CACHE_ENTRIES <= 0:
        return
    with _CACHE_LOCK:
        now = time.monotonic()
        for key in [key for key, (expires_at, _) in _CACHE.items() if expires_at <= now]:
            del _CACHE[key]
        while len(_CACHE) >= MAX_CACHE_ENTRIES:
            _CACHE.popitem(last=False)
        _CACHE[cep_digits] = (now + ttl, result)
        _CACHE.move_to_end(cep_digits)


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
    """Consulta o cache e, se necessário, o ViaCEP; nunca propaga falha de rede."""
    cached = _cache_get(cep_digits)
    if cached is not None:
        return cached

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
        result = CepLookup(status="not_found")
    else:
        result = CepLookup(status="found", address=_to_address(payload))
    _cache_set(cep_digits, result)
    return result

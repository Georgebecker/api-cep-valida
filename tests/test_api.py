"""Testes dos endpoints HTTP da API."""

import pytest
import requests
from fastapi.testclient import TestClient

from src.validators.uf import UFS


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


VIA_CEP_PAYLOAD = {
    "cep": "01001-000",
    "logradouro": "Praça da Sé",
    "complemento": "lado ímpar",
    "unidade": "",
    "bairro": "Sé",
    "localidade": "São Paulo",
    "uf": "SP",
    "estado": "São Paulo",
    "regiao": "Sudeste",
    "ibge": "3550308",
    "gia": "1004",
    "ddd": "11",
    "siafi": "7107",
}


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize(
    ("endpoint", "document", "valid_value", "invalid_value"),
    [
        ("/validate/cpf", "cpf", "529.982.247-25", "529.982.247-26"),
        ("/validate/cnpj", "cnpj", "11.222.333/0001-81", "11.222.333/0001-82"),
        ("/validate/uf", "uf", "sp", "XX"),
        ("/validate/pis", "pis", "120.425.445-09", "120.425.445-08"),
    ],
)
def test_endpoints_aceitam_valido_e_rejeitam_invalido(
    client: TestClient, endpoint: str, document: str, valid_value: str, invalid_value: str
) -> None:
    accepted = client.post(endpoint, json={"value": valid_value})
    assert accepted.status_code == 200
    assert accepted.json()["valid"] is True
    assert accepted.json()["document"] == document

    rejected = client.post(endpoint, json={"value": invalid_value})
    assert rejected.status_code == 200
    assert rejected.json()["valid"] is False


@pytest.mark.parametrize("uf", sorted(UFS))
def test_endpoint_uf_aceita_as_27_siglas(client: TestClient, uf: str) -> None:
    response = client.post("/validate/uf", json={"value": uf})
    assert response.json()["valid"] is True


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"value": ""},
        {"value": "52998224725", "extra": True},
        {"valor": "52998224725"},
        {"value": "x" * 33},
        {"value": 52998224725},
    ],
)
def test_payload_malformado_retorna_422(client: TestClient, payload: dict) -> None:
    response = client.post("/validate/cpf", json=payload)
    assert response.status_code == 422


def test_cep_valido_consulta_viacep(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float) -> FakeResponse:
        assert url.endswith("/01001000/json/")
        assert timeout >= 1.0
        return FakeResponse(VIA_CEP_PAYLOAD)

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    response = client.post("/validate/cep", json={"value": "01001-000"})
    body = response.json()
    assert response.status_code == 200
    assert body["valid"] is True
    assert body["source"] == "viacep"
    assert body["normalized"] == "01001-000"
    assert body["address"]["city"] == "São Paulo"
    assert body["address"]["state"] == "SP"


def test_cep_invalido_nao_consulta_viacep(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float) -> FakeResponse:
        raise AssertionError("ViaCEP não deveria ser consultado")

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    response = client.post("/validate/cep", json={"value": "0100100"})
    body = response.json()
    assert response.status_code == 200
    assert body["valid"] is False
    assert body["source"] == "local"


def test_cep_com_fallback_quando_viacep_cai(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_get(url: str, timeout: float) -> FakeResponse:
        raise requests.ConnectionError("ViaCEP fora do ar")

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    response = client.post("/validate/cep", json={"value": "01001-000"})
    body = response.json()
    assert response.status_code == 200
    assert body["valid"] is True
    assert body["source"] == "local"
    assert body["address"] is None


def test_cep_nao_encontrado_no_viacep(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float) -> FakeResponse:
        return FakeResponse({"erro": True})

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    response = client.post("/validate/cep", json={"value": "99999-999"})
    body = response.json()
    assert response.status_code == 200
    assert body["valid"] is False
    assert body["source"] == "viacep"


def test_cep_resposta_invalida_do_viacep_nao_quebra(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_get(url: str, timeout: float) -> FakeResponse:
        return FakeResponse(["lista"])  # type: ignore[arg-type]

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    response = client.post("/validate/cep", json={"value": "01001-000"})
    body = response.json()
    assert response.status_code == 200
    assert body["valid"] is True
    assert body["source"] == "local"


def test_cache_evita_segunda_consulta_ao_viacep(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def fake_get(url: str, timeout: float) -> FakeResponse:
        calls.append(url)
        return FakeResponse(VIA_CEP_PAYLOAD)

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    first = client.post("/validate/cep", json={"value": "01001-000"}).json()
    second = client.post("/validate/cep", json={"value": "01001-000"}).json()

    assert len(calls) == 1
    assert first == second


def test_cache_respeita_ttl_zero(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIA_CEP_CACHE_TTL", "0")
    calls: list[str] = []

    def fake_get(url: str, timeout: float) -> FakeResponse:
        calls.append(url)
        return FakeResponse(VIA_CEP_PAYLOAD)

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    client.post("/validate/cep", json={"value": "01001-000"})
    client.post("/validate/cep", json={"value": "01001-000"})

    assert len(calls) == 2


def test_falha_nao_entra_no_cache(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, timeout: float) -> FakeResponse:
        calls.append(url)
        if len(calls) <= 3:
            raise requests.ConnectionError("ViaCEP instável")
        return FakeResponse(VIA_CEP_PAYLOAD)

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    first = client.post("/validate/cep", json={"value": "01001-000"}).json()
    second = client.post("/validate/cep", json={"value": "01001-000"}).json()

    assert first["source"] == "local"
    assert second["source"] == "viacep"
    assert len(calls) == 4


def test_cache_respeita_limite_de_entradas(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.services import viacep

    monkeypatch.setattr(viacep, "MAX_CACHE_ENTRIES", 2)
    viacep.clear_cache()

    def fake_get(url: str, timeout: float) -> FakeResponse:
        return FakeResponse({"erro": True})

    monkeypatch.setattr("src.services.viacep.requests.get", fake_get)

    for cep in ("01001000", "02001000", "03001000"):
        response = client.post("/validate/cep", json={"value": cep})
        assert response.status_code == 200

    assert len(viacep._CACHE) == 2

"""Testes do rate limiting por IP."""

import time

from fastapi.testclient import TestClient

from src import middleware


def _validate_uf(client: TestClient) -> int:
    return client.post("/validate/uf", json={"value": "SP"}).status_code


def test_limite_por_ip_respeita_janela(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "3")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")
    middleware.reset()

    statuses = [_validate_uf(client) for _ in range(4)]

    assert statuses == [200, 200, 200, 429]
    blocked = client.post("/validate/uf", json={"value": "SP"})
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1


def test_rate_limit_pode_ser_desabilitado(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "0")
    middleware.reset()

    statuses = [_validate_uf(client) for _ in range(5)]

    assert statuses == [200] * 5


def test_health_nao_e_limitado(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    middleware.reset()

    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200


def test_janela_expira_e_libera_novamente(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "0.2")
    middleware.reset()

    assert _validate_uf(client) == 200
    assert _validate_uf(client) == 429
    time.sleep(0.25)
    assert _validate_uf(client) == 200


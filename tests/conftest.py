"""Fixtures compartilhadas pelos testes."""

import pytest
from fastapi.testclient import TestClient

from src import middleware
from src.main import app
from src.services import viacep


@pytest.fixture(autouse=True)
def _limpar_cache_viacep():
    viacep.clear_cache()
    yield
    viacep.clear_cache()


@pytest.fixture(autouse=True)
def _configurar_rate_limit(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "10000")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")
    middleware.reset()
    yield
    middleware.reset()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)

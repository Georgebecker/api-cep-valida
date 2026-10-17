"""Fixtures compartilhadas pelos testes."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services import viacep


@pytest.fixture(autouse=True)
def _limpar_cache_viacep():
    viacep.clear_cache()
    yield
    viacep.clear_cache()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)

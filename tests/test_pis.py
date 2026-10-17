"""Testes do validador de PIS/PASEP."""

import pytest

from src.validators.pis import validate_pis

VALID_PIS = ["120.425.445-09", "170.332.558-94", "123.456.789-00", "12042544509"]


@pytest.mark.parametrize("pis", VALID_PIS)
def test_pis_valido(pis: str) -> None:
    result = validate_pis(pis)
    assert result.valid is True
    assert len(result.normalized) == 11


@pytest.mark.parametrize(
    "pis",
    [
        "120.425.445-08",  # dígito verificador errado
        "111.111.111-11",  # sequência repetida
        "1204254450",  # tamanho errado
        "120425445090",  # tamanho errado
        "120.425.445-0A",  # caractere não numérico
        "pis-invalido",
        "",
    ],
)
def test_pis_invalido(pis: str) -> None:
    assert validate_pis(pis).valid is False


def test_pis_nao_numerico_nao_e_normalizado() -> None:
    result = validate_pis("120.425.445-0A")
    assert result.valid is False
    assert result.normalized == ""

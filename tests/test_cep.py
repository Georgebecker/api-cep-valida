"""Testes da validação local de CEP."""

import pytest

from src.validators.cep import validate_cep


@pytest.mark.parametrize("cep", ["01001-000", "01001000", "01001 000", "99999-999"])
def test_cep_formato_valido(cep: str) -> None:
    result = validate_cep(cep)
    assert result.valid is True
    assert len(result.normalized) == 9
    assert result.normalized[5] == "-"


@pytest.mark.parametrize(
    "cep",
    [
        "00000-000",
        "0100100",
        "010010000",
        "01001-00A",
        "cep-invalido",
        "",
    ],
)
def test_cep_formato_invalido(cep: str) -> None:
    assert validate_cep(cep).valid is False

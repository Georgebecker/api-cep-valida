"""Testes do validador de CNPJ."""

import pytest

from src.validators.cnpj import validate_cnpj

VALID_CNPJS = ["11.222.333/0001-81", "04.252.011/0001-10", "00.000.000/0001-91", "11222333000181"]


@pytest.mark.parametrize("cnpj", VALID_CNPJS)
def test_cnpj_valido(cnpj: str) -> None:
    result = validate_cnpj(cnpj)
    assert result.valid is True
    assert len(result.normalized) == 14


@pytest.mark.parametrize(
    "cnpj",
    [
        "11.222.333/0001-82",  # dígito verificador errado
        "11111111111111",  # sequência repetida
        "1122233300018",  # tamanho errado
        "112223330001811",  # tamanho errado
        "11.222.333/0001-8A",  # caractere não numérico
        "cnpj-invalido",
        "",
    ],
)
def test_cnpj_invalido(cnpj: str) -> None:
    assert validate_cnpj(cnpj).valid is False


def test_cnpj_nao_numerico_nao_e_normalizado() -> None:
    result = validate_cnpj("11.222.333/0001-8A")
    assert result.valid is False
    assert result.normalized == ""

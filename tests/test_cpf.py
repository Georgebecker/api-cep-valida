"""Testes do validador de CPF."""

import pytest

from src.validators.cpf import validate_cpf

VALID_CPFS = ["529.982.247-25", "111.444.777-35", "123.456.789-09", "52998224725"]


@pytest.mark.parametrize("cpf", VALID_CPFS)
def test_cpf_valido(cpf: str) -> None:
    result = validate_cpf(cpf)
    assert result.valid is True
    assert len(result.normalized) == 11


@pytest.mark.parametrize(
    "cpf",
    [
        "529.982.247-26",  # dígito verificador errado
        "111.111.111-11",  # sequência repetida
        "5299822472",  # tamanho errado
        "529982247251",  # tamanho errado
        "529.982.247-2A",  # caractere não numérico
        "abc.def.ghi-jk",
        "",
    ],
)
def test_cpf_invalido(cpf: str) -> None:
    assert validate_cpf(cpf).valid is False


def test_cpf_nao_numerico_nao_e_normalizado() -> None:
    result = validate_cpf("529.982.247-2A")
    assert result.valid is False
    assert result.normalized == ""

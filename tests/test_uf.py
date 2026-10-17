"""Testes do validador de UF."""

import pytest

from src.validators.uf import UFS, validate_uf


def test_existem_27_ufs() -> None:
    assert len(UFS) == 27


@pytest.mark.parametrize("uf", sorted(UFS))
def test_uf_valida(uf: str) -> None:
    result = validate_uf(uf)
    assert result.valid is True
    assert result.normalized == uf


@pytest.mark.parametrize("uf", ["sp", " Mg ", "rj", "to"])
def test_uf_case_insensitive(uf: str) -> None:
    assert validate_uf(uf).valid is True


@pytest.mark.parametrize("uf", ["XX", "S", "SPX", "1", "", "  "])
def test_uf_invalida(uf: str) -> None:
    assert validate_uf(uf).valid is False

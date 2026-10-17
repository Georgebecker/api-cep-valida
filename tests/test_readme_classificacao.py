"""Teste que verifica a presença e a validade da classificação no README."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
FIELDS = ("Propósito", "Maturidade", "O que está sendo treinado", "Quem usaria")
VALID_MATURITIES = {"rascunho", "funcional", "usável"}
FIELD_PATTERN = re.compile(
    r"^- \*\*(Propósito|Maturidade|O que está sendo treinado|Quem usaria):\*\*\s*(.+)$",
    re.MULTILINE,
)


def read_classification() -> dict[str, str]:
    text = README_PATH.read_text(encoding="utf-8")
    assert "## Classificação" in text, "README sem seção '## Classificação'"
    section = text.split("## Classificação", 1)[1].split("\n## ", 1)[0]
    return {field: value.strip() for field, value in FIELD_PATTERN.findall(section)}


def test_readme_tem_secao_classificacao() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    assert "## Classificação" in text


def test_classificacao_tem_os_quatro_campos_preenchidos() -> None:
    classification = read_classification()
    for field in FIELDS:
        assert field in classification, f"campo ausente: {field}"
        assert classification[field], f"campo vazio: {field}"


def test_maturidade_declarada_e_valida() -> None:
    maturity = read_classification()["Maturidade"].strip("`").lower()
    assert maturity in VALID_MATURITIES


def test_maturidade_usavel_exige_entregaveis() -> None:
    maturity = read_classification()["Maturidade"].strip("`").lower()
    if maturity != "usável":
        return
    for relative in ("pytest.ini", "requirements.txt", "Dockerfile", "src/main.py"):
        assert (PROJECT_ROOT / relative).is_file(), f"entregável ausente: {relative}"
    assert any((PROJECT_ROOT / "tests").glob("test_*.py")), "nenhum teste automatizado encontrado"

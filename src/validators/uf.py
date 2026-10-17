"""Validação das 27 unidades federativas do Brasil."""

from src.validators.common import ValidationResult

UFS = frozenset(
    {
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    }
)


def validate_uf(value: str) -> ValidationResult:
    """Valida uma sigla de UF, sem diferenciar maiúsculas de minúsculas."""
    normalized = value.strip().upper()
    if normalized in UFS:
        return ValidationResult(True, normalized, "UF válida")
    return ValidationResult(False, normalized, "UF deve ser uma das 27 siglas oficiais")

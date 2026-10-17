"""Tipos e utilidades compartilhados pelos validadores."""

from dataclasses import dataclass

ALLOWED_SEPARATORS = frozenset(".-/ ")


@dataclass(frozen=True)
class ValidationResult:
    """Resultado padronizado de uma validação local."""

    valid: bool
    normalized: str
    message: str


def only_digits(value: str) -> tuple[str, str | None]:
    """Remove separadores permitidos e exige que o restante seja dígito ASCII."""
    cleaned = "".join(char for char in value if char not in ALLOWED_SEPARATORS)
    if not cleaned or not (cleaned.isascii() and cleaned.isdigit()):
        return "", "deve conter apenas dígitos e separadores"
    return cleaned, None


def has_repeated_digits(digits: str) -> bool:
    """Indica se todos os dígitos são iguais."""
    return len(set(digits)) == 1

"""Validação de CNPJ pelo algoritmo oficial da Receita Federal."""

from src.validators.common import ValidationResult, has_repeated_digits, only_digits

FIRST_WEIGHTS = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
SECOND_WEIGHTS = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def _check_digit(digits: str, weights: tuple[int, ...]) -> str:
    total = sum(int(digit) * weight for digit, weight in zip(digits, weights))
    remainder = total % 11
    return "0" if remainder < 2 else str(11 - remainder)


def validate_cnpj(value: str) -> ValidationResult:
    """Valida um CNPJ, aceitando pontuação usual (`.` `/` e `-`)."""
    digits, error = only_digits(value)
    if error:
        return ValidationResult(False, "", error)
    if len(digits) != 14:
        return ValidationResult(False, digits, "CNPJ deve conter 14 dígitos")
    if has_repeated_digits(digits):
        return ValidationResult(False, digits, "CNPJ não pode ter os 14 dígitos iguais")

    first = _check_digit(digits[:12], FIRST_WEIGHTS)
    second = _check_digit(digits[:13], SECOND_WEIGHTS)
    if digits[12] != first or digits[13] != second:
        return ValidationResult(False, digits, "dígitos verificadores inválidos")
    return ValidationResult(True, digits, "CNPJ válido")

"""Validação de CPF pelo algoritmo oficial da Receita Federal."""

from src.validators.common import ValidationResult, has_repeated_digits, only_digits


def _check_digit(digits: str, first_weight: int) -> str:
    total = sum(int(digit) * weight for digit, weight in zip(digits, range(first_weight, 1, -1)))
    remainder = (total * 10) % 11
    return "0" if remainder == 10 else str(remainder)


def validate_cpf(value: str) -> ValidationResult:
    """Valida um CPF, aceitando pontuação usual (`.` e `-`)."""
    digits, error = only_digits(value)
    if error:
        return ValidationResult(False, "", error)
    if len(digits) != 11:
        return ValidationResult(False, digits, "CPF deve conter 11 dígitos")
    if has_repeated_digits(digits):
        return ValidationResult(False, digits, "CPF não pode ter os 11 dígitos iguais")

    first = _check_digit(digits[:9], 10)
    second = _check_digit(digits[:10], 11)
    if digits[9] != first or digits[10] != second:
        return ValidationResult(False, digits, "dígitos verificadores inválidos")
    return ValidationResult(True, digits, "CPF válido")

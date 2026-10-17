"""Validação de PIS/PASEP pelo algoritmo oficial."""

from src.validators.common import ValidationResult, has_repeated_digits, only_digits

WEIGHTS = (3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def _check_digit(digits: str) -> str:
    total = sum(int(digit) * weight for digit, weight in zip(digits, WEIGHTS))
    digit = 11 - (total % 11)
    return "0" if digit >= 10 else str(digit)


def validate_pis(value: str) -> ValidationResult:
    """Valida um PIS/PASEP, aceitando pontuação usual (`.` e `-`)."""
    digits, error = only_digits(value)
    if error:
        return ValidationResult(False, "", error)
    if len(digits) != 11:
        return ValidationResult(False, digits, "PIS/PASEP deve conter 11 dígitos")
    if has_repeated_digits(digits):
        return ValidationResult(False, digits, "PIS/PASEP não pode ter os 11 dígitos iguais")
    if digits[10] != _check_digit(digits[:10]):
        return ValidationResult(False, digits, "dígito verificador inválido")
    return ValidationResult(True, digits, "PIS/PASEP válido")

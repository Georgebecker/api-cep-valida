"""Validação de formato de CEP conforme o padrão dos Correios."""

from src.validators.common import ValidationResult, only_digits


def format_cep(digits: str) -> str:
    """Formata oito dígitos como `NNNNN-NNN`."""
    return f"{digits[:5]}-{digits[5:]}"


def validate_cep(value: str) -> ValidationResult:
    """Valida o formato do CEP, sem consultar serviço externo."""
    digits, error = only_digits(value)
    if error:
        return ValidationResult(False, "", error)
    if len(digits) != 8:
        return ValidationResult(False, digits, "CEP deve conter 8 dígitos")
    if digits == "00000000":
        return ValidationResult(False, format_cep(digits), "CEP 00000-000 não existe")
    return ValidationResult(True, format_cep(digits), "formato de CEP válido")

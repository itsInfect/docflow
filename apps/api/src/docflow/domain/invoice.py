from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


def normalize_fields(fields: dict[str, Any], schema: dict[str, Any]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    definitions = schema.get("fields", [])
    if not isinstance(definitions, list):
        raise ValueError("Schema fields must be a list")

    for definition in definitions:
        if not isinstance(definition, dict) or not isinstance(definition.get("key"), str):
            continue
        key = definition["key"]
        value = fields.get(key, definition.get("default"))
        normalized[key] = normalize_value(value, str(definition.get("type", "string")))
    return normalized


def normalize_value(value: Any, field_type: str) -> object:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if field_type == "string":
        return " ".join(text.split())
    if field_type == "inn":
        digits = re.sub(r"\D", "", text)
        return digits or None
    if field_type == "date":
        for pattern in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, pattern).date().isoformat()
            except ValueError:
                continue
        return text
    if field_type in {"money", "percent"}:
        decimal_value = parse_decimal(text)
        if decimal_value is None:
            return text
        precision = Decimal("0.01") if field_type == "money" else Decimal("0.001")
        return format(decimal_value.quantize(precision), "f").rstrip("0").rstrip(".")
    if field_type == "currency":
        currency = text.upper().replace(".", "")
        aliases = {"₽": "RUB", "РУБ": "RUB", "РУБЛЬ": "RUB", "RUR": "RUB"}
        return aliases.get(currency, currency)
    return text


def validate_invoice(
    *,
    fields: dict[str, object],
    raw_fields: dict[str, Any],
    schema: dict[str, Any],
    source_text: str,
) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    definitions = schema.get("fields", [])
    if not isinstance(definitions, list):
        return [check("schema", False, "Некорректная схема документа")]

    for definition in definitions:
        if not isinstance(definition, dict) or not isinstance(definition.get("key"), str):
            continue
        key = definition["key"]
        if definition.get("required"):
            present = fields.get(key) not in {None, ""}
            checks.append(check("required", present, f"Обязательное поле: {key}", key))
        if definition.get("critical") and fields.get(key) not in {None, ""}:
            grounded = compact(raw_fields.get(key)) in compact(source_text)
            checks.append(
                check("grounding", grounded, f"Значение {key} найдено в исходном тексте", key)
            )

    for key in ("supplier_inn", "buyer_inn"):
        value = fields.get(key)
        if value:
            checks.append(
                check("inn_checksum", valid_inn(str(value)), f"Контрольная сумма {key}", key)
            )

    doc_date = fields.get("doc_date")
    if doc_date:
        try:
            parsed_date = date.fromisoformat(str(doc_date))
            sensible = date(1990, 1, 1) <= parsed_date <= date.today() + timedelta(days=1)
        except ValueError:
            sensible = False
        checks.append(
            check(
                "date_sanity",
                sensible,
                "Дата документа находится в допустимом диапазоне",
                "doc_date",
            )
        )

    subtotal = decimal_field(fields, "amount_without_vat")
    vat_rate = decimal_field(fields, "vat_rate")
    vat_amount = decimal_field(fields, "vat_amount")
    total = decimal_field(fields, "total_amount")
    if subtotal is not None and vat_rate is not None and vat_amount is not None:
        expected_vat = subtotal * vat_rate / Decimal(100)
        checks.append(
            check(
                "vat_calculation",
                close_money(expected_vat, vat_amount),
                "НДС рассчитан корректно",
                "vat_amount",
            )
        )
    if subtotal is not None and vat_amount is not None and total is not None:
        checks.append(
            check(
                "total_calculation",
                close_money(subtotal + vat_amount, total),
                "Итог равен сумме без НДС и НДС",
                "total_amount",
            )
        )

    currency = fields.get("currency")
    if currency:
        checks.append(
            check(
                "currency_known",
                currency in {"RUB", "USD", "EUR"},
                "Валюта поддерживается",
                "currency",
            )
        )
    return checks


def check(code: str, passed: bool, message: str, field: str | None = None) -> dict[str, object]:
    return {"code": code, "passed": passed, "message": message, "field": field, "severity": "error"}


def parse_decimal(value: str) -> Decimal | None:
    cleaned = re.sub(r"[^\d,.-]", "", value.replace(" ", ""))
    if cleaned.count(",") == 1 and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def decimal_field(fields: dict[str, object], key: str) -> Decimal | None:
    value = fields.get(key)
    return parse_decimal(str(value)) if value not in {None, ""} else None


def close_money(left: Decimal, right: Decimal) -> bool:
    return abs(left - right) <= Decimal("0.02")


def compact(value: object) -> str:
    return re.sub(r"[^\w]+", "", str(value or "").casefold())


def valid_inn(value: str) -> bool:
    if not value.isdigit() or len(value) not in {10, 12}:
        return False

    digits = [int(char) for char in value]

    def checksum(coefficients: list[int]) -> int:
        return (
            sum(
                coefficient * digit
                for coefficient, digit in zip(coefficients, digits, strict=False)
            )
            % 11
            % 10
        )

    if len(digits) == 10:
        return checksum([2, 4, 10, 3, 5, 9, 4, 6, 8]) == digits[9]
    return (
        checksum([7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) == digits[10]
        and checksum([3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) == digits[11]
    )

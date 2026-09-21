from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

MONEY = r"(\d[\d ]*(?:[,.]\d{2})?)"
RUSSIAN_MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def extract_document_fields(text: str, document_type: str) -> dict[str, object]:
    invoice_number_patterns = [
        r"номер\s+документа\s*[:№]?\s*([A-ZА-ЯЁ0-9][\w/-]*)",
        r"(?:сч[её]т\s+на\s+оплату|invoice)\s*(?:№|no\.?|number)?\s*([\w/-]+)",
    ]
    act_number_patterns = [
        r"(?:service\s+act|акт(?:\s+выполненных\s+работ)?)\s*(?:№|no\.?)?\s*([\w/-]+)",
        *invoice_number_patterns,
    ]
    doc_number = _first_match(
        act_number_patterns if document_type == "service_act" else invoice_number_patterns,
        text,
    )

    doc_date = _extract_date(text)
    inns = re.findall(
        r"(?:ИНН|INN)\s*(?:поставщика|покупателя|исполнителя|заказчика)?\s*[:№]?\s*(\d{10}|\d{12})",
        text,
        re.IGNORECASE,
    )
    supplier_inn = inns[0] if inns else None
    buyer_inn = inns[1] if len(inns) > 1 else None

    supplier_name = _party_name(
        text,
        ["поставщик", "исполнитель", "contractor", "supplier"],
        ["покупатель", "заказчик", "customer", "buyer", "ИНН", "INN"],
    )
    buyer_name = _party_name(
        text,
        ["покупатель", "заказчик", "customer", "buyer"],
        ["ИНН", "INN", "КПП", "KPP", "адрес", "address"],
    )

    vat_match = _search(
        rf"(?:в\s+том\s+числе\s+)?(?:НДС|VAT)\s*(\d+(?:[.,]\d+)?)\s*%\s*[:\-]?\s*{MONEY}",
        text,
    )
    vat_rate = vat_match.group(1) if vat_match else None
    vat_amount = vat_match.group(2) if vat_match else None

    total_amount = _money_after(
        [
            r"итоговая\s+сумма\s+к\s+оплате",
            r"итого\s+к\s+оплате",
            r"\bитого\b",
            r"\btotal\b",
        ],
        text,
    )
    amount_without_vat = _money_after(
        [r"сумма\s+без\s+НДС", r"services\s+subtotal", r"subtotal"],
        text,
    )
    if amount_without_vat is None and total_amount is not None and vat_amount is not None:
        amount_without_vat = _subtract_money(total_amount, vat_amount)

    has_rubles = bool(re.search(r"\b(?:RUB|RUR|руб(?:ль|ля|лей)?\.?)\b", text, re.IGNORECASE))
    return {
        "doc_number": doc_number,
        "doc_date": doc_date,
        "supplier_inn": supplier_inn,
        "supplier_name": supplier_name,
        "buyer_inn": buyer_inn,
        "buyer_name": buyer_name,
        "amount_without_vat": amount_without_vat,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "total_amount": total_amount,
        "currency": "RUB" if has_rubles else None,
    }


def _first_match(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = _search(pattern, text)
        if match:
            return match.group(1).strip(" .:;|")
    return None


def _extract_date(text: str) -> str | None:
    numeric = _search(r"\b(\d{2}[./]\d{2}[./]\d{4})\b", text)
    if numeric:
        return numeric.group(1).replace("/", ".")
    written = _search(
        r"\b(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})\b",
        text,
    )
    if written:
        day = int(written.group(1))
        month = RUSSIAN_MONTHS[written.group(2).casefold()]
        return f"{day:02d}.{month:02d}.{written.group(3)}"
    return None


def _party_name(text: str, labels: list[str], stop_labels: list[str]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    stop_pattern = "|".join(re.escape(label) for label in stop_labels)
    match = _search(
        rf"(?:{label_pattern})\s*[:\-—]+\s*(.+?)(?=\s+(?:{stop_pattern})\s*[:\-—]|\n|$)",
        text,
    )
    if not match:
        return None
    value = re.sub(r"\s+", " ", match.group(1)).strip(" -—:;|")
    value = re.sub(r"^(?:000|OOO)\b", "ООО", value, count=1, flags=re.IGNORECASE)
    return value or None


def _money_after(labels: list[str], text: str) -> str | None:
    for label in labels:
        match = _search(rf"{label}\s*[:\-]?\s*{MONEY}", text)
        if match:
            return match.group(1).strip()
    return None


def _subtract_money(total: str, vat: str) -> str | None:
    try:
        difference = _decimal(total) - _decimal(vat)
    except InvalidOperation:
        return None
    return f"{difference:.2f}"


def _decimal(value: str) -> Decimal:
    return Decimal(value.replace(" ", "").replace(",", "."))


def _search(pattern: str, text: str) -> re.Match[str] | None:
    return re.search(pattern, text, re.IGNORECASE | re.MULTILINE)

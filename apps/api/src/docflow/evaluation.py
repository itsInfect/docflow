from __future__ import annotations

import json
import random
import re
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from docflow.domain.invoice import compact, normalize_fields, validate_invoice

FIELD_KEYS = (
    "doc_number",
    "doc_date",
    "supplier_inn",
    "supplier_name",
    "buyer_inn",
    "buyer_name",
    "amount_without_vat",
    "vat_rate",
    "vat_amount",
    "total_amount",
    "currency",
)
CRITICAL_FIELDS = ("doc_number", "doc_date", "supplier_inn", "total_amount")


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    case_id: str
    split: str
    layout: str
    text: str
    expected_doc_type: str
    expected_fields: dict[str, object]


@dataclass(frozen=True, slots=True)
class BaselinePrediction:
    document_type: str | None
    confidence: float
    raw_fields: dict[str, object]
    fields: dict[str, object]


def generate_invoice_dataset(*, count: int = 30, seed: int = 42) -> list[EvaluationCase]:
    if count < 10:
        raise ValueError("Evaluation dataset must contain at least 10 cases")
    randomizer = random.Random(seed)
    suppliers = [
        ("ООО Север", "7707083893"),
        ("АО Вектор", "7736050003"),
        ("ООО Альфа", "7704217370"),
    ]
    buyers = [
        ("ООО Маяк", "7707083893"),
        ("АО Горизонт", "7736050003"),
        ("ООО Контур", "7704217370"),
    ]
    layouts = ("classic", "compact", "ledger")
    cases: list[EvaluationCase] = []

    for index in range(count):
        split = "development" if index < int(count * 0.4) else "holdout"
        if index >= int(count * 0.73):
            split = "stress"
        layout = layouts[index % len(layouts)]
        supplier_name, supplier_inn = suppliers[index % len(suppliers)]
        buyer_name, buyer_inn = buyers[(index + 1) % len(buyers)]
        subtotal = (Decimal("750") + Decimal(index * 137)).quantize(Decimal("0.01"))
        vat_rate = Decimal("20")
        vat_amount = (subtotal * vat_rate / Decimal(100)).quantize(Decimal("0.01"))
        total = subtotal + vat_amount
        doc_date = date(2025, 1, 15) + timedelta(days=index * 7)
        doc_number = f"INV-{1000 + index}"
        raw_fields: dict[str, Any] = {
            "doc_number": doc_number,
            "doc_date": doc_date.strftime("%d.%m.%Y"),
            "supplier_inn": supplier_inn,
            "supplier_name": supplier_name,
            "buyer_inn": buyer_inn,
            "buyer_name": buyer_name,
            "amount_without_vat": russian_money(subtotal),
            "vat_rate": "20%",
            "vat_amount": russian_money(vat_amount),
            "total_amount": russian_money(total),
            "currency": "RUB",
        }
        text = render_layout(layout, raw_fields)
        if split == "stress":
            text = add_stress_noise(text, randomizer)

        cases.append(
            EvaluationCase(
                case_id=f"invoice-{index + 1:03d}",
                split=split,
                layout=layout,
                text=text,
                expected_doc_type="invoice",
                expected_fields=normalize_expected(raw_fields),
            )
        )
    return cases


def write_dataset(cases: list[EvaluationCase], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as target:
        for case in cases:
            target.write(json.dumps(asdict(case), ensure_ascii=False, sort_keys=True) + "\n")


def read_dataset(path: Path) -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            payload = json.loads(line)
            cases.append(EvaluationCase(**payload))
    return cases


def evaluate_dataset(
    cases: list[EvaluationCase],
    *,
    schema: dict[str, Any],
    target_precision: float = 0.98,
) -> dict[str, object]:
    predictions = [(case, baseline_predict(case.text, schema)) for case in cases]
    split_names = ("development", "holdout", "stress")
    splits = {
        split: calculate_metrics(
            [(case, prediction) for case, prediction in predictions if case.split == split],
            schema=schema,
            threshold=0.85,
        )
        for split in split_names
    }
    curve = [
        {
            "threshold": threshold,
            **calculate_acceptance(predictions, schema=schema, threshold=threshold),
        }
        for threshold in (0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)
    ]
    eligible = [point for point in curve if float(point["precision"]) >= target_precision]
    recommended = max(eligible, key=lambda point: float(point["coverage"]), default=curve[-1])
    overall = calculate_metrics(
        predictions, schema=schema, threshold=float(recommended["threshold"])
    )
    return {
        "dataset_version": "invoice-synthetic-v1",
        "model_version": "deterministic-baseline-v1",
        "generated_at": date.today().isoformat(),
        "case_count": len(cases),
        "target_precision": target_precision,
        "recommended_threshold": recommended["threshold"],
        "overall": overall,
        "splits": splits,
        "threshold_curve": curve,
    }


def write_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def baseline_predict(text: str, schema: dict[str, Any]) -> BaselinePrediction:
    lowered = text.casefold()
    if "счет" in lowered or "счёт" in lowered:
        document_type: str | None = "invoice"
        confidence = 0.96
    elif "платежный документ" in lowered:
        document_type = "invoice"
        confidence = 0.86
    else:
        document_type = None
        confidence = 0.55
    stress_markers = ("п0ставщик", "ит0го", "покупатепь", "   ")
    if any(marker in lowered for marker in stress_markers):
        confidence -= 0.32

    supplier_inn = find_value(
        text,
        (r"(?:Поставщик|Продавец|От кого)[^\n]*?ИНН\s*[:№]?\s*(\d{10,12})",),
    )
    buyer_inn = find_value(
        text,
        (r"(?:Покупатель|Заказчик|Для кого)[^\n]*?ИНН\s*[:№]?\s*(\d{10,12})",),
    )
    raw_fields: dict[str, object] = {
        "doc_number": find_value(
            text, (r"[№#]\s*([A-ZА-Я0-9-]+)", r"номер\s*[:№]?\s*([A-ZА-Я0-9-]+)")
        ),
        "doc_date": find_value(text, (r"(?:от|дата)\s*[:]?\s*(\d{2}[./]\d{2}[./]\d{4})",)),
        "supplier_inn": supplier_inn,
        "supplier_name": find_value(text, (r"(?:Поставщик|Продавец|От кого)\s*[:]\s*([^;|\n]+)",)),
        "buyer_inn": buyer_inn,
        "buyer_name": find_value(text, (r"(?:Покупатель|Заказчик|Для кого)\s*[:]\s*([^;|\n]+)",)),
        "amount_without_vat": find_value(
            text, (r"(?:Сумма без НДС|Без НДС|Подытог)\s*[:]\s*([\d\s]+[,.]\d{2})",)
        ),
        "vat_rate": find_value(text, (r"НДС\s*[:]?\s*(\d{1,2}\s*%)", r"НДС\s*(\d{1,2}\s*%)")),
        "vat_amount": find_value(text, (r"НДС[^\n|;]*?([\d\s]+[,.]\d{2})",)),
        "total_amount": find_value(
            text, (r"(?:Итого к оплате|Итого|Всего)\s*[:]\s*([\d\s]+[,.]\d{2})",)
        ),
        "currency": "RUB" if "RUB" in text.upper() or "РУБ" in text.upper() else None,
    }
    return BaselinePrediction(
        document_type=document_type,
        confidence=max(0.0, confidence),
        raw_fields=raw_fields,
        fields=normalize_fields(raw_fields, schema),
    )


def calculate_metrics(
    pairs: list[tuple[EvaluationCase, BaselinePrediction]],
    *,
    schema: dict[str, Any],
    threshold: float,
) -> dict[str, object]:
    if not pairs:
        return empty_metrics()
    total_fields = len(pairs) * len(FIELD_KEYS)
    correct_fields = sum(
        predicted.fields.get(key) == case.expected_fields.get(key)
        for case, predicted in pairs
        for key in FIELD_KEYS
    )
    correct_critical = sum(
        predicted.fields.get(key) == case.expected_fields.get(key)
        for case, predicted in pairs
        for key in CRITICAL_FIELDS
    )
    grounded_values = 0
    predicted_critical = 0
    for case, prediction in pairs:
        for key in CRITICAL_FIELDS:
            value = prediction.raw_fields.get(key)
            if value not in {None, ""}:
                predicted_critical += 1
                grounded_values += compact(value) in compact(case.text)
    acceptance = calculate_acceptance(pairs, schema=schema, threshold=threshold)
    return {
        "case_count": len(pairs),
        "classification_accuracy": round(
            sum(pred.document_type == case.expected_doc_type for case, pred in pairs) / len(pairs),
            4,
        ),
        "field_accuracy": round(correct_fields / total_fields, 4),
        "critical_field_accuracy": round(correct_critical / (len(pairs) * len(CRITICAL_FIELDS)), 4),
        "grounding_rate": round(grounded_values / predicted_critical, 4)
        if predicted_critical
        else 0.0,
        "stp_rate": acceptance["coverage"],
        "stp_precision": acceptance["precision"],
    }


def calculate_acceptance(
    pairs: list[tuple[EvaluationCase, BaselinePrediction]],
    *,
    schema: dict[str, Any],
    threshold: float,
) -> dict[str, float | int]:
    accepted = 0
    accepted_correct = 0
    for case, prediction in pairs:
        checks = validate_invoice(
            fields=prediction.fields,
            raw_fields=prediction.raw_fields,
            schema=schema,
            source_text=case.text,
        )
        valid = all(bool(item["passed"]) for item in checks)
        if (
            valid
            and prediction.document_type == case.expected_doc_type
            and prediction.confidence >= threshold
        ):
            accepted += 1
            if all(
                prediction.fields.get(key) == case.expected_fields.get(key) for key in FIELD_KEYS
            ):
                accepted_correct += 1
    total = len(pairs)
    return {
        "accepted": accepted,
        "coverage": round(accepted / total, 4) if total else 0.0,
        "precision": round(accepted_correct / accepted, 4) if accepted else 1.0,
    }


def empty_metrics() -> dict[str, object]:
    return {
        "case_count": 0,
        "classification_accuracy": 0.0,
        "field_accuracy": 0.0,
        "critical_field_accuracy": 0.0,
        "grounding_rate": 0.0,
        "stp_rate": 0.0,
        "stp_precision": 0.0,
    }


def render_layout(layout: str, fields: dict[str, Any]) -> str:
    if layout == "classic":
        return (
            f"Счёт на оплату № {fields['doc_number']} от {fields['doc_date']}\n"
            f"Поставщик: {fields['supplier_name']}; ИНН {fields['supplier_inn']}\n"
            f"Покупатель: {fields['buyer_name']}; ИНН {fields['buyer_inn']}\n"
            f"Сумма без НДС: {fields['amount_without_vat']} RUB\n"
            f"НДС {fields['vat_rate']}: {fields['vat_amount']} RUB\n"
            f"Итого к оплате: {fields['total_amount']} RUB"
        )
    if layout == "compact":
        return (
            f"Счет №{fields['doc_number']} | дата: {fields['doc_date']}\n"
            f"Продавец: {fields['supplier_name']} | ИНН: {fields['supplier_inn']}\n"
            f"Заказчик: {fields['buyer_name']} | ИНН: {fields['buyer_inn']}\n"
            f"Подытог: {fields['amount_without_vat']} RUB | НДС: {fields['vat_rate']} "
            f"{fields['vat_amount']} RUB | Всего: {fields['total_amount']} RUB"
        )
    return (
        f"ПЛАТЕЖНЫЙ ДОКУМЕНТ, номер: {fields['doc_number']}, дата: {fields['doc_date']}\n"
        f"От кого: {fields['supplier_name']}; ИНН {fields['supplier_inn']}\n"
        f"Для кого: {fields['buyer_name']}; ИНН {fields['buyer_inn']}\n"
        f"Без НДС: {fields['amount_without_vat']} RUB\n"
        f"НДС {fields['vat_rate']}: {fields['vat_amount']} RUB\n"
        f"Итого: {fields['total_amount']} RUB"
    )


def add_stress_noise(text: str, randomizer: random.Random) -> str:
    replacements = [
        ("Поставщик", "П0ставщик"),
        ("Итого", "Ит0го"),
        ("Покупатель", "Покупатепь"),
        ("Счёт", "Счет"),
    ]
    selected = randomizer.sample(replacements, k=2)
    for original, replacement in selected:
        text = text.replace(original, replacement)
    return text.replace(";", "  ").replace(" | ", "   ")


def normalize_expected(raw_fields: dict[str, Any]) -> dict[str, object]:
    schema = {
        "fields": [
            {"key": key, "type": field_type}
            for key, field_type in (
                ("doc_number", "string"),
                ("doc_date", "date"),
                ("supplier_inn", "inn"),
                ("supplier_name", "string"),
                ("buyer_inn", "inn"),
                ("buyer_name", "string"),
                ("amount_without_vat", "money"),
                ("vat_rate", "percent"),
                ("vat_amount", "money"),
                ("total_amount", "money"),
                ("currency", "currency"),
            )
        ]
    }
    return normalize_fields(raw_fields, schema)


def find_value(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def russian_money(value: Decimal) -> str:
    whole, fraction = f"{value:.2f}".split(".")
    grouped = f"{int(whole):,}".replace(",", " ")
    return f"{grouped},{fraction}"

from docflow.ai.deterministic import extract_document_fields

RUSSIAN_OCR_TEXT = """
СЧЕТ НА ОПЛАТУ
Дата 21.09.2026
Номер документа 1047
Поставщик: ООО "ТехСнаб Сервис" Покупатель: ООО "Альфа Логистик"
ИНН: 7704123456 ИНН: 7722334455
Итого: 120 000,00 руб.
В том числе НДС 20%: 20 000,00 руб.
Итоговая сумма к оплате: 120 000,00 руб.
"""


def test_extracts_fields_from_actual_russian_ocr_text() -> None:
    fields = extract_document_fields(RUSSIAN_OCR_TEXT, "invoice")

    assert fields == {
        "doc_number": "1047",
        "doc_date": "21.09.2026",
        "supplier_inn": "7704123456",
        "supplier_name": 'ООО "ТехСнаб Сервис"',
        "buyer_inn": "7722334455",
        "buyer_name": 'ООО "Альфа Логистик"',
        "amount_without_vat": "100000.00",
        "vat_rate": "20",
        "vat_amount": "20 000,00",
        "total_amount": "120 000,00",
        "currency": "RUB",
    }


def test_missing_fields_are_not_borrowed_from_a_fixture() -> None:
    fields = extract_document_fields("СЧЕТ НА ОПЛАТУ № 900", "invoice")

    assert fields["doc_number"] == "900"
    assert fields["supplier_inn"] is None
    assert fields["total_amount"] is None


def test_understands_english_demo_document() -> None:
    text = """
    INVOICE 42
    Date: 19.09.2026
    Supplier: Sever LLC, INN 7707083893
    Buyer: Mayak LLC, INN 7736050003
    Subtotal: 1 000,00 RUB
    VAT 20%: 200,00 RUB
    Total: 1 200,00 RUB
    """

    fields = extract_document_fields(text, "invoice")

    assert fields["doc_number"] == "42"
    assert fields["supplier_name"] == "Sever LLC, INN 7707083893"
    assert fields["buyer_name"] == "Mayak LLC, INN 7736050003"
    assert fields["total_amount"] == "1 200,00"

import io
import zipfile

from docflow.infrastructure.export import EXPORT_COLUMNS, render_csv, render_xlsx


def sample_rows() -> list[dict[str, object]]:
    return [
        {
            "revision_id": "revision-1",
            "document_id": "document-1",
            "revision_number": 2,
            "schema_code": "invoice",
            "approved_at": "2026-09-21T10:00:00+00:00",
            "doc_number": "42",
            "supplier_name": "ООО Север",
            "total_amount": "1200",
            "currency": "RUB",
        }
    ]


def test_csv_export_contains_revision_identity_and_utf8() -> None:
    content = render_csv(sample_rows())

    assert content.startswith(b"\xef\xbb\xbf")
    decoded = content.decode("utf-8-sig")
    assert "revision_id" in decoded
    assert "revision-1" in decoded
    assert "ООО Север" in decoded


def test_xlsx_export_is_valid_ooxml_archive() -> None:
    content = render_xlsx(sample_rows())

    assert content.startswith(b"PK")
    with zipfile.ZipFile(io.BytesIO(content)) as workbook:
        assert "xl/workbook.xml" in workbook.namelist()
        sheet = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "revision-1" in sheet
    assert "ООО Север" in sheet
    assert "A1" in sheet
    assert len(EXPORT_COLUMNS) == 16

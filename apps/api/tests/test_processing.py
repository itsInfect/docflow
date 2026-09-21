from pathlib import Path

import pymupdf
from fastapi.testclient import TestClient
from PIL import Image

from docflow.core.config import Settings
from docflow.infrastructure.preprocessing import DocumentPreprocessor
from docflow.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    database_path = (tmp_path / "docflow.db").as_posix()
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{database_path}",
        storage_root=tmp_path / "storage",
        auto_create_schema=True,
    )
    return TestClient(create_app(settings))


def make_text_pdf(
    text: str = "Invoice number 42 from portfolio supplier, total amount 1200 RUB.",
) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_textbox(
        pymupdf.Rect(72, 72, 520, 760),
        text,
    )
    content = document.tobytes()
    document.close()
    return content


def test_processing_run_extracts_pdf_text_and_is_versioned(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("invoice.pdf", make_text_pdf(), "application/pdf")},
        )
        document_id = upload.json()["id"]

        first_run = client.post(f"/api/v1/documents/{document_id}/process")
        second_run = client.post(f"/api/v1/documents/{document_id}/process")
        runs = client.get(f"/api/v1/documents/{document_id}/runs")
        revisions = client.get(f"/api/v1/documents/{document_id}/revisions")
        document = client.get(f"/api/v1/documents/{document_id}")

    assert first_run.status_code == 200
    assert first_run.json()["status"] == "succeeded"
    assert first_run.json()["run_number"] == 1
    assert first_run.json()["page_count"] == 1
    assert first_run.json()["text_layer_pages"] == 1
    assert first_run.json()["text_char_count"] > 20

    assert second_run.status_code == 200
    assert second_run.json()["run_number"] == 2
    assert runs.json()["total"] == 2
    assert [item["run_number"] for item in runs.json()["items"]] == [2, 1]
    assert revisions.json()["total"] == 2
    assert [item["revision_number"] for item in revisions.json()["items"]] == [2, 1]
    assert revisions.json()["items"][0]["status"] == "needs_review"
    assert document.json()["status"] == "needs_review"
    assert document.json()["page_count"] == 1
    assert len(list((tmp_path / "storage" / "derived").rglob("page-0001.png"))) == 2


def test_preprocessor_routes_image_to_ocr_when_engine_is_missing(tmp_path: Path) -> None:
    source = tmp_path / "scan.png"
    Image.new("RGB", (320, 180), "white").save(source)

    result = DocumentPreprocessor().process(
        source=source,
        mime_type="image/png",
        output_dir=tmp_path / "derived",
    )

    assert result.page_count == 1
    assert result.ocr_pages == 0
    assert result.ocr_pending_pages == 1
    assert (tmp_path / "derived" / "page-0001.png").exists()


def test_exact_duplicate_cannot_start_independent_processing(tmp_path: Path) -> None:
    content = make_text_pdf()
    with make_client(tmp_path) as client:
        original = client.post(
            "/api/v1/documents",
            files={"file": ("invoice.pdf", content, "application/pdf")},
        )
        duplicate = client.post(
            "/api/v1/documents",
            files={"file": ("copy.pdf", content, "application/pdf")},
        )
        response = client.post(f"/api/v1/documents/{duplicate.json()['id']}/process")

    assert original.status_code == 201
    assert duplicate.json()["status"] == "duplicate_file"
    assert response.status_code == 409


def test_grounded_valid_revision_is_auto_approved(tmp_path: Path) -> None:
    grounded_text = (
        "Invoice 42. Date: 19.09.2026. Supplier: Sever LLC, INN 7707083893. "
        "Buyer: Mayak LLC, INN 7736050003. "
        "Subtotal 1 000,00 VAT 20% 200,00 Total 1 200,00 RUB."
    )
    with make_client(tmp_path) as client:
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("grounded.pdf", make_text_pdf(grounded_text), "application/pdf")},
        )
        document_id = upload.json()["id"]
        run = client.post(f"/api/v1/documents/{document_id}/process")
        revisions = client.get(f"/api/v1/documents/{document_id}/revisions")
        document = client.get(f"/api/v1/documents/{document_id}")

    revision = revisions.json()["items"][0]
    assert run.json()["status"] == "succeeded"
    assert revision["status"] == "approved"
    assert revision["is_valid"] is True
    assert revision["fields_json"]["supplier_inn"] == "7707083893"
    assert revision["fields_json"]["total_amount"] == "1200"
    assert all(item["passed"] for item in revision["validation_json"])
    assert document.json()["status"] == "approved"


def test_operator_correction_creates_revision_and_can_be_approved(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("review.pdf", make_text_pdf(), "application/pdf")},
        )
        document_id = upload.json()["id"]
        client.post(f"/api/v1/documents/{document_id}/process")
        original = client.get(f"/api/v1/documents/{document_id}/revisions").json()["items"][0]

        correction = client.post(
            f"/api/v1/documents/{document_id}/revisions/{original['id']}/corrections",
            json={"fields": {"doc_number": "43"}},
        )
        corrected = correction.json()
        approval = client.post(
            f"/api/v1/documents/{document_id}/revisions/{corrected['id']}/approve",
            json={"reason": "Сверено оператором с оригиналом"},
        )
        revisions = client.get(f"/api/v1/documents/{document_id}/revisions").json()
        document = client.get(f"/api/v1/documents/{document_id}").json()

    assert correction.status_code == 201
    assert corrected["revision_number"] == 2
    assert corrected["fields_json"]["doc_number"] == "43"
    assert original["fields_json"]["doc_number"] == "42"
    assert approval.status_code == 200
    assert approval.json()["status"] == "approved"
    assert revisions["total"] == 2
    assert document["status"] == "approved"


def test_business_duplicate_is_routed_to_review(tmp_path: Path) -> None:
    grounded_text = (
        "Invoice 42 dated 19.09.2026. Supplier INN 7707083893. "
        "Subtotal 1 000,00 VAT 20% 200,00 Total 1 200,00 RUB."
    )
    with make_client(tmp_path) as client:
        first = client.post(
            "/api/v1/documents",
            files={"file": ("first.pdf", make_text_pdf(grounded_text), "application/pdf")},
        ).json()
        second = client.post(
            "/api/v1/documents",
            files={
                "file": (
                    "second.pdf",
                    make_text_pdf(grounded_text + " Copy rendered from another source."),
                    "application/pdf",
                )
            },
        ).json()
        client.post(f"/api/v1/documents/{first['id']}/process")
        client.post(f"/api/v1/documents/{second['id']}/process")
        revision = client.get(f"/api/v1/documents/{second['id']}/revisions").json()["items"][0]
        second_document = client.get(f"/api/v1/documents/{second['id']}").json()

    duplicate_checks = [
        item for item in revision["validation_json"] if item["code"] == "business_duplicate"
    ]
    assert duplicate_checks
    assert duplicate_checks[0]["passed"] is False
    assert revision["status"] == "needs_review"
    assert second_document["status"] == "needs_review"


def test_service_act_uses_its_own_versioned_schema(tmp_path: Path) -> None:
    source_text = (
        "SERVICE ACT 17 dated 20.09.2026. Contractor INN 7801234567. "
        "Subtotal 25 000,00 VAT 20% 5 000,00 Total 30 000,00 RUB."
    )
    with make_client(tmp_path) as client:
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("service-act.pdf", make_text_pdf(source_text), "application/pdf")},
        ).json()
        response = client.post(f"/api/v1/documents/{upload['id']}/process")
        document = client.get(f"/api/v1/documents/{upload['id']}").json()
        revision = client.get(f"/api/v1/documents/{upload['id']}/revisions").json()["items"][0]

    assert response.status_code == 200
    assert document["doc_type"] == "service_act"
    assert revision["schema_code"] == "service_act"
    assert revision["schema_version"] == 1
    assert revision["extraction_model"] == "local/service_act-deterministic-v1"

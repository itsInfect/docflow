from pathlib import Path

from fastapi.testclient import TestClient

from docflow.core.config import Settings
from docflow.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    database_path = (tmp_path / "docflow.db").as_posix()
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{database_path}",
        storage_root=tmp_path / "storage",
        auto_create_schema=True,
    )
    return TestClient(create_app(settings))


def test_upload_list_and_exact_duplicate(tmp_path: Path) -> None:
    file_bytes = b"%PDF-1.4\nportfolio document\n%%EOF"

    with make_client(tmp_path) as client:
        first = client.post(
            "/api/v1/documents",
            files={"file": ("invoice.pdf", file_bytes, "application/octet-stream")},
        )
        duplicate = client.post(
            "/api/v1/documents",
            files={"file": ("copy.exe", file_bytes, "application/x-msdownload")},
        )
        listing = client.get("/api/v1/documents")

    assert first.status_code == 201
    assert first.json()["mime_type"] == "application/pdf"
    assert first.json()["status"] == "uploaded"

    assert duplicate.status_code == 201
    assert duplicate.json()["status"] == "duplicate_file"
    assert duplicate.json()["is_duplicate_of"] == first.json()["id"]

    assert listing.status_code == 200
    assert listing.json()["total"] == 2


def test_upload_rejects_content_with_fake_extension(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/v1/documents",
            files={"file": ("invoice.pdf", b"not really a pdf", "application/pdf")},
        )

    assert response.status_code == 415


def test_operator_can_resolve_exact_duplicate(tmp_path: Path) -> None:
    content = b"%PDF-1.4\nportfolio duplicate\n%%EOF"
    with make_client(tmp_path) as client:
        client.post(
            "/api/v1/documents",
            files={"file": ("original.pdf", content, "application/pdf")},
        )
        duplicate = client.post(
            "/api/v1/documents",
            files={"file": ("copy.pdf", content, "application/pdf")},
        ).json()
        decision = client.post(
            f"/api/v1/documents/{duplicate['id']}/duplicate-decision",
            json={"decision": "reject"},
        )
        processing = client.post(f"/api/v1/documents/{duplicate['id']}/process")

    assert decision.status_code == 200
    assert decision.json()["status"] == "rejected"
    assert decision.json()["is_duplicate_of"] is not None
    assert processing.status_code == 409


def test_audit_returns_status_history_with_actor_and_reason(tmp_path: Path) -> None:
    content = b"%PDF-1.4\nportfolio audit\n%%EOF"
    with make_client(tmp_path) as client:
        original = client.post(
            "/api/v1/documents",
            files={"file": ("original.pdf", content, "application/pdf")},
        ).json()
        duplicate = client.post(
            "/api/v1/documents",
            files={"file": ("copy.pdf", content, "application/pdf")},
        ).json()
        client.post(
            f"/api/v1/documents/{duplicate['id']}/duplicate-decision",
            json={"decision": "reject"},
        )
        response = client.get("/api/v1/audit/events")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    events = response.json()["items"]
    rejection = next(item for item in events if item["to_status"] == "rejected")
    assert rejection["document_id"] == duplicate["id"]
    assert rejection["original_filename"] == "copy.pdf"
    assert rejection["actor_type"] == "operator"
    assert rejection["reason"] == "Operator rejected exact duplicate"
    assert any(item["document_id"] == original["id"] for item in events)

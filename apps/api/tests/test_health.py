from pathlib import Path

from fastapi.testclient import TestClient

from docflow.core.config import Settings
from docflow.main import create_app


def test_health(tmp_path: Path) -> None:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        storage_root=tmp_path / "storage",
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/health")
        readiness = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "docflow-api"
    assert readiness.status_code == 200

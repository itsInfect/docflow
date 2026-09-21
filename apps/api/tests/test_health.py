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
        capabilities = client.get("/api/v1/capabilities")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "docflow-api"
    assert readiness.status_code == 200
    assert capabilities.status_code == 200
    assert capabilities.json()["llm_provider"] == "mock"
    assert capabilities.json()["document_types"] == ["invoice", "service_act"]
    assert capabilities.json()["max_upload_size_mb"] == 20


def test_serves_web_app_and_spa_routes(tmp_path: Path) -> None:
    web_root = tmp_path / "web"
    assets_root = web_root / "assets"
    assets_root.mkdir(parents=True)
    (web_root / "index.html").write_text("<main>Docflow</main>", encoding="utf-8")
    (assets_root / "app.js").write_text("window.docflow = true", encoding="utf-8")
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        storage_root=tmp_path / "storage",
        web_dist_root=web_root,
    )

    with TestClient(create_app(settings)) as client:
        home = client.get("/")
        spa_route = client.get("/settings")
        asset = client.get("/assets/app.js")
        health = client.get("/api/v1/health")
        missing_api_route = client.get("/api/v1/missing")

    assert home.status_code == 200
    assert home.text == "<main>Docflow</main>"
    assert spa_route.status_code == 200
    assert spa_route.text == "<main>Docflow</main>"
    assert asset.status_code == 200
    assert asset.text == "window.docflow = true"
    assert health.status_code == 200
    assert missing_api_route.status_code == 404
    assert missing_api_route.json() == {"detail": "Not found"}

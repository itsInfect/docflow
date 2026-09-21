from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from docflow.core.config import Settings
from docflow.evaluation import evaluate_dataset, generate_invoice_dataset
from docflow.main import create_app


def load_invoice_schema() -> dict[str, object]:
    schema_path = Path(__file__).parents[3] / "schemas" / "invoice" / "v1.yaml"
    with schema_path.open(encoding="utf-8") as source:
        payload = yaml.safe_load(source)
    assert isinstance(payload, dict)
    return payload


def test_dataset_generation_and_evaluation_are_reproducible() -> None:
    first = generate_invoice_dataset()
    second = generate_invoice_dataset()
    report = evaluate_dataset(first, schema=load_invoice_schema())

    assert first == second
    assert len(first) == 30
    assert {case.split for case in first} == {"development", "holdout", "stress"}
    assert {case.layout for case in first} == {"classic", "compact", "ledger"}
    assert report["case_count"] == 30
    assert 0 <= float(report["recommended_threshold"]) <= 1
    overall = report["overall"]
    assert isinstance(overall, dict)
    assert 0 <= float(overall["field_accuracy"]) <= 1
    assert 0 <= float(overall["stp_precision"]) <= 1


def test_quality_api_creates_real_report(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{(tmp_path / 'docflow.db').as_posix()}",
        storage_root=tmp_path / "storage",
        evaluation_dataset_path=tmp_path / "dataset.jsonl",
        evaluation_report_path=tmp_path / "report.json",
        auto_create_schema=True,
    )
    with TestClient(create_app(settings)) as client:
        before = client.get("/api/v1/quality/report")
        generated = client.post("/api/v1/quality/run")
        after = client.get("/api/v1/quality/report")

    assert before.json() == {"available": False}
    assert generated.status_code == 200
    assert generated.json()["available"] is True
    assert generated.json()["case_count"] == 30
    assert after.json()["overall"] == generated.json()["overall"]
    assert settings.evaluation_dataset_path.exists()
    assert settings.evaluation_report_path.exists()


@pytest.mark.parametrize("count", [0, 9])
def test_tiny_evaluation_dataset_is_rejected(count: int) -> None:
    with pytest.raises(ValueError, match="at least 10"):
        generate_invoice_dataset(count=count)

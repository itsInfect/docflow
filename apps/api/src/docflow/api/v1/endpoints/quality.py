from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request

from docflow.core.config import Settings
from docflow.evaluation import (
    evaluate_dataset,
    generate_invoice_dataset,
    write_dataset,
    write_report,
)
from docflow.infrastructure.document_types import DocumentTypeCatalog

router = APIRouter(prefix="/quality")


@router.get("/report")
async def get_quality_report(request: Request) -> dict[str, object]:
    settings: Settings = request.app.state.settings
    if not settings.evaluation_report_path.exists():
        return {"available": False}
    payload: dict[str, Any] = json.loads(
        settings.evaluation_report_path.read_text(encoding="utf-8")
    )
    return {"available": True, **payload}


@router.post("/run")
async def run_quality_evaluation(request: Request) -> dict[str, object]:
    settings: Settings = request.app.state.settings
    catalog = DocumentTypeCatalog(
        schemas_root=settings.schemas_root,
        prompts_root=settings.prompts_root,
    )
    definition = catalog.load("invoice")
    cases = generate_invoice_dataset()
    report = evaluate_dataset(cases, schema=definition.schema)
    write_dataset(cases, settings.evaluation_dataset_path)
    write_report(report, settings.evaluation_report_path)
    return {"available": True, **report}

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docflow.ai.base import ClassificationResult, ExtractionResult
from docflow.ai.deterministic import extract_document_fields


class LocalDemoProvider:
    """Offline provider that extracts fields from the current document text."""

    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self._responses = responses
        self._selected_type = "invoice"

    @classmethod
    def from_directory(cls, root: Path) -> LocalDemoProvider:
        responses: dict[str, dict[str, Any]] = {}
        for code in ("invoice", "service_act"):
            path = root / f"{code}-v1.json"
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    responses[code] = payload
        return cls(responses)

    async def classify(self, *, text: str) -> ClassificationResult:
        lowered = text.casefold()
        if "акт выполненных работ" in lowered or "service act" in lowered:
            self._selected_type = "service_act"
        else:
            self._selected_type = "invoice"
        response = self._responses.get(self._selected_type, {}).get("classification", {})
        return ClassificationResult(
            document_type=self._selected_type,
            confidence=float(response.get("confidence", 0.95)),
            raw_response=dict(response),
        )

    async def extract(
        self,
        *,
        text: str,
        schema: dict[str, Any],
        prompt: str,
    ) -> ExtractionResult:
        fields = extract_document_fields(text, self._selected_type)
        return ExtractionResult(
            fields=fields,
            model=f"local/{self._selected_type}-deterministic-v1",
            raw_response={"fields": fields},
        )

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from docflow.ai.base import ClassificationResult, ExtractionResult


class MockProvider:
    """Deterministic provider backed by recorded responses."""

    def __init__(self, responses: Mapping[str, dict[str, Any]] | None = None) -> None:
        self._responses = dict(responses or {})

    @classmethod
    def from_file(cls, path: Path) -> MockProvider:
        if not path.exists():
            return cls()
        with path.open(encoding="utf-8") as source:
            payload = json.load(source)
        if not isinstance(payload, dict):
            raise ValueError("Recorded LLM response must contain a JSON object")
        return cls(payload)

    async def classify(self, *, text: str) -> ClassificationResult:
        response = self._responses.get("classification", {})
        return ClassificationResult(
            document_type=response.get("document_type", "invoice"),
            confidence=float(response.get("confidence", 1.0)),
            raw_response=response,
        )

    async def extract(
        self,
        *,
        text: str,
        schema: dict[str, Any],
        prompt: str,
    ) -> ExtractionResult:
        response = self._responses.get("extraction", {"fields": {}})
        return ExtractionResult(
            fields=dict(response.get("fields", {})),
            model="mock/recorded-v1",
            raw_response=response,
        )

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from docflow.ai.base import ClassificationResult, ExtractionResult


class MockProvider:
    """Deterministic provider backed by recorded responses."""

    def __init__(self, responses: Mapping[str, dict[str, Any]] | None = None) -> None:
        self._responses = dict(responses or {})

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

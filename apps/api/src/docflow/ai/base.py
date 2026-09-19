from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    document_type: str | None
    confidence: float
    raw_response: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    fields: dict[str, Any]
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    raw_response: dict[str, Any] | None = None


class LLMProvider(Protocol):
    async def classify(self, *, text: str) -> ClassificationResult: ...

    async def extract(
        self,
        *,
        text: str,
        schema: dict[str, Any],
        prompt: str,
    ) -> ExtractionResult: ...

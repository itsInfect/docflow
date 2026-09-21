from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from anthropic import AsyncAnthropic

from docflow.ai.base import ClassificationResult, ExtractionResult


class AnthropicProvider:
    """Optional live provider. Demo mode remains the dependency-free default."""

    def __init__(self, *, api_key: str, model: str) -> None:
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def classify(self, *, text: str) -> ClassificationResult:
        payload, _, _, _ = await self._request_json(
            system=(
                "Classify an accounting document. Return JSON only with document_type "
                "(invoice, service_act, or null) and confidence from 0 to 1."
            ),
            prompt=text[:20_000],
            max_tokens=200,
        )
        document_type = payload.get("document_type")
        if document_type not in {"invoice", "service_act"}:
            document_type = None
        return ClassificationResult(
            document_type=document_type,
            confidence=max(0.0, min(1.0, float(payload.get("confidence", 0.0)))),
            raw_response=payload,
        )

    async def extract(
        self,
        *,
        text: str,
        schema: dict[str, Any],
        prompt: str,
    ) -> ExtractionResult:
        payload, tokens_in, tokens_out, latency_ms = await self._request_json(
            system=(
                "Extract fields according to the supplied instructions. Return JSON only. "
                "Never invent a value that is absent from the document."
            ),
            prompt=(
                f"{prompt}\n\nRequired schema:\n"
                f"{json.dumps(schema, ensure_ascii=False, separators=(',', ':'))}"
            ),
            max_tokens=1_500,
        )
        fields = payload.get("fields", payload)
        if not isinstance(fields, dict):
            raise ValueError("AI extraction response does not contain a fields object")
        return ExtractionResult(
            fields=fields,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            raw_response=payload,
        )

    async def _request_json(
        self,
        *,
        system: str,
        prompt: str,
        max_tokens: int,
    ) -> tuple[dict[str, Any], int, int, int]:
        started = perf_counter()
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = round((perf_counter() - started) * 1_000)
        text = "".join(
            str(getattr(block, "text", ""))
            for block in response.content
            if getattr(block, "type", None) == "text"
        )
        payload = _parse_json_object(text)
        return (
            payload,
            int(response.usage.input_tokens),
            int(response.usage.output_tokens),
            latency_ms,
        )


def _parse_json_object(value: str) -> dict[str, Any]:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("AI response does not contain a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("AI response JSON must be an object")
    return payload

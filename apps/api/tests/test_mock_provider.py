import pytest

from docflow.ai.mock import MockProvider


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic() -> None:
    provider = MockProvider(
        {
            "classification": {"document_type": "invoice", "confidence": 0.99},
            "extraction": {"fields": {"doc_number": "42"}},
        }
    )

    classification = await provider.classify(text="ignored")
    extraction = await provider.extract(text="ignored", schema={}, prompt="ignored")

    assert classification.document_type == "invoice"
    assert extraction.fields == {"doc_number": "42"}

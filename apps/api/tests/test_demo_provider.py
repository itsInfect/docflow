from pathlib import Path

import pytest

from docflow.ai.demo import LocalDemoProvider


@pytest.mark.asyncio
async def test_demo_provider_selects_document_fixture() -> None:
    fixtures = Path(__file__).parents[3] / "fixtures" / "llm"
    provider = LocalDemoProvider.from_directory(fixtures)

    text = "SERVICE ACT ACT-77 dated 20.09.2026"
    classification = await provider.classify(text=text)
    extraction = await provider.extract(text=text, schema={}, prompt="ignored")

    assert classification.document_type == "service_act"
    assert classification.confidence == 0.96
    assert extraction.fields["doc_number"] == "ACT-77"
    assert extraction.model == "local/service_act-deterministic-v1"

import pytest

from docflow.ai.anthropic_provider import _parse_json_object
from docflow.ai.demo import LocalDemoProvider
from docflow.ai.factory import build_llm_provider
from docflow.core.config import Settings


def test_provider_factory_uses_reproducible_demo_by_default() -> None:
    provider = build_llm_provider(Settings())

    assert isinstance(provider, LocalDemoProvider)


def test_live_provider_requires_explicit_credentials_and_model() -> None:
    with pytest.raises(ValueError, match="API_KEY"):
        build_llm_provider(Settings(llm_provider="anthropic"))


def test_json_parser_accepts_markdown_fence() -> None:
    assert _parse_json_object('```json\n{"fields": {"doc_number": "42"}}\n```') == {
        "fields": {"doc_number": "42"}
    }

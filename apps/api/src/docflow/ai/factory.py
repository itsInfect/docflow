from docflow.ai.anthropic_provider import AnthropicProvider
from docflow.ai.base import LLMProvider
from docflow.ai.demo import LocalDemoProvider
from docflow.core.config import Settings


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return LocalDemoProvider.from_directory(settings.llm_fixtures_root)
    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("DOCFLOW_ANTHROPIC_API_KEY is required for the Anthropic provider")
        if not settings.anthropic_model:
            raise ValueError("DOCFLOW_ANTHROPIC_MODEL is required for the Anthropic provider")
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

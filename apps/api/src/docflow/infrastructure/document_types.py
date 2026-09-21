from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template


@dataclass(frozen=True, slots=True)
class DocumentTypeDefinition:
    code: str
    version: int
    schema: dict[str, Any]
    prompt: str


class DocumentTypeCatalog:
    def __init__(self, *, schemas_root: Path, prompts_root: Path) -> None:
        self.schemas_root = schemas_root
        self.prompts_root = prompts_root

    def load(self, code: str, version: int = 1) -> DocumentTypeDefinition:
        schema_path = self.schemas_root / code / f"v{version}.yaml"
        if not schema_path.exists():
            raise ValueError(f"Document schema is not configured: {code}/v{version}")
        with schema_path.open(encoding="utf-8") as source:
            schema = yaml.safe_load(source)
        if not isinstance(schema, dict):
            raise ValueError(f"Document schema is invalid: {schema_path}")

        prompt_relative = schema.get("prompt")
        if not isinstance(prompt_relative, str):
            raise ValueError(f"Prompt is not configured for document type: {code}")
        prompt_path = self.prompts_root / prompt_relative
        return DocumentTypeDefinition(
            code=code,
            version=int(schema.get("version", version)),
            schema=schema,
            prompt=prompt_path.read_text(encoding="utf-8"),
        )

    @staticmethod
    def render_prompt(definition: DocumentTypeDefinition, *, document_text: str) -> str:
        return str(Template(definition.prompt).render(document_text=document_text))

from __future__ import annotations

import json

from docflow.core.config import Settings
from docflow.evaluation import (
    evaluate_dataset,
    generate_invoice_dataset,
    write_dataset,
    write_report,
)
from docflow.infrastructure.document_types import DocumentTypeCatalog


def main() -> None:
    settings = Settings()
    definition = DocumentTypeCatalog(
        schemas_root=settings.schemas_root,
        prompts_root=settings.prompts_root,
    ).load("invoice")
    cases = generate_invoice_dataset()
    report = evaluate_dataset(cases, schema=definition.schema)
    write_dataset(cases, settings.evaluation_dataset_path)
    write_report(report, settings.evaluation_report_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

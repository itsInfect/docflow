# Architecture

Docflow is a modular monolith with asynchronous workers. The HTTP API owns commands and queries, while Celery workers execute document-processing stages. PostgreSQL is the source of truth, MinIO stores original and derived files, and Redis is used as the task broker.

The initial dependency direction is:

```text
API / worker entrypoints
        |
application workflows
        |
domain types and policies
        |
infrastructure adapters (database, object storage, LLM, queue)
```

AI providers implement a small contract and return typed results. They do not decide whether a document is accepted. Acceptance belongs to deterministic policies operating on normalized extracted values, grounding evidence, and validation results.

## Result versioning

The approved result will be represented as an immutable document revision. Extractions, human corrections, line items, and validation results attach to a revision. A document points to its current revision. Exports reference the exact revision included and do not mutate the document lifecycle.

## Configuration boundary

A new document type can be added without Python changes only when it is composed from existing field types, normalizers, validators, and UI renderers. New primitives intentionally require code and tests.


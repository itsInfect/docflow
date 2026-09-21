# Architecture

Docflow is a modular monolith with explicit application, domain, and infrastructure boundaries.
The default local profile is deliberately self-contained: FastAPI and SQLite store workflow state,
the local filesystem stores original and derived files, and React provides the operator interface.
Docker is not required for the portfolio demonstration.

```text
React operator interface
          |
FastAPI commands and queries
          |
application workflows
          |
domain policies and validation
          |
database / storage / OCR / AI adapters
```

The included Compose profile describes a production-oriented evolution with PostgreSQL, Redis,
MinIO, and asynchronous workers. Those services are replaceable infrastructure adapters rather
than requirements hidden inside the domain logic.

## Processing path

1. The API validates the real file signature, streams the original to content-addressed storage,
   and detects exact SHA-256 duplicates.
2. Preprocessing renders page previews and extracts the PDF text layer. Image-only pages use local
   Tesseract OCR; unavailable OCR is represented as an explicit resumable state.
3. A provider classifies the document and returns schema-shaped fields. The default local provider
   deterministically parses the current OCR text; an opt-in Anthropic adapter implements the same
   contract.
4. Normalizers and deterministic policies check required fields, INNs, dates, VAT arithmetic,
   totals, supported currencies, source grounding, and business duplicate keys.
5. Safe results can pass straight through. Risky results enter the operator queue, where every
   correction creates a new immutable revision.
6. CSV/XLSX exports select the latest approved revision and retain document and revision IDs.

AI providers never decide whether a document is accepted. Acceptance belongs to deterministic
policies operating on normalized values, grounding evidence, validation results, and a calibrated
confidence threshold.

## Audit and versioning

Processing runs, result revisions, and status transitions are stored separately. Reprocessing or a
human correction appends history instead of overwriting it. The audit API exposes the actor, reason,
old status, new status, document, and timestamp for every transition.

## Configuration boundary

A document type can be added without changing the processing workflow when it is composed from
existing field types, normalizers, validators, and UI renderers. The invoice and service-act schemas
demonstrate this boundary. New validation primitives intentionally require code and tests.

## Quality evidence

The evaluation module generates development, holdout, and OCR-stress cases independently from the
local demo profiles. It reports classification accuracy, field and critical-field accuracy,
grounding, straight-through-processing coverage and precision, plus a threshold curve. This keeps
demo repeatability separate from quality claims.

# Docflow

Portfolio-grade workflow for extracting, validating, reviewing, and exporting data from Russian accounting documents.

The repository is intentionally built around an unreliable AI component: model output is grounded in source text, checked by deterministic rules, and routed to a human reviewer when risk is too high.

## Repository layout

```text
apps/api/              FastAPI, workers, domain and infrastructure
apps/web/              React operator interface
schemas/               Versioned document-type schemas
prompts/               Versioned extraction prompts
fixtures/llm/          Recorded model responses for demo mode
datasets/generated/    Generated documents (not committed by default)
docs/                  Architecture and delivery notes
scripts/               Local development helpers
```

## Local development

Install project-local dependencies once:

```powershell
.\scripts\bootstrap.ps1
```

The checked-in defaults are enough for health checks. Copy `.env.example` to `.env` when you need to override services or secrets. Then start the applications separately:

```powershell
cd apps/api
.\.venv\Scripts\Activate.ps1
uvicorn docflow.main:app --reload
```

```powershell
cd apps/web
npm run dev
```

The API is available at `http://localhost:8000`; Swagger UI is at `/docs`. The web app runs at `http://localhost:5173`.

The default development profile needs no external services. It stores metadata in `apps/api/storage/docflow.db` and document bytes below `apps/api/storage/originals/`. Both are ignored by Git. Uploaded content is checked by file signature rather than filename extension.

Run the current verification suite with:

```powershell
.\scripts\verify.ps1
```

Docker Compose configuration is included, but Docker must be installed separately before it can be used:

```text
docker compose up --build
```

## Current milestone

The first vertical slice accepts one PDF, JPEG, PNG, or TIFF file up to 20 MB. It streams the file into content-addressed local storage, persists metadata and a status transition, detects exact SHA-256 duplicates, and shows recent documents in the web interface.

The next slice will preprocess accepted files: determine PDF page count, extract the text layer, render page previews, and route image-only pages to OCR.

FROM node:22-alpine AS web-builder

WORKDIR /build/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DOCFLOW_ENVIRONMENT=portfolio \
    DOCFLOW_DATABASE_URL=sqlite+aiosqlite:////data/docflow.db \
    DOCFLOW_STORAGE_ROOT=/data/storage \
    DOCFLOW_WEB_DIST_ROOT=/app/web \
    DOCFLOW_SCHEMAS_ROOT=/app/schemas \
    DOCFLOW_PROMPTS_ROOT=/app/prompts \
    DOCFLOW_LLM_FIXTURES_ROOT=/app/fixtures/llm \
    DOCFLOW_EVALUATION_DATASET_PATH=/data/evaluation/invoice-eval.jsonl \
    DOCFLOW_EVALUATION_REPORT_PATH=/data/evaluation/quality-report.json

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       libgl1 \
       libglib2.0-0 \
       tesseract-ocr \
       tesseract-ocr-eng \
       tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/src ./src
RUN pip install .

COPY schemas ./schemas
COPY prompts ./prompts
COPY fixtures/llm ./fixtures/llm
COPY --from=web-builder /build/apps/web/dist ./web

RUN mkdir -p /data/storage /data/evaluation

EXPOSE 8000

CMD ["sh", "-c", "uvicorn docflow.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

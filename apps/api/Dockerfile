FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       libgl1 \
       libglib2.0-0 \
       tesseract-ocr \
       tesseract-ocr-eng \
       tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

EXPOSE 8000

CMD ["uvicorn", "docflow.main:app", "--host", "0.0.0.0", "--port", "8000"]


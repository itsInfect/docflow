# Roadmap

## Milestone 0 — foundation

- Repository and application skeleton
- API and web health checks
- Configuration and logging boundaries
- LLM provider protocol and deterministic mock
- Queue and migration scaffolding

## Milestone 1 — one complete document path

- [x] Upload one invoice PDF or image
- [x] Store the original and initial status transition
- [x] Detect an exact file duplicate
- [x] Show the upload flow and recent documents in the browser
- [x] Create a versioned processing run
- [x] Extract text from digital PDFs and route scans to optional local OCR
- [x] Render normalized page previews during preprocessing
- [x] Use deterministic extraction from the current document in demo mode
- [x] Normalize and validate critical invoice fields
- [x] Persist an immutable result revision
- [x] Review, correct, and approve in the browser

## Milestone 2 — evaluation and evidence

- [x] Generate independent invoice layouts
- [x] Split development, holdout, and stress datasets
- [x] Produce classification, extraction, grounding, and STP reports
- [x] Add calibrated acceptance thresholds

## Milestone 3 — portfolio polish

- [x] Batch progress and operational dashboard
- [x] CSV/XLSX exports referencing immutable revisions
- [x] Exact and business duplicate review
- [x] Additional document types built from established primitives
- [x] Demo profile and scripted walkthrough

## Milestone 4 — portfolio release

- [x] Automatic Windows Tesseract discovery and real image OCR verification
- [x] Runtime capabilities page backed by the API
- [x] Optional live Anthropic provider behind the same provider contract
- [x] Complete automated and live end-to-end verification

**Portfolio release status: complete.** Production-scale infrastructure remains deliberately
separated from this local product milestone.

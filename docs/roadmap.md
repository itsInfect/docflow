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
- [ ] Create a versioned processing run
- Extract text from digital PDFs, fall back to OCR for scans
- Use a recorded extraction response in demo mode
- Normalize and validate critical invoice fields
- Persist an immutable result revision
- Review, correct, and approve in the browser

## Milestone 2 — evaluation and evidence

- Generate independent invoice layouts
- Split development, holdout, and stress datasets
- Produce classification, extraction, grounding, and STP reports
- Add calibrated acceptance thresholds

## Milestone 3 — portfolio polish

- Batch progress and operational dashboard
- CSV/XLSX exports referencing immutable revisions
- Exact and business duplicate review
- Additional document types built from established primitives
- Demo profile and short recorded walkthrough

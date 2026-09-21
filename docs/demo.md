# Demo walkthrough

This scenario demonstrates the complete local product path without Docker, cloud services, or an
external AI account. The deterministic local provider reads each document's recognized text and
makes every run reproducible.

## Prepare

Start the API and web application as described in the root README, then create two clean demo PDFs:

```powershell
apps/api/.venv/Scripts/python.exe scripts/generate_demo_documents.py
```

Open `http://localhost:5173` and use the generated files from `fixtures/demo-documents/`. The
folder also contains `ocr-invoice-demo.png`, an image-only document for demonstrating real OCR.

You can verify the local OCR installation independently before the presentation:

```powershell
$env:PYTHONPATH="apps/api/src"
apps/api/.venv/Scripts/python.exe scripts/verify_ocr.py
```

## Five-minute product story

1. Upload both PDFs together. The batch widget shows individual progress and creates two document
   records.
2. Open **Documents** and run processing for each file. Docflow extracts the PDF text, classifies
   the invoice and service act, applies their versioned schemas, normalizes monetary values, checks
   INNs, VAT arithmetic, totals, dates, grounding, and duplicate keys.
3. Open **Review**. A low-confidence or failed rule would appear here. Edit a field to demonstrate
   that the original result remains immutable and a new human-authored revision is created.
4. Approve the reviewed revision, then return to **Documents** and download CSV or XLSX. The export
   contains the latest approved revision and its traceability identifiers.
5. Open **History** to show every system and operator transition with its reason. Upload the same PDF
   again to demonstrate the exact-duplicate decision; render a changed copy with the same business
   details to demonstrate business-duplicate routing.
6. Open **Quality** and run the evaluation. Explain the development, holdout, and OCR-stress splits,
   the critical-field accuracy, and why the recommended acceptance threshold targets precision
   rather than maximum automation.

## What this proves

- an end-to-end human-in-the-loop document workflow rather than a standalone AI prompt;
- deterministic validation around probabilistic extraction;
- immutable revisions and an auditable decision trail;
- schema-driven extension to a second document type;
- measurable quality and calibrated straight-through-processing decisions;
- practical batch input and finance-friendly CSV/XLSX output.

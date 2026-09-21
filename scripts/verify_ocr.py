from pathlib import Path
from tempfile import TemporaryDirectory

from docflow.infrastructure.preprocessing import (
    DocumentPreprocessor,
    TesseractOcrEngine,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "fixtures" / "demo-documents" / "ocr-invoice-demo.png"


def main() -> None:
    engine = TesseractOcrEngine(language="rus+eng")
    if not engine.is_available():
        raise SystemExit(
            "Tesseract was not found. Set DOCFLOW_TESSERACT_CMD if it is non-standard."
        )
    if not SOURCE.exists():
        raise SystemExit("Generate demo documents first: python scripts/generate_demo_documents.py")

    with TemporaryDirectory(prefix="docflow-ocr-") as temp_dir:
        result = DocumentPreprocessor(engine).process(
            source=SOURCE,
            mime_type="image/png",
            output_dir=Path(temp_dir),
        )

    required_fragments = ["INVOICE", "7707083893", "1200"]
    compact_text = result.text.replace(" ", "").replace(",", "")
    missing = [fragment for fragment in required_fragments if fragment not in compact_text]
    if missing:
        raise SystemExit(
            f"OCR finished, but expected fragments are missing: {missing}\n{result.text}"
        )
    print(f"OCR ready: {result.ocr_pages} page, {len(result.text)} characters")
    print(result.text)


if __name__ == "__main__":
    main()

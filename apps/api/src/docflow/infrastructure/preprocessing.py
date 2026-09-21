from __future__ import annotations

import io
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pymupdf
import pytesseract  # type: ignore[import-untyped]
from PIL import Image, ImageOps, ImageSequence

MIN_TEXT_LAYER_CHARS = 20
PREVIEW_MAX_SIZE = (1800, 1800)


class OcrEngine(Protocol):
    def is_available(self) -> bool: ...

    def extract(self, image: Image.Image) -> str: ...


class TesseractOcrEngine:
    def __init__(self, language: str = "rus+eng", command: Path | None = None) -> None:
        self.language = language
        self.command = resolve_tesseract_command(command)
        if self.command is not None:
            pytesseract.pytesseract.tesseract_cmd = str(self.command)

    def is_available(self) -> bool:
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            return False
        return True

    def installed_languages(self) -> list[str]:
        if not self.is_available():
            return []
        try:
            return sorted(str(language) for language in pytesseract.get_languages(config=""))
        except pytesseract.TesseractError:
            return []

    def extract(self, image: Image.Image) -> str:
        return str(pytesseract.image_to_string(image, lang=self.language)).strip()


def resolve_tesseract_command(configured: Path | None = None) -> Path | None:
    if configured is not None:
        expanded = configured.expanduser()
        return expanded if expanded.is_file() else None

    executable = shutil.which("tesseract")
    if executable:
        return Path(executable)

    if os.name != "nt":
        return None

    candidates = [
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        / "Tesseract-OCR"
        / "tesseract.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
        / "Tesseract-OCR"
        / "tesseract.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
    ]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


@dataclass(frozen=True, slots=True)
class PreprocessingResult:
    page_count: int
    text: str
    text_layer_pages: int
    ocr_pages: int
    ocr_pending_pages: int


class DocumentPreprocessor:
    def __init__(self, ocr: OcrEngine | None = None) -> None:
        self.ocr = ocr

    def process(self, *, source: Path, mime_type: str, output_dir: Path) -> PreprocessingResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        if mime_type == "application/pdf":
            return self._process_pdf(source, output_dir)
        if mime_type in {"image/jpeg", "image/png", "image/tiff"}:
            return self._process_image(source, output_dir)
        raise ValueError(f"Unsupported document MIME type: {mime_type}")

    def _process_pdf(self, source: Path, output_dir: Path) -> PreprocessingResult:
        pages: list[str] = []
        text_layer_pages = 0
        ocr_pages = 0
        ocr_pending_pages = 0

        with pymupdf.open(source) as document:  # type: ignore[no-untyped-call]
            if document.needs_pass:
                raise ValueError("Password-protected PDF documents are not supported")
            if document.page_count == 0:
                raise ValueError("PDF document has no pages")

            for index, page in enumerate(document):
                native_text = page.get_text("text").strip()
                matrix = pymupdf.Matrix(1.5, 1.5)  # type: ignore[no-untyped-call]
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                preview_path = output_dir / f"page-{index + 1:04d}.png"
                pixmap.save(preview_path)

                page_text = native_text
                if len(native_text) >= MIN_TEXT_LAYER_CHARS:
                    text_layer_pages += 1
                else:
                    image = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
                    ocr_text = self._ocr(image)
                    if ocr_text is None:
                        ocr_pending_pages += 1
                    else:
                        page_text = ocr_text
                        ocr_pages += 1
                pages.append(self._page_block(index + 1, page_text))

            page_count = document.page_count

        return PreprocessingResult(
            page_count=page_count,
            text="\n\n".join(pages).strip(),
            text_layer_pages=text_layer_pages,
            ocr_pages=ocr_pages,
            ocr_pending_pages=ocr_pending_pages,
        )

    def _process_image(self, source: Path, output_dir: Path) -> PreprocessingResult:
        pages: list[str] = []
        ocr_pages = 0
        ocr_pending_pages = 0

        with Image.open(source) as document:
            frames = [frame.copy() for frame in ImageSequence.Iterator(document)]

        if not frames:
            raise ValueError("Image document has no pages")

        for index, frame in enumerate(frames):
            normalized = ImageOps.exif_transpose(frame).convert("RGB")
            preview = normalized.copy()
            preview.thumbnail(PREVIEW_MAX_SIZE)
            preview.save(output_dir / f"page-{index + 1:04d}.png", format="PNG")
            ocr_text = self._ocr(normalized)
            if ocr_text is None:
                ocr_pending_pages += 1
                page_text = ""
            else:
                ocr_pages += 1
                page_text = ocr_text
            pages.append(self._page_block(index + 1, page_text))

        return PreprocessingResult(
            page_count=len(frames),
            text="\n\n".join(pages).strip(),
            text_layer_pages=0,
            ocr_pages=ocr_pages,
            ocr_pending_pages=ocr_pending_pages,
        )

    def _ocr(self, image: Image.Image) -> str | None:
        if self.ocr is None or not self.ocr.is_available():
            return None
        return self.ocr.extract(image)

    @staticmethod
    def _page_block(page_number: int, text: str) -> str:
        return f"--- page {page_number} ---\n{text.strip()}"

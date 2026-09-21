from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "fixtures" / "demo-documents"

DOCUMENTS = {
    "invoice-demo.pdf": (
        "INVOICE 42\n"
        "Date: 19.09.2026\n"
        "Supplier: Sever LLC, INN 7707083893\n"
        "Buyer: Mayak LLC, INN 7736050003\n"
        "Subtotal: 1 000,00 RUB\n"
        "VAT 20%: 200,00 RUB\n"
        "Total: 1 200,00 RUB"
    ),
    "service-act-demo.pdf": (
        "SERVICE ACT ACT-77\n"
        "Date: 20.09.2026\n"
        "Contractor: Sever LLC, INN 7707083893\n"
        "Customer: Mayak LLC, INN 7736050003\n"
        "Services subtotal: 25 000,00 RUB\n"
        "VAT 20%: 5 000,00 RUB\n"
        "Total: 30 000,00 RUB"
    ),
}

SCAN_TEXT = (
    "INVOICE 42\n"
    "Date: 19.09.2026\n"
    "Supplier INN: 7707083893\n"
    "Buyer INN: 7736050003\n"
    "Subtotal: 1 000,00 RUB\n"
    "VAT 20%: 200,00 RUB\n"
    "Total: 1 200,00 RUB"
)


def generate_pdf(path: Path, text: str) -> None:
    document = pymupdf.open()
    page = document.new_page(width=595, height=842)
    page.insert_textbox(
        pymupdf.Rect(72, 84, 523, 760),
        text,
        fontsize=13,
        lineheight=1.5,
    )
    document.save(path)
    document.close()


def generate_scan(path: Path, text: str) -> None:
    image = Image.new("RGB", (1654, 2339), "white")
    draw = ImageDraw.Draw(image)
    font_candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    font_path = next((item for item in font_candidates if item.exists()), None)
    font = ImageFont.truetype(str(font_path), 52) if font_path else ImageFont.load_default()
    draw.multiline_text((140, 180), text, fill="#171717", font=font, spacing=34)
    image.save(path, format="PNG", optimize=True)


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for filename, text in DOCUMENTS.items():
        generate_pdf(OUTPUT_ROOT / filename, text)
        print(f"Created {OUTPUT_ROOT / filename}")
    scan_path = OUTPUT_ROOT / "ocr-invoice-demo.png"
    generate_scan(scan_path, SCAN_TEXT)
    print(f"Created {scan_path}")


if __name__ == "__main__":
    main()

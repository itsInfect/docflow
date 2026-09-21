from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS_ROOT = Path(__file__).resolve().parents[1] / "docs" / "assets"
FRAMES = [
    ("overview.png", "Операционный обзор"),
    ("documents.png", "Реестр документов"),
    ("review.png", "Ручная проверка"),
    ("history.png", "Полный аудит"),
    ("quality.png", "Метрики качества"),
]


def build_demo_gif() -> None:
    title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
    caption_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
    frames: list[Image.Image] = []

    for filename, title in FRAMES:
        screenshot = Image.open(ASSETS_ROOT / filename).convert("RGB")
        screenshot = screenshot.resize((1152, 800), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (1152, 870), "white")
        header = Image.new("RGB", (1152, 70), "#172033")
        draw = ImageDraw.Draw(header)
        draw.text((28, 13), title, font=title_font, fill="white")
        draw.text((936, 23), "Docflow · demo", font=caption_font, fill="#f4b29c")
        canvas.paste(header, (0, 0))
        canvas.paste(screenshot, (0, 70))
        frames.append(canvas.quantize(colors=192, method=Image.Quantize.MEDIANCUT))

    frames[0].save(
        ASSETS_ROOT / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[2200] * len(frames),
        loop=0,
        optimize=True,
        disposal=2,
    )


if __name__ == "__main__":
    build_demo_gif()

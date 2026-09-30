from pathlib import Path
from uuid import uuid4

from models import ImageExtraction
from services.text_extraction import extract_from_text

TEMP_DIR = Path(__file__).resolve().parent.parent / "temp"


def extract_from_image(image_bytes: bytes | None) -> ImageExtraction:
    """OCR a screenshot. Needs: pip install pytesseract pillow (plus the Tesseract binary)."""
    if not image_bytes:
        return ImageExtraction(note="No screenshot provided")

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ImageExtraction(note="OCR not installed (pip install pytesseract pillow)")

    TEMP_DIR.mkdir(exist_ok=True)
    path = TEMP_DIR / f"{uuid4().hex}.png"
    path.write_bytes(image_bytes)
    try:
        text = pytesseract.image_to_string(Image.open(path)).strip()
        codes = extract_from_text(text).error_codes
        return ImageExtraction(
            text=text, error_codes=codes, available=True, note=f"{len(text.split())} words read"
        )
    except Exception as exc:  # OCR binary missing, corrupt image, etc.
        return ImageExtraction(note=f"OCR failed: {exc}")
    finally:
        path.unlink(missing_ok=True)
from functools import lru_cache
from io import BytesIO

from models import ImageExtraction
from service.text_extraction import extract_from_text


@lru_cache(maxsize=1)
def _ocr_engine():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def extract_from_image(image_bytes: bytes | None) -> ImageExtraction:
    """OCR a screenshot with RapidOCR and return its extracted text and codes."""
    if not image_bytes:
        return ImageExtraction(note="No screenshot provided")

    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return ImageExtraction(note="OCR not installed (pip install rapidocr-onnxruntime pillow)")

    try:
        image = np.array(Image.open(BytesIO(image_bytes)).convert("RGB"))
        rows, _ = _ocr_engine()(image)
        text = " ".join(str(row[1]) for row in (rows or []) if len(row) > 1 and row[1]).strip()
        print(f"OCR read {len(text.split())} words from screenshot")
        codes = extract_from_text(text).error_codes
        return ImageExtraction(
            text=text, error_codes=codes, available=True, note=f"{len(text.split())} words read"
        )
    except Exception as exc:  # OCR binary missing, corrupt image, etc.
        return ImageExtraction(note=f"OCR failed: {exc}")
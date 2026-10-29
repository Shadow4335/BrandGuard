import io
from typing import Tuple

from app.config import get_settings
from app.parsing import ParsedDoc, UploadError

MAX_SIDE = 2500   # very large photos are downscaled for OCR speed
MIN_SIDE = 1400   # small or low-contrast images are upscaled so Tesseract can read them
OCR_TIMEOUT = 30  # seconds; a slow OCR returns no text instead of hanging the request


def _tesseract():
    import pytesseract
    cmd = get_settings().tesseract_cmd
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    return pytesseract


def prepare_for_ocr(img) -> Tuple[object, float]:
    """Grayscale + auto-contrast + resize. Returns (image, scale) where original = ocr_coords / scale."""
    from PIL import ImageOps
    longest = max(img.size)
    scale = MAX_SIDE / longest if longest > MAX_SIDE else (2.0 if longest < MIN_SIDE else 1.0)
    g = ImageOps.autocontrast(img.convert("L"), cutoff=2)
    if scale != 1.0:
        g = g.resize((int(img.width * scale), int(img.height * scale)))
    return g, scale


def ocr_text(img) -> str:
    try:
        prepared, _ = prepare_for_ocr(img)
        return _tesseract().image_to_string(prepared, timeout=OCR_TIMEOUT).strip()
    except Exception:
        return ""


def parse_image(data: bytes, content_type: str = "") -> ParsedDoc:
    from PIL import Image, UnidentifiedImageError
    try:
        raw = Image.open(io.BytesIO(data))
        fmt = (raw.format or "png").lower()
        img = raw.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise UploadError("We couldn't open that image. Upload a PNG, JPG, WEBP or GIF.", 415)
    fmt = {"jpg": "jpeg", "mpo": "jpeg"}.get(fmt, fmt)
    text = ocr_text(img)
    note = None if text else "No text was detected in this image, so only visual checks ran."
    return ParsedDoc(text=text, file_type=f"image/{fmt}", is_image=True, note=note)

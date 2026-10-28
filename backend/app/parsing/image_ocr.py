import io

from app.config import get_settings
from app.parsing import ParsedDoc


def _tesseract():
    import pytesseract
    cmd = get_settings().tesseract_cmd
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    return pytesseract


def parse_image(data: bytes, content_type: str = "image/png") -> ParsedDoc:
    from PIL import Image
    img = Image.open(io.BytesIO(data)).convert("RGB")
    try:
        text = _tesseract().image_to_string(img).strip()
        note = None
    except Exception:
        text, note = "", "Text recognition (OCR) is unavailable, so text checks were skipped for this image."
    return ParsedDoc(text=text, file_type=content_type, is_image=True, note=note)

"""Turn uploaded files into plain text. One function per format; parse_upload picks the right one."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedDoc:
    text: str
    file_type: str                 # text/plain | application/pdf | docx | image/png ...
    is_image: bool = False
    images_missing_alt: int = 0    # docx pictures / html <img> without a description
    note: Optional[str] = None


def parse_upload(filename: str, content_type: str, data: bytes) -> ParsedDoc:
    name = (filename or "").lower()
    if name.endswith(".pdf") or content_type == "application/pdf":
        from app.parsing.pdf import parse_pdf
        return parse_pdf(data)
    if name.endswith(".docx"):
        from app.parsing.docx import parse_docx
        return parse_docx(data)
    if name.endswith((".png", ".jpg", ".jpeg", ".webp")) or content_type.startswith("image/"):
        from app.parsing.image_ocr import parse_image
        return parse_image(data, content_type or "image/png")
    if name.endswith((".html", ".htm")) or content_type == "text/html":
        from app.parsing.html import parse_html
        return parse_html(data.decode("utf-8", errors="replace"))
    from app.parsing.text import parse_text
    return parse_text(data.decode("utf-8", errors="replace"))

"""Turn uploaded files into plain text. One function per format; parse_upload picks the right one."""
from dataclasses import dataclass
from typing import Optional

TEXT_EXT = (".txt", ".md")
HTML_EXT = (".html", ".htm")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff")
SUPPORTED = "PDF, DOCX, PNG, JPG, WEBP, GIF, TXT, Markdown or HTML"
MAX_BYTES = 10 * 1024 * 1024


class UploadError(Exception):
    """A user-facing problem with the uploaded file (unsupported type, unreadable, too large)."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class ParsedDoc:
    text: str
    file_type: str                 # text/plain | application/pdf | docx | text/html | image/png ...
    is_image: bool = False
    images_missing_alt: int = 0    # docx pictures / html <img> without a description
    note: Optional[str] = None


def _kind(name: str, content_type: str) -> str:
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith(".docx"):
        return "docx"
    if name.endswith(IMAGE_EXT):
        return "image"
    if name.endswith(HTML_EXT):
        return "html"
    if name.endswith(TEXT_EXT):
        return "text"
    if name.endswith(".doc"):
        raise UploadError("Old Word (.doc) files aren't supported. Save it as .docx and upload again.", 415)
    if name.endswith((".heic", ".heif")):
        raise UploadError("HEIC photos aren't supported. Export the image as JPG or PNG and upload again.", 415)
    # No helpful extension: fall back to the browser's content type
    if content_type == "application/pdf":
        return "pdf"
    if content_type.startswith("image/"):
        return "image"
    if content_type == "text/html":
        return "html"
    if content_type in ("text/plain", "text/markdown"):
        return "text"
    raise UploadError(f"That file type isn't supported. Upload a {SUPPORTED} file.", 415)


def decode_text(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-16"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def parse_upload(filename: str, content_type: str, data: bytes) -> ParsedDoc:
    if not data:
        raise UploadError("That file is empty. Choose another file.")
    if len(data) > MAX_BYTES:
        raise UploadError("That file is larger than 10 MB. Please upload a smaller one.", 413)
    kind = _kind((filename or "").lower().strip(), (content_type or "").lower())
    try:
        if kind == "pdf":
            from app.parsing.pdf import parse_pdf
            return parse_pdf(data)
        if kind == "docx":
            from app.parsing.docx import parse_docx
            return parse_docx(data)
        if kind == "image":
            from app.parsing.image_ocr import parse_image
            return parse_image(data)
        if kind == "html":
            from app.parsing.html import parse_html
            return parse_html(decode_text(data))
        from app.parsing.text import parse_text
        return parse_text(decode_text(data))
    except UploadError:
        raise
    except Exception:
        label = {"pdf": "PDF", "docx": "Word document", "image": "image", "html": "HTML file"}.get(kind, "file")
        raise UploadError(f"We couldn't read that {label}. It may be damaged or password-protected. Try exporting it again.")

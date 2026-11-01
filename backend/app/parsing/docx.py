import io
import zipfile

from app.parsing import ParsedDoc, UploadError

MAX_UNCOMPRESSED = 50 * 1024 * 1024  # a .docx is a zip: cap what it expands to (zip bombs)
MAX_RATIO = 100                      # and how much any one entry may expand


def _check_zip(data: bytes) -> None:
    try:
        entries = zipfile.ZipFile(io.BytesIO(data)).infolist()
    except zipfile.BadZipFile:
        return  # not a valid zip: python-docx fails next and the upload gets the usual "couldn't read" error
    if sum(e.file_size for e in entries) > MAX_UNCOMPRESSED:
        raise UploadError("Uncompressed document exceeds 50 MB limit.", 413)
    if any(e.compress_size and e.file_size / e.compress_size > MAX_RATIO for e in entries):
        raise UploadError("Uncompressed document exceeds 50 MB limit.", 413)


def parse_docx(data: bytes) -> ParsedDoc:
    from docx import Document
    _check_zip(data)
    doc = Document(io.BytesIO(data))
    text = "\n".join(p.text for p in doc.paragraphs)
    missing = 0
    # Inline pictures live in <wp:docPr descr="..."> ; no descr means no alt-text
    for el in doc.element.body.iter():
        if el.tag.endswith("}docPr") and not (el.get("descr") or "").strip():
            missing += 1
    return ParsedDoc(text=text.strip(), file_type="docx", images_missing_alt=missing)

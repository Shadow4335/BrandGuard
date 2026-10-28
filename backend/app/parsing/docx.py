import io

from app.parsing import ParsedDoc


def parse_docx(data: bytes) -> ParsedDoc:
    from docx import Document
    doc = Document(io.BytesIO(data))
    text = "\n".join(p.text for p in doc.paragraphs)
    missing = 0
    # Inline pictures live in <wp:docPr descr="..."> ; no descr means no alt-text
    for el in doc.element.body.iter():
        if el.tag.endswith("}docPr") and not (el.get("descr") or "").strip():
            missing += 1
    return ParsedDoc(text=text.strip(), file_type="docx", images_missing_alt=missing)

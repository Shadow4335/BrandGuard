from app.parsing import ParsedDoc


def parse_pdf(data: bytes) -> ParsedDoc:
    import fitz  # PyMuPDF
    with fitz.open(stream=data, filetype="pdf") as doc:
        text = "\n\n".join(page.get_text().strip() for page in doc)
    note = None if text.strip() else "No selectable text found. Upload a text PDF or an image of the page."
    return ParsedDoc(text=text.strip(), file_type="application/pdf", note=note)

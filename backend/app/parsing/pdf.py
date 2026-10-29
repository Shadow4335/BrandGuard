from app.parsing import ParsedDoc

OCR_PAGES = 5      # scanned PDFs: OCR at most this many pages to keep reviews fast
MIN_TEXT = 20      # fewer selectable characters than this means the PDF is probably a scan


def parse_pdf(data: bytes) -> ParsedDoc:
    import fitz  # PyMuPDF
    with fitz.open(stream=data, filetype="pdf") as doc:
        if doc.needs_pass:
            from app.parsing import UploadError
            raise UploadError("That PDF is password-protected. Remove the password and upload it again.")
        text = "\n\n".join(page.get_text().strip() for page in doc).strip()
        if len(text) >= MIN_TEXT:
            return ParsedDoc(text=text, file_type="application/pdf")
        # Scanned PDF: render pages and read them with OCR
        from PIL import Image
        from app.parsing.image_ocr import ocr_text
        pages = []
        for page in list(doc)[:OCR_PAGES]:
            pix = page.get_pixmap(dpi=200)
            pages.append(ocr_text(Image.frombytes("RGB", (pix.width, pix.height), pix.samples)))
        ocr = "\n\n".join(p for p in pages if p).strip()
        more = len(doc) > OCR_PAGES
    if not ocr:
        return ParsedDoc(text="", file_type="application/pdf",
                         note="No readable text found in this PDF. Upload a text PDF or a clearer scan.")
    note = "Scanned PDF: text was read with OCR" + (f" (first {OCR_PAGES} pages only)." if more else ".")
    return ParsedDoc(text=ocr, file_type="application/pdf", note=note)

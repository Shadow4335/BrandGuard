from app.parsing import ParsedDoc

OCR_PAGES = 5      # scanned PDFs: OCR at most this many pages to keep reviews fast
MIN_TEXT = 20      # fewer selectable characters than this means the PDF is probably a scan
MAX_PDF_PAGES = 100
MAX_TEXT_CHARS = 250_000  # longer text is cut here (a review only needs the content, not a whole book)
MAX_RENDER_PIXELS = 25_000_000  # same safety limit as uploaded images


def parse_pdf(data: bytes) -> ParsedDoc:
    import fitz  # PyMuPDF
    with fitz.open(stream=data, filetype="pdf") as doc:
        if doc.needs_pass:
            from app.parsing import UploadError
            raise UploadError("That PDF is password-protected. Remove the password and upload it again.")
        if len(doc) > MAX_PDF_PAGES:
            from app.parsing import UploadError
            raise UploadError("PDF exceeds 100-page limit.", 413)
        text = "\n\n".join(page.get_text().strip() for page in doc).strip()
        if len(text) >= MIN_TEXT:
            if len(text) > MAX_TEXT_CHARS:
                return ParsedDoc(text=text[:MAX_TEXT_CHARS], file_type="application/pdf",
                                 note=f"Long PDF: only the first {MAX_TEXT_CHARS:,} characters were checked.")
            return ParsedDoc(text=text, file_type="application/pdf")
        # Scanned PDF: render pages and read them with OCR
        from PIL import Image
        from app.parsing.image_ocr import ocr_text
        pages = []
        for page in list(doc)[:OCR_PAGES]:
            # 200 dpi normally, lower for oversized pages so the render stays under the 25 MP image limit
            area_in2 = max(page.rect.width * page.rect.height / (72 * 72), 1e-6)
            dpi = int(min(200, (MAX_RENDER_PIXELS / area_in2) ** 0.5))
            pix = page.get_pixmap(dpi=max(dpi, 30))
            pages.append(ocr_text(Image.frombytes("RGB", (pix.width, pix.height), pix.samples)))
        ocr = "\n\n".join(p for p in pages if p).strip()
        more = len(doc) > OCR_PAGES
    if not ocr:
        return ParsedDoc(text="", file_type="application/pdf",
                         note="No readable text found in this PDF. Upload a text PDF or a clearer scan.")
    note = "Scanned PDF: text was read with OCR" + (f" (first {OCR_PAGES} pages only)." if more else ".")
    return ParsedDoc(text=ocr, file_type="application/pdf", note=note)

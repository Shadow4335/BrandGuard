from app.parsing import ParsedDoc


def parse_text(text: str) -> ParsedDoc:
    return ParsedDoc(text=text.replace("\r\n", "\n").strip("\n"), file_type="text/plain")

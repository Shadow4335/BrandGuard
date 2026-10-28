from app.parsing import ParsedDoc


def count_imgs_without_alt(html: str):
    """Return (img tag source strings without alt, parsed soup)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    return [str(i) for i in soup.find_all("img") if not (i.get("alt") or "").strip()], soup


def parse_html(html: str) -> ParsedDoc:
    missing, soup = count_imgs_without_alt(html)
    return ParsedDoc(text=soup.get_text("\n").strip(), file_type="text/html", images_missing_alt=len(missing))

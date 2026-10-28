"""WCAG contrast checks on images: OCR word boxes, two dominant colours per box, ratio."""
import io
from typing import List, Tuple

from app.parsing.image_ocr import _tesseract

RGB = Tuple[int, int, int]


def _lin(c: int) -> float:
    v = c / 255
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def luminance(rgb: RGB) -> float:
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(a: RGB, b: RGB) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def dominant_two(crop) -> Tuple[RGB, RGB]:
    """Two dominant colours of a crop (text vs background) via a 2-colour palette quantisation."""
    q = crop.convert("RGB").quantize(colors=2, method=0)
    pal = q.getpalette()[:6]
    counts = sorted(q.getcolors(), reverse=True)  # [(count, index)]
    cols = [tuple(pal[i * 3:i * 3 + 3]) for _, i in counts]
    if len(cols) == 1:
        cols = cols * 2
    return cols[0], cols[1]


def find_low_contrast_regions(image_bytes: bytes) -> List[dict]:
    """Return one region per OCR line whose words fail WCAG AA. Empty if OCR is unavailable."""
    from PIL import Image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    try:
        d = _tesseract().image_to_data(img, output_type=_tesseract().Output.DICT)
    except Exception:
        return []
    lines: dict = {}
    for i, word in enumerate(d["text"]):
        if not word.strip() or float(d["conf"][i]) < 60 or len(word.strip()) < 2:
            continue
        x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
        crop = img.crop((x, y, x + w, y + h))
        c1, c2 = dominant_two(crop)
        ratio = contrast_ratio(c1, c2)
        need = 3.0 if h >= 24 else 4.5
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        line = lines.setdefault(key, {"words": [], "fails": 0, "min": 99.0, "need": need,
                                      "box": [x, y, x + w, y + h]})
        line["words"].append(word)
        line["box"] = [min(line["box"][0], x), min(line["box"][1], y), max(line["box"][2], x + w), max(line["box"][3], y + h)]
        line["min"] = min(line["min"], ratio)
        line["need"] = min(line["need"], need)
        if ratio < need:
            line["fails"] += 1
    out = []
    for ln in lines.values():
        if ln["fails"] >= max(1, len(ln["words"]) // 2):
            x0, y0, x1, y1 = ln["box"]
            out.append({"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0, "text": " ".join(ln["words"]),
                        "ratio": round(ln["min"], 2), "needed": ln["need"]})
    return out

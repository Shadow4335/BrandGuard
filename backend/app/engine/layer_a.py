"""Layer A: deterministic checks (regex, rapidfuzz, structure, contrast). No AI, always high confidence."""
import re
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from rapidfuzz import fuzz

from app.engine.rules_loader import load_rules
from app.models import Finding, TextSpan, VisualRegion
from app.models.enums import FindingCategory, FindingConfidence, FindingLayer, FindingSeverity

FUZZY_THRESHOLD = 88
INFLUENCER_TAGS = re.compile(r"#\s?(ad|sponsored|collab|paidpartnership)\b", re.I)
AI_LABEL = re.compile(r"(created|generated|made|produced)\s+(using|with|by)\s+ai|ai[- ]generated|#aigenerated|virtual influencer|digital avatar", re.I)
PERSONA_WORDS = re.compile(r"\b(virtual|avatar|ai[- ]generated|digital (human|influencer|persona)|synthetic)\b", re.I)
QUALIFIER = re.compile(r"(results?\s+vary|individual results|terms\s*(and|&)\s*conditions|t\s*&\s*c|conditions apply|contains\b|may vary)", re.I)


@dataclass
class ReviewContext:
    version_id: UUID
    org_id: UUID
    text: str
    channel: str = "instagram_post"
    ai_generated: bool = False
    alt_text: Optional[str] = None
    image_bytes: Optional[bytes] = None
    is_image: bool = False
    images_missing_alt: int = 0


def _make(ctx: ReviewContext, rule: dict, issue: str, start: Optional[int] = None, end: Optional[int] = None,
          fix: Optional[str] = None, replacement: Optional[str] = None, severity: Optional[str] = None,
          region: Optional[VisualRegion] = None, why: Optional[str] = None) -> Finding:
    span = TextSpan(start=start, end=end) if start is not None else None
    return Finding(
        content_version_id=ctx.version_id, org_id=ctx.org_id, layer=FindingLayer.A,
        category=FindingCategory(rule["category"]), rule_id=rule["id"],
        source_codes=[rule["source_code"]] if rule.get("source_code") else [],
        span=span, span_text=ctx.text[start:end] if span and ctx.text else None, region=region,
        issue=issue, why_flagged=why or f'{rule["why"]} Reference: {rule.get("reference", "")}.'.strip(),
        suggested_fix=fix or rule.get("fix_template", ""), replacement=replacement,
        severity=FindingSeverity(severity or rule["severity"]), confidence=FindingConfidence.HIGH,
    )


def _match_case(original: str, replacement: str) -> str:
    return replacement[:1].upper() + replacement[1:] if original[:1].isupper() else replacement


def _regex_rules(ctx: ReviewContext, rule: dict) -> List[Finding]:
    out = []
    for pat in rule.get("patterns", []):
        for m in re.finditer(pat, ctx.text, re.I):
            out.append(_make(ctx, rule, f'{rule["title"]}: "{m.group(0)}"', m.start(), m.end()))
    return out


def _terminology(ctx: ReviewContext, rule: dict) -> List[Finding]:
    toks = [(m.group(0).lower(), m.start(), m.end()) for m in re.finditer(r"[A-Za-z0-9']+", ctx.text)]
    out: List[Finding] = []
    seen = set()
    for term in rule.get("terms", []):
        banned = term["banned"].lower().replace("-", " ")
        n = len(banned.split())
        forms = term.get("forms")
        for i in range(len(toks) - n + 1):
            window = toks[i:i + n]
            cand = " ".join(t[0] for t in window)
            exact = cand in ([f.replace("-", " ") for f in forms] if forms else [banned])
            fuzzy = (not forms) and len(banned) >= 6 and fuzz.ratio(cand, banned) >= FUZZY_THRESHOLD
            if not (exact or fuzzy):
                continue
            s, e = window[0][1], window[-1][2]
            if (s, e) in seen:
                continue
            seen.add((s, e))
            orig = ctx.text[s:e]
            pref = forms.get(cand) if forms else term["preferred"]
            out.append(_make(ctx, rule, f'Banned term "{orig}" (use "{pref}")', s, e,
                             fix=f'Replace with "{pref}" (TERM-01).', replacement=_match_case(orig, pref),
                             severity=term.get("severity")))
    return out


def _contradictory_disclaimer(ctx: ReviewContext, rule: dict, abs_rules: List[dict]) -> List[Finding]:
    head = None
    for r in abs_rules:
        for pat in r.get("patterns", []):
            m = re.search(pat, ctx.text, re.I)
            if m and (head is None or m.start() < head.start()):
                head = m
    if not head:
        return []
    # Footnote: a later line starting with * or containing a qualifier phrase
    for line in re.finditer(r"[^\n]+", ctx.text[head.end():]):
        seg = line.group(0).strip()
        if seg.startswith("*") or QUALIFIER.search(seg):
            end = head.end() + line.end()
            return [_make(ctx, rule, f'Headline claim "{head.group(0)}" is undercut by the footnote', head.start(), end)]
    return []


def _influencer(ctx: ReviewContext, rule: dict) -> List[Finding]:
    if ctx.channel != "influencer_post":
        return []
    visible = "\n".join(ctx.text.splitlines()[:2])[:125]
    if INFLUENCER_TAGS.search(visible):
        return []
    return [_make(ctx, rule, "Influencer post has no #Ad / #Sponsored / #Collab label in the first visible lines",
                  0, 0, fix="Start the post with #Ad.", replacement="#Ad ")]


def _ai_label(ctx: ReviewContext, rule: dict) -> List[Finding]:
    m = PERSONA_WORDS.search(ctx.text)
    if not (ctx.ai_generated and m) or AI_LABEL.search(ctx.text):
        return []
    return [_make(ctx, rule, f'AI-generated persona ("{m.group(0)}") is not labelled', m.start(), m.end(),
                  fix='Add a visible label such as "Created using AI".')]


def _alt_text(ctx: ReviewContext, rule: dict) -> List[Finding]:
    out = []
    if ctx.is_image and not (ctx.alt_text or "").strip():
        out.append(_make(ctx, rule, "Image has no alt-text", fix="Add alt-text describing the image and any text in it."))
    if ctx.images_missing_alt:
        out.append(_make(ctx, rule, f"{ctx.images_missing_alt} image(s) in the document have no alt-text",
                         severity="medium"))
    for m in re.finditer(r"<img\b(?![^>]*\balt=\"[^\"]+\")[^>]*>", ctx.text, re.I):
        out.append(_make(ctx, rule, "<img> tag without alt text", m.start(), m.end()))
    return out


def _contrast(ctx: ReviewContext, rule: dict) -> List[Finding]:
    if not (ctx.is_image and ctx.image_bytes):
        return []
    from app.engine.contrast import find_low_contrast_regions
    out = []
    for r in find_low_contrast_regions(ctx.image_bytes):
        out.append(_make(ctx, rule, f'Text "{r["text"]}" has contrast {r["ratio"]}:1 (needs {r["needed"]}:1)',
                         region=VisualRegion(x=r["x"], y=r["y"], w=r["w"], h=r["h"], page=1)))
    return out


def run_layer_a(ctx: ReviewContext) -> List[Finding]:
    rules = [r for r in load_rules() if r["layer"] == "A"]
    abs_rules = [r for r in rules if r.get("patterns") and r["category"] == "claim"]
    checks = {"terminology": _terminology, "influencer_disclosure": _influencer, "ai_label": _ai_label,
              "alt_text": _alt_text, "contrast": _contrast}
    out: List[Finding] = []
    for r in rules:
        if r.get("patterns"):
            out += _regex_rules(ctx, r)
        elif r.get("check") == "contradictory_disclaimer":
            out += _contradictory_disclaimer(ctx, r, abs_rules)
        elif r.get("check") in checks:
            out += checks[r["check"]](ctx, r)
    return out

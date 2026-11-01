"""Findings Merger: de-duplicate overlapping findings, set severity and confidence, order the list."""
from typing import List

from app.models import Finding
from app.models.enums import FindingSeverity

RANK = {"high": 0, "medium": 1, "low": 2}


def _iou(a: Finding, b: Finding) -> float:
    if not (a.span and b.span):
        return 0.0
    lo, hi = max(a.span.start, b.span.start), min(a.span.end, b.span.end)
    inter = max(0, hi - lo)
    union = max(a.span.end, b.span.end) - min(a.span.start, b.span.start)
    if union == 0:  # two insertion points at the same offset
        return 1.0 if a.span.start == b.span.start else 0.0
    return inter / union


def _containment(a: Finding, b: Finding) -> float:
    """Share of the shorter span that lies inside the other: 1.0 when one span sits wholly within the other."""
    if not (a.span and b.span):
        return 0.0
    inter = max(0, min(a.span.end, b.span.end) - max(a.span.start, b.span.start))
    shorter = min(a.span.end - a.span.start, b.span.end - b.span.start)
    return inter / shorter if shorter > 0 else 0.0


MAX_WIDTH_RATIO = 3  # a span this many times longer than the other is a broader issue, not the same one


def _same_issue(a: Finding, b: Finding) -> bool:
    """Overlapping enough to be one issue. Besides a high IoU, this covers a rule match sitting inside a slightly
    wider AI span about the same thing ("100% natural" inside "100% natural, chemical-free"), which would otherwise
    show as two stacked highlights. Findings from the same layer, or a span much wider than the other (a whole
    sentence or post), stay separate: those are distinct issues that each need their own fix."""
    if _iou(a, b) >= 0.5:
        return True
    if a.layer == b.layer or a.category != b.category or not (a.span and b.span):
        return False
    widths = sorted((a.span.end - a.span.start, b.span.end - b.span.start))
    return _containment(a, b) >= 0.8 and widths[0] > 0 and widths[1] <= MAX_WIDTH_RATIO * widths[0]


def _pick_primary(group: List[Finding]) -> Finding:
    return sorted(group, key=lambda f: (RANK[f.severity.value], f.layer.value, 0 if f.source_codes else 1))[0]


def _merge_group(group: List[Finding]) -> Finding:
    if len(group) == 1:
        return group[0]
    primary = _pick_primary(group).model_copy(deep=True)
    codes = list(primary.source_codes)
    for o in group:
        if o is primary or o.id == primary.id:
            continue
        codes += [c for c in o.source_codes if c not in codes]
        primary.why_flagged += f" Also: {o.issue}."
        if o.rule_id == "RULE-CLAIM-UNSUPPORTED" and "Unsupported claim" not in primary.issue:
            primary.issue = f"{primary.issue} (Unsupported claim: no approved source)"
            primary.why_flagged += " No approved source supports it."
        if o.rule_id == "RULE-CLAIM-FACT":
            primary.suggested_fix = f"{primary.suggested_fix} {o.suggested_fix}".strip()
    primary.source_codes = codes
    # Accept replaces exactly the span with the replacement, so the two must come from the same finding. Use the
    # widest finding that has a ready-made replacement (a clause rewrite also covers a word-level fix inside it).
    with_fix = [f for f in group if f.replacement and f.span]
    if with_fix:
        best_fix = max(with_fix, key=lambda f: f.span.end - f.span.start)
        primary.span, primary.span_text, primary.replacement = best_fix.span, best_fix.span_text, best_fix.replacement
    best = min(group, key=lambda f: RANK[f.severity.value]).severity
    primary.severity = best
    return primary


def merge(layer_a: List[Finding], layer_b: List[Finding]) -> List[Finding]:
    all_f = layer_a + layer_b
    groups: List[List[Finding]] = []
    for f in all_f:
        for g in groups:
            if any(_same_issue(f, x) for x in g):
                g.append(f)
                break
        else:
            groups.append([f])
    merged = [_merge_group(g) for g in groups]
    for f in merged:  # regulatory references force high severity
        if any(c.startswith("REG-") for c in f.source_codes):
            f.severity = FindingSeverity.HIGH
    merged.sort(key=lambda f: (RANK[f.severity.value], f.span.start if f.span else 10**9))
    return merged

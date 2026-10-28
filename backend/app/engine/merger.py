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
        if not primary.replacement and o.replacement:
            primary.replacement = o.replacement
        if o.rule_id == "RULE-CLAIM-UNSUPPORTED" and "Unsupported claim" not in primary.issue:
            primary.issue = f"{primary.issue} (Unsupported claim: no approved source)"
            primary.why_flagged += " No approved source supports it."
        if o.rule_id == "RULE-CLAIM-FACT":
            primary.suggested_fix = f"{primary.suggested_fix} {o.suggested_fix}".strip()
    primary.source_codes = codes
    best = min(group, key=lambda f: RANK[f.severity.value]).severity
    primary.severity = best
    return primary


def merge(layer_a: List[Finding], layer_b: List[Finding]) -> List[Finding]:
    all_f = layer_a + layer_b
    groups: List[List[Finding]] = []
    for f in all_f:
        for g in groups:
            if any(_iou(f, x) >= 0.5 for x in g):
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

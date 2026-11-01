import uuid

from app.engine.merger import merge
from app.models import Finding, TextSpan
from app.models.enums import FindingCategory, FindingConfidence, FindingLayer, FindingSeverity

V = uuid.uuid4()


def mk(layer, start, end, sev="medium", codes=None, rule="R", cat="claim", issue="i", repl=None):
    return Finding(content_version_id=V, org_id=V, layer=FindingLayer(layer), category=FindingCategory(cat),
                   rule_id=rule, source_codes=codes or [], span=TextSpan(start=start, end=end), issue=issue,
                   why_flagged="w", suggested_fix="f", replacement=repl, severity=FindingSeverity(sev),
                   confidence=FindingConfidence.HIGH if layer == "A" else FindingConfidence.LOW)


def test_overlapping_findings_merge_and_union_citations():
    a = mk("A", 0, 12, "high", ["REG-CCPA-2022"], "RULE-ABS-001")
    b = mk("B", 0, 12, "high", ["FACT-001"], "RULE-CLAIM-FACT")
    out = merge([a], [b])
    assert len(out) == 1 and out[0].source_codes == ["REG-CCPA-2022", "FACT-001"] and out[0].layer.value == "A"


def test_contained_small_span_not_merged_into_large_one():
    out = merge([mk("A", 0, 100, "high"), mk("A", 10, 20, "high")], [])
    assert len(out) == 2


def test_severity_takes_max_and_regulatory_forces_high():
    out = merge([mk("A", 0, 5, "low", ["REG-DMR"])], [mk("B", 0, 5, "medium")])
    assert out[0].severity.value == "high"


def test_unsupported_merge_marks_issue_and_keeps_rule_confidence():
    a = mk("A", 0, 5, "high", ["REG-ASCI-SGC"], "RULE-SUP-001", issue="Ranking claim")
    b = mk("B", 0, 5, "medium", [], "RULE-CLAIM-UNSUPPORTED")
    f = merge([a], [b])[0]
    assert "Unsupported claim" in f.issue and f.confidence.value == "high"


def test_ordering_high_first_then_position():
    out = merge([mk("A", 50, 55, "low"), mk("A", 30, 35, "high"), mk("A", 10, 15, "high")], [])
    assert [(f.severity.value, f.span.start) for f in out] == [("high", 10), ("high", 30), ("low", 50)]


def test_rule_match_inside_a_slightly_wider_ai_span_merges():
    a = mk("A", 0, 12, "high", ["REG-CCPA-2022"], "RULE-ABS-001")    # "100% natural"
    b = mk("B", 0, 27, "medium", ["FACT-001"], "RULE-CLAIM-FACT")    # "100% natural, chemical-free"
    out = merge([a], [b])
    assert len(out) == 1 and set(out[0].source_codes) == {"REG-CCPA-2022", "FACT-001"}


def test_rule_match_inside_a_whole_sentence_stays_separate():
    out = merge([mk("A", 10, 15, "high")], [mk("B", 0, 80, "medium")])
    assert len(out) == 2


def test_different_categories_do_not_merge_by_containment():
    out = merge([mk("A", 0, 8, "high", cat="terminology")], [mk("B", 0, 20, "medium")])  # IoU 0.4, contained
    assert len(out) == 2


def test_merged_fix_keeps_its_own_span():
    """Accept replaces exactly the span, so the replacement must come with the span it was written for."""
    a = mk("A", 5, 10, "high", repl="free from parabens")
    b = mk("B", 0, 12, "medium")
    f = merge([a], [b])[0]
    assert (f.span.start, f.span.end, f.replacement) == (5, 10, "free from parabens")
    wide = mk("B", 0, 12, "medium", repl="Gentle, natural care")
    f = merge([mk("A", 5, 10, "high", repl="x")], [wide])[0]
    assert (f.span.start, f.span.end, f.replacement) == (0, 12, "Gentle, natural care")

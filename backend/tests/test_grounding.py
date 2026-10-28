import uuid

from app.engine.layer_a import ReviewContext
from app.engine.layer_b import AIFinding, AIOutput, ground, heuristic_layer_b
from app.engine.retrieval import RetrievedSource

V = uuid.uuid4()
FACT = RetrievedSource("1", "FACT-001", "claim_library", "The lip balm contains 92% naturally derived ingredients.")
TONE = RetrievedSource("2", "GUIDE-TONE-01", "guideline", "Warm, honest, no hype.")


def ctx(text):
    return ReviewContext(V, V, text)


def out(**kw):
    base = dict(category="claim", span_text="100% natural", issue="x", verdict="contradicted", source_code="FACT-001")
    return AIOutput(findings=[AIFinding(**{**base, **kw})])


def test_valid_citation_is_kept_with_medium_confidence():
    f = ground(out(), ctx("A 100% natural balm"), [FACT, TONE])[0]
    assert f.source_codes == ["FACT-001"] and f.confidence.value == "medium"


def test_fabricated_source_id_is_rejected_and_downgraded():
    f = ground(out(source_code="FACT-999"), ctx("A 100% natural balm"), [FACT, TONE])[0]
    assert f.source_codes == []
    assert f.issue.startswith("Unsupported claim") and f.confidence.value == "low"


def test_retrieved_set_only_citation_not_in_set_is_rejected():
    # FACT-001 exists in the org but was not retrieved for this run
    f = ground(out(), ctx("A 100% natural balm"), [TONE])[0]
    assert f.source_codes == [] and f.confidence.value == "low"


def test_span_not_in_content_is_dropped():
    assert ground(out(span_text="totally absent"), ctx("A 100% natural balm"), [FACT]) == []


def test_tone_finding_without_guideline_is_dropped():
    o = out(category="tone", verdict="off_tone", source_code=None, span_text="natural")
    assert ground(o, ctx("A 100% natural balm"), [FACT]) == []


def test_heuristic_flags_contradiction_and_unsupported():
    c = ctx("Our 100% natural lip balm works in 1 day!")
    fs = ground(heuristic_layer_b(c, [FACT, TONE]), c, [FACT, TONE])
    kinds = {(f.rule_id, tuple(f.source_codes)) for f in fs}
    assert ("RULE-CLAIM-FACT", ("FACT-001",)) in kinds
    assert any(f.rule_id == "RULE-CLAIM-UNSUPPORTED" for f in fs)

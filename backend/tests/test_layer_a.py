import uuid

from app.engine.layer_a import ReviewContext, run_layer_a
from app.seed_data import SAMPLES, make_poster_png

V = uuid.uuid4()


def sample(key):
    return next(s for s in SAMPLES if s["key"] == key)


def run(key, **kw):
    s = sample(key)
    return run_layer_a(ReviewContext(V, V, s["text"], s["channel"], s["ai_generated"], **kw))


def test_sample1_has_at_least_five_findings_with_exact_spans():
    s = sample("instagram")
    fs = run("instagram")
    assert len(fs) >= 5
    for f in fs:
        assert f.span and s["text"][f.span.start:f.span.end] == f.span_text
        assert f.confidence.value == "high" and f.layer.value == "A"
    rules = {f.rule_id for f in fs}
    assert {"RULE-ABS-001", "RULE-MED-001", "RULE-TERM-001", "RULE-DISC-001", "RULE-SUP-001"} <= rules


def test_terminology_suggests_preferred_term():
    fs = [f for f in run("instagram") if f.rule_id == "RULE-TERM-001"]
    assert "made without parabens and sulfates" in {f.replacement for f in fs}
    assert "Affordable" in {f.replacement for f in fs}


def test_fuzzy_catches_misspelling():
    ctx = ReviewContext(V, V, "Our chemcial-free serum", "website_page")
    assert any(f.span_text.lower().startswith("chemcial") for f in run_layer_a(ctx))


def test_influencer_disclosure_and_ai_label():
    fs = run("influencer")
    assert {f.rule_id for f in fs} == {"RULE-DISC-INFL-001", "RULE-DISC-AI-001"}


def test_disclosure_present_passes():
    ctx = ReviewContext(V, V, "#Ad Loving this serum", "influencer_post")
    assert not run_layer_a(ctx)


def test_clean_sample_has_no_findings():
    assert run("clean") == []


def test_image_contrast_and_alt_text():
    ctx = ReviewContext(V, V, "", "instagram_post", image_bytes=make_poster_png(), is_image=True, alt_text="")
    fs = run_layer_a(ctx)
    rules = {f.rule_id for f in fs}
    assert "RULE-VIS-CONTRAST-001" in rules and "RULE-A11Y-ALT-001" in rules
    assert all(f.region for f in fs if f.rule_id == "RULE-VIS-CONTRAST-001")


def test_alt_text_present_removes_finding():
    ctx = ReviewContext(V, V, "", "instagram_post", is_image=True, alt_text="A sale poster")
    assert not run_layer_a(ctx)

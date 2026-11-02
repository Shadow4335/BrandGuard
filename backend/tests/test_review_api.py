from fastapi.testclient import TestClient

from app.main import app
from app.seed_data import SAMPLES

c = TestClient(app)


def login(role):
    t = c.post("/api/auth/demo-login", json={"role": role}).json()
    return {"Authorization": "Bearer " + t["token"]}


def create_sample(h, key="instagram"):
    s = next(x for x in SAMPLES if x["key"] == key)
    r = c.post("/api/content", headers=h, data={"title": s["title"], "channel": s["channel"], "text": s["text"],
                                               "ai_generated": str(s["ai_generated"]).lower()})
    return r.json()["id"]


def test_review_without_llm_key_falls_back():
    h = login("creator")
    cid = create_sample(h)
    r = c.post(f"/api/content/{cid}/review", headers=h).json()
    assert r["used_fallback"] is True and "AI layer unavailable" in r["notice"]
    assert len(r["findings"]) >= 5
    assert any("Unsupported claim" in f["issue"] for f in r["findings"])
    assert all(f["issue"] and f["why_flagged"] and f["suggested_fix"] and f["severity"] and f["confidence"] for f in r["findings"])


def test_decisions_build_version_and_nothing_auto_applied():
    h = login("creator")
    cid = create_sample(h)
    fs = c.post(f"/api/content/{cid}/review", headers=h).json()["findings"]
    term = [f for f in fs if f["rule_id"] == "RULE-TERM-001" and f["replacement"]]
    # v1 unchanged until a version is saved
    assert c.get(f"/api/content/{cid}", headers=h).json()["versions"][0]["raw_text"].startswith("Our 100% natural")
    c.patch(f"/api/findings/{term[0]['id']}", headers=h, json={"decision": "accepted"})
    edited = next(f for f in fs if f["rule_id"] == "RULE-ABS-001" and f["span_text"] == "100% natural")
    c.patch(f"/api/findings/{edited['id']}", headers=h, json={"decision": "edited", "decision_text": "92% naturally derived"})
    rej = next(f for f in fs if f["span_text"] == "Guaranteed")
    assert c.patch(f"/api/findings/{rej['id']}", headers=h, json={"decision": "rejected"}).status_code == 400
    c.patch(f"/api/findings/{rej['id']}", headers=h, json={"decision": "rejected", "reason": "Intentional"})
    d = c.post(f"/api/content/{cid}/versions", headers=h, json={}).json()
    v2 = d["versions"][1]["raw_text"]
    assert "92% naturally derived" in v2 and "Guaranteed" in v2 and d["content"]["current_version"] == 2
    assert d["latest_run"]["version_number"] == 2


def test_only_creator_can_review():
    h = login("manager")
    assert c.post("/api/content/x/review", headers=h).status_code == 403


def test_image_sample_flags_contrast_and_alt():
    h = login("creator")
    img = c.get("/api/samples/poster/image", headers=h).content
    r = c.post("/api/content", headers=h, data={"title": "p", "channel": "instagram_post"}, files={"file": ("p.png", img, "image/png")})
    fs = c.post(f"/api/content/{r.json()['id']}/review", headers=h).json()["findings"]
    assert {"RULE-VIS-CONTRAST-001", "RULE-A11Y-ALT-001"} <= {f["rule_id"] for f in fs}


def test_stream_emits_progress_then_done():
    h = login("creator")
    cid = create_sample(h, "clean")
    body = c.post(f"/api/content/{cid}/review/stream", headers=h).text
    assert '"stage": "layer_a"' in body and '"stage": "done"' in body


def test_full_golden_path_through_workflow_and_audit():
    cr, mg, rv = login("creator"), login("manager"), login("reviewer")
    cid = create_sample(cr)
    # cannot submit before a review exists
    assert c.post(f"/api/content/{cid}/transition", headers=cr, json={"action": "submit"}).status_code == 409
    c.post(f"/api/content/{cid}/review", headers=cr)
    d = c.post(f"/api/content/{cid}/transition", headers=cr, json={"action": "submit"}).json()
    assert d["content"]["status"] == "pending_manager"
    assert any(i["content"]["id"] == cid for i in c.get("/api/reviews/queue", headers=mg).json())
    assert c.post(f"/api/content/{cid}/comments", headers=mg, json={"body": "Please check the claims"}).status_code == 200
    # a creator cannot approve their own content
    assert c.post(f"/api/content/{cid}/transition", headers=cr, json={"action": "approve"}).status_code == 403
    assert c.post(f"/api/content/{cid}/transition", headers=mg, json={"action": "escalate"}).json()["content"]["status"] == "escalated"
    r = c.post(f"/api/content/{cid}/transition", headers=rv, json={"action": "approve"})
    assert r.status_code == 409 and "override" in r.json()["detail"]
    r = c.post(f"/api/content/{cid}/transition", headers=rv,
               json={"action": "approve", "override": True, "reason": "Claims verified with legal"})
    assert r.json()["content"]["status"] == "approved"
    events = [e["event_type"] for e in c.get(f"/api/audit?content_id={cid}", headers=cr).json()]
    for ev in ["content_created", "review_run", "workflow_submit", "workflow_escalate", "workflow_approve", "comment_added"]:
        assert ev in events
    ap = [a for a in r.json()["approvals"] if a["action"] == "approve"][0]
    assert ap["override"] is True and ap["role"] == "reviewer"


def test_org_isolation_and_unauthenticated():
    assert c.get("/api/content").status_code in (401, 403)
    assert c.get("/api/content/nonexistent", headers=login("creator")).status_code == 404


def test_audit_log_is_append_only():
    import pytest
    from app.store import get_store
    row = get_store().select("audit_log", limit=1)[0]
    with pytest.raises(PermissionError):
        get_store().update("audit_log", row["id"], {"event_type": "x"})


def test_insights_are_seeded_and_flag_unclear_rule():
    h = login("admin")
    s = c.get("/api/insights/summary", headers=h).json()
    assert s["total_findings"] >= 60 and s["top_rules"][0]["rule_id"] == "RULE-ABS-001"
    assert len(s["trend"]) == 30 and s["status_counts"]
    unclear = c.get("/api/insights/unclear-rules", headers=h).json()
    assert "RULE-TONE-HYPE" in {u["rule_id"] for u in unclear}
    hype = next(r for r in s["most_overridden"] if r["rule_id"] == "RULE-TONE-HYPE")
    assert hype["override_rate"] >= 0.5


def test_list_and_queue_read_each_table_once(monkeypatch):
    """Content list and review queue batch their reads instead of querying per item."""
    from app.store import get_store
    store, reads = get_store(), []
    select, select_in = store.select, store.select_where_in
    monkeypatch.setattr(store, "select", lambda t, *a, **k: reads.append(t) or select(t, *a, **k))
    monkeypatch.setattr(store, "select_where_in", lambda t, *a, **k: reads.append(t) or select_in(t, *a, **k))
    for role, path in (("creator", "/api/content"), ("admin", "/api/content"), ("manager", "/api/reviews/queue")):
        token = c.post("/api/auth/demo-login", json={"role": role}).json()["token"]
        reads.clear()
        assert c.get(path, headers={"Authorization": "Bearer " + token}).status_code == 200
        assert all(reads.count(t) <= 1 for t in ("content_versions", "review_runs", "findings")), reads


def test_apply_decisions_insertions_and_overlaps():
    from app.routers.review import apply_decisions
    text = "Our balm cures lips fast."

    def f(s, e, new, status="accepted"):
        return {"span": {"start": s, "end": e}, "status": status, "replacement": new, "decision_text": new}
    # an insertion at the start never consumes text, even with an edit starting at the same place
    assert apply_decisions(text, [f(0, 3, "My"), f(0, 0, "#Ad ")]) == "#Ad My balm cures lips fast."
    # overlapping edits: the wider one wins
    assert apply_decisions(text, [f(9, 14, "soothes"), f(4, 19, "balm soothes lips")]) == "Our balm soothes lips fast."
    # rejected or open findings change nothing
    assert apply_decisions(text, [f(9, 14, "x", "rejected"), f(9, 14, "y", "open")]) == text


def test_review_writes_the_audit_log_in_one_batch(monkeypatch):
    from app.store import get_store
    store = get_store()
    single, batches = [], []
    orig_insert, orig_many = store.insert, store.insert_many
    monkeypatch.setattr(store, "insert", lambda t, r: single.append(t) or orig_insert(t, r))
    monkeypatch.setattr(store, "insert_many", lambda t, rows: batches.append((t, len(rows))) or orig_many(t, rows))
    h = {"Authorization": "Bearer " + c.post("/api/auth/demo-login", json={"role": "creator"}).json()["token"]}
    cid = c.post("/api/content", headers=h, data={"title": "t", "text": SAMPLES[0]["text"]}).json()["id"]
    single.clear(); batches.clear()
    assert c.post(f"/api/content/{cid}/review", headers=h).status_code == 200
    audit = [n for t, n in batches if t == "audit_log"]
    # one batch for the run and every finding (the in-memory store writes a batch row by row, so those rows are the
    # only single audit inserts)
    assert len(audit) == 1 and audit[0] >= 2 and single.count("audit_log") == audit[0]


def test_unique_sentences_drops_repeats():
    from app.engine.retrieval import unique_sentences
    assert unique_sentences("Soft lips. soft  LIPS. New formula!") == ["Soft lips.", "New formula!"]


def test_low_confidence_by_design_does_not_flag_a_guideline_as_unclear():
    """Every unsupported-claim finding is low confidence, so that says nothing about how clear the rule is."""
    unclear = c.get("/api/insights/unclear-rules", headers=login("admin")).json()
    assert "RULE-CLAIM-UNSUPPORTED" not in {u["rule_id"] for u in unclear}
    assert all("rejected" in u["reason"] and "disagree" not in u["suggestion"] for u in unclear)


def test_seeded_history_has_real_evidence_and_follows_the_approval_rule():
    h = login("manager")
    queue = c.get("/api/reviews/queue", headers=h).json()
    assert queue
    for card in queue:
        d = c.get(f"/api/content/{card['content']['id']}", headers=h).json()
        text = d["versions"][0]["raw_text"]
        assert "historical sample" not in text and d["findings"]
        for f in d["findings"]:
            assert text[f["span"]["start"]:f["span"]["end"]] == f["span_text"]
            assert "Seeded" not in f["issue"] and f["suggested_fix"] != "n/a"
    from app.store import get_store
    from app.workflow.state_machine import unresolved_high
    from app.engine.pipeline import latest_findings
    store = get_store()
    for a in store.select("approvals", {"action": "approve", "role": "manager"}):
        ver = store.select("content_versions", {"content_item_id": a["content_item_id"], "version_number": 1})[0]
        if "seeded" == store.select("review_runs", {"content_version_id": ver["id"]})[0].get("model"):
            assert a["override"] == (unresolved_high(latest_findings(ver["id"])) > 0)
            assert a["reason"] if a["override"] else True


def test_summary_counts_decisions_for_people_who_decide():
    s = c.get("/api/insights/summary?scope=mine", headers=login("manager")).json()
    assert s["decisions_total"] >= s["approvals_total"] and len(s["decision_trend"]) == 30
    assert sum(d["count"] for d in s["decision_trend"]) == s["decisions_total"]

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

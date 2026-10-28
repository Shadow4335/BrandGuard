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

"""What someone trying to break the app will do: bad IDs, repeated actions, oversized and junk input."""
from fastapi.testclient import TestClient

from app.main import app
from app.seed_data import SAMPLES
from app.store import Store, is_uuid, strip_nul

c = TestClient(app)
S = SAMPLES[0]


def login(role):
    return {"Authorization": "Bearer " + c.post("/api/auth/demo-login", json={"role": role}).json()["token"]}


def reviewed(h):
    cid = c.post("/api/content", headers=h, data={"title": "t", "channel": S["channel"], "text": S["text"]}).json()["id"]
    return cid, c.post(f"/api/content/{cid}/review", headers=h).json()["findings"]


def test_malformed_ids_never_reach_the_database():
    class Exploding(Store):
        def select(self, *a, **k):
            raise AssertionError("a Postgres uuid column would reject this")
    assert Exploding().get("content_items", "not-a-uuid") is None
    assert is_uuid("00000000-0000-0000-0000-000000000000") and not is_uuid("'; drop table x;--")


def test_malformed_ids_are_404_on_every_route():
    h = login("creator")
    assert c.get("/api/content/not-a-uuid", headers=h).status_code == 404
    assert c.get("/api/content/not-a-uuid/image", headers=h).status_code == 404
    assert c.get("/api/audit?content_id=not-a-uuid", headers=h).status_code == 404
    assert c.patch("/api/findings/not-a-uuid", headers=h, json={"decision": "accepted"}).status_code == 404


def test_nul_characters_are_removed_before_writing():
    assert strip_nul({"a": "x\x00y", "b": ["\x00z"], "c": 1}) == {"a": "xy", "b": ["z"], "c": 1}


def test_manager_approval_with_open_high_findings_needs_a_recorded_reason():
    cr, mg = login("creator"), login("manager")
    cid, _ = reviewed(cr)
    c.post(f"/api/content/{cid}/transition", headers=cr, json={"action": "submit"})
    r = c.post(f"/api/content/{cid}/transition", headers=mg, json={"action": "approve"})
    assert r.status_code == 409 and "override" in r.json()["detail"]
    r = c.post(f"/api/content/{cid}/transition", headers=mg,
               json={"action": "approve", "override": True, "reason": "Legal cleared these claims"})
    assert r.json()["content"]["status"] == "approved"
    ap = [a for a in r.json()["approvals"] if a["action"] == "approve"][0]
    assert ap["override"] is True and ap["reason"] == "Legal cleared these claims"


def test_saving_with_no_changes_does_not_make_a_new_version():
    h = login("creator")
    cid, findings = reviewed(h)
    assert c.post(f"/api/content/{cid}/versions", headers=h, json={}).status_code == 409
    f = next(x for x in findings if x.get("replacement"))
    c.patch(f"/api/findings/{f['id']}", headers=h, json={"decision": "accepted"})
    assert c.post(f"/api/content/{cid}/versions", headers=h, json={}).status_code == 200
    # the second click of a double click: the new version has no decisions yet
    assert c.post(f"/api/content/{cid}/versions", headers=h, json={}).status_code == 409
    assert len(c.get(f"/api/content/{cid}", headers=h).json()["versions"]) == 2


def test_oversized_input_gets_a_clear_refusal():
    cr, ad = login("creator"), login("admin")
    r = c.post("/api/content", headers=cr, data={"title": "x" * 201, "text": "hello"})
    assert r.status_code == 413 and "title" in r.json()["detail"]
    r = c.post("/api/content", headers=cr, data={"title": "t", "text": "x" * 100_001})
    assert r.status_code == 413 and "text" in r.json()["detail"]
    cid, _ = reviewed(cr)
    assert c.post(f"/api/content/{cid}/comments", headers=cr, json={"body": "x" * 2_001}).status_code == 413
    assert c.post("/api/sources", headers=ad, data={"kind": "guideline", "title": " ", "text": "x"}).status_code == 400


def test_comments_show_their_author_and_only_link_to_this_contents_findings():
    h = login("creator")
    cid, findings = reviewed(h)
    _, other_findings = reviewed(h)
    assert c.post(f"/api/content/{cid}/comments", headers=h, json={"body": "hi", "finding_id": "nope"}).status_code == 400
    assert c.post(f"/api/content/{cid}/comments", headers=h,
                  json={"body": "hi", "finding_id": other_findings[0]["id"]}).status_code == 400
    assert c.post(f"/api/content/{cid}/comments", headers=h,
                  json={"body": "hi", "finding_id": findings[0]["id"]}).status_code == 200
    assert c.get(f"/api/content/{cid}", headers=h).json()["comments"][0]["author_name"]

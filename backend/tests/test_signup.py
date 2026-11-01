"""Real (non-demo) accounts: sign up, sign in, and use the product with the chosen role."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seed_data import SAMPLES

c = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_rate_limit():
    from app.routers import core
    for bucket in (core._signups, core._logins, core._demos):
        bucket.clear()
    yield
    for bucket in (core._signups, core._logins, core._demos):
        bucket.clear()


def new_email():
    return f"judge-{uuid.uuid4().hex[:8]}@example.com"


def signup(email, role="creator", password="correct horse 1", name="Jamie Judge"):
    return c.post("/api/auth/signup", json={"email": email, "password": password, "full_name": name, "role": role})


def test_signup_then_full_creator_flow():
    email = new_email()
    r = signup(email)
    assert r.status_code == 200 and r.json()["mode"] == "memory"
    h = {"Authorization": "Bearer " + r.json()["session"]["token"]}
    me = c.get("/api/me", headers=h).json()
    assert me["role"] == "creator" and me["email"] == email
    s = SAMPLES[0]
    cid = c.post("/api/content", headers=h, data={"title": "t", "channel": s["channel"], "text": s["text"]}).json()["id"]
    assert len(c.post(f"/api/content/{cid}/review", headers=h).json()["findings"]) >= 5
    assert c.post(f"/api/content/{cid}/transition", headers=h, json={"action": "submit"}).status_code == 200
    # the demo manager sees the real user's submission in the shared workspace queue
    m = c.post("/api/auth/demo-login", json={"role": "manager"}).json()["token"]
    queue = c.get("/api/reviews/queue", headers={"Authorization": "Bearer " + m}).json()
    assert any(i["content"]["id"] == cid and i["creator_name"] == "Jamie Judge" for i in queue)


def test_login_after_signup_and_wrong_password():
    email = new_email()
    signup(email)
    ok = c.post("/api/auth/login", json={"email": email.upper(), "password": "correct horse 1"})
    assert ok.status_code == 200 and ok.json()["role"] == "creator"
    assert c.post("/api/auth/login", json={"email": email, "password": "nope nope"}).status_code == 401
    assert c.post("/api/auth/login", json={"email": "creator@demo.test", "password": "x"}).status_code == 401


def test_self_signup_is_creator_only_by_default():
    for role in ["manager", "reviewer", "admin"]:
        assert signup(new_email(), role=role).status_code == 403


def test_legacy_signup_roles_cannot_bypass_admin_authorization(monkeypatch):
    monkeypatch.setenv("SIGNUP_ALLOWED_ROLES", "creator,manager,reviewer,admin")
    for role in ["manager", "reviewer", "admin"]:
        assert signup(new_email(), role=role).status_code == 403


def test_signup_validation():
    assert signup("not-an-email").status_code == 400
    assert signup(new_email(), password="short").status_code == 400
    assert signup(new_email(), role="superuser").status_code == 400
    assert signup(new_email(), name="  ").status_code == 400
    assert signup("creator@demo.test").status_code == 400
    e = new_email()
    assert signup(e).status_code == 200
    assert signup(e.upper()).status_code == 409


def test_signup_rate_limit():
    from app.routers import core
    core._signups.clear()
    codes = [c.post("/api/auth/signup", headers={"x-forwarded-for": "9.9.9.9"},
                    json={"email": new_email(), "password": "longenough1", "full_name": "A", "role": "creator"}).status_code
             for _ in range(7)]
    assert codes[:5] == [200] * 5 and codes[5] == 429
    core._signups.clear()


def test_password_hash_never_returned():
    r = signup(new_email())
    h = {"Authorization": "Bearer " + r.json()["session"]["token"]}
    assert "pw" not in r.text and "pw" not in c.get("/api/me", headers=h).text


def test_creators_cannot_see_each_others_content():
    a = {"Authorization": "Bearer " + signup(new_email()).json()["session"]["token"]}
    b = {"Authorization": "Bearer " + signup(new_email()).json()["session"]["token"]}
    cid = c.post("/api/content", headers=a, data={"title": "A's draft", "text": "hello you"}).json()["id"]
    assert c.get(f"/api/content/{cid}", headers=a).status_code == 200
    # Creator B gets the same 404 as for a missing item, on every route that takes the ID
    assert c.get(f"/api/content/{cid}", headers=b).status_code == 404
    assert c.get(f"/api/content/{cid}/image", headers=b).status_code == 404
    assert c.post(f"/api/content/{cid}/comments", headers=b, json={"body": "hi"}).status_code == 404
    assert c.get(f"/api/audit?content_id={cid}", headers=b).status_code == 404
    assert c.post(f"/api/content/{cid}/review", headers=b).status_code == 404
    # Reviewers still see everything in the workspace
    m = c.post("/api/auth/demo-login", json={"role": "manager"}).json()["token"]
    assert c.get(f"/api/content/{cid}", headers={"Authorization": "Bearer " + m}).status_code == 200

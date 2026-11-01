"""Sign-up and sign-in hardening: password rules, self-service roles, password hashing, rate limits and demo mode."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.passwords import check_password
from app.routers import core
from app.store import get_store

c = TestClient(app, raise_server_exceptions=False)
STRONG = "violet harbour 42 lantern"


@pytest.fixture(autouse=True)
def clear_rate_limits():
    for bucket in (core._signups, core._logins, core._demos):
        bucket.clear()
    yield
    for bucket in (core._signups, core._logins, core._demos):
        bucket.clear()


def new_email():
    return f"person-{uuid.uuid4().hex[:8]}@example.com"


def signup(email=None, password=STRONG, role="creator", name="Asha Verma", headers=None):
    return c.post("/api/auth/signup", headers=headers or {},
                  json={"email": email or new_email(), "password": password, "full_name": name, "role": role})


def stored_profile(email):
    return next(p for p in get_store().select("profiles") if p.get("email") == email)


# --- password rules ---

@pytest.mark.parametrize("password, says", [
    ("short1", "at least 10"),
    ("a" * 129, "at most 128"),
    ("aaaaaaaaaaaa", "repeats"),
    ("1234567890123", "Add letters"),
    ("Password123", "too common"),
    ("qwertyuiop99", "too common"),
    ("BrandGuard2026!", "brand name"),  # the old published demo password must never be accepted again
    ("my-glowleaf-2026-x", "brand name"),
])
def test_weak_passwords_are_refused_with_a_reason(password, says):
    reason = check_password(password, email="someone@example.com", name="Asha Verma")
    assert reason and says in reason


def test_password_cannot_contain_email_or_name():
    assert "email" in check_password("zorbaxmail-77-lamp", email="zorbaxmail@example.com", name="Asha Verma")
    assert "name" in check_password("my-verma-is-cool-77", email="x@example.com", name="Asha Verma")


def test_long_unrelated_phrase_is_fine():
    assert check_password(STRONG, email="asha@example.com", name="Asha Verma") is None


def test_server_enforces_the_rules_at_signup():
    assert signup(password="short").status_code == 400
    r = signup(password="Password123")
    assert r.status_code == 400 and "common" in r.json()["detail"]
    assert signup().status_code == 200


# --- roles ---

def test_only_creator_is_self_service_by_default():
    for role in ("admin", "manager", "reviewer"):
        r = signup(role=role)
        assert r.status_code == 403 and "creator" in r.json()["detail"].lower()
    assert signup(role="creator").status_code == 200
    assert signup(role="not-a-role").status_code == 400


def test_signup_roles_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("SIGNUP_ALLOWED_ROLES", "creator,manager,reviewer,admin")
    assert signup(role="admin").status_code == 200


def test_health_reports_demo_mode_and_signup_roles():
    h = c.get("/api/health").json()
    assert h["demo_mode"] is True
    assert h["signup_roles"] == ["creator"] and h["signup"] == "open"


# --- password storage (offline store) ---

def test_password_kept_only_as_salted_slow_hash_with_fresh_salt():
    first, second = new_email(), new_email()
    signup(first)
    signup(second)
    scheme, iterations, salt, _ = stored_profile(first)["pw"].split("$")
    assert scheme == "pbkdf2_sha256" and int(iterations) >= 600_000 and len(salt) >= 32
    assert STRONG not in stored_profile(first)["pw"]
    assert stored_profile(second)["pw"].split("$")[2] != salt


def test_login_accepts_right_password_and_refuses_wrong_one():
    email = new_email()
    signup(email)
    assert c.post("/api/auth/login", json={"email": email, "password": STRONG}).status_code == 200
    assert c.post("/api/auth/login", json={"email": email, "password": STRONG + "x"}).status_code == 401


# --- rate limits ---

def test_forged_left_of_x_forwarded_for_does_not_dodge_the_signup_limit():
    codes = [signup(headers={"x-forwarded-for": f"10.0.0.{i}, 203.0.113.9"}).status_code for i in range(6)]
    assert codes == [200] * 5 + [429]


def test_repeated_wrong_passwords_are_throttled():
    email = new_email()
    signup(email)
    codes = [c.post("/api/auth/login", json={"email": email, "password": "wrong password!"}).status_code
             for _ in range(12)]
    assert codes[0] == 401 and 429 in codes


# --- demo mode ---

def test_demo_accounts_can_be_switched_off(monkeypatch):
    assert c.post("/api/auth/demo-login", json={"role": "creator"}).status_code == 200
    monkeypatch.setattr(get_settings(), "demo_mode", False)
    assert c.post("/api/auth/demo-login", json={"role": "creator"}).status_code == 404
    assert c.post("/api/auth/demo-session", json={"role": "creator"}).status_code == 404
    assert c.get("/api/health").json()["demo_mode"] is False


def test_demo_session_is_supabase_only():
    assert c.post("/api/auth/demo-session", json={"role": "creator"}).status_code == 404


# --- who may sign up (demo mode off) ---

@pytest.fixture
def demo_off(monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_mode", False)
    monkeypatch.delenv("SIGNUP_ORG_ID", raising=False)
    monkeypatch.delenv("SIGNUP_INVITE_CODE", raising=False)


def test_signup_is_closed_without_a_shared_workspace_or_invite_code(demo_off):
    assert c.get("/api/health").json()["signup"] == "closed"
    r = signup()
    assert r.status_code == 403 and "closed" in r.json()["detail"]


def test_invite_code_is_required_when_configured(demo_off, monkeypatch):
    monkeypatch.setenv("SIGNUP_INVITE_CODE", "glow-2026-team")
    assert c.get("/api/health").json()["signup"] == "invite"
    assert signup().status_code == 403
    r = c.post("/api/auth/signup", json={"email": new_email(), "password": STRONG, "full_name": "Asha Verma",
                                         "role": "creator", "invite_code": "wrong-code"})
    assert r.status_code == 403 and "invite code" in r.json()["detail"]
    r = c.post("/api/auth/signup", json={"email": new_email(), "password": STRONG, "full_name": "Asha Verma",
                                         "role": "creator", "invite_code": " glow-2026-team "})
    assert r.status_code == 200


def test_explicit_signup_workspace_is_open(demo_off, monkeypatch):
    from app.seed_data import ORG_ID
    monkeypatch.setenv("SIGNUP_ORG_ID", ORG_ID)
    assert c.get("/api/health").json()["signup"] == "open"
    assert signup().status_code == 200


# --- logout, startup guard, rate-limit memory ---

def test_logout_evicts_the_cached_token():
    from app import auth
    from app.models.enums import UserRole
    user = auth.UserContext(user_id=uuid.uuid4(), email="a@b.co", org_id=uuid.uuid4(), role=UserRole.CREATOR)
    auth.cache_user("supabase-access-token", user)
    assert auth.cached_user("supabase-access-token") == user
    r = c.post("/api/auth/logout", headers={"Authorization": "Bearer supabase-access-token"})
    assert r.status_code == 200 and r.json() == {"ok": True}
    assert auth.cached_user("supabase-access-token") is None
    assert c.post("/api/auth/logout").status_code in (401, 403)  # needs a bearer token


def test_api_refuses_to_start_with_published_demo_password(monkeypatch):
    from app import config, main
    monkeypatch.setattr(config.Settings, "use_supabase", property(lambda self: True))
    monkeypatch.setattr(main.settings, "demo_mode", True)
    monkeypatch.setattr(main.settings, "demo_password", "BrandGuard2026!")
    with pytest.raises(RuntimeError, match="default DEMO_USER_PASSWORD"):
        main.announce()
    monkeypatch.setattr(main.settings, "demo_password", "a-long-random-rotated-secret-123")
    main.announce()  # a real secret starts fine


def test_rate_limit_memory_is_bounded_and_empty_entries_are_dropped(monkeypatch):
    from starlette.requests import Request
    bucket = {}
    req = Request({"type": "http", "headers": [], "client": ("203.0.113.9", 1)})
    monkeypatch.setattr(core, "MAX_THROTTLE_IPS", 10)
    for i in range(25):
        core.throttle(bucket, req, 5, "slow down", key=f"10.0.0.{i}")
    assert len(bucket) <= 10 and "10.0.0.24" in bucket
    monkeypatch.setattr(core.time, "time", lambda: 10**12)  # every entry has expired
    core.throttle(bucket, req, 5, "slow down", key="10.0.0.24")
    assert len(bucket[("10.0.0.24")]) == 1  # the expired timestamps were dropped, not counted

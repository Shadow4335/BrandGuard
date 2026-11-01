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

def test_admin_is_not_self_service_by_default():
    r = signup(role="admin")
    assert r.status_code == 403 and "demo" in r.json()["detail"].lower()
    assert signup(role="manager").status_code == 200
    assert signup(role="not-a-role").status_code == 400


def test_signup_roles_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("SIGNUP_ALLOWED_ROLES", "creator,manager,reviewer,admin")
    assert signup(role="admin").status_code == 200


def test_health_reports_demo_mode_and_signup_roles():
    h = c.get("/api/health").json()
    assert h["demo_mode"] is True
    assert "creator" in h["signup_roles"] and "admin" not in h["signup_roles"]


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

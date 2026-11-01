"""Google sign-in through Firebase: a verified Google email maps to a BrandGuard account and an ordinary session."""
import uuid
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.routers import core

c = TestClient(app, raise_server_exceptions=False)
PROJECT = "brandguard-test"
ORG = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def google_enabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "firebase_project_id", PROJECT)
    for bucket in (core._google, core._signups):
        bucket.clear()
    yield
    for bucket in (core._google, core._signups):
        bucket.clear()


def google_account(email, verified=True, name="Gina Google"):
    """Patch token verification to accept "valid-token" as this Google account."""
    claims = {"iss": f"https://securetoken.google.com/{PROJECT}", "sub": uuid.uuid4().hex,
              "email": email, "email_verified": verified, "name": name}
    return lambda token: claims if token == "valid-token" else None


def sign_in(role=None, token="valid-token"):
    return c.post("/api/auth/google", json={"id_token": token, **({"role": role} if role else {})})


def fresh_email():
    return f"g-{uuid.uuid4().hex[:8]}@gmail.com"


# --- offline (memory) store ---------------------------------------------------------------------------------------

def test_first_sign_in_creates_account_with_chosen_role_then_reuses_it(monkeypatch):
    email = fresh_email()
    monkeypatch.setattr(core, "verify_firebase_token", google_account(email))
    first = sign_in(role="creator")
    assert first.status_code == 200 and first.json()["created"] is True
    me = c.get("/api/me", headers={"Authorization": "Bearer " + first.json()["session"]["token"]}).json()
    assert (me["email"], me["role"], me["full_name"]) == (email, "creator", "Gina Google")
    again = sign_in(role="manager")  # the role only applies to a new account
    assert again.json()["created"] is False and again.json()["session"]["role"] == "creator"


def test_links_to_existing_password_account(monkeypatch):
    email = fresh_email()
    c.post("/api/auth/signup", json={"email": email, "password": "correct horse 1", "full_name": "Pat", "role": "creator"})
    monkeypatch.setattr(core, "verify_firebase_token", google_account(email))
    r = sign_in()
    assert r.status_code == 200 and r.json()["created"] is False and r.json()["session"]["role"] == "creator"


def test_rejects_invalid_token_unverified_email_admin_role_and_demo_addresses(monkeypatch):
    monkeypatch.setattr(core, "verify_firebase_token", google_account(fresh_email(), verified=False))
    assert sign_in(token="forged").status_code == 401
    assert sign_in().status_code == 403
    monkeypatch.setattr(core, "verify_firebase_token", google_account(fresh_email()))
    assert sign_in(role="admin").status_code == 403
    monkeypatch.setattr(core, "verify_firebase_token", google_account("creator@demo.test"))
    assert sign_in().status_code == 403


def test_off_unless_configured(monkeypatch):
    monkeypatch.setattr(get_settings(), "firebase_project_id", "")
    assert sign_in().status_code == 404
    assert c.get("/api/health").json()["firebase_enabled"] is False


def test_real_verifier_rejects_garbage():
    from app.firebase_auth import verify_firebase_token
    assert verify_firebase_token("not-a-jwt") is None


# --- Supabase mode, against a fake client --------------------------------------------------------------------------

LINK_USER, NEW_USER = str(uuid.uuid4()), str(uuid.uuid4())


class FakeSupabase:
    """The parts of the Supabase client the endpoint uses. `link_makes_user` mimics Supabase creating the auth user
    while generating a link for an unknown email."""

    def __init__(self, profiles, link_makes_user=False):
        self.profiles, self.link_makes_user, self.calls = profiles, link_makes_user, []
        self.auth = NS(admin=NS(generate_link=self._link, create_user=self._create, delete_user=lambda uid: None,
                                update_user_by_id=lambda uid, attrs: self.calls.append("update_user")))

    def _link(self, params):
        self.calls.append("generate_link")
        known = next((p for p in self.profiles if p["email"] == params["email"]), None)
        if not known and not self.link_makes_user:
            raise RuntimeError("User not found")
        return NS(user=NS(id=known["id"] if known else LINK_USER), properties=NS(hashed_token="hash"))

    def _create(self, attrs):
        self.calls.append("create_user")
        return NS(user=NS(id=NEW_USER))

    def table(self, name):
        def insert(row):
            self.profiles.append(row)
            return NS(execute=lambda: NS(data=[row]))
        return NS(insert=insert)


class FakeStore:
    def __init__(self, client):
        self.client = client

    def select(self, table, where=None, limit=None, **_):
        rows = [p for p in self.client.profiles if all(p.get(k) == v for k, v in (where or {}).items())]
        return rows[:limit] if limit else rows


@pytest.fixture
def supabase(monkeypatch):
    import supabase as supabase_pkg
    from app import config
    monkeypatch.setattr(config.Settings, "use_supabase", property(lambda self: True))
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)
    session = NS(access_token=f"access-{uuid.uuid4().hex}", refresh_token="refresh", expires_at=None)
    monkeypatch.setattr(supabase_pkg, "create_client", lambda *a: NS(auth=NS(verify_otp=lambda p: NS(session=session))))

    def connect(fake):
        monkeypatch.setattr(core, "get_store", lambda: FakeStore(fake))
        return session
    return connect


def test_returning_user_gets_session_and_profile_with_one_link(monkeypatch, supabase):
    from app.auth import cached_user
    uid = str(uuid.uuid4())
    fake = FakeSupabase([{"id": uid, "org_id": ORG, "role": "manager", "email": "pat@gmail.com", "full_name": "Pat"}])
    session = supabase(fake)
    monkeypatch.setattr(core, "verify_firebase_token", google_account("pat@gmail.com"))
    r = sign_in()
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["mode"], body["created"], body["access_token"]) == ("supabase", False, session.access_token)
    assert body["profile"]["id"] == uid and body["profile"]["role"] == "manager"
    assert fake.calls == ["generate_link"]
    assert cached_user(session.access_token).role.value == "manager"  # first API call skips Supabase


@pytest.mark.parametrize("link_makes_user, calls, uid", [
    (False, ["generate_link", "create_user", "generate_link"], NEW_USER),
    (True, ["generate_link", "update_user", "generate_link"], LINK_USER),
])
def test_new_user_whether_or_not_the_early_link_made_the_auth_user(monkeypatch, supabase, link_makes_user, calls, uid):
    fake = FakeSupabase([], link_makes_user=link_makes_user)
    supabase(fake)
    monkeypatch.setattr(core, "verify_firebase_token", google_account("new@gmail.com"))
    r = sign_in(role="creator")
    assert r.status_code == 200, r.text
    assert r.json()["created"] is True and r.json()["profile"]["role"] == "creator"
    assert fake.calls == calls and fake.profiles[0]["id"] == uid


# --- verified-token cache ------------------------------------------------------------------------------------------

def test_token_cache_honours_ttl_and_token_expiry(monkeypatch):
    from app import auth
    from app.models.enums import UserRole
    user = auth.UserContext(user_id=uuid.uuid4(), email="a@b.co", org_id=uuid.uuid4(), role=UserRole.CREATOR)
    auth.cache_user("token-a", user)
    assert auth.cached_user("token-a") == user
    auth.cache_user("token-b", user, token_expires_at=1.0)  # already expired
    assert auth.cached_user("token-b") is None
    monkeypatch.setattr(auth.time, "time", lambda: 10**12)
    assert auth.cached_user("token-a") is None


@pytest.mark.parametrize("role", ["manager", "reviewer", "admin"])
def test_google_sign_up_with_a_privileged_role_needs_the_admin_password(monkeypatch, role):
    monkeypatch.setenv("PRIVILEGED_SIGNUP_PASSWORD", "orchid-ledger-7731-quiet")
    monkeypatch.setattr(core, "verify_firebase_token", google_account(fresh_email()))
    assert sign_in(role=role).status_code == 403
    r = c.post("/api/auth/google", json={"id_token": "valid-token", "role": role,
                                         "role_password": "orchid-ledger-7731-quiet"})
    assert r.status_code == 200 and r.json()["created"] is True and r.json()["session"]["role"] == role

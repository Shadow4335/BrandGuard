"""Latest kit invariants: elevated signup and real workspace isolation."""
import uuid
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.store import get_store
from app.auth import _context_from_profile
from app.routers import core, workspaces
from app.config import get_settings

c = TestClient(app, raise_server_exceptions=False)

@pytest.mark.parametrize("role", ["manager", "reviewer", "admin"])
def test_all_elevated_roles_need_correct_password_even_with_legacy_public_config(monkeypatch, role):
    secret = "test-server-authorization-5319"
    monkeypatch.setenv("PRIVILEGED_SIGNUP_PASSWORD", secret)
    monkeypatch.setenv("SIGNUP_ALLOWED_ROLES", "creator,manager,reviewer,admin")
    payload = {"email": f"kit-{uuid.uuid4().hex}@example.com", "password": "unrelated words 972", "full_name": "Kit Test", "role": role}
    assert c.post("/api/auth/signup", json=payload).status_code == 403
    assert c.post("/api/auth/signup", json={**payload, "role_password": "incorrect"}).status_code == 403
    result = c.post("/api/auth/signup", json={**payload, "role_password": secret})
    assert result.status_code == 200 and result.json()["role"] == role
    assert secret not in result.text

@pytest.mark.parametrize("role", ["manager", "reviewer", "admin"])
def test_google_rejection_has_no_supabase_account_side_effect(monkeypatch, role):
    from app.config import Settings
    monkeypatch.setattr(Settings, "use_supabase", property(lambda self: True))
    monkeypatch.setattr(get_settings(), "firebase_project_id", "test-project")
    monkeypatch.setenv("SIGNUP_ALLOWED_ROLES", "creator,manager,reviewer,admin")
    monkeypatch.setattr(core, "verify_firebase_token", lambda _: {"email": "new-kit@example.com", "email_verified": True})
    calls = []
    fake = NS(select=lambda *a, **k: [], client=NS(auth=NS(admin=NS(generate_link=lambda _: calls.append("link"), create_user=lambda _: calls.append("create")))))
    monkeypatch.setattr(core, "get_store", lambda: fake)
    r = c.post("/api/auth/google", json={"id_token": "test-token", "role": role, "role_password": "incorrect"})
    assert r.status_code == 403 and calls == []


def test_workspaces_only_returns_verified_profile_org():
    store = get_store()
    org = store.insert("organisations", {"name": "Isolated kit workspace"})
    profile = store.insert("profiles", {"id": str(uuid.uuid4()), "email": "kit-isolation@example.com", "org_id": org["id"], "role": "creator"})
    body = workspaces.list_workspaces(_context_from_profile(profile))
    assert body["current_id"] == org["id"]
    assert body["workspaces"] == [{"id": org["id"], "name": org["name"]}]
    assert body["can_create"] is False
    assert c.get("/api/workspaces").status_code in (401, 403)


def test_invalid_auth_payload_does_not_echo_credentials():
    r = c.post("/api/auth/signup", json={"email": "invalid", "password": {"secret": "do-not-echo"}, "full_name": "test", "role_password": "do-not-echo"})
    assert r.status_code == 422 and "do-not-echo" not in r.text


def test_real_workspace_create_switch_and_cross_tenant_denial():
    admin = c.post("/api/auth/demo-login", json={"role": "admin"}).json()
    headers = {"Authorization": "Bearer " + admin["token"]}
    created = c.post("/api/workspaces", headers=headers, json={"name": "New isolated workspace", "description": "Test workspace"})
    assert created.status_code == 200
    org = created.json()["id"]
    scoped = {**headers, "X-Workspace-ID": org}
    assert c.get("/api/me", headers=scoped).json()["org_id"] == org
    assert c.get("/api/me", headers=scoped).json()["role"] == "admin"
    assert c.get("/api/sources", headers=scoped).json() == []
    assert c.get("/api/content", headers=scoped).json() == []
    assert c.get("/api/workspaces", headers=scoped).json()["current_id"] == org
    creator = c.post("/api/auth/demo-login", json={"role": "creator"}).json()
    outsider = {"Authorization": "Bearer " + creator["token"], "X-Workspace-ID": org}
    for path in ["/api/me", "/api/content", "/api/sources", "/api/insights/summary", "/api/workspaces"]:
        assert c.get(path, headers=outsider).status_code == 403
    assert c.post("/api/workspaces", headers={"Authorization": "Bearer " + creator["token"]}, json={"name": "Forbidden"}).status_code == 403
    # Membership revocation takes effect immediately, even for an otherwise valid session.
    get_store().tables["workspace_memberships"] = [m for m in get_store().tables["workspace_memberships"] if m["org_id"] != org]
    assert c.get("/api/me", headers=scoped).status_code == 403


def test_alternate_workspace_uses_membership_role_not_home_admin_role():
    admin = c.post("/api/auth/demo-login", json={"role": "admin"}).json()
    org = get_store().insert("organisations", {"name": "Reviewer membership only"})
    get_store().insert("workspace_memberships", {"user_id": admin["user_id"], "org_id": org["id"], "role": "reviewer"})
    h = {"Authorization": "Bearer " + admin["token"], "X-Workspace-ID": org["id"]}
    assert c.get("/api/me", headers=h).json()["role"] == "reviewer"
    assert c.get("/api/workspaces", headers=h).json()["can_create"] is False
    assert c.post("/api/sources", headers=h, data={"kind": "guideline", "title": "Forbidden", "text": "Not allowed"}).status_code == 403
    assert c.post("/api/workspaces", headers=h, json={"name": "Forbidden"}).status_code == 403


def test_missing_optional_membership_migration_keeps_original_workspace(monkeypatch):
    admin = c.post("/api/auth/demo-login", json={"role": "admin"}).json()
    store = get_store()
    select = store.select
    def without_memberships(table, *args, **kwargs):
        if table == "workspace_memberships":
            raise RuntimeError("relation does not exist")
        return select(table, *args, **kwargs)
    monkeypatch.setattr(store, "select", without_memberships)
    h = {"Authorization": "Bearer " + admin["token"]}
    result = c.get("/api/workspaces", headers=h)
    assert result.status_code == 200
    assert result.json()["membership_mode"] == "single_workspace"
    assert result.json()["can_create"] is False
    assert result.json()["workspaces"][0]["id"] == admin["org_id"]
    assert c.post("/api/workspaces", headers=h, json={"name": "Unavailable"}).status_code == 503


def test_cached_supabase_identity_cannot_cache_alternate_workspace_access(monkeypatch):
    from app import auth
    from app.config import Settings
    store = get_store()
    user_id, original, alternate = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    base = _context_from_profile({"id": user_id, "email": "cached@example.com", "org_id": original, "role": "admin"})
    auth.cache_user("kit-cached-token", base)
    monkeypatch.setattr(Settings, "use_supabase", property(lambda self: True))
    store.insert("workspace_memberships", {"user_id": user_id, "org_id": alternate, "role": "creator"})
    h = {"Authorization": "Bearer kit-cached-token", "X-Workspace-ID": alternate}
    assert c.get("/api/me", headers=h).json()["role"] == "creator"
    store.tables["workspace_memberships"] = [m for m in store.tables["workspace_memberships"] if m["user_id"] != user_id]
    assert c.get("/api/me", headers=h).status_code == 403
    assert c.get("/api/me", headers={"Authorization": "Bearer kit-cached-token"}).json()["role"] == "admin"
    auth.evict_token("kit-cached-token")

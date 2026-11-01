"""Health, sign-up, demo login and 'who am I' endpoints."""
import hashlib
import os
import re
import secrets
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, Request

from app.audit import log_event
from app.auth import UserContext, _context_from_profile, cache_user, get_current_user
from app.config import get_settings
from app.firebase_auth import verify_firebase_token
from app.models.api import (DemoLoginIn, DemoLoginOut, DemoSessionOut, GoogleLoginIn, GoogleLoginOut, HealthOut, LoginIn,
                            SignupIn, SignupOut)
from app.passwords import check_password
from app.seed_data import ORG_ID
from app.store import get_store

router = APIRouter(prefix="/api", tags=["Core"])
ROLES = {"admin", "creator", "manager", "reviewer"}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
SIGNUP_LIMIT, SIGNUP_WINDOW = 5, 600  # per IP: 5 sign-ups per 10 minutes
LOGIN_LIMIT, DEMO_LIMIT = 10, 30        # per IP per 10 minutes: offline password logins, demo sessions
PBKDF2_ITERATIONS = 600_000            # OWASP (2023) figure for PBKDF2-HMAC-SHA256
_signups: dict = defaultdict(deque)
_logins: dict = defaultdict(deque)
_demos: dict = defaultdict(deque)
_google: dict = defaultdict(deque)


@router.get("/health", response_model=HealthOut)
def health():
    s = get_settings()
    return HealthOut(ai_provider=(s.llm_provider if s.llm_api_key else s.llm_backup_provider) if s.llm_available
                     else "mock (rule-based fallback)",
                     ai_live=s.llm_available, ai_backup=s.llm_backup_provider if s.llm_backup_ready else "", store="supabase" if s.use_supabase else "memory",
                     version=s.app_version, commit=os.getenv("RENDER_GIT_COMMIT", "local")[:7],
                     demo_mode=s.demo_mode, signup_roles=s.signup_roles,
                     firebase_enabled=bool(s.firebase_project_id))


@router.get("/me")
def me(user: UserContext = Depends(get_current_user)):
    return {"user_id": str(user.user_id), "email": user.email, "org_id": str(user.org_id),
            "role": user.role.value, "full_name": user.full_name}


def _session(p: dict) -> DemoLoginOut:
    return DemoLoginOut(token=f"demo.{p['id']}", user_id=p["id"], email=p["email"], org_id=p["org_id"],
                        role=p["role"], full_name=p.get("full_name"))


def _hash(password: str, salt: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def _stored_hash(password: str) -> str:
    """Salted hash that records its own parameters: pbkdf2_sha256$<iterations>$<salt>$<digest>."""
    salt = secrets.token_hex(16)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${_hash(password, salt)}"


def _verify_hash(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt, digest = stored.split("$", 3)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256" or not iterations.isdigit():
        return False
    return secrets.compare_digest(_hash(password, salt, int(iterations)), digest)


def _client_ip(request: Request) -> str:
    """The client address as the hosting proxy saw it. The left of X-Forwarded-For is whatever the client sent, so use
    the right-most entry, which the proxy appends."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip() or "?"
    return request.client.host if request.client else "?"


def _throttle(bucket: dict, request: Request, limit: int, message: str, window: int = SIGNUP_WINDOW) -> None:
    """Allow `limit` requests per client address per `window` seconds (in memory, per server instance)."""
    q, now = bucket[_client_ip(request)], time.time()
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, message)
    q.append(now)


def _rate_limit(request: Request) -> None:
    _throttle(_signups, request, SIGNUP_LIMIT, "Too many sign-ups from this network. Please wait a few minutes and try again.")


@router.post("/auth/signup", response_model=SignupOut)
def signup(body: SignupIn, request: Request):
    """Create a real account in the shared GlowLeaf Naturals demo workspace with the chosen role.
    The account is confirmed immediately (no email step) so judges can try every role."""
    email = body.email.strip().lower()
    name = body.full_name.strip()
    if not EMAIL.match(email):
        raise HTTPException(400, "Enter a valid email address.")
    if email.endswith("@demo.test"):
        raise HTTPException(400, "That address is reserved for the demo accounts. Use your own email.")
    if not name or len(name) > 80:
        raise HTTPException(400, "Enter your name (up to 80 characters).")
    problem = check_password(body.password, email=email, name=name)
    if problem:
        raise HTTPException(400, problem)
    if body.role not in ROLES:
        raise HTTPException(400, "Choose a role: creator, manager or reviewer.")
    if body.role not in get_settings().signup_roles:
        raise HTTPException(403, "That role can't be chosen when signing up. Pick another, or use the one-click demo account for it on the sign-in page.")
    _rate_limit(request)

    s, store = get_settings(), get_store()
    org = os.getenv("SIGNUP_ORG_ID", ORG_ID)
    if not s.use_supabase:
        if any((p.get("email") or "").lower() == email for p in store.select("profiles")):
            raise HTTPException(409, "An account with this email already exists. Sign in instead.")
        p = store.insert("profiles", {"id": str(uuid.uuid4()), "org_id": org, "role": body.role, "email": email,
                                      "full_name": name, "pw": _stored_hash(body.password)})
        log_event(org, p["id"], "user_signed_up", "profile", p["id"], {"role": body.role})
        return SignupOut(email=email, role=body.role, mode="memory", session=_session(p))

    client = store.client  # type: ignore[attr-defined]
    try:
        created = client.auth.admin.create_user({"email": email, "password": body.password, "email_confirm": True,
                                                 "user_metadata": {"full_name": name, "role": body.role}})
        uid = created.user.id
    except Exception as e:
        msg = str(e).lower()
        if "already" in msg or "registered" in msg or "exists" in msg:
            raise HTTPException(409, "An account with this email already exists. Sign in instead.")
        if "password" in msg:
            raise HTTPException(400, "That password was rejected. Try a longer one with letters and numbers.")
        raise HTTPException(502, "We couldn't create your account right now. Please try again.")
    try:
        client.table("profiles").insert({"id": uid, "org_id": org, "role": body.role, "email": email,
                                         "full_name": name}).execute()
    except Exception:
        try:
            client.auth.admin.delete_user(uid)  # don't leave a login without a profile
        except Exception:
            pass
        raise HTTPException(502, "We couldn't finish setting up your account. Please try again.")
    log_event(org, uid, "user_signed_up", "profile", uid, {"role": body.role})
    return SignupOut(email=email, role=body.role, mode="supabase")


@router.post("/auth/login", response_model=DemoLoginOut)
def memory_login(body: LoginIn, request: Request):
    """Offline demo mode only: password login for accounts created with /auth/signup."""
    if get_settings().use_supabase:
        raise HTTPException(404, "Use Supabase sign-in.")
    _throttle(_logins, request, LOGIN_LIMIT, "Too many sign-in attempts. Please wait a few minutes and try again.")
    email = body.email.strip().lower()
    p = next((p for p in get_store().select("profiles") if (p.get("email") or "").lower() == email), None)
    if not p or not _verify_hash(body.password, p.get("pw") or ""):
        raise HTTPException(401, "Wrong email or password.")
    return _session(p)


@router.post("/auth/demo-login", response_model=DemoLoginOut)
def demo_login(body: DemoLoginIn):
    """Offline demo only: returns a token for a seeded user. Disabled when Supabase Auth is in use."""
    if not get_settings().demo_mode:
        raise HTTPException(404, "Demo accounts are switched off on this server.")
    if get_settings().use_supabase:
        raise HTTPException(404, "Demo login is only available in offline demo mode. Use Supabase sign-in.")
    rows = [p for p in get_store().select("profiles") if (p.get("email") or "").startswith(f"{body.role}@")]
    if not rows:
        raise HTTPException(404, "Unknown demo role. Choose admin, creator, manager or reviewer.")
    return _session(rows[0])


@router.post("/auth/demo-session", response_model=DemoSessionOut)
def demo_session(body: DemoLoginIn, request: Request):
    """Supabase mode: the server signs a seeded demo user in and returns the session tokens, so the demo password
    never ships to the browser. Turned off by DEMO_MODE=false."""
    s = get_settings()
    if not s.demo_mode:
        raise HTTPException(404, "Demo accounts are switched off on this server.")
    if not s.use_supabase:
        raise HTTPException(404, "Use the offline demo login.")
    if body.role not in ROLES:
        raise HTTPException(400, "Unknown demo role. Choose admin, creator, manager or reviewer.")
    _throttle(_demos, request, DEMO_LIMIT, "Too many demo sign-ins from this network. Please wait a few minutes and try again.")
    try:
        # A throwaway anon client, so the service-role client never holds a user session
        from supabase import create_client
        session = create_client(s.supabase_url, s.supabase_anon_key).auth.sign_in_with_password(
            {"email": f"{body.role}@demo.test", "password": s.demo_password}).session
    except Exception:
        session = None
    if not session:
        raise HTTPException(502, "Demo sign-in is unavailable right now. Please try again in a moment.")
    return DemoSessionOut(access_token=session.access_token, refresh_token=session.refresh_token)


@router.post("/auth/google", response_model=GoogleLoginOut)
def google_login(body: GoogleLoginIn, request: Request):
    """Google sign-in through Firebase. The verified Google email picks the BrandGuard account; a first sign-in creates
    it (with the chosen role) in the shared workspace. Returns an ordinary session, so nothing else changes."""
    s, store = get_settings(), get_store()
    if not s.firebase_project_id:
        raise HTTPException(404, "Google sign-in isn't set up on this server.")
    _throttle(_google, request, LOGIN_LIMIT, "Too many sign-in attempts. Please wait a few minutes and try again.")
    claims = verify_firebase_token(body.id_token)
    if not claims:
        raise HTTPException(401, "We couldn't verify your Google sign-in. Please try again.")
    email = (claims.get("email") or "").strip().lower()
    if not email or not claims.get("email_verified"):
        raise HTTPException(403, "Your Google account doesn't have a verified email address.")
    if email.endswith("@demo.test"):
        raise HTTPException(403, "That address is reserved for the demo accounts.")
    name = (claims.get("name") or email.split("@")[0]).strip()[:80]
    default_role = "creator" if "creator" in s.signup_roles else (s.signup_roles or ["creator"])[0]
    role = body.role or default_role
    org = os.getenv("SIGNUP_ORG_ID", ORG_ID)

    def find_profile():
        rows = store.select("profiles", {"email": email}, limit=1)
        return rows[0] if rows else None

    if not s.use_supabase:
        profile = find_profile()
        created = profile is None
        if created:
            if role not in s.signup_roles:
                raise HTTPException(403, "That role can't be chosen when signing up. Pick another.")
            profile = store.insert("profiles", {"id": str(uuid.uuid4()), "org_id": org, "role": role,
                                                "email": email, "full_name": name})
            log_event(org, profile["id"], "user_signed_up", "profile", profile["id"], {"role": role, "via": "google"})
        return GoogleLoginOut(mode="memory", created=created, session=_session(profile))

    admin = store.client.auth.admin  # type: ignore[attr-defined]

    def magic_link():
        return admin.generate_link({"type": "magiclink", "email": email})

    # Returning users are the common case: look up the profile and make the one-time sign-in link at the same time
    # (one Supabase round trip instead of two).
    with ThreadPoolExecutor(max_workers=2) as pool:
        profile_job, link_job = pool.submit(find_profile), pool.submit(magic_link)
        profile = profile_job.result()
        try:
            early_link = link_job.result()
        except Exception:
            early_link = None  # e.g. the email has no auth user yet

    created = profile is None
    if created:
        if role not in s.signup_roles:
            raise HTTPException(403, "That role can't be chosen when signing up. Pick another.")
        meta = {"full_name": name, "role": role, "firebase_uid": claims.get("sub")}
        try:
            if early_link and early_link.user:
                # Supabase can create the auth user while making a link for an unknown email: adopt that user
                uid = early_link.user.id
                admin.update_user_by_id(uid, {"email_confirm": True, "user_metadata": meta})
            else:
                # Random password: this account signs in with Google only
                uid = admin.create_user({"email": email, "password": secrets.token_urlsafe(32), "email_confirm": True,
                                         "user_metadata": meta}).user.id
        except Exception as e:
            if any(w in str(e).lower() for w in ("already", "registered", "exists")):
                raise HTTPException(409, "An account with this email exists but isn't set up. Ask an admin.")
            raise HTTPException(502, "We couldn't create your account right now. Please try again.")
        profile = {"id": uid, "org_id": org, "role": role, "email": email, "full_name": name}
        try:
            store.client.table("profiles").insert(profile).execute()  # type: ignore[attr-defined]
        except Exception:
            try:
                admin.delete_user(uid)  # don't leave a login without a profile
            except Exception:
                pass
            raise HTTPException(502, "We couldn't finish setting up your account. Please try again.")
        log_event(org, uid, "user_signed_up", "profile", uid, {"role": role, "via": "google"})
        early_link = None  # an early link for a brand-new user may be a sign-up link: make a fresh magic link

    try:
        # Redeem the one-time link on a throwaway anon client, so the service-role client never holds a user session
        from supabase import create_client
        link = early_link or magic_link()
        session = create_client(s.supabase_url, s.supabase_anon_key).auth.verify_otp(
            {"token_hash": link.properties.hashed_token, "type": "magiclink"}).session
    except Exception:
        session = None
    if not session:
        raise HTTPException(502, "Google sign-in is unavailable right now. Please try again in a moment.")

    user = _context_from_profile(profile, email)
    cache_user(session.access_token, user, getattr(session, "expires_at", None))  # the first API calls skip Supabase
    return GoogleLoginOut(mode="supabase", created=created, access_token=session.access_token,
                          refresh_token=session.refresh_token,
                          profile={"id": str(user.user_id), "org_id": str(user.org_id), "role": user.role.value,
                                   "email": email, "full_name": user.full_name})

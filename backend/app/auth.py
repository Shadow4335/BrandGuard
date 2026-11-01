import hashlib
import threading
import time
from typing import Dict, Optional, Tuple
from uuid import UUID
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import get_settings
from app.store import get_store
from app.models.enums import UserRole

security = HTTPBearer(auto_error=True)

# Recently verified Supabase tokens. Checking a token costs two Supabase round trips (auth + profile), which made every
# API call slow; reusing the result for a short time is safe because tokens are short-lived anyway. A role change or a
# removed profile takes effect within TOKEN_CACHE_TTL seconds.
TOKEN_CACHE_TTL, TOKEN_CACHE_SIZE = 60, 2000
_token_cache: Dict[str, Tuple[float, "UserContext"]] = {}
_token_lock = threading.Lock()


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()  # keep hashes, not bearer tokens, in memory


def cache_user(token: str, user: "UserContext", token_expires_at: Optional[float] = None) -> None:
    """Remember a verified token for TOKEN_CACHE_TTL seconds, or until the token expires if that is sooner."""
    now = time.time()
    until = min(now + TOKEN_CACHE_TTL, token_expires_at or float("inf"))
    with _token_lock:
        if len(_token_cache) >= TOKEN_CACHE_SIZE:
            stale = [k for k, (t, _) in _token_cache.items() if t <= now]
            for k in stale or list(_token_cache)[: TOKEN_CACHE_SIZE // 2]:
                del _token_cache[k]
        _token_cache[_digest(token)] = (until, user)


def evict_token(token: str) -> None:
    """Forget a cached token, e.g. on sign-out, so it stops working here straight away."""
    with _token_lock:
        _token_cache.pop(_digest(token), None)


def cached_user(token: str) -> Optional["UserContext"]:
    with _token_lock:
        entry = _token_cache.get(_digest(token))
    return entry[1] if entry and entry[0] > time.time() else None


class UserContext(BaseModel):
    user_id: UUID
    email: str
    org_id: UUID
    role: UserRole
    full_name: Optional[str] = None


def _context_from_profile(data: dict, fallback_email: str = "") -> UserContext:
    return UserContext(
        user_id=UUID(data["id"]),
        email=data.get("email") or fallback_email,
        org_id=UUID(data["org_id"]),
        role=UserRole(data["role"]),
        full_name=data.get("full_name"),
    )


def _workspace_context(base: UserContext, selected: Optional[str]) -> UserContext:
    if not selected or selected == str(base.org_id):
        return base
    try:
        org = str(UUID(selected))
        rows = get_store().select("workspace_memberships", {"user_id": str(base.user_id), "org_id": org}, limit=1)
    except Exception:
        rows = []
    if not rows:
        raise HTTPException(403, "You don't have access to that workspace. Choose your default workspace or ask an admin.")
    return base.model_copy(update={"org_id": UUID(org), "role": UserRole(rows[0]["role"])})


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> UserContext:
    """Resolve identity from the bearer token and validate any selected workspace against server membership."""
    token = credentials.credentials
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in to continue.",
                            headers={"WWW-Authenticate": "Bearer"})

    settings = get_settings()
    store = get_store()

    # Offline demo mode: tokens look like "demo.<profile id>"
    if not settings.use_supabase:
        if token.startswith("demo."):
            profile = store.get("profiles", token[5:])
            if profile:
                return _workspace_context(_context_from_profile(profile), request.headers.get("x-workspace-id"))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session expired. Please sign in again.",
                            headers={"WWW-Authenticate": "Bearer"})

    hit = cached_user(token)
    if hit:
        return _workspace_context(hit, request.headers.get("x-workspace-id"))
    try:
        # Verify the token with Supabase Auth; no local JWT secret is needed.
        auth_response = store.client.auth.get_user(token)  # type: ignore[attr-defined]
        user = auth_response.user if auth_response else None
    except Exception:
        user = None
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session expired. Please sign in again.",
                            headers={"WWW-Authenticate": "Bearer"})

    profile = store.get("profiles", user.id)
    if not profile:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No BrandGuard profile exists for this account. Ask an admin.")
    context = _context_from_profile(profile, user.email or "")
    cache_user(token, context)
    return _workspace_context(context, request.headers.get("x-workspace-id"))


def require_roles(*allowed_roles: UserRole):
    """Dependency factory to enforce role-based access control."""
    def role_checker(current_user: UserContext = Depends(get_current_user)) -> UserContext:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role ({current_user.role.value}) cannot do this. Allowed: {', '.join(r.value for r in allowed_roles)}.",
            )
        return current_user
    return role_checker

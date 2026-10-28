from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import get_settings
from app.store import get_store
from app.models.enums import UserRole

security = HTTPBearer(auto_error=True)


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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> UserContext:
    """Resolve role + org from the bearer token. org_id always comes from the profile, never the client."""
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
                return _context_from_profile(profile)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session expired. Please sign in again.",
                            headers={"WWW-Authenticate": "Bearer"})

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
    return _context_from_profile(profile, user.email or "")


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

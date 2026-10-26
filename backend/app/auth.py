from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import Client, create_client

from app.config import get_settings
from app.models.enums import UserRole

security = HTTPBearer(auto_error=True)


class UserContext(BaseModel):
    user_id: UUID
    email: str
    org_id: UUID
    role: UserRole
    full_name: Optional[str] = None


def get_supabase_service_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase credentials are not configured on server",
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> UserContext:
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    supabase = get_supabase_service_client()

    try:
        # GEMINI.md Rule: verify token by calling supabase auth get_user(token) with service client
        # Do not use a local JWT secret.
        auth_response = supabase.auth.get_user(token)
        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = auth_response.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Load profile (role + org_id) from profiles table
    try:
        profile_res = (
            supabase.table("profiles")
            .select("id, org_id, role, full_name, email")
            .eq("id", user.id)
            .single()
            .execute()
        )
        if not profile_res.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User profile not found for this account",
            )
        data = profile_res.data
        return UserContext(
            user_id=UUID(data["id"]),
            email=data.get("email") or user.email or "",
            org_id=UUID(data["org_id"]),
            role=UserRole(data["role"]),
            full_name=data.get("full_name"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}",
        )


def require_roles(*allowed_roles: UserRole):
    """Dependency factory to enforce role-based access control."""
    def role_checker(current_user: UserContext = Depends(get_current_user)) -> UserContext:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role in {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker

"""Health, demo login and 'who am I' endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.auth import UserContext, get_current_user
from app.config import get_settings
from app.models.api import DemoLoginIn, DemoLoginOut, HealthOut
from app.store import get_store

router = APIRouter(prefix="/api", tags=["Core"])


@router.get("/health", response_model=HealthOut)
def health():
    s = get_settings()
    return HealthOut(ai_provider=s.llm_provider if s.llm_available else "mock (rule-based fallback)",
                     ai_live=s.llm_available, store="supabase" if s.use_supabase else "memory")


@router.get("/me")
def me(user: UserContext = Depends(get_current_user)):
    return {"user_id": str(user.user_id), "email": user.email, "org_id": str(user.org_id),
            "role": user.role.value, "full_name": user.full_name}


@router.post("/auth/demo-login", response_model=DemoLoginOut)
def demo_login(body: DemoLoginIn):
    """Offline demo only: returns a token for a seeded user. Disabled when Supabase Auth is in use."""
    if get_settings().use_supabase:
        raise HTTPException(404, "Demo login is only available in offline demo mode. Use Supabase sign-in.")
    rows = [p for p in get_store().select("profiles") if p["role"] == body.role]
    if not rows:
        raise HTTPException(404, "Unknown demo role. Choose admin, creator, manager or reviewer.")
    p = rows[0]
    return DemoLoginOut(token=f"demo.{p['id']}", user_id=p["id"], email=p["email"], org_id=p["org_id"],
                        role=p["role"], full_name=p.get("full_name"))

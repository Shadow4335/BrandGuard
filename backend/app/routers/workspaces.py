"""Real workspace membership. Existing profiles keep their original tenancy and role."""
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from app.auth import UserContext, get_current_user, require_roles
from app.models.enums import UserRole
from app.store import get_store
from app.audit import log_event
from app.config import get_settings
from app.routers.core import throttle

router = APIRouter(prefix="/api/workspaces", tags=["Workspaces"])
_creates: dict = {}

class WorkspaceIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)


def memberships(user_id: str):
    try:
        return get_store().select("workspace_memberships", {"user_id": user_id})
    except Exception:
        return None  # older installations work without the optional additive migration


@router.get("")
def list_workspaces(user: UserContext = Depends(get_current_user)):
    store = get_store()
    profile = store.get("profiles", str(user.user_id))
    if not profile:
        raise HTTPException(403, "Your account is unavailable. Sign in again.")
    rows = memberships(str(user.user_id))
    ids = {profile["org_id"]} | {r["org_id"] for r in rows or []}
    orgs = store.select_where_in("organisations", "id", list(ids))
    return {"current_id": str(user.org_id), "workspaces": [{"id": o["id"], "name": o["name"]} for o in orgs],
            "can_create": rows is not None and user.role == UserRole.ADMIN,
            "membership_mode": "memberships" if rows is not None else "single_workspace"}


@router.post("")
def create_workspace(body: WorkspaceIn, request: Request, user: UserContext = Depends(require_roles(UserRole.ADMIN))):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Enter a workspace name.")
    throttle(_creates, request, 5, "Too many new workspaces. Please try again later.", key=str(user.user_id))
    store = get_store()
    if memberships(str(user.user_id)) is None:
        raise HTTPException(503, "Workspace creation needs the optional workspace-membership migration. Ask your server admin.")
    if get_settings().use_supabase:
        try:
            org_id = store.client.rpc("create_brandguard_workspace", {"p_user_id": str(user.user_id), "p_name": name, "p_description": body.description.strip()}).execute().data
        except Exception:
            raise HTTPException(503, "Workspace creation is unavailable. Ask your server admin to check the workspace-membership migration.")
    else:
        org_id = str(uuid4())
        store.insert("organisations", {"id": org_id, "name": name})
        store.insert("workspace_memberships", {"user_id": str(user.user_id), "org_id": org_id, "role": "admin"})
    log_event(org_id, user.user_id, "workspace_created", "organisation", org_id, {"description": body.description.strip()})
    return {"id": org_id, "name": name}

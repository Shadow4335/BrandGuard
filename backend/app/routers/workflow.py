"""Workflow transitions, review queue and audit trail."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.audit import log_event
from app.auth import UserContext, get_current_user
from app.engine.pipeline import latest_findings
from app.models import ContentItem
from app.models.api import AuditOut, ContentDetail, QueueItem, TransitionIn
from app.models.enums import UserRole
from app.routers.content import build_detail, get_content_or_404, latest_version, names
from app.store import get_store
from app.workflow.state_machine import TransitionError, apply_transition

router = APIRouter(prefix="/api", tags=["Workflow"])


@router.post("/content/{content_id}/transition", response_model=ContentDetail)
def transition(content_id: str, body: TransitionIn, user: UserContext = Depends(get_current_user)):
    store = get_store()
    content = get_content_or_404(content_id, user)
    ver = latest_version(content)
    findings = latest_findings(ver["id"])
    try:
        res = apply_transition(content["status"], body.action.value, user.role, findings, body.reason, body.override,
                               is_owner=content.get("creator_id") == str(user.user_id))
    except TransitionError as e:
        raise HTTPException(e.status_code, e.message)
    store.insert("approvals", {"org_id": str(user.org_id), "content_item_id": content_id,
                               "version_number": content["current_version"], "actor_id": str(user.user_id),
                               "role": user.role.value, "action": body.action.value,
                               "reason": (body.reason or "").strip() or None, "override": res.override})
    updated = store.update("content_items", content_id, {"status": res.new_status})
    log_event(user.org_id, user.user_id, f"workflow_{body.action.value}", "content_item", content_id,
              {"from": content["status"], "to": res.new_status, "role": user.role.value,
               "reason": (body.reason or "").strip(), "override": res.override, "version": content["current_version"]})
    return build_detail(updated, user)


@router.get("/reviews/queue", response_model=List[QueueItem])
def queue(user: UserContext = Depends(get_current_user)):
    store, org = get_store(), str(user.org_id)
    wanted = {UserRole.MANAGER: ["pending_manager"], UserRole.REVIEWER: ["escalated"],
              UserRole.ADMIN: ["pending_manager", "escalated"]}.get(user.role)
    rows = store.select("content_items", {"org_id": org}, order="created_at", desc=True)
    if wanted is None:  # creators see their own items that are past draft
        rows = [r for r in rows if r.get("creator_id") == str(user.user_id)]
    else:
        rows = [r for r in rows if r["status"] in wanted]
    people = names(org)
    out = []
    for r in rows:
        fs = latest_findings(latest_version(r)["id"])
        out.append(QueueItem(content=ContentItem(**r), creator_name=(people.get(r.get("creator_id")) or {}).get("full_name"),
                             open_high=sum(1 for f in fs if f["severity"] == "high" and f["status"] in ("open", "rejected")),
                             total_findings=len(fs)))
    return out


@router.get("/audit", response_model=List[AuditOut])
def audit(content_id: str, user: UserContext = Depends(get_current_user)):
    store, org = get_store(), str(user.org_id)
    get_content_or_404(content_id, user)
    version_ids = [v["id"] for v in store.select("content_versions", {"content_item_id": content_id})]
    finding_ids = {f["id"] for vid in version_ids for f in store.select("findings", {"content_version_id": vid})}
    people = names(org)
    rows = [r for r in store.select("audit_log", {"org_id": org}, order="created_at")
            if r.get("target_id") == content_id or r.get("target_id") in finding_ids]
    return [AuditOut(id=r["id"], event_type=r["event_type"], actor_id=r.get("actor_id"),
                     actor_name=(people.get(r.get("actor_id")) or {}).get("full_name"),
                     actor_role=(people.get(r.get("actor_id")) or {}).get("role"),
                     target_type=r["target_type"], target_id=r.get("target_id"), details=r.get("details") or {},
                     created_at=r.get("created_at")) for r in rows]

"""Run a review, record decisions on findings, and save new versions."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.audit import log_event
from app.auth import UserContext, require_roles
from app.engine.pipeline import latest_findings, review_steps
from app.models import Finding, ReviewRun
from app.models.api import ContentDetail, FindingDecisionIn, ReviewResult, VersionCreateIn
from app.models.enums import UserRole
from app.routers.content import build_detail, get_content_or_404
from app.store import get_store

router = APIRouter(prefix="/api", tags=["Review"])
EDITABLE = ("draft", "checked", "changes_requested", "rejected", "approved")


def _own_content(content_id: str, user: UserContext) -> dict:
    c = get_content_or_404(content_id, user)
    if c.get("creator_id") != str(user.user_id):
        raise HTTPException(403, "Only the creator of this content can do that.")
    return c


def _require_editable(content: dict) -> None:
    if content["status"] not in EDITABLE:
        raise HTTPException(409, "This item is waiting for review, so it can't be changed right now.")


def _result(done: dict) -> ReviewResult:
    return ReviewResult(run=ReviewRun(**done["run"]), findings=[Finding(**f) for f in done["findings"]],
                        used_fallback=done["used_fallback"], notice=done["notice"])


@router.post("/content/{content_id}/review", response_model=ReviewResult)
def run_review(content_id: str, user: UserContext = Depends(require_roles(UserRole.CREATOR))):
    content = _own_content(content_id, user)
    _require_editable(content)
    done = None
    for ev in review_steps(content, user.user_id, user.org_id):
        done = ev
    return _result(done)


@router.post("/content/{content_id}/review/stream")
def run_review_stream(content_id: str, user: UserContext = Depends(require_roles(UserRole.CREATOR))):
    content = _own_content(content_id, user)
    _require_editable(content)

    def gen():
        try:
            for ev in review_steps(content, user.user_id, user.org_id):
                if ev["stage"] == "done":
                    ev = {"stage": "done", "message": ev["message"], "result": json.loads(_result(ev).model_dump_json())}
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception:
            yield 'data: {"stage": "error", "message": "The review could not finish. Please try again."}\n\n'

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.patch("/findings/{finding_id}", response_model=Finding)
def decide(finding_id: str, body: FindingDecisionIn, user: UserContext = Depends(require_roles(UserRole.CREATOR))):
    store = get_store()
    row = store.get("findings", finding_id, str(user.org_id))
    if not row:
        raise HTTPException(404, "We couldn't find that finding.")
    ver = store.get("content_versions", row["content_version_id"])
    content = _own_content(ver["content_item_id"], user)
    _require_editable(content)
    if ver["version_number"] != content["current_version"]:
        raise HTTPException(409, "This finding belongs to an older version.")
    d = body.decision.value
    if d == "open":
        raise HTTPException(400, "Choose accept, edit or reject.")
    if d == "edited" and not (body.decision_text or "").strip():
        raise HTTPException(400, "Type the text you want to use instead.")
    if d == "rejected" and not (body.reason or "").strip():
        raise HTTPException(400, "Add a short reason for rejecting this suggestion.")
    upd = store.update("findings", finding_id, {
        "status": d, "decision_text": body.decision_text if d == "edited" else None,
        "decision_reason": body.reason, "decided_by": str(user.user_id),
        "decided_at": _now()})
    log_event(user.org_id, user.user_id, "finding_decided", "finding", finding_id,
              {"decision": d, "rule_id": row.get("rule_id"), "reason": body.reason})
    return Finding(**upd)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def apply_decisions(text: str, findings: list) -> str:
    """Build the new text from accepted/edited findings only. Overlaps are skipped; nothing else changes."""
    edits = []
    for f in findings:
        if not f.get("span"):
            continue
        new = f["decision_text"] if f["status"] == "edited" else f.get("replacement") if f["status"] == "accepted" else None
        if new is None:
            continue
        edits.append((f["span"]["start"], f["span"]["end"], new))
    edits.sort(key=lambda e: (e[0], e[1]))
    out, pos = [], 0
    for s, e, new in edits:
        if s < pos:
            continue
        out.append(text[pos:s])
        out.append(new)
        pos = e
    out.append(text[pos:])
    return "".join(out)


@router.post("/content/{content_id}/versions", response_model=ContentDetail)
def save_version(content_id: str, body: VersionCreateIn, user: UserContext = Depends(require_roles(UserRole.CREATOR))):
    store = get_store()
    content = _own_content(content_id, user)
    _require_editable(content)
    cur = store.select("content_versions", {"content_item_id": content_id, "version_number": content["current_version"]})[0]
    fs = latest_findings(cur["id"])
    new_text = body.body_text if body.body_text is not None else apply_decisions(cur.get("raw_text") or "", fs)
    n = content["current_version"] + 1
    store.insert("content_versions", {
        "content_item_id": content_id, "org_id": str(user.org_id), "version_number": n, "file_type": cur["file_type"],
        "raw_text": new_text, "file_path": cur.get("file_path"),
        "alt_text": body.alt_text if body.alt_text is not None else cur.get("alt_text"),
        "note": body.note or "Applied accepted and edited suggestions", "created_by": str(user.user_id)})
    content = store.update("content_items", content_id, {"current_version": n, "status": "checked"})
    log_event(user.org_id, user.user_id, "version_saved", "content_item", content_id,
              {"version": n, "accepted": sum(1 for f in fs if f["status"] == "accepted"),
               "edited": sum(1 for f in fs if f["status"] == "edited")})
    for _ in review_steps(content, user.user_id, user.org_id):  # re-check the new version
        pass
    return build_detail(store.get("content_items", content_id), user)

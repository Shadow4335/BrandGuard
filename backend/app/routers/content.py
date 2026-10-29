"""Content submission, detail, comments, images and sample loader."""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from app.audit import log_event
from app.auth import UserContext, get_current_user, require_roles
from app.engine.pipeline import latest_findings
from app.models import Approval, Comment, ContentItem, ContentVersion, Finding, ReviewRun
from app.models.api import CommentCreateIn, ContentDetail, QueueItem, SampleOut
from app.models.enums import UserRole
from app.parsing import UploadError, parse_upload
from app.seed_data import SAMPLES, make_poster_png
from app.store import get_store

router = APIRouter(prefix="/api", tags=["Content"])
CHANNELS = {"instagram_post", "website_page", "influencer_post", "press_release", "email"}


def storage_name(filename: Optional[str]) -> str:
    """Unique, storage-safe object name that keeps the extension (Supabase rejects some characters)."""
    import re
    import uuid
    name = (filename or "upload").rsplit("/", 1)[-1]
    stem, dot, ext = name.rpartition(".")
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem if dot else name).strip("-")[:60] or "upload"
    ext = re.sub(r"[^A-Za-z0-9]", "", ext)[:8].lower() if dot else ""
    return f"{uuid.uuid4().hex[:8]}-{stem}" + (f".{ext}" if ext else "")


def mime_for(file_type: str, fallback: Optional[str]) -> str:
    return {"docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}.get(
        file_type, file_type if "/" in file_type else (fallback or "application/octet-stream"))


def get_content_or_404(content_id: str, user: UserContext) -> dict:
    row = get_store().get("content_items", content_id, str(user.org_id))
    if not row:
        raise HTTPException(404, "We couldn't find that content. It may have been removed.")
    return row


def names(org_id: str) -> dict:
    return {p["id"]: p for p in get_store().select("profiles", {"org_id": org_id})}


def latest_version(content: dict) -> dict:
    vs = get_store().select("content_versions", {"content_item_id": content["id"], "version_number": content["current_version"]})
    return vs[0]


def build_detail(content: dict, user: UserContext) -> ContentDetail:
    from app.workflow.state_machine import allowed_actions
    store = get_store()
    org = str(user.org_id)
    people = names(org)
    versions = store.select("content_versions", {"content_item_id": content["id"]}, order="version_number")
    cur = next(v for v in versions if v["version_number"] == content["current_version"])
    findings = latest_findings(cur["id"])
    runs = store.select("review_runs", {"content_version_id": cur["id"]}, order="created_at", desc=True, limit=1)
    comments = []
    for v in versions:
        for c in store.select("comments", {"content_version_id": v["id"]}, order="created_at"):
            comments.append({**c, "author_name": (people.get(c["author_id"]) or {}).get("full_name")})
    approvals = store.select("approvals", {"content_item_id": content["id"]}, order="created_at")
    return ContentDetail(
        content=ContentItem(**content), versions=[ContentVersion(**v) for v in versions],
        findings=[Finding(**f) for f in findings], latest_run=ReviewRun(**runs[0]) if runs else None,
        comments=comments,
        approvals=[Approval(**a) for a in approvals],
        creator_name=(people.get(content.get("creator_id")) or {}).get("full_name"),
        allowed_actions=allowed_actions(content, user.role, str(user.user_id), findings),
        has_image=bool(cur.get("file_path")) and (cur.get("file_type") or "").startswith("image/"),
    )


@router.get("/samples", response_model=List[SampleOut])
def samples(user: UserContext = Depends(get_current_user)):
    return [SampleOut(**{k: s[k] for k in ("key", "title", "channel", "ai_generated", "text", "image", "alt_text")}) for s in SAMPLES]


@router.get("/samples/{key}/image")
def sample_image(key: str, user: UserContext = Depends(get_current_user)):
    if key != "poster":
        raise HTTPException(404, "That sample has no image.")
    return Response(make_poster_png(), media_type="image/png")


@router.post("/content")
def create_content(  # sync on purpose: OCR/parsing runs in the worker pool, not on the event loop
    title: str = Form(...), channel: str = Form("instagram_post"), ai_generated: bool = Form(False),
    text: Optional[str] = Form(None), alt_text: Optional[str] = Form(None), file: Optional[UploadFile] = File(None),
    user: UserContext = Depends(require_roles(UserRole.CREATOR)),
):
    if channel not in CHANNELS:
        raise HTTPException(400, f"Channel must be one of: {', '.join(sorted(CHANNELS))}.")
    store, org = get_store(), str(user.org_id)
    body, file_type, path, note = text or "", "text/plain", None, None
    if file is not None:
        data = file.file.read()
        try:
            doc = parse_upload(file.filename or "", file.content_type or "", data)
        except UploadError as e:
            raise HTTPException(e.status_code, e.message)
        body, file_type, note = doc.text or body, doc.file_type, doc.note
        path = f"{org}/{user.user_id}/{storage_name(file.filename)}"
        try:
            store.put_file("submissions", path, data, mime_for(file_type, file.content_type))
        except Exception:
            raise HTTPException(502, "We couldn't save your file right now. Please try again in a moment.")
    elif not body.strip():
        raise HTTPException(400, "Paste some text or upload a file to review.")
    item = store.insert("content_items", {"org_id": org, "title": title.strip() or "Untitled", "status": "draft",
                                          "creator_id": str(user.user_id), "channel": channel,
                                          "ai_generated": ai_generated, "current_version": 1})
    store.insert("content_versions", {"content_item_id": item["id"], "org_id": org, "version_number": 1,
                                      "file_type": file_type, "raw_text": body, "file_path": path,
                                      "alt_text": alt_text or "", "note": note or "Initial version",
                                      "created_by": str(user.user_id)})
    log_event(org, user.user_id, "content_created", "content_item", item["id"], {"title": item["title"], "channel": channel})
    return {"id": item["id"], "notice": note}


@router.get("/content", response_model=List[QueueItem])
def list_content(user: UserContext = Depends(get_current_user)):
    store, org = get_store(), str(user.org_id)
    where = {"org_id": org}
    if user.role == UserRole.CREATOR:
        where["creator_id"] = str(user.user_id)
    rows = store.select("content_items", where, order="created_at", desc=True)
    people = names(org)
    out = []
    for r in rows:
        v = store.select("content_versions", {"content_item_id": r["id"], "version_number": r["current_version"]})
        fs = latest_findings(v[0]["id"]) if v else []
        out.append(QueueItem(content=ContentItem(**r), creator_name=(people.get(r.get("creator_id")) or {}).get("full_name"),
                             open_high=sum(1 for f in fs if f["severity"] == "high" and f["status"] in ("open", "rejected")),
                             total_findings=len(fs)))
    return out


@router.get("/content/{content_id}", response_model=ContentDetail)
def get_content(content_id: str, user: UserContext = Depends(get_current_user)):
    return build_detail(get_content_or_404(content_id, user), user)


@router.get("/content/{content_id}/image")
def content_image(content_id: str, version: Optional[int] = None, user: UserContext = Depends(get_current_user)):
    content = get_content_or_404(content_id, user)
    v = get_store().select("content_versions", {"content_item_id": content_id, "version_number": version or content["current_version"]})
    if not v or not v[0].get("file_path"):
        raise HTTPException(404, "This content has no image.")
    data = get_store().get_file("submissions", v[0]["file_path"])
    if data is None:
        raise HTTPException(404, "The image file is no longer available.")
    ftype = v[0].get("file_type") or ""
    return Response(data, media_type=ftype if ftype.startswith("image/") else "application/octet-stream")


@router.post("/content/{content_id}/comments")
def add_comment(content_id: str, body: CommentCreateIn, user: UserContext = Depends(get_current_user)):
    content = get_content_or_404(content_id, user)
    if not body.body.strip():
        raise HTTPException(400, "Write a comment first.")
    ver = latest_version(content)
    row = get_store().insert("comments", {"org_id": str(user.org_id), "finding_id": body.finding_id,
                                          "content_version_id": ver["id"], "author_id": str(user.user_id),
                                          "text": body.body.strip()})
    log_event(user.org_id, user.user_id, "comment_added", "content_item", content_id, {"role": user.role.value})
    return row

"""Brand sources (guidelines, facts, terminology, regulatory, assets) and the read-only rule library."""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.audit import log_event
from app.auth import UserContext, get_current_user, require_roles
from app.engine.embeddings import embed_texts
from app.engine.rules_loader import load_rules
from app.models.api import RuleOut, SourceOut
from app.models.enums import UserRole
from app.parsing import parse_upload
from app.seed_data import chunk_text
from app.store import get_store

router = APIRouter(prefix="/api", tags=["Brand"])
KINDS = {"guideline", "terminology", "claim_library", "regulatory", "asset", "other"}


@router.get("/sources", response_model=List[SourceOut])
def list_sources(user: UserContext = Depends(get_current_user)):
    store = get_store()
    chunks = store.select("source_chunks", {"org_id": str(user.org_id)})
    counts: dict = {}
    for c in chunks:
        counts[c["source_id"]] = counts.get(c["source_id"], 0) + 1
    rows = store.select("sources", {"org_id": str(user.org_id)}, order="code")
    return [SourceOut(**r, chunk_count=counts.get(r["id"], 0)) for r in rows]


@router.post("/sources", response_model=SourceOut)
async def create_source(
    kind: str = Form(...), title: str = Form(...), code: Optional[str] = Form(None),
    text: Optional[str] = Form(None), file: Optional[UploadFile] = File(None),
    user: UserContext = Depends(require_roles(UserRole.ADMIN)),
):
    if kind not in KINDS:
        raise HTTPException(400, f"Kind must be one of: {', '.join(sorted(KINDS))}.")
    body, path = text or "", None
    store, org = get_store(), str(user.org_id)
    if file is not None:
        data = await file.read()
        body = parse_upload(file.filename or "", file.content_type or "", data).text or body
        path = f"{org}/{file.filename}"
        store.put_file("sources", path, data, file.content_type or "application/octet-stream")
    if not body.strip():
        raise HTTPException(400, "Add some text or upload a file with readable text.")
    row = store.insert("sources", {"org_id": org, "title": title, "source_type": kind, "code": code,
                                   "body": body, "file_path": path, "metadata": {}})
    pieces = chunk_text(body)
    vecs = embed_texts(pieces)
    for i, piece in enumerate(pieces):
        store.insert("source_chunks", {"source_id": row["id"], "org_id": org, "content": piece, "chunk_index": i,
                                       "embedding": vecs[i] if vecs else None, "metadata": {"code": code}})
    log_event(org, user.user_id, "source_created", "source", row["id"], {"title": title, "kind": kind})
    return SourceOut(**row, chunk_count=len(pieces))


@router.get("/rules", response_model=List[RuleOut])
def list_rules(user: UserContext = Depends(get_current_user)):
    return [RuleOut(id=r["id"], category=r["category"], title=r["title"], severity=r["severity"],
                    reference=r.get("reference"), source_code=r.get("source_code"), why=r.get("why", ""),
                    layer=r["layer"]) for r in load_rules()]

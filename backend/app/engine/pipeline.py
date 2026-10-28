"""Run one review: Layer A, retrieval + Layer B, merge, persist, audit. A generator so the API can stream progress."""
import time
from typing import Iterator, List
from uuid import UUID

from app.audit import log_event
from app.engine.layer_a import ReviewContext, run_layer_a
from app.engine.layer_b import run_layer_b
from app.engine.merger import merge
from app.engine.retrieval import retrieve
from app.models import Finding, ReviewRun
from app.store import get_store

FALLBACK_NOTICE = ("AI layer unavailable: showing rule-based results plus offline claim and tone checks. "
                   "Nothing was sent to an AI provider.")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")


def latest_findings(version_id: str) -> List[dict]:
    """Findings of the most recent review run for a version (older runs are kept for history)."""
    store = get_store()
    runs = store.select("review_runs", {"content_version_id": version_id}, order="created_at", desc=True, limit=1)
    if not runs:
        return []
    return store.select("findings", {"run_id": runs[0]["id"]}, order="created_at")


def review_steps(content: dict, user_id, org_id) -> Iterator[dict]:
    store = get_store()
    org = str(org_id)
    ver = store.select("content_versions", {"content_item_id": content["id"], "version_number": content["current_version"]})[0]
    path = ver.get("file_path") or ""
    is_image = path.lower().endswith(IMAGE_EXT)
    image = store.get_file("submissions", path) if is_image else None
    ctx = ReviewContext(version_id=UUID(ver["id"]), org_id=UUID(org), text=ver.get("raw_text") or "",
                        channel=content.get("channel", "instagram_post"), ai_generated=bool(content.get("ai_generated")),
                        alt_text=ver.get("alt_text"), image_bytes=image, is_image=is_image)
    yield {"stage": "start", "message": "Starting review..."}

    t0 = time.perf_counter()
    a = run_layer_a(ctx)
    a_ms = int((time.perf_counter() - t0) * 1000)
    yield {"stage": "layer_a", "message": f"Rule checks done ({len(a)} issues). AI checks running..."}

    t1 = time.perf_counter()
    sources = retrieve(org, ctx.text) if ctx.text.strip() else []
    b, used_fallback, model = run_layer_b(ctx, sources)
    b_ms = int((time.perf_counter() - t1) * 1000)
    findings = merge(a, b)

    by_code = {s["code"]: s["id"] for s in store.select("sources", {"org_id": org}) if s.get("code")}
    run = store.insert("review_runs", {"org_id": org, "content_item_id": content["id"], "content_version_id": ver["id"],
                                       "version_number": ver["version_number"], "layer_a_ms": a_ms, "layer_b_ms": b_ms,
                                       "used_fallback": used_fallback, "model": model})
    rows = []
    for f in findings:
        d = f.model_dump(mode="json", exclude_none=False)
        d.update({"run_id": run["id"], "org_id": org, "source_ids": [by_code[c] for c in f.source_codes if c in by_code],
                  "content_version_id": ver["id"]})
        d.pop("created_at", None)
        d.pop("decided_at", None)
        rows.append(d)
    saved = get_store().insert_many("findings", rows)
    if content["status"] in ("draft", "checked", "changes_requested", "rejected"):
        store.update("content_items", content["id"], {"status": "checked"})
    log_event(org, user_id, "review_run", "content_item", content["id"],
              {"run_id": run["id"], "version": ver["version_number"], "findings": len(saved), "used_fallback": used_fallback})
    for r in saved:
        log_event(org, user_id, "finding_created", "finding", r["id"],
                  {"rule_id": r.get("rule_id"), "severity": r["severity"], "layer": r["layer"]})
    yield {"stage": "done", "message": "Review complete.", "run": run, "findings": saved,
           "used_fallback": used_fallback, "notice": FALLBACK_NOTICE if used_fallback else None}

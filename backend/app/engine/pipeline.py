"""Run one review: Layer A, retrieval + Layer B, merge, persist, audit. A generator so the API can stream progress."""
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator, List
from uuid import UUID

from app.audit import audit_row, log_events
from app.engine.layer_a import ReviewContext, run_layer_a
from app.engine.layer_b import run_layer_b
from app.engine.merger import merge
from app.engine.retrieval import retrieve
from app.models import Finding, ReviewRun
from app.store import get_store, io_pool

FALLBACK_NOTICE = ("AI layer unavailable: showing rule-based results plus offline claim and tone checks. "
                   "Nothing was sent to an AI provider.")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff")
# Retrieval runs here while Layer A runs on the request thread. Separate from io_pool because retrieval itself fans
# its lookups out to io_pool and waits for them.
_retrieval_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="retrieval")


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
    ftype = ver.get("file_type") or ""
    is_image = ftype.startswith("image/") or path.lower().endswith(IMAGE_EXT)
    data = store.get_file("submissions", path) if path else None
    image = data if is_image else None
    missing_alt = 0
    if data and ftype in ("docx", "text/html"):
        from app.parsing import parse_upload
        try:
            missing_alt = parse_upload(path, ftype, data).images_missing_alt
        except Exception:
            missing_alt = 0
    ctx = ReviewContext(version_id=UUID(ver["id"]), org_id=UUID(org), text=ver.get("raw_text") or "",
                        channel=content.get("channel", "instagram_post"), ai_generated=bool(content.get("ai_generated")),
                        alt_text=ver.get("alt_text"), image_bytes=image, is_image=is_image,
                        images_missing_alt=missing_alt)
    yield {"stage": "start", "message": "Starting review..."}

    def load_sources():
        # The org's sources are read once: retrieval picks from them and findings link to them by code
        rows = store.select("sources", {"org_id": org})
        return rows, (retrieve(org, ctx.text, all_sources=rows) if ctx.text.strip() else [])

    t1 = time.perf_counter()
    retrieval = _retrieval_pool.submit(load_sources)  # runs while Layer A works (OCR on images can take seconds)
    t0 = time.perf_counter()
    a = run_layer_a(ctx)
    a_ms = int((time.perf_counter() - t0) * 1000)
    yield {"stage": "layer_a", "message": f"Rule checks done ({len(a)} issues). AI checks running..."}

    all_sources, sources = retrieval.result()
    b, used_fallback, model = run_layer_b(ctx, sources)
    b_ms = int((time.perf_counter() - t1) * 1000)
    findings = merge(a, b)

    by_code = {s["code"]: s["id"] for s in all_sources if s.get("code")}
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
    status_job = None
    if content["status"] in ("draft", "checked", "changes_requested", "rejected"):
        status_job = io_pool.submit(store.update, "content_items", content["id"], {"status": "checked"})
    events = [audit_row(org, user_id, "review_run", "content_item", content["id"],
                        {"run_id": run["id"], "version": ver["version_number"], "findings": len(saved),
                         "used_fallback": used_fallback})]
    events += [audit_row(org, user_id, "finding_created", "finding", r["id"],
                         {"rule_id": r.get("rule_id"), "severity": r["severity"], "layer": r["layer"]}) for r in saved]
    log_events(events)  # one write, alongside the status update
    if status_job:
        status_job.result()
    yield {"stage": "done", "message": "Review complete.", "run": run, "findings": saved,
           "used_fallback": used_fallback, "notice": FALLBACK_NOTICE if used_fallback else None}

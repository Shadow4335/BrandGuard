#!/usr/bin/env python3
"""Seed Supabase with the GlowLeaf Naturals demo org: users, brand sources, chunks (+embeddings if an
LLM key is set) and 30 days of historical content for Insights. Idempotent: safe to run again.

Run from the repo root:  backend/.venv/bin/python seed/seed_demo.py
Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in backend/.env (service key stays server-side).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.engine.embeddings import embed_texts  # noqa: E402
from app.seed_data import (ORG_ID, ORG_NAME, USERS, chunk_text, make_logo_png, seed_history, source_rows, _id)  # noqa: E402
from app.store import SupabaseStore  # noqa: E402


def main() -> None:
    s = get_settings()
    if not (s.supabase_url and s.supabase_service_key):
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in backend/.env first.")
    store = SupabaseStore()
    client = store.client

    if not store.get("organisations", ORG_ID):
        store.insert("organisations", {"id": ORG_ID, "name": ORG_NAME})
        print("created organisation", ORG_NAME)

    ids = {}
    existing = {u.email: u for u in client.auth.admin.list_users()}
    for u in USERS:
        au = existing.get(u["email"])
        if au is None:
            au = client.auth.admin.create_user({"email": u["email"], "password": s.demo_password, "email_confirm": True,
                                                "user_metadata": {"full_name": u["full_name"], "role": u["role"]}}).user
            print("created user", u["email"])
        ids[u["key"]] = au.id
        client.table("profiles").upsert({"id": au.id, "org_id": ORG_ID, "role": u["role"], "email": u["email"],
                                         "full_name": u["full_name"]}).execute()

    have = {r["code"] for r in store.select("sources", {"org_id": ORG_ID}) if r.get("code")}
    for row in source_rows():
        if row["code"] in have:
            continue
        store.insert("sources", row)
        pieces = chunk_text(row["body"])
        vecs = embed_texts(pieces)
        store.insert_many("source_chunks", [{"source_id": row["id"], "org_id": ORG_ID, "content": p, "chunk_index": i,
                                              "embedding": vecs[i] if vecs else None, "metadata": {"code": row["code"]}}
                                             for i, p in enumerate(pieces)])
        if row["code"] == "ASSET-LOGO":
            store.put_file("sources", f"{ORG_ID}/glowleaf-logo.png", make_logo_png(), "image/png")
    print(f"sources ready ({len(source_rows())})")

    if not store.get("content_items", _id("hist-c0")):
        seed_history(store, ORG_ID, ids["history"], ids["manager"], ids["reviewer"])
        print("seeded 25 historical content items")
    print("Done. Demo password:", s.demo_password)


if __name__ == "__main__":
    main()

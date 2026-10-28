"""Tiny data-access layer.

Routers talk to a `Store` with select/insert/update. Two implementations:
  * SupabaseStore: production (service-role client, org scoping done in API code).
  * MemoryStore:   offline demo and tests (seeded at startup, same table/column names).
"""
from __future__ import annotations

import copy
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import get_settings

Row = Dict[str, Any]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def select(self, table: str, where: Optional[Row] = None, order: Optional[str] = None,
               desc: bool = False, limit: Optional[int] = None) -> List[Row]: ...
    def get(self, table: str, row_id: str, org_id: Optional[str] = None) -> Optional[Row]:
        rows = self.select(table, {"id": row_id, **({"org_id": org_id} if org_id else {})}, limit=1)
        return rows[0] if rows else None
    def insert(self, table: str, row: Row) -> Row: ...
    def update(self, table: str, row_id: str, patch: Row) -> Row: ...
    def put_file(self, bucket: str, path: str, data: bytes, content_type: str) -> None: ...
    def get_file(self, bucket: str, path: str) -> Optional[bytes]: ...
    def match_chunks(self, org_id: str, source_types: List[str], query_embedding: List[float], k: int) -> List[Row]:
        return []


class MemoryStore(Store):
    def __init__(self) -> None:
        self.tables: Dict[str, List[Row]] = {}
        self.files: Dict[str, bytes] = {}
        self.lock = threading.RLock()

    def select(self, table, where=None, order=None, desc=False, limit=None):
        with self.lock:
            rows = [r for r in self.tables.get(table, []) if all(r.get(k) == v for k, v in (where or {}).items())]
            if order:
                rows = sorted(rows, key=lambda r: (r.get(order) is None, r.get(order)), reverse=desc)
            rows = rows[:limit] if limit else rows
            return copy.deepcopy(rows)

    def insert(self, table, row):
        with self.lock:
            row = {"id": str(uuid.uuid4()), "created_at": _now(), **row}
            if table == "audit_log":
                row.setdefault("details", {})
            self.tables.setdefault(table, []).append(copy.deepcopy(row))
            return copy.deepcopy(row)

    def update(self, table, row_id, patch):
        with self.lock:
            if table == "audit_log":
                raise PermissionError("audit_log is append-only")
            for r in self.tables.get(table, []):
                if r["id"] == row_id:
                    r.update(copy.deepcopy(patch))
                    return copy.deepcopy(r)
            raise KeyError(f"{table}/{row_id} not found")

    def put_file(self, bucket, path, data, content_type):
        self.files[f"{bucket}/{path}"] = data

    def get_file(self, bucket, path):
        return self.files.get(f"{bucket}/{path}")


class SupabaseStore(Store):
    def __init__(self) -> None:
        from supabase import create_client
        s = get_settings()
        self.client = create_client(s.supabase_url, s.supabase_service_key)

    def select(self, table, where=None, order=None, desc=False, limit=None):
        q = self.client.table(table).select("*")
        for k, v in (where or {}).items():
            q = q.eq(k, v)
        if order:
            q = q.order(order, desc=desc)
        if limit:
            q = q.limit(limit)
        return q.execute().data or []

    def insert(self, table, row):
        return self.client.table(table).insert(row).execute().data[0]

    def update(self, table, row_id, patch):
        return self.client.table(table).update(patch).eq("id", row_id).execute().data[0]

    def put_file(self, bucket, path, data, content_type):
        self.client.storage.from_(bucket).upload(path, data, {"content-type": content_type, "upsert": "true"})

    def get_file(self, bucket, path):
        try:
            return self.client.storage.from_(bucket).download(path)
        except Exception:
            return None

    def match_chunks(self, org_id, source_types, query_embedding, k):
        res = self.client.rpc("match_chunks", {"query_embedding": query_embedding, "org_id": org_id,
                                               "source_types": source_types, "k": k}).execute()
        return res.data or []


_store: Optional[Store] = None


def get_store() -> Store:
    global _store
    if _store is None:
        if get_settings().use_supabase:
            _store = SupabaseStore()
        else:
            from app.seed_data import seed_memory_store
            _store = MemoryStore()
            seed_memory_store(_store)
    return _store


def reset_store(store: Optional[Store] = None) -> None:
    """For tests."""
    global _store
    _store = store

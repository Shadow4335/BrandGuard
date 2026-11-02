"""Tiny data-access layer.

Routers talk to a `Store` with select/insert/update. Two implementations:
  * SupabaseStore: production (service-role client, org scoping done in API code).
  * MemoryStore:   offline demo and tests (seeded at startup, same table/column names).
"""
from __future__ import annotations

import copy
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import get_settings

Row = Dict[str, Any]

# Long-lived threads for running independent database calls in parallel. Each thread keeps its own Supabase client
# (see SupabaseStore.client), so reusing threads reuses their connections instead of opening new ones per request.
# Tasks submitted here must not wait on other tasks in this pool.
io_pool = ThreadPoolExecutor(max_workers=16, thread_name_prefix="store-io")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_uuid(value: Any) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def strip_nul(value: Any) -> Any:
    """Postgres text and jsonb can't hold NUL characters, and pasted text or parsed files sometimes contain them."""
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, dict):
        return {k: strip_nul(v) for k, v in value.items()}
    if isinstance(value, list):
        return [strip_nul(v) for v in value]
    return value


class Store:
    def select(self, table: str, where: Optional[Row] = None, order: Optional[str] = None,
               desc: bool = False, limit: Optional[int] = None) -> List[Row]: ...
    def get(self, table: str, row_id: str, org_id: Optional[str] = None) -> Optional[Row]:
        if not is_uuid(row_id):  # a malformed ID is "not found", not a Postgres type error
            return None
        rows = self.select(table, {"id": row_id, **({"org_id": org_id} if org_id else {})}, limit=1)
        return rows[0] if rows else None
    def select_where_in(self, table: str, column: str, values: List[Any], order: Optional[str] = None,
                        desc: bool = False) -> List[Row]:
        """All rows whose `column` matches one of `values`, in one query rather than one per value."""
        ...
    def insert(self, table: str, row: Row) -> Row: ...
    def insert_many(self, table: str, rows: List[Row]) -> List[Row]:
        return [self.insert(table, r) for r in rows]
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

    def select_where_in(self, table, column, values, order=None, desc=False):
        keep = set(values)
        with self.lock:
            rows = [r for r in self.tables.get(table, []) if r.get(column) in keep]
        if order:
            rows.sort(key=lambda r: (r.get(order) is None, r.get(order)), reverse=desc)
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
    IN_BATCH = 100  # values per IN (...) filter, keeping the request URL short

    def __init__(self) -> None:
        self._per_thread = threading.local()

    @property
    def client(self):
        """A client per thread. FastAPI runs sync endpoints on a thread pool, and one shared HTTP/2 client fails under
        parallel requests (httpx ReadError, errno 35)."""
        client = getattr(self._per_thread, "client", None)
        if client is None:
            from supabase import create_client
            s = get_settings()
            client = self._per_thread.client = create_client(s.supabase_url, s.supabase_service_key)
        return client

    def select(self, table, where=None, order=None, desc=False, limit=None):
        q = self.client.table(table).select("*")
        for k, v in (where or {}).items():
            q = q.eq(k, v)
        if order:
            q = q.order(order, desc=desc)
        if limit:
            q = q.limit(limit)
        return q.execute().data or []

    def select_where_in(self, table, column, values, order=None, desc=False):
        values, rows = list(dict.fromkeys(values)), []
        for i in range(0, len(values), self.IN_BATCH):
            q = self.client.table(table).select("*").in_(column, values[i:i + self.IN_BATCH])
            if order:
                q = q.order(order, desc=desc)
            rows.extend(q.execute().data or [])
        if order and len(values) > self.IN_BATCH:  # several batches: restore one overall order
            rows.sort(key=lambda r: (r.get(order) is None, r.get(order)), reverse=desc)
        return rows

    def insert(self, table, row):
        return self.client.table(table).insert(strip_nul(row)).execute().data[0]

    def insert_many(self, table, rows):
        return self.client.table(table).insert(strip_nul(rows)).execute().data if rows else []

    def update(self, table, row_id, patch):
        return self.client.table(table).update(strip_nul(patch)).eq("id", row_id).execute().data[0]

    def put_file(self, bucket, path, data, content_type):
        self.client.storage.from_(bucket).upload(path, data, {"content-type": content_type, "upsert": "true"})

    def get_file(self, bucket, path):
        try:
            return self.client.storage.from_(bucket).download(path)
        except Exception:
            return None

    def match_chunks(self, org_id, source_types, query_embedding, k):
        res = self.client.rpc("match_chunks", {"query_embedding": query_embedding, "p_org_id": org_id,
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

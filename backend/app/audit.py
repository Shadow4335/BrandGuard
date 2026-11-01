from typing import Any, Dict, List, Optional

from app.store import get_store


def log_event(org_id, actor_id, event_type: str, target_type: str, target_id: Optional[str] = None,
              details: Optional[Dict[str, Any]] = None) -> None:
    """Append one row to the append-only audit log."""
    get_store().insert("audit_log", audit_row(org_id, actor_id, event_type, target_type, target_id, details))


def audit_row(org_id, actor_id, event_type: str, target_type: str, target_id: Optional[str] = None,
              details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "org_id": str(org_id), "actor_id": str(actor_id) if actor_id else None,
        "event_type": event_type, "target_type": target_type,
        "target_id": str(target_id) if target_id else None, "details": details or {},
    }


def log_events(rows: List[Dict[str, Any]]) -> None:
    """Append several audit rows in one write (one database round trip instead of one per row)."""
    if rows:
        get_store().insert_many("audit_log", rows)

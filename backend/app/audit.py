from typing import Any, Dict, Optional

from app.store import get_store


def log_event(org_id, actor_id, event_type: str, target_type: str, target_id: Optional[str] = None,
              details: Optional[Dict[str, Any]] = None) -> None:
    """Append one row to the append-only audit log."""
    get_store().insert("audit_log", {
        "org_id": str(org_id), "actor_id": str(actor_id) if actor_id else None,
        "event_type": event_type, "target_type": target_type,
        "target_id": str(target_id) if target_id else None, "details": details or {},
    })

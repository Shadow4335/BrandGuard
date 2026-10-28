"""Content workflow. Pure functions so every legal and illegal transition is unit-testable.

draft --review--> checked --submit(creator)--> pending_manager ("In review")
pending_manager --approve(manager)--> approved
pending_manager --request_changes(manager, reason)--> changes_requested --new version--> checked
pending_manager --escalate(manager)--> escalated
escalated --approve(reviewer; written override reason if high-severity findings are unresolved)--> approved
escalated --reject(reviewer, reason)--> rejected --new version--> checked
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.models.enums import UserRole


class TransitionError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# (current status, action) -> (role allowed, new status)
TRANSITIONS: Dict[Tuple[str, str], Tuple[UserRole, str]] = {
    ("checked", "submit"): (UserRole.CREATOR, "pending_manager"),
    ("pending_manager", "approve"): (UserRole.MANAGER, "approved"),
    ("pending_manager", "request_changes"): (UserRole.MANAGER, "changes_requested"),
    ("pending_manager", "escalate"): (UserRole.MANAGER, "escalated"),
    ("escalated", "approve"): (UserRole.REVIEWER, "approved"),
    ("escalated", "reject"): (UserRole.REVIEWER, "rejected"),
}
REASON_REQUIRED = {"request_changes", "reject"}


def unresolved_high(findings: List[dict]) -> int:
    """High-severity findings the creator has not fixed (open, or rejected as 'not applicable')."""
    return sum(1 for f in findings if f["severity"] == "high" and f["status"] in ("open", "rejected"))


@dataclass
class Result:
    new_status: str
    override: bool


def apply_transition(status: str, action: str, role: UserRole, findings: List[dict],
                     reason: Optional[str] = None, override: bool = False,
                     is_owner: bool = True) -> Result:
    key = (status, action)
    if key not in TRANSITIONS:
        raise TransitionError(409, f"You can't {action.replace('_', ' ')} while this item is '{status.replace('_', ' ')}'.")
    needed_role, new_status = TRANSITIONS[key]
    if role != needed_role:
        raise TransitionError(403, f"Only a {needed_role.value} can {action.replace('_', ' ')} at this stage.")
    if action == "submit" and not is_owner:
        raise TransitionError(403, "Only the creator can submit this content.")
    reason = (reason or "").strip()
    if action in REASON_REQUIRED and not reason:
        raise TransitionError(400, "Please write a short reason; it is recorded in the audit trail.")
    is_override = False
    if action == "approve" and role == UserRole.REVIEWER and unresolved_high(findings):
        if not (override and len(reason) >= 5):
            raise TransitionError(409, f"{unresolved_high(findings)} high-severity finding(s) are still unresolved. "
                                       "Approving anyway is an override and needs a written reason.")
        is_override = True
    return Result(new_status, is_override)


def allowed_actions(content: dict, role: UserRole, user_id: str, findings: List[dict]) -> List[str]:
    out = []
    for (status, action), (needed, _) in TRANSITIONS.items():
        if status == content["status"] and needed == role:
            if action == "submit" and content.get("creator_id") != user_id:
                continue
            out.append(action)
    return out

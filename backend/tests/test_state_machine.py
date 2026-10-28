import pytest

from app.models.enums import UserRole as R
from app.workflow.state_machine import TRANSITIONS, TransitionError, allowed_actions, apply_transition

HIGH_OPEN = [{"severity": "high", "status": "open"}]
CLEAN = [{"severity": "high", "status": "accepted"}]
STATUSES = ["draft", "checked", "pending_manager", "changes_requested", "escalated", "approved", "rejected"]
ACTIONS = ["submit", "approve", "request_changes", "escalate", "reject"]


def go(status, action, role, findings=CLEAN, reason="a reason", override=False):
    return apply_transition(status, action, role, findings, reason, override)


def test_every_legal_transition():
    for (status, action), (role, new) in TRANSITIONS.items():
        assert go(status, action, role).new_status == new


def test_every_illegal_status_action_pair_is_rejected_409():
    for status in STATUSES:
        for action in ACTIONS:
            if (status, action) in TRANSITIONS:
                continue
            for role in R:
                with pytest.raises(TransitionError) as e:
                    go(status, action, role)
                assert e.value.status_code == 409


def test_wrong_role_is_403():
    for (status, action), (role, _) in TRANSITIONS.items():
        for other in R:
            if other != role:
                with pytest.raises(TransitionError) as e:
                    go(status, action, other)
                assert e.value.status_code == 403


def test_submit_by_non_owner_is_403():
    with pytest.raises(TransitionError) as e:
        apply_transition("checked", "submit", R.CREATOR, CLEAN, is_owner=False)
    assert e.value.status_code == 403


def test_reason_required_for_request_changes_and_reject():
    for status, action, role in [("pending_manager", "request_changes", R.MANAGER), ("escalated", "reject", R.REVIEWER)]:
        with pytest.raises(TransitionError) as e:
            go(status, action, role, reason="")
        assert e.value.status_code == 400


def test_reviewer_approve_with_open_high_needs_override_reason():
    with pytest.raises(TransitionError) as e:
        go("escalated", "approve", R.REVIEWER, HIGH_OPEN, reason="", override=False)
    assert e.value.status_code == 409
    with pytest.raises(TransitionError):
        go("escalated", "approve", R.REVIEWER, HIGH_OPEN, reason="ok", override=True)  # too short
    res = go("escalated", "approve", R.REVIEWER, HIGH_OPEN, reason="Legal confirmed claim is supported", override=True)
    assert res.new_status == "approved" and res.override is True


def test_reviewer_approve_clean_is_not_an_override():
    assert go("escalated", "approve", R.REVIEWER, CLEAN, reason="").override is False


def test_rejected_finding_counts_as_unresolved():
    with pytest.raises(TransitionError):
        go("escalated", "approve", R.REVIEWER, [{"severity": "high", "status": "rejected"}], reason="")


def test_allowed_actions_per_role():
    c = {"status": "pending_manager", "creator_id": "u1"}
    assert set(allowed_actions(c, R.MANAGER, "m", [])) == {"approve", "request_changes", "escalate"}
    assert allowed_actions(c, R.CREATOR, "u1", []) == []
    assert allowed_actions({"status": "checked", "creator_id": "u1"}, R.CREATOR, "u2", []) == []
    assert allowed_actions({"status": "checked", "creator_id": "u1"}, R.CREATOR, "u1", []) == ["submit"]

"""Governance insights: recurring violations, trend, most-rejected rules, unclear guidelines.

Two rates, kept apart in the interface: RuleStat.override_rate is a rule's rejected findings / decided findings (shown
as "rejection rate"); override_approvals / approvals_total is how often content was approved over open high findings."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Literal

from fastapi import APIRouter, Depends, Query

from app.auth import UserContext, get_current_user
from app.engine.rules_loader import rule_title
from app.models.api import InsightsSummary, RuleStat, UnclearRule
from app.store import get_store

router = APIRouter(prefix="/api/insights", tags=["Insights"])
UNCLEAR_RATE, UNCLEAR_MIN_DECISIONS = 0.4, 3


def _current_findings(org: str) -> List[dict]:
    """Findings from the most recent review run of each version (older runs are history, not signal)."""
    store = get_store()
    latest: Dict[str, dict] = {}
    for r in store.select("review_runs", {"org_id": org}, order="created_at"):
        latest[r["content_version_id"]] = r["id"]
    keep = set(latest.values())
    return [f for f in store.select("findings", {"org_id": org}) if f.get("run_id") in keep]


def _rule_stats(findings: List[dict]) -> List[RuleStat]:
    by: Dict[str, List[dict]] = {}
    for f in findings:
        if f.get("rule_id"):
            by.setdefault(f["rule_id"], []).append(f)
    out = []
    for rid, fs in by.items():
        decided = [f for f in fs if f["status"] != "open"]
        rejected = [f for f in decided if f["status"] == "rejected"]
        out.append(RuleStat(rule_id=rid, title=rule_title(rid), category=fs[0]["category"], count=len(fs),
                            decided=len(decided), rejected=len(rejected),
                            override_rate=round(len(rejected) / len(decided), 2) if decided else 0.0,
                            low_confidence_share=round(sum(1 for f in fs if f["confidence"] == "low") / len(fs), 2)))
    return out


@router.get("/summary", response_model=InsightsSummary)
def summary(user: UserContext = Depends(get_current_user),
            scope: Literal["workspace", "mine"] = Query("workspace")):
    """Last 30 days. scope=workspace: everyone's activity in the workspace (the Insights page). scope=mine: only the
    caller's own work (the dashboard), so a new account starts at zero instead of seeing the shared history:
    content they created, the findings on it, and approvals they decided."""
    store, org = get_store(), str(user.org_id)
    me = str(user.user_id)
    findings = _current_findings(org)
    items = store.select("content_items", {"org_id": org})
    approvals = store.select("approvals", {"org_id": org})
    if scope == "mine":
        items = [i for i in items if i.get("creator_id") == me]
        version_ids = {v["id"] for v in store.select_where_in("content_versions", "content_item_id", [i["id"] for i in items])}
        findings = [f for f in findings if f.get("content_version_id") in version_ids]
        approvals = [a for a in approvals if a.get("actor_id") == me]
    since = datetime.now(timezone.utc) - timedelta(days=30)
    recent = [f for f in findings if datetime.fromisoformat(f["created_at"].replace("Z", "+00:00")) >= since]
    stats = _rule_stats(recent)

    def daily(rows: List[dict]) -> List[dict]:
        days = Counter(r["created_at"][:10] for r in rows)
        dates = [(since + timedelta(days=i + 1)).date().isoformat() for i in range(30)]
        return [{"date": d, "count": days.get(d, 0)} for d in dates]

    items = [i for i in items if datetime.fromisoformat(i["created_at"].replace("Z", "+00:00")) >= since]
    approvals = [a for a in approvals if datetime.fromisoformat(a["created_at"].replace("Z", "+00:00")) >= since]
    decisions = [a for a in approvals if a["action"] != "submit"]
    cats = Counter(f["category"] for f in recent)
    return InsightsSummary(
        total_findings=len(recent), total_content=len(items),
        top_rules=sorted((s for s in stats), key=lambda s: -s.count)[:8],
        by_category=[{"category": c, "count": n} for c, n in cats.most_common()],
        trend=daily(recent),
        decision_trend=daily(decisions),
        findings_decided=sum(1 for f in recent if f["status"] != "open"),
        decisions_total=len(decisions),
        most_overridden=sorted((s for s in stats if s.decided >= 1), key=lambda s: (-s.override_rate, -s.decided))[:8],
        status_counts=dict(Counter(i["status"] for i in items)),
        override_approvals=sum(1 for a in approvals if a.get("override")),
        approvals_total=sum(1 for a in approvals if a["action"] == "approve"))


@router.get("/unclear-rules", response_model=List[UnclearRule])
def unclear_rules(user: UserContext = Depends(get_current_user)):
    out = []
    for s in _rule_stats(_current_findings(str(user.org_id))):
        # Rejections only: low confidence isn't evidence here, since every unsupported-claim finding is low by design
        if s.decided < UNCLEAR_MIN_DECISIONS or s.override_rate < UNCLEAR_RATE:
            continue
        out.append(UnclearRule(rule_id=s.rule_id, title=s.title, override_rate=s.override_rate, decisions=s.decided,
                               reason=f"Creators rejected {round(s.override_rate * 100)}% of {s.decided} decisions",
                               suggestion="Consider clarifying the wording or adding examples."))
    return sorted(out, key=lambda r: -r.override_rate)

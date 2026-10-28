"""Phase 1 contract stubs: every endpoint from the API contract returns typed mock data.
Real routers replace these phase by phase; this file is deleted once none remain."""
from fastapi import APIRouter, Depends

from app.auth import UserContext, get_current_user
from app.models.api import InsightsSummary

router = APIRouter(prefix="/api", tags=["Stubs"])


@router.get("/insights/summary", response_model=InsightsSummary)
def insights_summary(user: UserContext = Depends(get_current_user)):
    return InsightsSummary(total_findings=0, total_content=0, top_rules=[], by_category=[], trend=[],
                           most_overridden=[], status_counts={})


@router.get("/insights/unclear-rules")
def unclear(user: UserContext = Depends(get_current_user)):
    return []

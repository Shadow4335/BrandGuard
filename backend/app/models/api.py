"""Request/response shapes for the HTTP API. Mirrored in frontend/lib/types.ts."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.domain import Approval, Comment, ContentItem, ContentVersion, ReviewRun, Source
from app.models.enums import FindingStatus, WorkflowAction
from app.models.finding import Finding


class HealthOut(BaseModel):
    status: str = "ok"
    service: str = "brandguard-api"
    ai_provider: str
    ai_live: bool
    fallback_available: bool = True
    store: str
    version: str = ""
    commit: str = ""


class DemoLoginIn(BaseModel):
    role: str


class DemoLoginOut(BaseModel):
    token: str
    user_id: str
    email: str
    org_id: str
    role: str
    full_name: Optional[str] = None


class SourceOut(Source):
    chunk_count: int = 0


class RuleOut(BaseModel):
    id: str
    category: str
    title: str
    severity: str
    reference: Optional[str] = None
    source_code: Optional[str] = None
    why: str = ""
    layer: str = "A"


class ContentCreateIn(BaseModel):
    title: str
    channel: str = "instagram_post"
    ai_generated: bool = False
    text: Optional[str] = None
    alt_text: Optional[str] = None


class FindingDecisionIn(BaseModel):
    decision: FindingStatus
    decision_text: Optional[str] = None
    reason: Optional[str] = None


class VersionCreateIn(BaseModel):
    note: Optional[str] = None
    alt_text: Optional[str] = None
    body_text: Optional[str] = None  # optional manual override; normally built from decisions


class CommentCreateIn(BaseModel):
    body: str
    finding_id: Optional[str] = None


class TransitionIn(BaseModel):
    action: WorkflowAction
    reason: Optional[str] = None
    override: bool = False


class ReviewResult(BaseModel):
    run: ReviewRun
    findings: List[Finding]
    used_fallback: bool
    notice: Optional[str] = None


class ContentDetail(BaseModel):
    content: ContentItem
    versions: List[ContentVersion]
    findings: List[Finding]
    latest_run: Optional[ReviewRun] = None
    comments: List[Comment] = Field(default_factory=list)
    approvals: List[Approval] = Field(default_factory=list)
    creator_name: Optional[str] = None
    allowed_actions: List[str] = Field(default_factory=list)
    has_image: bool = False


class QueueItem(BaseModel):
    content: ContentItem
    creator_name: Optional[str] = None
    open_high: int = 0
    total_findings: int = 0


class SampleOut(BaseModel):
    key: str
    title: str
    channel: str
    ai_generated: bool
    text: str
    image: bool
    alt_text: str = ""


class AuditOut(BaseModel):
    id: str
    event_type: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    target_type: str
    target_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


class RuleStat(BaseModel):
    rule_id: str
    title: str
    category: str
    count: int
    decided: int = 0
    rejected: int = 0
    override_rate: float = 0.0
    low_confidence_share: float = 0.0


class UnclearRule(BaseModel):
    rule_id: str
    title: str
    override_rate: float
    decisions: int
    reason: str
    suggestion: str


class InsightsSummary(BaseModel):
    total_findings: int
    total_content: int
    top_rules: List[RuleStat]
    by_category: List[Dict[str, Any]]
    trend: List[Dict[str, Any]]
    most_overridden: List[RuleStat]
    status_counts: Dict[str, int]
    override_approvals: int = 0
    approvals_total: int = 0

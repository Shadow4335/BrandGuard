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
    ai_backup: str = ""  # backup provider name, empty if none
    fallback_available: bool = True
    store: str
    version: str = ""
    commit: str = ""
    demo_mode: bool = True       # the one-click demo accounts are on
    signup_roles: list = ["creator", "manager", "reviewer"]  # roles a new account may pick
    firebase_enabled: bool = False  # Google sign-in (Firebase) is set up on this server
    signup: str = "open"         # "open", "invite" (an invite code is needed) or "closed"
    password_roles: list = []    # roles that can be chosen at sign-up with the admin password


class DemoLoginIn(BaseModel):
    role: str


class SignupIn(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "creator"
    invite_code: Optional[str] = None  # needed when the server has no shared sign-up workspace (see SIGNUP_INVITE_CODE)
    role_password: Optional[str] = None  # admin password, needed for manager / reviewer / admin


class GoogleLoginIn(BaseModel):
    id_token: str                  # Firebase ID token from the Google popup
    role: Optional[str] = None     # only used if this sign-in creates the account
    invite_code: Optional[str] = None  # likewise
    role_password: Optional[str] = None  # likewise: admin password for manager / reviewer / admin


class GoogleLoginOut(BaseModel):
    """"supabase": session tokens to hand to supabase-js. "memory": an offline-mode session."""
    mode: str
    created: bool = False
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    session: Optional["DemoLoginOut"] = None
    profile: Optional[Dict[str, Any]] = None  # so the browser doesn't have to look it up again


class LoginIn(BaseModel):
    email: str
    password: str


class SignupOut(BaseModel):
    email: str
    role: str
    mode: str                      # "supabase": sign in with Supabase next; "memory": token below
    session: Optional["DemoLoginOut"] = None


class DemoSessionOut(BaseModel):
    """A demo user's Supabase session, created on the server so the demo password never reaches the browser."""
    access_token: str
    refresh_token: str


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


class CommentOut(Comment):
    author_name: Optional[str] = None


class ContentDetail(BaseModel):
    content: ContentItem
    versions: List[ContentVersion]
    findings: List[Finding]
    latest_run: Optional[ReviewRun] = None
    comments: List[CommentOut] = Field(default_factory=list)
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
    findings_decided: int = 0
    decisions_total: int = 0  # approvals, escalations, change requests and rejections, not submissions
    decision_trend: List[Dict[str, Any]] = Field(default_factory=list)


SignupOut.model_rebuild()
GoogleLoginOut.model_rebuild()

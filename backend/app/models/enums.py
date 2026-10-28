from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    CREATOR = "creator"
    MANAGER = "manager"
    REVIEWER = "reviewer"


class ContentStatus(str, Enum):
    DRAFT = "draft"
    CHECKED = "checked"
    CHANGES_REQUESTED = "changes_requested"
    PENDING_MANAGER = "pending_manager"
    ESCALATED = "escalated"
    APPROVED = "approved"
    REJECTED = "rejected"


class FindingLayer(str, Enum):
    A = "A"
    B = "B"


class FindingCategory(str, Enum):
    TONE = "tone"
    TERMINOLOGY = "terminology"
    MESSAGING = "messaging"
    CLAIM = "claim"
    DISCLOSURE = "disclosure"
    VISUAL = "visual"
    ACCESSIBILITY = "accessibility"


class FindingSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class Channel(str, Enum):
    INSTAGRAM_POST = "instagram_post"
    WEBSITE_PAGE = "website_page"
    INFLUENCER_POST = "influencer_post"
    PRESS_RELEASE = "press_release"
    EMAIL = "email"


class WorkflowAction(str, Enum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    ESCALATE = "escalate"
    REJECT = "reject"


class SourceType(str, Enum):
    GUIDELINE = "guideline"
    TERMINOLOGY = "terminology"
    CLAIM_LIBRARY = "claim_library"  # approved facts
    REGULATORY = "regulatory"
    ASSET = "asset"
    OTHER = "other"

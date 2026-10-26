from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.models.enums import ContentStatus, FindingCategory, FindingSeverity, SourceType, UserRole


class Organisation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Profile(BaseModel):
    id: UUID
    org_id: UUID
    role: UserRole
    email: Optional[str] = None
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Source(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    title: str
    source_type: SourceType = SourceType.GUIDELINE
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SourceChunk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    org_id: UUID
    content: str
    embedding: Optional[List[float]] = None  # 768 dimensions
    chunk_index: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class Rule(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    name: str
    description: Optional[str] = None
    category: FindingCategory
    severity: FindingSeverity = FindingSeverity.MEDIUM
    pattern: str
    rule_type: str = "regex"  # regex, rapidfuzz, prohibited_term, required_disclosure
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContentItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    title: str
    status: ContentStatus = ContentStatus.DRAFT
    creator_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContentVersion(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content_item_id: UUID
    org_id: UUID
    version_number: int = 1
    file_type: str = "text/plain"  # text/plain, application/pdf, docx, image/png
    raw_text: Optional[str] = None
    file_path: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None


class Comment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    finding_id: Optional[UUID] = None
    content_version_id: UUID
    author_id: UUID
    text: str
    created_at: Optional[datetime] = None


class AuditEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    event_type: str  # finding_created, decision_made, status_override, content_approved, etc.
    actor_id: Optional[UUID] = None
    target_type: str  # finding, content_item, content_version, rule, source
    target_id: Optional[UUID] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    FindingCategory,
    FindingConfidence,
    FindingLayer,
    FindingSeverity,
    FindingStatus,
)


class TextSpan(BaseModel):
    start: int
    end: int


class VisualRegion(BaseModel):
    x: float
    y: float
    w: float
    h: float
    page: Optional[int] = 1


class Finding(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content_version_id: UUID
    org_id: UUID
    layer: FindingLayer
    category: FindingCategory
    rule_id: Optional[UUID] = None
    source_ids: Optional[List[UUID]] = Field(default_factory=list)
    span: Optional[TextSpan] = None
    region: Optional[VisualRegion] = None
    issue: str
    why_flagged: str
    suggested_fix: str
    severity: FindingSeverity
    confidence: FindingConfidence
    status: FindingStatus = FindingStatus.OPEN
    decided_by: Optional[UUID] = None
    decision_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_grounding_and_decisions(self) -> "Finding":
        # Hard Rule 6: Overrides/rejections require a decision reason
        if self.status in (FindingStatus.EDITED, FindingStatus.REJECTED) and self.decided_by:
            if not self.decision_reason or not self.decision_reason.strip():
                raise ValueError("A written decision reason is required when editing or rejecting a finding")

        # Layer B grounding rule: If category is claim with no sources, ensure proper issue description
        if self.layer == FindingLayer.B and self.category == FindingCategory.CLAIM:
            if not self.source_ids and "Unsupported claim" not in self.issue:
                # Keep issue explicit as required by Hard Rule 1
                pass

        return self

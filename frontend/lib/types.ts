/**
 * BrandGuard Core Data Contracts & Domain Types
 * Mirrored from backend/app/models adhering to GEMINI.md
 */

export type UserRole = "admin" | "creator" | "manager" | "reviewer";

export type ContentStatus =
  | "draft"
  | "checked"
  | "changes_requested"
  | "pending_manager"
  | "escalated"
  | "approved"
  | "rejected";

export type FindingLayer = "A" | "B";

export type FindingCategory =
  | "tone"
  | "terminology"
  | "messaging"
  | "claim"
  | "disclosure"
  | "visual"
  | "accessibility";

export type FindingSeverity = "high" | "medium" | "low";

export type FindingConfidence = "high" | "medium" | "low";

export type FindingStatus = "open" | "accepted" | "edited" | "rejected";

export type SourceType =
  | "guideline"
  | "claim_library"
  | "regulatory"
  | "asset"
  | "other";

export interface TextSpan {
  start: number;
  end: number;
}

export interface VisualRegion {
  x: number;
  y: number;
  w: number;
  h: number;
  page?: number;
}

/**
 * Core contract: Every check in Layer A and Layer B returns a Finding
 */
export interface Finding {
  id: string;
  content_version_id: string;
  org_id: string;
  layer: FindingLayer;
  category: FindingCategory;
  rule_id?: string | null;
  source_ids?: string[] | null;
  span?: TextSpan | null;
  region?: VisualRegion | null;
  issue: string;
  why_flagged: string;
  suggested_fix: string;
  severity: FindingSeverity;
  confidence: FindingConfidence;
  status: FindingStatus;
  decided_by?: string | null;
  decision_reason?: string | null;
  created_at?: string;
}

export interface Organisation {
  id: string;
  name: string;
  created_at?: string;
  updated_at?: string;
}

export interface Profile {
  id: string;
  org_id: string;
  role: UserRole;
  email?: string | null;
  full_name?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Source {
  id: string;
  org_id: string;
  title: string;
  source_type: SourceType;
  file_path?: string | null;
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface SourceChunk {
  id: string;
  source_id: string;
  org_id: string;
  content: string;
  embedding?: number[]; // 768 dimensions
  chunk_index: number;
  metadata?: Record<string, unknown>;
  created_at?: string;
}

export interface Rule {
  id: string;
  org_id: string;
  name: string;
  description?: string | null;
  category: FindingCategory;
  severity: FindingSeverity;
  pattern: string;
  rule_type: string;
  is_active: boolean;
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface ContentItem {
  id: string;
  org_id: string;
  title: string;
  status: ContentStatus;
  creator_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ContentVersion {
  id: string;
  content_item_id: string;
  org_id: string;
  version_number: number;
  file_type: string;
  raw_text?: string | null;
  file_path?: string | null;
  created_by?: string | null;
  created_at?: string;
}

export interface Comment {
  id: string;
  org_id: string;
  finding_id?: string | null;
  content_version_id: string;
  author_id: string;
  text: string;
  created_at?: string;
}

export interface AuditEntry {
  id: string;
  org_id: string;
  event_type: string;
  actor_id?: string | null;
  target_type: string;
  target_id?: string | null;
  details?: Record<string, unknown>;
  created_at?: string;
}

export interface UserContext {
  user_id: string;
  email: string;
  org_id: string;
  role: UserRole;
  full_name?: string | null;
}

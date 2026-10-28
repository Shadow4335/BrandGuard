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

export type Channel =
  | "instagram_post"
  | "website_page"
  | "influencer_post"
  | "press_release"
  | "email";

export type WorkflowAction = "submit" | "approve" | "request_changes" | "escalate" | "reject";

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
  | "terminology"
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
  run_id?: string | null;
  rule_id?: string | null;
  source_ids?: string[] | null;
  source_codes: string[];
  span?: TextSpan | null;
  span_text?: string | null;
  region?: VisualRegion | null;
  issue: string;
  why_flagged: string;
  suggested_fix: string;
  replacement?: string | null;
  severity: FindingSeverity;
  confidence: FindingConfidence;
  status: FindingStatus;
  decided_by?: string | null;
  decision_reason?: string | null;
  decision_text?: string | null;
  decided_at?: string | null;
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
  code?: string | null;
  body?: string | null;
  chunk_count?: number;
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
  channel: Channel;
  ai_generated: boolean;
  current_version: number;
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
  alt_text?: string | null;
  note?: string | null;
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

export interface ReviewRun {
  id: string;
  content_item_id: string;
  content_version_id: string;
  version_number: number;
  layer_a_ms: number;
  layer_b_ms: number;
  used_fallback: boolean;
  model?: string | null;
  created_at?: string;
}

export interface Approval {
  id: string;
  content_item_id: string;
  version_number: number;
  actor_id: string;
  role: string;
  action: WorkflowAction;
  reason?: string | null;
  override: boolean;
  created_at?: string;
}

export interface ContentDetail {
  content: ContentItem;
  versions: ContentVersion[];
  findings: Finding[];
  latest_run?: ReviewRun | null;
  comments: (Comment & { author_name?: string })[];
  approvals: Approval[];
  creator_name?: string | null;
  allowed_actions: WorkflowAction[];
  has_image: boolean;
}

export interface ReviewResult {
  run: ReviewRun;
  findings: Finding[];
  used_fallback: boolean;
  notice?: string | null;
}

export interface QueueItem {
  content: ContentItem;
  creator_name?: string | null;
  open_high: number;
  total_findings: number;
}

export interface Sample {
  key: string;
  title: string;
  channel: Channel;
  ai_generated: boolean;
  text: string;
  image: boolean;
  alt_text: string;
}

export interface AuditRow {
  id: string;
  event_type: string;
  actor_id?: string | null;
  actor_name?: string | null;
  actor_role?: string | null;
  target_type: string;
  target_id?: string | null;
  details: Record<string, unknown>;
  created_at?: string;
}

export interface RuleInfo {
  id: string;
  category: string;
  title: string;
  severity: FindingSeverity;
  reference?: string | null;
  source_code?: string | null;
  why: string;
  layer: string;
}

export interface RuleStat {
  rule_id: string;
  title: string;
  category: string;
  count: number;
  decided: number;
  rejected: number;
  override_rate: number;
  low_confidence_share: number;
}

export interface UnclearRule {
  rule_id: string;
  title: string;
  override_rate: number;
  decisions: number;
  reason: string;
  suggestion: string;
}

export interface InsightsSummary {
  total_findings: number;
  total_content: number;
  top_rules: RuleStat[];
  by_category: { category: string; count: number }[];
  trend: { date: string; count: number }[];
  most_overridden: RuleStat[];
  status_counts: Record<string, number>;
  override_approvals: number;
  approvals_total: number;
}

export interface Health {
  status: string;
  ai_provider: string;
  ai_live: boolean;
  fallback_available: boolean;
  store: "supabase" | "memory";
}

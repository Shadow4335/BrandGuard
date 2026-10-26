# BrandGuard Architecture & System Design

BrandGuard is a pre-publication brand governance platform designed with a core principle: **AI suggests, humans decide. Nothing is ever auto-published or auto-edited.**

---

## 1. Governance Layers

BrandGuard evaluates creative content through two distinct layers returning standardized `Finding` objects:

### Layer A: Deterministic Rule-Based Engine
- **Technologies**: Python regex, RapidFuzz, YAML rule library.
- **Scope**:
  - Prohibited terminology & claims (e.g. absolute guarantees).
  - Mandatory regulatory disclosures (e.g. FDA, FTC, SEC requirements).
  - Formatting, tone heuristics, and accessibility checks.
- **Confidence**: `high` (deterministic rule match).

### Layer B: Semantic Grounding & LLM Engine
- **Technologies**: Swappable LLM provider (default Gemini) and vector embeddings (768 dimensions) via pgvector.
- **Hard Grounding Principle**:
  - Layer B may **only** cite source IDs that were actually retrieved via vector similarity search.
  - If a claim has no matching evidence in the brand source library, it is flagged as an `Unsupported claim` under the `claim` category with medium/low confidence. Hallucinating sources is strictly blocked.

---

## 2. Core Data Models

Every check returns a `Finding` schema:
```typescript
interface Finding {
  id: string;
  content_version_id: string;
  org_id: string;
  layer: "A" | "B";
  category: "tone" | "terminology" | "messaging" | "claim" | "disclosure" | "visual" | "accessibility";
  rule_id?: string;
  source_ids?: string[];
  span?: { start: number; end: number };
  region?: { x: number; y: number; w: number; h: number; page?: number };
  issue: string;
  why_flagged: string;
  suggested_fix: string;
  severity: "high" | "medium" | "low";
  confidence: "high" | "medium" | "low";
  status: "open" | "accepted" | "edited" | "rejected";
  decided_by?: string;
  decision_reason?: string;
}
```

---

## 3. Security & Multi-Tenancy

- **Row-Level Security (RLS)**: Every table carries `org_id`. Data access is strictly bounded to the authenticated user's organization.
- **Append-Only Audit Log**: An PostgreSQL trigger blocks any `UPDATE` or `DELETE` statements on the `audit_log` table.
- **Auth Verification**: Token verification queries Supabase Auth via `supabase.auth.get_user(token)` without relying on local JWT secret decryption.
- **Storage Isolation**: Supabase storage buckets `sources` and `submissions` are private.

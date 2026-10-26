PROJECT: BrandGuard, a pre-publication brand governance platform. AI suggests, humans decide. Nothing is ever auto-published or auto-edited.

STACK (do not deviate):
- Frontend: Next.js (App Router), TypeScript, Tailwind, shadcn/ui, Recharts, react-diff-viewer
- Backend: FastAPI, pydantic v2, Python 3.11+ (macOS: use python3 and a venv at backend/.venv)
- Data: Supabase (Postgres, Auth, Storage, pgvector, Row Level Security)
- AI: hosted LLM API + embeddings behind a provider adapter (env: LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, EMBED_MODEL, EMBED_DIM=768, MOCK_LLM). Default to Gemini; must be swappable. Embedding output must be 768 dimensions.
- Parsing: PyMuPDF, python-docx, Tesseract OCR, Pillow, BeautifulSoup
- Rules: Python regex + rapidfuzz + YAML rule library
- Hosting: Vercel (frontend), Render via Docker (backend; Dockerfile must apt-install tesseract-ocr)
- Local ports: API 8000, web 3000. Never use 5000 (macOS AirPlay).

MONOREPO: /frontend (Next.js app), /backend (FastAPI app, YAML rules in backend/rules), /seed (SQL migrations in seed/migrations, seed scripts and sample data), /docs, README.md. Never create /apps, /supabase or /rules at the repo root. Do not create new top-level folders.

CORE CONTRACT: every check in every layer returns a pydantic Finding:
 id, content_version_id, layer ("A"|"B"), category (tone|terminology|messaging|claim|disclosure|visual|accessibility),
 rule_id (nullable), source_ids (list, nullable), span {start,end} or region {x,y,w,h,page},
 issue, why_flagged, suggested_fix, severity (high|medium|low), confidence (high|medium|low),
 status (open|accepted|edited|rejected), decided_by, decision_reason.
Confidence: High = rule-based, Medium = AI + source match, Low = needs a human look.

HARD RULES:
1. Grounding: Layer B may only cite source IDs that were actually retrieved. If no source supports a claim, output category "claim" with issue "Unsupported claim", never a guess. Validate with pydantic and drop/downgrade anything citing an unretrieved ID.
2. Every finding must show: Issue | Why flagged | Rule or source involved | Suggested fix | Severity | Confidence.
3. Suggestions preserve the creator's original intent and are never auto-applied.
4. Tenant isolation: every table has org_id; enforce with Supabase RLS and org scoping in API code; storage buckets are private.
5. audit_log is append-only (no UPDATE/DELETE, enforced by trigger/policy). Log every finding, decision, override, approval.
6. Overrides by a Reviewer require a written reason.
7. Show an in-app banner disclosing AI and external services used. Not legal advice: flags risk, humans confirm.
8. Environment variables only; never hardcode keys. SUPABASE_SERVICE_KEY and LLM_API_KEY must exist only in backend, never in frontend. Provide .env.example files.
9. Keep code simple and readable; one student developer must be able to maintain it. Add short README notes per module.

# BrandGuard

> **Pre-publication brand governance.** Creators submit content; BrandGuard checks it against the organisation's approved guidelines, facts, terminology and regulatory references, explains every issue with the rule or source behind it, suggests fixes that keep the creator's intent, and routes it through role-based review and approval.
> **AI suggests, humans decide. Nothing is ever auto-edited or auto-published.**

- **Live app:** _add the Vercel URL after deploying_ (the API sleeps on Render's free tier; the app pings it on load)
- **Backup demo video:** _add link after recording_
- Docs: [ARCHITECTURE.md](ARCHITECTURE.md) · [AI_AND_SERVICES.md](AI_AND_SERVICES.md) · [CHECKLIST.md](CHECKLIST.md) · [BUILD_WORKFLOW.md](BUILD_WORKFLOW.md)

## Try it in 2 minutes (no walkthrough needed)

The demo brand is **GlowLeaf Naturals**, a fictional Indian personal-care brand. On the login page click a role; the password for every account is `BrandGuard2026!`.

1. **Creator** → *New content* → **Load sample 1** → *Submit for AI review*. Highlighted issues appear with Issue, Why, rule/source chip, Fix, Severity and Confidence. Click a source chip to read the approved excerpt.
2. **Accept** two suggestions, **Edit** one, **Reject** one (with a reason) → *Save as new version* → the diff shows exactly those changes.
3. *Submit for review*.
4. Use the **role switcher**: **Manager** → open the item, comment, **Escalate**.
5. **Reviewer** → **Approve**. High-severity findings are unresolved, so a written override reason is required.
6. Open the audit trail on the item, then **Admin** → *Insights* (charts, most-overridden rules, "Guidelines that may be unclear").

Sample 2 is an influencer post (missing #Ad and AI label); sample 3 is a poster image (contrast and missing alt-text); sample 4 is clean.

## Stack

Next.js (App Router, TypeScript, Tailwind, Recharts, react-diff-viewer) · FastAPI + pydantic v2 · Supabase (Postgres, Auth, Storage, pgvector, RLS) · hosted LLM + embeddings behind an adapter (Gemini by default) · PyMuPDF, python-docx, Tesseract, BeautifulSoup, rapidfuzz, Pillow · Vercel + Render (Docker).

## Run locally (macOS)

Offline demo mode needs **no accounts or keys**: with no Supabase credentials the API uses a seeded in-memory store and the rule-based fallback for the AI layer.

```bash
brew install tesseract                      # OCR for image checks
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

```bash
cd frontend && cp .env.example .env.local && npm install && npm run dev   # http://localhost:3000
```

Tests (offline, no keys): `cd backend && python -m pytest -q`.

### With Supabase and a live LLM

1. Create a Supabase project. In the SQL editor run `seed/migrations/001_initial_schema.sql`, then `002_workflow.sql`.
2. Copy `backend/.env.example` to `backend/.env`; set `SUPABASE_*`, `LLM_API_KEY`, and `MOCK_LLM=false`. Copy `frontend/.env.example` to `frontend/.env.local`.
3. Seed users, brand sources and 30 days of history (idempotent): `backend/.venv/bin/python seed/seed_demo.py`.

### Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | backend only | database, auth verification, storage |
| `SUPABASE_ANON_KEY` | backend + frontend | public client key |
| `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `MOCK_LLM` | backend only | AI layer; unset key = offline fallback |
| `EMBED_MODEL`, `EMBED_DIM` | backend | embeddings (768) |
| `ALLOWED_ORIGINS` | backend | CORS (add the Vercel URL) |
| `DEMO_USER_PASSWORD` | backend/seed | password for demo accounts |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL` | frontend | public config |

Secrets live only in environment variables; `.env*` files are git-ignored.

## Deploy

- **Backend (Render, Docker):** root `backend/`, uses `backend/Dockerfile` (installs Tesseract). Set the backend env vars above.
- **Frontend (Vercel):** root `frontend/`, set the three `NEXT_PUBLIC_*` vars (API URL = the Render URL).

## Requirement mapping

| Requirement | Where |
|---|---|
| Define guidelines, facts, terminology, assets | `/brand`, `sources`, YAML rules in `backend/rules` |
| Review text, images, documents | text, PDF, DOCX, image (OCR) parsing |
| Tone, language, facts, claims, visuals, accessibility | Layer A (rules) + Layer B (grounded AI) |
| Explain and cite | Explanation cards, rule/source chips |
| Suggest without overriding humans | Accept / Edit / Reject; new versions built only from decisions |
| Comments, approvals, history, roles | workflow state machine, `approvals`, `content_versions`, `comments` |
| Recurring problems | `/insights`, unclear-guideline flags |
| Confidentiality and AI disclosure | RLS, private buckets, banner, `/about-ai`, AI_AND_SERVICES.md |

*Not legal advice. The demo brand, facts and certifications are fictional; regulatory summaries are paraphrased, so verify against the official sources linked in each.*

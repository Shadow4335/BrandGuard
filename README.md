# BrandGuard

> **Pre-publication brand governance.** Creators submit content; BrandGuard checks it against the organisation's approved guidelines, facts, terminology and regulatory references, explains every issue with the rule or source behind it, suggests fixes that keep the creator's intent, and routes it through role-based review and approval.
> **AI suggests, humans decide. Nothing is ever auto-edited or auto-published.**

- **Live app:** https://brand-guard-lovat.vercel.app (API: https://brandguard-api-74et.onrender.com). The API sleeps on Render's free tier, so the first load can take up to a minute; the app pings it on load.
- **Demo video and Round 2 PDF:** [Google Drive folder](https://drive.google.com/drive/folders/1lYTpx39wpcZCzE3xBsDXBks_W1Axockj?usp=sharing)
- **Docs:** [ARCHITECTURE.md](ARCHITECTURE.md) · [AI_AND_SERVICES.md](AI_AND_SERVICES.md) · [SECURITY.md](SECURITY.md) · [CHECKLIST.md](CHECKLIST.md) · [BUILD_WORKFLOW.md](BUILD_WORKFLOW.md)

## What it does

1. **Define the brand.** The `/brand` page holds the organisation's sources (guidelines, approved facts, terminology, regulatory references) next to the YAML rules in `backend/rules` (absolute claims, disclosures, terminology, visual accessibility, AI-checked rules).
2. **Submit content.** Paste text or upload a file (up to 10 MB):
   - PDF (scanned PDFs are read with OCR, first 5 pages)
   - Word `.docx` (pictures without alt-text are flagged)
   - Images: PNG, JPG, WEBP, GIF, BMP, TIFF (OCR, contrast and alt-text checks; alt-text can be added later from the content page)
   - TXT, Markdown, and HTML (`<img>` without alt is flagged)

   Old `.doc`, HEIC, PowerPoint and other files get a clear message asking for a supported format.
3. **Two-layer review.**
   - **Layer A** is deterministic: regex and fuzzy-terminology rules, structural checks (missing `#Ad`, missing AI label, contradictory disclaimers, alt-text) and a WCAG contrast check on image regions. Findings carry exact spans and high confidence.
   - **Layer B** is grounded AI: the model sees only the sources retrieved for that content (pgvector retrieval), and its JSON output is validated. Citations outside the retrieved set are downgraded to *Unsupported claim*; spans that can't be located are dropped. With no key, or on timeout or error, an offline heuristic produces the same shape and a visible notice says so.
4. **Explain and cite.** Every finding shows Issue, Why, a rule/source chip (click it to read the approved excerpt), Fix, Severity and Confidence.
5. **Human decisions.** Creators Accept, Edit or Reject each suggestion (rejections need a reason). *Save as new version* builds the next version only from those decisions, and a diff shows exactly what changed.
6. **Workflow.** Draft → submitted → manager review / escalation → reviewer approval, with comments. Approving with unresolved high-severity findings requires a written override reason, whoever approves. Every step lands in the audit trail.
7. **Insights.** The `/insights` page (admin) charts review volume, the most-rejected rules, and flags "Guidelines that may be unclear".
8. **Transparency.** `/about-ai` and [AI_AND_SERVICES.md](AI_AND_SERVICES.md) describe what AI does and which services see data.

**Roles:** Creator (submit, resolve findings), Manager (review, comment, escalate), Reviewer (approve/reject), Admin (insights, brand sources, workspaces).

## Use the live deployment

Open https://brand-guard-lovat.vercel.app. If it seems stuck, wait up to a minute while the free-tier API wakes up.

The demo brand is **GlowLeaf Naturals**, a fictional Indian personal-care brand.

- **Quick tour:** on the login page click a role; demo accounts sign in with one click (the server signs them in, so there is no password to type).
- **Your own account:** *Sign up* (top right or under the login form) puts you in as a **Creator**. Manager, Reviewer and Admin need the admin password (`PRIVILEGED_SIGNUP_PASSWORD`) set by whoever runs the deployment. Passwords need 10+ characters. No email confirmation. **Continue with Google** appears when Firebase is configured.

### Two-minute walkthrough

1. **Creator** → *New content* → **Load sample 1** → *Submit for AI review*. Click a source chip to read the approved excerpt.
2. **Accept** two suggestions, **Edit** one, **Reject** one (with a reason) → *Save as new version* → the diff shows exactly those changes.
3. *Submit for review*.
4. Use the **role switcher**: **Manager** → open the item, comment, **Escalate**.
5. **Reviewer** → **Approve**. High-severity findings are unresolved, so a written override reason is required (the Manager's Approve asks for one too).
6. Open the audit trail on the item, then **Admin** → *Insights*.

Samples: 1 is a marketing claim post, 2 an influencer post (missing #Ad and AI label), 3 a poster image (contrast and missing alt-text), 4 is clean.

The role switcher is shown only while signed in as a demo user; otherwise sign out and pick another role.

## Run locally

Prerequisites: Python 3.11+, Node.js 20.9+, and Tesseract for OCR on images and scanned PDFs (`brew install tesseract` on macOS, `apt install tesseract-ocr` on Debian/Ubuntu; set `TESSERACT_CMD` if it isn't on `PATH`).

```bash
git clone https://github.com/Shadow4335/BrandGuard.git && cd BrandGuard
```

### Offline mode (no accounts, no keys)

With no Supabase credentials the API uses a seeded in-memory store, and with no LLM key the rule-based fallback replaces Layer B. Set `DEMO_MODE=true` to get the one-click demo accounts (it is off by default). You don't need a `backend/.env` for this.

Terminal 1, from the repository root:

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
DEMO_MODE=true uvicorn app.main:app --port 8000
```

Terminal 2, from the repository root:

```bash
cd frontend && cp .env.example .env.local && npm install && npm run dev
```

Open http://localhost:3000, click **Sign in**, pick a role under the demo accounts, and follow the walkthrough above. In-memory data resets when the API restarts, and demo sessions end with it: if the app says it can't load your workspace, sign out and pick a role again.

In Claude Code, `.claude/launch.json` defines `api`, `web`, and fully offline `api-offline` (port 8001) / `web-offline` (port 3001) servers.

Tests and checks (offline, no keys), from the repository root:

```bash
cd backend && .venv/bin/python -m pytest -q
```

```bash
cd frontend && npx tsc --noEmit && npm run lint && npm run build
```

### Troubleshooting

| What you see | What to do |
|---|---|
| No demo accounts on the sign-in page | Start the API with `DEMO_MODE=true`, then reload. |
| "Sign-up is closed on this server" | Same: use `DEMO_MODE=true`, or set `SIGNUP_ORG_ID` or `SIGNUP_INVITE_CODE`. |
| "Can't reach the BrandGuard server" | The API isn't running on the port in `NEXT_PUBLIC_API_URL` (`frontend/.env.local`). |
| CORS errors in the browser console | Serving the frontend somewhere other than `localhost:3000`? Add its address to `ALLOWED_ORIGINS` for the API. |
| Images or scanned PDFs have no extracted text | Tesseract isn't installed or isn't on `PATH`. |
| The orange "AI layer unavailable" notice | Expected with no LLM key: rule checks and the offline fallback still run. |

### With Supabase and a live LLM

1. Create a Supabase project. In the SQL editor run, in order, `seed/migrations/001_initial_schema.sql`, `002_workflow.sql`, `003_security_hardening.sql`, and optionally `004_workspace_memberships.sql` (extra workspaces; it doesn't move or re-grant existing accounts).
2. `cp backend/.env.example backend/.env` and set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `LLM_API_KEY`, and `MOCK_LLM=false`. Fill in `frontend/.env.local` from `frontend/.env.example`.
3. For one-click demo accounts also set `DEMO_MODE=true` and a long random `DEMO_USER_PASSWORD` (the API refuses to start in demo mode with Supabase while it is the published default), then run `python seed/rotate_demo_passwords.py`.
4. Seed users, brand sources and 30 days of history (idempotent): `backend/.venv/bin/python seed/seed_demo.py`.
5. Start both servers as above.

Admins can create extra workspaces from the workspace dropdown (needs migration 004); each switch is checked against verified membership.

### Google sign-in (optional, Firebase)

Firebase only confirms who the person is. The API verifies the Firebase ID token, finds or creates the BrandGuard account for that Google email (role picked on the sign-up page) and returns a normal session. The button stays hidden until both sides are configured.

1. [Firebase console](https://console.firebase.google.com) → create a project → *Authentication* → *Sign-in method* → enable **Google**.
2. *Authentication* → *Settings* → *Authorized domains*: `localhost` is there by default; add your Vercel domain.
3. *Project settings* → *Your apps* → add a **Web** app; put its `apiKey`, `authDomain`, `projectId` and `appId` in `frontend/.env.local` as the four `NEXT_PUBLIC_FIREBASE_*` values.
4. Set `FIREBASE_PROJECT_ID` in `backend/.env`. No service-account key is needed.
5. Restart both servers.

Elevated roles via Google also require `PRIVILEGED_SIGNUP_PASSWORD`.

## Deploy

**Backend (Render, Docker):** root `backend/`, uses `backend/Dockerfile` (installs Tesseract, runs as an unprivileged user, honours `$PORT`). Set the backend env vars below, including `ALLOWED_ORIGINS` with the Vercel URL.

**Frontend (Vercel):** root `frontend/`. Set `NEXT_PUBLIC_API_URL` to the Render URL plus the `NEXT_PUBLIC_SUPABASE_*` and (optional) `NEXT_PUBLIC_FIREBASE_*` values. On hosts that restrict Turbopack worker ports, build with `npm run build -- --webpack`.

**Google sign-in in production (needed for Safari):** Safari blocks storage for Firebase's sign-in iframe when it comes from `<project>.firebaseapp.com`, so the app proxies `/__/auth/*` through its own domain (`frontend/next.config.ts`).

1. Google Cloud console → APIs & Services → Credentials → the "Web client (auto created by Google Service)" OAuth client → *Authorized redirect URIs*: add `https://<your-vercel-domain>/__/auth/handler`.
2. On Vercel set `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` to `<your-vercel-domain>` (no `https://`) and redeploy. Locally keep `<project>.firebaseapp.com`.

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | backend only | database, auth verification, storage. Empty = in-memory store |
| `SUPABASE_ANON_KEY` | backend + frontend | public client key |
| `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `MOCK_LLM` | backend only | AI layer; `MOCK_LLM=true` or no key = offline fallback |
| `LLM_FALLBACK_MODEL` | backend only | second Gemini model used when the main one is overloaded or out of quota (default `gemini-flash-lite-latest`) |
| `LLM_BACKUP_PROVIDER`, `LLM_BACKUP_API_KEY`, `LLM_BACKUP_MODEL` | backend only | optional second provider (`groq`, `anthropic`, `openai`, `xai` or another `gemini` key) tried when Gemini fails. The demo uses Groq (`openai/gpt-oss-120b`) |
| `EMBED_MODEL`, `EMBED_DIM` | backend | embeddings (768, must match the migrations) |
| `ALLOWED_ORIGINS` | backend | CORS (add the Vercel URL) |
| `DEMO_MODE` | backend | `false` (default): real accounts only. `true`: one-click demo accounts, and anyone may sign up to the shared demo workspace |
| `DEMO_USER_PASSWORD` | backend/seed | secret password of the four demo accounts; only the server uses it |
| `PRIVILEGED_SIGNUP_PASSWORD` | backend only | admin password (12+ characters) that lets people sign up as manager, reviewer or admin; empty = those roles can't be chosen |
| `SIGNUP_ORG_ID` | backend only | workspace anyone may join at sign-up. Without it (and with `DEMO_MODE` off), sign-up needs `SIGNUP_INVITE_CODE`, or is closed |
| `SIGNUP_INVITE_CODE` | backend only | code required at sign-up when there's no `SIGNUP_ORG_ID` and demo mode is off |
| `FIREBASE_PROJECT_ID` | backend | turns on Google sign-in |
| `TESSERACT_CMD` | backend | path to Tesseract if not on `PATH` |
| `NEXT_PUBLIC_API_URL` | frontend | backend URL (`http://localhost:8000` locally) |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend | public Supabase config |
| `NEXT_PUBLIC_FIREBASE_API_KEY`, `_AUTH_DOMAIN`, `_PROJECT_ID`, `_APP_ID` | frontend | Firebase web app config (public values) |

Secrets live only in environment variables; `.env*` files are git-ignored. No provider keys or admin passwords belong in frontend configuration.

## Stack

Next.js (App Router, TypeScript, Tailwind, Recharts, react-diff-viewer) · FastAPI + pydantic v2 · Supabase (Postgres, Auth, Storage, pgvector, RLS) · hosted LLM + embeddings behind an adapter (Gemini by default) · PyMuPDF, python-docx, Tesseract, BeautifulSoup, rapidfuzz, Pillow · Firebase (optional Google sign-in) · Vercel + Render (Docker).

## Requirement mapping

| Requirement | Where |
|---|---|
| Define guidelines, facts, terminology, assets | `/brand`, `sources`, YAML rules in `backend/rules` |
| Review text, images, documents | text, PDF, DOCX, HTML, image (OCR) parsing |
| Tone, language, facts, claims, visuals, accessibility | Layer A (rules) + Layer B (grounded AI) |
| Explain and cite | Explanation cards, rule/source chips |
| Suggest without overriding humans | Accept / Edit / Reject; new versions built only from decisions |
| Comments, approvals, history, roles | workflow state machine, `approvals`, `content_versions`, `comments` |
| Recurring problems | `/insights`, unclear-guideline flags |
| Confidentiality and AI disclosure | RLS, private buckets, banner, `/about-ai`, AI_AND_SERVICES.md |

*Not legal advice. The demo brand, facts and certifications are fictional; regulatory summaries are paraphrased, so verify against the official sources linked in each.*

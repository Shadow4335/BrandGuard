# BrandGuard

> **Pre-publication brand governance.** Creators submit content; BrandGuard checks it against the organisation's approved guidelines, facts, terminology and regulatory references, explains every issue with the rule or source behind it, suggests fixes that keep the creator's intent, and routes it through role-based review and approval.
> **AI suggests, humans decide. Nothing is ever auto-edited or auto-published.**

- **Live app:** https://brand-guard-lovat.vercel.app (API: https://brandguard-api-74et.onrender.com). The API sleeps on Render's free tier, so the first load can take up to a minute; the app pings it on load
- **Demo video and Round 2 PDF:** [Google Drive folder](https://drive.google.com/drive/folders/1lYTpx39wpcZCzE3xBsDXBks_W1Axockj?usp=sharing)
- Docs: [ARCHITECTURE.md](ARCHITECTURE.md) · [AI_AND_SERVICES.md](AI_AND_SERVICES.md) · [CHECKLIST.md](CHECKLIST.md) · [BUILD_WORKFLOW.md](BUILD_WORKFLOW.md)

## Try it in 2 minutes (no walkthrough needed)

The demo brand is **GlowLeaf Naturals**, a fictional Indian personal-care brand. On the login page click a role: the demo accounts sign in with one click (the server signs them in, so there is no password to type or find). See [SECURITY.md](SECURITY.md) for how accounts and passwords are protected.

1. **Creator** → *New content* → **Load sample 1** → *Submit for AI review*. Highlighted issues appear with Issue, Why, rule/source chip, Fix, Severity and Confidence. Click a source chip to read the approved excerpt.
2. **Accept** two suggestions, **Edit** one, **Reject** one (with a reason) → *Save as new version* → the diff shows exactly those changes.
3. *Submit for review*.
4. Use the **role switcher**: **Manager** → open the item, comment, **Escalate**.
5. **Reviewer** → **Approve**. High-severity findings are unresolved, so a written override reason is required.
6. Open the audit trail on the item, then **Admin** → *Insights* (charts, most-overridden rules, "Guidelines that may be unclear").

Sample 2 is an influencer post (missing #Ad and AI label); sample 3 is a poster image (contrast and missing alt-text); sample 4 is clean.

**Your own account:** click *Sign up* (top right or under the login form), and you're in as a Creator. Manager, Reviewer and Admin can also be chosen there with the admin password (`PRIVILEGED_SIGNUP_PASSWORD`). Passwords need 10+ characters and are checked on the server. No email confirmation. New accounts join the shared GlowLeaf Naturals demo workspace, so brand sources and sample history are already there. Admin signup also requires the server-configured admin password. To see the whole workflow, use the demo role switcher (shown only while signed in as a demo user) or sign out and pick another demo role.

**Supported uploads (up to 10 MB):** PDF (scanned PDFs are read with OCR, first 5 pages), Word `.docx` (pictures without alt-text are flagged), images PNG/JPG/WEBP/GIF/BMP/TIFF (OCR, contrast and alt-text checks; add alt-text later from the content page), TXT/Markdown, and HTML (`<img>` without alt is flagged). Old `.doc`, HEIC, PowerPoint and other files get a clear message asking for a supported format.

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

1. Create a Supabase project. In the SQL editor run `seed/migrations/001_initial_schema.sql`, then `002_workflow.sql`, then `003_security_hardening.sql`.
2. Copy `backend/.env.example` to `backend/.env`; set `SUPABASE_*`, `LLM_API_KEY`, and `MOCK_LLM=false`. Copy `frontend/.env.example` to `frontend/.env.local`.
3. Seed users, brand sources and 30 days of history (idempotent): `backend/.venv/bin/python seed/seed_demo.py`.

### Google sign-in (optional, Firebase)

Firebase only confirms who the person is. The API checks the Firebase ID token, finds the BrandGuard account with that verified Google email (or creates one on first sign-in, with the role picked on the sign-up page) and returns a normal session, so roles and workspaces work as before. The "Continue with Google" button stays hidden until both sides are configured.

1. [Firebase console](https://console.firebase.google.com) → create a project → *Authentication* → *Sign-in method* → enable **Google**.
2. *Authentication* → *Settings* → *Authorized domains*: `localhost` is there by default; add your Vercel domain.
3. *Project settings* → *Your apps* → add a **Web** app; put its `apiKey`, `authDomain`, `projectId` and `appId` in `frontend/.env.local` as the four `NEXT_PUBLIC_FIREBASE_*` values.
4. Set `FIREBASE_PROJECT_ID` (same project ID) in `backend/.env`. No service-account key is needed.
5. Restart both servers.

**Production (needed for Safari):** Safari blocks storage for the sign-in iframe when it comes from `<project>.firebaseapp.com`, so on the deployed site Firebase's sign-in pages are served from the app's own domain (`/__/auth/*` is proxied in `frontend/next.config.ts`).

1. Google Cloud console → APIs & Services → Credentials → the "Web client (auto created by Google Service)" OAuth client → *Authorized redirect URIs*: add `https://<your-vercel-domain>/__/auth/handler`.
2. On Vercel set `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` to `<your-vercel-domain>` (no `https://`) and redeploy. Locally keep `<project>.firebaseapp.com`.

### Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | backend only | database, auth verification, storage |
| `SUPABASE_ANON_KEY` | backend + frontend | public client key |
| `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `MOCK_LLM` | backend only | AI layer; unset key = offline fallback |
| `LLM_FALLBACK_MODEL` | backend only | second Gemini model used when the main one is overloaded or out of quota (default `gemini-flash-lite-latest`) |
| `LLM_BACKUP_PROVIDER`, `LLM_BACKUP_API_KEY`, `LLM_BACKUP_MODEL` | backend only | optional second provider (`groq`, `anthropic`, `openai`, `xai` or another `gemini` key) tried when Gemini fails. The demo uses Groq (`openai/gpt-oss-120b`) |
| `SIGNUP_ORG_ID` | backend only | optional: workspace anyone may join at sign-up. Without it (and with `DEMO_MODE` off) sign-up needs `SIGNUP_INVITE_CODE`, or is closed |
| `SIGNUP_INVITE_CODE` | backend only | optional: code people must enter to sign up when there's no `SIGNUP_ORG_ID` and demo mode is off |
| `EMBED_MODEL`, `EMBED_DIM` | backend | embeddings (768) |
| `ALLOWED_ORIGINS` | backend | CORS (add the Vercel URL) |
| `DEMO_USER_PASSWORD` | backend/seed | secret password of the four demo accounts; only the server uses it. Set a long random value and run `seed/rotate_demo_passwords.py` |
| `DEMO_MODE` | backend | `false` (default) leaves only real accounts; `true` enables the one-click demo accounts and lets anyone sign up to the shared demo workspace. With Supabase, the API refuses to start in demo mode while `DEMO_USER_PASSWORD` is the published default |
| `SIGNUP_ALLOWED_ROLES` | backend | legacy option, ignored; Creator is the only role without an admin password |
| `PRIVILEGED_SIGNUP_PASSWORD` | backend only | admin password (12+ characters) that lets people sign up as manager, reviewer or admin; empty means those roles can't be chosen at sign-up |
| `FIREBASE_PROJECT_ID` | backend | turns on Google sign-in; ID tokens must come from this Firebase project |
| `NEXT_PUBLIC_FIREBASE_API_KEY`, `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`, `NEXT_PUBLIC_FIREBASE_PROJECT_ID`, `NEXT_PUBLIC_FIREBASE_APP_ID` | frontend | Firebase web app config for the Google popup (public values) |
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

### Silver interface and additional workspaces

The current interface follows `BrandGuard-Latest-Kit`: Silver artwork, responsive workspace navigation, manual hero slides, sliding tabs and reduced-motion support. For extra workspaces, apply the optional additive `seed/migrations/004_workspace_memberships.sql` in Supabase; this does not move accounts or grant access to existing organisations. Admins can then create a real workspace from the workspace dropdown. Additional members and their roles are provisioned server-side. Each switch is checked against verified membership; the original profile and workspace are retained. In-memory mode supports the same API for local testing.

Elevated email and Google signup always require `PRIVILEGED_SIGNUP_PASSWORD` (12+ characters, backend only). `SIGNUP_ALLOWED_ROLES` can no longer bypass this requirement. Google requires the Firebase configuration described above. No provider keys or admin passwords belong in frontend configuration.

On hosts that restrict Turbopack worker ports, use `cd frontend && npm run build -- --webpack`; both build engines use the official Tailwind PostCSS integration.

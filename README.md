# BrandGuard

> **Pre-publication brand governance platform.**  
> *AI suggests, humans decide. Nothing is ever auto-published or auto-edited.*

---

## 🚀 Quickstart (macOS)

### 1. Prerequisites
- **Python 3.11+** (`python3`)
- **Node.js 20+** and `npm`
- **Tesseract OCR** (optional for local visual OCR): `brew install tesseract`

---

### 2. Backend Setup & Run

1. Navigate to `/backend` and configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase and Gemini credentials
   ```

2. Create virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Start the FastAPI server (Runs on port `8000`, never `5000`):
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Verify status at [http://localhost:8000/health](http://localhost:8000/health).

---

### 3. Database Migration & Seed

1. Copy the SQL migration in `seed/migrations/001_initial_schema.sql` and run it in your **Supabase SQL Editor** in a single paste.
2. Run the seed script to set up the **Demo Brand** organization and 4 demo user roles:
   ```bash
   python3 seed/seed_users.py
   ```
   Demo accounts created:
   - `admin@demo.test` (Role: `admin`)
   - `creator@demo.test` (Role: `creator`)
   - `manager@demo.test` (Role: `manager`)
   - `reviewer@demo.test` (Role: `reviewer`)
   - Default Password: `BrandGuard2026!`

---

### 4. Frontend Setup & Run

1. Navigate to `/frontend` and configure your environment:
   ```bash
   cp .env.example .env.local
   # Enter your NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
   ```

2. Install dependencies and start the development server:
   ```bash
   npm install
   npm run dev
   ```
3. Open [http://localhost:3000](http://localhost:3000) in your browser. Use the **Demo accounts** panel on the login screen for 1-click role testing.

---

## 🏛️ Monorepo Architecture

```
BrandGuard/
├── backend/            # FastAPI app, models, auth, YAML rules, Dockerfile
│   ├── app/            # FastAPI source code (main.py, auth.py, config.py, models/)
│   ├── rules/          # Layer A YAML rule definitions
│   └── .venv/          # Python 3 virtual environment
├── frontend/           # Next.js App Router, Tailwind CSS, shadcn/ui components
│   ├── app/            # App Router pages and layouts
│   └── lib/            # Types (types.ts), Supabase client
├── seed/               # Database setup
│   ├── migrations/     # 001_initial_schema.sql (pgvector, RLS, audit trigger)
│   └── seed_users.py   # Idempotent demo accounts seed script
├── docs/               # System documentation
├── GEMINI.md           # Core platform rules & non-negotiables
└── README.md           # This file
```

---

## 🛡️ Core Rules & Compliance Notice

- **Human in the Loop**: AI provides suggestions; content changes require human review and approval.
- **Tenant Isolation**: All database queries are scoped by `org_id` with Row-Level Security (RLS).
- **Append-Only Audit**: The `audit_log` table strictly prevents updates and deletions via PostgreSQL trigger.
- **Notice**: *AI-assisted review. Suggestions are never auto-applied. Not legal advice.*
# Build checklist (honest status)

Layout note: the repo's own rules (GEMINI.md) took precedence over BUILD_WORKFLOW.md where they conflicted: SQL lives in `seed/migrations`, rules in `backend/rules`, embeddings are 768-dim, Gemini is the default provider, ports 8000/3000. No `supabase/` folder was created. Migration 002 extends the existing schema instead of replacing it ("In review" is the existing `pending_manager` status).

## Gates

| Gate | Status | Evidence |
|---|---|---|
| 1 Skeleton and contracts | Passed (local) | `/api/health` works; TypeScript types compile; pydantic models mirrored in `frontend/lib/types.ts` |
| 2A Layer A | Passed | `pytest tests/test_layer_a.py`: sample 1 gives 8 findings with exact spans; poster gives contrast and alt-text findings |
| 2B Auth and content flow | Passed (offline demo mode, checked in the in-app browser) | One-click role login, dashboard checklist, `/brand`, content from a sample |
| 3A Layer B, merger | Passed | `test_grounding.py` (fabricated source rejected), `test_merger.py`; with no LLM key the review returns `used_fallback=true` and the notice |
| 3B Hero screen | Passed (offline demo mode, in-app browser) | Review, highlighted spans with citations, accept/edit/reject, save v2, diff shows exactly those changes |
| 4A State machine, seed | Passed | Transitions tested offline. `seed/seed_demo.py` ran on a fresh Supabase project and a second run created nothing new (idempotent) |
| Live check | Passed | Real Supabase Auth login for all roles, live Gemini review, pgvector retrieval, the full submit/escalate/override-approve flow, creator blocked (403) from adding sources, and the DB trigger blocks `audit_log` updates. Run once via a script on localhost |
| 4B Review queue and approvals | Passed (offline demo mode, in-app browser) | Creator submit, Manager comment and escalate, Reviewer override approval with reason; audit entries visible |
| 5 Insights | Passed | Seeded charts render; `RULE-TONE-HYPE` (62% overridden) and `RULE-CLAIM-UNSUPPORTED` appear under "may be unclear" |
| 6 Deploy | Passed | Vercel + Render + Supabase live; Golden Path steps 1-10 walked through by Claude on the deployed link (real Supabase login, live Gemini review, decisions, v2 diff, submit, manager escalate, reviewer override approval, audit, Insights). Not yet done: the "stranger test" with a real first-time user, and the backup demo video |

Test suite: `cd backend && python -m pytest -q` (38 tests, offline).

## Upload formats and real accounts

| Check | Status |
|---|---|
| PDF (text), scanned PDF (OCR), DOCX (with alt-text check on pictures), PNG/JPG/WEBP/GIF (OCR, contrast, alt-text), TXT/Markdown (UTF-8 and UTF-16), HTML (`<img>` alt) | Tested offline (`tests/test_uploads.py`), against real Supabase storage, and on the live Render API (PDF, scanned PDF, DOCX, JPG, PNG, TXT, HTML created; images and scanned PDF reviewed with live Gemini; three clean repeat runs with health checks answering throughout) |
| Corrupt, empty, oversized (>10 MB), `.doc`, HEIC, `.pptx`, `.zip` | Friendly 4xx message, no crash (tested) |
| Sign-up with a chosen role, sign-in, wrong password, duplicate email, validation, rate limit (5 per IP per 10 min) | Tested offline and through the UI on a local offline build. **Supabase sign-up path not exercised by Claude** (no real accounts were created on the live site); it uses the same admin API as the seed script, which worked |

## Known limitations
- The API uses the Supabase service role, so RLS and storage policies were not exercised directly (API-level role and org checks were).
- The Gemini key is on the free tier: `gemini-2.5-flash` hit its daily quota (429) during testing. Quota errors now skip straight to `LLM_FALLBACK_MODEL` (`gemini-flash-lite-latest`, verified working); overload (503) retries once first. A backup provider with its own key (`LLM_BACKUP_*`; this deployment uses Groq, `openai/gpt-oss-120b`) is tried next; verified with a real call with Gemini switched off (answered in about 4 s with grounded findings). Only if all of these fail does the review use offline checks. The chain is also unit-tested with fake providers, then falls back to offline checks with a visible notice. Live reviews take roughly 20 seconds. Which findings the model raises varies run to run (for example "100% natural" may be labelled Unsupported rather than contradicting FACT-001).
- Free-tier Render sleeps after ~15 minutes idle; the first request can take up to a minute.
- The version diff viewer loads lazily and can take a few seconds the first time.
- Findings re-order after a decision is made (decided cards move down).
- Offline "demo mode" (in-memory store, `demo.<id>` tokens) activates only when Supabase credentials are absent. Data resets on restart.
- Gemini (review and `gemini-embedding-001` at 768 dims) is verified live; the Anthropic and OpenAI adapters are untested. `text-embedding-004` no longer exists on the API, so the default changed. The offline heuristic stands in for the "cached Layer B" in the workflow: it is generic (numbers, superlatives, exclamations), not hash-keyed per sample, and is cruder than a model.
- Layer A merges: chemical-free/toxin-free and cure are covered by the terminology rule, so claim rules do not list them separately.
- Findings Merger does not use embedding similarity for messaging consistency (P1, skipped). Logo/palette check and admin rule editor UI (P1) were skipped; rules are YAML with a read-only viewer.
- Contrast check relies on Tesseract finding words; on very busy images it may miss text.
- Accept on a finding without a literal replacement only acknowledges it; the creator must Edit to change text.
- No Lighthouse accessibility run; contrast and keyboard focus were handled by design but not measured. Light theme only.
- Not done: step 12 of the Golden Path on a deployed environment (covered by an automated offline test instead).
- Sign-ups join the shared demo workspace and can pick any role, including Admin, which can add brand sources (nothing can be deleted through the app). This trades isolation for letting judges try every role.
- Scanned PDFs: OCR covers the first 5 pages. Images are OCR'd at most 2500 px on the long side, with a 30 s OCR time limit.
- Server memory on the 512 MB Render instance: PyMuPDF is pinned to 1.26 because 2.x loads onnxruntime (~190 MB) and crashed the instance during OCR. Peak is now about 175 MB plus about 45 MB for Tesseract.
- Image reviews take 5 to 30 seconds on the live server, depending mostly on Gemini latency.

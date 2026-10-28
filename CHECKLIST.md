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
| 4A State machine, seed | Partly verified | All legal/illegal transitions tested. Memory seeding verified. `seed/seed_demo.py` (Supabase) was **not run**: no Supabase project was available |
| 4B Review queue and approvals | Passed (offline demo mode, in-app browser) | Creator submit, Manager comment and escalate, Reviewer override approval with reason; audit entries visible |
| 5 Insights | Passed | Seeded charts render; `RULE-TONE-HYPE` (62% overridden) and `RULE-CLAIM-UNSUPPORTED` appear under "may be unclear" |
| 6 Deploy and stranger test | **Not done** | No Vercel/Render/Supabase accounts were used; the README link and demo video are placeholders |

Test suite: `cd backend && python -m pytest -q` (38 tests, offline).

## Known limitations
- **Not deployed**; nothing here was run against real Supabase, Gemini or Render. `002_workflow.sql` was only syntax-checked (pglast), not executed. RLS policies, pgvector search, storage policies and Supabase Auth login are untested.
- Offline "demo mode" (in-memory store, `demo.<id>` tokens) activates only when Supabase credentials are absent. Data resets on restart.
- Live LLM path (Gemini, Anthropic, OpenAI adapters, embeddings) is implemented but untested against the real APIs. The offline heuristic stands in for the "cached Layer B" in the workflow: it is generic (numbers, superlatives, exclamations), not hash-keyed per sample, and is cruder than a model.
- Layer A merges: chemical-free/toxin-free and cure are covered by the terminology rule, so claim rules do not list them separately.
- Findings Merger does not use embedding similarity for messaging consistency (P1, skipped). Logo/palette check and admin rule editor UI (P1) were skipped; rules are YAML with a read-only viewer.
- Contrast check relies on Tesseract finding words; on very busy images it may miss text.
- Accept on a finding without a literal replacement only acknowledges it; the creator must Edit to change text.
- No Lighthouse accessibility run; contrast and keyboard focus were handled by design but not measured. Light theme only.
- Not done: step 12 of the Golden Path on a deployed environment (covered by an automated offline test instead).

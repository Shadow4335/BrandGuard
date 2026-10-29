# BrandGuard: Project Report

**Pre-publication brand governance. AI suggests, humans decide. Nothing is ever auto-edited or auto-published.**

Live app: https://brand-guard-lovat.vercel.app · API: https://brandguard-api-74et.onrender.com · Repo: github.com/Shadow4335/BrandGuard

---

## 1. The problem and what BrandGuard does

Marketing teams publish content (social posts, web pages, influencer posts, press releases, emails) that can break the brand's own rules or advertising regulations: banned words, exaggerated or unsupported claims, wrong facts, missing influencer disclosures, unreadable text on images, missing alt-text. Catching this by hand is slow and inconsistent.

BrandGuard checks content **before it is published**. A creator submits text, a PDF, a DOCX or an image. The system:

1. checks it against the organisation's approved guidelines, facts, terminology and regulatory references;
2. explains every issue, naming the rule or source behind it;
3. suggests fixes that keep the creator's intent;
4. lets the creator accept, edit or reject each suggestion;
5. routes the result through a role-based review and approval workflow with a full audit trail;
6. shows managers which rules are violated most often and which guidelines people keep disagreeing with.

The demo organisation is **GlowLeaf Naturals**, a fictional Indian personal-care brand, so no real company is implicated.

## 2. Core principles

| Principle | How it shows up in the product |
|---|---|
| AI suggests, humans decide | Nothing changes the text until a creator accepts or edits a suggestion and saves a new version. Nothing is published by the system. |
| Explainability | Every finding shows Issue, Why flagged, Rule or source, Suggested fix, Severity, Confidence. |
| No guessing | If no approved source supports a claim, it is labelled **Unsupported claim** instead of being invented. |
| Accountability | Append-only audit log, version history, approvals with reasons. A reviewer who approves with unresolved high-severity issues must write an override reason. |
| Privacy and disclosure | Each organisation's data is isolated; an AI-use banner is on every page; an About AI page explains what is sent where. "Not legal advice" appears on regulatory findings. |
| Never fail the demo | Every AI call has a timeout, retries and an offline fallback. |

## 3. Users and roles

| Role | What they can do |
|---|---|
| **Creator** | Create content, run the review, accept/edit/reject suggestions, save versions, submit for review, comment |
| **Brand Manager** | See the review queue, comment, **Approve / Request changes / Escalate** |
| **Authorised Reviewer** | Handle escalated items: **Approve / Reject**. Approving with unresolved high-severity findings requires a written override reason |
| **Admin** | Manage brand sources (typed or uploaded as files), view rules and Insights |

Roles are enforced in the backend (every endpoint checks the role) and in the database for sources. The UI hides forbidden actions but is never the only guard.

**Accounts:** judges can use the one-click demo accounts or **sign up** with their own email, name, password and chosen role. Sign-up creates a confirmed account straight away (no email step) in the shared GlowLeaf Naturals demo workspace, so brand sources and history are already there.

## 4. How a piece of content flows through the system

```
Creator submits ──► Review runs ──► Creator decides on each finding ──► Save new version
                     (Layer A + B)                                           │
                                                                     (re-checked automatically)
                                                                             ▼
        Reviewer ◄── Escalate ── Manager ◄── Submit for review ◄── status "Checked"
           │              │          │
        Approve /      Request    Approve
        Reject         changes
```

**Statuses:** Draft → Checked → In review → (Changes requested | Escalated | Approved) → (Approved | Rejected). A rejected or changes-requested item goes back to Checked when the creator saves a new version. Illegal moves (for example a creator approving their own content) are refused with a clear message.

### Step by step

1. **Submit.** The creator picks a channel, optionally declares that AI was used, and pastes text or uploads a file (up to 10 MB). Supported: PDF (scanned PDFs are read with OCR), Word .docx, images (PNG, JPG, WEBP, GIF, BMP, TIFF; read with Tesseract OCR), TXT/Markdown and HTML. Unsupported or damaged files get a clear message. The file goes to a private storage bucket and version 1 is created.
2. **Review.** Two layers run (section 5). Progress streams to the screen: "Rule checks done, AI checks running...".
3. **Findings appear.** The original text is highlighted by severity. Each highlight links to a card on the right. Clicking a source chip (for example `FACT-001`) shows the approved excerpt it came from.
4. **Decide.** For each card the creator chooses **Accept** (apply the suggested replacement), **Edit** (type their own wording) or **Reject** (with a short reason).
5. **Save as new version.** A new version is built *only* from accepted replacements and edited text, then automatically re-checked. A diff view shows exactly what changed.
6. **Submit for review.** The status becomes "In review". The manager comments and approves, requests changes or escalates; the reviewer approves (with an override reason if high-severity issues remain) or rejects.
7. **Audit.** Every step is recorded with who, which role, when, and the reason.

## 5. The review engine: two layers plus a merger

### Layer A: deterministic rules (no AI)

Fast, free, exact and explainable. Rules live in YAML files (`backend/rules/`) and always produce high-confidence findings with exact character spans.

| Check | Method |
|---|---|
| Absolute claims ("100% natural", "guaranteed") | Regex |
| Superiority claims ("India's #1") | Regex |
| Medical or cure claims ("cures", "heals") | Regex plus the Drugs and Magic Remedies reference |
| Banned vs preferred terms ("chemical-free" becomes "made without parabens and sulfates") | Exact plus fuzzy matching (rapidfuzz, threshold 88), catches typos like "chemcial-free" |
| Contradictory disclaimer (a headline claim undercut by a footnote) | Structural check across the headline and the footnote |
| Missing influencer disclosure (#Ad, #Sponsored, #Collab) | Channel-aware check of the first visible lines |
| Missing AI or synthetic-persona label | Checks the creator's AI declaration plus persona keywords |
| Low text contrast on images | Tesseract finds word boxes; Pillow takes two dominant colours per box; the WCAG ratio is computed (4.5:1, or 3:1 for large text); failures are reported as image regions |
| Missing alt-text | Image alt field, HTML `<img>` tags, DOCX pictures |

### Layer B: grounded AI review

Handles what rules cannot: comparing claims with approved facts, and judging tone against the brand voice.

1. **Retrieval.** The system picks which approved sources the AI may see: vector search (pgvector, Gemini embeddings, 768 dimensions) over the organisation's fact chunks, always plus the voice guideline. If embeddings are unavailable or return nothing, it falls back to keyword matching, so retrieval never blocks.
2. **Prompt.** The model receives only those sources and the content, wrapped in `<content>` tags and told it is untrusted data (a prompt-injection defence).
3. **Strict output.** The model must return JSON, validated by pydantic.
4. **Grounding rule (the trust feature).** The model may only cite sources it was given. Any citation to a source that was not retrieved, or that does not exist, is rejected and the finding is downgraded to **Unsupported claim** with low confidence. A span that cannot be located in the text is dropped. This is covered by automated tests, including a fabricated source ID.
5. **Reliability.** 20-second timeout, a retry, then a second Gemini model if the first is overloaded, then an offline heuristic that produces the same output shape and goes through the same checks. When that happens the screen shows "AI layer unavailable" and nothing is sent to an AI provider.

### Findings merger

- Overlapping findings (span overlap of 50% or more) merge into one card with the citations combined, for example a rule hit on "100% natural" plus the AI's fact contradiction citing `FACT-001`.
- Severity is the highest of the merged findings, and any finding citing a regulatory source is forced to high.
- Confidence: **High** = rule-based, **Medium** = AI with a validated source, **Low** = AI with no source (Unsupported claim).
- Order: high severity first, then position in the text.

## 6. Data and security

**Stack:** Next.js (App Router, TypeScript, Tailwind, Recharts, react-diff-viewer) on Vercel · FastAPI and pydantic on Render (Docker, with Tesseract installed) · Supabase (Postgres, Auth, private Storage, pgvector) · Gemini for review and embeddings behind a provider adapter (Anthropic and OpenAI adapters also exist).

**Main tables:** organisations, profiles (role and org), sources and source_chunks (brand material and embeddings), content_items, content_versions, review_runs, findings, comments, approvals, audit_log.

**Security model:**
- Every table carries `org_id`. The API takes the organisation from the signed-in user's profile and never trusts one sent by the client.
- Row-level security is enabled on every table. Storage buckets are private and scoped by organisation folder.
- `audit_log` is append-only, enforced by a database trigger that rejects updates and deletes (verified live).
- The Supabase service key and the AI key exist only on the backend. The frontend has only the public anon key.
- Errors shown to users are friendly messages with a next step, never raw stack traces.

**Offline demo mode:** with no Supabase credentials, the API uses a seeded in-memory store, so the whole product runs locally with zero setup. Production uses the real database.

## 7. Insights

Computed from the findings of each version's latest review run, over the last 30 days:

- **Most violated rules** (bar chart) and **findings by category**.
- **Violations over time** (line chart).
- **Most overridden rules:** the share of decided findings that creators rejected, per rule.
- **Guidelines that may be unclear:** a rule is flagged when at least 40% of its decisions are rejections (with at least 3 decisions), or at least 30% of its findings are low confidence. The panel suggests: "Creators frequently disagree with this rule. Consider clarifying the wording or adding examples," and links to the Brand page.

The demo database holds 25 seeded historical items and about 80 findings so this page is never empty. For example, `RULE-TONE-HYPE` is rejected about 60% of the time and shows as unclear.

## 8. The demo experience

The login page has one-click buttons for each role, a "Try it in 2 minutes" box, and a shared demo password. Content creation has **Load sample** buttons:

1. **Instagram post** with planted issues: absolute claims, banned terms, cure claim, "India's #1", a contradictory footnote, a figure that conflicts with the approved 92%.
2. **Influencer post** with no #Ad and an AI-generated persona.
3. **Poster image** with low-contrast text and no alt-text.
4. **Clean post** that passes, so an approval path is visible too.

A role switcher in the top bar changes role in one click. The dashboard shows a guided checklist per role with the next best action, and empty screens always say what to do next.

## 9. Testing and verification

- **38 automated tests, all offline:** Layer A on every sample, grounding (a fabricated source is rejected), the merger, every legal and illegal workflow transition, the full creator-manager-reviewer flow with the audit trail, role and organisation isolation, and the insights output.
- **Verified live** on Vercel, Render and Supabase: real login, a live Gemini review, decisions, version diff, the escalation and override-approval chain, the audit trail, and all three Insights charts.
- Bugs found only in deployment and fixed: a double-slash API URL, a review stream held open by Render's proxy, a health-check path typo, Gemini 503 overload handling, a retired embedding model, and a SQL function parameter clash.

## 10. Known limitations

- Rule-based and AI checks flag risk; they are **not legal advice**, and the regulatory summaries are paraphrases that should be verified against the official sources linked in each.
- Which findings Gemini raises can vary run to run. The deterministic layer does not.
- The free Render tier sleeps after about 15 minutes idle, so the first request can take up to a minute. Live reviews take roughly 20 seconds.
- Row-level security and storage policies were not exercised directly, because the API uses the service role and enforces roles and organisations in code.
- Skipped as lower priority: logo and palette checks, messaging-similarity scoring, an admin rule-editor screen (rules are YAML with a read-only viewer), and email notifications.
- Still to do: a stranger test with a real first-time user, the backup demo video, and confirming the repository is public.

## 11. Where things are

| Need | File |
|---|---|
| How to run and try it | `README.md` |
| System design, diagrams, decisions | `ARCHITECTURE.md` |
| Every AI model, service, dataset and library | `AI_AND_SERVICES.md` |
| Gate-by-gate status and limitations | `CHECKLIST.md` |
| Backend engine | `backend/app/engine/` (layer A, layer B, merger, retrieval, pipeline) |
| Rules | `backend/rules/*.yaml` |
| Workflow rules | `backend/app/workflow/state_machine.py` |
| Database migrations and seed | `seed/migrations/`, `seed/seed_demo.py` |

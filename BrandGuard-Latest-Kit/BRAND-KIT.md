# BrandGuard — latest Silver design and behavior kit

## Authority and scope
Apply to the existing local BrandGuard repository, preserving its framework, backend, authentication, APIs, database, data, tenancy, permissions and workflows. Inspect repo instructions and architecture first. Refactor shared tokens/components; do not transplant the demo’s accumulated CSS/JS overrides.

`reference.html` is the latest approved frontend including animated waves, rounded sliding tabs, workspace dropdown and admin-password signup. Open it in a browser for appearance; do not paste its base64 or full bundled code into model context. Use `assets/silver-waves.jpg` exactly for the artwork. `assets/wave-renderer-reference.js` is a bounded GPU wave-motion reference, to adapt with proper lifecycle cleanup. Demo persistence and auth handoffs are not production implementation patterns.

Latest user requirements override older audit/kit statements: **waves animate; signup offers four roles; only Creator does not require an admin password.** Previous Creator-only signup and static-background instructions are obsolete.

## Identity
BrandGuard: pre-publication brand governance. Tagline: **AI suggests. Humans decide.** Hero: **Every word. Every claim. Considered.** Plain, precise, calm, evidence-led language. No guaranteed compliance/legal approval claims. Retain established production logo; no ® unless verified.

## Exact visual direction
Keep the approved Silver appearance: sculptural silver sphere/contour-wave artwork, near-black/graphite surfaces, paper-white sections, fine borders, editorial type, generous space and restrained shadows. No emerald rebrand, neon, spinning cubes/sheets or tilted dashboard mockups.

```css
:root {
 --paper:#e8e9e3; --paper-raised:#f0f1eb; --paper-shade:#dce1d5;
 --ink:#151618; --graphite:#17191c; --recessed:#15191a;
 --panel:#171c1d; --panel-raised:#282d2e;
 --text-dark:#eceee6; --muted-dark:#a6aea1; --muted-light:#62695e;
 --silver:#ced3d6; --silver-mid:#8d9295; --silver-dark:#62676b;
 --border-light:rgba(21,22,24,.14); --border-dark:rgba(255,255,255,.13);
 --surface-light:linear-gradient(120deg,#f0f1eb,#dce1d5);
 --surface-dark:linear-gradient(125deg,#282d2e,#171c1d);
 --ease:cubic-bezier(.16,1,.3,1);
 --ease-slide:cubic-bezier(.22,1,.36,1);
}
```
Semantic success/warning/error/info remain distinguishable with labels/icons and sufficient contrast. Never use decorative muted shades for unreadable functional copy.

Typography: Inter 400–600 for UI and headings; Georgia italic for occasional large marketing emphasis only. Desktop/mobile px: hero 72–106/48–58; section 44–67/34–42; app title 32–40/28–32; panel title 16–22; body/forms 14–16; labels 12–13. Tight large-heading tracking (~-.04em), body line-height 1.6–1.8. Preserve readability instead of copying tiny decorative labels.

8px spacing system. Marketing max-width 1280–1440px; app 1440–1600px. Sections 80–110px vertical/7–9% horizontal; mobile 48–64px/6–7%. Sidebar 224–248px, header 72–86px. App gaps 16–24px, panel radius 10–14px, inputs 6–8px. Marketing buttons pill-shaped; app controls compact rounded. Match reference responsive composition.

## Artwork and motion
Use the exact JPEG, cover; desktop crop around center 42%, mobile around 61% 40%. Keep sphere/right ridge visible and copy legible over dark lower-left overlays. Reuse artwork in dark standards/final CTA/authentication. Preserve subtle wave distortion, not a visibly sliding/duplicated background sheet. Adapt provided renderer; avoid double-running CSS fallback and GPU effects. Bound resolution/mobile frame rate; pause when offscreen/document hidden; clean up GPU/listeners on unmount. Fallback gracefully when WebGL fails. Respect reduced motion with a static image.

Hero: three manually controlled slides, stable arrows/dots/counter, swipe and keyboard arrows, inactive content inert. Titles: Every word…Considered; Clarity in every layer; Intelligence. Human judgment. No autoplay.

Standards tabs **Rules / Intelligence / People**: rounded outer pill bar, generous inner breathing room (13px desktop, 10px mobile), selected capsule never touches border. One selection indicator glides left/right ~550ms; content enters from the corresponding side ~600ms using --ease-slide. Handle rapid taps, resize, arrows/Home/End and cleanup. Keep colors/text unchanged.

Other motion: hover 150–200ms; press 100–150ms; contained ripple 450–650ms; slide crossfade 500–650ms; page/tab opacity + small translation 250–450ms; reveals 500–800ms/stagger 50–80ms; FAQ expansion 200–300ms. Native smooth scrolling; no hijacking/layout shifts. Reduced-motion fallback removes nonessential movement.

## Landing and navigation
Retain artwork hero → paper principles/process → dark standards tabs → paper insights → FAQ → artwork CTA/footer. Include live product content:
- Heading/message: Catch brand and compliance risks before you publish; explain approved guidelines/facts/advertising rules, explained findings/fixes and human approval.
- Logged-out **Try the live demo → real login route**, **Create an account → signup**; logged-in **Go to your dashboard**. No-setup/pick-demo-role/fictional-brand explanation.
- Process **Submit / Check / Decide / Approve**; trust **Grounded, never guessing / People stay in charge / Every step on record**.
- Real service-check loading/status/latency, Recheck, About AI link. Do not display a false online state.
- Persistent accurate AI disclosure: human approval, no automatic edits/publication, configured providers, legal caveat.
- Signed-in Dashboard/Reviews/Brand/Insights/About AI; Creator New content; role-appropriate demo switch only where supported; real Sign out.

## Authentication — latest required behavior
Restyle the actual auth routes; do not redirect users out to the old deployment as the local demo does. Reuse real provider/session/recovery/registration flows.
- Login: email/password, visibility control, Sign in, **Continue with Google**, supported four-role demo buttons, loading states, two-minute walkthrough.
- Signup: name, email, account password with 10-character guidance; shared GlowLeaf demo-workspace disclosure and confidential-material/non-reused-password warnings where applicable. **Create account**, **Sign up with Google**, sign-in/demo links.
- Role choices: **Creator** (default), **Brand Manager**, **Authorised Reviewer**, **Admin**, with workflow descriptions.
- Creator: no admin password. Other three: reveal **Admin password**, required, with: “This role can approve content or change the brand sources, so it needs the password your admin set up.”
- Switching to Creator hides/disables/clears admin input. Add accessible visibility control; do not retain credentials across navigation.
- **Elevated-role authorization must be validated server-side before any account/role is granted**, including OAuth paths. Never embed an admin secret/hash in the client, accept any nonempty string as authorization, or store/log passwords. Reuse existing backend policy; if absent, implement a secure server-side verification path using server-only configuration. Do not weaken existing auth or grant privileges solely from a posted role. Report missing required configuration without exposing it.
- Google UI can initialize asynchronously; wait before declaring it absent. Preserve real OAuth state/errors/cancellation. Do not infer privilege from a Google email or use the UI field as the authorization boundary.

## Workspace dropdown
Preserve the dark workspace selector: initials, full name/Brand workspace subtitle, chevron. Rounded popover: selected workspace/check, divider, **Other workspaces**, named options, **Add workspace** form (name/description). Keyboard navigation, Escape/outside dismissal, focus restoration, smooth reveal, mobile fit. In production load authorized organisations and switch actual org scope with backend tenancy enforced; no cross-org data leakage or fabricated membership. Demo’s browser-local names do not create backend organisations.

## Role workflows and data
Backend permissions authoritative; preserve separate role queues/actions.
- Creator: guided checklist, own status counts/recent items, New content, **Your content** queue, `/content/:id`.
- Manager: **Waiting for your review**; in-review content; `/reviews/:id`; **Approve / Request changes / Escalate**.
- Reviewer: **Escalated to you**; `/reviews/:id`; **Approve / Reject**; written reasons for overrides/rejection.
- Admin: source management/Insights; **In review or escalated** queue. Recent-content links observed as `/content/:id`. Do not invent approval permission.
- Statuses: Draft, Checked, In review, Escalated, Approved, Changes requested, Rejected. Preserve scope, authors, channels, findings and unresolved counts. Treat loading separately from empty/zero.
- New content: exact four sample labels (Lip balm launch post; Influencer morning routine; Summer sale poster; Delivery announcement); title/channel/AI checkbox/text. Channels Instagram post/Website page/Influencer post/Press release/Email. Upload PDF incl scans/DOCX/PNG/JPG/WEBP/GIF/TXT/HTML up to 10MB. Poster is an image file with **Alt-text (describe the image)**. Preserve sample channel/AI settings, actual extraction/progress/errors; do not substitute keyword checks for AI.
- Findings: highlighted spans/insertion points → card; issue, explanation, separate severity/confidence/layer/category, real citations, unsupported badge/no-source state, fix, decision.
- Ready replacement: **Accept fix / Edit / Reject**. No replacement: **Acknowledge / Edit / Reject** with explanatory helper. Acknowledging does not apply wording or pretend risk is resolved. Inline Edit prefilled with actual highlighted span; **Save my edit**. **Save as new version** gated on accepted/edited changes; accepted/edited and high-severity-open counts. Preserve rerun/submit permissions, versions/comparisons, comments and dated actor/role audit.
- Brand tabs: Guidelines/Approved facts/Terminology/Regulatory rules/Assets/Rule library; expandable sources; Admin category-specific add form, title/citation-code/text/upload. Keep actual reviewed-brand source facts/palette; do not replace GlowLeaf guidelines with platform Silver tokens.
- Insights: real Last-30-days metrics, unclear-guideline links, most violated rules, category bars, daily trend and overridden-rule decision table. Latest audit snapshot **109 findings / 32 items / 3 of 9 override approvals / 33%**; never hardcode these as live totals. New examples include checked Delivery announcement (1 finding) and Lip balm launch post (engine check, 9 findings). Decision-table counts are not violation counts.
- About AI/disclosures must match deployment behavior; do not turn unverified app statements into security guarantees.

## Acceptance
Theme/artwork and approved motion remain visually unchanged. Signup has all four roles, correct conditional admin input and backend enforcement; Google flows work. Role permissions/tenancy remain secure. Real data/processing replace demo simulations. Include loading/empty/error/success/disabled states. WCAG AA, readable type, ~44px targets, semantic controls, visible focus, keyboard/dialog management, accessible chart summaries. Verify desktop/mobile/reduced-motion, rapid tab changes, workspace switching, auth success/failure and existing workflow tests/build. Never claim browser/security verification not performed. Deliver concise changes, checks and remaining limitations. Do not deploy unless separately requested.

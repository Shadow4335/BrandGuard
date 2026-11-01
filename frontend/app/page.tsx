"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, ArrowUpRight } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { SilverWaves } from "@/components/SilverWaves";
import { SlidingTabs } from "@/components/SlidingTabs";
import { BrandLogo } from "@/components/AppShell";

const SLIDES = [
  { kicker: "Considered content. Confident brands.", lines: ["Every word.", "Every claim."], italic: "Considered.", body: "Catch brand and compliance risks before you publish." },
  { kicker: "Rules. Context. Perspective.", lines: ["Clarity in", "every layer."], italic: "By design.", body: "Approved guidelines, facts and advertising rules. Findings explained, with sources and suggested fixes." },
  { kicker: "People own the decision.", lines: ["Intelligence."], italic: "Human judgment.", body: "Evidence where it matters. Human review before every approval." },
];
const STANDARDS = [
  { id: "rules", label: "01  Rules", detail: "Deterministic checks", eyebrow: "Layer A / deterministic", title: "Precision in the details.", body: "Flag absolute promises, prohibited terms, missing disclosures, and accessibility issues against configured rules.", rule: "RULE-ABS-001", issue: "Absolute or guaranteed claim", example: "“100% natural” needs complete substantiation. Approved fact: 92% naturally derived ingredients. FACT-001." },
  { id: "intelligence", label: "02  Intelligence", detail: "Grounded AI", eyebrow: "Layer B / context", title: "Context behind every claim.", body: "Find relevant approved evidence, assess tone and check claims. A claim without an approved source is labelled unsupported.", rule: "RULE-CLAIM-UNSUPPORTED", issue: "Evidence before confidence", example: "Source-grounded AI checks quote the submitted text and cite only retrieved approved sources. Offline checks remain available when AI is unavailable." },
  { id: "people", label: "03  People", detail: "Human decisions", eyebrow: "Your team / final judgment", title: "People make the final call.", body: "Creators accept, edit or reject suggestions. Managers review and escalate. Authorised reviewers explain override decisions.", rule: "HUMAN APPROVAL", issue: "A considered decision. On record.", example: "Versions, comments, approval reasons and an audit trail preserve the context behind each decision. Nothing is automatically edited or published." },
];
export default function HomePage() {
  const { user } = useAuth();
  const [slide, setSlide] = useState(0), [direction, setDirection] = useState(1), [standard, setStandard] = useState("rules");
  const [service, setService] = useState<{ state: "loading" | "ok" | "error"; latency?: number; demo?: boolean }>({ state: "loading" });
  const touch = useRef<number | null>(null);
  useEffect(() => { let active = true; const start = performance.now(); api.health().then((h) => { if (active) setService({ state: "ok", latency: Math.round(performance.now() - start), demo: h.demo_mode }); }).catch(() => { if (active) setService({ state: "error" }); }); return () => { active = false; }; }, []);
  async function recheck() {
    setService({ state: "loading" }); const start = performance.now();
    try { const h = await api.health(); setService({ state: "ok", latency: Math.round(performance.now() - start), demo: h.demo_mode }); } catch { setService({ state: "error" }); }
  }
  function change(next: number, dir: number) { setDirection(dir); setSlide((next + SLIDES.length) % SLIDES.length); }
  const current = SLIDES[slide], tab = STANDARDS.find((s) => s.id === standard)!;
  const destination = user ? "/dashboard" : "/signup";
  return <>
    <SilverWaves className="hero">
      <div className="hero-meta"><span>Pre-publication brand governance</span><span>Rules · Context · Judgment</span></div>
      <section aria-label={`Introduction slide ${slide + 1} of 3`} aria-roledescription="carousel" tabIndex={0} onKeyDown={(e) => {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); const d = e.key === "ArrowRight" ? 1 : -1; change(slide + d, d); }
      }} onTouchStart={(e) => { touch.current = e.touches[0].clientX; }} onTouchEnd={(e) => { if (touch.current !== null) { const dx = e.changedTouches[0].clientX - touch.current; if (Math.abs(dx) > 50) change(slide + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1); touch.current = null; } }}>
        <div className="hero-content" key={slide} style={{ "--slide-from": `${direction * 28}px` } as React.CSSProperties}>
          <p className="eyebrow">{current.kicker}</p>
          <h1>{current.lines.map((l) => <span key={l}>{l}</span>)}<em>{current.italic}</em></h1>
          <p>{current.body}</p><p>AI suggests. Humans decide.</p>
          <div className="hero-actions"><Link href={destination}>{user ? "Go to your dashboard" : "Create an account"} ↗</Link><Link className="pill-button" href={user ? "/dashboard" : "/login"}>{user ? "Open your workspace" : "Try the live demo"}<ArrowUpRight size={15} /></Link><a href="#process">Discover the approach ↓</a></div>
        </div>
      </section>
      <div className="hero-controls"><button aria-label="Previous slide" onClick={() => change(slide - 1, -1)}><ArrowLeft size={16} /></button><span aria-live="polite">0{slide + 1} / 03</span><button aria-label="Next slide" onClick={() => change(slide + 1, 1)}><ArrowRight size={16} /></button><div className="hero-dots" aria-label="Choose introduction slide">{SLIDES.map((_, i) => <button key={i} aria-label={`Go to slide ${i + 1}`} aria-pressed={slide === i} onClick={() => change(i, i >= slide ? 1 : -1)} />)}</div><p>AI suggests. Humans decide.</p></div>
    </SilverWaves>
    <section className="marketing-section" aria-labelledby="trust-title"><p className="eyebrow">Why teams trust it</p><h2 id="trust-title">Grounded.<em>Human. On record.</em></h2><p>{service.demo ? "No setup needed: pick a demo role on the sign-in screen. The demo brand is GlowLeaf Naturals, a fictional personal-care company." : "A shared view of your brand’s guidelines, evidence and review decisions. Sign in to your workspace to begin."}</p><div className="marketing-grid">{[
      ["Grounded, never guessing", "The AI may only cite your approved sources. If nothing supports a claim, it says so."], ["People stay in charge", "Suggestions are never auto-applied and nothing is auto-published."], ["Every step on record", "An audit trail shows who decided what, when, and why."],
    ].map(([title, body], i) => <article key={title}><span className="process-number">0{i + 1} ↗</span><h3>{title}</h3><p>{body}</p></article>)}</div><div className="service-status"><span role="status">{service.state === "loading" ? "Checking the service. The server may take a minute to wake." : service.state === "ok" ? `API responded · ${service.latency} ms` : "The service could not be reached. Please retry."}</span><button onClick={recheck} disabled={service.state === "loading"}>Recheck</button><Link href="/about-ai">How the AI is used ↗</Link></div></section>
    <section id="process" className="marketing-section process-section"><p className="eyebrow">01 / The approach</p><h2>How it works.<em>Human by design.</em></h2><p>From the first draft to the final decision, keep your brand’s intent in view.</p><div className="marketing-grid four">{[
      ["Submit", "Paste text or upload a PDF, Word file or image, then pick the channel."], ["Check", "Review configured rule checks and grounded AI findings, with source references."], ["Decide", "Accept, edit, or reject suggestions. Save only the changes you choose."], ["Approve", "A manager approves or escalates to a reviewer, and every step is recorded."],
    ].map(([title, body], i) => <article key={title}><span className="process-number">0{i + 1} ↗</span><h3>{title}</h3><p>{body}</p></article>)}</div></section>
    <SilverWaves className="standards-section"><section id="standards"><p className="eyebrow">02 / One source of truth</p><h2>Standards.<br /><em>With substance.</em></h2><SlidingTabs tabs={STANDARDS} value={standard} onChange={setStandard} label="Brand standard layers"><div className="standard-content"><div><p className="eyebrow">{tab.eyebrow}</p><h3>{tab.title}</h3><p>{tab.body}</p><Link href={user ? "/brand" : "/login"}>Explore the brand library ↗</Link></div><div className="standard-card"><code>{tab.rule}</code><strong>{tab.issue}</strong><p>{tab.example}</p><small>Illustrative review preview · Live checks in your workspace</small></div></div></SlidingTabs></section></SilverWaves>
    <section id="insights" className="marketing-section insights-teaser"><p className="eyebrow">03 / A clearer perspective</p><h2>The bigger<em>brand picture.</em></h2><p>See patterns. Understand disagreements. Improve the guidance behind your next review.</p><div className="marketing-grid">{[["Recurring findings", "Understand which rules and categories need the most attention."], ["Guidelines that may be unclear", "See when creators disagree with a rule and where more examples could help."], ["Human decisions", "Track review activity and approval overrides from real workspace records."]].map(([title, body]) => <article key={title}><h3>{title}</h3><p>{body}</p></article>)}</div><Link href={user ? "/insights" : "/login"} className="pill-button dark" style={{ marginTop: 40 }}>Explore insights <ArrowUpRight size={16} /></Link></section>
    <section className="marketing-section"><p className="eyebrow">04 / A little more clarity</p><h2>Good questions.<em>Clear answers.</em></h2><div className="faq-list">{[
      ["Does BrandGuard publish my content?", "No. BrandGuard reviews submitted content and records decisions. You decide what changes to make; publication stays with your team."], ["What do the two review layers do?", "Layer A runs configured deterministic checks. Layer B checks claims and tone against retrieved approved sources, with offline checks when the AI service is unavailable."], ["Who makes the final call?", "Creators decide on suggestions, managers review submissions, and authorised reviewers decide escalated items. Approving unresolved high-severity findings at the reviewer stage requires a written override reason."], ["Can I use my real BrandGuard account?", "Yes. Use Sign in, or create an account here. Elevated roles require server-verified admin authorization."], ["Does a review provide legal approval?", "No. Findings flag potential risk and provide context. They are not legal advice or a guarantee of compliance."],
    ].map(([q, a]) => <details key={q}><summary>{q}</summary><p>{a}</p></details>)}</div></section>
    <SilverWaves className="cta"><p className="eyebrow">Your next idea deserves a clearer review.</p><h2>Your brand.<br /><em>In good hands.</em></h2><Link className="pill-button" href={destination}>{user ? "Go to your dashboard" : "Create an account"}<ArrowUpRight size={16} /></Link></SilverWaves>
    <footer className="marketing-footer"><Link href="/" aria-label="BrandGuard home"><BrandLogo /></Link><span>AI suggests. Humans decide.</span><Link href="/about-ai">About AI ↗</Link></footer>
  </>;
}

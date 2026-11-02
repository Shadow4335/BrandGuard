"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ArrowUpRight, AlertCircle, ChevronDown } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { GoogleSignIn } from "@/components/GoogleSignIn";
import { PasswordInput } from "@/components/PasswordInput";
import { api } from "@/lib/api";
import type { UserRole } from "@/lib/types";

const DEMO_ACCOUNTS: { role: UserRole; label: string; desc: string }[] = [
  { role: "creator", label: "Creator", desc: "Draft content, run checks and decide on suggestions." },
  { role: "manager", label: "Brand Manager", desc: "Review submissions, request changes or escalate." },
  { role: "reviewer", label: "Authorised Reviewer", desc: "Decide escalated content, with reasons on record." },
  { role: "admin", label: "Admin", desc: "Manage approved brand sources and view insights." },
];

export default function LoginPage() {
  const router = useRouter();
  const { signIn, signInDemo, error } = useAuth();
  const [demoMode, setDemoMode] = useState<boolean | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<UserRole | null>(null);

  useEffect(() => {
    let active = true;
    api.health().then((h) => { if (active) setDemoMode(h.demo_mode === true); }).catch(() => { if (active) setDemoMode(false); });
    return () => { active = false; };
  }, []);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); setLoading(true);
    try { if (await signIn(email, password)) router.push("/dashboard"); }
    finally { setPassword(""); setLoading(false); }
  }

  async function demo(role: UserRole) {
    setLoading(true); setPending(role);
    try { if (await signInDemo(role)) router.push("/dashboard"); }
    finally { setLoading(false); setPending(null); }
  }

  return <div className="login-page">
    <div className="login-primary">
    <header className="login-heading">
      <p className="eyebrow">A considered perspective</p>
      <h1>Sign in to BrandGuard</h1>
      <p>Your brand’s guidelines, evidence and decisions.<br />All in one workspace.</p>
    </header>

    <form onSubmit={submit} className="login-form" aria-label="Sign in" aria-busy={loading}>
      {error && <div role="alert" className="login-error"><AlertCircle size={18} /><span>{error}</span></div>}
      <label htmlFor="login-email">Email address</label>
      <input id="login-email" name="email" type="email" autoComplete="username" required disabled={loading} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" />
      <label htmlFor="login-password">Password</label>
      <PasswordInput id="login-password" name="password" autoComplete="current-password" required disabled={loading} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" />
      <button type="submit" disabled={loading} className="login-submit"><span>{loading && !pending ? "Signing in…" : "Sign in"}</span><ArrowRight size={18} /></button>
      <div className="login-divider"><span>or</span></div>
      <div className="login-provider"><GoogleSignIn disabled={loading} /></div>
      <p className="login-create">New to BrandGuard? <Link href="/signup">Create an account <ArrowUpRight size={13} /></Link></p>
      {demoMode && <p className="login-create login-demo-link"><a href="#demo-title">Just exploring? Try a demo role ↓</a></p>}
    </form>
    </div>

    {demoMode === null && <p role="status" className="login-demo-loading">Checking demo availability…</p>}
    {demoMode && <>
      <section className="login-demo" aria-labelledby="demo-title">
        <div className="login-demo-heading"><span className="eyebrow">Explore the workspace</span><span className="login-demo-badge">Live demo</span></div>
        <h2 id="demo-title">Four roles. One considered process.</h2>
        <p>No setup needed. Choose a role to try the real review workflow.</p>
        <div className="login-role-grid">{DEMO_ACCOUNTS.map((acc, i) => <button key={acc.role} type="button" onClick={() => demo(acc.role)} disabled={loading} aria-busy={pending === acc.role} className="login-role">
          <span className="login-role-top"><span className="login-role-number">0{i + 1}</span><ArrowUpRight size={17} /></span>
          <strong>{acc.label}</strong><span>{pending === acc.role ? "Signing in…" : acc.desc}</span>
        </button>)}</div>
        <p className="login-demo-note">Shared GlowLeaf Naturals workspace · Fictional brand.<br />Don’t upload confidential material.</p>
      </section>
      <details className="login-walkthrough">
        <summary><span><span className="eyebrow">Your first review</span><strong>Try it in 2 minutes</strong></span><ChevronDown size={18} /></summary>
        <ol>
          <li><strong>Submit.</strong> As Creator, open New content and load the Lip balm launch sample.</li>
          <li><strong>Check.</strong> Run the review and read the findings and their sources.</li>
          <li><strong>Decide.</strong> Accept, edit or reject suggestions, save a new version, then submit for review.</li>
          <li><strong>Approve.</strong> As Brand Manager, comment and escalate. As Authorised Reviewer, approve with a written override reason where required.</li>
        </ol>
        <p>Open Insights as Admin to explore recurring findings and unclear guidelines.</p>
      </details>
    </>}
    <p className="login-signature">AI suggests. Humans decide.</p>
  </div>;
}

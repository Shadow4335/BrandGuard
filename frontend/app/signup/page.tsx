"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, ArrowRight, ArrowUpRight } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { GoogleSignIn } from "@/components/GoogleSignIn";
import { api } from "@/lib/api";
import { PasswordInput } from "@/components/PasswordInput";
import type { UserRole } from "@/lib/types";

const ROLES: { value: UserRole; label: string; desc: string }[] = [
  { value: "creator", label: "Creator", desc: "Upload content, run the AI review, fix issues, submit for approval" },
  { value: "manager", label: "Brand Manager", desc: "Review submitted content: approve, request changes or escalate" },
  { value: "reviewer", label: "Authorised Reviewer", desc: "Decide escalated items; overrides need a written reason" },
  { value: "admin", label: "Admin", desc: "Manage brand sources and view Insights" },
];

export default function SignupPage() {
  const router = useRouter();
  const { signUp, error } = useAuth();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "creator" as UserRole, invite_code: "", role_password: "" });
  const [busy, setBusy] = useState(false);
  const [local, setLocal] = useState<string | null>(null);
  const [passwordRoles, setPasswordRoles] = useState<UserRole[]>([]);
  const [mode, setMode] = useState<"open" | "invite" | "closed" | "loading">("loading");
  const [healthError, setHealthError] = useState(false);
  useEffect(() => {
    api.health().then((h) => {
      setPasswordRoles(h.password_roles ?? []);
      if (h.signup) setMode(h.signup);
    }).catch(() => setHealthError(true));
  }, []);
  const needsRolePassword = form.role !== "creator";
  const roleChoices = ROLES;
  const configured = !needsRolePassword || passwordRoles.includes(form.role);
  const MIN = 10;
  const left = Math.max(0, MIN - form.password.length);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password.length < MIN) { setLocal(`Use a password with at least ${MIN} characters.`); return; }
    setLocal(null); setBusy(true);
    const ok = await signUp({
      ...form,
      invite_code: form.invite_code.trim() || undefined,
      role_password: needsRolePassword ? form.role_password : undefined,
    });
    setForm((f) => ({ ...f, password: "", role_password: "" }));
    setBusy(false);
    if (ok) router.push("/dashboard");
  }

  return (
    <div className="login-page">
      <div className="login-primary">
      <header className="login-heading">
        <p className="eyebrow">A considered perspective</p>
        <h1>Create your account</h1>
        <p>New accounts join the shared <strong>GlowLeaf Naturals</strong> demo workspace, a fictional brand with guidelines, approved facts and sample history already set up.</p>
      </header>
      <form onSubmit={submit} className="login-form signup-form" aria-label="Create your account" aria-busy={busy}>
        {(local || error) && <div role="alert" className="login-error"><AlertCircle size={18} /><span>{local || error}</span></div>}
        {mode === "loading" && <p role="status" className="auth-notice">{healthError ? "Cannot reach the server. Reload to check signup availability." : "Checking signup availability…"}</p>}
        {mode === "closed" && (
          <p role="status" className="auth-notice">
            Sign-up is closed on this server. Ask an admin to create your account, or <Link href="/login" className="underline">sign in</Link>.
          </p>
        )}
        <label className="signup-field">Your name
          <input required autoComplete="name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        </label>
        <label className="signup-field">Email
          <input required type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@company.com" />
        </label>
        <label className="signup-field">Password
          <PasswordInput required minLength={MIN} maxLength={128} autoComplete="new-password" aria-describedby="pw-help" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <span id="pw-help" className="signup-help">
            {left > 0 ? `${left} more character${left === 1 ? "" : "s"} needed. ` : "Long enough. "}A few unrelated words works well. Avoid common passwords, your name or email, and the product name.
          </span>
        </label>
        {mode === "invite" && (
          <label className="signup-field">Invite code
            <input required autoComplete="off" value={form.invite_code} onChange={(e) => setForm({ ...form, invite_code: e.target.value })} />
          </label>
        )}
        <fieldset className="signup-roles">
          <legend>Your role</legend>
          {roleChoices.map((r) => (
            <label key={r.value} className="signup-role">
              <input type="radio" name="role" value={r.value} checked={form.role === r.value} onChange={() => { setForm({ ...form, role: r.value, role_password: "" }); setLocal(null); }} />
              <span><strong>{r.label}</strong>{r.value !== "creator" && <small> (admin password)</small>}<br /><span className="signup-help">{r.desc}</span></span>
            </label>
          ))}
          {needsRolePassword && (
            <label className="signup-field signup-admin-password">Admin password
              <PasswordInput label="admin password" required autoComplete="off" value={form.role_password} onChange={(e) => setForm({ ...form, role_password: e.target.value })} aria-describedby="role-pw-help" />
              <span id="role-pw-help" className="signup-help">This role can approve content or change the brand sources, so it needs the password your admin set up.</span>
            </label>
          )}
        </fieldset>
        {needsRolePassword && !configured && mode !== "loading" && <p role="status" className="auth-notice">Admin authorization is not configured on this server. Ask your admin to enable elevated-role registration, or choose Creator.</p>}
        <button type="submit" disabled={busy || mode === "closed" || mode === "loading" || !configured} className="login-submit">
          <span>{busy ? "Creating your account…" : "Create account"}</span><ArrowRight size={18} />
        </button>
        {mode !== "closed" && mode !== "loading" && <>
          <div className="login-divider"><span>or</span></div>
          <div className="login-provider">
            <GoogleSignIn role={form.role} inviteCode={form.invite_code.trim() || undefined}
              rolePassword={needsRolePassword ? form.role_password : undefined} label="Sign up with Google" disabled={!configured || (needsRolePassword && !form.role_password)} onComplete={() => setForm((f) => ({ ...f, password: "", role_password: "" }))} />
          </div>
        </>}
        <p className="login-create">Already have an account? <Link href="/login">Sign in <ArrowUpRight size={13} /></Link></p>
        <p className="login-create signup-demo-note">Want to try every role without an account? Use the one-click demo buttons on the <Link href="/login">sign-in page</Link>.</p>
        <p className="signup-warning">Use a password you don’t use elsewhere, and don’t upload confidential material: this is a shared demo workspace. Account availability follows this server’s signup policy.</p>
      </form>
      </div>
      <p className="login-signature">AI suggests. Humans decide.</p>
    </div>
  );
}

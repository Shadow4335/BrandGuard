"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ErrorNote } from "@/components/RequireAuth";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
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
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "creator" as UserRole });
  const [busy, setBusy] = useState(false);
  const [local, setLocal] = useState<string | null>(null);
  const [allowed, setAllowed] = useState<UserRole[]>(["creator", "manager", "reviewer"]);
  useEffect(() => { api.health().then((h) => h.signup_roles?.length && setAllowed(h.signup_roles)).catch(() => {}); }, []);
  const MIN = 10;
  const left = Math.max(0, MIN - form.password.length);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password.length < MIN) { setLocal(`Use a password with at least ${MIN} characters.`); return; }
    setLocal(null); setBusy(true);
    const ok = await signUp(form);
    setBusy(false);
    if (ok) router.push("/dashboard");
  }

  const input = "mt-1 w-full border border-zinc-400 rounded-lg px-3 py-2 bg-white text-zinc-900";
  return (
    <div className="max-w-lg mx-auto p-4 md:p-8 space-y-4">
      <h1 className="text-2xl font-bold">Create your account</h1>
      <p className="text-sm text-zinc-800">
        New accounts join the shared <strong>GlowLeaf Naturals</strong> demo workspace, a fictional brand with
        guidelines, approved facts and sample history already set up. Your account is ready immediately; no email confirmation. Your password is stored only as a salted hash and is never visible to anyone, including us.
      </p>
      <ErrorNote message={local || error} />
      <form onSubmit={submit} className="space-y-4 rounded-xl border border-zinc-300 bg-white p-5">
        <label className="block text-sm font-medium">Your name
          <input required autoComplete="name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className={input} />
        </label>
        <label className="block text-sm font-medium">Email
          <input required type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={input} />
        </label>
        <label className="block text-sm font-medium">Password
          <input required type="password" minLength={MIN} maxLength={128} autoComplete="new-password" aria-describedby="pw-help" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className={input} />
          <span id="pw-help" className="mt-1 block text-xs font-normal text-zinc-700">
            {left > 0 ? `${left} more character${left === 1 ? "" : "s"} needed. ` : "Long enough. "}A few unrelated words works well. Avoid common passwords, your name or email, and the product name.
          </span>
        </label>
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Your role</legend>
          {ROLES.filter((r) => allowed.includes(r.value)).map((r) => (
            <label key={r.value} className={`flex items-start gap-2 rounded-lg border p-2 cursor-pointer ${form.role === r.value ? "border-indigo-700 bg-indigo-50" : "border-zinc-300"}`}>
              <input type="radio" name="role" value={r.value} checked={form.role === r.value} onChange={() => setForm({ ...form, role: r.value })} className="mt-1" />
              <span><strong className="text-sm">{r.label}</strong><br /><span className="text-xs text-zinc-700">{r.desc}</span></span>
            </label>
          ))}
          {!allowed.includes("admin") && <p className="text-xs text-zinc-700">Admin accounts can&apos;t be created here, because admins change the shared brand sources. Use the one-click Admin demo on the <Link href="/login" className="underline">sign-in page</Link> to see that view.</p>}
        </fieldset>
        <button disabled={busy} className="w-full rounded-lg bg-indigo-700 text-white px-4 py-2.5 font-medium disabled:opacity-50">
          {busy ? "Creating your account..." : "Create account"}
        </button>
      </form>
      <p className="text-sm text-zinc-800">
        Already have an account? <Link href="/login" className="underline font-medium">Sign in</Link>. Want to try every role without an account? Use the one-click demo buttons on the <Link href="/login" className="underline font-medium">sign-in page</Link>.
      </p>
      <p className="text-xs text-zinc-700">Use a password you don&apos;t use elsewhere. Don&apos;t upload confidential material: this is a shared demo workspace.</p>
    </div>
  );
}

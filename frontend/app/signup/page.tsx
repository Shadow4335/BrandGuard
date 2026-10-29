"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ErrorNote } from "@/components/RequireAuth";
import { useAuth } from "@/lib/auth-context";
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

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password.length < 8) { setLocal("Use a password with at least 8 characters."); return; }
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
        guidelines, approved facts and sample history already set up. Your account is ready immediately; no email confirmation.
      </p>
      <ErrorNote message={local || error} />
      <form onSubmit={submit} className="space-y-4 rounded-xl border border-zinc-300 bg-white p-5">
        <label className="block text-sm font-medium">Your name
          <input required autoComplete="name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className={input} />
        </label>
        <label className="block text-sm font-medium">Email
          <input required type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={input} />
        </label>
        <label className="block text-sm font-medium">Password (at least 8 characters)
          <input required type="password" minLength={8} autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className={input} />
        </label>
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Your role</legend>
          {ROLES.map((r) => (
            <label key={r.value} className={`flex items-start gap-2 rounded-lg border p-2 cursor-pointer ${form.role === r.value ? "border-indigo-700 bg-indigo-50" : "border-zinc-300"}`}>
              <input type="radio" name="role" value={r.value} checked={form.role === r.value} onChange={() => setForm({ ...form, role: r.value })} className="mt-1" />
              <span><strong className="text-sm">{r.label}</strong><br /><span className="text-xs text-zinc-700">{r.desc}</span></span>
            </label>
          ))}
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

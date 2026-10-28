"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { RequireAuth, ErrorNote } from "@/components/RequireAuth";
import { StatusBadge } from "@/components/Pills";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import type { QueueItem, UserRole } from "@/lib/types";

const STEPS: Record<UserRole, { text: string; href: string; done: (c: QueueItem[]) => boolean }[]> = {
  creator: [
    { text: "Create your first content (try Load sample 1)", href: "/content/new", done: (c) => c.length > 0 },
    { text: "Run the AI review and decide on each suggestion", href: "/reviews", done: (c) => c.some((i) => i.content.status !== "draft") },
    { text: "Save a new version and submit it for review", href: "/reviews", done: (c) => c.some((i) => ["pending_manager", "escalated", "approved"].includes(i.content.status)) },
  ],
  manager: [
    { text: "Open the review queue and read the findings", href: "/reviews", done: () => false },
    { text: "Add a comment, then approve, request changes or escalate", href: "/reviews", done: () => false },
  ],
  reviewer: [
    { text: "Open an escalated item", href: "/reviews", done: () => false },
    { text: "Approve (with a written override reason if high-severity issues remain) or reject with a reason", href: "/reviews", done: () => false },
  ],
  admin: [
    { text: "Check the brand sources and rules", href: "/brand", done: () => false },
    { text: "Open Insights and look at guidelines that may be unclear", href: "/insights", done: () => false },
  ],
};

export default function DashboardPage() {
  return <RequireAuth><Dashboard /></RequireAuth>;
}

function Dashboard() {
  const { profile } = useAuth();
  const [items, setItems] = useState<QueueItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.contentList().then(setItems).catch((e) => setError(e.message)); }, []);
  if (!profile) return null;
  const steps = STEPS[profile.role];
  const counts = (items ?? []).reduce<Record<string, number>>((a, i) => ({ ...a, [i.content.status]: (a[i.content.status] ?? 0) + 1 }), {});
  const next = steps.find((s) => !s.done(items ?? []));
  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-6">
      <h1 className="text-2xl font-bold">Welcome, {profile.full_name ?? profile.email}</h1>
      <ErrorNote message={error} />
      <section aria-labelledby="checklist" className="rounded-xl border border-zinc-300 bg-white p-5">
        <h2 id="checklist" className="font-semibold mb-3">Your guided checklist ({profile.role})</h2>
        <ol className="space-y-2">
          {steps.map((s) => {
            const done = s.done(items ?? []);
            return (
              <li key={s.text} className="flex items-start gap-2">
                <span aria-hidden className={done ? "text-emerald-700" : "text-zinc-500"}>{done ? "✔" : "○"}</span>
                <Link href={s.href} className={`underline ${s === next ? "font-semibold text-indigo-800" : "text-zinc-800"}`}>{s.text}</Link>
                {s === next && <span className="text-xs bg-indigo-100 text-indigo-900 border border-indigo-300 rounded px-1.5">next</span>}
              </li>
            );
          })}
        </ol>
      </section>
      <section aria-label="Status counts" className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(["draft", "checked", "pending_manager", "escalated", "approved", "changes_requested", "rejected"] as const).map((s) => (
          <div key={s} className="rounded-lg border border-zinc-300 bg-white p-3"><StatusBadge status={s} /><p className="text-2xl font-bold mt-1">{counts[s] ?? 0}</p></div>
        ))}
      </section>
      <section aria-labelledby="recent">
        <h2 id="recent" className="font-semibold mb-2">Recent content</h2>
        {items && items.length === 0 && (
          <p className="rounded-lg border border-dashed border-zinc-400 p-4 text-zinc-800">
            Nothing here yet. {profile.role === "creator" ? <Link className="underline font-medium" href="/content/new">Create your first content</Link> : "Ask a creator to submit content, or switch role to Creator."}
          </p>
        )}
        <ul className="divide-y divide-zinc-200 rounded-lg border border-zinc-300 bg-white">
          {(items ?? []).slice(0, 8).map((i) => (
            <li key={i.content.id} className="p-3 flex items-center justify-between gap-3">
              <Link href={profile.role === "creator" || profile.role === "admin" ? `/content/${i.content.id}` : `/reviews/${i.content.id}`} className="font-medium underline">{i.content.title}</Link>
              <span className="flex items-center gap-2"><span className="text-xs text-zinc-700">{i.total_findings} findings</span><StatusBadge status={i.content.status} /></span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

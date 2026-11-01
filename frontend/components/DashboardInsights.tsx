"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import type { InsightsSummary } from "@/lib/types";
export function DashboardInsights() {
  const [summary, setSummary] = useState<InsightsSummary | null>(null);
  const [failed, setFailed] = useState(false);
  // The dashboard shows the signed-in user's own activity; the shared workspace history lives on the Insights page.
  useEffect(() => { api.insights("mine").then(setSummary).catch(() => setFailed(true)); }, []);
  if (!summary) return <p role="status" className="text-sm text-zinc-700">{failed ? "Your activity could not be loaded. Refresh to retry." : "Loading your activity…"}</p>;
  const empty = !summary.total_content && !summary.total_findings && !summary.approvals_total;
  return <section className="space-y-5" aria-label="Your activity in the last 30 days">
    <p className="eyebrow text-zinc-700">Your activity · Last 30 days</p>
    <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">{[["Your content", summary.total_content], ["Findings on your content", summary.total_findings], ["Your override approvals", `${summary.override_approvals} / ${summary.approvals_total}`], ["Your override rate", summary.approvals_total ? `${Math.round(summary.override_approvals / summary.approvals_total * 100)}%` : "n/a"]].map(([label, value]) => <div key={label} className="rounded-xl border border-zinc-300 bg-white p-5"><dt className="text-xs text-zinc-700">{label}</dt><dd className="text-3xl mt-4">{value}</dd></div>)}</dl>
    <div className="rounded-xl border border-zinc-300 bg-white p-6"><div className="flex justify-between gap-4"><h2>Findings over time</h2><Link className="text-sm underline" href="/insights">View insights ↗</Link></div><p className="text-sm text-zinc-700 mt-2">{empty ? "Nothing yet. Findings on content you create appear here; Insights shows the whole workspace." : `${summary.total_findings} findings on your content in the last 30 days`}</p><div className="h-56 mt-6" role="img" aria-label={`Daily findings on your content for the last 30 days. ${summary.total_findings} total.`}><ResponsiveContainer><LineChart data={summary.trend}><XAxis dataKey="date" tickFormatter={(v: string) => v.slice(5)} tick={{ fontSize: 11 }} minTickGap={40} /><YAxis allowDecimals={false} width={30} /><Tooltip /><Line dataKey="count" stroke="#cbd2c5" strokeWidth={2} dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer></div></div>
  </section>;
}

"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import type { InsightsSummary } from "@/lib/types";
export function DashboardInsights() {
  const [summary, setSummary] = useState<InsightsSummary | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { api.insights().then(setSummary).catch(() => setFailed(true)); }, []);
  if (!summary) return <p role="status" className="text-sm text-zinc-700">{failed ? "Insights could not be loaded. Open Insights to retry." : "Loading workspace insights…"}</p>;
  return <section className="space-y-5" aria-label="Workspace insights for the last 30 days">
    <p className="eyebrow text-zinc-700">Governance at a glance · Last 30 days</p>
    <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">{[["Content items", summary.total_content], ["Review findings", summary.total_findings], ["Override approvals", `${summary.override_approvals} / ${summary.approvals_total}`], ["Override rate", summary.approvals_total ? `${Math.round(summary.override_approvals / summary.approvals_total * 100)}%` : "n/a"]].map(([label, value]) => <div key={label} className="rounded-xl border border-zinc-300 bg-white p-5"><dt className="text-xs text-zinc-700">{label}</dt><dd className="text-3xl mt-4">{value}</dd></div>)}</dl>
    <div className="rounded-xl border border-zinc-300 bg-white p-6"><div className="flex justify-between gap-4"><h2>Findings over time</h2><Link className="text-sm underline" href="/insights">View insights ↗</Link></div><p className="text-sm text-zinc-700 mt-2">{summary.total_findings} findings recorded in the last 30 days</p><div className="h-56 mt-6" role="img" aria-label={`Daily findings for the last 30 days. ${summary.total_findings} total. See Insights for the data table.`}><ResponsiveContainer><LineChart data={summary.trend}><XAxis dataKey="date" tickFormatter={(v: string) => v.slice(5)} tick={{ fontSize: 11 }} minTickGap={40} /><YAxis allowDecimals={false} width={30} /><Tooltip /><Line dataKey="count" stroke="#cbd2c5" strokeWidth={2} dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer></div></div>
  </section>;
}

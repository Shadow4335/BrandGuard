"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import { plural } from "@/lib/utils";
import type { InsightsSummary, UserRole } from "@/lib/types";

const overrideRate = (s: InsightsSummary) => (s.approvals_total ? `${Math.round((s.override_approvals / s.approvals_total) * 100)}%` : "n/a");

/** What each role does differently, so nobody gets another role's numbers: creators write, managers and reviewers
 *  decide, admins look after the whole workspace. */
function view(role: UserRole, s: InsightsSummary, waiting: number) {
  if (role === "creator") {
    return {
      eyebrow: "Your activity", cards: [["Your content", s.total_content], ["Findings on your content", s.total_findings],
        ["Findings you decided", s.findings_decided], ["Findings still open", s.total_findings - s.findings_decided]],
      chartTitle: "Findings over time", trend: s.trend, link: { href: "/insights", label: "View insights ↗" },
      caption: s.total_content ? `${plural(s.total_findings, "finding")} on your content in the last 30 days`
        : "Nothing yet. Findings on content you create appear here; Insights shows the whole workspace.",
    };
  }
  if (role === "admin") {
    return {
      eyebrow: "Workspace activity", cards: [["Content items", s.total_content], ["Findings", s.total_findings],
        ["Approvals with override", `${s.override_approvals} / ${s.approvals_total}`], ["Approval override rate", overrideRate(s)]],
      chartTitle: "Findings over time", trend: s.trend, link: { href: "/insights", label: "View insights ↗" },
      caption: `${plural(s.total_findings, "finding")} across the workspace in the last 30 days`,
    };
  }
  return {
    eyebrow: "Your decisions", cards: [["Waiting for you", waiting], ["Decisions you made", s.decisions_total],
      ["Your approvals with override", `${s.override_approvals} / ${s.approvals_total}`], ["Your override rate", overrideRate(s)]],
    chartTitle: "Decisions over time", trend: s.decision_trend, link: { href: "/reviews", label: "Open your queue ↗" },
    caption: s.decisions_total ? `${plural(s.decisions_total, "decision")} in the last 30 days`
      : "Nothing yet. Your approvals, escalations and other decisions appear here.",
  };
}

export function DashboardInsights({ role, waiting }: { role: UserRole; waiting: number }) {
  const [summary, setSummary] = useState<InsightsSummary | null>(null);
  const [failed, setFailed] = useState(false);
  // Everyone sees their own work; only admins, who run the workspace, start from the shared totals.
  useEffect(() => { api.insights(role === "admin" ? "workspace" : "mine").then(setSummary).catch(() => setFailed(true)); }, [role]);
  if (!summary) return <p role="status" className="text-sm text-zinc-700">{failed ? "Your activity could not be loaded. Refresh to retry." : "Loading your activity…"}</p>;
  const v = view(role, summary, waiting);
  return <section className="space-y-5" aria-label={`${v.eyebrow} in the last 30 days`}>
    <p className="eyebrow text-zinc-700">{v.eyebrow} · Last 30 days</p>
    <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">{v.cards.map(([label, value]) => <div key={label} className="rounded-xl border border-zinc-300 bg-white p-5"><dt className="text-xs text-zinc-700">{label}</dt><dd className="text-3xl mt-4">{value}</dd></div>)}</dl>
    <div className="rounded-xl border border-zinc-300 bg-white p-6"><div className="flex justify-between gap-4"><h2>{v.chartTitle}</h2><Link className="text-sm underline" href={v.link.href}>{v.link.label}</Link></div><p className="text-sm text-zinc-700 mt-2">{v.caption}</p><div className="h-56 mt-6" role="img" aria-label={`${v.chartTitle}, last 30 days. ${v.caption}`}><ResponsiveContainer><LineChart data={v.trend}><XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} tick={{ fontSize: 11 }} minTickGap={40} /><YAxis allowDecimals={false} width={30} /><Tooltip /><Line dataKey="count" stroke="#cbd2c5" strokeWidth={2} dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer></div></div>
  </section>;
}

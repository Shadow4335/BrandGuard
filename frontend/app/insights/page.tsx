"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { RequireAuth, ErrorNote } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { InsightsSummary, UnclearRule } from "@/lib/types";

export default function InsightsPage() {
  return <RequireAuth><Insights /></RequireAuth>;
}

const card = "rounded-xl border border-zinc-300 bg-white p-4";

function Insights() {
  const [s, setS] = useState<InsightsSummary | null>(null);
  const [unclear, setUnclear] = useState<UnclearRule[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.insights().then(setS).catch((e) => setError(e.message));
    api.unclear().then(setUnclear).catch(() => {});
  }, []);
  if (!s) return <div className="p-8">{error ? <ErrorNote message={error} /> : "Loading insights..."}</div>;
  const short = (t: string) => (t.length > 26 ? t.slice(0, 25) + "…" : t);

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-6">
      <h1 className="text-2xl font-bold">Insights</h1>
      <p className="text-zinc-800">Last 30 days. {s.total_findings} findings across {s.total_content} content items. {s.override_approvals} of {s.approvals_total} approvals were overrides.</p>

      <section aria-labelledby="unclear-h" className="rounded-xl border-2 border-amber-500 bg-amber-50 p-4 space-y-2">
        <h2 id="unclear-h" className="font-semibold">Guidelines that may be unclear</h2>
        {unclear.length === 0 && <p className="text-sm">No rules are being disputed right now.</p>}
        <ul className="space-y-2">
          {unclear.map((u) => (
            <li key={u.rule_id} className="rounded-lg bg-white border border-amber-300 p-3 text-sm">
              <strong>{u.title}</strong> <code className="text-xs bg-zinc-100 px-1 rounded">{u.rule_id}</code>
              <p>{u.reason}. {u.suggestion}</p>
              <Link href="/brand" className="underline font-medium text-indigo-900">Review this guideline</Link>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid md:grid-cols-2 gap-6">
        <section className={card} aria-labelledby="top-h">
          <h2 id="top-h" className="font-semibold mb-2">Most frequently violated rules</h2>
          <div className="h-72" role="img" aria-label="Bar chart of findings per rule">
            <ResponsiveContainer><BarChart data={s.top_rules.map((r) => ({ ...r, name: short(r.title) }))} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
              <Tooltip /><Bar dataKey="count" fill="#4338ca" name="Findings" />
            </BarChart></ResponsiveContainer>
          </div>
        </section>
        <section className={card} aria-labelledby="cat-h">
          <h2 id="cat-h" className="font-semibold mb-2">Findings by category</h2>
          <div className="h-72" role="img" aria-label="Bar chart of findings per category">
            <ResponsiveContainer><BarChart data={s.by_category}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="category" tick={{ fontSize: 12 }} /><YAxis allowDecimals={false} />
              <Tooltip /><Bar dataKey="count" fill="#0f766e" name="Findings" />
            </BarChart></ResponsiveContainer>
          </div>
        </section>
      </div>

      <section className={card} aria-labelledby="trend-h">
        <h2 id="trend-h" className="font-semibold mb-2">Violations over time</h2>
        <div className="h-64" role="img" aria-label="Line chart of findings per day">
          <ResponsiveContainer><LineChart data={s.trend}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} tick={{ fontSize: 11 }} /><YAxis allowDecimals={false} />
            <Tooltip /><Line type="monotone" dataKey="count" stroke="#b45309" strokeWidth={2} dot={false} name="Findings" />
          </LineChart></ResponsiveContainer>
        </div>
      </section>

      <section className={card} aria-labelledby="ov-h">
        <h2 id="ov-h" className="font-semibold mb-2">Most overridden rules</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left border-b border-zinc-300"><th className="py-1 pr-3">Rule</th><th className="pr-3">Decisions</th><th className="pr-3">Rejected</th><th>Override rate</th></tr></thead>
            <tbody>
              {s.most_overridden.map((r) => (
                <tr key={r.rule_id} className="border-b border-zinc-100">
                  <td className="py-1 pr-3">{r.title} <code className="text-xs bg-zinc-100 px-1 rounded">{r.rule_id}</code></td>
                  <td className="pr-3">{r.decided}</td><td className="pr-3">{r.rejected}</td>
                  <td className={r.override_rate >= 0.4 ? "font-bold text-red-800" : ""}>{Math.round(r.override_rate * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

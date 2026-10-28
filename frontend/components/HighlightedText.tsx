"use client";

import type { Finding, FindingSeverity } from "@/lib/types";

const BG: Record<FindingSeverity, string> = {
  high: "bg-red-200 border-red-700",
  medium: "bg-amber-200 border-amber-700",
  low: "bg-sky-200 border-sky-700",
};
const RANK: Record<FindingSeverity, number> = { high: 0, medium: 1, low: 2 };

/** Renders text with every finding span highlighted (overlaps handled by splitting at all boundaries). */
export function HighlightedText({
  text, findings, selectedId, onSelect,
}: { text: string; findings: Finding[]; selectedId?: string | null; onSelect: (id: string) => void }) {
  const spans = findings.filter((f) => f.span);
  const cuts = new Set<number>([0, text.length]);
  spans.forEach((f) => { cuts.add(Math.min(f.span!.start, text.length)); cuts.add(Math.min(f.span!.end, text.length)); });
  const pts = [...cuts].sort((a, b) => a - b);
  const parts: React.ReactNode[] = [];
  const inserts = spans.filter((f) => f.span!.start === f.span!.end);

  for (let i = 0; i < pts.length - 1; i++) {
    const [s, e] = [pts[i], pts[i + 1]];
    inserts.filter((f) => f.span!.start === s).forEach((f) => parts.push(
      <button key={`ins-${f.id}`} type="button" onClick={() => onSelect(f.id)} aria-label={`Insertion point: ${f.issue}`}
        className={`px-1 mx-0.5 rounded border-b-2 text-xs font-bold ${BG[f.severity]} ${selectedId === f.id ? "ring-2 ring-indigo-700" : ""}`}>+ add</button>));
    if (e <= s) continue;
    const covering = spans.filter((f) => f.span!.start < e && f.span!.end > s && f.span!.end > f.span!.start)
      .sort((a, b) => RANK[a.severity] - RANK[b.severity]);
    const chunk = text.slice(s, e);
    if (!covering.length) { parts.push(<span key={`t-${s}`}>{chunk}</span>); continue; }
    const top = covering.find((f) => f.id === selectedId) ?? covering[0];
    const resolved = top.status === "accepted" || top.status === "edited";
    parts.push(
      <mark key={`m-${s}`} onClick={() => onSelect(top.id)} tabIndex={0} role="button"
        onKeyDown={(e2) => { if (e2.key === "Enter" || e2.key === " ") { e2.preventDefault(); onSelect(top.id); } }}
        aria-label={`${top.severity} severity issue: ${top.issue}`}
        className={`cursor-pointer border-b-2 text-zinc-950 rounded-sm ${BG[top.severity]} ${resolved ? "opacity-60" : ""} ${covering.some((f) => f.id === selectedId) ? "ring-2 ring-indigo-700" : ""}`}>
        {chunk}
      </mark>);
  }
  return <p className="whitespace-pre-wrap leading-relaxed text-zinc-900">{parts}</p>;
}

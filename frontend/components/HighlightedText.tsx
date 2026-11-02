"use client";

import { hasTextChange } from "@/lib/findings";
import type { Finding, FindingSeverity } from "@/lib/types";

const BG: Record<FindingSeverity, string> = {
  high: "bg-red-200 border-red-700",
  medium: "bg-amber-200 border-amber-700",
  low: "bg-sky-200 border-sky-700",
};
const RANK: Record<FindingSeverity, number> = { high: 0, medium: 1, low: 2 };
const isBroad = (f: Finding) => f.span!.end - f.span!.start > 60;

type Piece =
  | { kind: "insert"; finding: Finding }
  | { kind: "text"; start: number; end: number }
  | { kind: "mark"; start: number; end: number; top: Finding; selected: boolean };

/** Renders text with every finding span highlighted (overlaps handled by splitting at all boundaries). Neighbouring
 *  pieces for the same finding join into one highlight. A finding split up by other findings gets one keyboard stop,
 *  on its first piece, so screen readers and Tab don't meet the same issue over and over. */
export function HighlightedText({
  text, findings, selectedId, onSelect,
}: { text: string; findings: Finding[]; selectedId?: string | null; onSelect: (id: string) => void }) {
  const spans = findings.filter((f) => f.span);
  const cuts = new Set<number>([0, text.length]);
  spans.forEach((f) => { cuts.add(Math.min(f.span!.start, text.length)); cuts.add(Math.min(f.span!.end, text.length)); });
  const pts = [...cuts].sort((a, b) => a - b);
  const inserts = spans.filter((f) => f.span!.start === f.span!.end);
  const pieces: Piece[] = [];

  for (let i = 0; i < pts.length; i++) {
    const s = pts[i];
    inserts.filter((f) => f.span!.start === s).forEach((finding) => pieces.push({ kind: "insert", finding }));
    const e = pts[i + 1];
    if (e === undefined || e <= s) continue;
    const covering = spans.filter((f) => f.span!.start < e && f.span!.end > s && f.span!.end > f.span!.start)
      // A broad, post-level finding goes last whatever its severity, so it can't hide the precise ones inside it
      .sort((a, b) => Number(isBroad(a)) - Number(isBroad(b)) || RANK[a.severity] - RANK[b.severity] || (a.span!.end - a.span!.start) - (b.span!.end - b.span!.start));
    if (!covering.length) { pieces.push({ kind: "text", start: s, end: e }); continue; }
    const top = covering.find((f) => f.id === selectedId) ?? covering[0];
    const selected = covering.some((f) => f.id === selectedId);
    const last = pieces[pieces.length - 1];
    if (last?.kind === "mark" && last.top.id === top.id && last.selected === selected) last.end = e;
    else pieces.push({ kind: "mark", start: s, end: e, top, selected });
  }

  const announced = new Set<string>();
  return (
    <p className="whitespace-pre-wrap leading-relaxed text-zinc-900">
      {pieces.map((p) => {
        if (p.kind === "insert") {
          return (
            <button key={`ins-${p.finding.id}`} type="button" onClick={() => onSelect(p.finding.id)} aria-label={`Insertion point: ${p.finding.issue}`}
              className={`px-1 mx-0.5 rounded border-b-2 text-xs font-bold ${BG[p.finding.severity]} ${selectedId === p.finding.id ? "ring-2 ring-indigo-700" : ""}`}>+ add</button>
          );
        }
        const chunk = text.slice(p.start, p.end);
        if (p.kind === "text") return <span key={`t-${p.start}`}>{chunk}</span>;
        const { top } = p;
        const first = !announced.has(top.id);
        announced.add(top.id);
        const look = `cursor-pointer border-b-2 text-zinc-950 rounded-sm ${BG[top.severity]} ${hasTextChange(top) ? "opacity-60" : ""} ${p.selected ? "ring-2 ring-indigo-700" : ""}`;
        return first ? (
          <mark key={`m-${p.start}`} onClick={() => onSelect(top.id)} tabIndex={0} role="button"
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(top.id); } }}
            aria-label={`${chunk}. ${top.severity} severity issue: ${top.issue}`} className={look}>{chunk}</mark>
        ) : <mark key={`m-${p.start}`} onClick={() => onSelect(top.id)} className={look}>{chunk}</mark>;
      })}
    </p>
  );
}

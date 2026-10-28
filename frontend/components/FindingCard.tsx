"use client";

import { useState } from "react";
import { ConfidencePill, SeverityPill } from "@/components/Pills";
import type { Finding, Source } from "@/lib/types";

export function FindingCard({
  f, sources, selected, canDecide, onSelect, onDecide, onComment,
}: {
  f: Finding; sources: Source[]; selected: boolean; canDecide: boolean;
  onSelect: () => void;
  onDecide?: (decision: "accepted" | "edited" | "rejected", text?: string, reason?: string) => Promise<void>;
  onComment?: () => void;
}) {
  const [mode, setMode] = useState<null | "edit" | "reject">(null);
  const [text, setText] = useState(f.replacement ?? f.span_text ?? "");
  const [reason, setReason] = useState("Not applicable here");
  const [openCode, setOpenCode] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const isUnsupported = f.rule_id === "RULE-CLAIM-UNSUPPORTED" || f.issue.includes("Unsupported claim");
  const legal = f.source_codes.some((c) => c.startsWith("REG-"));

  async function go(d: "accepted" | "edited" | "rejected") {
    if (!onDecide) return;
    setBusy(true);
    try { await onDecide(d, d === "edited" ? text : undefined, d === "rejected" ? reason : undefined); setMode(null); }
    finally { setBusy(false); }
  }

  const btn = "rounded-md border px-3 py-1 text-sm font-medium disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-700";
  return (
    <article onClick={onSelect} aria-label={f.issue}
      className={`rounded-xl border bg-white p-4 space-y-2 ${selected ? "border-indigo-700 ring-2 ring-indigo-300" : "border-zinc-300"}`}>
      <div className="flex flex-wrap items-center gap-2">
        <SeverityPill value={f.severity} /><ConfidencePill value={f.confidence} />
        <span className="text-xs text-zinc-700">Layer {f.layer} · {f.category}</span>
        {isUnsupported && <span className="text-xs font-semibold bg-orange-100 text-orange-900 border border-orange-300 rounded px-1.5">Unsupported claim</span>}
        {f.status !== "open" && <span className="ml-auto text-xs font-semibold bg-zinc-900 text-white rounded px-2 py-0.5">{f.status}</span>}
      </div>
      <p className="font-semibold text-zinc-950"><span className="text-xs uppercase tracking-wide text-zinc-600 mr-1">Issue</span>{f.issue}</p>
      <p className="text-sm text-zinc-900"><span className="text-xs uppercase tracking-wide text-zinc-600 mr-1">Why flagged</span>{f.why_flagged}</p>
      <div className="text-sm flex flex-wrap items-center gap-1">
        <span className="text-xs uppercase tracking-wide text-zinc-600 mr-1">Rule / source</span>
        {f.rule_id && <code className="text-xs bg-zinc-100 px-1.5 rounded">{f.rule_id}</code>}
        {f.source_codes.map((c) => (
          <button key={c} type="button" aria-expanded={openCode === c}
            onClick={(e) => { e.stopPropagation(); setOpenCode(openCode === c ? null : c); }}
            className="text-xs bg-indigo-100 text-indigo-950 border border-indigo-400 px-1.5 rounded hover:bg-indigo-200">{c}</button>
        ))}
        {f.source_codes.length === 0 && isUnsupported && <span className="text-xs text-zinc-700">no approved source found</span>}
      </div>
      {openCode && (
        <blockquote className="text-sm bg-zinc-50 border-l-4 border-indigo-600 p-2 whitespace-pre-wrap">
          <strong>{openCode}</strong> {sources.find((s) => s.code === openCode)?.title}
          <br />{sources.find((s) => s.code === openCode)?.body ?? "Source text not available."}
        </blockquote>
      )}
      <p className="text-sm text-zinc-900"><span className="text-xs uppercase tracking-wide text-zinc-600 mr-1">Suggested fix</span>{f.suggested_fix}
        {f.replacement && <span className="block mt-1">Replacement text: <code className="bg-emerald-50 border border-emerald-300 px-1 rounded">{f.replacement}</code></span>}
      </p>
      {legal && <p className="text-xs text-zinc-700">Not legal advice. This flags risk; people make the final call.</p>}
      {f.decision_reason && <p className="text-xs text-zinc-800">Reason given: {f.decision_reason}</p>}
      {f.status === "edited" && <p className="text-xs text-zinc-800">Edited to: <code>{f.decision_text}</code></p>}

      {canDecide && onDecide && (
        <div className="pt-1 space-y-2" onClick={(e) => e.stopPropagation()}>
          <div className="flex flex-wrap gap-2">
            <button disabled={busy || (!f.replacement && !f.span)} onClick={() => go("accepted")} className={`${btn} border-emerald-700 text-emerald-900 bg-emerald-50`}>Accept</button>
            <button disabled={busy} onClick={() => setMode(mode === "edit" ? null : "edit")} className={`${btn} border-indigo-700 text-indigo-900 bg-indigo-50`}>Edit</button>
            <button disabled={busy} onClick={() => setMode(mode === "reject" ? null : "reject")} className={`${btn} border-zinc-600 text-zinc-900 bg-zinc-50`}>Reject</button>
            {onComment && <button onClick={onComment} className={`${btn} border-zinc-300 text-zinc-800`}>Comment</button>}
          </div>
          {!f.replacement && f.status === "open" && <p className="text-xs text-zinc-700">This fix needs your wording: use Edit to type the text, or Accept to acknowledge it.</p>}
          {mode === "edit" && (
            <div className="space-y-1">
              <label className="text-sm font-medium block">Your wording (replaces the highlighted text)
                <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} className="mt-1 w-full border border-zinc-400 rounded p-2" /></label>
              <button disabled={busy || !text.trim()} onClick={() => go("edited")} className={`${btn} border-indigo-700 bg-indigo-700 text-white`}>Save my edit</button>
            </div>
          )}
          {mode === "reject" && (
            <div className="space-y-1">
              <label className="text-sm font-medium block">Why are you rejecting this?
                <input value={reason} onChange={(e) => setReason(e.target.value)} className="mt-1 w-full border border-zinc-400 rounded p-2" /></label>
              <button disabled={busy || !reason.trim()} onClick={() => go("rejected")} className={`${btn} border-zinc-800 bg-zinc-800 text-white`}>Confirm reject</button>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

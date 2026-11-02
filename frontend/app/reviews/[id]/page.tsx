"use client";

import { isUnresolvedHigh } from "@/lib/findings";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { RequireAuth, ErrorNote, LoadFailed } from "@/components/RequireAuth";
import { StatusBadge } from "@/components/Pills";
import { HighlightedText } from "@/components/HighlightedText";
import { FindingCard } from "@/components/FindingCard";
import { CommentThread } from "@/components/CommentThread";
import { AuditTrail } from "@/components/AuditTrail";
import { DiffPane } from "@/components/DiffPane";
import { ActionDialog } from "@/components/ActionDialog";
import { Loading } from "@/components/Loading";
import { api } from "@/lib/api";
import { plural } from "@/lib/utils";
import type { ContentDetail, Source, WorkflowAction } from "@/lib/types";

export default function ReviewDetailPage() {
  return <RequireAuth><Detail /></RequireAuth>;
}

const LABELS: Record<WorkflowAction, string> = {
  submit: "Submit for review", approve: "Approve", request_changes: "Request changes", escalate: "Escalate", reject: "Reject",
};

function Detail() {
  const { id } = useParams<{ id: string }>();
  const [d, setD] = useState<ContentDetail | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dialog, setDialog] = useState<WorkflowAction | null>(null);
  const [tick, setTick] = useState(0);
  const [busy, setBusy] = useState(false);
  const [imgUrl, setImgUrl] = useState<string | null>(null);
  const [imgSize, setImgSize] = useState<[number, number] | null>(null);
  const load = useCallback(async () => {
    try { setD(await api.content(id)); setTick((t) => t + 1); } catch (e) { setError((e as Error).message); }
  }, [id]);
  useEffect(() => { let active = true; Promise.resolve().then(() => { if (active) return load(); }); api.sources().then(setSources).catch(() => {}); return () => { active = false; }; }, [load]);
  useEffect(() => {
    if (d?.has_image) api.imageUrl(id, d.content.current_version).then(setImgUrl).catch(() => setImgUrl(null));
  }, [d?.has_image, d?.content.current_version, id]);
  if (!d) return error ? <LoadFailed message={error} /> : <Loading label="Loading review" />;

  const cur = d.versions.find((v) => v.version_number === d.content.current_version)!;
  const prev = d.versions.find((v) => v.version_number === d.content.current_version - 1);
  const unresolved = d.findings.filter(isUnresolvedHigh).length;
  const lastDecision = d.approvals[d.approvals.length - 1];
  const isOverride = dialog === "approve" && unresolved > 0;
  const needsReason = dialog === "request_changes" || dialog === "reject" || isOverride;

  async function run(action: WorkflowAction, reason?: string) {
    if (busy) return;
    setBusy(true);
    try {
      setError(null);
      setD(await api.transition(id, action, reason, isOverride));
      setDialog(null); setTick((t) => t + 1);
    } catch (e) { setError((e as Error).message); setDialog(null); }
    finally { setBusy(false); }
  }
  function click(a: WorkflowAction) {
    if (a === "approve" && !unresolved && d!.content.status === "pending_manager") { run(a); return; }
    setDialog(a);
  }

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6">
      <header className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">{d.content.title}</h1>
        <StatusBadge status={d.content.status} />
        <span className="text-sm text-zinc-700">by {d.creator_name} · v{d.content.current_version} · {d.content.channel.replace("_", " ")}{d.content.ai_generated ? " · AI-assisted" : ""}</span>
      </header>
      <ErrorNote message={error} />
      {lastDecision?.reason && lastDecision.action !== "submit" && (
        <p className="rounded-lg border border-zinc-300 bg-white p-3 text-sm"><strong className="capitalize">{lastDecision.role}</strong> chose to {lastDecision.action.replace("_", " ")}: &ldquo;{lastDecision.reason}&rdquo;{lastDecision.override ? <strong className="text-red-800"> [override]</strong> : null}</p>
      )}
      {d.allowed_actions.length > 0 ? (
        <div className="rounded-lg border border-indigo-300 bg-indigo-50 p-3 flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium mr-2">Your decision{unresolved ? ` (${plural(unresolved, "high-severity finding")} unresolved)` : ""}:</span>
          {d.allowed_actions.map((a) => (
            <button key={a} disabled={busy} onClick={() => click(a)} className={`rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${a === "reject" ? "bg-red-700" : a === "approve" ? "bg-emerald-700" : a === "escalate" ? "bg-purple-700" : "bg-indigo-700"}`}>{LABELS[a]}</button>
          ))}
        </div>
      ) : (
        <p className="rounded-lg border border-zinc-300 bg-white p-3 text-sm">No action needed from you right now. Status: <StatusBadge status={d.content.status} /> <Link href="/reviews" className="underline font-medium ml-2">Back to the queue</Link></p>
      )}
      {dialog && (
        <ActionDialog
          title={isOverride ? "Approve with override" : LABELS[dialog]}
          description={isOverride ? `${plural(unresolved, "high-severity finding")} still unresolved. Approving anyway is an override and is recorded in the audit trail.` : undefined}
          label={isOverride ? "Override reason" : "Reason"} required={needsReason}
          confirmText={isOverride ? "Approve with override" : LABELS[dialog]} danger={dialog === "reject"}
          onConfirm={(r) => run(dialog, r)} onCancel={() => setDialog(null)} />
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <section aria-labelledby="c-h" className="rounded-xl border border-zinc-300 bg-white p-4 space-y-2 self-start">
          <h2 id="c-h" className="font-semibold">Content</h2>
          {imgUrl && (
            <div className="relative inline-block max-w-full">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={imgUrl} alt={cur.alt_text || "Uploaded image (no alt-text yet)"} className="max-w-full rounded border border-zinc-300"
                onLoad={(e) => setImgSize([e.currentTarget.naturalWidth, e.currentTarget.naturalHeight])} />
              {imgSize && d.findings.filter((f) => f.region).map((f) => (
                <button key={f.id} aria-label={`Region: ${f.issue}`} onClick={() => setSelected(f.id)}
                  style={{ left: `${(f.region!.x / imgSize[0]) * 100}%`, top: `${(f.region!.y / imgSize[1]) * 100}%`,
                           width: `${(f.region!.w / imgSize[0]) * 100}%`, height: `${(f.region!.h / imgSize[1]) * 100}%` }}
                  className={`absolute border-2 border-red-700 bg-red-500/20 ${selected === f.id ? "ring-2 ring-indigo-700" : ""}`} />
              ))}
            </div>
          )}
          {cur.alt_text ? <p className="text-sm">Alt-text: {cur.alt_text}</p> : imgUrl ? <p className="text-sm text-red-800">No alt-text</p> : null}
          {cur.raw_text ? <HighlightedText text={cur.raw_text} findings={d.findings} selectedId={selected} onSelect={setSelected} /> : !imgUrl && <p className="text-sm text-zinc-700">No text was found in this content.</p>}
        </section>
        <section aria-labelledby="f-h" className="space-y-3">
          <h2 id="f-h" className="font-semibold">Findings and the creator&apos;s decisions ({d.findings.length})</h2>
          {d.findings.map((f) => (
            <FindingCard key={f.id} f={f} sources={sources} selected={selected === f.id} canDecide={false} onSelect={() => setSelected(f.id)} />
          ))}
        </section>
      </div>

      {prev && <section><h2 className="font-semibold mb-2">Changes from v{prev.version_number}</h2><DiffPane oldText={prev.raw_text ?? ""} newText={cur.raw_text ?? ""} oldLabel={`v${prev.version_number}`} newLabel={`v${cur.version_number}`} /></section>}
      <div className="grid md:grid-cols-2 gap-6">
        <CommentThread detail={d} onChange={load} />
        <AuditTrail contentId={id} refreshKey={tick} />
      </div>
    </div>
  );
}

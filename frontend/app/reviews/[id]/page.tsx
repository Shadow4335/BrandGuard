"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { RequireAuth, ErrorNote } from "@/components/RequireAuth";
import { StatusBadge } from "@/components/Pills";
import { HighlightedText } from "@/components/HighlightedText";
import { FindingCard } from "@/components/FindingCard";
import { CommentThread } from "@/components/CommentThread";
import { AuditTrail } from "@/components/AuditTrail";
import { DiffPane } from "@/components/DiffPane";
import { ActionDialog } from "@/components/ActionDialog";
import { api } from "@/lib/api";
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
  const load = useCallback(async () => {
    try { setD(await api.content(id)); setTick((t) => t + 1); } catch (e) { setError((e as Error).message); }
  }, [id]);
  useEffect(() => { load(); api.sources().then(setSources).catch(() => {}); }, [load]);
  if (!d) return <div className="p-8">{error ? <ErrorNote message={error} /> : "Loading..."}</div>;

  const cur = d.versions.find((v) => v.version_number === d.content.current_version)!;
  const prev = d.versions.find((v) => v.version_number === d.content.current_version - 1);
  const unresolved = d.findings.filter((f) => f.severity === "high" && (f.status === "open" || f.status === "rejected")).length;
  const isReviewerApprove = dialog === "approve" && d.allowed_actions.includes("approve") && d.content.status === "escalated";
  const needsReason = dialog === "request_changes" || dialog === "reject" || (isReviewerApprove && unresolved > 0);

  async function run(action: WorkflowAction, reason?: string) {
    try {
      setError(null);
      setD(await api.transition(id, action, reason, isReviewerApprove && unresolved > 0));
      setDialog(null); setTick((t) => t + 1);
    } catch (e) { setError((e as Error).message); setDialog(null); }
  }
  function click(a: WorkflowAction) {
    if (a === "approve" && d!.content.status === "pending_manager") { run(a); return; }
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
      {d.allowed_actions.length > 0 ? (
        <div className="rounded-lg border border-indigo-300 bg-indigo-50 p-3 flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium mr-2">Your decision{unresolved ? ` (${unresolved} high-severity finding(s) unresolved)` : ""}:</span>
          {d.allowed_actions.map((a) => (
            <button key={a} onClick={() => click(a)} className={`rounded-lg px-4 py-2 text-sm font-medium text-white ${a === "reject" ? "bg-red-700" : a === "approve" ? "bg-emerald-700" : a === "escalate" ? "bg-purple-700" : "bg-indigo-700"}`}>{LABELS[a]}</button>
          ))}
        </div>
      ) : (
        <p className="rounded-lg border border-zinc-300 bg-white p-3 text-sm">No action needed from you right now. Status: <StatusBadge status={d.content.status} /></p>
      )}
      {dialog && (
        <ActionDialog
          title={isReviewerApprove && unresolved > 0 ? "Approve with override" : LABELS[dialog]}
          description={isReviewerApprove && unresolved > 0 ? `${unresolved} high-severity finding(s) are still unresolved. Approving anyway is an override and is recorded in the audit trail.` : undefined}
          label={isReviewerApprove && unresolved > 0 ? "Override reason" : "Reason"} required={needsReason}
          confirmText={isReviewerApprove && unresolved > 0 ? "Approve with override" : LABELS[dialog]} danger={dialog === "reject"}
          onConfirm={(r) => run(dialog, r)} onCancel={() => setDialog(null)} />
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <section aria-labelledby="c-h" className="rounded-xl border border-zinc-300 bg-white p-4 space-y-2 self-start">
          <h2 id="c-h" className="font-semibold">Content</h2>
          {cur.raw_text ? <HighlightedText text={cur.raw_text} findings={d.findings} selectedId={selected} onSelect={setSelected} /> : <p className="text-sm">Image content: open it from the creator view to see regions.</p>}
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

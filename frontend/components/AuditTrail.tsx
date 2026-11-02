"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatWhen } from "@/lib/utils";
import type { AuditRow } from "@/lib/types";

export function AuditTrail({ contentId, refreshKey }: { contentId: string; refreshKey?: unknown }) {
  const [rows, setRows] = useState<AuditRow[] | null>(null); // null until the first answer
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    api.audit(contentId).then((r) => { setRows(r); setFailed(false); }).catch(() => setFailed(true));
  }, [contentId, refreshKey]);
  const important = (rows ?? []).filter((r) => r.event_type !== "finding_created");
  return (
    <section aria-labelledby="audit" className="space-y-2">
      <h2 id="audit" className="font-semibold">Audit trail</h2>
      {failed && <p role="alert" className="text-sm text-red-800">The audit trail could not be loaded. Refresh the page to try again.</p>}
      {!rows && !failed && <p role="status" className="text-sm text-zinc-700">Loading the audit trail…</p>}
      {rows && !failed && important.length === 0 && <p className="text-sm text-zinc-700">No events yet.</p>}
      <ol className="text-sm space-y-1">
        {important.map((r) => (
          <li key={r.id} className="border-l-2 border-zinc-400 pl-2">
            <span className="text-xs text-zinc-700"><time dateTime={r.created_at ?? undefined}>{formatWhen(r.created_at)}</time></span>{" "}
            <strong>{r.event_type.replace(/_/g, " ")}</strong> by {r.actor_name ?? "system"}{r.actor_role ? ` (${r.actor_role})` : ""}
            {typeof r.details?.reason === "string" && r.details.reason ? <> - reason: &ldquo;{r.details.reason}&rdquo;</> : null}
            {r.details?.override ? <strong className="text-red-800"> [override]</strong> : null}
          </li>
        ))}
      </ol>
    </section>
  );
}

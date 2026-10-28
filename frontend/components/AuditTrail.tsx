"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditRow } from "@/lib/types";

export function AuditTrail({ contentId, refreshKey }: { contentId: string; refreshKey?: unknown }) {
  const [rows, setRows] = useState<AuditRow[]>([]);
  useEffect(() => { api.audit(contentId).then(setRows).catch(() => setRows([])); }, [contentId, refreshKey]);
  const important = rows.filter((r) => r.event_type !== "finding_created");
  return (
    <section aria-labelledby="audit" className="space-y-2">
      <h2 id="audit" className="font-semibold">Audit trail</h2>
      {important.length === 0 && <p className="text-sm text-zinc-700">No events yet.</p>}
      <ol className="text-sm space-y-1">
        {important.map((r) => (
          <li key={r.id} className="border-l-2 border-zinc-400 pl-2">
            <span className="text-xs text-zinc-700">{r.created_at?.slice(0, 19).replace("T", " ")}</span>{" "}
            <strong>{r.event_type.replace(/_/g, " ")}</strong> by {r.actor_name ?? "system"}{r.actor_role ? ` (${r.actor_role})` : ""}
            {typeof r.details?.reason === "string" && r.details.reason ? <> - reason: &ldquo;{r.details.reason}&rdquo;</> : null}
            {r.details?.override ? <strong className="text-red-800"> [override]</strong> : null}
          </li>
        ))}
      </ol>
    </section>
  );
}

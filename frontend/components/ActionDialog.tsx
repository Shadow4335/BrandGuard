"use client";

import { useEffect, useRef, useState } from "react";

export function ActionDialog({
  title, description, label, required, confirmText, danger, onConfirm, onCancel,
}: {
  title: string; description?: string; label: string; required: boolean; confirmText: string; danger?: boolean;
  onConfirm: (reason: string) => Promise<void>; onCancel: () => void;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => { ref.current?.focus(); }, []);
  const ok = !required || reason.trim().length >= 5;
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="dlg-title"
      onKeyDown={(e) => { if (e.key === "Escape") onCancel(); }}
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl p-5 w-full max-w-md space-y-3 shadow-xl">
        <h2 id="dlg-title" className="text-lg font-bold">{title}</h2>
        {description && <p className="text-sm text-zinc-800">{description}</p>}
        <label className="block text-sm font-medium">{label}{required ? " (required, min 5 characters)" : " (optional)"}
          <textarea ref={ref} rows={3} value={reason} onChange={(e) => setReason(e.target.value)} className="mt-1 w-full border border-zinc-400 rounded p-2" />
        </label>
        <div className="flex justify-end gap-2">
          <button onClick={onCancel} className="rounded border border-zinc-400 px-3 py-1.5 text-sm">Cancel</button>
          <button disabled={!ok || busy} onClick={async () => { setBusy(true); try { await onConfirm(reason); } finally { setBusy(false); } }}
            className={`rounded px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 ${danger ? "bg-red-700" : "bg-indigo-700"}`}>{confirmText}</button>
        </div>
      </div>
    </div>
  );
}

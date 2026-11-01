"use client";

import { useEffect, useState } from "react";

/** Spinner and skeleton. After a few seconds it explains that the free-tier server may still be waking up. */
export function Loading({ label = "Loading" }: { label?: string }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 5000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div role="status" aria-live="polite" className="max-w-3xl mx-auto p-6 md:p-8 space-y-4">
      <div className="flex items-center gap-3 text-zinc-800">
        <span aria-hidden className="h-5 w-5 rounded-full border-2 border-indigo-200 border-t-indigo-700 animate-spin" />
        <span>{label}…</span>
      </div>
      <div aria-hidden className="space-y-3 animate-pulse">
        <div className="h-6 w-2/3 rounded bg-zinc-200" />
        <div className="h-4 w-1/2 rounded bg-zinc-200" />
        <div className="h-28 rounded-xl bg-zinc-200" />
      </div>
      {slow && (
        <p className="text-sm text-zinc-700">
          Still working. The demo server sleeps when idle, so the first request can take up to a minute.
        </p>
      )}
    </div>
  );
}

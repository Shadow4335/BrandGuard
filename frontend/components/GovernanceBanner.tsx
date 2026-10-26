"use client";

import { AlertTriangle, ShieldCheck } from "lucide-react";

export function GovernanceBanner() {
  return (
    <div
      role="region"
      aria-label="Compliance Notice"
      className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-xs md:text-sm text-amber-700 dark:text-amber-300 flex items-center justify-between"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-center w-full">
        <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
        <span className="font-medium">
          AI-assisted review. Suggestions are never auto-applied. Not legal advice.
        </span>
      </div>
    </div>
  );
}

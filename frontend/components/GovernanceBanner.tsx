"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";

export function GovernanceBanner() {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth(null)); }, []); // also wakes the backend
  const provider = health?.ai_live ? `${health.ai_provider} (Google)` : "an AI provider when a key is configured";
  return (
    <div role="region" aria-label="AI disclosure" className="bg-amber-100 border-b border-amber-300 px-4 py-2 text-xs md:text-sm text-amber-950">
      <div className="max-w-7xl mx-auto flex items-start justify-center gap-2 text-center">
        <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
        <span>
          AI-assisted review. Suggestions need human approval and are never auto-applied. Content is sent to {provider} for analysis. Not legal advice.{" "}
          <Link href="/about-ai" className="underline font-medium">About AI</Link>
        </span>
      </div>
    </div>
  );
}

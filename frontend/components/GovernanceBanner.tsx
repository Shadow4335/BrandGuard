"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Info } from "lucide-react";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";

export function GovernanceBanner() {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth(null)); }, []); // also wakes the backend
  const NAMES: Record<string, string> = { gemini: "Google Gemini", anthropic: "Anthropic Claude", openai: "OpenAI", groq: "Groq", xai: "xAI Grok" };
  const name = (p?: string) => (p ? NAMES[p] ?? p : "");
  const provider = health?.ai_live
    ? `Review content may be sent to ${name(health.ai_provider)}${health.ai_backup ? ` or ${name(health.ai_backup)} (backup)` : ""}.`
    : health ? "Offline rule and heuristic checks are active; review content is not sent to an AI provider." : "AI provider status is not yet available. See About AI for data handling.";
  return (
    <div role="region" aria-label="AI disclosure" className="disclosure">
      <div >
        <Info className="w-4 h-4 shrink-0 mt-0.5" />
        <span>
          AI suggests. Humans decide. No automatic edits or publication. {provider} Not legal advice.{" "}
          <Link href="/about-ai" className="underline font-medium">About AI</Link>
        </span>
      </div>
    </div>
  );
}

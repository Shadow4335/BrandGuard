"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";
export default function AboutAiPage() {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => { api.health().then(setHealth).catch(() => {}); }, []);
  return (
    <div className="max-w-3xl mx-auto p-4 md:p-8 space-y-5 text-zinc-900">
      <h1 className="text-2xl font-bold">About AI in BrandGuard</h1>
      <p><strong>AI suggests, humans decide.</strong> Nothing is ever auto-edited or auto-published.</p>
      <section><h2 className="font-semibold">What the AI does</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li>Layer A (no AI): fixed rules for absolute claims, banned terms, missing disclosures, contrast and alt-text. Always high confidence.</li>
          <li>Layer B (AI): checks tone and compares claims with your approved facts, citing only sources it was given. If nothing supports a claim it is labelled <em>Unsupported claim</em>, never guessed.</li>
          <li>Suggested rewrites aim to keep the creator&apos;s intent. Creators accept, edit or reject each one.</li>
        </ul></section>
      <section><h2 className="font-semibold">What the AI does not do</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li>It does not publish, approve or change your content on its own.</li>
          <li>It does not give legal advice. Regulatory findings flag risk; people confirm.</li>
          <li>It cannot guarantee a claim is correct or that content complies with every applicable rule.</li>
        </ul></section>
      <section><h2 className="font-semibold">Providers and data</h2>
        <p role="status">{!health ? "Provider status is unavailable until the API responds." : health.ai_live ? `Configured review provider: ${health.ai_provider}${health.ai_backup ? `; backup: ${health.ai_backup}` : ""}.` : "Offline rule and heuristic checks are active. No review content is sent to an AI provider in this mode."}</p>
        <p className="mt-3">When live AI is enabled, submitted text and retrieved approved-source excerpts may be sent to configured providers. If a provider fails, another configured model or backup provider may also receive that content. Each review records the provider/model that answered or indicates offline fallback. Provider data handling depends on the service and account configuration; this app does not guarantee provider retention or training policies.</p>
        <p className="mt-3">{health?.store === "memory" ? "This server uses seeded in-memory storage. Data resets on restart." : health?.store === "supabase" ? "This server uses Supabase for accounts, database records and uploaded files. API authorization uses the verified account’s role and workspace." : "Storage status has not been confirmed."} The shared demo workspace uses the fictional GlowLeaf Naturals brand. Do not upload confidential material there.</p></section>
      <section><h2 className="font-semibold">Human control and audit</h2>
        <p>Every finding, decision, comment, approval and override is written to an append-only audit log. Anyone who approves with high-severity issues unresolved must write an override reason.</p></section>
      <p className="text-sm text-zinc-700">The demo brand &ldquo;GlowLeaf Naturals&rdquo; is fictional. See AI_AND_SERVICES.md in the repository for the full list of services, models and libraries.</p>
    </div>
  );
}

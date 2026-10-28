export default function AboutAiPage() {
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
          <li>It is not trained on your content.</li>
        </ul></section>
      <section><h2 className="font-semibold">Providers and data</h2>
        <p>By default the hosted model is Google Gemini (model set by <code>LLM_MODEL</code>), with Gemini embeddings (768 dimensions) for retrieval. When enabled, the content being reviewed and the retrieved brand-source excerpts are sent to the provider for that review only. When no API key is set, or the provider fails or times out, BrandGuard falls back to offline rule-based and keyword checks and nothing is sent. Data is stored in Supabase (Postgres, private storage) with row-level security per organisation; the app is hosted on Vercel and Render.</p></section>
      <section><h2 className="font-semibold">Human control and audit</h2>
        <p>Every finding, decision, comment, approval and override is written to an append-only audit log. A reviewer who approves with high-severity issues unresolved must write an override reason.</p></section>
      <p className="text-sm text-zinc-700">The demo brand &ldquo;GlowLeaf Naturals&rdquo; is fictional. See AI_AND_SERVICES.md in the repository for the full list of services, models and libraries.</p>
    </div>
  );
}

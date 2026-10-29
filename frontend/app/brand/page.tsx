"use client";

import { useEffect, useState } from "react";
import { RequireAuth, ErrorNote } from "@/components/RequireAuth";
import { SeverityPill } from "@/components/Pills";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import type { RuleInfo, Source, SourceType } from "@/lib/types";

const TABS: { id: string; label: string; types: SourceType[] }[] = [
  { id: "guideline", label: "Guidelines", types: ["guideline"] },
  { id: "claim_library", label: "Approved facts", types: ["claim_library"] },
  { id: "terminology", label: "Terminology", types: ["terminology"] },
  { id: "regulatory", label: "Regulatory rules", types: ["regulatory"] },
  { id: "asset", label: "Assets", types: ["asset"] },
  { id: "rules", label: "Rule library", types: [] },
];

export default function BrandPage() {
  return <RequireAuth><Brand /></RequireAuth>;
}

function Brand() {
  const { profile } = useAuth();
  const [tab, setTab] = useState("guideline");
  const [sources, setSources] = useState<Source[]>([]);
  const [rules, setRules] = useState<RuleInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", code: "", text: "" });
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const reload = () => api.sources().then(setSources).catch((e) => setError(e.message));
  useEffect(() => { reload(); api.rules().then(setRules).catch((e) => setError(e.message)); }, []);
  const current = TABS.find((t) => t.id === tab)!;
  const list = sources.filter((s) => current.types.includes(s.source_type));

  async function add(e: React.FormEvent) {
    e.preventDefault();
    const fd = new FormData();
    fd.set("kind", tab); fd.set("title", form.title); fd.set("text", form.text);
    if (form.code) fd.set("code", form.code);
    if (file) fd.set("file", file);
    setBusy(true);
    try { await api.uploadSource(fd); setForm({ title: "", code: "", text: "" }); setFile(null); await reload(); setError(null); }
    catch (err) { setError((err as Error).message); }
    finally { setBusy(false); }
  }

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-4">
      <h1 className="text-2xl font-bold">Brand sources</h1>
      <p className="text-zinc-800">Everything the review checks against. Each item has a code that appears in citations.</p>
      <ErrorNote message={error} />
      <div role="tablist" className="flex flex-wrap gap-1 border-b border-zinc-300">
        {TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)}
            className={`px-3 py-2 text-sm font-medium border-b-2 ${tab === t.id ? "border-indigo-700 text-indigo-900" : "border-transparent text-zinc-700"}`}>{t.label}</button>
        ))}
      </div>
      {tab === "rules" ? (
        <ul className="space-y-2">
          {rules.map((r) => (
            <li key={r.id} className="rounded-lg border border-zinc-300 bg-white p-3">
              <div className="flex flex-wrap items-center gap-2"><code className="text-xs bg-zinc-100 px-1.5 rounded">{r.id}</code><strong>{r.title}</strong><SeverityPill value={r.severity} /><span className="text-xs text-zinc-700">Layer {r.layer} · {r.category}</span></div>
              <p className="text-sm text-zinc-800 mt-1">{r.why}</p>
              {r.reference && <p className="text-xs text-zinc-700 mt-1">Reference: {r.reference}</p>}
            </li>
          ))}
        </ul>
      ) : (
        <>
          {list.length === 0 && <p className="rounded-lg border border-dashed border-zinc-400 p-4">No items yet.{profile?.role === "admin" ? " Add one below." : " An admin can add them."}</p>}
          <ul className="space-y-2">
            {list.map((s) => (
              <li key={s.id} className="rounded-lg border border-zinc-300 bg-white p-3">
                <button className="w-full text-left flex items-center gap-2" aria-expanded={open === s.id} onClick={() => setOpen(open === s.id ? null : s.id)}>
                  <code className="text-xs bg-zinc-100 px-1.5 rounded">{s.code}</code><strong>{s.title}</strong>
                </button>
                {open === s.id && <p className="text-sm text-zinc-800 mt-2 whitespace-pre-wrap">{s.body}</p>}
              </li>
            ))}
          </ul>
          {profile?.role === "admin" && (
            <form onSubmit={add} className="rounded-lg border border-zinc-300 bg-white p-4 space-y-2">
              <h2 className="font-semibold">Add to {current.label}</h2>
              <label className="block text-sm">Title<input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="mt-1 w-full border border-zinc-400 rounded px-2 py-1" /></label>
              <label className="block text-sm">Code (for citations, e.g. FACT-013)<input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="mt-1 w-full border border-zinc-400 rounded px-2 py-1" /></label>
              <label className="block text-sm">Text<textarea required={!file} rows={4} value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} className="mt-1 w-full border border-zinc-400 rounded px-2 py-1" /></label>
              <label className="block text-sm">...or upload a file (PDF, DOCX, image, TXT, HTML)
                <input type="file" accept=".pdf,.docx,.txt,.md,.html,.htm,image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="mt-1 w-full border border-zinc-400 rounded px-2 py-1" /></label>
              <button disabled={busy} className="rounded-lg bg-indigo-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">{busy ? "Adding..." : "Add source"}</button>
            </form>
          )}
        </>
      )}
    </div>
  );
}

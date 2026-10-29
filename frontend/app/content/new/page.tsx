"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { RequireAuth, ErrorNote } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { Channel, Sample } from "@/lib/types";

const CHANNELS: [Channel, string][] = [
  ["instagram_post", "Instagram post"], ["website_page", "Website page"], ["influencer_post", "Influencer post"],
  ["press_release", "Press release"], ["email", "Email"],
];

export default function NewContentPage() {
  return <RequireAuth roles={["creator"]}><NewContent /></RequireAuth>;
}

function NewContent() {
  const router = useRouter();
  const [samples, setSamples] = useState<Sample[]>([]);
  const [title, setTitle] = useState("");
  const [channel, setChannel] = useState<Channel>("instagram_post");
  const [ai, setAi] = useState(false);
  const [text, setText] = useState("");
  const [alt, setAlt] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.samples().then(setSamples).catch((e) => setError(e.message)); }, []);

  async function load(s: Sample, n: number) {
    setError(null);
    setTitle(s.title); setChannel(s.channel); setAi(s.ai_generated); setText(s.text); setAlt(s.alt_text); setFile(null);
    if (s.image) {
      try { const blob = await api.sampleImage(s.key); setFile(new File([blob], "summer-sale-poster.png", { type: "image/png" })); }
      catch (e) { setError((e as Error).message); }
    }
    void n;
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setError(null);
    const fd = new FormData();
    fd.set("title", title || "Untitled"); fd.set("channel", channel); fd.set("ai_generated", String(ai));
    fd.set("text", text); fd.set("alt_text", alt);
    if (file) fd.set("file", file);
    try {
      const { id } = await api.createContent(fd);
      router.push(`/content/${id}?run=1`);
    } catch (err) { setError((err as Error).message); setBusy(false); }
  }

  const input = "mt-1 w-full border border-zinc-400 rounded-lg px-3 py-2 bg-white text-zinc-900";
  return (
    <div className="max-w-3xl mx-auto p-4 md:p-8 space-y-4">
      <h1 className="text-2xl font-bold">New content</h1>
      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-3">
        <p className="text-sm font-medium mb-2">No content handy? Load a sample:</p>
        <div className="flex flex-wrap gap-2">
          {samples.map((s, i) => (
            <button key={s.key} type="button" onClick={() => load(s, i + 1)} className="rounded-lg border border-indigo-400 bg-white px-3 py-1.5 text-sm font-medium text-indigo-900 hover:bg-indigo-100">
              Load sample {i + 1}: {s.title}
            </button>
          ))}
        </div>
      </div>
      <ErrorNote message={error} />
      <form onSubmit={submit} className="space-y-4">
        <label className="block text-sm font-medium">Title<input required value={title} onChange={(e) => setTitle(e.target.value)} className={input} /></label>
        <label className="block text-sm font-medium">Channel
          <select value={channel} onChange={(e) => setChannel(e.target.value as Channel)} className={input}>
            {CHANNELS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={ai} onChange={(e) => setAi(e.target.checked)} /> This was created or assisted by AI</label>
        <label className="block text-sm font-medium">Paste text<textarea rows={7} value={text} onChange={(e) => setText(e.target.value)} className={input} /></label>
        <label className="block text-sm font-medium">...or upload a file: PDF (including scans), Word .docx, image (PNG, JPG, WEBP, GIF), TXT or HTML, up to 10 MB
          <input type="file" accept=".pdf,.docx,.txt,.md,.html,.htm,image/*" onChange={(e) => {
            const f = e.target.files?.[0] ?? null;
            if (f && f.size > 10 * 1024 * 1024) { setError("That file is larger than 10 MB. Please choose a smaller one."); e.target.value = ""; setFile(null); return; }
            setError(null); setFile(f);
          }} className={input} />
        </label>
        {file && <p className="text-sm text-zinc-800">Selected file: {file.name}{text.trim() ? " (the file is reviewed; the pasted text is used only if the file has no readable text)" : ""}</p>}
        {file?.type.startsWith("image/") && (
          <label className="block text-sm font-medium">Alt-text (describe the image)<input value={alt} onChange={(e) => setAlt(e.target.value)} className={input} /></label>
        )}
        <button disabled={busy || (!text.trim() && !file)} className="rounded-lg bg-indigo-700 text-white px-5 py-2.5 font-medium disabled:opacity-50">
          {busy ? "Creating..." : "Submit for AI review"}
        </button>
      </form>
    </div>
  );
}

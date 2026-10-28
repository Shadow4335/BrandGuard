"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { ContentDetail } from "@/lib/types";

export function CommentThread({ detail, onChange }: { detail: ContentDetail; onChange: () => void }) {
  const [body, setBody] = useState("");
  const [err, setErr] = useState<string | null>(null);
  async function add(e: React.FormEvent) {
    e.preventDefault();
    try { await api.comment(detail.content.id, body); setBody(""); setErr(null); onChange(); }
    catch (x) { setErr((x as Error).message); }
  }
  return (
    <section aria-labelledby="comments" className="space-y-2">
      <h2 id="comments" className="font-semibold">Comments</h2>
      {detail.comments.length === 0 && <p className="text-sm text-zinc-700">No comments yet.</p>}
      <ul className="space-y-2">
        {detail.comments.map((c) => (
          <li key={c.id} className="rounded-lg bg-zinc-100 p-2 text-sm"><strong>{c.author_name ?? "Someone"}</strong> <span className="text-zinc-700 text-xs">{c.created_at?.slice(0, 16).replace("T", " ")}</span><br />{c.text}</li>
        ))}
      </ul>
      {err && <p role="alert" className="text-sm text-red-800">{err}</p>}
      <form onSubmit={add} className="flex gap-2">
        <label className="sr-only" htmlFor="newcomment">Add a comment</label>
        <input id="newcomment" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Add a comment" className="flex-1 border border-zinc-400 rounded px-2 py-1 text-sm" />
        <button disabled={!body.trim()} className="rounded bg-zinc-800 text-white px-3 py-1 text-sm disabled:opacity-50">Post</button>
      </form>
    </section>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { RequireAuth, ErrorNote } from "@/components/RequireAuth";
import { StatusBadge } from "@/components/Pills";
import { HighlightedText } from "@/components/HighlightedText";
import { FindingCard } from "@/components/FindingCard";
import { DiffPane } from "@/components/DiffPane";
import { CommentThread } from "@/components/CommentThread";
import { AuditTrail } from "@/components/AuditTrail";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import type { ContentDetail, Finding, FindingStatus, Source } from "@/lib/types";

export default function ContentPage() {
  return <RequireAuth><ContentView /></RequireAuth>;
}

function ContentView() {
  const { id } = useParams<{ id: string }>();
  const { profile } = useAuth();
  const [d, setD] = useState<ContentDetail | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [progress, setProgress] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [imgUrl, setImgUrl] = useState<string | null>(null);
  const [imgSize, setImgSize] = useState<[number, number] | null>(null);
  const [cmpA, setCmpA] = useState<number | null>(null);
  const [tick, setTick] = useState(0);
  const autoRan = useRef(false);

  const load = useCallback(async () => {
    try { const x = await api.content(id); setD(x); setTick((t) => t + 1); return x; }
    catch (e) { setError((e as Error).message); return null; }
  }, [id]);

  useEffect(() => { load(); api.sources().then(setSources).catch(() => {}); }, [load]);
  useEffect(() => {
    if (d?.has_image) api.imageUrl(id, d.content.current_version).then(setImgUrl).catch(() => setImgUrl(null));
  }, [d?.has_image, d?.content.current_version, id]);

  const runReview = useCallback(async () => {
    setRunning(true); setError(null); setNotice(null); setProgress(["Starting review..."]);
    try {
      await api.reviewStream(id, (ev) => {
        if (ev.stage === "error") setError(ev.message);
        else if (ev.stage === "done") { if (ev.result?.notice) setNotice(ev.result.notice); }
        setProgress((p) => [...p, ev.message]);
      });
      await load();
    } catch (e) { setError((e as Error).message); }
    finally { setRunning(false); }
  }, [id, load]);

  useEffect(() => {
    if (d && !autoRan.current && typeof window !== "undefined" && window.location.search.includes("run=1")
        && d.findings.length === 0 && profile?.role === "creator") {
      autoRan.current = true;
      runReview();
    }
  }, [d, profile, runReview]);

  const cur = d?.versions.find((v) => v.version_number === d.content.current_version);
  const findings = useMemo(() => d?.findings ?? [], [d]);
  const isOwner = profile?.role === "creator";
  const editable = !!d && isOwner && ["draft", "checked", "changes_requested", "rejected", "approved"].includes(d.content.status);
  const decidedCount = findings.filter((f) => f.status === "accepted" || f.status === "edited").length;
  const openHigh = findings.filter((f) => f.severity === "high" && (f.status === "open" || f.status === "rejected")).length;

  async function decide(f: Finding, decision: FindingStatus, text?: string, reason?: string) {
    try { await api.decide(f.id, decision, text, reason); await load(); }
    catch (e) { setError((e as Error).message); }
  }
  async function saveVersion() {
    try { setError(null); const x = await api.saveVersion(id); setD(x); setCmpA(null); setTick((t) => t + 1); setNotice(`Saved as version ${x.content.current_version} and re-checked.`); }
    catch (e) { setError((e as Error).message); }
  }
  async function submitForReview() {
    try { setError(null); setD(await api.transition(id, "submit")); setTick((t) => t + 1); }
    catch (e) { setError((e as Error).message); }
  }

  if (!d || !cur) return <div className="p-8">{error ? <ErrorNote message={error} /> : "Loading..."}</div>;
  const prev = d.versions.find((v) => v.version_number === (cmpA ?? d.content.current_version - 1));

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6">
      <header className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">{d.content.title}</h1>
        <StatusBadge status={d.content.status} />
        <span className="text-sm text-zinc-700">v{d.content.current_version} · {d.content.channel.replace("_", " ")}{d.content.ai_generated ? " · AI-assisted" : ""}</span>
        <div className="ml-auto flex gap-2">
          {editable && <button onClick={runReview} disabled={running} className="rounded-lg border border-indigo-700 text-indigo-900 bg-white px-4 py-2 text-sm font-medium disabled:opacity-50">{findings.length ? "Re-run review" : "Run AI review"}</button>}
          {d.allowed_actions.includes("submit") && <button onClick={submitForReview} className="rounded-lg bg-indigo-700 text-white px-4 py-2 text-sm font-medium">Submit for review</button>}
        </div>
      </header>

      <ErrorNote message={error} />
      {notice && <p role="status" className="rounded-lg border border-amber-400 bg-amber-50 text-amber-950 p-3 text-sm">{notice}</p>}
      {running && (
        <ol aria-live="polite" className="rounded-lg border border-indigo-300 bg-indigo-50 p-3 text-sm space-y-1">
          {progress.map((p, i) => <li key={i}>{i === progress.length - 1 ? "⏳" : "✔"} {p}</li>)}
        </ol>
      )}
      {d.latest_run?.used_fallback && !running && !notice && (
        <p role="status" className="rounded-lg border border-amber-400 bg-amber-50 text-amber-950 p-3 text-sm">AI layer unavailable: showing rule-based results plus offline claim and tone checks.</p>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <section aria-labelledby="content-h" className="rounded-xl border border-zinc-300 bg-white p-4 space-y-3 self-start">
          <h2 id="content-h" className="font-semibold">Content (version {cur.version_number})</h2>
          {imgUrl && (
            <div className="relative inline-block max-w-full">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={imgUrl} alt={cur.alt_text || "Uploaded image (no alt-text yet)"} className="max-w-full rounded border border-zinc-300"
                onLoad={(e) => setImgSize([e.currentTarget.naturalWidth, e.currentTarget.naturalHeight])} />
              {imgSize && findings.filter((f) => f.region).map((f) => (
                <button key={f.id} aria-label={`Region: ${f.issue}`} onClick={() => setSelected(f.id)}
                  style={{ left: `${(f.region!.x / imgSize[0]) * 100}%`, top: `${(f.region!.y / imgSize[1]) * 100}%`,
                           width: `${(f.region!.w / imgSize[0]) * 100}%`, height: `${(f.region!.h / imgSize[1]) * 100}%` }}
                  className={`absolute border-2 border-red-700 bg-red-500/20 ${selected === f.id ? "ring-2 ring-indigo-700" : ""}`} />
              ))}
            </div>
          )}
          {cur.alt_text ? <p className="text-sm">Alt-text: {cur.alt_text}</p> : imgUrl ? <p className="text-sm text-red-800">No alt-text</p> : null}
          {cur.raw_text
            ? <HighlightedText text={cur.raw_text} findings={findings} selectedId={selected} onSelect={setSelected} />
            : !imgUrl && <p className="text-sm text-zinc-700">No text was found in this content.</p>}
          {findings.length > 0 && <p className="text-xs text-zinc-700">Click a highlight to jump to its card. Nothing changes until you save a new version.</p>}
        </section>

        <section aria-labelledby="findings-h" className="space-y-3">
          <h2 id="findings-h" className="font-semibold">Findings ({findings.length})</h2>
          {findings.length === 0 && !running && (
            <p className="rounded-lg border border-dashed border-zinc-400 p-4">
              {d.latest_run ? "No issues found. This looks on-brand." : "No review yet. Click Run AI review to check this against your brand sources."}
            </p>
          )}
          {findings.map((f) => (
            <div key={f.id} id={`f-${f.id}`} ref={(el) => { if (el && selected === f.id) el.scrollIntoView({ block: "nearest", behavior: "smooth" }); }}>
              <FindingCard f={f} sources={sources} selected={selected === f.id} canDecide={editable}
                onSelect={() => setSelected(f.id)} onDecide={(dec, t, r) => decide(f, dec, t, r)} />
            </div>
          ))}
          {editable && findings.length > 0 && (
            <div className="rounded-lg border border-zinc-300 bg-white p-3 flex flex-wrap items-center gap-3">
              <button onClick={saveVersion} disabled={decidedCount === 0} className="rounded-lg bg-emerald-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">Save as new version</button>
              <span className="text-sm text-zinc-800">{decidedCount} accepted/edited · {openHigh} high-severity still open</span>
            </div>
          )}
        </section>
      </div>

      <section aria-labelledby="versions-h" className="space-y-2">
        <h2 id="versions-h" className="font-semibold">Version history</h2>
        <div className="flex flex-wrap gap-2 text-sm">
          {d.versions.map((v) => <span key={v.id} className="rounded border border-zinc-300 bg-white px-2 py-1">v{v.version_number}: {v.note}</span>)}
        </div>
        {prev && prev.version_number < cur.version_number ? (
          <DiffPane oldText={prev.raw_text ?? ""} newText={cur.raw_text ?? ""} oldLabel={`v${prev.version_number}`} newLabel={`v${cur.version_number}`} />
        ) : <p className="text-sm text-zinc-700">Save a new version to see what changed.</p>}
        {d.versions.length > 2 && (
          <label className="text-sm">Compare from version{" "}
            <select value={prev?.version_number} onChange={(e) => setCmpA(Number(e.target.value))} className="border border-zinc-400 rounded px-1">
              {d.versions.filter((v) => v.version_number < cur.version_number).map((v) => <option key={v.id} value={v.version_number}>v{v.version_number}</option>)}
            </select>
          </label>
        )}
      </section>

      <div className="grid md:grid-cols-2 gap-6">
        <CommentThread detail={d} onChange={load} />
        <AuditTrail contentId={id} refreshKey={tick} />
      </div>
    </div>
  );
}

"use client";

import { hasTextChange, isUnresolvedHigh } from "@/lib/findings";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { RequireAuth, ErrorNote, LoadFailed } from "@/components/RequireAuth";
import { StatusBadge } from "@/components/Pills";
import { HighlightedText } from "@/components/HighlightedText";
import { FindingCard } from "@/components/FindingCard";
import { DiffPane } from "@/components/DiffPane";
import { CommentThread } from "@/components/CommentThread";
import { AuditTrail } from "@/components/AuditTrail";
import { Loading } from "@/components/Loading";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import type { Approval, ContentDetail, Finding, FindingStatus, Source } from "@/lib/types";

const ROLE_NAMES: Record<string, string> = { manager: "The brand manager", reviewer: "The authorised reviewer" };

/** What the creator should do next, in one line, so nobody has to guess from the status badge. */
function nextStep(status: string, findings: number, openHigh: number, last?: Approval): string | null {
  const said = last?.reason ? `: \u201c${last.reason}\u201d` : ".";
  const who = ROLE_NAMES[last?.role ?? ""] ?? "A reviewer";
  const fix = findings ? "Accept, edit or reject the findings below, save a new version, then submit again." : "Re-run the review, then submit again.";
  switch (status) {
    case "checked": return openHigh
      ? `Next: choose Accept, Edit or Reject on each finding, save a new version, then submit for review. ${openHigh} high-severity ${openHigh === 1 ? "finding is" : "findings are"} still open.`
      : "Next: submit for review. A brand manager decides from there.";
    case "pending_manager": return "With the brand manager. Editing is locked until a decision comes back.";
    case "escalated": return "Escalated to the authorised reviewer. Editing is locked until a decision comes back.";
    case "changes_requested": return `${who} requested changes${said} ${fix}`;
    case "rejected": return `${who} rejected this${said} ${fix}`;
    case "approved": return "Approved. BrandGuard never publishes anything itself; publishing is up to you. Saving a new version sends it back through review.";
    default: return null;
  }
}

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
  const [alt, setAlt] = useState("");
  const [saving, setSaving] = useState<null | "version" | "submit">(null);
  const autoRan = useRef(false);

  const load = useCallback(async () => {
    try { const x = await api.content(id); setD(x); setTick((t) => t + 1); return x; }
    catch (e) { setError((e as Error).message); return null; }
  }, [id]);

  useEffect(() => { let active = true; Promise.resolve().then(() => { if (active) return load(); }); api.sources().then(setSources).catch(() => {}); return () => { active = false; }; }, [load]);
  useEffect(() => {
    if (d?.has_image) api.imageUrl(id, d.content.current_version).then(setImgUrl).catch(() => setImgUrl(null));
  }, [d?.has_image, d?.content.current_version, id]);

  const runReview = useCallback(async () => {
    setRunning(true); setError(null); setNotice(null); setProgress([]);
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
        && !d.latest_run && profile?.role === "creator") {
      autoRan.current = true;
      window.history.replaceState(null, "", window.location.pathname); // a refresh must not start another review
      runReview();
    }
  }, [d, profile, runReview]);

  const cur = d?.versions.find((v) => v.version_number === d.content.current_version);
  // Reading order (then severity), so cards don't jump around when a decision is saved
  const findings = useMemo(() => {
    const rank = { high: 0, medium: 1, low: 2 } as const;
    return [...(d?.findings ?? [])].sort((a, b) =>
      (a.span?.start ?? 1e9) - (b.span?.start ?? 1e9) || rank[a.severity] - rank[b.severity] || a.id.localeCompare(b.id));
  }, [d]);
  const isOwner = profile?.role === "creator";
  const editable = !!d && isOwner && ["draft", "checked", "changes_requested", "rejected", "approved"].includes(d.content.status);
  const decidedCount = findings.filter(hasTextChange).length;
  const openHigh = findings.filter(isUnresolvedHigh).length;

  async function decide(f: Finding, decision: FindingStatus, text?: string, reason?: string) {
    try { setError(null); await api.decide(f.id, decision, text, reason); await load(); }
    catch (e) { setError((e as Error).message); }
  }
  async function saveVersion() {
    if (saving) return;
    setSaving("version");
    try { setError(null); const x = await api.saveVersion(id); setD(x); setCmpA(null); setTick((t) => t + 1); setNotice(`Saved as version ${x.content.current_version} and re-checked.`); }
    catch (e) { setError((e as Error).message); }
    finally { setSaving(null); }
  }
  async function saveAltText() {
    if (saving) return;
    setSaving("version");
    try { setError(null); const x = await api.saveVersion(id, "Added alt-text", alt.trim()); setD(x); setAlt(""); setTick((t) => t + 1); setNotice(`Alt-text saved as version ${x.content.current_version} and re-checked.`); }
    catch (e) { setError((e as Error).message); }
    finally { setSaving(null); }
  }
  async function submitForReview() {
    if (saving) return;
    setSaving("submit");
    try {
      setError(null); setD(await api.transition(id, "submit")); setTick((t) => t + 1);
      const stillOpen = openHigh ? ` ${openHigh} high-severity ${openHigh === 1 ? "finding is" : "findings are"} still open, and the manager and reviewer will see that.` : "";
      setNotice(`Submitted for manager review.${stillOpen} Editing is locked until a decision comes back; this page will show it.`);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    catch (e) { setError((e as Error).message); }
    finally { setSaving(null); }
  }

  if (!d || !cur) return error ? <LoadFailed message={error} /> : <Loading label="Loading content" />;
  const hint = isOwner && !running ? nextStep(d.content.status, findings.length, openHigh, d.approvals[d.approvals.length - 1]) : null;
  const prev = d.versions.find((v) => v.version_number === (cmpA ?? d.content.current_version - 1));

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6">
      <header className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">{d.content.title}</h1>
        <StatusBadge status={d.content.status} />
        <span className="text-sm text-zinc-700">v{d.content.current_version} · {d.content.channel.replace("_", " ")}{d.content.ai_generated ? " · AI-assisted" : ""}</span>
        <div className="ml-auto flex gap-2">
          {editable && <button onClick={runReview} disabled={running || !!saving} className="rounded-lg border border-indigo-700 text-indigo-900 bg-white px-4 py-2 text-sm font-medium disabled:opacity-50">{d.latest_run ? "Re-run review" : "Run AI review"}</button>}
          {d.allowed_actions.includes("submit") && <button onClick={submitForReview} disabled={running || !!saving} className="rounded-lg bg-indigo-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">{saving === "submit" ? "Submitting…" : "Submit for review"}</button>}
        </div>
      </header>

      <ErrorNote message={error} />
      {hint && <p className="rounded-lg border border-indigo-300 bg-indigo-50 p-3 text-sm font-medium">{hint}</p>}
      {notice && <p role="status" className="rounded-lg border border-amber-400 bg-amber-50 text-amber-950 p-3 text-sm">{notice}</p>}
      {running && (
        <ol aria-live="polite" className="rounded-lg border border-indigo-300 bg-indigo-50 p-3 text-sm space-y-1">
          {(progress.length ? progress : ["Starting review..."]).map((p, i, all) => <li key={i}>{i === all.length - 1 ? "⏳" : "✔"} {p}</li>)}
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
          {imgUrl && editable && (
            <div className="flex flex-wrap items-end gap-2">
              <label className="text-sm font-medium flex-1 min-w-[12rem]">{cur.alt_text ? "Change alt-text" : "Add alt-text"}
                <input value={alt} onChange={(e) => setAlt(e.target.value)} placeholder="Describe the image and any text in it"
                  className="mt-1 w-full border border-zinc-400 rounded px-2 py-1 text-sm" />
              </label>
              <button onClick={saveAltText} disabled={alt.trim().length < 5 || !!saving} className="rounded-lg bg-emerald-700 text-white px-3 py-1.5 text-sm font-medium disabled:opacity-50">Save as new version</button>
            </div>
          )}
          {cur.file_path && !d.has_image && (
            <p className="text-xs text-zinc-700">Text extracted from <strong>{cur.file_path.split("/").pop()?.replace(/^[0-9a-f]{8}-/, "")}</strong> ({cur.file_type === "docx" ? "Word document" : cur.file_type}).</p>
          )}
          {cur.note && /^(Scanned|No )/.test(cur.note) && <p role="status" className="text-sm rounded border border-amber-400 bg-amber-50 p-2">{cur.note}</p>}
          {cur.raw_text
            ? <HighlightedText text={cur.raw_text} findings={findings} selectedId={selected} onSelect={setSelected} />
            : !imgUrl && <p className="text-sm text-zinc-700">No text was found in this content.</p>}
          {findings.length > 0 && <p className="text-xs text-zinc-700">Click a highlight to jump to its card. Nothing changes until you save a new version.</p>}
        </section>

        <section aria-labelledby="findings-h" className="space-y-3">
          <h2 id="findings-h" className="font-semibold">Findings ({running ? "checking…" : findings.length})</h2>
          {running && findings.length === 0 && <p className="rounded-lg border border-dashed border-indigo-300 bg-indigo-50 p-4 text-sm">Your findings appear here as soon as the checks finish, usually within 30 seconds.</p>}
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
              <button onClick={saveVersion} disabled={decidedCount === 0 || !!saving || running} className="rounded-lg bg-emerald-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">{saving === "version" ? "Saving and re-checking…" : "Save as new version"}</button>
              <span className="text-sm text-zinc-800">{decidedCount === 0 ? "Accept or edit a suggestion to enable saving. " : ""}{decidedCount} accepted/edited · {openHigh} high-severity still open</span>
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

"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, ChevronDown, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Organisation } from "@/lib/types";

export function WorkspaceSelector() {
  const router = useRouter();
  const { profile, switchWorkspace } = useAuth();
  const [workspaces, setWorkspaces] = useState<Organisation[] | null>(null);
  const [canCreate, setCanCreate] = useState(false), [membershipMode, setMembershipMode] = useState("");
  const [error, setError] = useState(""), [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false), [adding, setAdding] = useState(false);
  const [name, setName] = useState(""), [description, setDescription] = useState("");
  const root = useRef<HTMLDivElement>(null), trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => { let active = true; api.workspaces().then((r) => { if (active) { setWorkspaces(r.workspaces); setCanCreate(r.can_create); setMembershipMode(r.membership_mode); } }).catch((e) => { if (active) setError(e.message); }); return () => { active = false; }; }, [profile?.id, profile?.org_id, profile?.role]);
  useEffect(() => {
    if (!open) return;
    const outside = (e: PointerEvent) => { if (!root.current?.contains(e.target as Node)) { setOpen(false); setAdding(false); } };
    document.addEventListener("pointerdown", outside);
    root.current?.querySelector<HTMLButtonElement>('[role="menuitem"]')?.focus();
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);
  function close() { setOpen(false); setAdding(false); trigger.current?.focus(); }
  async function select(id: string) {
    setBusy(true); setError("");
    try { await switchWorkspace(id); close(); router.push("/dashboard"); } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  const current = workspaces?.find((w) => w.id === profile?.org_id);
  return <div className="workspace-selector" ref={root} onKeyDown={(e) => {
    if (e.key === "Escape") { e.preventDefault(); close(); }
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key) && open && !adding) {
      const buttons = Array.from(root.current!.querySelectorAll<HTMLButtonElement>('[role="menuitem"]:not(:disabled)'));
      const at = buttons.indexOf(document.activeElement as HTMLButtonElement);
      const next = e.key === "Home" ? 0 : e.key === "End" ? buttons.length - 1 : (at + (e.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length;
      e.preventDefault(); buttons[next]?.focus();
    }
  }}>
    <button ref={trigger} className="workspace-trigger" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen(!open)}>
      <span className="workspace-initials">{current?.name.split(" ").slice(0, 2).map((w) => w[0]).join("") || "…"}</span>
      <span><strong>{current?.name || (error ? "Workspace unavailable" : "Loading workspace…")}</strong><small>Brand workspace</small></span><ChevronDown size={14} />
    </button>
    {open && <div className="workspace-popover">
      <div role="menu" aria-label="Workspaces">
        {current && <button role="menuitem" onClick={close}><span>{current.name}</span><Check size={16} /></button>}
        <hr /><p className="eyebrow">Other workspaces</p>
        {workspaces?.filter((w) => w.id !== current?.id).map((w) => <button role="menuitem" key={w.id} disabled={busy} onClick={() => select(w.id)}>{w.name}</button>)}
        {workspaces?.length === 1 && <p>No other workspace memberships.</p>}
        <button role="menuitem" disabled={busy} onClick={() => setAdding(!adding)} aria-expanded={adding}><Plus size={16} /> Add workspace</button>
      </div>
      {error && <p role="alert">{error}</p>}
      {adding && <form className="workspace-add" onSubmit={async (e) => {
        e.preventDefault(); setBusy(true); setError("");
        try { const created = await api.createWorkspace(name.trim(), description.trim()); setWorkspaces((ws) => [...(ws ?? []), created]); setName(""); setDescription(""); await switchWorkspace(created.id); close(); router.push("/dashboard"); }
        catch (err) { setError((err as Error).message); } finally { setBusy(false); }
      }}>
        <label>Workspace name<input required maxLength={80} disabled={!canCreate || busy} value={name} onChange={(e) => setName(e.target.value)} placeholder="Workspace name" /></label>
        <label>Description<textarea maxLength={500} disabled={!canCreate || busy} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What is this workspace for?" /></label>
        {!canCreate && <p role="status">{membershipMode === "single_workspace" ? "Workspace creation needs the optional workspace-membership migration. Ask your server admin." : "Only an Admin can create a workspace. Ask your admin for access."}</p>}
        <button type="submit" disabled={!canCreate || busy || !name.trim()}>{busy ? "Creating…" : "Create workspace"}</button>
      </form>}
    </div>}
  </div>;
}

import { createClient } from "@/lib/supabase";
import type {
  AuditRow, ContentDetail, Finding, FindingStatus, Health, InsightsSummary, QueueItem,
  ReviewResult, RuleInfo, Sample, Source, UnclearRule, WorkflowAction,
} from "@/lib/types";

// Tolerate trailing slashes or stray punctuation in the env var (a "//api/..." path 404s on the server)
export const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim().replace(/[/.\s]+$/, "");
const DEMO_KEY = "bg_demo_session";

export interface DemoSession {
  token: string; user_id: string; email: string; org_id: string; role: string; full_name?: string | null;
}

export function getDemoSession(): DemoSession | null {
  try {
    const raw = typeof window !== "undefined" ? window.localStorage.getItem(DEMO_KEY) : null;
    return raw ? (JSON.parse(raw) as DemoSession) : null;
  } catch { return null; }
}
export function setDemoSession(s: DemoSession | null) {
  try {
    if (s) window.localStorage.setItem(DEMO_KEY, JSON.stringify(s));
    else window.localStorage.removeItem(DEMO_KEY);
  } catch { /* storage may be blocked; session then lasts only for this page */ }
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

async function token(): Promise<string | null> {
  const demo = getDemoSession();
  if (demo) return demo.token;
  const { data } = await createClient().auth.getSession();
  return data.session?.access_token ?? null;
}

async function authHeaders(json = true): Promise<Record<string, string>> {
  const t = await token();
  return { ...(json ? { "Content-Type": "application/json" } : {}), ...(t ? { Authorization: `Bearer ${t}` } : {}) };
}

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = "Something went wrong. Please try again.";
    try { const j = await res.json(); if (typeof j.detail === "string") msg = j.detail; } catch { /* keep default */ }
    if (res.status === 401) msg = "Your session expired. Please sign in again.";
    throw new ApiError(msg, res.status);
  }
  return res.json() as Promise<T>;
}

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method, headers: await authHeaders(), body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Can't reach the BrandGuard server. It may be waking up; wait a few seconds and retry.", 0);
  }
  return parse<T>(res);
}

async function upload<T>(path: string, form: FormData): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { method: "POST", headers: await authHeaders(false), body: form });
  } catch {
    throw new ApiError("Can't reach the BrandGuard server. It may be waking up; wait a few seconds and retry.", 0);
  }
  return parse<T>(res);
}

export const api = {
  health: async (): Promise<Health> => {
    const res = await fetch(`${API_BASE}/api/health`);
    return parse<Health>(res);
  },
  demoLogin: (role: string) => call<DemoSession>("POST", "/api/auth/demo-login", { role }),

  sources: () => call<Source[]>("GET", "/api/sources"),
  uploadSource: (form: FormData) => upload<Source>("/api/sources", form),
  rules: () => call<RuleInfo[]>("GET", "/api/rules"),

  samples: () => call<Sample[]>("GET", "/api/samples"),
  sampleImage: async (key: string): Promise<Blob> => {
    const res = await fetch(`${API_BASE}/api/samples/${key}/image`, { headers: await authHeaders(false) });
    if (!res.ok) throw new ApiError("Couldn't load the sample image.", res.status);
    return res.blob();
  },
  contentList: () => call<QueueItem[]>("GET", "/api/content"),
  createContent: (form: FormData) => upload<{ id: string }>("/api/content", form),
  content: (id: string) => call<ContentDetail>("GET", `/api/content/${id}`),
  imageUrl: async (id: string, version: number): Promise<string> => {
    const res = await fetch(`${API_BASE}/api/content/${id}/image?version=${version}`, { headers: await authHeaders(false) });
    if (!res.ok) throw new ApiError("Couldn't load the image.", res.status);
    return URL.createObjectURL(await res.blob());
  },
  review: (id: string) => call<ReviewResult>("POST", `/api/content/${id}/review`),
  /** Streams progress events (SSE over fetch so the auth header can be sent). */
  reviewStream: async (id: string, onEvent: (e: { stage: string; message: string; result?: ReviewResult }) => void) => {
    let res: Response;
    try {
      res = await fetch(`${API_BASE}/api/content/${id}/review/stream`, { method: "POST", headers: await authHeaders() });
    } catch {
      throw new ApiError("Can't reach the BrandGuard server. It may be waking up; wait a few seconds and retry.", 0);
    }
    if (!res.ok || !res.body) { await parse(res); return; }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n\n")) >= 0) {
        const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
        const line = chunk.split("\n").find((l) => l.startsWith("data:"));
        if (line) {
          const ev = JSON.parse(line.slice(5).trim());
          onEvent(ev);
          // Don't wait for the connection to close: proxies can hold it open after the last event
          if (ev.stage === "done" || ev.stage === "error") { await reader.cancel().catch(() => {}); return; }
        }
      }
    }
  },
  decide: (findingId: string, decision: FindingStatus, decision_text?: string, reason?: string) =>
    call<Finding>("PATCH", `/api/findings/${findingId}`, { decision, decision_text, reason }),
  saveVersion: (id: string, note?: string, alt_text?: string) =>
    call<ContentDetail>("POST", `/api/content/${id}/versions`, { note, alt_text }),
  comment: (id: string, body: string, finding_id?: string) =>
    call<unknown>("POST", `/api/content/${id}/comments`, { body, finding_id }),
  transition: (id: string, action: WorkflowAction, reason?: string, override = false) =>
    call<ContentDetail>("POST", `/api/content/${id}/transition`, { action, reason, override }),
  queue: () => call<QueueItem[]>("GET", "/api/reviews/queue"),
  audit: (contentId: string) => call<AuditRow[]>("GET", `/api/audit?content_id=${contentId}`),
  insights: () => call<InsightsSummary>("GET", "/api/insights/summary"),
  unclear: () => call<UnclearRule[]>("GET", "/api/insights/unclear-rules"),
};

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { API_BASE } from "@/lib/api";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Sparkles,
  Layers,
  FileCheck,
  Lock,
  ArrowRight,
  UserCheck,
} from "lucide-react";

interface HealthData {
  status: string;
  service: string;
  ai_provider?: string;
  ai_live?: boolean;
  store?: string;
}

export default function HomePage() {
  const { user, profile, loading } = useAuth();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [healthStatus, setHealthStatus] = useState<"loading" | "ok" | "error">("loading");
  const [healthLatency, setHealthLatency] = useState<number | null>(null);

  const fetchHealth = async () => {
    setHealthStatus("loading");
    const startTime = performance.now();
    try {
      // First request can take up to a minute if the free-tier API was asleep
      const res = await fetch(`${API_BASE}/api/health`, {
        cache: "no-store",
      });
      const latency = Math.round(performance.now() - startTime);
      setHealthLatency(latency);

      if (res.ok) {
        const data = await res.json();
        setHealth(data);
        setHealthStatus(data.status === "ok" ? "ok" : "error");
      } else {
        setHealthStatus("error");
      }
    } catch {
      setHealthStatus("error");
      setHealth(null);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const getRoleColor = (role?: string) => {
    switch (role) {
      case "admin":
        return "text-purple-600 dark:text-purple-400 bg-purple-500/10 border-purple-500/30";
      case "creator":
        return "text-blue-600 dark:text-blue-400 bg-blue-500/10 border-blue-500/30";
      case "manager":
        return "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
      case "reviewer":
        return "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/30";
      default:
        return "text-zinc-600 dark:text-zinc-400 bg-zinc-500/10 border-zinc-500/30";
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Welcome / Role Banner */}
      {!loading && user ? (
        <section className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                Welcome back, {profile?.full_name || user.email?.split("@")[0]}
              </h1>
              <span
                className={`px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full border ${getRoleColor(
                  profile?.role
                )}`}
              >
                {profile?.role || "Active User"}
              </span>
            </div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Tenant: <strong className="text-zinc-900 dark:text-zinc-200">Demo Brand</strong> &bull; Authenticated via Supabase Auth &bull; Session scoped with RLS
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-500 dark:text-zinc-400">Current Role:</span>
            <span className="text-xs font-mono font-medium px-2 py-1 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200">
              {profile?.role || "creator"}
            </span>
          </div>
        </section>
      ) : (
        <section className="p-6 rounded-2xl bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 border border-indigo-500/20 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              BrandGuard Governance Console
            </h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Deterministic rule checks (Layer A) + Grounded LLM validation (Layer B).
            </p>
          </div>
          <Link
            href="/login"
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition shadow-sm inline-flex items-center gap-2"
          >
            <span>Sign in with Demo Role</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </section>
      )}

      {/* Backend API Health Status Card */}
      <section className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-700 dark:text-zinc-300">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                Backend System Status
              </h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Checks the BrandGuard API at <code className="font-mono text-zinc-700 dark:text-zinc-300">GET /api/health</code>
              </p>
            </div>
          </div>
          <button
            onClick={fetchHealth}
            disabled={healthStatus === "loading"}
            className="p-2 rounded-lg text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition"
            title="Refresh status"
          >
            <RefreshCw className={`w-4 h-4 ${healthStatus === "loading" ? "animate-spin" : ""}`} />
          </button>
        </div>

        <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {healthStatus === "ok" ? (
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <span className="font-bold text-sm text-emerald-600 dark:text-emerald-400 tracking-wide">
                  API OK
                </span>
              </div>
            ) : healthStatus === "loading" ? (
              <div className="flex items-center gap-2 text-zinc-500 text-sm">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Checking backend health...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                <XCircle className="w-4 h-4" />
                <span>Can't reach the BrandGuard server. It may be waking up (the free tier sleeps when idle); wait a few seconds and press refresh.</span>
              </div>
            )}
          </div>

          {health && (
            <div className="flex items-center gap-4 text-xs text-zinc-600 dark:text-zinc-400 font-mono">
              <span>Service: <strong className="text-zinc-900 dark:text-zinc-200">{health.service}</strong></span>
              <span>AI: <strong className="text-zinc-900 dark:text-zinc-200">{health.ai_live ? health.ai_provider : "offline fallback"}</strong></span>
              {healthLatency !== null && (
                <span>Latency: <strong className="text-zinc-900 dark:text-zinc-200">{healthLatency}ms</strong></span>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Governance Architecture Cards */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-600 dark:text-purple-400 flex items-center justify-center">
            <FileCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-zinc-900 dark:text-zinc-100">
            Layer A: Rule-Based Engine
          </h3>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Deterministic evaluation using Python regex and RapidFuzz against YAML rule sets. Flags prohibited claims and missing disclosures with high confidence.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-zinc-900 dark:text-zinc-100">
            Layer B: Grounded AI RAG
          </h3>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Semantic grounding via 768-dimensional pgvector embeddings. Strict rule: Layer B may only cite verified, retrieved source IDs.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <Lock className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-zinc-900 dark:text-zinc-100">
            Tenant Isolation & Audit Trail
          </h3>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Supabase RLS on all tables scoped by <code>org_id</code>. Append-only audit log enforced by database trigger—no updates or deletions allowed.
          </p>
        </div>
      </section>
    </div>
  );
}

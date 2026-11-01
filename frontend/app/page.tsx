"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, FileSearch, History, MessageSquareWarning, RefreshCw, ShieldCheck, UserCheck } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { API_BASE } from "@/lib/api";

const HOW_IT_WORKS = [
  { icon: FileSearch, title: "Submit", text: "Paste text or upload a PDF, Word file or image, and pick the channel." },
  { icon: MessageSquareWarning, title: "Check", text: "Rules and grounded AI flag risky claims, banned terms, missing disclosures and contrast problems, each with the reason and a fix." },
  { icon: UserCheck, title: "Decide", text: "You accept, edit or reject every suggestion. Nothing is changed for you." },
  { icon: CheckCircle2, title: "Approve", text: "A manager approves or escalates to a reviewer, and every step is recorded." },
];

const PROMISES = [
  { icon: ShieldCheck, title: "Grounded, never guessing", text: "The AI may only cite your uploaded sources. If nothing supports a claim, it says so." },
  { icon: UserCheck, title: "People stay in charge", text: "Suggestions are never auto-applied and nothing is auto-published." },
  { icon: History, title: "Every step on record", text: "An append-only audit trail shows who decided what, and why." },
];

type ServiceState = "loading" | "ok" | "error";

export default function HomePage() {
  const { user, loading } = useAuth();
  const [service, setService] = useState<ServiceState>("loading");
  const [latency, setLatency] = useState<number | null>(null);

  const checkService = useCallback(async () => {
    const started = performance.now();
    try {
      // The free-tier API sleeps when idle, so this first request can take up to a minute
      const res = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
      const body = res.ok ? await res.json() : null;
      setLatency(Math.round(performance.now() - started));
      setService(body?.status === "ok" ? "ok" : "error");
    } catch {
      setService("error");
    }
  }, []);
  useEffect(() => { checkService(); }, [checkService]); // starts as "loading", so nothing is set before the reply
  const recheck = () => { setService("loading"); checkService(); };

  const signedIn = !loading && !!user;
  const dot = service === "ok" ? "bg-emerald-600" : service === "error" ? "bg-red-600" : "bg-amber-500 animate-pulse";

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 md:py-16 space-y-14">
      <section className="space-y-6 max-w-3xl">
        <p className="inline-flex items-center gap-2 text-sm font-medium text-indigo-900 bg-indigo-50 border border-indigo-200 rounded-full px-3 py-1">
          <ShieldCheck className="w-4 h-4" aria-hidden /> Pre-publication brand governance
        </p>
        <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-zinc-950">
          Catch brand and compliance risks before you publish.
        </h1>
        <p className="text-lg text-zinc-800">
          BrandGuard checks every post, poster and press release against your approved guidelines, facts and advertising rules.
          It explains each issue, suggests a fix, and routes the content for human approval. AI suggests, humans decide.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <Link href={signedIn ? "/dashboard" : "/login"} className="inline-flex items-center gap-2 rounded-lg bg-indigo-700 px-5 py-3 font-medium text-white hover:bg-indigo-800">
            {signedIn ? "Go to your dashboard" : "Try the live demo"} <ArrowRight className="w-4 h-4" aria-hidden />
          </Link>
          {!signedIn && (
            <Link href="/signup" className="rounded-lg border border-indigo-700 px-5 py-3 font-medium text-indigo-900 hover:bg-indigo-50">Create an account</Link>
          )}
        </div>
        {!signedIn && <p className="text-sm text-zinc-700">No setup needed: pick a role on the next screen and you are in. The demo brand is a fictional personal-care company.</p>}
      </section>

      <section aria-labelledby="how-h" className="space-y-4">
        <h2 id="how-h" className="text-xl font-semibold">How it works</h2>
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {HOW_IT_WORKS.map(({ icon: Icon, title, text }, i) => (
            <li key={title} className="rounded-xl border border-zinc-300 bg-white p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-800 flex items-center justify-center"><Icon className="w-4 h-4" aria-hidden /></span>
                <h3 className="font-semibold">{i + 1}. {title}</h3>
              </div>
              <p className="text-sm text-zinc-800">{text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="trust-h" className="grid gap-4 md:grid-cols-3">
        <h2 id="trust-h" className="sr-only">Why teams trust it</h2>
        {PROMISES.map(({ icon: Icon, title, text }) => (
          <div key={title} className="rounded-xl border border-zinc-300 bg-white p-4 space-y-2">
            <Icon className="w-5 h-5 text-indigo-800" aria-hidden />
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-zinc-800">{text}</p>
          </div>
        ))}
      </section>

      <footer className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-zinc-200 pt-4 text-sm text-zinc-700" aria-live="polite">
        <span className="inline-flex items-center gap-2">
          <span aria-hidden className={`h-2.5 w-2.5 rounded-full ${dot}`} />
          {service === "ok" ? `Service online${latency !== null ? ` (${latency} ms)` : ""}`
            : service === "loading" ? "Checking the service. The free-tier server may take up to a minute to wake."
            : "Can't reach the server yet. It may be waking up; try again in a few seconds."}
        </span>
        <button onClick={recheck} disabled={service === "loading"} className="inline-flex items-center gap-1 underline disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${service === "loading" ? "animate-spin" : ""}`} aria-hidden /> Recheck
        </button>
        <Link href="/about-ai" className="underline">How the AI is used</Link>
      </footer>
    </div>
  );
}

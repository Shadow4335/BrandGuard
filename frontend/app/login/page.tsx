"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { UserRole } from "@/lib/types";
import {
  ShieldCheck,
  Eye,
  EyeOff,
  UserCheck,
  Sparkles,
  Lock,
  ArrowRight,
  AlertCircle,
} from "lucide-react";

const DEMO_ACCOUNTS: { role: UserRole; email: string; label: string; desc: string; color: string }[] = [
  {
    role: "admin",
    email: "admin@demo.test",
    label: "Admin",
    desc: "Configure rules, sources & system policies",
    color: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30 hover:bg-purple-500/20",
  },
  {
    role: "creator",
    email: "creator@demo.test",
    label: "Creator",
    desc: "Draft copy, upload assets & run checks",
    color: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30 hover:bg-blue-500/20",
  },
  {
    role: "manager",
    email: "manager@demo.test",
    label: "Manager",
    desc: "Review findings, escalate & approve drafts",
    color: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20",
  },
  {
    role: "reviewer",
    email: "reviewer@demo.test",
    label: "Reviewer",
    desc: "Legal & compliance review with justification",
    color: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30 hover:bg-amber-500/20",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { signIn, error: authError } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleManualSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLocalError(null);
    setLoading(true);

    const success = await signIn(email, password);
    setLoading(false);
    if (success) {
      router.push("/dashboard");
    }
  };

  const handleQuickSignIn = async (demoEmail: string) => {
    setLocalError(null);
    setLoading(true);
    setEmail(demoEmail);
    setPassword("BrandGuard2026!");

    const success = await signIn(demoEmail, "BrandGuard2026!");
    setLoading(false);
    if (success) {
      router.push("/dashboard");
    }
  };

  return (
    <div className="min-h-[calc(100vh-6rem)] flex flex-col justify-center items-center px-4 py-8">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400 mb-2 shadow-sm">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Sign in to BrandGuard
          </h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Pre-publication governance platform. AI suggests, humans decide.
          </p>
        </div>

        {/* Demo Accounts Panel */}
        <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 backdrop-blur-sm space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-600 dark:text-zinc-400">
            <Sparkles className="w-4 h-4 text-indigo-500" />
            <span>One-Click Demo Accounts</span>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Select a role to sign in instantly with test credentials:
          </p>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.role}
                type="button"
                onClick={() => handleQuickSignIn(acc.email)}
                disabled={loading}
                className={`p-2.5 rounded-lg border text-left transition-all duration-150 flex flex-col justify-between ${acc.color} disabled:opacity-50`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-semibold text-xs">{acc.label}</span>
                  <UserCheck className="w-3.5 h-3.5 opacity-80" />
                </div>
                <span className="text-[10px] opacity-75 mt-1 line-clamp-1">{acc.desc}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-950">
          <p className="font-semibold mb-2">Try it in 2 minutes</p>
          <ol className="list-decimal pl-5 space-y-1">
            <li>Creator: New content, Load sample 1, Submit for AI review</li>
            <li>Accept, edit or reject each suggestion, then save a new version</li>
            <li>Submit for review</li>
            <li>Manager: comment and Escalate</li>
            <li>Reviewer: Approve (an override reason is required). Then open Insights as Admin.</li>
          </ol>
          <p className="mt-2 text-xs">Demo password for all accounts: BrandGuard2026!</p>
        </div>

        {/* Form Separator */}
        <div className="relative flex items-center justify-center">
          <div className="border-t border-zinc-200 dark:border-zinc-800 w-full" />
          <span className="bg-white dark:bg-zinc-950 px-3 text-xs text-zinc-400 uppercase tracking-wider absolute">
            Or standard login
          </span>
        </div>

        {/* Standard Form */}
        <form onSubmit={handleManualSubmit} className="space-y-4" noValidate={false}>
          {(localError || authError) && (
            <div
              role="alert"
              className="p-3 text-xs rounded-lg bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 flex items-start gap-2"
            >
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{localError || authError}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label
              htmlFor="email"
              className="block text-xs font-medium text-zinc-700 dark:text-zinc-300"
            >
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 transition"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label
                htmlFor="password"
                className="block text-xs font-medium text-zinc-700 dark:text-zinc-300"
              >
                Password
              </label>
            </div>
            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2 pr-10 text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-medium text-sm shadow-sm transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span>Sign in</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

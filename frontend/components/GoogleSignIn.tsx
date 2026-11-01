"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { firebaseConfigured, loadFirebase } from "@/lib/firebase";
import type { UserRole } from "@/lib/types";

const PREPARE_TIMEOUT_MS = 5000;

/** Real Google integration, with preparation and unavailable states checked against the server. */
export function GoogleSignIn({ role, inviteCode, rolePassword, label = "Continue with Google", disabled = false, onComplete }: {
  role?: UserRole; inviteCode?: string; rolePassword?: string; label?: string; disabled?: boolean; onComplete?: () => void;
}) {
  const router = useRouter();
  const { signInWithGoogle } = useAuth();
  const [available, setAvailable] = useState(false);
  const [checked, setChecked] = useState(false);
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [prepared, setPrepared] = useState(false);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    router.prefetch("/dashboard");
    api.health().then((h) => {
      if (!active) return;
      setChecked(true);
      if (!firebaseConfigured || !h.firebase_enabled) return;
      setAvailable(true);
      timer = setTimeout(() => { if (active) setPrepared(true); }, PREPARE_TIMEOUT_MS);
      loadFirebase().catch(() => {}).finally(() => { clearTimeout(timer); if (active) setPrepared(true); });
    }).catch(() => { if (active) { setChecked(true); setFailed(true); } });
    return () => { active = false; clearTimeout(timer); };
  }, [router]);


  async function onClick() {
    setBusy(true);
    try {
      const ok = await signInWithGoogle(role, inviteCode, rolePassword);
      if (ok) router.push("/dashboard");
    } finally { setBusy(false); onComplete?.(); }
  }

  return (
    <div>
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || busy || !available || !prepared}
      aria-busy={!checked || (available && !prepared) || busy}
      className="w-full py-2.5 px-4 rounded-lg border border-zinc-300 bg-white hover:bg-zinc-50 text-zinc-900 font-medium text-sm shadow-sm transition flex items-center justify-center gap-2 disabled:opacity-50"
    >
      <GoogleLogo />
      <span>{busy ? "Signing in with Google..." : !checked || (available && !prepared) ? "Preparing Google sign-in..." : label}</span>
    </button>
    {checked && !available && <p className="mt-2 text-xs text-zinc-700" role="status">{failed ? "Google sign-in status could not be checked. Please retry after the server responds." : "Google sign-in is not configured on this server. Use email sign-in or a supported demo role."}</p>}
    </div>
  );
}

function GoogleLogo() {
  return (
    <svg aria-hidden="true" viewBox="0 0 48 48" className="w-4 h-4">
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.6 5.4 2.7 13.3l7.9 6.1C12.5 13.6 17.8 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.4c-.5 2.9-2.2 5.3-4.6 7l7.2 5.6c4.2-3.9 7.1-9.6 7.1-17.1z" />
      <path fill="#FBBC05" d="M10.6 28.6c-.5-1.4-.8-3-.8-4.6s.3-3.2.8-4.6l-7.9-6.1C1 16.6 0 20.2 0 24s1 7.4 2.7 10.7l7.9-6.1z" />
      <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.2-5.6c-2.2 1.5-5 2.4-8.7 2.4-6.2 0-11.5-4.1-13.4-9.9l-7.9 6.1C6.6 42.6 14.6 48 24 48z" />
    </svg>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { firebaseConfigured, loadFirebase } from "@/lib/firebase";
import type { UserRole } from "@/lib/types";

const PREPARE_TIMEOUT_MS = 5000;

/** "Continue with Google". Only shown when the browser has the Firebase config and the API says it's set up too. */
export function GoogleSignIn({ role, inviteCode, label = "Continue with Google" }: { role?: UserRole; inviteCode?: string; label?: string }) {
  const router = useRouter();
  const { signInWithGoogle } = useAuth();
  const [available, setAvailable] = useState(false);
  const [busy, setBusy] = useState(false);
  const [prepared, setPrepared] = useState(false);

  useEffect(() => {
    if (!firebaseConfigured) return;
    router.prefetch("/dashboard"); // so the page is ready the moment sign-in finishes
    api.health()
      .then((h) => {
        if (!h.firebase_enabled) return;
        setAvailable(true);
        // Enable the button once Firebase is fully loaded, so the click opens the popup straight away. If loading
        // fails or is slow (a slow network can hold the sign-in iframe up for a long time), enable it anyway after a
        // few seconds: the click then finishes the load first, and the popup may be blocked with a clear message.
        const giveUp = setTimeout(() => setPrepared(true), PREPARE_TIMEOUT_MS);
        loadFirebase().catch(() => {}).finally(() => { clearTimeout(giveUp); setPrepared(true); });
      })
      .catch(() => {});
  }, [router]);

  if (!available) return null;

  async function onClick() {
    setBusy(true);
    const ok = await signInWithGoogle(role, inviteCode);
    setBusy(false);
    if (ok) router.push("/dashboard");
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={busy || !prepared}
      aria-busy={!prepared || busy}
      className="w-full py-2.5 px-4 rounded-lg border border-zinc-300 bg-white hover:bg-zinc-50 text-zinc-900 font-medium text-sm shadow-sm transition flex items-center justify-center gap-2 disabled:opacity-50"
    >
      <GoogleLogo />
      <span>{busy ? "Signing in with Google..." : prepared ? label : "Preparing Google sign-in..."}</span>
    </button>
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

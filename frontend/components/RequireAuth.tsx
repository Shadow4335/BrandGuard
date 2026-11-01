"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { Loading } from "@/components/Loading";

/** Redirects to /login when signed out; renders children once a profile is loaded. */
export function RequireAuth({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { user, profile, loading, error, refreshProfile, signOut } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);
  if (loading || !user) return <Loading label="Loading your workspace" />;
  if (!profile) return <div className="max-w-xl mx-auto p-8"><ErrorNote message={error || "Could not load your workspace. Please retry."} /><div className="flex gap-3"><button className="rounded-lg border px-4 py-2" onClick={() => refreshProfile()}>Retry</button><button className="rounded-lg border px-4 py-2" onClick={() => signOut()}>Sign out</button></div></div>;
  if (roles && !roles.includes(profile.role)) {
    return (
      <div className="max-w-xl mx-auto p-8">
        <p className="font-semibold">This page is for {roles.join(" / ")} accounts.</p>
        <p className="text-zinc-700 mt-1">Use the role switcher at the top to change role, or go back to your dashboard.</p>
      </div>
    );
  }
  return <>{children}</>;
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return <p role="alert" className="my-3 rounded-lg border border-red-300 bg-red-50 text-red-900 p-3 text-sm">{message}</p>;
}

"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import type { UserRole } from "@/lib/types";

const ROLES: UserRole[] = ["creator", "manager", "reviewer", "admin"];

/** Hops between the shared demo accounts. Hidden for real accounts, so their comments and audit entries stay theirs. */
export function RoleSwitcher() {
  const { profile, signInDemo } = useAuth();
  const router = useRouter();
  if (!profile?.email?.endsWith("@demo.test")) return null;
  return (
    <label className="flex items-center gap-1 text-xs text-zinc-700">
      <span className="hidden sm:inline">Demo role</span>
      <select
        aria-label="Switch demo role"
        value={profile.role}
        onChange={async (e) => { if (await signInDemo(e.target.value as UserRole)) router.push("/dashboard"); }}
        className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900"
      >
        {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
      </select>
    </label>
  );
}

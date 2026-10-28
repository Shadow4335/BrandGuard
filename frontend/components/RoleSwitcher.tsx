"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const ROLES = [
  ["creator", "creator@demo.test"], ["manager", "manager@demo.test"],
  ["reviewer", "reviewer@demo.test"], ["admin", "admin@demo.test"],
] as const;

export function RoleSwitcher() {
  const { profile, signIn } = useAuth();
  const router = useRouter();
  if (!profile) return null;
  return (
    <label className="flex items-center gap-1 text-xs text-zinc-700">
      <span className="hidden sm:inline">Switch role</span>
      <select
        aria-label="Switch demo role"
        value={profile.role}
        onChange={async (e) => {
          const email = ROLES.find((r) => r[0] === e.target.value)?.[1];
          if (email && (await signIn(email))) router.push("/dashboard");
        }}
        className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900"
      >
        {ROLES.map(([r]) => <option key={r} value={r}>{r}</option>)}
      </select>
    </label>
  );
}

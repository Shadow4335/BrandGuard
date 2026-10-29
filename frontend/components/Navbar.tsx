"use client";

import Link from "next/link";
import { LogOut, ShieldCheck } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { RoleSwitcher } from "@/components/RoleSwitcher";

const LINKS: { href: string; label: string; roles?: string[] }[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/content/new", label: "New content", roles: ["creator"] },
  { href: "/reviews", label: "Reviews", roles: ["creator", "manager", "reviewer", "admin"] },
  { href: "/brand", label: "Brand" },
  { href: "/insights", label: "Insights" },
  { href: "/about-ai", label: "About AI" },
];

export function Navbar() {
  const { user, profile, signOut, loading } = useAuth();
  return (
    <header className="border-b border-zinc-200 bg-white sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 min-h-14 py-2 flex flex-wrap items-center justify-between gap-2">
        <Link href={user ? "/dashboard" : "/"} className="flex items-center gap-2 font-bold text-lg">
          <span className="w-8 h-8 rounded-lg bg-indigo-700 text-white flex items-center justify-center"><ShieldCheck className="w-5 h-5" /></span>
          <span>BrandGuard</span>
          <span className="hidden md:inline text-xs font-normal text-zinc-600">GlowLeaf Naturals</span>
        </Link>
        {user && profile && (
          <nav aria-label="Main" className="flex flex-wrap items-center gap-1 text-sm">
            {LINKS.filter((l) => !l.roles || l.roles.includes(profile.role)).map((l) => (
              <Link key={l.href} href={l.href} className="px-2 py-1 rounded-md text-zinc-800 hover:bg-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600">{l.label}</Link>
            ))}
          </nav>
        )}
        <div className="flex items-center gap-3">
          {!loading && user ? (
            <>
              <RoleSwitcher />
              <button onClick={() => signOut()} title="Sign out" aria-label="Sign out" className="p-1.5 text-zinc-700 hover:bg-zinc-100 rounded-md"><LogOut className="w-4 h-4" /></button>
            </>
          ) : !loading ? (
            <span className="flex items-center gap-2">
              <Link href="/signup" className="px-3 py-1.5 text-xs font-medium rounded-lg border border-indigo-700 text-indigo-900">Sign up</Link>
              <Link href="/login" className="px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-700 text-white">Sign In</Link>
            </span>
          ) : null}
        </div>
      </div>
    </header>
  );
}

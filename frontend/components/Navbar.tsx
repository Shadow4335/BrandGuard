"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut } from "lucide-react";
import { BrandMark } from "@/components/BrandMark";
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
type NavLink = (typeof LINKS)[number];

function NavLinks({ links, pathname }: { links: NavLink[]; pathname: string }) {
  return (
    <ul className="flex flex-nowrap items-center gap-1 text-sm whitespace-nowrap">
      {links.map((l) => {
        const current = !!pathname && (pathname === l.href || pathname.startsWith(`${l.href}/`));
        return (
          <li key={l.href}>
            <Link href={l.href} aria-current={current ? "page" : undefined}
              className={`block px-3 py-2 md:py-1 rounded-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 ${current ? "bg-indigo-50 text-indigo-900 font-semibold" : "text-zinc-800 hover:bg-zinc-100"}`}>
              {l.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

// usePathname can't be resolved while prerendering routes with unknown params (e.g. /content/[id]) under Cache
// Components, so only this part waits for it, inside Suspense; the fallback is the same links without a highlight.
function CurrentNavLinks({ links }: { links: NavLink[] }) {
  return <NavLinks links={links} pathname={usePathname() ?? ""} />;
}

export function Navbar() {
  const { user, profile, signOut, loading } = useAuth();
  const links = profile ? LINKS.filter((l) => !l.roles || l.roles.includes(profile.role)) : [];
  // Sticky from tablet width up only: on a phone the wrapped header would cover too much of the screen
  return (
    <header className="border-b border-zinc-200 bg-white md:sticky md:top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 min-h-14 py-2 flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
        <Link href={user ? "/dashboard" : "/"} className="flex items-center gap-2 font-bold text-lg">
          <BrandMark />
          <span>BrandGuard</span>
        </Link>
        {user && profile && (
          <nav aria-label="Main" className="order-last w-full md:order-none md:w-auto -mx-4 px-4 md:mx-0 md:px-0 overflow-x-auto">
            <Suspense fallback={<NavLinks links={links} pathname="" />}>
              <CurrentNavLinks links={links} />
            </Suspense>
          </nav>
        )}
        <div className="flex items-center gap-3">
          {!loading && user ? (
            <>
              <RoleSwitcher />
              <button onClick={() => signOut()} title="Sign out" aria-label="Sign out" className="p-2 text-zinc-700 hover:bg-zinc-100 rounded-md"><LogOut className="w-4 h-4" /></button>
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

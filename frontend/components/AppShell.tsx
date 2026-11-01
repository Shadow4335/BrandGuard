"use client";

import { Suspense, useEffect, useLayoutEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, BookOpen, ChartNoAxesCombined, ClipboardList, Info, LayoutDashboard, LogOut, Plus, ShieldCheck } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { WorkspaceSelector } from "./WorkspaceSelector";
import { RoleSwitcher } from "./RoleSwitcher";
import { GovernanceBanner } from "./GovernanceBanner";
import { ButtonEffects } from "./ButtonEffects";
import { MotionControl } from "./MotionControl";
import { PublicNav } from "./PublicNav";
import { SilverWaves } from "./SilverWaves";

const LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/content/new", label: "New content", icon: Plus, creator: true },
  { href: "/reviews", label: "Reviews", icon: ClipboardList },
  { href: "/brand", label: "Brand", icon: BookOpen },
  { href: "/insights", label: "Insights", icon: ChartNoAxesCombined },
  { href: "/about-ai", label: "About AI", icon: Info },
];
export function BrandLogo() {
  return <span className="brand-logo"><ShieldCheck size={28} strokeWidth={1.5} /><span>BrandGuard</span></span>;
}
function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname() || "/";
  const { user, profile, loading, signOut } = useAuth();
  const auth = path === "/login" || path === "/signup";
  const publicInfo = path === "/about-ai" && !user;
  const workspace = !auth && !publicInfo && path !== "/";
  const previous = useRef(path), page = useRef<HTMLDivElement>(null);
  // Over the hero the public header is see-through; once the page scrolls it becomes a solid, blurred bar
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    if (workspace) return;
    const update = () => setScrolled(window.scrollY > 8);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, [workspace]);
  useLayoutEffect(() => {
    const order = ["/", "/login", "/signup", ...LINKS.map((l) => l.href)];
    const index = (p: string) => order.findIndex((r) => r === p);
    const direction = index(path) >= index(previous.current) ? 1 : -1;
    let animation: Animation | undefined;
    if (previous.current !== path && !matchMedia("(prefers-reduced-motion: reduce)").matches && !document.documentElement.dataset.reduceMotion) {
      animation = page.current?.animate([{ opacity: 0, transform: `translateX(${direction * 16}px)` }, { opacity: 1, transform: "translateX(0)" }], { duration: 350, easing: "cubic-bezier(.22,1,.36,1)" });
    }
    previous.current = path;
    return () => animation?.cancel();
  }, [path]);
  return <div className={workspace ? "workspace-shell" : auth ? "auth-shell" : publicInfo ? "public-info-shell" : "marketing-shell"}>
    <ButtonEffects />
    <a href="#main-content" className="skip-link">Skip to content</a>
    {workspace ? <>
      <aside className="app-sidebar">
        <Link href="/" aria-label="BrandGuard home"><BrandLogo /></Link>
        {profile && <WorkspaceSelector />}
        <p className="eyebrow sidebar-label">Workspace</p>
        <nav aria-label="Main"><ul>{LINKS.filter((l) => !l.creator || profile?.role === "creator").map((l) => <li key={l.href}><Link href={l.href} aria-current={path === l.href ? "page" : undefined}><l.icon size={18} />{l.label}<ArrowUpRight size={14} className="nav-arrow" /></Link></li>)}</ul></nav>
        <div className="sidebar-bottom">{profile && <><p className="profile-name">{profile.full_name || profile.email}</p><p className="profile-role">{profile.role === "manager" ? "Brand Manager" : profile.role === "reviewer" ? "Authorised Reviewer" : profile.role}</p><RoleSwitcher /></>}<p className="sidebar-tagline">AI suggests. Humans decide.</p></div>
      </aside>
      <div className="app-topbar"><span>Workspace <span className="breadcrumb-slash">/</span> {LINKS.find((l) => l.href === path)?.label || "Content review"}</span><div><MotionControl /><Link href="/about-ai" aria-label="About AI"><Info size={18} /></Link>{user && <button onClick={() => signOut()}><LogOut size={16} />Sign out</button>}</div></div>
    </> : <header className={`public-header${scrolled ? " is-scrolled" : ""}`}><Link href="/" aria-label="BrandGuard home" className="public-logo"><BrandLogo /></Link><PublicNav /><div className="public-actions"><MotionControl />{!loading && user ? <Link className="pill-button" href="/dashboard">Dashboard <ArrowUpRight size={16} /></Link> : <><Link href="/login" className="public-signin">Sign in</Link><Link className="pill-button" href="/signup">Get started <ArrowUpRight size={16} /></Link></>}</div></header>}
    {auth && <SilverWaves className="auth-art"><div><p className="eyebrow">A considered perspective</p><h2>Your brand.<br /><em>In good hands.</em></h2><p>Every word. Every claim. Considered.</p><p>AI suggests. Humans decide.</p></div></SilverWaves>}
    <main id="main-content" className={workspace ? "app-main" : auth ? "auth-main" : publicInfo ? "public-info-main" : "marketing-main"}><GovernanceBanner /><div ref={page} className="route-content" key={auth ? path : profile ? `${profile.id}:${profile.org_id}:${profile.role}` : "anonymous"}>{children}</div></main>
    {workspace && <footer className="app-footer">BrandGuard <span>AI suggests. Humans decide.</span><Link href="/about-ai">Responsible by design ↗</Link></footer>}
  </div>;
}
export function AppShell({ children }: { children: React.ReactNode }) { return <Suspense fallback={<div className="shell-loading">Loading BrandGuard…</div>}><Shell>{children}</Shell></Suspense>; }

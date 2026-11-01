"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

const LINKS: { href: string; label: string; section?: string }[] = [
  { href: "/#process", label: "The process", section: "process" },
  { href: "/#standards", label: "Brand standards", section: "standards" },
  { href: "/#insights", label: "Insights", section: "insights" },
  { href: "/about-ai", label: "About AI" },
];

/** Public-site navigation as a rounded pill. One capsule glides to the hovered or focused link and otherwise rests on
 *  where you are: the landing-page section in view, or the current page. Same motion as the brand-standards tabs. */
export function PublicNav() {
  const path = usePathname() || "/";
  const track = useRef<HTMLDivElement>(null);
  const [section, setSection] = useState<string | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const [capsule, setCapsule] = useState<{ left: number; width: number } | null>(null);
  const [instant, setInstant] = useState(true); // no slide when the capsule first appears; it fades in where it is

  const current = path === "/about-ai" ? LINKS.length - 1
    : path === "/" && section ? LINKS.findIndex((l) => l.section === section) : -1;
  const shown = hovered ?? (current >= 0 ? current : null);

  // Which landing section is in view: the one crossing a band just above the middle of the viewport
  useEffect(() => {
    if (path !== "/") return; // elsewhere `current` ignores the section
    const ids = LINKS.flatMap((l) => (l.section ? [l.section] : []));
    const inBand = new Set<string>();
    const observer = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) inBand.add(e.target.id); else inBand.delete(e.target.id);
      }
      setSection(ids.find((id) => inBand.has(id)) ?? null);
    }, { rootMargin: "-40% 0px -55% 0px" });
    ids.forEach((id) => { const el = document.getElementById(id); if (el) observer.observe(el); });
    return () => observer.disconnect();
  }, [path]);

  const wasVisible = useRef(false);
  useLayoutEffect(() => {
    const measure = () => {
      const links = track.current?.querySelectorAll<HTMLAnchorElement>("a");
      const el = shown === null ? null : links?.[shown];
      if (!el) { wasVisible.current = false; setCapsule(null); return; }
      setInstant(!wasVisible.current);
      wasVisible.current = true;
      setCapsule({ left: el.offsetLeft, width: el.offsetWidth });
    };
    measure();
    const observer = new ResizeObserver(measure);
    if (track.current) observer.observe(track.current);
    return () => observer.disconnect();
  }, [shown]);

  return (
    <nav aria-label="Main" className="public-nav-pill">
      <div ref={track} className="nav-pill-track" onMouseLeave={() => setHovered(null)}>
        <span aria-hidden className={`nav-pill-capsule${instant ? " is-instant" : ""}`}
          style={capsule ? { width: capsule.width, transform: `translateX(${capsule.left}px)`, opacity: 1 } : { opacity: 0 }} />
        <ul>
          {LINKS.map((l, i) => (
            <li key={l.href}>
              <Link href={l.href} aria-current={i === current ? (l.section ? "location" : "page") : undefined}
                className={i === shown ? "is-highlighted" : undefined}
                onMouseEnter={() => setHovered(i)} onFocus={() => setHovered(i)} onBlur={() => setHovered(null)}>
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}

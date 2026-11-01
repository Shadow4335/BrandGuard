"use client";
import { useEffect } from "react";
export function ButtonEffects() {
  useEffect(() => {
    const pending = new Map<ReturnType<typeof setTimeout>, HTMLElement>();
    const press = (e: PointerEvent) => {
      if (matchMedia("(prefers-reduced-motion: reduce)").matches || document.documentElement.dataset.reduceMotion) return;
      const button = (e.target as HTMLElement).closest<HTMLButtonElement>("button:not(:disabled)");
      if (!button) return;
      const b = button.getBoundingClientRect(), size = Math.max(b.width, b.height) * 2;
      if (getComputedStyle(button).position === "static") button.style.position = "relative";
      const clip = document.createElement("span"); clip.className = "ripple-clip"; clip.setAttribute("aria-hidden", "true");
      const ripple = document.createElement("span"); ripple.className = "control-ripple";
      Object.assign(ripple.style, { width: `${size}px`, height: `${size}px`, left: `${e.clientX - b.left - size / 2}px`, top: `${e.clientY - b.top - size / 2}px` });
      clip.appendChild(ripple); button.appendChild(clip);
      const timer = setTimeout(() => { clip.remove(); pending.delete(timer); }, 600); pending.set(timer, clip);
    };
    document.addEventListener("pointerdown", press);
    return () => { document.removeEventListener("pointerdown", press); pending.forEach((el, timer) => { clearTimeout(timer); el.remove(); }); };
  }, []);
  return null;
}

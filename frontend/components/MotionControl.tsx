"use client";
import { useEffect, useState } from "react";
/** Optional manual reduction also makes motion controls available beyond OS settings. */
export function MotionControl() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    try { if (localStorage.getItem("bg_reduce_motion") === "true") { document.documentElement.dataset.reduceMotion = "true"; queueMicrotask(() => setReduced(true)); } } catch { /* OS preference still applies */ }
  }, []);
  return <button type="button" className="motion-control" aria-pressed={reduced} onClick={() => {
    const next = !reduced; setReduced(next);
    if (next) document.documentElement.dataset.reduceMotion = "true"; else delete document.documentElement.dataset.reduceMotion;
    try { localStorage.setItem("bg_reduce_motion", String(next)); } catch { /* optional preference */ }
  }}>{reduced ? "Motion reduced" : "Reduce motion"}</button>;
}

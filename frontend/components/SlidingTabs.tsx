"use client";

import { useId, useLayoutEffect, useRef, useState } from "react";

type Tab = { id: string; label: string; detail?: string };
/** One measured capsule, roving keyboard focus and direction-aware content. */
export function SlidingTabs({ tabs, value, onChange, label, children }: {
  tabs: Tab[]; value: string; onChange: (id: string) => void; label: string; children: React.ReactNode;
}) {
  const uid = useId();
  const list = useRef<HTMLDivElement>(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });
  const [direction, setDirection] = useState(1);
  const index = tabs.findIndex((t) => t.id === value);
  useLayoutEffect(() => {
    const measure = () => {
      const el = list.current?.querySelector<HTMLButtonElement>('[aria-selected="true"]');
      if (el) setIndicator({ left: el.offsetLeft, width: el.offsetWidth });
    };
    measure();
    const observer = new ResizeObserver(measure);
    if (list.current) observer.observe(list.current);
    return () => observer.disconnect();
  }, [value]);
  function choose(next: number, focus = false) {
    setDirection(next >= index ? 1 : -1);
    onChange(tabs[next].id);
    if (focus) list.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next]?.focus();
  }
  return <div className="sliding-tabs">
    <div className="tab-scroll">
      <div ref={list} role="tablist" aria-label={label} className="tab-bar" onKeyDown={(e) => {
        let next = index;
        if (e.key === "ArrowRight") next = (index + 1) % tabs.length;
        else if (e.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
        else if (e.key === "Home") next = 0;
        else if (e.key === "End") next = tabs.length - 1;
        else return;
        e.preventDefault(); choose(next, true);
      }}>
        <span aria-hidden className="tab-indicator" style={{ left: indicator.left, width: indicator.width }} />
        {tabs.map((t, i) => <button type="button" role="tab" key={t.id} id={`${uid}-${t.id}`} aria-controls={`${uid}-panel`} aria-selected={value === t.id} tabIndex={value === t.id ? 0 : -1} onClick={() => choose(i)}>
          <span>{t.label}</span>{t.detail && <small>{t.detail}</small>}
        </button>)}
      </div>
    </div>
    <div role="tabpanel" tabIndex={0} id={`${uid}-panel`} aria-labelledby={`${uid}-${value}`} className="tab-panel" key={value} style={{ "--slide-from": `${direction * 24}px` } as React.CSSProperties}>{children}</div>
  </div>;
}

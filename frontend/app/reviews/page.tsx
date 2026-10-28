"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { RequireAuth, ErrorNote } from "@/components/RequireAuth";
import { StatusBadge } from "@/components/Pills";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import type { QueueItem } from "@/lib/types";

export default function ReviewsPage() {
  return <RequireAuth><Queue /></RequireAuth>;
}

function Queue() {
  const { profile } = useAuth();
  const [items, setItems] = useState<QueueItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.queue().then(setItems).catch((e) => setError(e.message)); }, []);
  const role = profile?.role;
  const heading = role === "manager" ? "Waiting for your review" : role === "reviewer" ? "Escalated to you" : role === "admin" ? "In review or escalated" : "Your content";
  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-4">
      <h1 className="text-2xl font-bold">{heading}</h1>
      <ErrorNote message={error} />
      {items && items.length === 0 && (
        <p className="rounded-lg border border-dashed border-zinc-400 p-4">
          {role === "creator" ? <>You have no content yet. <Link href="/content/new" className="underline font-medium">Create some</Link>.</>
            : role === "manager" ? "Nothing is waiting. A creator needs to submit content; switch role to Creator to try it."
            : role === "reviewer" ? "Nothing has been escalated yet. A manager escalates items from the review queue."
            : "No items are in review right now."}
        </p>
      )}
      <ul className="divide-y divide-zinc-200 rounded-lg border border-zinc-300 bg-white">
        {(items ?? []).map((i) => (
          <li key={i.content.id} className="p-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <Link href={role === "creator" ? `/content/${i.content.id}` : `/reviews/${i.content.id}`} className="font-medium underline">{i.content.title}</Link>
              <p className="text-xs text-zinc-700">by {i.creator_name ?? "unknown"} · {i.content.channel.replace("_", " ")} · {i.total_findings} findings{i.open_high ? ` · ${i.open_high} high-severity unresolved` : ""}</p>
            </div>
            <StatusBadge status={i.content.status} />
          </li>
        ))}
      </ul>
    </div>
  );
}

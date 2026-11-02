"use client";

import Link from "next/link";

export default function Error({ retry }: { error: unknown; retry: () => void }) {
  return (
    <div className="max-w-xl mx-auto p-8 space-y-3">
      <h1 className="text-2xl font-bold">Something went wrong</h1>
      <p className="text-zinc-700">This page hit an unexpected problem. Your saved work is not affected.</p>
      <div className="flex items-center gap-4">
        <button onClick={() => retry()} className="rounded-lg border px-4 py-2">Try again</button>
        <Link href="/" className="underline font-medium">Go to the home page</Link>
      </div>
    </div>
  );
}

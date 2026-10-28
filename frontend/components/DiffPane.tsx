"use client";

import dynamic from "next/dynamic";

const ReactDiffViewer = dynamic(() => import("react-diff-viewer-continued"), {
  ssr: false, loading: () => <p className="text-sm text-zinc-700">Loading diff...</p>,
});

export function DiffPane({ oldText, newText, oldLabel, newLabel }: { oldText: string; newText: string; oldLabel: string; newLabel: string }) {
  if (oldText === newText) return <p className="text-sm text-zinc-800">No text changes between these versions.</p>;
  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-300 text-sm">
      <ReactDiffViewer oldValue={oldText} newValue={newText} splitView={false} compareMethod={"diffWords" as never}
        leftTitle={oldLabel} rightTitle={newLabel} />
    </div>
  );
}

import type { ContentStatus, FindingConfidence, FindingSeverity } from "@/lib/types";

const SEV: Record<FindingSeverity, string> = {
  high: "bg-red-100 text-red-900 border-red-300",
  medium: "bg-amber-100 text-amber-900 border-amber-300",
  low: "bg-sky-100 text-sky-900 border-sky-300",
};
const CONF: Record<FindingConfidence, string> = {
  high: "bg-emerald-100 text-emerald-900 border-emerald-300",
  medium: "bg-zinc-100 text-zinc-800 border-zinc-300",
  low: "bg-orange-100 text-orange-900 border-orange-300",
};
const STATUS: Record<ContentStatus, [string, string]> = {
  draft: ["Draft", "bg-zinc-100 text-zinc-800 border-zinc-300"],
  checked: ["Checked", "bg-sky-100 text-sky-900 border-sky-300"],
  pending_manager: ["In review", "bg-indigo-100 text-indigo-900 border-indigo-300"],
  changes_requested: ["Changes requested", "bg-amber-100 text-amber-900 border-amber-300"],
  escalated: ["Escalated", "bg-purple-100 text-purple-900 border-purple-300"],
  approved: ["Approved", "bg-emerald-100 text-emerald-900 border-emerald-300"],
  rejected: ["Rejected", "bg-red-100 text-red-900 border-red-300"],
};
const base = "inline-block px-2 py-0.5 text-xs font-semibold rounded-md border";

export function SeverityPill({ value }: { value: FindingSeverity }) {
  return <span className={`${base} ${SEV[value]}`}>{value} severity</span>;
}
export function ConfidencePill({ value }: { value: FindingConfidence }) {
  return <span className={`${base} ${CONF[value]}`}>{value} confidence</span>;
}
export function StatusBadge({ status }: { status: ContentStatus }) {
  const [label, cls] = STATUS[status];
  return <span className={`${base} ${cls}`}>{label}</span>;
}
export const statusLabel = (s: ContentStatus) => STATUS[s][0];

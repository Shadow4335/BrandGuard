import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** "1 finding", "3 findings". */
export const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

/** Tidies generated copy: doubled full stops, spaces before punctuation, runs of spaces. */
export const tidy = (text: string) =>
  text.replace(/\.{2,}/g, ".").replace(/\s+([.,;:])/g, "$1").replace(/\s{2,}/g, " ").trim();

/** A server timestamp (UTC unless it says otherwise) shown in the viewer's own time zone, e.g. "1 Nov, 9:40 am". */
export function formatWhen(iso?: string | null) {
  if (!iso) return "";
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(iso);
  const when = new Date(hasZone ? iso : `${iso.replace(" ", "T")}Z`);
  if (Number.isNaN(when.getTime())) return iso.slice(0, 16).replace("T", " ");
  return when.toLocaleString(undefined, { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
}

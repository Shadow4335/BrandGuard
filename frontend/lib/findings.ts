import type { Finding } from "./types";
export const hasTextChange = (f: Finding) => !!f.span && (f.status === "edited" ? f.decision_text != null && f.decision_text !== f.span_text : f.status === "accepted" && f.replacement != null && f.replacement !== f.span_text);
export const isUnresolvedHigh = (f: Finding) => f.severity === "high" && !hasTextChange(f);

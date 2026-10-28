"""Pick the approved sources that the AI may cite. pgvector top-k when embeddings work,
otherwise keyword overlap (full-text style) so retrieval never blocks the demo."""
import re
from dataclasses import dataclass
from typing import Dict, List

from app.engine.embeddings import embed_texts
from app.store import get_store

STOP = set("the a an and or of to in on for with is are was be it its our your you we at by from as this that "
           "contains made have has not no can will".split())
KINDS = ["guideline", "claim_library"]


@dataclass
class RetrievedSource:
    id: str
    code: str
    kind: str
    text: str


def stem(w: str) -> str:
    w = w.lower()
    for suf in ("ly", "ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def tokens(text: str) -> set:
    return {stem(w) for w in re.findall(r"[A-Za-z]+", text) if w.lower() not in STOP and len(w) > 2}


def split_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def retrieve(org_id: str, text: str, k: int = 6) -> List[RetrievedSource]:
    store = get_store()
    sources = {s["id"]: s for s in store.select("sources", {"org_id": org_id}) if s["source_type"] in KINDS and s.get("code")}
    chosen: Dict[str, float] = {}
    # Guidelines are short and always relevant to tone: always include them.
    for s in sources.values():
        if s["source_type"] == "guideline":
            chosen[s["id"]] = 1.0
    sentences = split_sentences(text) or [text]
    vecs = embed_texts(sentences)
    if vecs:
        for v in vecs:
            for row in store.match_chunks(org_id, ["claim_library"], v, k):
                if row["source_id"] in sources:
                    chosen[row["source_id"]] = max(chosen.get(row["source_id"], 0), row.get("similarity", 0.5))
    else:  # keyword fallback
        for sent in sentences:
            st = tokens(sent)
            scored = []
            for s in sources.values():
                if s["source_type"] != "claim_library":
                    continue
                overlap = len(st & tokens(s["body"] or s["title"]))
                if overlap:
                    scored.append((overlap, s["id"]))
            for overlap, sid in sorted(scored, reverse=True)[:k]:
                chosen[sid] = max(chosen.get(sid, 0), overlap)
    return [RetrievedSource(id=i, code=sources[i]["code"], kind=sources[i]["source_type"], text=sources[i]["body"] or "")
            for i in chosen]

"""Demo organisation "GlowLeaf Naturals" (fictional Indian D2C personal-care brand).

Used by the in-memory store at startup and by seed/seed_demo.py for Supabase.
Everything here is invented; no real company, person or certification is implied.
"""
from __future__ import annotations

import io
import json
import random
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.workflow.state_machine import unresolved_high

NS = uuid.UUID("6f1c2a3e-0000-4000-8000-00000000b6a2")


def _id(name: str) -> str:
    return str(uuid.uuid5(NS, name))


ORG_NAME = "GlowLeaf Naturals"
ORG_ID = _id("org")

USERS = [
    {"key": "admin", "email": "admin@demo.test", "role": "admin", "full_name": "Asha Admin"},
    {"key": "creator", "email": "creator@demo.test", "role": "creator", "full_name": "Chirag Creator"},
    {"key": "manager", "email": "manager@demo.test", "role": "manager", "full_name": "Meera Manager"},
    {"key": "reviewer", "email": "reviewer@demo.test", "role": "reviewer", "full_name": "Rohan Reviewer"},
    # Owns the seeded historical content so the demo creator starts with a clean slate. Not shown on the login page.
    {"key": "history", "email": "history@demo.test", "role": "creator", "full_name": "Priya (past campaigns)"},
]
for _u in USERS:
    _u["id"] = _id("user-" + _u["key"])

NOT_LEGAL = "Not legal advice. Always verify against the official text."

SOURCES: List[Dict[str, Any]] = [
    {"code": "GUIDE-TONE-01", "source_type": "guideline", "title": "Brand voice",
     "body": "GlowLeaf speaks in a warm, honest, plain-spoken voice. No hype, no shouting, no exaggerated promises. "
             "Never use medical language such as cure, heal or treat. Address the reader directly as 'you'. "
             "Prefer short sentences and everyday words over superlatives."},
    {"code": "GUIDE-VIS-01", "source_type": "guideline", "title": "Visual identity and accessibility",
     "body": "Primary colour #2F6B4F (leaf green), accent #F2C94C (sun yellow), neutrals #FFFFFF, #F4F4F0, #1F2A24. "
             "Keep clear space around the logo equal to the height of the leaf mark. Text must keep a minimum "
             "contrast ratio of 4.5:1 against its background. Every image needs descriptive alt-text."},
    {"code": "TERM-01", "source_type": "terminology", "title": "Banned and preferred terms",
     "body": "Banned term -> preferred term.\n"
             "chemical-free -> made without parabens and sulfates\n"
             "toxin-free -> free from the ingredients listed on pack\n"
             "cure -> care for\n"
             "anti-aging -> age-care\n"
             "cheap -> affordable"},
    {"code": "FACT-001", "source_type": "claim_library", "title": "Lip balm naturally derived share",
     "body": "The GlowLeaf lip balm contains 92% naturally derived ingredients (third-party lab report LR-2026-04)."},
    {"code": "FACT-002", "source_type": "claim_library", "title": "Delivery times",
     "body": "Delivery takes 2-4 working days in metro cities."},
    {"code": "FACT-003", "source_type": "claim_library", "title": "Dermatological testing",
     "body": "Products were dermatologically tested on 50 volunteers in January 2026."},
    {"code": "FACT-004", "source_type": "claim_library", "title": "Founding year",
     "body": "GlowLeaf Naturals was founded in 2021."},
    {"code": "FACT-005", "source_type": "claim_library", "title": "Cruelty-free certification",
     "body": "GlowLeaf is cruelty-free certified by the (fictional) Humane Beauty Council, 2025."},
    {"code": "FACT-006", "source_type": "claim_library", "title": "Vitamin C serum strength",
     "body": "The vitamin C serum contains 10% stabilised vitamin C."},
    {"code": "FACT-007", "source_type": "claim_library", "title": "Lip balm price",
     "body": "The lip balm is priced at Rs 199 for a 10 g stick."},
    {"code": "FACT-008", "source_type": "claim_library", "title": "Fragrance",
     "body": "The lip balm contains a synthetic fragrance, listed on the pack."},
    {"code": "FACT-009", "source_type": "claim_library", "title": "Returns",
     "body": "Unopened products can be returned within 14 days of delivery."},
    {"code": "FACT-010", "source_type": "claim_library", "title": "Packaging",
     "body": "Outer cartons are made from 80% recycled paper."},
    {"code": "FACT-011", "source_type": "claim_library", "title": "Customer base",
     "body": "More than 100,000 orders have been shipped since launch."},
    {"code": "FACT-012", "source_type": "claim_library", "title": "Lip balm results",
     "body": "In a 4-week consumer trial, 78% of participants said their lips felt softer. Individual results vary. "
             "The lip balm is a cosmetic and is not a treatment for any medical condition."},
    {"code": "REG-CCPA-2022", "source_type": "regulatory", "title": "CCPA misleading advertisement guidelines (2022)",
     "body": "Summary: Advertisements must not mislead consumers. Claims must be truthful and capable of "
             "substantiation. Disclaimers must not contradict or hide the main claim and must be clearly visible. "
             "Absolute claims such as 'guaranteed' or '100%' need complete evidence. "
             "Official: https://consumeraffairs.nic.in/ . " + NOT_LEGAL},
    {"code": "REG-ASCI-INFL", "source_type": "regulatory", "title": "ASCI influencer advertising guidelines",
     "body": "Summary: Influencers must disclose material connections with brands clearly, using labels such as "
             "#Ad, #Sponsored or #Collab placed where viewers see them first, not hidden among hashtags. "
             "Digitally created or AI-generated personas should be disclosed. "
             "Official: https://www.ascionline.in/ . " + NOT_LEGAL},
    {"code": "REG-ASCI-SGC", "source_type": "regulatory", "title": "ASCI general advertising code",
     "body": "Summary: Advertising must be honest, must not make unsupported superiority claims such as 'No. 1' "
             "without evidence, and must not exaggerate product benefits. "
             "Official: https://www.ascionline.in/the-asci-code/ . " + NOT_LEGAL},
    {"code": "REG-DMR", "source_type": "regulatory", "title": "Drugs and Magic Remedies (Objectionable Advertisements) Act",
     "body": "Summary: Advertising that claims a product can cure, treat or prevent listed diseases and conditions "
             "is restricted. Cosmetics should not be presented as medicines or cures. "
             "Official: https://www.indiacode.nic.in/ . " + NOT_LEGAL},
    {"code": "ASSET-PALETTE", "source_type": "asset", "title": "Approved palette",
     "body": json.dumps({"primary": "#2F6B4F", "accent": "#F2C94C", "neutrals": ["#FFFFFF", "#F4F4F0", "#1F2A24"]})},
    {"code": "ASSET-LOGO", "source_type": "asset", "title": "GlowLeaf logo (placeholder)",
     "body": "Placeholder logo: green leaf mark with the wordmark 'GlowLeaf'."},
]

SAMPLES: List[Dict[str, Any]] = [
    {"key": "instagram", "title": "Lip balm launch post", "channel": "instagram_post", "ai_generated": False,
     "text": "Our 100% natural, chemical-free lip balm cures chapped lips in 1 day! Guaranteed. India's #1 lip care. "
             "Cheap at ₹199 \U0001F33F\n\n*Results vary; contains synthetic fragrance.",
     "image": False, "alt_text": ""},
    {"key": "influencer", "title": "Influencer morning routine", "channel": "influencer_post", "ai_generated": True,
     "text": "Good morning, glow gang! Meet Mira, my virtual best friend, showing off her new GlowLeaf morning "
             "routine. Swipe to see the vitamin C serum in action. Link in bio! #glow #skincare #naturals",
     "image": False, "alt_text": ""},
    {"key": "poster", "title": "Summer sale poster", "channel": "instagram_post", "ai_generated": False,
     "text": "", "image": True, "alt_text": ""},
    {"key": "clean", "title": "Delivery announcement", "channel": "website_page", "ai_generated": False,
     "text": "Good news for you: your GlowLeaf order arrives in 2-4 working days in metro cities. "
             "Our lip balm contains 92% naturally derived ingredients and costs Rs 199.",
     "image": False, "alt_text": ""},
]


def make_poster_png() -> bytes:
    """Light yellow text on a busy multicolour background: fails the 4.5:1 contrast rule on purpose."""
    from PIL import Image, ImageDraw, ImageFont
    rnd = random.Random(7)
    w, h = 900, 500
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (int(210 - 60 * x / w), int(150 + 40 * y / h), int(90 + 80 * x / w))
    d = ImageDraw.Draw(img)
    for _ in range(45):
        x0, y0 = rnd.randint(0, w), rnd.randint(0, h)
        r = rnd.randint(20, 70)
        d.ellipse([x0, y0, x0 + r, y0 + r], fill=(rnd.randint(150, 230), rnd.randint(120, 200), rnd.randint(80, 190)))
    font = ImageFont.load_default(size=88)
    small = ImageFont.load_default(size=44)
    d.text((60, 120), "SUMMER SALE", font=font, fill=(255, 250, 170))
    d.text((60, 260), "GlowLeaf lip care 50% off", font=small, fill=(255, 250, 170))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def make_logo_png() -> bytes:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (240, 240), "#FFFFFF")
    d = ImageDraw.Draw(img)
    d.ellipse([40, 40, 200, 200], fill="#2F6B4F")
    d.polygon([(120, 60), (170, 120), (120, 180), (70, 120)], fill="#F2C94C")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def chunk_text(text: str, max_chars: int = 600) -> List[str]:
    """Split on paragraph/sentence boundaries into chunks of at most max_chars."""
    parts: List[str] = []
    cur = ""
    for piece in [p.strip() for p in text.replace("\n", "\n\n").split("\n\n") if p.strip()]:
        if cur and len(cur) + len(piece) > max_chars:
            parts.append(cur)
            cur = piece
        else:
            cur = f"{cur}\n{piece}".strip()
    if cur:
        parts.append(cur)
    return parts or [text]


def source_rows(org_id: str = ORG_ID) -> List[Dict[str, Any]]:
    return [{"id": _id("src-" + s["code"]), "org_id": org_id, "metadata": {}, **s} for s in SOURCES]


def seed_memory_store(store) -> None:
    store.insert("organisations", {"id": ORG_ID, "name": ORG_NAME})
    for u in USERS:
        store.insert("profiles", {"id": u["id"], "org_id": ORG_ID, "role": u["role"],
                                  "email": u["email"], "full_name": u["full_name"]})
    for row in source_rows():
        store.insert("sources", row)
        for i, c in enumerate(chunk_text(row["body"])):
            store.insert("source_chunks", {"source_id": row["id"], "org_id": ORG_ID, "content": c,
                                           "chunk_index": i, "embedding": None, "metadata": {"code": row["code"]}})


# ---------------------------------------------------------------------------
# Historical data so Insights is never empty (everything flagged seeded=true)
# ---------------------------------------------------------------------------

# rule_id -> (category, layer, severity, weight, reject_rate, low_confidence)
HISTORY_RULES = {
    "RULE-ABS-001": ("claim", "A", "high", 22, 0.10, False),
    "RULE-TERM-001": ("terminology", "A", "medium", 14, 0.10, False),
    "RULE-MED-001": ("claim", "A", "high", 8, 0.05, False),
    "RULE-SUP-001": ("claim", "A", "high", 7, 0.15, False),
    "RULE-DISC-INFL-001": ("disclosure", "A", "high", 7, 0.0, False),
    "RULE-A11Y-ALT-001": ("accessibility", "A", "medium", 6, 0.1, False),
    "RULE-VIS-CONTRAST-001": ("accessibility", "A", "high", 4, 0.0, False),
    "RULE-TONE-HYPE": ("tone", "B", "low", 9, 0.67, False),
    "RULE-CLAIM-UNSUPPORTED": ("claim", "B", "medium", 6, 0.2, True),
    "RULE-CLAIM-FACT": ("claim", "B", "high", 4, 0.0, False),
}
HISTORY_STATUSES = ["approved"] * 9 + ["pending_manager"] * 3 + ["escalated"] * 2 + ["changes_requested"] * 4 + \
                   ["rejected"] * 2 + ["checked"] * 3 + ["draft"] * 2
HISTORY_SEASONS = ["Monsoon", "Festive", "Winter", "Summer", "Spring"]
HISTORY_PRODUCTS = ["lip balm", "face wash", "body lotion", "vitamin C serum", "hair oil"]
# rule_id -> (sentence, flagged phrase, issue, why, suggested fix, replacement, wording if the creator edits it, citations)
HISTORY_EVIDENCE = {
    "RULE-ABS-001": ("Our {p} is 100% safe for every skin type.", "100% safe", 'Absolute or guaranteed claim: "100% safe"',
                     "Absolute claims need complete substantiation and cannot be narrowed by fine print.",
                     "Soften it to a statement you can support.", "gentle", "gentle", ["REG-CCPA-2022"]),
    "RULE-TERM-001": ("This {p} is chemical-free and made in small batches.", "chemical-free",
                      'Banned term "chemical-free" (use "made without parabens and sulfates")',
                      "This term is on the brand's banned list; use the approved wording.",
                      'Replace with "made without parabens and sulfates".', "made without parabens and sulfates",
                      "made without parabens and sulfates", ["TERM-01"]),
    "RULE-MED-001": ("Our {p} cures dry, irritated skin.", "cures", 'Medical or cure claim on a cosmetic: "cures"',
                     "Cosmetics must not be presented as treating or curing conditions.",
                     "Describe care or comfort, not treatment.", "cares for", "soothes", ["REG-DMR", "TERM-01"]),
    "RULE-SUP-001": ("The {p} is India's #1 choice for daily care.", "India's #1", 'Unsupported superiority claim: "India\'s #1"',
                     "Ranking claims need independent evidence on file.", "Remove the ranking.", "a popular", "a popular",
                     ["REG-ASCI-SGC"]),
    "RULE-DISC-INFL-001": ("Loving my new {p} from GlowLeaf, it's all I use now.", "Loving my new", "Missing #Ad disclosure on a paid post",
                           "Paid influencer posts must carry a clear disclosure at the start.", "Add #Ad at the start of the post.",
                           "#Ad Loving my new", "#Ad Loving my new", ["REG-ASCI-INFL"]),
    "RULE-A11Y-ALT-001": ("[Image: {p} on a shelf, no alt-text supplied]", "no alt-text supplied", "Image has no alt-text",
                          "Images need alt-text so screen-reader users get the same information.",
                          "Add alt-text that describes the image and any text in it.", None, "alt-text added", ["GUIDE-VIS-01"]),
    "RULE-VIS-CONTRAST-001": ("[Banner: pale yellow {p} headline on a white background]", "pale yellow", "Headline contrast is below WCAG AA",
                              "Text must reach a 4.5:1 contrast ratio against its background.",
                              "Use a darker colour from the approved palette.", None, "dark green", ["GUIDE-VIS-01", "ASSET-PALETTE"]),
    "RULE-TONE-HYPE": ("This {p} is a total game-changer!", "game-changer!", "Tone is more excited than the brand voice",
                       "Brand voice is warm, honest and plain-spoken with no hype.",
                       "Use plain wording and a calm full stop.", "good everyday choice.", "nice daily habit.", ["GUIDE-TONE-01"]),
    "RULE-CLAIM-UNSUPPORTED": ("Customers see results from the {p} in 3 days.", "in 3 days", 'Unsupported claim: "in 3 days" has no approved source',
                               "No approved fact covers this timeframe. No approved source supports this claim.",
                               "Remove it, or ask an admin to add an approved fact that supports it.", None, "over time", []),
    "RULE-CLAIM-FACT": ("Your {p} arrives in 1 day in metro cities.", "in 1 day", '"in 1 day" contradicts approved fact FACT-002',
                        "The approved delivery time for metro cities is 2-4 working days.",
                        "Use the approved figure.", "in 2-4 working days", "in 2-4 working days", ["FACT-002"]),
}
ESCALATE_REASON = "Legal should look at these claims before this goes out."


def seed_history(store, org_id: str, creator_id: str, manager_id: str, reviewer_id: str, now: datetime = None) -> None:
    rnd = random.Random(42)
    now = now or datetime.now(timezone.utc)
    rule_ids = list(HISTORY_RULES)
    weights = [HISTORY_RULES[r][3] for r in rule_ids]
    channels = ["instagram_post", "website_page", "influencer_post", "press_release", "email"]
    items, versions, runs, findings, approvals, audits = [], [], [], [], [], []
    total_target = 80
    per_item = [3] * 25
    for i in range(total_target - sum(per_item)):
        per_item[i % 25] += 1
    for n in range(25):
        # Three hours back so the decisions below, an hour apart, are never in the future
        created = now - timedelta(days=29 - n * 29 / 24, hours=3 + rnd.randint(0, 6))
        iso = created.isoformat()
        status = HISTORY_STATUSES[n % len(HISTORY_STATUSES)]
        cid, vid, rid = _id(f"hist-c{n}"), _id(f"hist-v{n}"), _id(f"hist-r{n}")
        items.append({"id": cid, "org_id": org_id, "title": f"{HISTORY_SEASONS[n % 5]} {HISTORY_PRODUCTS[n // 5]} campaign", "status": status,
                      "creator_id": creator_id, "channel": rnd.choice(channels), "ai_generated": n % 7 == 0,
                      "current_version": 1, "created_at": iso, "updated_at": iso})
        runs.append({"id": rid, "org_id": org_id, "content_item_id": cid, "content_version_id": vid, "version_number": 1,
                     "layer_a_ms": 4, "layer_b_ms": 900, "used_fallback": False, "model": "seeded", "created_at": iso})
        audits.append({"org_id": org_id, "actor_id": creator_id, "event_type": "review_run", "target_type": "content_item",
                       "target_id": cid, "details": {"seeded": True, "findings": per_item[n]}, "created_at": iso})
        text, item_findings, seen = "", [], Counter()
        for k in range(per_item[n]):
            rule = rnd.choices(rule_ids, weights)[0]
            cat, layer, sev, _, rej, low = HISTORY_RULES[rule]
            decided = status not in ("draft", "checked") or rnd.random() < 0.7
            r = rnd.random()
            st = "open" if not decided else ("rejected" if r < rej else rnd.choice(["accepted", "accepted", "edited"]))
            fid = _id(f"hist-f{n}-{k}")
            sentence, phrase, issue, why, fix, replacement, edit, codes = HISTORY_EVIDENCE[rule]
            if status == "approved" and n % 4 and sev == "high":  # only every fourth approval went through on an override
                st = "accepted" if replacement else "edited"
            # The campaign's own product; a rule that fires twice moves to the next one so no sentence repeats
            sentence = sentence.format(p=HISTORY_PRODUCTS[(n // 5 + seen[rule]) % 5])
            seen[rule] += 1
            text += " " if text else ""
            start = len(text) + sentence.index(phrase)
            text += sentence
            item_findings.append({
                "id": fid, "content_version_id": vid, "org_id": org_id, "run_id": rid, "layer": layer, "category": cat,
                "rule_id": rule, "source_ids": [], "source_codes": codes, "span": {"start": start, "end": start + len(phrase)},
                "region": None, "span_text": phrase, "issue": issue, "why_flagged": why, "suggested_fix": fix,
                "replacement": replacement, "severity": sev, "confidence": "low" if low else ("high" if layer == "A" else "medium"),
                "status": st, "decision_text": edit if st == "edited" else None, "decided_by": creator_id if st != "open" else None,
                "decision_reason": "Not applicable to this channel" if st == "rejected" else None,
                "decided_at": iso if st != "open" else None, "created_at": iso})
            if st != "open":
                audits.append({"org_id": org_id, "actor_id": creator_id, "event_type": "finding_decided",
                               "target_type": "finding", "target_id": fid,
                               "details": {"seeded": True, "decision": st, "rule_id": rule}, "created_at": iso})
        findings += item_findings
        versions.append({"id": vid, "content_item_id": cid, "org_id": org_id, "version_number": 1, "file_type": "text/plain",
                         "raw_text": text, "alt_text": "", "note": "Initial version", "created_by": creator_id, "created_at": iso})

        def decide(actor: str, role: str, action: str, to: str, hours: int, reason: str = None, override: bool = False) -> None:
            at = (created + timedelta(hours=hours)).isoformat()
            approvals.append({"org_id": org_id, "content_item_id": cid, "version_number": 1, "actor_id": actor, "role": role,
                              "action": action, "reason": reason, "override": override, "created_at": at})
            audits.append({"org_id": org_id, "actor_id": actor, "event_type": f"workflow_{action}", "target_type": "content_item",
                           "target_id": cid, "details": {"seeded": True, "to": to, "role": role, "reason": reason or "", "override": override},
                           "created_at": at})

        if status in ("pending_manager", "escalated", "approved", "changes_requested", "rejected"):
            decide(creator_id, "creator", "submit", "pending_manager", 0)
        if status == "approved":
            override = unresolved_high(item_findings) > 0  # the same rule the workflow applies to live approvals
            decide(manager_id, "manager", "approve", "approved", 1, "Legal cleared these claims for this campaign." if override else None, override)
        elif status == "changes_requested":
            decide(manager_id, "manager", "request_changes", "changes_requested", 1, "Please fix the flagged wording and resubmit.")
        elif status in ("escalated", "rejected"):
            decide(manager_id, "manager", "escalate", "escalated", 1, ESCALATE_REASON)
            if status == "rejected":
                decide(reviewer_id, "reviewer", "reject", "rejected", 2, "These claims can't be substantiated as written.")
    for table, rows in [("content_items", items), ("content_versions", versions), ("review_runs", runs),
                        ("findings", findings), ("approvals", approvals), ("audit_log", audits)]:
        store.insert_many(table, rows)


_orig_seed = seed_memory_store


def seed_memory_store(store) -> None:  # noqa: F811 - extends the base seeding with history
    _orig_seed(store)
    u = {x["key"]: x["id"] for x in USERS}
    seed_history(store, ORG_ID, u["history"], u["manager"], u["reviewer"])

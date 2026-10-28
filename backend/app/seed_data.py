"""Demo organisation "GlowLeaf Naturals" (fictional Indian D2C personal-care brand).

Used by the in-memory store at startup and by seed/seed_demo.py for Supabase.
Everything here is invented; no real company, person or certification is implied.
"""
from __future__ import annotations

import io
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

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

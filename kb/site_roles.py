#!/usr/bin/env python3
"""Where the pages place a person in the school — and nothing more.

The old build filed every recurring character under allies / rivals /
classmates / faculty & student council, read off `characters.mid_type`, a
table written before any volume had been read. Those are relations, not
properties: "ally" needs a subject and a moment, and the table stored
neither, so it could not be right even for the volume it described. It also
merged two different axes (who someone is enrolled as, and how they stand to
someone else) into one column, which is why a single label like "faculty &
student council" could be half right and half wrong at the same time.

What the pages can carry without inference is narrower: the institution a
person is recorded in, stated next to the page that says it, with the volume
attached, so a transfer or a promotion shows up as a second row instead of
silently falsifying the first.

Source: `[role:…]` entries in the walk ledgers. Nothing else. A class is not
inferred from the room a scene happens in, and a stance is not inferred at
all. Where no ledger line states a role, the site says so and shows which
rooms the scenes happen in, so the gap is visible instead of filled.
"""

import re

# the vocabulary a `[role:…]` entry may use. A closed set keeps the buckets
# mechanical: the build never has to guess what a label means.
ROLE_BUCKETS = {
    "class-1a": ("class", "Class 1-A", 10),
    "class-1b": ("class", "Class 1-B", 11),
    "class-1c": ("class", "Class 1-C", 12),
    "class-1d": ("class", "Class 1-D", 13),
    "student-council": ("service", "Student council", 20),
    "faculty": ("service", "Faculty", 21),
}

BUCKET_ORDER = ["Class 1-A", "Class 1-B", "Class 1-C", "Class 1-D",
                "Student council", "Faculty"]

# A scene line that names the room it happens in. Used only on the
# "role not stated" list, as a pointer to where to look, never as a claim
# about membership.
ROOM_RE = re.compile(
    r"\bClass\s*(?:1\s*[-–]\s*)?([A-D])\b\s*(?:classroom|room|homeroom)\b",
    re.I)


def _bucket(target):
    entry = ROLE_BUCKETS.get(target or "")
    return entry[1] if entry else None


def bucket_label(target):
    """Human label for a `[role:…]` value; the key itself if unknown, so a
    typo shows up in review instead of turning into a silent blank."""
    return _bucket(target) or (target or "Role")


def collect(ledgers):
    """{vol_id: {bucket_label: [fact]}} from `[role:…]` entries.

    fact = {id, page, text}. The volume comes from the ledger section the
    entry sits in, so the same person can hold two different roles in two
    volumes without either overwriting the other. Entries without a page
    anchor are dropped here and reported by the gate, because a role is
    exactly the kind of fact that must be checkable.
    """
    out = {}
    for stem, led in ledgers.items():
        cid = (led.get("meta") or {}).get("char_id") or stem
        for section in led.get("vols") or []:
            vol = section["vol"]
            for block in section["blocks"]:
                for e in block["entries"]:
                    if e.get("marker") != "role":
                        continue
                    label = _bucket(e.get("target"))
                    if not label or not e.get("pages"):
                        continue
                    out.setdefault(vol, {}).setdefault(label, []).append({
                        "id": cid,
                        "page": e["pages"],
                        "text": e.get("text") or "",
                    })
    return out


def room_hints(ledgers):
    """{char_id: [(vol, 'Class 1-D', 'p.32–34'), ...]} for characters whose
    role no ledger line states: where their scenes are set, so a reader can
    see the gap is a missing line, not a missing scene."""
    out = {}
    for stem, led in ledgers.items():
        cid = (led.get("meta") or {}).get("char_id") or stem
        for section in led.get("vols") or []:
            for block in section["blocks"]:
                hits = []
                for e in block["entries"]:
                    m = ROOM_RE.search(e.get("text") or "")
                    if m:
                        hits.append(m.group(1).upper())
                if hits and block.get("pages"):
                    # one hint per room per block, first one wins
                    label = f"Class 1-{hits[0]}"
                    out.setdefault(cid, []).append(
                        (section["vol"], label, block["pages"]))
    return out


def index(facts):
    """[(vol, [(bucket_label, [fact])])] in reading order, buckets ordered."""
    vols = []
    for vol in sorted(facts):
        buckets = []
        for label in BUCKET_ORDER:
            rows = facts[vol].get(label)
            if rows:
                buckets.append((label, sorted(rows, key=lambda f: f["id"])))
        if buckets:
            vols.append((vol, buckets))
    return vols


def stated_ids(facts):
    return {f["id"] for buckets in facts.values()
            for rows in buckets.values() for f in rows}


def facts_for(facts, cid):
    """[(vol, label, fact)] for one person, oldest volume first."""
    out = []
    for vol in sorted(facts):
        for label in BUCKET_ORDER:
            for f in facts[vol].get(label, []):
                if f["id"] == cid:
                    out.append((vol, label, f))
    return out

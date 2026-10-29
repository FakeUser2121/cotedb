#!/usr/bin/env python3
"""P8-2a: location discovery report (read-only, no DB writes).

python3 kb/p8_mine.py

Three extractors, mirroring the P1 multi-extractor union idea:

  1. SEED    — curated canonical location forms (COTE settings knowledge)
               verified against the corpus: hit count + volume spread.
               Macron variants matched via character classes.
  2. HEADS   — noun-phrase mining around place-noun heads (building,
               floor, room, hall, island, ship, hotel, ...) with up to
               2 leading modifiers; ranked by corpus frequency. Catches
               facilities the seed missed.
  3. NAMED   — capitalized multiword place names after locative
               prepositions (at/in/to/near the X) — off-site/city
               venues the common-noun extractors cannot see.

Output is a review report: candidates get curated into kb/p8_import.py
(decisions persist in the script, never ad-hoc DB edits).
"""

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import iter_pages  # noqa: E402

SEED = {
    # campus buildings / facilities
    "school building": "campus-building",
    "main building": "campus-building",
    "schoolhouse": "campus-building",
    "gymnasium": "campus-building",
    "swimming pool": "campus-building",
    "pool": "campus-building",
    "cafeteria": "campus-building",
    "dining hall": "campus-building",
    "library": "campus-building",
    "auditorium": "campus-building",
    "rooftop": "campus-building",
    "roof": "campus-building",
    "athletic field": "campus-zone",
    "tennis court": "campus-zone",
    "student council room": "campus-building",
    "guidance office": "campus-building",
    "club room": "campus-building",
    "convenience store": "campus-building",
    "infirmary": "campus-building",
    "nurse's office": "campus-building",
    "clinic": "campus-building",
    "campus": "campus-zone",
    "school grounds": "campus-zone",
    # dorms
    "dormitory": "dorm",
    "dorm": "dorm",
    "residence hall": "dorm",
    "dorm room": "dorm",
    # exam venues
    "deserted island": "exam-venue",
    "cruise ship": "exam-venue",
    "old school building": "exam-venue",
    "hotel": "exam-venue",
    "ski resort": "exam-venue",
    # off-site / city
    "tokyo": "city",
    "shinjuku": "city",
    "yokohama": "city",
    "kyoto": "city",
    "osaka": "city",
    "sapporo": "city",
    "hokkaido": "city",
    "station": "city",
    "airport": "city",
    "hospital": "city",
    "shopping district": "city",
}

HEADS = [
    "dormitory", "dorm", "building", "wing", "floor", "room", "hall",
    "cafeteria", "dining hall", "library", "pool", "gymnasium", "gym",
    "auditorium", "rooftop", "roof", "field", "court", "stadium",
    "island", "ship", "cruise ship", "liner", "hotel", "station", "city",
    "town", "village", "port", "office", "store", "shop", "clinic",
    "infirmary", "shrine", "temple", "park", "beach", "mountain",
    "forest", "river", "bridge", "airport", "hospital", "restaurant",
    "cafe", "cinema", "mall", "street", "avenue", "alley", "apartment",
    "room", "classroom", "lab", "grounds", "campus", "yard",
    "hallway", "corridor", "staircase", "stairs", "elevator", "gate",
    "entrance", "meeting room", "conference room", "storage", "locker",
]

PREP = r"(?:at|in|to|near|toward|towards|from|into|on|off)"

MACRON = {"ō": "o", "ū": "u", "ā": "a", "ī": "i", "ē": "e"}


def form_pattern(form):
    """Literal match with macron classes: 'Ōnuki' -> [oō]nuki;
    hyphen matches either a literal hyphen or word break
    ('end-of-year' covers 'end-of-year' and 'end of year')."""
    out = []
    for ch in form.lower():
        if ch in MACRON:
            out.append(f"[{ch}{MACRON[ch]}]")
        elif ch == "-":
            out.append(r"[-\s]+")
        elif ch.isalnum():
            out.append(ch)
        else:
            out.append(r"\s+")
    return "".join(out)


def seed_report():
    compiled = {f: re.compile(rf"\b{form_pattern(f)}", re.I) for f in SEED}
    totals = Counter()
    vols = {f: set() for f in SEED}
    for vol, _stem, _page, _s, text in iter_pages():
        for form, rx in compiled.items():
            n = len(rx.findall(text))
            if n:
                totals[form] += n
                vols[form].add(vol)
    print("=== SEED verification (hits, vols) ===")
    for form in sorted(SEED, key=lambda f: -totals[f]):
        print(f"{totals[form]:5d} {len(vols[form]):2d}v  {form}")


def head_report():
    head_rx = re.compile(
        r"\b([A-Za-z][A-Za-z'’\-]*(?:\s+[A-Za-z][A-Za-z'’\-]*){0,2}\s+"
        r"(?:" + "|".join(re.escape(h) for h in HEADS) + r"))\b",
        re.I)
    counts = Counter()
    for _vol, _stem, _page, _s, text in iter_pages():
        for m in head_rx.finditer(text):
            phrase = re.sub(r"\s+", " ", m.group(1).strip().lower())
            counts[phrase] += 1
    stop = {"the floor", "this room", "that room", "a room", "one floor",
            "first floor", "second floor", "third floor", "fourth floor",
            "fifth floor", "class room", "classroom"}
    print("\n=== HEADS top candidates (count phrase) ===")
    for phrase, n in counts.most_common(90):
        if phrase not in stop and n >= 8:
            print(f"{n:5d}  {phrase}")


def named_report():
    named_rx = re.compile(
        rf"\b{PREP}\s+(?:the\s+)?"
        r"([A-Z][\w'’\-]+(?:\s+(?:of\s+)?[A-Z][\w'’\-]+){1,3})\b")
    counts = Counter()
    for _vol, _stem, _page, _s, text in iter_pages():
        for m in named_rx.finditer(text):
            counts[m.group(1)] += 1
    print("\n=== NAMED after locative preposition ===")
    for phrase, n in counts.most_common(60):
        if n >= 4:
            print(f"{n:5d}  {phrase}")


if __name__ == "__main__":
    seed_report()
    head_report()
    named_report()

#!/usr/bin/env python3
"""P8-3: anchored location mentions (idempotent full rebuild).

python3 kb/p8_mentions.py

Run order: p8_init -> p8_import -> p8_mentions -> location_analysis.

One corpus pass with a single combined alternation of all curated alias
forms (longest form first, so 'gymnasium' wins over 'gym' at the same
position and finditer's non-overlap scan swallows prefix collisions).
Spans are absolute offsets (page start + match start), same anchor model
as quotes/events. Per-location overlap cleanup as defense in depth:
sort by start, drop any span contained in an already-kept span.

Also derives locations.first_vol / last_vol from the rebuilt mentions
(chronological min/max via volumes.chrono_order).

Rebuild is scoped to provenance='p8_mentions': DELETE own rows, insert,
update footprint, commit. location_claims and locations prose untouched.
"""

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402
from p8_import import LOCATIONS  # noqa: E402
from p8_mine import form_pattern  # noqa: E402

PROV = "p8_mentions"


def build_matcher():
    """(regex, {group_index: loc_id}); longest form first per position."""
    form_to_loc = {}
    for loc_id, _n, _k, aliases in LOCATIONS:
        for form, _t in aliases:
            form_to_loc[form] = loc_id
    forms = sorted(form_to_loc, key=len, reverse=True)
    groups = {}
    parts = []
    for i, form in enumerate(forms):
        groups[i] = form_to_loc[form]
        parts.append(f"(?P<g{i}>\\b{form_pattern(form)})")
    return re.compile("|".join(parts), re.I), groups


def key(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def main():
    rx, groups = build_matcher()
    hits = defaultdict(list)  # loc_id -> [(vol, page, start, end)]

    for vol, _stem, page, pstart, text in iter_pages():
        for m in rx.finditer(text):
            grp = m.lastgroup
            if grp is None:
                continue
            loc_id = groups[int(grp[1:])]
            hits[loc_id].append(
                (vol, page, pstart + m.start(), pstart + m.end()))

    db = sqlite3.connect(DB_PATH)
    db.execute("DELETE FROM location_mentions WHERE provenance=?",
               (PROV,))
    total = 0
    per_loc = {}
    for loc_id in sorted(hits):
        spans = sorted(set(hits[loc_id]), key=lambda s: (s[2], -(s[3])))
        kept = []
        for vol, page, s, e in spans:
            if kept and kept[-1][0] == vol and kept[-1][1] == page \
                    and s < kept[-1][3]:
                continue  # contained in previous kept span
            kept.append((vol, page, s, e))
        for vol, page, s, e in kept:
            db.execute(
                "INSERT INTO location_mentions "
                "(loc_id, vol_id, pdf_page, span_start, span_end, "
                "provenance) VALUES (?,?,?,?,?,?)",
                (loc_id, vol, page, s, e, PROV))
        total += len(kept)
        per_loc[loc_id] = kept

    chrono = {v: i for i, (v,) in enumerate(
        db.execute("SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    for loc_id, _n, _k, _a in LOCATIONS:
        vols = [s[0] for s in hits.get(loc_id, ())]
        first = min(vols, key=lambda v: chrono.get(v, 1 << 30)) \
            if vols else None
        last = max(vols, key=lambda v: chrono.get(v, -1)) \
            if vols else None
        db.execute(
            "UPDATE locations SET first_vol=?, last_vol=? "
            "WHERE loc_id=?", (first, last, loc_id))
    db.commit()
    n_rows = db.execute(
        "SELECT count(*) FROM location_mentions").fetchone()[0]
    db.close()

    print(f"p8_mentions: {n_rows} anchored mentions "
          f"(dedup removed {total and ''}"
          f"{sum(len(set(hits[k])) for k in hits) - total} overlaps)")
    for loc_id, _n, _k, _a in LOCATIONS:
        kept = per_loc.get(loc_id, [])
        vols = sorted({s[0] for s in kept}, key=lambda v: chrono.get(v, 999))
        raw = len(set(hits.get(loc_id, [])))
        print(f"  {loc_id:24s} {len(kept):5d} mentions  "
              f"{len(vols):2d} vols  ({vols[0] if vols else '-'}.."
              f"{vols[-1] if vols else '-'}, raw {raw})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

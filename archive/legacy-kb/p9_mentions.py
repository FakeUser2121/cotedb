#!/usr/bin/env python3
"""P9-4: anchored exam + system mentions (idempotent full rebuild).

python3 kb/p9_mentions.py

Run order: p9_init -> p9_import -> p9_mentions -> p9_analysis.

One corpus pass with a single combined alternation of all curated alias
forms (longest form first, so 'uninhabited island special exam' wins
over 'island exam' at the same position and finditer's non-overlap scan
swallows prefix collisions). Spans are absolute offsets (page start +
match start), same anchor model as quotes/events. Per-entity overlap
cleanup as defense in depth: sort by start, drop any span contained in
an already-kept span.

Also derives exams.first_vol/last_vol and systems.first_vol/last_vol
from the rebuilt mentions (chronological min/max via volumes.chrono_order).

Rebuild is scoped to provenance='p9_mentions': DELETE own rows, insert,
update footprint, commit. Instances/claims/authored prose untouched.
"""

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402
from p9_import import EXAMS, SYSTEMS  # noqa: E402
from p8_mine import form_pattern  # noqa: E402

PROV = "p9_mentions"


def build_matcher():
    """(regex, {group_index: entity_id}); longest form first per position."""
    form_to_entity = {}
    for exam_id, _n, _k, aliases in EXAMS:
        for form, _t in aliases:
            form_to_entity[form] = exam_id
    for sys_id, _n, _k, aliases in SYSTEMS:
        for form, _t in aliases:
            form_to_entity[form] = sys_id
    forms = sorted(form_to_entity, key=len, reverse=True)
    groups = {}
    parts = []
    for i, form in enumerate(forms):
        groups[i] = form_to_entity[form]
        parts.append(f"(?P<g{i}>\\b{form_pattern(form)})")
    return re.compile("|".join(parts), re.I), groups


def main():
    rx, groups = build_matcher()
    hits = defaultdict(list)  # entity_id -> [(vol, page, start, end)]

    for vol, _stem, page, pstart, text in iter_pages():
        for m in rx.finditer(text):
            grp = m.lastgroup
            if grp is None:
                continue
            ent_id = groups[int(grp[1:])]
            hits[ent_id].append(
                (vol, page, pstart + m.start(), pstart + m.end()))

    db = sqlite3.connect(DB_PATH)
    db.execute("DELETE FROM exam_mentions WHERE provenance=?", (PROV,))
    db.execute("DELETE FROM system_mentions WHERE provenance=?", (PROV,))
    total_kept = 0
    total_raw = 0
    per_ent = {}
    for ent_id in sorted(hits):
        spans = sorted(set(hits[ent_id]), key=lambda s: (s[2], -(s[3])))
        kept = []
        for vol, page, s, e in spans:
            if kept and kept[-1][0] == vol and kept[-1][1] == page \
                    and s < kept[-1][3]:
                continue  # contained in previous kept span
            kept.append((vol, page, s, e))
        exam_ids = {e for e, _n, _k, _a in EXAMS}
        if ent_id in exam_ids:
            sql = ("INSERT INTO exam_mentions "
                   "(exam_id, vol_id, pdf_page, span_start, span_end, "
                   "provenance) VALUES (?,?,?,?,?,?)")
        else:
            sql = ("INSERT INTO system_mentions "
                   "(sys_id, vol_id, pdf_page, span_start, span_end, "
                   "provenance) VALUES (?,?,?,?,?,?)")
        for vol, page, s, e in kept:
            db.execute(sql, (ent_id, vol, page, s, e, PROV))
        total_kept += len(kept)
        total_raw += len(spans)
        per_ent[ent_id] = kept

    chrono = {v: i for i, (v,) in enumerate(
        db.execute("SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    for ent_id, _n, _k, _a in EXAMS:
        vols = [s[0] for s in per_ent.get(ent_id, [])]
        first = min(vols, key=lambda v: chrono.get(v, 1 << 30)) \
            if vols else None
        last = max(vols, key=lambda v: chrono.get(v, -1)) \
            if vols else None
        db.execute("UPDATE exams SET first_vol=?, last_vol=? "
                   "WHERE exam_id=?", (first, last, ent_id))
    for ent_id, _n, _k, _a in SYSTEMS:
        vols = [s[0] for s in per_ent.get(ent_id, [])]
        first = min(vols, key=lambda v: chrono.get(v, 1 << 30)) \
            if vols else None
        last = max(vols, key=lambda v: chrono.get(v, -1)) \
            if vols else None
        db.execute("UPDATE systems SET first_vol=?, last_vol=? "
                   "WHERE sys_id=?", (first, last, ent_id))
    db.commit()
    n_exam = db.execute(
        "SELECT count(*) FROM exam_mentions").fetchone()[0]
    n_sys = db.execute(
        "SELECT count(*) FROM system_mentions").fetchone()[0]
    db.close()

    print(f"p9_mentions: {n_exam} exam + {n_sys} system anchored "
          f"mentions (dedup removed {total_raw - total_kept} overlaps)")
    for ent_id, _n, _k, _a in EXAMS + SYSTEMS:
        kept = per_ent.get(ent_id, [])
        vols = sorted({s[0] for s in kept},
                      key=lambda v: chrono.get(v, 1 << 30))
        print(f"  {ent_id:30s} {len(kept):5d} mentions  "
              f"{len(vols):2d} vols  ({vols[0] if vols else '-'}.."
              f"{vols[-1] if vols else '-'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

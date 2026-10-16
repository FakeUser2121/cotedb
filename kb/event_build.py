"""P3 step 5: scene-level dialogue events from attributed quotes.

python3 kb/event_build.py

Per the locked data model events are multi-participant scene records
(character timelines derive from them), so quotes are CLUSTERED into
scenes: consecutive attributed quotes with inter-quote gap <= 400 chars
form one scene (page breaks are layout, not scene breaks).

Each scene -> one `events` row:
  event_id   = <vol>-p<first_page>-e<n>   (deterministic per vol)
  type       = 'dialogue'
  summary    = first speaker + opening line (truncated), then participant roll
  participants: role='speaker', attribution_confidence = mean of that
  speaker's quote confidences in the scene

Idempotent by full rebuild: previous provenance='quote_scenes' rows
(participants first, FK has no cascade) are deleted, then every volume is
rebuilt deterministically. No other tables are touched.
"""
import re
import sqlite3
from collections import defaultdict

from roster_mine import DB_PATH

import sys

GAP_MAX = 400
PROV = "quote_scenes"


def clean(t, n=70):
    return re.sub(r"\s+", " ", t).strip()[:n]


def main():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        "DELETE FROM event_participants WHERE event_id IN "
        "(SELECT event_id FROM events WHERE provenance=?)", (PROV,))
    db.execute("DELETE FROM events WHERE provenance=?", (PROV,))

    chrono = db.execute(
        "SELECT vol_id FROM volumes ORDER BY chrono_order").fetchall()
    total_events = total_parts = 0
    for (vol,) in chrono:
        quotes = db.execute(
            "SELECT quote_id, pdf_page, span_start, span_end, char_id, "
            "attribution_confidence, text_verbatim FROM quotes "
            "WHERE vol_id=? AND char_id IS NOT NULL ORDER BY span_start",
            (vol,)).fetchall()
        scenes = []
        cur = []
        for q in quotes:
            if cur and q[2] - cur[-1][3] > GAP_MAX:
                scenes.append(cur)
                cur = []
            cur.append(q)
        if cur:
            scenes.append(cur)
        for n, sc in enumerate(scenes, start=1):
            page = sc[0][1]
            eid = f"{vol}-p{page}-e{n}"
            roll = []
            per_cid = defaultdict(list)
            for q in sc:
                per_cid[q[4]].append(q[5])
            for cid in sorted(per_cid, key=lambda c: -len(per_cid[c])):
                roll.append(f"{cid} ({len(per_cid[cid])})")
            summary = (f"{len(sc)}-line dialogue — "
                       f"{sc[0][4]}: {clean(sc[0][6])}"
                       if len(sc) == 1 else
                       f"{len(sc)}-line dialogue, {len(per_cid)} speaker(s): "
                       + ", ".join(roll) + f"; opens {sc[0][4]}: "
                       + clean(sc[0][6]))
            db.execute(
                "INSERT INTO events (event_id, vol_id, pdf_page, span_start, "
                "span_end, event_type, summary, provenance, confidence) "
                "VALUES (?,?,?,?,?,'dialogue',?,?,?)",
                (eid, vol, page, sc[0][2], sc[-1][3], clean(summary, 240),
                 PROV, 1.0))
            for cid, confs in per_cid.items():
                db.execute(
                    "INSERT INTO event_participants "
                    "(event_id, char_id, role, attribution_confidence) "
                    "VALUES (?,?,'speaker',?)",
                    (eid, cid, round(sum(confs) / len(confs), 3)))
                total_parts += 1
            total_events += 1

    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) "
        "VALUES ('event_build', datetime('now'), datetime('now'), ?)",
        (f"events={total_events} participants={total_parts}",))
    db.commit()
    print(f"scene events: {total_events}  participants: {total_parts}")
    db.close()


if __name__ == "__main__":
    main()

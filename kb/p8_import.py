#!/usr/bin/env python3
"""P8-2b: curated location entities + aliases (idempotent, gate on hits).

python3 kb/p8_import.py

Run order: p8_init -> p8_import -> p8_mentions -> location_analysis.

Owns: locations identity (loc_id, name, kind) + location_aliases.
Rebuilds location_mentions too (they derive from the alias set — any
entity/alias change invalidates them; p8_mentions restores them).
location_claims are authored elsewhere (location_analysis) and NOT
touched here; loc_ids are stable slugs so those FKs survive.
Function/notes prose lives in location_analysis.apply() (authored-content
model, digest-excluded) — not here. FTS is refreshed at the end so name/
kind changes stay searchable.

GATE: every curated alias form must hit the corpus >=1 time (macron
classes, word-aware) — a zero form means a typo and fails the run.

Curation decisions came from kb/p8_mine.py + context probes (2026-10-16):

  included after context check
    special-building  y1v2 incident venue, real campus building
    keyaki-mall       "complex on the school grounds" (y1v4.5 p.12)
    student-council-room  "office" and "room" are the same venue
    staff-room        y1v6 teachers' office
    uninhabited-island  dominant MTL term; "deserted island" = drift
                        (first y1v3 p.14 lodge wording, same place)
    ryokan / ski-resort  y2v8 Hokkaido trip venue (ryokan East Wing +
                        main building; ski training)
    haneda / shin-chitose-airport  y2v8 trip route (thin: 4 / 2 hits)
    white-room        ~400 hits, core setting
    hokkaido / sapporo  y2v8 visited (Sapporo Station, Clock Tower)

  excluded (recorded so the sweep is reproducible)
    kyoto, okinawa    ballot-only trip candidates (Unanimous Vote y2v5/
                      y2v8), never visited
    hospital, clinic  generic institutions (y0 career talk etc.)
    waiting-room      y0 adult political drama, not ANHS
    maid-cafe         exam business concept (y2v5), not a fixed venue
    main-building     context-dependent role (island camp y1v8 / ryokan
                      y2v8), not an ANHS entity
    dining-hall       5 hits, mixes cafeteria (y1v1) and trip-venue
                      (y2v8) senses — ambiguous, dropped
    old-school-building, schoolhouse, tennis-court, club-room,
    nurse's-office, residence-hall, shinjuku, yokohama, osaka,
    shopping-district  0 corpus hits (seed guesses)
    camp              generic class of venue across 20+ vols (island
                      base camp folds into uninhabited-island notes)
    floors, elevator, hallway, corridor, stairs  generic interiors
    sapporo-station, sapporo-clock-tower  site details -> sapporo notes
"""

import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402
from p8_init import FTS_REBUILD  # noqa: E402
from p8_mine import form_pattern  # noqa: E402

KINDS = {"campus-building", "campus-zone", "dorm", "exam-venue",
         "off-site", "city", "other"}

# loc_id, name, kind, [(raw_form, form_type), ...]
LOCATIONS = [
    ("school-building", "School Building", "campus-building",
     [("school building", "full")]),
    ("gymnasium", "Gymnasium", "campus-building",
     [("gymnasium", "full"), ("gym", "short")]),
    ("swimming-pool", "Swimming Pool", "campus-building",
     [("swimming pool", "full"), ("pool", "short")]),
    ("cafeteria", "Cafeteria", "campus-building",
     [("cafeteria", "full")]),
    ("library", "Library", "campus-building",
     [("library", "full")]),
    ("rooftop", "Rooftop", "campus-building",
     [("rooftop", "full"), ("roof", "short")]),
    ("auditorium", "Auditorium", "campus-building",
     [("auditorium", "full")]),
    ("student-council-room", "Student Council Room", "campus-building",
     [("student council room", "full"),
      ("student council office", "variant")]),
    ("staff-room", "Staff Room", "campus-building",
     [("staff room", "full")]),
    ("guidance-office", "Guidance Office", "campus-building",
     [("guidance office", "full")]),
    ("special-building", "Special Building", "campus-building",
     [("special building", "full")]),
    ("convenience-store", "Convenience Store", "campus-building",
     [("convenience store", "full")]),
    ("infirmary", "Infirmary", "campus-building",
     [("infirmary", "full")]),
    ("classroom", "Classroom", "campus-building",
     [("classroom", "full"), ("classrooms", "variant")]),
    ("campus", "Campus", "campus-zone",
     [("campus", "full"), ("school grounds", "variant")]),
    ("keyaki-mall", "Keyaki Mall", "campus-zone",
     [("keyaki mall", "full")]),
    ("athletic-field", "Athletic Field", "campus-zone",
     [("athletic field", "full")]),
    ("dormitory", "Dormitory", "dorm",
     [("dormitory", "full"), ("dorm", "short"),
      ("dorm room", "variant")]),
    ("uninhabited-island", "Uninhabited Island", "exam-venue",
     [("uninhabited island", "full"), ("deserted island", "variant")]),
    ("cruise-ship", "Cruise Ship", "exam-venue",
     [("cruise ship", "full")]),
    ("ski-resort", "Ski Resort", "exam-venue",
     [("ski resort", "full")]),
    ("ryokan", "Ryokan", "exam-venue",
     [("ryokan", "full")]),
    ("white-room", "White Room", "off-site",
     [("white room", "full")]),
    ("haneda-airport", "Haneda Airport", "off-site",
     [("haneda airport", "full"), ("haneda", "short")]),
    ("shin-chitose-airport", "Shin Chitose Airport", "off-site",
     [("shin chitose airport", "full"), ("shin chitose", "short"),
      ("shinchitose", "variant")]),
    ("tokyo", "Tokyo", "city",
     [("tokyo", "full")]),
    ("hokkaido", "Hokkaido", "city",
     [("hokkaido", "full")]),
    ("sapporo", "Sapporo", "city",
     [("sapporo", "full")]),
]


def corpus_hits(forms):
    """forms -> {form: total hits}; one corpus pass, all regexes."""
    compiled = {f: re.compile(rf"\b{form_pattern(f)}", re.I)
                for f in forms}
    hits = dict.fromkeys(forms, 0)
    for _vol, _stem, _page, _s, text in iter_pages():
        for form, rx in compiled.items():
            n = len(rx.findall(text))
            if n:
                hits[form] += n
    return hits


def main():
    forms = [f for _l, _n, _k, aliases in LOCATIONS
             for f, _t in aliases]
    dup = {f for f in forms if forms.count(f) > 1}
    if dup:
        print(f"p8_import: duplicate alias forms {sorted(dup)}")
        return 1
    for loc_id, name, kind, _aliases in LOCATIONS:
        if kind not in KINDS:
            print(f"p8_import: {loc_id} bad kind {kind!r}")
            return 1
    hits = corpus_hits(forms)
    zero = [f for f in forms if hits[f] == 0]
    if zero:
        print(f"p8_import: zero-hit alias forms {zero}")
        return 1

    db = sqlite3.connect(DB_PATH)
    db.execute("DELETE FROM location_mentions")
    db.execute("DELETE FROM location_aliases")
    db.execute("DELETE FROM locations")
    for loc_id, name, kind, aliases in LOCATIONS:
        db.execute(
            "INSERT INTO locations (loc_id, name, kind) VALUES (?,?,?)",
            (loc_id, name, kind))
        for raw, ftype in aliases:
            db.execute(
                "INSERT INTO location_aliases "
                "(loc_id, raw_form, normalized, form_type) "
                "VALUES (?,?,?,?)",
                (loc_id, raw, raw, ftype))
    db.executescript(FTS_REBUILD)
    db.commit()
    n_loc = db.execute("SELECT count(*) FROM locations").fetchone()[0]
    n_al = db.execute(
        "SELECT count(*) FROM location_aliases").fetchone()[0]
    db.close()

    print(f"p8_import: {n_loc} locations  {n_al} aliases  "
          f"(mentions cleared — rerun p8_mentions)")
    for loc_id, name, kind, aliases in LOCATIONS:
        detail = " · ".join(f"{f}={hits[f]}" for f, _t in aliases)
        print(f"  [{kind:14s}] {loc_id:24s} {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

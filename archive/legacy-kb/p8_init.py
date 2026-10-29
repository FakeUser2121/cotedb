#!/usr/bin/env python3
"""P8-1: locations layer schema for cote_kb.db (idempotent).

python3 kb/p8_init.py

Adds the entity + occurrence + claim pattern used by characters, with
anchors on the same vol_id + pdf_page + span model:

  locations          entity: loc_id slug, display name, kind, authored
                     function/notes, corpus footprint (first/last vol)
  location_aliases   every written form -> location (noise flagged)
  location_mentions  anchored occurrences (vol + page + span offsets
                     into canonical text/<stem>.txt)
  location_claims    claims pattern 1:1 (kind narrator_fact |
                     character_claim | other_reported | inference,
                     claimant, corroboration refs, evidence quote)
  locations_fts      FTS5 over name/kind/function/notes — dropped and
                     rebuilt every run so authored edits stay in sync
                     (never trigger-maintained)

location kinds (ASCII tokens): campus-building | campus-zone | dorm |
exam-venue | off-site | city | other
"""

import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "cote_kb.db")

SCHEMA = """
-- world entity identity
CREATE TABLE IF NOT EXISTS locations (
    loc_id TEXT PRIMARY KEY,          -- slug e.g. central-island
    name TEXT NOT NULL,               -- display "Central Island"
    kind TEXT NOT NULL,               -- campus-building|campus-zone|dorm|
                                      -- exam-venue|off-site|city|other
    function TEXT,                    -- one-line function summary
    notes TEXT,                       -- layout / changes-over-time prose
    first_vol TEXT, last_vol TEXT     -- corpus footprint (derived)
);

-- every written form -> location
CREATE TABLE IF NOT EXISTS location_aliases (
    alias_id INTEGER PRIMARY KEY,
    loc_id TEXT REFERENCES locations(loc_id),
    raw_form TEXT NOT NULL,
    normalized TEXT NOT NULL,         -- canon() key (lowercase, macron-folded)
    form_type TEXT,                   -- full|short|variant|epithet
    is_noise INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_loc_alias_norm
    ON location_aliases(normalized);

-- anchored occurrence layer (vol + page + span, same as quotes/events)
CREATE TABLE IF NOT EXISTS location_mentions (
    loc_id TEXT REFERENCES locations(loc_id),
    vol_id TEXT REFERENCES volumes(vol_id),
    pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    provenance TEXT
);
CREATE INDEX IF NOT EXISTS idx_loc_mentions
    ON location_mentions(loc_id, vol_id);
CREATE INDEX IF NOT EXISTS idx_loc_mentions_page
    ON location_mentions(vol_id, pdf_page);

-- claims pattern (mirrors claims, char_id -> loc_id)
CREATE TABLE IF NOT EXISTS location_claims (
    claim_id INTEGER PRIMARY KEY,
    loc_id TEXT REFERENCES locations(loc_id),
    claim TEXT NOT NULL,
    kind TEXT NOT NULL,               -- narrator_fact|character_claim|
                                      -- other_reported|inference
    claimant TEXT,                    -- char_id / 'narrator' / NULL
    perspective TEXT,
    corroboration TEXT DEFAULT 'none',  -- none|supported|contradicted
    corroboration_refs TEXT,          -- JSON list of claim/event refs
    reliability_note TEXT,
    confidence REAL DEFAULT 1.0,
    vol_id TEXT, pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    evidence_quote TEXT               -- short verbatim support
);
CREATE INDEX IF NOT EXISTS idx_loc_claims ON location_claims(loc_id);

-- FTS over authored location fields (drop+rebuild every run so
-- authored edits stay in sync; never trigger-maintained)
DROP TABLE IF EXISTS locations_fts;
CREATE VIRTUAL TABLE IF NOT EXISTS locations_fts USING fts5(
    loc_id UNINDEXED, name, kind, function, notes
);
"""

FTS_REBUILD = """
DELETE FROM locations_fts;
INSERT INTO locations_fts(rowid, loc_id, name, kind, function, notes)
    SELECT rowid, loc_id, name, kind, COALESCE(function, ''),
           COALESCE(notes, '') FROM locations;
"""


def main():
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    db.executescript(FTS_REBUILD)
    db.commit()
    n_locs = db.execute("SELECT count(*) FROM locations").fetchone()[0]
    n_alias = db.execute(
        "SELECT count(*) FROM location_aliases").fetchone()[0]
    n_fts = db.execute("SELECT count(*) FROM locations_fts").fetchone()[0]
    print(f"p8_init: schema ok — locations {n_locs}  aliases {n_alias}  "
          f"fts {n_fts}")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

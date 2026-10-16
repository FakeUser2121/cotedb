#!/usr/bin/env python3
"""P9-2: exams + systems layer schema for cote_kb.db (idempotent).

python3 kb/p9_init.py

Same entity + occurrence + claim pattern as characters/locations,
anchored on vol_id + pdf_page + span into canonical text/<stem>.txt:

  exams            entity: exam_id slug, name, kind, authored
                   rules_summary / points / conditions / organizer /
                   notes, corpus footprint (first/last vol)
  exam_aliases     every written form -> exam (noise flagged)
  exam_mentions    anchored occurrences (vol + page + span)
  exam_instances   one row per occurrence of an exam: volume anchor,
                   authored chronology, participants, outcome,
                   corroboration refs, verbatim evidence quote
  exam_claims      claims pattern (kind narrator_fact |
                   character_claim | other_reported | inference)
  systems          entity: sys_id, name, kind, authored function/notes
  system_aliases / system_mentions / system_claims
  exams_fts, systems_fts   FTS5, dropped + rebuilt every run so
                   authored edits stay in sync (never trigger-maintained)

exam kinds (ASCII tokens): written | special | event | entrance | other
system kinds (ASCII tokens): points | governance | activity |
discipline | admissions | other
"""

import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "cote_kb.db")

SCHEMA = """
-- exam entity identity
CREATE TABLE IF NOT EXISTS exams (
    exam_id TEXT PRIMARY KEY,       -- slug e.g. paper-shuffle
    name TEXT NOT NULL,             -- display "Paper Shuffle"
    kind TEXT NOT NULL,             -- written|special|event|entrance|other
    rules_summary TEXT,             -- authored: how it works
    points TEXT,                    -- authored: point values/conditions
    conditions TEXT,                -- authored: entry/elimination rules
    organizer TEXT,                 -- authored: who runs it (school, class...)
    notes TEXT,                     -- authored: narrative importance
    first_vol TEXT, last_vol TEXT   -- corpus footprint (derived)
);

CREATE TABLE IF NOT EXISTS exam_aliases (
    alias_id INTEGER PRIMARY KEY,
    exam_id TEXT REFERENCES exams(exam_id),
    raw_form TEXT NOT NULL,
    normalized TEXT NOT NULL,       -- canon() key (lowercase, macron-folded)
    form_type TEXT,                 -- full|short|variant|epithet
    is_noise INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_exam_alias_norm
    ON exam_aliases(normalized);

CREATE TABLE IF NOT EXISTS exam_mentions (
    exam_id TEXT REFERENCES exams(exam_id),
    vol_id TEXT REFERENCES volumes(vol_id),
    pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    provenance TEXT
);
CREATE INDEX IF NOT EXISTS idx_exam_mentions
    ON exam_mentions(exam_id, vol_id);
CREATE INDEX IF NOT EXISTS idx_exam_mentions_page
    ON exam_mentions(vol_id, pdf_page);

-- one row per occurrence of an exam (announcement / run / results)
CREATE TABLE IF NOT EXISTS exam_instances (
    instance_id INTEGER PRIMARY KEY,
    exam_id TEXT REFERENCES exams(exam_id),
    seq INTEGER NOT NULL,           -- occurrence order within the exam
    vol_id TEXT REFERENCES volumes(vol_id),
    pdf_page INTEGER,               -- anchor page (first ref)
    span_start INTEGER, span_end INTEGER,
    chronology TEXT,                -- authored: when/how this run unfolds
    participants TEXT,              -- authored: who competes / who is bound
    outcome TEXT,                   -- authored: what happened, points shift
    corroboration_refs TEXT,        -- JSON list of "vol p.N" refs
    evidence_quote TEXT,            -- short verbatim support
    confidence REAL DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS idx_exam_instances
    ON exam_instances(exam_id, vol_id);

CREATE TABLE IF NOT EXISTS exam_claims (
    claim_id INTEGER PRIMARY KEY,
    exam_id TEXT REFERENCES exams(exam_id),
    claim TEXT NOT NULL,
    kind TEXT NOT NULL,             -- narrator_fact|character_claim|
                                    -- other_reported|inference
    claimant TEXT,                  -- char_id / 'narrator' / NULL
    perspective TEXT,
    corroboration TEXT DEFAULT 'none',   -- none|supported|contradicted
    corroboration_refs TEXT,        -- JSON list of claim/event refs
    reliability_note TEXT,
    confidence REAL DEFAULT 1.0,
    vol_id TEXT, pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    evidence_quote TEXT             -- short verbatim support
);
CREATE INDEX IF NOT EXISTS idx_exam_claims ON exam_claims(exam_id);

-- system entity identity
CREATE TABLE IF NOT EXISTS systems (
    sys_id TEXT PRIMARY KEY,        -- slug e.g. private-points
    name TEXT NOT NULL,             -- display "Private Points"
    kind TEXT NOT NULL,             -- points|governance|activity|
                                    -- discipline|admissions|other
    function TEXT,                  -- one-line function summary
    notes TEXT,                     -- authored mechanics prose
    first_vol TEXT, last_vol TEXT   -- corpus footprint (derived)
);

CREATE TABLE IF NOT EXISTS system_aliases (
    alias_id INTEGER PRIMARY KEY,
    sys_id TEXT REFERENCES systems(sys_id),
    raw_form TEXT NOT NULL,
    normalized TEXT NOT NULL,
    form_type TEXT,                 -- full|short|variant|epithet
    is_noise INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sys_alias_norm
    ON system_aliases(normalized);

CREATE TABLE IF NOT EXISTS system_mentions (
    sys_id TEXT REFERENCES systems(sys_id),
    vol_id TEXT REFERENCES volumes(vol_id),
    pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    provenance TEXT
);
CREATE INDEX IF NOT EXISTS idx_sys_mentions
    ON system_mentions(sys_id, vol_id);
CREATE INDEX IF NOT EXISTS idx_sys_mentions_page
    ON system_mentions(vol_id, pdf_page);

CREATE TABLE IF NOT EXISTS system_claims (
    claim_id INTEGER PRIMARY KEY,
    sys_id TEXT REFERENCES systems(sys_id),
    claim TEXT NOT NULL,
    kind TEXT NOT NULL,             -- narrator_fact|character_claim|
                                    -- other_reported|inference
    claimant TEXT,
    perspective TEXT,
    corroboration TEXT DEFAULT 'none',
    corroboration_refs TEXT,
    reliability_note TEXT,
    confidence REAL DEFAULT 1.0,
    vol_id TEXT, pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    evidence_quote TEXT
);
CREATE INDEX IF NOT EXISTS idx_sys_claims ON system_claims(sys_id);

-- FTS over authored fields (drop+rebuild every run)
DROP TABLE IF EXISTS exams_fts;
CREATE VIRTUAL TABLE IF NOT EXISTS exams_fts USING fts5(
    exam_id UNINDEXED, name, kind, rules_summary, points, conditions,
    organizer, notes
);
DROP TABLE IF EXISTS systems_fts;
CREATE VIRTUAL TABLE IF NOT EXISTS systems_fts USING fts5(
    sys_id UNINDEXED, name, kind, function, notes
);
"""

FTS_REBUILD = """
DELETE FROM exams_fts;
INSERT INTO exams_fts(rowid, exam_id, name, kind, rules_summary, points,
    conditions, organizer, notes)
    SELECT rowid, exam_id, name, kind, COALESCE(rules_summary, ''),
           COALESCE(points, ''), COALESCE(conditions, ''),
           COALESCE(organizer, ''), COALESCE(notes, '')
    FROM exams;
DELETE FROM systems_fts;
INSERT INTO systems_fts(rowid, sys_id, name, kind, function, notes)
    SELECT rowid, sys_id, name, kind, COALESCE(function, ''),
           COALESCE(notes, '') FROM systems;
"""


def main():
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    db.executescript(FTS_REBUILD)
    db.commit()
    for table in ("exams", "exam_aliases", "exam_mentions",
                  "exam_instances", "exam_claims", "systems",
                  "system_aliases", "system_mentions", "system_claims",
                  "exams_fts", "systems_fts"):
        n = db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"p9_init: {table} {n}")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

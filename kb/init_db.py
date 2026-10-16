#!/usr/bin/env python3
"""P0: create/upgrade cote_kb.db schema (evidence DB, source of truth)."""
import datetime
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "cote_kb.db")

SCHEMA = """
-- corpus registry
CREATE TABLE IF NOT EXISTS volumes (
    vol_id TEXT PRIMARY KEY, title TEXT, file_stem TEXT,
    chrono_order REAL, kind TEXT, pdf_pages INTEGER, txt_pages INTEGER,
    chars INTEGER, empty_pages INTEGER, validated INTEGER
);

-- stable character identity
CREATE TABLE IF NOT EXISTS characters (
    char_id TEXT PRIMARY KEY,          -- slug e.g. honami-ichinose
    canonical_name TEXT,               -- display "Ichinose Honami"
    name_order TEXT,                   -- family-given | given-family | unknown
    tier INTEGER,                      -- 1 main 2 mid 3 bg 4 one-off 9 unidentified
    mid_type TEXT,                     -- authority|rivals|allies|peers|family|outside
    status TEXT DEFAULT 'provisional', -- provisional|confirmed|merged|noise
    merged_into TEXT,                  -- char_id if merged
    notes TEXT,
    first_vol TEXT, last_vol TEXT
);

-- every written form -> character (incl. noise stoplist via is_noise)
CREATE TABLE IF NOT EXISTS aliases (
    alias_id INTEGER PRIMARY KEY,
    char_id TEXT REFERENCES characters(char_id),
    raw_form TEXT NOT NULL,
    normalized TEXT NOT NULL,          -- macron-folded lowercase key
    form_type TEXT,                    -- full|given|family|honorific|nickname|epithet|variant
    is_noise INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_alias_norm ON aliases(normalized);

-- events: scene-level facts (multi-participant)
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,         -- e.g. y1v1-p250-e3
    vol_id TEXT REFERENCES volumes(vol_id),
    pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,  -- char offsets into canonical text/<stem>.txt
    event_type TEXT,                   -- action|dialogue|thought|revelation|relationship|status_change|mention
    summary TEXT,
    provenance TEXT,
    confidence REAL DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS idx_events_vol_page ON events(vol_id, pdf_page);

CREATE TABLE IF NOT EXISTS event_participants (
    event_id TEXT REFERENCES events(event_id),
    char_id TEXT REFERENCES characters(char_id),
    role TEXT,                         -- actor|target|speaker|addressee|observer|referenced
    attribution_confidence REAL DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS idx_part_char ON event_participants(char_id);

-- complete verbatim dialogue
CREATE TABLE IF NOT EXISTS quotes (
    quote_id INTEGER PRIMARY KEY,
    char_id TEXT REFERENCES characters(char_id),  -- NULL = unattributed
    vol_id TEXT REFERENCES volumes(vol_id),
    pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    text_verbatim TEXT NOT NULL,
    addressee TEXT,                    -- char_id or NULL
    tone TEXT,
    context TEXT,
    attribution_confidence REAL DEFAULT 1.0,
    reviewed INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_quotes_char ON quotes(char_id);

-- claims with full attribution model (evidence != interpretation)
CREATE TABLE IF NOT EXISTS claims (
    claim_id INTEGER PRIMARY KEY,
    char_id TEXT REFERENCES characters(char_id),
    claim TEXT NOT NULL,
    kind TEXT NOT NULL,                -- narrator_fact|character_claim|other_reported|inference
    claimant TEXT,                     -- who asserts (char_id / 'narrator' / NULL)
    perspective TEXT,                  -- POV the passage filters through
    corroboration TEXT DEFAULT 'none', -- none|supported|contradicted
    corroboration_refs TEXT,           -- JSON list of claim/event refs
    reliability_note TEXT,
    confidence REAL DEFAULT 1.0,
    vol_id TEXT, pdf_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    evidence_quote TEXT                -- short verbatim support
);
CREATE INDEX IF NOT EXISTS idx_claims_char ON claims(char_id);

CREATE TABLE IF NOT EXISTS relations (
    rel_id INTEGER PRIMARY KEY,
    char_a TEXT REFERENCES characters(char_id),
    char_b TEXT REFERENCES characters(char_id),
    rel_type TEXT,                     -- rival|ally|superior|family|...
    direction_note TEXT,
    valid_from_vol TEXT, valid_to_vol TEXT,
    evidence_refs TEXT                 -- JSON list of event/claim refs
);

CREATE TABLE IF NOT EXISTS status_timeline (
    char_id TEXT REFERENCES characters(char_id),
    vol_id TEXT REFERENCES volumes(vol_id),
    situation TEXT, knowledge_state TEXT, changes TEXT, why TEXT,
    evidence_refs TEXT
);

CREATE TABLE IF NOT EXISTS interpretations (
    interp_id INTEGER PRIMARY KEY,
    char_id TEXT REFERENCES characters(char_id),
    claim TEXT NOT NULL,
    basis_refs TEXT,                   -- JSON evidence refs
    confidence REAL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS unknown_entities (
    ent_id TEXT PRIMARY KEY,
    description TEXT,
    context_vol TEXT, context_page INTEGER,
    span_start INTEGER, span_end INTEGER,
    status TEXT DEFAULT 'open',        -- open|resolved
    resolved_char_id TEXT
);

-- raw token counts per volume (gap detection)
CREATE TABLE IF NOT EXISTS mention_stats (
    vol_id TEXT, token TEXT, count INTEGER,
    PRIMARY KEY (vol_id, token)
);

-- char x volume workflow grid
CREATE TABLE IF NOT EXISTS coverage (
    char_id TEXT, vol_id TEXT,
    status TEXT DEFAULT 'pending',     -- pending|occurrences|quotes|drafted|verified
    PRIMARY KEY (char_id, vol_id)
);

CREATE TABLE IF NOT EXISTS provenance (
    run_id INTEGER PRIMARY KEY,
    method TEXT, started TEXT, finished TEXT, notes TEXT
);

-- roster mining candidates (P1 working table)
CREATE TABLE IF NOT EXISTS roster_candidates (
    cand_id INTEGER PRIMARY KEY,
    raw_form TEXT,
    normalized TEXT,
    total_count INTEGER,
    signals TEXT,                      -- JSON list e.g. ["E1","E2"]
    sample_contexts TEXT,              -- JSON list of {vol,page,snippet}
    classification TEXT DEFAULT 'unreviewed', -- unreviewed|character|noise|unknown
    char_id TEXT,
    reviewer_note TEXT
);
CREATE INDEX IF NOT EXISTS idx_cand_norm ON roster_candidates(normalized);

-- FTS over quotes + claims for research queries
CREATE VIRTUAL TABLE IF NOT EXISTS quotes_fts USING fts5(
    text_verbatim, content='quotes', content_rowid='quote_id'
);
CREATE TRIGGER IF NOT EXISTS quotes_ai AFTER INSERT ON quotes BEGIN
    INSERT INTO quotes_fts(rowid, text_verbatim) VALUES (new.quote_id, new.text_verbatim);
END;
"""


def main():
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    db.commit()
    n = db.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]
    db.close()
    print(f"Schema ready: {n} tables in {DB_PATH}")


if __name__ == "__main__":
    main()

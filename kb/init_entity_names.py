#!/usr/bin/env python3
"""Create the names table and seed it from the names the site shows today.

`entity_names` is the one place a reader-facing spelling lives. The build reads
it before it reads any romanisation rule, so changing what a page calls
something is a row update, not a code change. Seeding is INSERT OR IGNORE:
running this again never overwrites a name that was chosen deliberately.

    python3 kb/init_entity_names.py            # create + seed
    python3 kb/init_entity_names.py --report   # show what would be added
    python3 kb/init_entity_names.py --export   # write the committed seed file

The database is local build state and is not in git, so the table cannot be
the only home of a decided spelling: `kb/entity_names.tsv` is the seed every
fresh database imports, and `--export` writes the table back to it after a
decision. A row in the seed wins over the computed fallback.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "cote_kb.db"
SEED = Path(__file__).with_name("entity_names.tsv")

DDL = """
CREATE TABLE IF NOT EXISTS entity_names (
    entity_type TEXT NOT NULL,        -- character | volume | exam | system | place
    entity_id   TEXT NOT NULL,        -- the permanent id
    display_name TEXT NOT NULL,       -- the one spelling every page shows
    sort_key    TEXT,                 -- optional override of the computed key
    notes       TEXT,                 -- why this spelling, when it differs
    PRIMARY KEY (entity_type, entity_id)
);
"""


def rows(con):
    out = []
    for cid, canon in con.execute(
            "SELECT char_id, canonical_name FROM characters "
            "WHERE merged_into IS NULL"):
        out.append(("character", cid, site_arch.display_name(canon, cid),
                    site_arch.initials_first(site_arch.display_name(canon, cid))))
    for vol_id, in con.execute("SELECT vol_id FROM volumes"):
        out.append(("volume", vol_id, site_arch.volume_label(vol_id), ""))
    for eid, name in con.execute("SELECT exam_id, name FROM exams"):
        out.append(("exam", eid, name, ""))
    for sid, name in con.execute("SELECT sys_id, name FROM systems"):
        out.append(("system", sid, name, ""))
    for lid, name in con.execute("SELECT loc_id, name FROM locations"):
        out.append(("place", lid, name, ""))
    return out


def seed_rows():
    """Rows from the committed seed file, if there is one."""
    if not SEED.exists():
        return []
    out = []
    for line in SEED.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        while len(parts) < 5:
            parts.append("")
        out.append(tuple(parts[:5]))
    return out


def main():
    con = sqlite3.connect(DB_PATH)
    con.executescript(DDL)
    have = {(t, i) for t, i in con.execute(
        "SELECT entity_type, entity_id FROM entity_names")}
    if "--export" in sys.argv:
        out = ["# entity_type\tentity_id\tdisplay_name\tsort_key\tnotes"]
        for row in con.execute(
                "SELECT entity_type, entity_id, display_name, "
                "COALESCE(sort_key, ''), COALESCE(notes, '') "
                "FROM entity_names ORDER BY entity_type, entity_id"):
            out.append("\t".join(row))
        SEED.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"seed: {len(out) - 1} names → {SEED.name}")
        return 0
    seeds = [r for r in seed_rows() if (r[0], r[1]) not in have]
    todo = [r for r in rows(con) if (r[0], r[1]) not in have
            and (r[0], r[1]) not in {(s[0], s[1]) for s in seeds}]
    if "--report" in sys.argv:
        print(f"would add {len(seeds)} seeded and {len(todo)} computed names "
              f"({len(have)} already set)")
        for t, i, n, _s in (seeds + todo)[:20]:
            print(f"  {t:9} {i:28} {n}")
        return 0
    con.executemany(
        "INSERT OR IGNORE INTO entity_names "
        "(entity_type, entity_id, display_name, sort_key, notes) "
        "VALUES (?,?,?,?,?)", seeds)
    con.executemany(
        "INSERT OR IGNORE INTO entity_names "
        "(entity_type, entity_id, display_name, sort_key) VALUES (?,?,?,?)",
        todo)
    con.commit()
    total = con.execute("SELECT count(*) FROM entity_names").fetchone()[0]
    print(f"entity_names: {len(seeds)} seeded, {len(todo)} computed, "
          f"{total} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())

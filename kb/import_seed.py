#!/usr/bin/env python3
"""Import verified external seed list into characters/aliases (class-labeled).

Parses kb/external_seed_wattpad.txt, creates characters for entries present in
corpus (verified by surname hits > 0 via grep already done in check_seed),
assigns given-name alias only when given name is unique across seed entries,
marks matching roster_candidates rows as classified.
"""
import json
import os
import re
import sqlite3
from collections import defaultdict

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_mine import normalize, fold, iter_pages  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "kb", "external_seed_wattpad.txt")
DB = os.path.join(ROOT, "cote_kb.db")

# seed class/year -> (mid_type_hint, notes)
CLASS_NOTES = {}


def slug(canonical):
    return re.sub(r"[^a-z0-9]+", "-", fold(canonical).lower()).strip("-")


def surname_hits(fam):
    """count surname (folded) across corpus quickly using volume text files."""
    pat = re.compile(rf"\b{re.escape(fold(fam))}\b")
    total = 0
    for fn in os.listdir(os.path.join(ROOT, "text")):
        if fn.endswith(".txt"):
            total += len(pat.findall(fold(open(os.path.join(ROOT, "text", fn), encoding="utf-8").read())))
    return total


def main():
    entries = []
    with open(SEED, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#") or "\t" not in line:
                continue
            parts = line.split("\t")
            placement, name = parts[0].strip(), parts[-1].strip()
            if not name or name.startswith("("):
                continue
            if "," in name:
                fam, giv = [p.strip() for p in name.split(",", 1)]
            else:
                fam, giv = name.strip(), ""
            entries.append({"placement": placement, "fam": fam, "giv": giv, "raw": name})

    # pre-count surname hits
    for e in entries:
        e["hits"] = surname_hits(e["fam"])

    present = [e for e in entries if e["hits"] > 0]

    # given-name uniqueness among present entries
    giv_count = defaultdict(int)
    for e in present:
        if e["giv"]:
            giv_count[normalize(e["giv"])] += 1

    db = sqlite3.connect(DB)
    created = merged_cands = 0
    for e in present:
        canonical = f"{e['fam']} {e['giv']}".strip() if e["giv"] else e["fam"]
        cid = slug(canonical)
        # if slug already exists (KNOWN table), attach alias instead
        exists = db.execute("SELECT 1 FROM characters WHERE char_id=?", (cid,)).fetchone()
        db.execute(
            "INSERT OR IGNORE INTO characters "
            "(char_id, canonical_name, name_order, tier, status, notes) VALUES (?,?,?,?,?,?)",
            (cid, canonical, "family-given" if e["giv"] else "unknown",
             None, "seed", f"seed: {e['placement']} | corpus surname hits {e['hits']}"),
        )
        if not exists:
            created += 1
        # alias: family form (always), full (always), given (only if unique)
        for form, ftype in ((e["fam"], "family"), (canonical, "full")):
            db.execute(
                "INSERT OR IGNORE INTO aliases (char_id, raw_form, normalized, form_type, is_noise) "
                "VALUES (?,?,?,?,0)",
                (cid, form, normalize(form), ftype),
            )
        if e["giv"] and giv_count[normalize(e["giv"])] == 1:
            db.execute(
                "INSERT OR IGNORE INTO aliases (char_id, raw_form, normalized, form_type, is_noise) "
                "VALUES (?,?,?,?,0)",
                (cid, e["giv"], normalize(e["giv"]), "given"),
            )
        # claim candidate: fresh unreviewed OR stale E1 provisional shell
        db.execute(
            "UPDATE roster_candidates SET classification='character', char_id=?, "
            "reviewer_note=? WHERE normalized=? AND "
            "(classification='unreviewed' OR char_id LIKE 'provisional-%')",
            (cid, f"seed import: {e['placement']}", normalize(e["fam"])),
        )

    # ambiguous given names report
    amb = {g: c for g, c in giv_count.items() if c > 1}

    # shell cleanup: re-point candidates still on provisional-<key> shells to
    # any real character that owns an alias with the same key; then drop orphans
    shells = [r[0] for r in db.execute(
        "SELECT char_id FROM characters WHERE char_id LIKE 'provisional-%'")]
    repointed = dropped = 0
    for sh in shells:
        key = sh[len("provisional-"):]
        owner = db.execute(
            "SELECT a.char_id FROM aliases a JOIN characters c "
            "ON c.char_id=a.char_id "
            "WHERE a.normalized=? AND c.char_id NOT LIKE 'provisional-%' "
            "LIMIT 1", (key,)).fetchone()
        if owner:
            repointed += db.execute(
                "UPDATE roster_candidates SET char_id=?, "
                "reviewer_note=COALESCE(reviewer_note,'') || ' [shell->seed]' "
                "WHERE char_id=? AND classification='character'",
                (owner[0], sh)).rowcount
            db.execute(
                "UPDATE quotes SET char_id=? WHERE char_id=?", (owner[0], sh))
        nrefs = db.execute(
            "SELECT COUNT(*) FROM roster_candidates WHERE char_id=?", (sh,)).fetchone()[0]
        if nrefs == 0:
            db.execute("DELETE FROM aliases WHERE char_id=?", (sh,))
            used = False
            for tbl, col in (("event_participants", "char_id"),
                             ("claims", "char_id"), ("coverage", "char_id"),
                             ("quotes", "char_id")):
                try:
                    c = db.execute(
                        f"SELECT COUNT(*) FROM {tbl} WHERE {col}=?", (sh,)).fetchone()[0]
                    if c:
                        used = True
                except sqlite3.Error:
                    pass
            if not used:
                db.execute("DELETE FROM characters WHERE char_id=?", (sh,))
                dropped += 1

    db.commit()
    total_chars = db.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    unrev = db.execute(
        "SELECT COUNT(*) FROM roster_candidates WHERE classification='unreviewed'"
    ).fetchone()[0]
    db.close()
    print(f"seed entries present in corpus: {len(present)} (new chars created: {created})")
    print(f"shell cleanup: {repointed} candidates re-pointed, {dropped} shells dropped")
    print(f"total characters: {total_chars}  unreviewed candidates: {unrev}")
    if amb:
        print(f"ambiguous given names (shared, NOT aliased): {sorted(amb)}")


if __name__ == "__main__":
    main()

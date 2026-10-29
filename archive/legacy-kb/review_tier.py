#!/usr/bin/env python3
"""P2 review tier: identity merges/re-splits, alias policy, tier assignment.

Pipeline (runs LAST; every decision here is reproduced on a full re-run):
  roster_mine -> classify -> import_seed -> review_pass1 -> review_pass2
   -> review_pass3 -> review_tier
Idempotent: a second run must print all-zero effect stats.

Decisions persisted (corpus-verified 2026-10-16):
  merges (loser -> winner; loser row deleted, notes preserved on winner):
    katsuragi-kohei    -> katsuragi-kouhei    seed 'Kohei' vs KNOWN 'Kouhei'
    kushida-kikyo      -> kushida-kikyou      seed 'Kikyo' vs KNOWN 'Kikyou'
    kiryuuin-fuuka     -> kiryuin-fuuka       pass2 canonical fixed to seed
                                               spelling (no dup slug)
    yashima-mariko     -> yajima-mariko       Y1V4 roster TL typo
    ikari              -> ikari-momoko        seed bare 'Class 3-B Ikari'
    tokinari-tsukishiro -> tsukishiro         Y0 full name (V0 p27);
                                               'Tokinari' is the GIVEN
    yoshimoto-kousetsu -> yoshimoto-kosetsu   seed 'Kousetsu' vs corpus
                                               'Kosetsu' (Kōsetsu)
  re-splits (earlier ad-hoc dup-slug merge was WRONG):
    seed bare 'Onodera'  (Y1V8 instructor, 3rd-Yr Class B) -> own char
    seed bare 'Ishikura' (3rd-Yr Class B student, Y1V8)    -> own char
    both distinct from Onodera Kayano / Ishikura Kayoko; the bare keys
    stay claimed to the students with [P2-collision] notes (volume
    disambiguation happens at P3)
  removals:
    horikita-tomiko -> candidate noise, char deleted (Y1V3 p18 joke
                       answer: 'Tomiko. Horikita Tomiko.')
    kouejin         -> alias variant on kouenji-rokusuke ('Kouejin-kun'
                       Y1V1 pool race = TL typo of Kouenji)
  new chars:
    ikari-sensei — Y2V5 faculty ('gathered the homeroom teachers of the
    four classes'); third Ikari, distinct from student Ikari Momoko
  Himeno: id himeno -> himeno-yuki, canonical 'Himeno Yuki', 2nd-Yr Class B
    (Y2V4.5 OAA 'Second-Year Class B Himeno Yuki'; Y2V6 Ichinose class;
    Y2V12 first-discussion roster header swap)
  Matsuo father (butler Y1V7/Y2V8 suicide mention) vs son Matsuo
    Eiichirou (Y2V3): DISTINCT people — explicitly NOT merged;
    [P2-distinct] notes both sides
  Kijima: V0-only Senator Kijima-sensei (politician); no student
    same-surname in Y1+ — note rewritten in place
  alias policy: given aliases removed for {haruka, satoru, shigeru,
    kyosuke, nagisa, todo, ko} (candidates stay the authority);
    'Toshizou' removed from student Kamogawa; 'Eiichiro' removed from
    butler Matsuo
  tiers: kouenji-rokusuke -> 2 (1659); NULL band max-count >=5 -> 3
    else -> 4; tier4 max-count >=10 -> 3; recreated 3rd-yr ishikura
    forced -> 3 (Y1V8 presence); tier 9 unused
  2nd recall strata (25/75/95 depth): credits-page staff alya/budos/
    inkpetagon -> noise; 'Miyaki' (Y2V6) -> variant claim on
    miyake-akito; 'blueocean'/'kkiyotaka' correctly absent from the
    roster (café name / 'K-Kiyotaka' stammer — mining filters)
"""
import datetime
import os
import re
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_mine import normalize  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "cote_kb.db")

CHILD = (
    "aliases", "quotes", "coverage", "claims", "event_participants",
    "relations", "status_timeline", "interpretations", "mention_stats",
)

MERGES = [
    ("katsuragi-kohei", "katsuragi-kouhei",
     "seed 'Katsuragi, Kohei' spelling vs KNOWN 'Kouhei' — same person"),
    ("kushida-kikyo", "kushida-kikyou",
     "seed 'Kushida, Kikyo' spelling vs KNOWN 'Kikyou' — same person"),
    ("kiryuuin-fuuka", "kiryuin-fuuka",
     "pass2 canonical spelling fixed to seed 'Kiryuin, Fuuka' (no dup slug)"),
    ("yashima-mariko", "yajima-mariko",
     "Y1V4 roster TL typo 'Yashima Mariko' = seed 'Yajima, Mariko'"),
    ("ikari", "ikari-momoko",
     "seed bare 'Class 3-B Ikari' = Ikari Momoko (group rep); faculty "
     "Ikari-sensei (Y2V5) is a third, distinct char"),
    ("tokinari-tsukishiro", "tsukishiro",
     "Y0 full name 'Tokinari Tsukishiro' (V0 p27) = bare seed 'Tsukishiro'; "
     "'Tokinari' is the given name"),
    ("yoshimoto-kousetsu", "yoshimoto-kosetsu",
     "seed 'Yoshimoto, Kousetsu' vs pass2 canonical 'Kosetsu' (corpus "
     "'Kōsetsu') — same person"),
]

PEOPLE = [
    ("onodera", "Onodera", "Onodera",
     "[P2-instr] 3rd-Year Class B homeroom teacher: Y1V8 'the teacher "
     "entered the room. \"I'm Onodera, the instructor in charge of "
     "third-year Class B\"' — distinct from student Onodera Kayano "
     "(seed Class 1-D); bare-key mentions volume-disambiguated at P3"),
    ("ishikura", "Ishikura", "Ishikura",
     "[P2-instr] 3rd-Yr Class B student (Y1V8 card-game scene with "
     "Nagumo; council/club 'Vice President' titles TL-ambiguous — "
     "student-council VP = Kiriyama) — distinct from Ishikura Kayoko "
     "(seed eval sheet); bare-key mentions volume-disambiguated at P3"),
    ("ikari-sensei", "Ikari-sensei", "Ikari",
     "[P2-instr] faculty: Y2V5 male teacher who 'gathered the homeroom "
     "teachers of the four classes' — third Ikari, distinct from "
     "student Ikari Momoko"),
]

AMBIG_GIVEN = ("haruka", "satoru", "shigeru", "kyosuke", "nagisa",
               "todo", "ko")

HIMENO_OLD = "1-B student (Y2V10); family-only mention"
HIMENO_NEW = (
    "2nd-Yr Class B / Ichinose class: full name 'Himeno Yuki' "
    "(Y2V4.5 OAA 'Second-Year Class B Himeno Yuki'; Y2V6 "
    "'Himeno-san from Ichinose-san's class'; Y3V1 "
    "'Himeno Yuki — 69 pts' vs Sudou). Y2V12 first-"
    "discussion roster header '2nd Year Class D' over her "
    "name is swapped — same block files undisputed 2-D "
    "Sudou/Miyake/Matsushita/Onodera/Nishimura/Ichihashi "
    "under 'Class B' — P2")

TOMIKO_NOTE = (
    "[P2-not-a-person] Ayanokouji joke first name for Horikita Suzune "
    "(Y1V3 p18: \"Tomiko. Horikita Tomiko.\" -> \"sorry, I was wrong. "
    "It's Suzune.\") — candidate noise, char deleted"
)

# 2nd recall strata (25/75/95, P2): real-world TL staff on the Y2V9.75
# credits page — never people of the corpus
CREDITS_NOISE = {
    "alya": "RoyalMTLs credits: Illustrator (Y2V9.75 p17) — real-world staff",
    "budos": "RoyalMTLs credits: Editor (Y2V9.75 p17) — real-world staff",
    "inkpetagon": "RoyalMTLs credits: Japanese Proofreader (Y2V9.75 p17) "
                  "— real-world staff",
}

# normalized key -> (target char_id, alias raw, form_type, note)
VARIANT_CLAIMS = [
    ("miyaki", "miyake-akito", "Miyaki", "variant",
     "TL typo of Miyake (Y2V6 Haruka SS: 'Miyaki didn't have the courage to "
     "ask her' — Miyake replying to Haruka) — P2"),
]

CNOTES = {
    "onodera": ("[P2-collision]",
                "[P2-collision] bare 'Onodera' spans seed instructor "
                "(Y1V8 3rd-Yr Class B, char 'onodera') and Onodera Kayano "
                "(Y1 student) — disambiguate by volume at P3"),
    "ishikura": ("[P2-collision]",
                 "[P2-collision] bare 'Ishikura' spans seed 3rd-Yr Class B "
                 "(Y1V8, char 'ishikura') and Ishikura Kayoko (Y1 eval "
                 "sheet) — disambiguate by volume at P3"),
    "ikari": ("[P2-collision]",
              "[P2-collision] bare 'Ikari' = student Ikari Momoko (seed "
              "3-B, merged); faculty Ikari-sensei (Y2V5) = separate char "
              "'ikari-sensei'"),
    "matsuo": ("[P2-matsuo]",
               "[P2-matsuo] two distinct people, NOT merged: father/butler "
               "Matsuo (Y1V7, Y2V8 suicide mention) vs son Matsuo "
               "Eiichirou (Y2V3) — bare key mixes both, disambiguate by "
               "volume at P3"),
    "koejin": ("[P2-typo]",
               "[P2-typo] 'Kouejin-kun' Y1V1 pool race = Kouenji Rokusuke "
               "(TL typo) — alias variant, dup char deleted"),
}


def ensure_alias(db, cid, raw, ftype):
    key = normalize(raw)
    if db.execute("SELECT 1 FROM aliases WHERE char_id=? AND normalized=?",
                  (cid, key)).fetchone():
        return
    db.execute(
        "INSERT INTO aliases (char_id, raw_form, normalized, form_type, is_noise) "
        "VALUES (?,?,?,?,0)", (cid, raw, key, ftype))


def ensure_note(db, cid, tag, text):
    return db.execute(
        "UPDATE characters SET notes=COALESCE(notes,'') || ? "
        "WHERE char_id=? AND instr(COALESCE(notes,''), ?)=0",
        (" | " + text, cid, tag)).rowcount


def note_replace(db, cid, old, new):
    return db.execute(
        "UPDATE characters SET notes=REPLACE(COALESCE(notes,''), ?, ?) "
        "WHERE char_id=? AND instr(COALESCE(notes,''), ?)>0",
        (old, new, cid, old)).rowcount


def cnote(db, key, tag, text):
    return db.execute(
        "UPDATE roster_candidates SET reviewer_note=COALESCE(reviewer_note,'') "
        "|| ? WHERE normalized=? AND instr(COALESCE(reviewer_note,''), ?)=0",
        (" " + text, key, tag)).rowcount


def repoint(db, src, dst, note):
    n = db.execute(
        "UPDATE roster_candidates SET char_id=?, "
        "reviewer_note=COALESCE(reviewer_note,'') || ? WHERE char_id=?",
        (dst, note, src)).rowcount
    for tbl in CHILD:
        try:
            db.execute(f"UPDATE {tbl} SET char_id=? WHERE char_id=?",
                       (dst, src))
        except sqlite3.Error:
            pass
    return n


def purge(db, cid, stats, label):
    for tbl in CHILD:
        try:
            db.execute(f"DELETE FROM {tbl} WHERE char_id=?", (cid,))
        except sqlite3.Error:
            pass
    n = db.execute("DELETE FROM characters WHERE char_id=?", (cid,)).rowcount
    if n:
        stats[label] += 1
    return n


def merge(db, src, dst, reason, stats):
    if not db.execute("SELECT 1 FROM characters WHERE char_id=?",
                      (src,)).fetchone():
        return
    if not db.execute("SELECT 1 FROM characters WHERE char_id=?",
                      (dst,)).fetchone():
        stats["WARN merge target missing"] += 1
        return
    lnotes = db.execute("SELECT COALESCE(notes,'') FROM characters "
                        "WHERE char_id=?", (src,)).fetchone()[0]
    repoint(db, src, dst, f" [P2-merge -> {dst}]")
    text = f"[P2-merge {src}] {reason}"
    if lnotes:
        text += f" | from '{src}': {lnotes}"
    ensure_note(db, dst, f"[P2-merge {src}]", text)
    db.execute("DELETE FROM characters WHERE char_id=?", (src,))
    stats["merges applied"] += 1


def ensure_person(db, cid, canonical, note, stats):
    if not db.execute("SELECT 1 FROM characters WHERE char_id=?",
                      (cid,)).fetchone():
        db.execute(
            "INSERT INTO characters "
            "(char_id, canonical_name, name_order, tier, status, notes) "
            "VALUES (?,?,?,NULL,'confirmed','')",
            (cid, canonical, "single"))
        stats["chars created"] += 1
    else:
        n = db.execute(
            "UPDATE characters SET canonical_name=?, name_order='single', "
            "status='confirmed' WHERE char_id=? AND "
            "(canonical_name!=? OR name_order!='single' OR status!='confirmed')",
            (canonical, cid, canonical)).rowcount
        if n:
            stats["person canonical/status upgraded"] += 1
    if ensure_note(db, cid, "[P2-instr]", note):
        stats["person notes"] += 1


def rename_char(db, old, new):
    for tbl in ("roster_candidates",) + CHILD:
        try:
            db.execute(f"UPDATE {tbl} SET char_id=? WHERE char_id=?",
                       (new, old))
        except sqlite3.Error:
            pass
    db.execute("UPDATE characters SET char_id=? WHERE char_id=?", (new, old))
    try:
        db.execute("UPDATE characters SET merged_into=? WHERE merged_into=?",
                   (new, old))
    except sqlite3.Error:
        pass


def main():
    db = sqlite3.connect(DB)
    stats = defaultdict(int)

    # ---- 2nd recall strata fixes: credits noise + typo variants ----
    for key, note in sorted(CREDITS_NOISE.items()):
        n = db.execute(
            "UPDATE roster_candidates SET classification='noise', char_id=NULL, "
            "reviewer_note=? WHERE normalized=? AND classification='unreviewed'",
            (f"P2 credits-noise: {note}", key)).rowcount
        stats["credits -> noise"] += n
    for key, tcid, raw, ftype, note in VARIANT_CLAIMS:
        if not db.execute("SELECT 1 FROM characters WHERE char_id=?",
                          (tcid,)).fetchone():
            stats["WARN variant target missing"] += 1
            continue
        ensure_alias(db, tcid, raw, ftype)
        n = db.execute(
            "UPDATE roster_candidates SET classification='character', "
            "char_id=?, reviewer_note=? WHERE normalized=? AND "
            "(classification='unreviewed' OR classification='unknown')",
            (tcid, f"P2 variant claim: {note}", key)).rowcount
        stats["variant claims"] += n

    # ---- removals ----
    n = db.execute(
        "UPDATE roster_candidates SET classification='noise', char_id=NULL, "
        "reviewer_note=? WHERE normalized='tomiko' AND "
        "(classification!='noise' OR char_id IS NOT NULL)",
        (TOMIKO_NOTE,)).rowcount
    stats["tomiko -> noise"] += n
    purge(db, "horikita-tomiko", stats, "chars deleted (not-a-person)")

    if db.execute("SELECT 1 FROM characters WHERE char_id='kouejin'").fetchone():
        repoint(db, "kouejin", "kouenji-rokusuke",
                " [P2-typo -> kouenji-rokusuke]")
        db.execute("DELETE FROM characters WHERE char_id='kouejin'")
        stats["chars deleted (not-a-person)"] += 1
    db.execute("UPDATE aliases SET form_type='variant' WHERE char_id="
               "'kouenji-rokusuke' AND normalized='koejin'")
    ensure_alias(db, "kouenji-rokusuke", "Kouejin", "variant")
    stats["cnotes"] += cnote(db, "koejin", *CNOTES["koejin"])

    # ---- re-split recreations ----
    for cid, canonical, family, note in PEOPLE:
        ensure_person(db, cid, canonical, note, stats)
        ensure_alias(db, cid, family, "family")

    # ---- merges ----
    for src, dst, reason in MERGES:
        merge(db, src, dst, reason, stats)

    # ---- post-merge identity fixes ----
    if db.execute(
            "UPDATE aliases SET form_type='variant' WHERE char_id="
            "'yajima-mariko' AND normalized='yashima' "
            "AND form_type='family'").rowcount:
        stats["alias form fixed"] += 1
    n = db.execute(
        "UPDATE roster_candidates SET classification='character', "
        "char_id='yajima-mariko', reviewer_note=CASE WHEN "
        "instr(COALESCE(reviewer_note,''),'[P2-typo]')>0 THEN reviewer_note "
        "ELSE COALESCE(reviewer_note,'') || "
        "' [P2-typo] Y1V4 roster TL typo of Yajima' END "
        "WHERE normalized='yashima' AND "
        "(classification!='character' OR char_id!='yajima-mariko')").rowcount
    stats["yashima candidate forced"] += n
    if db.execute(
            "UPDATE aliases SET form_type='given' WHERE char_id='tsukishiro' "
            "AND normalized='tokinari' AND form_type='family'").rowcount:
        stats["alias form fixed"] += 1
    ensure_alias(db, "tsukishiro", "Tokinari Tsukishiro", "full")

    # ---- Himeno: rename + canonical upgrade ----
    himeno = db.execute(
        "SELECT 1 FROM characters WHERE char_id='himeno'").fetchone()
    if himeno and not db.execute(
            "SELECT 1 FROM characters WHERE char_id='himeno-yuki'").fetchone():
        rename_char(db, "himeno", "himeno-yuki")
        stats["chars renamed"] += 1
    elif himeno:
        merge(db, "himeno", "himeno-yuki",
              "both himeno and himeno-yuki existed — folded", stats)
    n = db.execute(
        "UPDATE characters SET canonical_name='Himeno Yuki', "
        "name_order='family-given', status='confirmed' "
        "WHERE char_id='himeno-yuki' AND (canonical_name!='Himeno Yuki' OR "
        "name_order!='family-given' OR status!='confirmed')").rowcount
    if n:
        stats["Himeno canonical upgraded"] += 1
    ensure_alias(db, "himeno-yuki", "Yuki", "given")
    if note_replace(db, "himeno-yuki", HIMENO_OLD, HIMENO_NEW):
        stats["note fixes"] += 1

    # ---- in-place note rewrites ----
    KIJIMA_OLD = "verify any student same-surname at P2"
    KIJIMA_NEW = ("P2 verified: all Kijima mentions are V0-only (Senator "
                  "Kijima-sensei, politician); no student same-surname in Y1+")
    if note_replace(db, "kijima", KIJIMA_OLD, KIJIMA_NEW):
        stats["note fixes"] += 1
    if note_replace(db, "onodera-kayano", "merged dup slug 'onodera' (P2)",
                    "P2 re-split: seed bare 'Onodera' (3-B) verified = Y1V8 "
                    "instructor, own char 'onodera'"):
        stats["note fixes"] += 1
    if note_replace(db, "ishikura-kayoko", "merged dup slug 'ishikura' (P2)",
                    "P2 re-split: seed bare 'Ishikura' (3-B) verified = "
                    "3rd-Yr Class B (Y1V8), own char 'ishikura'"):
        stats["note fixes"] += 1

    stats["notes added"] += ensure_note(
        db, "matsuo", "[P2-distinct]",
        "[P2-distinct] father/butler Matsuo (Y1V7; Y2V8 'Did Matsuo really "
        "commit suicide?') — DISTINCT from son Matsuo Eiichirou (Y2V3, "
        "Nanase's childhood friend), NO merge")
    stats["notes added"] += ensure_note(
        db, "matsuo-eiichirou", "[P2-distinct]",
        "[P2-distinct] Matsuo Eiichirou (Y2V3, expelled; suicide Feb 14; "
        "Y2V8 'his son, Eiichiro') — DISTINCT from father/butler Matsuo "
        "(Y1V7), NO merge")
    stats["notes added"] += ensure_note(
        db, "kiryuin-fuuka", "[P2-info]",
        "[P2-info] 3rd-year Class B in Y2 era (Y2V9.5; Fuuka SS Y2V4.5) — "
        "seed roster line is her Y1 2-B placement")
    for key, (tag, text) in sorted(CNOTES.items()):
        if key == "koejin":
            continue
        stats["cnotes"] += cnote(db, key, tag, text)

    # ---- alias policy ----
    marks = ",".join("?" for _ in AMBIG_GIVEN)
    n = db.execute(
        f"DELETE FROM aliases WHERE form_type='given' AND normalized IN "
        f"({marks})", AMBIG_GIVEN).rowcount
    stats["ambiguous given aliases removed"] += n
    n = db.execute(
        "DELETE FROM aliases WHERE char_id='kamogawa' AND normalized="
        "'toshizo' AND form_type='given'").rowcount
    stats["wrong-given aliases removed"] += n
    n = db.execute(
        "DELETE FROM aliases WHERE char_id='matsuo' AND normalized="
        "'eichiro' AND form_type='given'").rowcount
    stats["wrong-given aliases removed"] += n

    n = db.execute(
        "DELETE FROM aliases WHERE alias_id NOT IN "
        "(SELECT MIN(alias_id) FROM aliases GROUP BY char_id, "
        " normalized)").rowcount
    stats["alias dups removed"] += n

    # ---- tiers ----
    n = db.execute(
        "UPDATE characters SET tier=2, notes=COALESCE(notes,'') || "
        "' | [P2-tier2] mid (2): 1659 mentions, Class-D peer group' "
        "WHERE char_id='kouenji-rokusuke' AND tier IS NULL").rowcount
    stats["tier2 promoted"] += n
    band = db.execute(
        "SELECT c.char_id, COALESCE(MAX(r.total_count),0) FROM characters c "
        "LEFT JOIN roster_candidates r ON r.char_id=c.char_id "
        "WHERE c.tier IS NULL GROUP BY c.char_id").fetchall()
    for cid, cnt in band:
        tier = 3 if cnt >= 5 else 4
        n = db.execute(
            "UPDATE characters SET tier=?, notes=COALESCE(notes,'') || "
            "' | [P2-band]' WHERE char_id=? AND tier IS NULL",
            (tier, cid)).rowcount
        if n:
            stats[f"NULL band -> t{tier}"] += 1
    band10 = db.execute(
        "SELECT c.char_id FROM characters c "
        "LEFT JOIN roster_candidates r ON r.char_id=c.char_id "
        "WHERE c.tier=4 GROUP BY c.char_id "
        "HAVING COALESCE(MAX(r.total_count),0)>=10").fetchall()
    for (cid,) in band10:
        n = db.execute(
            "UPDATE characters SET tier=3, notes=COALESCE(notes,'') || "
            "' | [P2-band10]' WHERE char_id=? AND tier=4",
            (cid,)).rowcount
        if n:
            stats["tier4 >=10 -> t3"] += 1
    n = db.execute(
        "UPDATE characters SET tier=3, notes=COALESCE(notes,'') || "
        "' | [P2-force] tier 3 (Y1V8 presence)' WHERE char_id='ishikura' "
        "AND COALESCE(tier,-1)!=3").rowcount
    stats["force ishikura -> t3"] += n

    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) "
        "VALUES (?,?,?,?)",
        ("review_tier_p2", datetime.datetime.now().isoformat(
            timespec="seconds"), datetime.datetime.now().isoformat(
            timespec="seconds"),
         "P2 identity merges/re-splits/alias policy/tier bands"))
    db.commit()

    print("effects:")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    chars = db.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    tiers = dict(db.execute(
        "SELECT tier, COUNT(*) FROM characters GROUP BY tier").fetchall())
    dist = dict(db.execute(
        "SELECT classification, COUNT(*) FROM roster_candidates "
        "GROUP BY classification").fetchall())
    aliases = db.execute("SELECT COUNT(*) FROM aliases").fetchone()[0]
    unrev3 = db.execute(
        "SELECT COUNT(*) FROM roster_candidates "
        "WHERE classification='unreviewed' AND total_count>=3").fetchone()[0]
    orphan = db.execute(
        "SELECT COUNT(*) FROM roster_candidates c "
        "LEFT JOIN characters ch ON ch.char_id=c.char_id "
        "WHERE c.classification='character' AND ch.char_id IS NULL").fetchone()[0]
    shells = db.execute(
        "SELECT COUNT(*) FROM characters "
        "WHERE char_id LIKE 'provisional-%'").fetchone()[0]
    nulls = db.execute(
        "SELECT COUNT(*) FROM characters WHERE tier IS NULL").fetchone()[0]
    db.close()
    print(f"characters: {chars}  tiers: {tiers}  (null tier: {nulls})")
    print("candidates:", dist)
    print(f"aliases: {aliases}")
    print(f"unreviewed>=3: {unrev3}  orphan candidates: {orphan}  "
          f"shell chars: {shells}")
    ok = unrev3 == 0 and orphan == 0 and shells == 0 and nulls == 0
    print("GATES:", "OK" if ok else "FAIL")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

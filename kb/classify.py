#!/usr/bin/env python3
"""P1 classification: curated KNOWN table (raw forms -> identity, tier).

Keys are normalized at load time with roster_mine.normalize so they always match
roster_candidates. Wipes + rebuilds characters/aliases (derived tables) so re-runs
are clean; run import_seed.py after this.
"""
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_mine import normalize  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "cote_kb.db")

# RAW written form -> (canonical "Family Given", tier 1/2/3)
# Corrections verified against corpus 2026-10-16 (Ike Kanji via "Ike Kanji" x12,
# Hashimoto Masayoshi x28, Kitou Hayato x7, Shinohara Satsuki x9, Yukimura
# Teruhiko confirmed, Mii = Wang Mei-Yu stated in Y1V11, Keisei = Yukimura
# nickname stated in-corpus, Hiyori = Shiina (Y1V9 "Hiyori Shiina"), Nanase
# Tsubasa, Hasebe Haruka separate from Shinohara).
KNOWN_RAW = {
    # --- class D (Y1) core ---
    "Ayanokouji": ("Ayanokouji Kiyotaka", 1),
    "Kiyotaka": ("Ayanokouji Kiyotaka", 1),
    "Horikita": ("Horikita Suzune", 1),
    "Suzune": ("Horikita Suzune", 1),
    "Kushida": ("Kushida Kikyou", 1),
    "Kikyou": ("Kushida Kikyou", 1),
    "Sudou": ("Sudou Ken", 2),
    "Ike": ("Ike Kanji", 3),
    "Sakura": ("Sakura Airi", 2),
    "Airi": ("Sakura Airi", 2),
    "Hirata": ("Hirata Yousuke", 2),
    "Karuizawa": ("Karuizawa Kei", 1),
    "Kei": ("Karuizawa Kei", 1),
    "Shinohara": ("Shinohara Satsuki", 3),
    "Hasebe": ("Hasebe Haruka", 3),
    "Yukimura": ("Yukimura Teruhiko", 3),
    "Keisei": ("Yukimura Teruhiko", 3),  # nickname, stated in-corpus
    "Yamauchi": ("Yamauchi Haruki", 3),
    "Kinoshita": ("Kinoshita Minori", 3),
    "Kaneda": ("Kaneda Satoru", 3),
    "Hamaguchi": ("Hamaguchi Tetsuya", 3),
    "Shiraishi": ("Shiraishi Asuka", 3),  # given name confirmed Y3V1 OAA
    "Kitou": ("Kitou Hayato", 3),
    "Yamamura": ("Yamamura Miki", 3),
    "Miyake": ("Miyake Akito", 3),
    "Sotomura": ("Sotomura Hideo", 3),
    "Matsushita": ("Matsushita Chiaki", 3),
    "Satou": ("Satou Maya", 3),
    "Ishikura": ("Ishikura Kayoko", 3),
    "Maezono": ("Maezono", 3),
    "Wang": ("Wang Mei-Yu", 3),
    "Mii": ("Wang Mei-Yu", 3),  # stated in-corpus (Y1V11)
    "Inogashira": ("Inogashira Kokoro", 3),
    "Onodera": ("Onodera Kayano", 3),
    "Mori": ("Mori Nene", 3),
    # --- class A (Y1) ---
    "Sakayanagi": ("Sakayanagi Arisu", 1),
    "Arisu": ("Sakayanagi Arisu", 1),
    "Katsuragi": ("Katsuragi Kouhei", 2),
    "Kamuro": ("Kamuro Masumi", 3),
    "Hashimoto": ("Hashimoto Masayoshi", 2),
    # --- class B (Y1) ---
    "Ichinose": ("Ichinose Honami", 1),
    "Honami": ("Ichinose Honami", 1),
    "Kanzaki": ("Kanzaki Ryuuji", 3),
    "Shiranami": ("Shiranami Chihiro", 3),
    "Amikura": ("Amikura Mako", 3),
    "Kobashi": ("Kobashi Yume", 3),
    # --- class C (Y1) ---
    "Ryuuen": ("Ryuuen Kakeru", 1),
    "Kakeru": ("Ryuuen Kakeru", 1),
    "Ishizaki": ("Ishizaki Daichi", 2),
    "Albert": ("Albert", 3),
    "Ibuki": ("Ibuki Mio", 3),
    "Shiina": ("Shiina Hiyori", 2),
    "Hiyori": ("Shiina Hiyori", 2),
    "Komiya": ("Komiya Kyogo", 3),
    # --- staff / authority ---
    "Chabashira": ("Chabashira Sae", 2),
    "Hoshinomiya": ("Hoshinomiya Chie", 2),
    "Mashima": ("Mashima Tomonari", 2),
    "Sakagami": ("Sakagami", 2),  # -sensei; given name unverified
    "Naoe": ("Naoe", 3),
    "Manabu": ("Horikita Manabu", 2),
    "Nagumo": ("Nagumo Miyabi", 2),
    "Miyabi": ("Nagumo Miyabi", 2),  # dominant given-name usage; Kitou is Hayato
    # --- Y2 cast ---
    "Yagami": ("Yagami Takuya", 2),
    "Amasawa": ("Amasawa Ichika", 3),
    "Nanase": ("Nanase Tsubasa", 2),
    "Tsubasa": ("Nanase Tsubasa", 2),
    "Housen": ("Housen Kazuomi", 2),
    "Tsukishiro": ("Tsukishiro", 2),
    "Tsubaki": ("Tsubaki Sakurako", 2),
    "Utomiya": ("Utomiya Riku", 3),
    # --- family / outside ---
    "Atsuomi": ("Ayanokouji Atsuomi", 2),
}


def slug(canonical):
    return re.sub(r"[^a-z0-9]+", "-", canonical.lower()).strip("-")


# given names shared by multiple characters (seed cross-check) — never auto-alias
GIVEN_AMBIGUOUS = {"haruka", "satoru", "shigeru", "kyosuke", "hitomi"}


def form_type(raw, canonical):
    parts = canonical.split()
    if raw == canonical:
        return "full"
    if raw == parts[0]:
        return "family"
    if len(parts) > 1 and raw == parts[1]:
        return "given"
    return "variant"


def main():
    db = sqlite3.connect(DB)
    # derived tables: full rebuild on every run
    db.execute("DELETE FROM aliases")
    db.execute("DELETE FROM characters")

    matched = 0
    for raw, (canonical, tier) in KNOWN_RAW.items():
        key = normalize(raw)
        cid = slug(canonical)
        fam = canonical.split()[0]
        giv = canonical.split()[1] if len(canonical.split()) > 1 else ""
        db.execute(
            "INSERT OR IGNORE INTO characters "
            "(char_id, canonical_name, name_order, tier, status, notes) "
            "VALUES (?,?,?,?,?,?)",
            (cid, canonical, "family-given" if giv else "unknown",
             tier, "confirmed", "KNOWN curated"),
        )
        db.execute(
            "INSERT OR IGNORE INTO aliases "
            "(char_id, raw_form, normalized, form_type, is_noise) VALUES (?,?,?,?,0)",
            (cid, raw, key, form_type(raw, canonical)),
        )
        # also alias family+given splits of canonical (e.g. Kiyotaka, Suzune)
        for part, ptype in ((fam, "family"), (giv, "given")):
            if part and part != raw and normalize(part) not in GIVEN_AMBIGUOUS:
                db.execute(
                    "INSERT OR IGNORE INTO aliases "
                    "(char_id, raw_form, normalized, form_type, is_noise) "
                    "VALUES (?,?,?,?,0)",
                    (cid, part, normalize(part), ptype),
                )
        n = db.execute(
            "UPDATE roster_candidates SET classification='character', char_id=?, "
            "reviewer_note=? WHERE normalized=? AND classification='unreviewed'",
            (cid, f"KNOWN: {canonical}", key),
        ).rowcount
        matched += n

    # E1 auto: remaining honorific recipients -> provisional characters
    rows = db.execute(
        "SELECT normalized, raw_form, signals FROM roster_candidates "
        "WHERE classification='unreviewed'"
    ).fetchall()
    e1_auto = 0
    for norm, raw, sigs in rows:
        if "E1" in json.loads(sigs):
            cid = f"provisional-{norm}"
            db.execute(
                "INSERT OR IGNORE INTO characters "
                "(char_id, canonical_name, name_order, tier, status, notes) "
                "VALUES (?,?,?,?,?,?)",
                (cid, raw.split("/")[0], "unknown", 4, "provisional",
                 "E1 honorific recipient"),
            )
            db.execute(
                "INSERT OR IGNORE INTO aliases "
                "(char_id, raw_form, normalized, form_type, is_noise) VALUES (?,?,?,?,0)",
                (cid, raw.split("/")[0], norm, "honorific"),
            )
            db.execute(
                "UPDATE roster_candidates SET classification='character', char_id=?, "
                "reviewer_note='E1 auto (honorific recipient)' "
                "WHERE normalized=? AND classification='unreviewed'",
                (cid, norm),
            )
            e1_auto += 1

    db.commit()
    unrev = db.execute(
        "SELECT COUNT(*) FROM roster_candidates WHERE classification='unreviewed'"
    ).fetchone()[0]
    nchars = db.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    db.close()
    print(f"KNOWN matched: {matched}/{len(KNOWN_RAW)}  E1 auto: {e1_auto}")
    print(f"characters: {nchars}  candidates unreviewed: {unrev}")


if __name__ == "__main__":
    main()

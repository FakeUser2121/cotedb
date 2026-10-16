#!/usr/bin/env python3
"""P1 review pass 1: decisions for the 100+ and 10-99 mention bands (2026-10-16).

Run AFTER: roster_mine.py -> classify.py -> import_seed.py.
Idempotent (INSERT OR IGNORE + UPDATE). Categories:
  - new characters created here (surname/given evidence in-corpus)
  - nickname/MTL/given-name aliases onto existing characters
  - noise (English words, TL watermarks, exam/meta language)
  - unknown with reviewer note (ambiguous, kept visible for straggler pass)
  - location note (P8 scope: kyoto, pallet)
"""
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_mine import normalize  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "cote_kb.db")


def slug(canonical):
    return re.sub(r"[^a-z0-9]+", "-", canonical.lower()).strip("-")


# --- new characters: raw key -> (canonical, tier, status, placement-note) ---
NEW_CHARS = {
    "kamogawa": ("Kamogawa", 3, "provisional",
                 "y0; father Senator Kamogawa Toshizou (Naoe ally); given name unknown"),
    "mika": ("Mika", 4, "provisional",
             "y0 White Room / restaurant scenes; given name unknown"),
    "tabuchi": ("Tabuchi", 4, "provisional",
                "y0 White Room researcher (DNA report); given name unknown"),
    "shiro": ("Shiro", 4, "provisional",
              "y0 White Room randori opponent; given name unknown"),
    "fuji": ("Fuji", 4, "provisional",
             "y0 youth group with Ryuuji and Nogi; given name unknown"),
    "mikitani": ("Mikitani", 3, "provisional",
                 "Y2V4, class 3B as written; speaks with Kiriyama"),
    "kikuchi": ("Kikuchi", 3, "provisional",
                "1-D Y1; exam scoring context (Y1V1); given name unknown"),
    "kosei": ("Sanada Kousei", 3, "confirmed",
              "Y2 class A representative (vanguard, Y2V12 sheet); OAA Academic A"),
    "ikkei": ("Shimazaki Ikkei", 4, "confirmed",
              "Y1V11 Event Selection (Class A team)"),
    "toyohashi": ("Toyohashi Goro", 4, "confirmed",
                  "Y2V11 first-year Class A list"),
    "nazuna": ("Asahina Nazuna", 3, "confirmed",
               "Y1: second-year Class A, Nagumo ally (Y1V8)"),
}

# --- aliases: raw key -> (canonical target, form_type, note) ---
ALIASES = {
    # nicknames
    "miyacchi": ("Miyake Akito", "variant", "nickname (E6)"),
    "miyachi": ("Miyake Akito", "variant", "nickname (E6)"),
    "yukimu": ("Yukimura Teruhiko", "variant", "nickname (E6)"),
    "kiyopon": ("Ayanokouji Kiyotaka", "variant", "nickname (E6)"),
    "princess": ("Sakayanagi Arisu", "variant",
                 "nickname used by Hashimoto/Kamuro (Y2V1/Y2V6, verified)"),
    "yoshi": ("Yoshida Kenta", "variant",
              "nickname used by Nishikawa (Y3V1 p148, verified)"),
    # MTL variants
    "sakayagani": ("Sakayanagi Arisu", "variant", "MTL spelling variant"),
    "sakayangi": ("Sakayanagi Arisu", "variant", "MTL spelling variant"),
    # given-name forms (identity verified via full-name hits in corpus)
    "masayoshi": ("Hashimoto Masayoshi", "given", "given name"),
    "miki": ("Yamamura Miki", "given", "given name (list contexts)"),
    "takuya": ("Yagami Takuya", "given", "given name"),
    "mio": ("Ibuki Mio", "given", "given name"),
    "mei": ("Wang Mei-Yu", "given", "given-name form of Mei-Yu"),
    "satsuki": ("Shinohara Satsuki", "given", "given name"),
    "sakurako": ("Tsubaki Sakurako", "given", "given name"),
    "teruhiko": ("Yukimura Teruhiko", "given", "given name"),
    "daichi": ("Ishizaki Daichi", "given", "given name"),
    "asuka": ("Shiraishi Asuka", "given", "given name (Y3 OAA + scenes)"),
    "kayano": ("Onodera Kayano", "given", "given name (rumor list Y1V9)"),
    "chiaki": ("Matsushita Chiaki", "given", "given name"),
    "naoki": ("Shimizu Naoki", "given", "given name (Y1V4 group lists)"),
    "hideo": ("Sotomura Hideo", "given", "given name"),
    "tetsuya": ("Hamaguchi Tetsuya", "given", "given name"),
    "kosei": ("Sanada Kousei", "given", "given name (Y2V9.5/Y2V12)"),
    "ikkei": ("Shimazaki Ikkei", "given", "given name (Y1V11 list)"),
    "toyohashi": ("Toyohashi Goro", "family", "surname"),
    "nazuna": ("Asahina Nazuna", "given", "given name"),
}

# --- canonical upgrades (legacy slug chars; primary fix lives in classify.py) ---
UPGRADE = {
    "shiraishi": "Shiraishi Asuka",  # legacy char_id 'shiraishi' only
}

# --- noise: raw key -> note ---
NOISE = {
    # TL / meta
    "translated": "TL credit line", "royal": "TL group (RoyalMTLs)",
    "rhymar": "TL watermark (Rhymar)", "editor": "TL credits",
    "profreader": "TL credits", "senior": "TL credits", "author": "book meta",
    "postscript": "book meta", "afterword": "book meta", "credits": "book meta",
    "newsletter": "book meta", "zeroboks": "TL site ad", "seas": "publisher ad",
    "syougo": "author Kinugasa", "shogo": "author Kinugasa",
    "syogo": "author Kinugasa", "classrom": "series title",
    "character": "TOC", "gallery": "TOC", "title": "TOC", "contents": "TOC",
    "soliloquy": "chapter-title word", "monologue": "chapter-title word",
    "intro": "section header", "epilogue": "section header",
    "confusion": "chapter title (Y3V1)", "confirmation": "chapter title (Y3V1)",
    "beginning": "chapter title", "curtain": "chapter title",
    "everyday": "chapter title", "enemies": "chapter title",
    "allies": "chapter title", "ahead": "chapter title", "war": "chapter title",
    "middle": "chapter title", "scenes": "section header", "true": "chapter title",
    "first": "chapter-title word", "double": "chapter title (dooble separate)",
    "doble": "chapter title (Double Question)", "mock": "SS title word",
    "date": "chapter/SS title word", "remaining": "chapter title (Y2V9.5)",
    "development": "chapter/meta word", "perspective": "chapter title (Y3V1)",
    "commencement": "chapter title (Y3V1)", "defeat": "chapter title (Y1V8)",
    "premonition_defeat_part": "",
    # English common words / pronouns / exam+system language
    "she": "English", "he": "English", "an": "English", "to": "English",
    "is": "English", "are": "English", "was": "English", "my": "English",
    "we": "English", "me": "English", "her": "English", "they": "English",
    "did": "English", "not": "English", "had": "English", "now": "English",
    "one": "English", "part": "English", "life": "English", "like": "English",
    "having": "English", "seeing": "English", "seing": "English",
    "watching": "English", "considering": "English", "apparently": "English",
    "following": "English", "hearing": "English", "unlike": "English",
    "off": "English", "half": "English", "place": "English", "people": "English",
    "man": "English/sentence artifact (Hirata Man)", "god": "English",
    "love": "English", "happy": "English", "light": "English", "free": "English",
    "fre": "English", "basic": "English", "total": "English",
    "academic": "eval-sheet word", "physical": "eval-sheet word",
    "social": "eval-sheet word", "contribution": "eval-sheet word",
    "overall": "eval-sheet word", "adaptability": "eval-sheet word",
    "acting": "title word (acting president)", "council": "student council word",
    "secretary": "title word (Tachibana)", "vice": "title word",
    "professor": "title word", "mister": "title word", "senator": "title word (Kamogawa father)",
    "minister": "title word", "prime": "title word", "company": "title word",
    "parliament": "political word (y0)", "peace": "y0 party (P8/politics)",
    "citizen": "y0 party (Citizens' Party)",
    "festival": "event word", "sports": "event word", "christmas": "event word",
    "eve": "event word", "karaoke": "event word", "vacation": "event word",
    "celebration": "event word", "party": "event word",
    "task": "exam word", "tasks": "exam word", "exam_word": "",
    "unanimos": "exam word (Unanimous Voting)", "vote": "exam word",
    "poll": "exam word (Class Poll)", "consent": "exam word",
    "protection": "exam word (Protection Points)", "protected": "exam word",
    "project": "exam/system word", "delta": "exam plan (Operation Delta)",
    "rabbit": "exam group label (Y1V4)", "outcome": "exam word",
    "otcome": "exam word", "bonuses": "exam word", "arrival": "exam word",
    "movement": "exam word", "task_s": "",
    "intervention": "exam rules word", "commander": "exam role",
    "participants": "exam rules word", "nomines": "exam word (Nominees)",
    "members": "exam word", "representative": "exam word (Y2V12)",
    "guard": "exam role (Y2V12)", "rope": "exam event", "race": "exam event",
    "battle": "exam event", "battles": "exam event (Y3V1)", "flags": "exam event",
    "flash": "exam event (Flash Mental Arithmetic)", "arithmetic": "exam event",
    "literature": "exam event", "modern": "exam event", "mental": "exam event",
    "required": "exam rules word", "rules": "exam rules word",
    "alert": "watch system word", "warning": "watch system word",
    "emergency": "watch system word", "table": "watch system word",
    "tables": "watch system word", "start": "exam word", "trial": "exam card",
    "ride": "exam card (Free Ride)", "guard_": "",
    "shuffle": "exam name (Paper Shuffle)", "selection": "exam name",
    "training": "exam name (Mixed Training Camp)", "mixed": "exam name",
    "camp": "exam word", "difficulty": "exam word", "overview": "exam word",
    "eve_": "", "basic_": "",
    "defensive": "exam word (Y2V10)", "success": "exam word",
    "successfully": "exam word", "adventures": "",
    "uninhabited": "exam name (Uninhabited Island)", "island_word": "",
    "guidance": "", "advancement": "",
    "dragon": "pop-culture (Dragon Ball)", "joker": "card game",
    "maid": "card game (Old Maid)", "icarus": "myth reference (Wings of Icarus)",
    "musashi": "historical reference (y0)", "beta": "y0 curriculum word",
    "metropolitan": "school name word", "internet": "English",
    "anime": "pop culture", "gourmet": "exam word (Y2V10)",
    "gormet": "exam word (Y2V10)", "food": "exam word",
    "subculture": "exam word", "cultural": "festival word",
    "guidebok": "SS section (Guidebook)", "development_": "",
    "notes": "book meta", "reader": "TL credits (Japanese Reader)",
    "slayer": "Shiraishi Asuka nickname context (Hundred-Man Slayer)",
    "born": "author bio", "guards": "author bio (Guards of Daybreak)",
    "daybreak": "author bio", "reminiscence": "author bio",
    "bird": "English/unknown non-name", "nurturing": "school name word",
    "advanced": "school name word", "elite": "series title",
    "act": "English", "total_": "",
    "resorce": "y0 doc word (Human Resource Development Plan)",
    "fod": "exam word (Gourmet Food)",
    "stabbing": "",
    "group": "exam word (group assignment)",
    "senpaaii": "honorific token (Senpai/Sensei) — not a name",
    "period": "chapter title / English",
    "paper": "exam name word (Paper Shuffle)",
    "onloker": "chapter title (An Onlooker's Perspective)",
    "awaits": "chapter title (Epilogue: What Awaits Ahead)",
    "valentine": "event word (Valentine's)",
    "human": "chapter/y0 doc word",
    "end": "chapter title (The End of Everyday Life)",
    "operation": "exam plan word (Operation ...)",
    "girl": "chapter title word / English",
    "change": "exam result word / English",
    "rewards": "exam word",
    "airport": "school trip schedule word",
    "event": "exam name word (Event Selection)",
    "petty": "knife type word (Y2V1) — English",
    "trip": "school trip word",
    "discussion": "exam word (Y2V12 Discussion)",
    "shizuku": "external celebrity (gravure idol, Y1V2)",
    "idiot": "group nickname word (Idiot Trio)", "trio": "group nickname word",
    "princess_": "",
    "current": "English", "student": "English", "value": "English",
    "to_": "",
}

# --- unknown (kept visible, straggler pass) : key -> note ---
UNKNOWN = {
    "ryuji": "ambiguous given: Kanzaki Ryuuji (1-B) OR y0 boy (Ryuuji/Fuji/Nogi group)",
    "koji": "given of Machida Kouji (Y1V4 list); uniqueness unverified",
    "shinobu": "given of Fukuyama Shinobu (Y1V11 list); uniqueness unverified",
    "so": "given of Shibata Sou (Y1V5 MVP); sentence-initial 'So' risk — not aliased",
}

# --- P8 location placeholders: key -> note ---
LOCATION = {
    "kyoto": "trip destination option (Y2V5) — P8 scope",
    "pallet": "café at school grounds (Y1V5+) — P8 scope",
}


def ensure_char(db, cid, canonical, tier, status, notes):
    db.execute(
        "INSERT OR IGNORE INTO characters "
        "(char_id, canonical_name, name_order, tier, status, notes) VALUES (?,?,?,?,?,?)",
        (cid, canonical, "family-given" if len(canonical.split()) > 1 else "unknown",
         tier, status, notes),
    )


def add_alias(db, cid, raw, ftype, note=""):
    key = normalize(raw)
    db.execute(
        "INSERT OR IGNORE INTO aliases "
        "(char_id, raw_form, normalized, form_type, is_noise) VALUES (?,?,?,?,0)",
        (cid, raw, key, ftype),
    )
    return key


def claim(db, key, cid, note):
    db.execute(
        "UPDATE roster_candidates SET classification='character', char_id=?, "
        "reviewer_note=? WHERE normalized=? AND "
        "(classification='unreviewed' OR char_id LIKE 'provisional-%')",
        (cid, note, key),
    )


def main():
    db = sqlite3.connect(DB)

    # 1. canonical upgrades
    for old, newname in UPGRADE.items():
        db.execute("UPDATE characters SET canonical_name=?, notes=? "
                   "WHERE char_id=?", (newname, "given name added: " + newname,
                                      slug(old)))

    # 2. new characters (+ alias their family/given parts, claim candidates)
    for key, (canonical, tier, status, note) in NEW_CHARS.items():
        cid = slug(canonical)
        ensure_char(db, cid, canonical, tier, status, note)
        parts = canonical.split()
        add_alias(db, cid, parts[0], "family")
        if len(parts) > 1:
            add_alias(db, cid, parts[1], "given")
        fam_key = normalize(parts[0])
        if key != fam_key:
            add_alias(db, cid, key, "variant")
        claim(db, key, cid, f"P1 pass1: {note}")
        if key != fam_key:
            claim(db, fam_key, cid, f"P1 pass1: surname of {canonical}")

    # 3. aliases onto existing chars
    for key, (canonical, ftype, note) in ALIASES.items():
        cid = slug(canonical)
        row = db.execute("SELECT 1 FROM characters WHERE char_id=?", (cid,)).fetchone()
        if not row:
            print(f"WARN: alias target missing for {key} -> {cid}")
            continue
        add_alias(db, cid, key, ftype)
        claim(db, key, cid, f"P1 pass1 alias: {note}")

    # 4. noise
    for key, note in NOISE.items():
        if not note:
            continue
        k = normalize(key)
        db.execute(
            "UPDATE roster_candidates SET classification='noise', "
            "reviewer_note=? WHERE normalized=? AND classification='unreviewed'",
            (f"P1 pass1 noise: {note}", k),
        )

    # 5. unknowns
    for key, note in UNKNOWN.items():
        db.execute(
            "UPDATE roster_candidates SET classification='unknown', "
            "reviewer_note=? WHERE normalized=? AND classification='unreviewed'",
            (f"P1 pass1: {note}", key),
        )

    # 6. locations
    for key, note in LOCATION.items():
        db.execute(
            "UPDATE roster_candidates SET classification='unknown', "
            "reviewer_note=? WHERE normalized=? AND classification='unreviewed'",
            (f"P1 pass1 location: {note}", key),
        )

    db.commit()
    stats = db.execute(
        "SELECT classification, COUNT(*) FROM roster_candidates "
        "GROUP BY classification ORDER BY 2 DESC").fetchall()
    chars = db.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    db.close()
    print("candidates:", dict(stats))
    print("characters:", chars)


if __name__ == "__main__":
    main()

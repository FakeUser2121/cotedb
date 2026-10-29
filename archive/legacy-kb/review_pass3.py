#!/usr/bin/env python3
"""P1 review pass 3: batch full-name pair scan for the 1-2 band (precision gate).

Scans every page with the corpus E3 pattern (adjacent capitalized name-like
pair, read as Family Given; SPECIAL_SWAP corrects known TL reversals).

Per pair:
- skip stop/noise tokens, noise rows, TL-reversals (family slot already a
  given alias), keys colliding
- VARIANT_PAIRS (TL manglings) -> alias onto the real char, no new char
- family already a real character -> claim exclusive givens onto it
- case A (new char) requires ALL of:
    * family row exists with total_count >= 2
    * family NOT in en_US dictionary (unless hand-verified ALLOW list)
    * given NOT in en_US dictionary
    * family pairs with exactly one given in the whole scan
  (calibrated on a hand-labeled sample of 159: keeps 9/9 real names —
   allowlisted 'jute' — and rejects the verb-phrase/English false pairs)

Idempotent; run after pass2. hunspell en_US.dic/aff is bootstrapped from the
GNOME flatpak runtime into /tmp/opencode/hdict (no pip, no system writes).
"""
import glob
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_mine import (  # noqa: E402
    E3_RE, fold, is_noise_token, iter_pages, normalize,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "cote_kb.db")

HDICT = "/tmp/opencode/hdict"

# normalized-pair -> (family_raw, given_raw) when corpus writes Given Family
SPECIAL_SWAP = {
    ("ikuko", "yamanaka"): ("Yamanaka", "Ikuko"),
}

# normalized-pair -> real canonical (TL manglings; no new char)
VARIANT_PAIRS = {
    ("horokita", "manabu"): "Horikita Manabu",
    ("rotsukaku", "momoe"): "Rokkaku Momoe",
    ("fujirika", "morofuji"): "Morofuji Rika",
}

# hand-verified surnames that happen to be dictionary words
ALLOW_FAMILIES = {"jute"}

# ---- unreviewed-key english sweep (count<=3 -> noise) ----
SWEEP_MAX_COUNT = 3

# ---- E1 shell triage (context-verified against corpus 2026-10-16) ----
# descriptor / gloss / real-world junk shells -> key becomes noise
SHELL_NOISE_KEYS = {
    "boy", "busty", "delinquent", "eyes", "glasses", "hair",   # descriptors
    "sazae",      # 'Sazae-san' TV show mention
    "oji", "ojo",  # honorific-gloss afterword (Y2V9.5)
    "kinugasa",   # real-world author Kinugasa Shougo (v0 intro)
    "kami",       # 'Kami-sama' deity gloss
    "mine",       # first-person possessive "Mine's a mess" (Y1V1) — not a name
}

# shell key -> existing real char (TL misspellings of known characters)
SHELL_VARIANT = {
    "ayaayanokoji": "ayanokouji-kiyotaka",
    "ayakoji": "ayanokouji-kiyotaka",
    "ayankoji": "ayanokouji-kiyotaka",
    "ayanokoij": "ayanokouji-kiyotaka",
    "chabasira": "chabashira-sae",
    "chabishira": "chabashira-sae",
    "chibashira": "chabashira-sae",
    "chiyabashira": "chabashira-sae",
    "koejin": "kouenji-rokusuke",   # 'Kouejin-kun' Y1V1 pool race = Kouenji
    "sayakanagi": "sakayanagi-arisu",
    "matushita": "matsushita-chiaki",
    "hoshonimya": "hoshinomiya-chie",
    "wan": "wang-mei-yu",       # 'Wan Mei-Yui' TL form of Wang Mei-Yu
}

# family+given shells of the SAME person -> merge into one real char
SHELL_PAIRS = [
    ("Morishita Ai", ["morishita", "ai"]),
    ("Ichino Yuyu", ["ichino", "yuyu"]),
    ("Tomose Shunsaku", ["tomose", "shunsaku", "tomoseshunsaku"]),
]

# family-only shells -> promote to real background chars (context verified)
SHELL_PROMOTE = {
    "Aga": (["aga"], "", "Class A; student-council context (Y2V9)"),
    "Akiyama": (["akiyama"], "", "gym staff member (Y2V10/10.25)"),
    "Anazai": (["anazai"], "", "Class D student (Y2V9)"),
    "Asagaya Mai": (["asagaya"], "Mai", "Y2V12 evaluation list"),
    "Asama": (["asama"], "", "y0 adult, Asama-sensei (Naoe's colleague)"),
    "Chiba": (["chiba"], "", "Class D context (Y2V12)"),
    "Enoshima Midoriko": (["enoshima"], "Midoriko", "3-B student (Y2V10)"),
    "Etou": (["eto"], "", "1st-Yr Class D (Y1V4.5)"),
    "Gouda": (["goda"], "", "2nd-Yr group leader (Y2V8)"),
    "Hatsukawa Maho": (["hatsukawa"], "Maho",
                       "Y2V11 Class D roster: Hatsukawa Maho; Y2V12 mentions"),
    "Hatsutori": (["hatsutori"], "", "class-rep exam executive (Y2V12)"),
    "Higashiyama": (["higashiyama"], "", "PE instructor / sensei (Y1V2)"),
    "Himeno Yuki": (["himeno"], "Yuki",
                    "2nd-Yr Class B / Ichinose class: full name 'Himeno Yuki' "
                    "(Y2V4.5 OAA 'Second-Year Class B Himeno Yuki'; Y2V6 "
                    "'Himeno-san from Ichinose-san's class'; Y3V1 "
                    "'Himeno Yuki — 69 pts' vs Sudou). Y2V12 first-"
                    "discussion roster header '2nd Year Class D' over her "
                    "name is swapped — same block files undisputed 2-D "
                    "Sudou/Miyake/Matsushita/Onodera/Nishimura/Ichihashi "
                    "under 'Class B' — P2"),
    "Iizuka": (["izuka"], "", "Ichinose classmate (Y3V1)"),
    "Iki": (["iki"], "", "3rd-Yr Class D, OAA (Y2V11)"),
    "Isomaru": (["isomaru"], "", "y0 faction leader, Isomaru-sensei"),
    "Katagiri": (["katagiri"], "", "Y2 Class C student; NOT credits-name "
                                   "Katagiri Yuuichi (distinct)"),
    "Kibayashi": (["kibayashi"], "", "1-B student (Y2V4.5)"),
    "Kijima": (["kijima"], "", "y0 Senator Kijima; verify any student "
                               "same-surname at P2"),
    "Kimura": (["kimura"], "", "Keyaki Mall clerk / staff (Y1V7.5)"),
    "Kisarazu": (["kisarazu"], "", "y0 student, 3 years Senpai to narrator"),
    "Kishi": (["kishi"], "", "senpai rumor-spreader context (Y2V7)"),
    "Kurachi": (["kurachi"], "", "1st-Yr Class C (Y2V4.5)"),
    "Minamikawa": (["minamikawa"], "", "3-C group leader (Y2V11)"),
    "Mochizuki": (["mochizuki"], "", "1-B student (Y2V4.5)"),
    "Morimiya": (["morimiya"], "", "Class A student (Y1V4)"),
    "Niiura": (["niura"], "", "student list context (Y2V12)"),
    "Ninomiya Kuranosuke": (["kuranosuke"], "",
                            "3rd-Yr Class C (Y1V8); surname shared with "
                            "Ninomiya Yui (1-B) — family key NOT claimed"),
    "Nogi": (["nogi"], "", "y0, Nogi Pharmaceuticals family"),
    "Okabe Fuyu": (["okabe"], "Fuyu", "Y2V12 evaluation list"),
    "Sasaki": (["sasaki"], "", "3-A teacher (Y2V4); NOT Sasaki Kojirō "
                               "(outside-world mention)"),
    "Sonezaki": (["sonezaki"], "", "y0 spoken name"),
    "Souya": (["soya"], "", "y0 lab-coat staff"),
    "Takanashi Kō": (["takanashi"], None,
                     "Y2V12 evaluation list; given key 'ko' shared — "
                     "left unknown at P2"),
    "Takato": (["takato", "takoto"], "", "student (TL macron variants)"),
    "Tanaka": (["tanaka"], "", "senpai group context (Y2V11)"),
    "Tatebayashi": (["tatebayashi"], "", "group leader, senpai (Y2V11)"),
    "Tatara": (["tatara"], "", "3rd-Yr student (Y2V4.5)"),
    "Ukon": (["ukon"], "", "fortune-teller staff, Ukon-sensei (Y1V4.5)"),
    "Yamaga": (["yamaga"], "", "guest-room classmate context (Y2V4.5)"),
    "Yamawaki": (["yamawaki"], "", "Class C student (Y1V1)"),
    "Yuki": (["yuki"], "", "y0 girl student (narrator's seatmate)"),
}


def ensure_dict():
    os.makedirs(HDICT, exist_ok=True)
    dic = os.path.join(HDICT, "en_US.dic")
    if os.path.exists(dic):
        return
    hits = glob.glob(
        "/home/user3/.local/share/flatpak/runtime/**/hunspell/en_US.dic",
        recursive=True)
    if not hits:
        raise SystemExit("hunspell en_US dictionary not found in flatpak runtime")
    shutil.copy(hits[0], dic)
    shutil.copy(hits[0][:-4] + ".aff", os.path.join(HDICT, "en_US.aff"))


def english_words(words):
    """Return the subset of `words` accepted by en_US hunspell."""
    if not words:
        return set()
    ensure_dict()
    p = subprocess.run(
        ["hunspell", "-d", "en_US", "-l"],
        input="\n".join(sorted(words)),
        capture_output=True, text=True, cwd=HDICT)
    if p.returncode not in (0, 1) or p.stderr.strip():
        print(f"WARN hunspell failed: {p.stderr[:200]}")
        return set()
    misspelled = set(p.stdout.split())
    return {w for w in words if w not in misspelled}


def canon_piece(tok):
    s = fold(tok)
    s = re.sub(r"['’]s$", "", s)
    s = re.sub(r"-(san|kun|chan|sama|sensei|dono|don|nee|nii)$", "", s,
               flags=re.I)
    return s


def slug(canonical):
    s = canonical.lower()
    for a, b in (("ā", "a"), ("ē", "e"), ("ī", "i"), ("ō", "o"), ("ū", "u")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def add_alias(db, cid, raw, ftype):
    key = normalize(raw)
    if db.execute("SELECT 1 FROM aliases WHERE char_id=? AND normalized=?",
                  (cid, key)).fetchone():
        return
    db.execute(
        "INSERT INTO aliases (char_id, raw_form, normalized, form_type, is_noise) "
        "VALUES (?,?,?,?,0)", (cid, raw, key, ftype))


def claim(db, raw, cid, note, include_unknown=False):
    key = normalize(raw)
    filt = "classification='unreviewed'"
    if include_unknown:
        filt = ("(classification='unreviewed' OR classification='unknown' "
                " OR char_id LIKE 'provisional-%')")
    return db.execute(
        "UPDATE roster_candidates SET classification='character', char_id=?, "
        "reviewer_note=? WHERE normalized=? AND " + filt,
        (cid, note, key)).rowcount


def repoint(db, src_cid, dst_cid, note):
    n = db.execute(
        "UPDATE roster_candidates SET char_id=?, "
        "reviewer_note=COALESCE(reviewer_note,'') || ? WHERE char_id=?",
        (dst_cid, note, src_cid)).rowcount
    db.execute("UPDATE aliases SET char_id=? WHERE char_id=?", (dst_cid, src_cid))
    db.execute("UPDATE quotes SET char_id=? WHERE char_id=?", (dst_cid, src_cid))
    return n


def ensure_char(db, canonical, notes, created, stats):
    cid = slug(canonical)
    if not db.execute("SELECT 1 FROM characters WHERE char_id=?",
                      (cid,)).fetchone():
        name_order = "family-given" if len(canonical.split()) >= 2 else "single"
        db.execute(
            "INSERT INTO characters "
            "(char_id, canonical_name, name_order, tier, status, notes) "
            "VALUES (?,?,?,?,?,?)",
            (cid, canonical, name_order, 4, "confirmed", notes))
        created.append(canonical)
        stats["chars created"] += 1
    return cid


def resolve_shells(db, stats, created):
    for key in sorted(SHELL_NOISE_KEYS):
        sh = f"provisional-{key}"
        n = db.execute(
            "UPDATE roster_candidates SET classification='noise', char_id=NULL, "
            "reviewer_note='P1 pass3: junk/descriptor shell -> noise' "
            "WHERE char_id=? AND classification='character'", (sh,)).rowcount
        if n:
            stats["shell junk -> noise"] += 1
        db.execute("DELETE FROM aliases WHERE char_id=?", (sh,))
        exists = db.execute("SELECT 1 FROM characters WHERE char_id=?",
                            (sh,)).fetchone()
        nrefs = db.execute("SELECT COUNT(*) FROM roster_candidates "
                           "WHERE char_id=?", (sh,)).fetchone()[0]
        if exists and nrefs == 0:
            db.execute("DELETE FROM characters WHERE char_id=?", (sh,))
            stats["junk shells deleted"] += 1
    for canonical, keys in SHELL_PAIRS:
        cid = ensure_char(db, canonical,
                          f"P1 shell merge: keys {', '.join(keys)} "
                          f"(family+given shells of one person)",
                          created, stats)
        moved = False
        for k in keys:
            if repoint(db, f"provisional-{k}", cid, " [shell->real]"):
                moved = True
        if moved:
            stats["shell pairs merged"] += 1
    for key, tcid in sorted(SHELL_VARIANT.items()):
        n = db.execute("SELECT 1 FROM characters WHERE char_id=?",
                       (tcid,)).fetchone()
        if not n:
            stats["WARN shell-variant target missing"] += 1
            continue
        if repoint(db, f"provisional-{key}", tcid, " [shell variant]"):
            stats["shell variants redirected"] += 1
    for canonical, (keys, given, note) in sorted(SHELL_PROMOTE.items()):
        cid = ensure_char(db, canonical, f"P1 shell promotion: {note}",
                          created, stats)
        moved = False
        for k in keys:
            if repoint(db, f"provisional-{k}", cid, " [shell->real]"):
                moved = True
        if given:
            add_alias(db, cid, given, "given")
        if moved:
            stats["shells promoted"] += 1


def main():
    raw_pairs = defaultdict(lambda: {"n": 0, "first": None})
    for vol_id, _stem, page, _pstart, text in iter_pages():
        for m in E3_RE.finditer(text):
            a, b = m.group(1), m.group(2)
            if is_noise_token(a) or is_noise_token(b):
                continue
            k = (fold(a), fold(b))
            p = raw_pairs[k]
            p["n"] += 1
            if p["first"] is None:
                p["first"] = (vol_id, page)

    # apply TL-reversal swaps -> processing list
    proc = []
    for (a, b), info in raw_pairs.items():
        kf, kg = normalize(a), normalize(b)
        if (kf, kg) in SPECIAL_SWAP:
            fa, ga = SPECIAL_SWAP[(kf, kg)]
        else:
            fa, ga = canon_piece(a), canon_piece(b)
            kf, kg = normalize(fa), normalize(ga)
        if kf == kg:
            continue
        proc.append((fa, ga, kf, kg, info))

    fam2givs = defaultdict(set)
    giv2fams = defaultdict(set)
    for _fa, _ga, kf, kg, _info in proc:
        fam2givs[kf].add(kg)
        giv2fams[kg].add(kf)

    eng = english_words({w for f, g, _, _, _ in proc
                         for w in (f.lower(), g.lower())})

    db = sqlite3.connect(DB)
    stats = defaultdict(int)
    created = []

    # honorific/title/typo keys are never characters (and would poison
    # case-B given-claims, e.g. pair (Yomawari, Sensei))
    TITLE_NOISE = {
        "sensei": "title/word used as address ('Sensei'), never a name",
        "thre": "TL text artifact: 'Three-' vowel-collapsed key (y1v5)",
        "thirten": "TL typo key: 'Thirteen' vowel-collapsed (y1v5)",
        "agatha": "outside-world author mention (Agatha Christie, y1v6)",
    }
    for key, note in sorted(TITLE_NOISE.items()):
        n = db.execute(
            "UPDATE roster_candidates SET classification='noise', reviewer_note=? "
            "WHERE normalized=? AND classification IN ('unreviewed','character')",
            (f"P1 pass3 title-noise: {note}", key)).rowcount
        if n:
            stats["titles -> noise"] += n

    # english noise sweep over open low-count keys (before pair gates);
    # SWEEP_EXCLUDE: hand-verified real surnames that hunspell also accepts
    SWEEP_EXCLUDE = {"jute"}
    sweep_rows = {r[0] for r in db.execute(
        "SELECT normalized FROM roster_candidates "
        "WHERE classification='unreviewed' AND total_count<=?",
        (SWEEP_MAX_COUNT,))} - SWEEP_EXCLUDE
    swept = sorted(english_words(sweep_rows))
    for k in swept:
        db.execute(
            "UPDATE roster_candidates SET classification='noise', reviewer_note=? "
            "WHERE normalized=? AND classification='unreviewed'",
            (f"P1 pass3 dict-sweep: english word (count<={SWEEP_MAX_COUNT})", k))
    stats["dict-sweep -> noise"] = len(swept)
    if swept:
        print(f"dict-sweep: {len(swept)} english keys -> noise "
              f"(e.g. {', '.join(swept[:12])} ...)")

    # triage E1 shells FIRST so pair-scan case-A/B sees real chars and
    # noise families (single-pass complete; a second run must be a no-op)
    resolve_shells(db, stats, created)

    for fa, ga, kf, kg, info in sorted(proc, key=lambda x: -x[4]["n"]):
        fam_row = db.execute(
            "SELECT classification, char_id, total_count "
            "FROM roster_candidates WHERE normalized=?",
            (kf,)).fetchone()
        giv_row = db.execute(
            "SELECT classification, char_id, total_count "
            "FROM roster_candidates WHERE normalized=?",
            (kg,)).fetchone()
        if fam_row and fam_row[0] == "noise":
            stats["skip: family noise"] += 1
            continue
        if giv_row and giv_row[0] == "noise":
            stats["skip: given noise"] += 1
            continue
        if db.execute("SELECT 1 FROM aliases WHERE normalized=? AND form_type='given'",
                      (kf,)).fetchone():
            stats["skip: fam-slot is a given alias"] += 1
            continue

        # known TL manglings -> alias onto the real char
        if (kf, kg) in VARIANT_PAIRS:
            target = VARIANT_PAIRS[(kf, kg)]
            tcid = slug(target)
            if not db.execute("SELECT 1 FROM characters WHERE char_id=?",
                              (tcid,)).fetchone():
                stats["WARN variant target missing"] += 1
                continue
            add_alias(db, tcid, fa, "variant")
            add_alias(db, tcid, ga, "variant")
            for row, raw in ((fam_row, fa), (giv_row, ga)):
                if row and row[0] in ("unreviewed", "unknown"):
                    if claim(db, raw, tcid,
                             f"P1 pass3: TL variant of {target} "
                             f"('{fa} {ga}' x{info['n']})",
                             include_unknown=True):
                        stats["variant claims"] += 1
            stats["variant pairs handled"] += 1
            continue

        giv_exclusive = len(giv2fams[kg]) == 1

        # family already a real character -> claim exclusive givens onto it
        if fam_row and fam_row[0] == "character":
            fcid = fam_row[1]
            if fcid.startswith("provisional-"):
                stats["skip: family on E1 shell"] += 1
                continue
            canonical = db.execute(
                "SELECT canonical_name FROM characters WHERE char_id=?",
                (fcid,)).fetchone()[0]
            if not canonical.lower().startswith(fa.lower() + " ") and \
               canonical.split()[0].lower() != fa.lower():
                stats["skip: family-char canonical mismatch"] += 1
                print(f"WARN pair mismatch: {fa} {ga} -> {fcid} ({canonical})")
                continue
            if ga.lower() in eng:
                stats["skip: given is english (case B)"] += 1
                continue
            ctoks = canonical.split()
            if len(ctoks) >= 2 and normalize(ctoks[1]) != kg:
                stats["skip: given not in canonical"] += 1
                continue
            add_alias(db, fcid, ga, "given")
            if giv_row and giv_row[0] in ("unreviewed", "unknown") and giv_exclusive:
                if claim(db, ga, fcid,
                         f"P1 pass3: given of {canonical} "
                         f"('{fa} {ga}' x{info['n']})"):
                    stats["given claimed (existing char)"] += 1
            continue

        # case A: new char — strict precision gate
        if fam_row is None:
            stats["skip: no family row"] += 1
            continue
        if fam_row[2] < 2:
            stats["skip: family count < 2"] += 1
            continue
        if fa.lower() in eng and fa.lower() not in ALLOW_FAMILIES:
            stats["skip: family is english"] += 1
            continue
        if ga.lower() in eng:
            stats["skip: given is english"] += 1
            continue
        if fam_row[0] == "unknown":
            stats["skip: family unknown (deliberate)"] += 1
            continue
        if len(fam2givs[kf]) > 1:
            if fam_row[0] == "unreviewed":
                db.execute(
                    "UPDATE roster_candidates SET classification='unknown', "
                    "reviewer_note=? WHERE normalized=? AND classification='unreviewed'",
                    (f"P1 pass3: family pairs with "
                     f"{len(fam2givs[kf])} givens in scan — not claimed", kf))
                stats["family ambiguous -> unknown"] += 1
            else:
                stats["skip: ambiguous family, no claim"] += 1
            continue

        canonical = f"{fa} {ga}"
        cid = slug(canonical)
        exists = db.execute("SELECT 1 FROM characters WHERE char_id=?",
                            (cid,)).fetchone()
        if not exists:
            db.execute(
                "INSERT INTO characters "
                "(char_id, canonical_name, name_order, tier, status, notes) "
                "VALUES (?,?,?,?,?,?)",
                (cid, canonical, "family-given", 4, "confirmed",
                 f"P1 pass3 pair scan: '{fa} {ga}' x{info['n']} "
                 f"(first {info['first'][0]} p{info['first'][1]})"))
            created.append(canonical)
            stats["chars created"] += 1
        add_alias(db, cid, fa, "family")
        add_alias(db, cid, ga, "given")
        if fam_row[0] in ("unreviewed", "unknown"):
            if claim(db, fa, cid,
                     f"P1 pass3: family of {canonical} "
                     f"('{fa} {ga}' x{info['n']})"):
                stats["family claimed"] += 1
        if giv_row and giv_row[0] in ("unreviewed", "unknown") and giv_exclusive:
            if claim(db, ga, cid,
                     f"P1 pass3: given of {canonical} (exclusive pair)"):
                stats["given claimed (new char)"] += 1

    # shell cleanup for shells that gained a real owner in this pass
    shells = [r[0] for r in db.execute(
        "SELECT char_id FROM characters WHERE char_id LIKE 'provisional-%'")]
    for sh in shells:
        key = sh[len("provisional-"):]
        owner = db.execute(
            "SELECT a.char_id FROM aliases a JOIN characters c ON c.char_id=a.char_id "
            "WHERE a.normalized=? AND c.char_id NOT LIKE 'provisional-%' LIMIT 1",
            (key,)).fetchone()
        if not owner:
            continue
        db.execute(
            "UPDATE roster_candidates SET char_id=?, "
            "reviewer_note=COALESCE(reviewer_note,'') || ' [shell->real]' "
            "WHERE char_id=? AND classification='character'",
            (owner[0], sh))
        db.execute("UPDATE quotes SET char_id=? WHERE char_id=?", (owner[0], sh))
        nrefs = db.execute("SELECT COUNT(*) FROM roster_candidates WHERE char_id=?",
                           (sh,)).fetchone()[0]
        if nrefs == 0:
            db.execute("DELETE FROM aliases WHERE char_id=?", (sh,))
            db.execute("DELETE FROM characters WHERE char_id=?", (sh,))
            stats["shells dropped"] += 1

    leftover = db.execute(
        "SELECT c.char_id, (SELECT COUNT(*) FROM roster_candidates r "
        " WHERE r.char_id=c.char_id) AS refs "
        "FROM characters c WHERE c.char_id LIKE 'provisional-%' ORDER BY refs DESC").fetchall()
    if leftover:
        print("leftover shells:", ", ".join(f"{s}({r})" for s, r in leftover))

    db.commit()
    unrev3 = db.execute(
        "SELECT COUNT(*) FROM roster_candidates "
        "WHERE classification='unreviewed' AND total_count>=3").fetchone()[0]
    dist = dict(db.execute(
        "SELECT classification, COUNT(*) FROM roster_candidates "
        "GROUP BY classification").fetchall())
    chars = db.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    orphan = db.execute(
        "SELECT COUNT(*) FROM roster_candidates c "
        "LEFT JOIN characters ch ON ch.char_id=c.char_id "
        "WHERE c.classification='character' AND ch.char_id IS NULL").fetchone()[0]
    db.close()

    print("pairs scanned:", len(raw_pairs), " processed:", len(proc))
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print("candidates:", dist)
    print(f"characters: {chars}  unreviewed>=3: {unrev3}  orphan candidates: {orphan}")
    if created:
        print(f"\ncreated {len(created)} chars:")
        for c in created:
            print("   ", c)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""P1 roster discovery: multi-extractor name mining (E1-E6) over text/.

Writes candidates + sample contexts into roster_candidates table.
Normalization: macron folding, possessive strip, honorific strip -> merge key.
"""
import glob
import json
import os
import re
import sqlite3
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT_DIR = os.path.join(ROOT, "text")
DB_PATH = os.path.join(ROOT, "cote_kb.db")

# ---------- normalization ----------

MACRON = str.maketrans({
    "ō": "o", "ū": "u", "ā": "a", "ī": "i", "ē": "e",
    "Ō": "O", "Ū": "U", "Ā": "A", "Ī": "I", "Ē": "E",
})
HONORIFICS = ("kun", "san", "sensei", "senpai", "chan", "sama")


def fold(s: str) -> str:
    return s.translate(MACRON)


def normalize(raw: str) -> str:
    """Merge key: fold macrons, unify romanization variants (ou->o, doubled vowels),
    lowercase, strip possessive/honorific/space. Raw forms preserved in aliases."""
    s = fold(raw).replace("’", "'").lower()
    # ou -> o  (Kouenji==Kōenji, Ayanokouji==Ayanokōji, Sudou==Sudō, Kyou==Kyō)
    s = s.replace("ou", "o")
    # strip possessive, then honorifics BEFORE vowel collapse so that
    # 'Miichan'/'Sae-chan-sensei' strip cleanly ('mii' >= 3, chained
    # suffixes see their separator) instead of collapsing into odd keys
    s = re.sub(r"'s$", "", s)
    s = re.sub(r"s'$", "", s)
    for h in HONORIFICS:
        if not s.endswith(h):
            continue
        rem = s[: -len(h)]
        # strip only when clearly suffixed (separator) or glued with enough
        # name left — bare names like Asama/Misama must NOT eat 'sama'
        if (rem and s[-len(h) - 1] in "- \t'’") or len(rem) >= 3:
            s = rem.rstrip("- \t'’")
    # collapse doubled vowels (Ryuuen==Ryūen, Mii==Mi)
    s = re.sub(r"([aeiou])\1", r"\1", s)
    s = re.sub(r"[\s\-']", "", s)
    return s


# ---------- stoplist (common English / noise) ----------

STOP = set("""
The This That These Those There Here What Which Who Whom Why How When Where
It Its In On At Of As By With From Into Onto Upon Than Then Thus While During
After Before Above Below Under Over Again Once Else Since Because Although
Unless Whether Until Despite Plus Minus Per Via Each Every All Any Some Many
Most Few Several Such Another Other Others Both Either Neither None Nothing
Also Just Only Even Still Already Almost Maybe Perhaps Actually Anyway Besides
However Meanwhile Therefore Instead Certainly Perhaps Surely Obviously
Maybe Rather Almost Nearly Quite Rather Slightly Extremely
Really Very Too Also Just May Might Must Shall Should Would Could Can Will
Yes No Well Right Okay Ok Fine Good Great Bad Nice Cool Wow Hey Hello Hi
Please Thanks Thank Sorry Excuse Stop Wait Come Go Look Listen See Saw Seen
Make Makes Made Take Takes Taken Give Gives Given Come Comes Came Know Knows Knew
Think Thinks Thought Feel Feels Felt Want Wants Wanted Need Needs Needed
Say Says Said Tell Tells Told Ask Asks Asked Answer Answers Answered
One Two Three Four Five Six Seven Eight Nine Ten First Second Third Last Next
Mr Mrs Ms Dr Prof
English Japanese Chinese Korean Math Mathematics Science History Geography
Physics Chemistry Biology Class Classes Student Students School Schools
Room Rooms Page Pages Year Years Month Months Day Days Week Weeks
Monday Tuesday Wednesday Thursday Friday Saturday Sunday
January February March April May June July August September October November December
Morning Afternoon Evening Night Today Tomorrow Yesterday
Ability Abilities Exam Exams Test Tests Score Scores Point Points
Private Public Special New Old Early Late High Low Big Small Long Short
Story Stories Novel Chapter Chapters Volume Volumes
Japan Tokyo Yokohama Osaka Hokkaido Kyushu Okinawa Sendai Nagoya Sapporo
America American England Europe Asia China Korea
White Black Red Blue Green Yellow Brown Gray
Convolution Bonus MTLs MTL Fan Fans Wiki Wikipedia
Keyaki Mall Station Hotel Hospital Park Pool Beach Island Ship Boat Train
Bus Street Road Bridge Building Floor Hall Gym Library Cafeteria Dormitory
Dormitory Dormitories Club Clubs Team Teams Game Games Match Matches
Point Point Market Store Shop Restaurant Cafe Bar
President Chairman Director Manager Leader Captain Coach Teacher Tutor
You Your Yours Our Their There These Those Things Time School About Around
Though Through Thought Sound Mountain Country Young Youth Soul Course Outside
Everyone Someone Nobody Somebody Anyone Could Would Should About Amount Around
Because Before Behind Below Between During Except Inside Near Next Opposite
Outside Since Until Upon Without Within Anything Everything Nothing Something
Evening Morning Afternoon Night Week Month Summer Winter Spring Autumn
Teacher Student Example Reason Result Problem Answer Question Point Moment
Always Never Often Sometimes Usually Again Already Still Yet Ever Never
Cute Pretty Beautiful Strong Weak Quiet Loud Fresh Old Young Rich Poor
First Second Third Fourth Fifth Last Next Previous Final Initial
If But And Or Nor So Yet For
I'm I'll I'd I've It's That's There's Here's What's Who's Where's When's How's
He's She's We're They're You're Don't Doesn't Didn't Isn't Aren't Wasn't Weren't
Won't Can't Couldn't Wouldn't Shouldn't Should't Haven't Hasn't Hadn't Let's
im id ill ive its thats theres hes shes were youres dont doesnt didnt isnt arent
wasnt werent wont cant couldnt wouldnt shouldnt havent hasnt hadnt lets
Goldenagato
""".split())
STOP_LOWER = {w.lower() for w in STOP}


def is_noise_token(raw: str) -> bool:
    base = re.sub(r"['’]s$", "", raw.replace("’", "'"))
    if base.lower() in STOP_LOWER:
        return True
    if len(base) <= 2 and base.isupper():
        return True
    return False
    # single uppercase letter (initials) or very short all-caps
    if len(base) <= 2 and base.isupper():
        return True
    return False


# ---------- page-aware corpus reader ----------

PAGE_RE = re.compile(r"^--- page (\d+) ---$", re.M)


def iter_pages():
    """Yield (vol_id, file_stem, page, page_start_offset, page_text)."""
    import subprocess
    db = sqlite3.connect(DB_PATH)
    vols = db.execute("SELECT vol_id, file_stem FROM volumes ORDER BY chrono_order").fetchall()
    db.close()
    for vol_id, stem in vols:
        path = os.path.join(TXT_DIR, stem + ".txt")
        text = open(path, encoding="utf-8").read()
        marks = list(PAGE_RE.finditer(text))
        for i, m in enumerate(marks):
            start = m.end() + 1  # skip newline after marker
            end = marks[i + 1].start() - 1 if i + 1 < len(marks) else len(text)
            yield vol_id, stem, int(m.group(1)), start, text[start:end]


# ---------- extractors ----------

# E1: honorific pairs
E1_RE = re.compile(
    r"\b([A-Z][A-Za-zéèōūāīēÖü'’\-]+)-(kun|san|sensei|senpai|chan|sama)\b"
)

# E2/E3 shared token pattern (name-like single token, incl. macrons: Ryūen, Kōenji, Dōgami)
NAME_TOK = r"[A-Z][a-zéèōūāīēü'’\-]+"

# E2: mid-sentence capital (after lowercase char or ,;:)"')
E2_RE = re.compile(rf"(?<=[a-z,;:\)\"'])\s+({NAME_TOK})\b")

# E3: adjacent capital pair, both tokens name-like
E3_RE = re.compile(rf"\b({NAME_TOK}) ({NAME_TOK})\b")

# E4: dialogue tags — "X said", "said X", "X," said
SPEECH_VERBS = (
    "said|asked|replied|shouted|whispered|muttered|murmured|called|yelled|"
    "cried|screamed|answered|continued|added|insisted|demanded|begged|"
    "suggested|stated|declared|remarked|noted|pointed|argued|warned|"
    "ordered|commanded|groaned|sighed|laughed|smiled|grinned|snapped|"
    "hissed|barked|growled|rasped|breathed|sobbed|chuckled|giggled|"
    "stammered|stuttered|exclaimed|retorted|shot back|said quietly"
)
E4a_RE = re.compile(rf"\b(?:{SPEECH_VERBS})\s+(?:to\s+)?({NAME_TOK})\b")
E4b_RE = re.compile(rf"\b({NAME_TOK})\s+(?:{SPEECH_VERBS})\b")
# vocative inside quotes: "Hey, Suzuki" / "Come on, Kiyopon"
E4c_RE = re.compile(rf"[\"'](?:[A-Z][a-z]+[!,.]?\s+)?(?:[A-Z][a-z]+[!,]\s+)({NAME_TOK})[!,.?]")

# E5: intro patterns
E5_RE = re.compile(
    rf"\b(?:named|called)\s+({NAME_TOK}(?:\s+{NAME_TOK})?)\b"
    rf"|\b({NAME_TOK})\s+(?:was|were|is|are)\s+(?:a|an|the)\s+\w"
)

# E6: nickname suffixes
E6_RE = re.compile(rf"\b({NAME_TOK}(?:pon|cchi|yan|rin|tan|nin|kko|bee|chi))\b")


def context_snippet(text, start, end, radius=70):
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    snip = " ".join(text[a:b].split())
    return snip


def mine():
    acc = defaultdict(lambda: {"count": 0, "signals": set(), "contexts": [], "raws": set()})

    def add(raw, norm, signal, vol, page, snip):
        if is_noise_token(raw):
            return
        if not re.fullmatch(r"[A-Z][a-zéèōūāīēü'’\-]+", raw):
            return
        e = acc[norm]
        e["count"] += 1
        e["signals"].add(signal)
        e["raws"].add(raw)
        if len(e["contexts"]) < 6:
            e["contexts"].append({"vol": vol, "page": page, "snippet": snip})

    for vol_id, stem, page, pstart, ptext in iter_pages():
        for m in E1_RE.finditer(ptext):
            raw = m.group(1)
            add(raw, normalize(raw), "E1", vol_id, page,
                context_snippet(ptext, m.start(), m.end()))
        for m in E2_RE.finditer(ptext):
            raw = m.group(1)
            add(raw, normalize(raw), "E2", vol_id, page,
                context_snippet(ptext, m.start(), m.end()))
        for m in E3_RE.finditer(ptext):
            for raw in m.groups():
                add(raw, normalize(raw), "E3", vol_id, page,
                    context_snippet(ptext, m.start(), m.end()))
        for rx, sig in ((E4a_RE, "E4"), (E4b_RE, "E4"), (E4c_RE, "E4voc"),
                        (E5_RE, "E5"), (E6_RE, "E6")):
            for m in rx.finditer(ptext):
                for raw in m.groups():
                    if raw is None:
                        continue
                    # E5 can capture two-token names; take tokens individually
                    for tok in raw.split():
                        add(tok, normalize(tok), sig, vol_id, page,
                            context_snippet(ptext, m.start(), m.end()))

    db = sqlite3.connect(DB_PATH)
    db.execute("DELETE FROM roster_candidates")
    rows = []
    for norm, e in sorted(acc.items(), key=lambda kv: -kv[1]["count"]):
        rows.append((
            sorted(e["raws"])[0] if len(e["raws"]) == 1 else "/".join(sorted(e["raws"])[:4]),
            norm, e["count"],
            json.dumps(sorted(e["signals"])),
            json.dumps(e["contexts"][:4], ensure_ascii=False),
            "unreviewed", None, None,
        ))
    db.executemany(
        "INSERT INTO roster_candidates "
        "(raw_form, normalized, total_count, signals, sample_contexts, "
        " classification, char_id, reviewer_note) VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) VALUES (?,?,?,?)",
        ("roster_mine_e1_e6", now, now, f"{len(rows)} distinct normalized candidates"),
    )
    db.commit()
    db.close()
    print(f"{len(rows)} distinct normalized candidates written")


def stats():
    db = sqlite3.connect(DB_PATH)
    print("total:", db.execute("SELECT COUNT(*) FROM roster_candidates").fetchone()[0])
    for sig in ("E1", "E2", "E3", "E4", "E4voc", "E5", "E6"):
        n = db.execute(
            "SELECT COUNT(*) FROM roster_candidates WHERE signals LIKE ?",
            (f"%{sig}%",),
        ).fetchone()[0]
        print(f"  {sig:5s}: {n}")
    print("\nTop 40:")
    for norm, cnt, sigs in db.execute(
        "SELECT normalized, total_count, signals FROM roster_candidates "
        "ORDER BY total_count DESC LIMIT 40"
    ):
        print(f"  {cnt:6d}  {norm:25s} {sigs}")
    db.close()


if __name__ == "__main__":
    mine()
    stats()

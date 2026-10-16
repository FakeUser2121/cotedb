"""P3 step 3: attribution deepening pass (runs AFTER quote_mine).

python3 kb/quote_attr.py

1. GENDER VOTES — corpus-derived, no config: every full/given alias
   occurrence followed within 60 chars by a gendered pronoun casts a vote;
   majority (>=4 votes, >=0.75 ratio) wins. Recomputed every run.
2. PRONOUN ROWS (quotes.context='pronoun', char_id IS NULL):
   * re-read the 120 chars after span_end; if it is a strict dialogue tag
     (`he/she/they + speech-act verb`, action-verb starts are NOT tags):
     scan back on the same page (<=800 chars, cut at page marker) for the
     nearest alias-resolvable name whose voted gender matches the pronoun
     -> char_id, conf 0.65 (honest moderate confidence)
   * else the look was narration (quote itself is untagged speech):
     context -> 'speech'
3. AMBIGUOUS ROWS (conf 0.2, char_id NULL, context A1/A2): same-window
   scan for a candidate's distinctive GIVEN-name evidence; exactly one
   candidate matches -> resolve, conf 0.7. No evidence -> stays NULL.

Idempotent: step-2/3 updates only touch rows still NULL/unresolved, so
re-runs are no-ops; after a quote_mine re-run the deepening simply
recomputes. Nothing outside `quotes` is modified.
"""
import re
import sys
from collections import Counter, defaultdict

from roster_mine import DB_PATH, normalize

import sqlite3

PRON = r"(?:he|she|they)"
TAG_VERBS = (
    "said|asked|replied|answered|continued|returned|added|noted|insisted|"
    "countered|retorted|argued|demanded|warned|muttered|whispered|shouted|"
    "cried|stammered|stated|claimed|admitted|denied|explained|announced|"
    "agreed|refused|objected|protested|teased|mocked|interrupted|concluded|"
    "echoed|ordered|commanded|shot|snapped|laughed|smiled|sighed|groaned|"
    "questioned|exclaimed|called|murmured|suggested|demanded"
)
RE_TAG = re.compile(r"^\s*(" + PRON + r")\s+(" + TAG_VERBS + r")\b", re.I)
RE_PAGE = re.compile(r"^--- page \d+ ---$", re.M)
RE_PRONWORD = re.compile(r"\b(he|she|his|her|him|hers|herself|himself)\b", re.I)
RE_GENDERED = {"he": "m", "she": "f", "him": "m", "his": "m",
               "her": "f", "hers": "f", "himself": "m", "herself": "f"}
NAME_RE = re.compile(r"[A-Z][a-zéèōūāīēü'’\-]+(?:\s+[A-Z][a-zéèōūāīēü'’\-]+)?")
MASC = {"he", "him", "his", "himself"}
FEM = {"she", "her", "hers", "herself"}

DEFAULT_TAG = {"horikita": ("horikita-suzune", 0.8)}


def load_files(db):
    files = {}
    for vol_id, stem in db.execute("SELECT vol_id, file_stem FROM volumes"):
        files[vol_id] = open(
            f"text/{stem}.txt", encoding="utf-8").read()
    return files


def gender_votes(db, files):
    forms = defaultdict(set)
    for cid, raw in db.execute(
        "SELECT DISTINCT char_id, raw_form FROM aliases WHERE is_noise=0"
    ):
        forms[cid].add(raw)
    votes = defaultdict(Counter)
    for cid, raws in forms.items():
        for vol_id, text in files.items():
            for raw in raws:
                if not raw or raw[0].islower():
                    continue
                for m in re.finditer(r"\b" + re.escape(raw) + r"\b", text):
                    nxt = RE_PRONWORD.search(text, m.end(), m.end() + 60)
                    if nxt:
                        votes[cid][RE_GENDERED[nxt.group(1).lower()]] += 1
    gender = {}
    for cid, c in votes.items():
        total = c["m"] + c["f"]
        top, n = c.most_common(1)[0]
        if total >= 4 and n / total >= 0.75:
            gender[cid] = top
    return gender


def window_names(text, pos, aliases_by_norm):
    w = text[max(0, pos - 800):pos]
    cut = RE_PAGE.search(w)
    if cut:
        w = w[cut.end():]
    found = []
    for m in NAME_RE.finditer(w):
        key = normalize(m.group(0))
        cid = aliases_by_norm.get(key)
        if cid:
            found.append((m.start(), cid, m.group(0)))
    return found


def coref_pronoun(text, span_end, pron, gender, aliases_by_norm):
    look = text[span_end:span_end + 120]
    m = RE_TAG.match(look)
    if not m:
        return None, None
    want = "f" if pron.lower() in ("she", "her", "hers", "herself") else "m"
    if pron.lower() in ("we", "they", "us", "them"):
        want = None
    if want is None:
        return None, None
    names = window_names(text, span_end, aliases_by_norm)
    for _, cid, _n in reversed(names):
        if gender.get(cid) == want:
            return cid, 0.65
    return None, None


def resolve_ambiguous(text, span_start, span_end, cands, aliases_by_norm,
                      given_index):
    w_start = max(0, span_start - 800)
    w = text[w_start:span_end + 800]
    cut = RE_PAGE.search(w)
    if cut:
        w = w[cut.end():]
    hits = set()
    for cid in cands:
        for g in given_index.get(cid, ()): 
            if re.search(r"\b" + re.escape(g) + r"\b", w):
                hits.add(cid)
                break
    if len(hits) == 1:
        return hits.pop()
    return None


def main():
    db = sqlite3.connect(DB_PATH)
    files = load_files(db)
    gender = gender_votes(db, files)
    alias_rows = db.execute(
        "SELECT DISTINCT normalized, char_id FROM aliases WHERE is_noise=0"
    ).fetchall()
    aliases_by_norm = defaultdict(set)
    for norm, cid in alias_rows:
        aliases_by_norm[norm].add(cid)
    aliases_by_norm = {k: (list(v)[0] if len(v) == 1 else None)
                       for k, v in aliases_by_norm.items()}
    given_index = defaultdict(list)
    for cid, raw, ftype in db.execute(
        "SELECT char_id, raw_form, form_type FROM aliases "
        "WHERE form_type IN ('given','full') AND is_noise=0"
    ):
        given_index[cid].append(raw)

    stats = Counter()
    rows = db.execute(
        "SELECT quote_id, vol_id, span_start, span_end, text_verbatim "
        "FROM quotes WHERE char_id IS NULL AND context='pronoun'"
    ).fetchall()
    for qid, vol, s, e, tv in rows:
        text = files[vol]
        look = text[e:e + 120]
        m = RE_TAG.match(look)
        if not m:
            db.execute("UPDATE quotes SET context='speech' WHERE quote_id=?",
                       (qid,))
            stats["pronoun -> speech (was narration)"] += 1
            continue
        cid, conf = coref_pronoun(text, e, m.group(1), gender,
                                  aliases_by_norm)
        if cid:
            db.execute(
                "UPDATE quotes SET char_id=?, attribution_confidence=? "
                "WHERE quote_id=?", (cid, conf, qid))
            stats["pronoun coreferred"] += 1
        else:
            stats["pronoun tag kept NULL"] += 1

    amb = db.execute(
        "SELECT quote_id, vol_id, span_start, span_end, char_id "
        "FROM quotes WHERE char_id IS NULL AND attribution_confidence=0.2 "
        "AND context IN ('A1','A2')"
    ).fetchall()
    amb_cands = defaultdict(set)
    for cid, norm in db.execute(
        "SELECT DISTINCT char_id, normalized FROM aliases WHERE is_noise=0"
    ):
        amb_cands[norm].add(cid)
    for qid, vol, s, e, cid in amb:
        norm_key = None
        text = files[vol]
        w = text[max(0, s - 300):e + 800]
        cut = RE_PAGE.search(w)
        if cut:
            w = w[cut.end():]
        for m in NAME_RE.finditer(w):
            k = normalize(m.group(0))
            if len(amb_cands.get(k, ())) > 1:
                norm_key = k
                break
        if norm_key is None:
            stats["ambiguous kept"] += 1
            continue
        cands = sorted(amb_cands[norm_key])
        pick = resolve_ambiguous(text, s, e, cands, aliases_by_norm,
                                 given_index)
        if pick:
            db.execute(
                "UPDATE quotes SET char_id=?, attribution_confidence=0.7 "
                "WHERE quote_id=?", (pick, qid))
            stats["ambiguous resolved"] += 1
        else:
            stats["ambiguous kept"] += 1

    RE_TAGKEY = re.compile(r"[,\s]([A-Z][A-Za-z’\-]+)")
    RE_MANABU_TAG = re.compile(
        r"\bManabu\b[^.\n]{0,40}(said|asked|replied)|(?:said|asked|replied)"
        r"[^.]{0,20}\bManabu\b")
    for qid, vol, s, e, cid in db.execute(
            "SELECT quote_id, vol_id, span_start, span_end, char_id "
            "FROM quotes WHERE char_id IS NULL AND "
            "attribution_confidence=0.2 AND context IN ('A1','A2')"
    ).fetchall():
        text = files[vol]
        m = RE_TAGKEY.search(text[e:e + 70])
        if not m:
            continue
        key = normalize(m.group(1))
        if key not in DEFAULT_TAG:
            continue
        ps = text.rfind("--- page ", 0, e)
        pe = text.find("--- page ", e)
        if RE_MANABU_TAG.search(text[ps: pe if pe > 0 else len(text)]):
            stats["default skipped (Manabu on page)"] += 1
            continue
        target, conf = DEFAULT_TAG[key]
        db.execute(
            "UPDATE quotes SET char_id=?, attribution_confidence=? "
            "WHERE quote_id=?", (target, conf, qid))
        stats["default rule applied"] += 1

    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) "
        "VALUES ('quote_attr', datetime('now'), datetime('now'), ?)",
        (f"gender={len(gender)}",))
    db.commit()
    print(f"gender-known chars: {len(gender)} / "
          f"{db.execute('SELECT COUNT(*) FROM characters').fetchone()[0]}")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    db.close()


if __name__ == "__main__":
    main()

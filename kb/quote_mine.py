"""P3 step 1: verbatim dialogue extraction with speaker attribution.

Scope (deliberately small — one volume per run, verify, then expand):
  python3 kb/quote_mine.py y1v1 [more_vols...]

For each run page of the given volume(s):
  * find every curly-quoted dialogue span “...” (complete verbatim capture,
    multi-line kept as-is; page-boundary spans are missed by design here)
  * look for an explicit same-sentence attribution after the closing quote:
      A1: ” said Horikita.          verb + name
      A2: ” Horikita said.          name + verb
      A3: ” I asked.                first-person -> per-volume POV char
    pronoun/she-said forms stay unattributed (honest, conf 0)
  * resolve the name through the verified aliases table (normalize() imported
    from roster_mine so keys match P1/P2 exactly); ambiguous or unknown names
    stay char_id NULL with confidence 0.2 / 0.0
  * offsets are absolute char positions in text/<stem>.txt

Idempotent per volume: previous quotes rows (+ their external-content FTS
entries) for the volume are deleted before reinsert. quote_mine does not
touch any other table.
"""
import os
import re
import sys
from collections import Counter

from roster_mine import DB_PATH, iter_pages, normalize

import sqlite3

VERBS = (
    "said|asked|replied|answered|continued|returned|called|shouted|yelled|"
    "muttered|whispered|insisted|added|noted|questioned|exclaimed|argued|"
    "admitted|denied|claimed|stated|explained|announced|retorted|countered|"
    "agreed|refused|ordered|commanded|echoed|groaned|sighed|laughed|smiled|"
    "cried|snapped|shot|demanded|warned|murmured|shrieked|stammered|"
    "suggested|objected|protested|teased|mocked|interrupted|concluded"
)

NAME = r"[A-Z][A-Za-zéèōūāīēü'’\-]+(?:\s+[A-Z][A-Za-zéèōūāīēü'’\-]+)?"
HON = r"(?:-(?:kun|san|sensei|chan|sama|senpai|dono))?"

RE_QUOTE = re.compile(r"“([^”]*)”|\"(.*?)\"|«([^»]*)»", re.S)
RE_A1 = re.compile(r"^\s*[,;]?\s*(" + VERBS + r")\s+(" + NAME + r")(" + HON + r")\b")
RE_A2 = re.compile(r"^\s*[,;]?\s*(" + NAME + r")(" + HON + r")\s+(" + VERBS + r")\b")
RE_A3 = re.compile(r"^\s*[,;]?\s*I\s+(" + VERBS + r")\b")

STOP_FIRST = {
    "He", "She", "They", "We", "It", "You", "The", "And", "But", "So", "As",
    "Then", "When", "What", "That", "There", "This", "Those", "His", "Her",
    "My", "Your", "One", "Now", "Well", "Okay", "If", "Yes", "No",
}

POV_MAP = {v: "ayanokouji-kiyotaka" for v in
           [f"y1v{i}" for i in range(1, 12)] + [f"y2v{i}" for i in range(1, 13)]
           + ["y3v1"]}

FP_RE = re.compile(r"\b(I|I'd|I'll|I'm|me|my|mine|we|we'd|we'll|we're|our|ours|you|your|yours)\b")
CONTR_RE = re.compile(r"[’'](s|d|ll|re|m)\b|n't\b", re.I)
INTERJ = {
    "no", "yes", "hey", "huh", "hmm", "hm", "um", "uh", "eh", "okay", "ok",
    "wait", "fine", "sorry", "right", "really", "exactly", "what", "why",
    "how", "so", "and", "but", "well", "now", "hello", "goodbye", "bye",
    "thanks", "please", "indeed", "maybe", "perhaps", "come", "look", "see",
}


def classify_quoted(inner):
    t = inner.strip()
    if not t:
        return "other"
    if re.search(r"[.!?…,][\"”'’]?$", t) or t.endswith(("—", "–", "-", "★")):
        return "speech"
    if FP_RE.search(t) or CONTR_RE.search(t):
        return "speech"
    toks = t.split()
    if len(toks) <= 4 and not re.search(r"[.:;\"“”]", t):
        if toks[0].lower().rstrip(",!?…") in INTERJ:
            return "speech"
        if len(t) <= 30 and re.fullmatch(r"[A-Za-zéèōūāīēü'’ \-]+", t):
            return "term"
    return "other"


def resolve(db, name):
    key = normalize(name)
    rows = db.execute(
        "SELECT DISTINCT char_id FROM aliases WHERE normalized=?", (key,)
    ).fetchall()
    if len(rows) == 1:
        return rows[0][0], 1.0
    if len(rows) > 1:
        return None, 0.2
    return None, 0.0


def attribute(db, vol_id, look, inner):
    m = RE_A1.match(look)
    if m:
        name = m.group(2)
        if name.split()[0] in STOP_FIRST:
            return None, 0.0, "pronoun", name
        cid, conf = resolve(db, name)
        return cid, conf, "A1", name
    m = RE_A2.match(look)
    if m:
        name = m.group(1)
        if name.split()[0] in STOP_FIRST:
            return None, 0.0, "pronoun", name
        cid, conf = resolve(db, name)
        return cid, conf, "A2", name
    m = RE_A3.match(look)
    if m:
        cid = POV_MAP.get(vol_id)
        if cid:
            return cid, 0.9, "A3-pov", "I"
        return None, 0.0, "A3-nopov", "I"
    if re.match(r"^\s*[a-z]+ (said|asked|replied|answered)\b", look):
        return None, 0.0, "pronoun", "-"
    return None, 0.0, classify_quoted(inner), "-"


def purge_volume(db, vol_id):
    rows = db.execute(
        "SELECT quote_id, text_verbatim FROM quotes WHERE vol_id=?", (vol_id,)
    ).fetchall()
    for qid, text in rows:
        db.execute(
            "INSERT INTO quotes_fts(quotes_fts, rowid, text_verbatim) "
            "VALUES('delete', ?, ?)",
            (qid, text),
        )
    db.execute("DELETE FROM quotes WHERE vol_id=?", (vol_id,))
    return len(rows)


def mine_volume(db, vol_id, vol_ord):
    stats = Counter()
    unresolved = Counter()
    inserted = 0
    id_base = (vol_ord + 1) * 1_000_000
    stats["deleted_prev"] = purge_volume(db, vol_id)
    for vid, stem, page, pstart, ptext in iter_pages():
        if vid != vol_id:
            continue
        stats["pages"] += 1
        for m in RE_QUOTE.finditer(ptext):
            inner = next(g for g in m.groups() if g is not None)
            if not inner or len(inner) > 4000 or not re.search(r"\w", inner):
                continue
            stats["spans"] += 1
            look = ptext[m.end():m.end() + 120]
            look = look.split("“")[0]
            cid, conf, kind, name = attribute(db, vol_id, look, inner)
            stats[kind] += 1
            if kind in ("A1", "A2") and cid is None:
                if conf == 0.2:
                    stats["ambiguous-name"] += 1
                else:
                    unresolved[name] += 1
            db.execute(
                "INSERT INTO quotes (quote_id, char_id, vol_id, pdf_page, "
                "span_start, span_end, text_verbatim, context, "
                "attribution_confidence, reviewed) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                (
                    id_base + inserted + 1,
                    cid,
                    vol_id,
                    page,
                    pstart + m.start(),
                    pstart + m.end(),
                    inner,
                    kind,
                    conf,
                ),
            )
            inserted += 1
    stats["inserted"] = inserted
    return stats, unresolved


def main():
    if len(sys.argv) < 2:
        print("usage: quote_mine.py <vol_id> [vol_id ...]")
        sys.exit(1)
    vols = sys.argv[1:]
    db = sqlite3.connect(DB_PATH)
    known = {r[0] for r in db.execute("SELECT vol_id FROM volumes").fetchall()}
    bad = [v for v in vols if v not in known]
    if bad:
        print("unknown vol_id(s):", ", ".join(bad))
        sys.exit(1)
    vol_ord = {v: i for i, (v,) in enumerate(db.execute(
        "SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    for vol_id in vols:
        stats, unresolved = mine_volume(db, vol_id, vol_ord[vol_id])
        db.commit()
        print(f"=== {vol_id} ===")
        for k in sorted(stats):
            print(f"  {k}: {stats[k]}")
        if unresolved:
            print("  top unresolved names:")
            for name, n in unresolved.most_common(15):
                print(f"    {name}: {n}")
    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) "
        "VALUES ('quote_mine', datetime('now'), datetime('now'), ?)",
        (" ".join(vols),),
    )
    db.commit()
    db.close()


if __name__ == "__main__":
    main()

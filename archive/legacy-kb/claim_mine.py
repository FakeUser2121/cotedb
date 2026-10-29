"""P3 step 6b: pattern-mined claims (starter set, anchors included).

python3 kb/claim_mine.py

Sentence pattern: `<Name> is|was a|an|the <predicate 8-90 chars>` with an
unambiguously resolvable name, EXCLUDING anything inside an already-quoted
span (quotes table has exact offsets).

kind: 'character_claim' with claimant = volume POV when the sentence
carries first-person language (it is that narrator's claim, not the
author's), else 'narrator_fact'. perspective = same POV when known.
confidence 0.6 — pattern mining; metaphors and opinion-narration survive
in the pool by design (they are still attributed statements with exact
anchors, and P5 authors refine per char).

Marker: reliability_note = 'auto:claim_mine-v1'. Full rebuild each run
(DELETE marker rows first) — hand-authored claims (no marker) untouched.
Span anchors are absolute offsets into text/<stem>.txt; pdf_page via
binary search over page markers.
"""
import bisect
import re
import sqlite3
from bisect import bisect_right

from roster_mine import DB_PATH, normalize

import sys

MARKER = "auto:claim_mine-v1"
POV_MAP = {v: "ayanokouji-kiyotaka" for v in
           [f"y1v{i}" for i in range(1, 12)] + [f"y2v{i}" for i in range(1, 13)]
           + ["y3v1"]}
PAGE_RE = re.compile(r"^--- page (\d+) ---$", re.M)
NAME = r"([A-Z][a-zéèōūāīēü'’\-]+(?:\s+[A-Z][a-zéèōūāīēü'’\-]+)?)"
RE_SENT = re.compile(
    r"\b" + NAME + r"\s+(?:is|was|are|were)\s+(?:a|an|the)\s+"
    r"([^.\n!?]{8,90})[.\n]")
FIRST_PERSON = re.compile(r"\b(I|my|me|we|our|us|mine)\b")


def build_alias_map(db):
    multi = {n for (n,) in db.execute(
        "SELECT normalized FROM aliases WHERE is_noise=0 "
        "GROUP BY normalized HAVING COUNT(DISTINCT char_id)>1")}
    return {n: c for n, c in db.execute(
        "SELECT DISTINCT normalized, char_id FROM aliases WHERE is_noise=0")
        if n not in multi}


def main():
    db = sqlite3.connect(DB_PATH)
    alias = build_alias_map(db)
    db.execute("DELETE FROM claims WHERE reliability_note=?", (MARKER,))
    q_spans = {}
    for vol, s, e in db.execute(
            "SELECT vol_id, span_start, span_end FROM quotes"):
        q_spans.setdefault(vol, []).append((s, e))

    made = skipped_quote = 0
    vol_ord = {v: i for i, (v,) in enumerate(db.execute(
        "SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    for vol, stem in db.execute(
            "SELECT vol_id, file_stem FROM volumes ORDER BY chrono_order"):
        raw = open(f"text/{stem}.txt", encoding="utf-8").read()
        text = raw.replace("\n", " ")
        id_base = (vol_ord[vol] + 1) * 1_000_000
        vol_made = 0
        starts = [m.start() for m in PAGE_RE.finditer(raw)]
        pages = [int(m.group(1)) for m in PAGE_RE.finditer(raw)]
        spans = sorted(q_spans.get(vol, ()))
        sp_s = [s for s, _ in spans]
        pov = POV_MAP.get(vol)
        for m in RE_SENT.finditer(text):
            cid = alias.get(normalize(m.group(1)))
            if not cid:
                continue
            pos = m.start()
            before = text[max(0, pos - 60):pos].rstrip()
            if before and before[-1] not in ".!?…””»\"'" and not before.endswith("---"):
                continue
            if re.search(r"Goldenagato|mp4directs|https?://|Page \d+ Goldenagato",
                         m.group(0)):
                continue
            i = bisect_right(sp_s, pos) - 1
            if i >= 0 and pos < spans[i][1]:
                skipped_quote += 1
                continue
            sent = re.sub(r"\s+", " ", m.group(0)).strip().rstrip(".\n") + "."
            if not sent.endswith("."):
                sent += "."
            pidx = bisect_right(starts, pos) - 1
            page = pages[pidx] if pidx >= 0 else 0
            fp = bool(FIRST_PERSON.search(m.group(0)))
            kind = "character_claim" if (fp and pov) else "narrator_fact"
            db.execute(
                "INSERT INTO claims (claim_id, char_id, claim, kind, "
                "claimant, perspective, corroboration, confidence, vol_id, "
                "pdf_page, span_start, span_end, evidence_quote, "
                "reliability_note) "
                "VALUES (?, ?, ?, ?, ?, ?, 'none', 0.6, ?, ?, ?, ?, ?, ?)",
                (id_base + vol_made + 1,
                 cid, sent, kind, pov if fp else "narrator", pov, vol, page,
                 pos, m.end(), m.group(0).replace("\n", " "), MARKER))
            made += 1
            vol_made += 1

    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) "
        "VALUES ('claim_mine', datetime('now'), datetime('now'), ?)",
        (f"claims={made} skipped_inside_quotes={skipped_quote}",))
    db.commit()
    print(f"claims mined: {made}  (skipped inside quotes: {skipped_quote})")
    print("by kind:", dict(db.execute(
        "SELECT kind, COUNT(*) FROM claims WHERE reliability_note=? "
        "GROUP BY kind", (MARKER,))))
    print("top chars:", db.execute(
        "SELECT char_id, COUNT(*) n FROM claims WHERE reliability_note=? "
        "GROUP BY char_id ORDER BY n DESC LIMIT 8", (MARKER,)).fetchall())
    db.close()


if __name__ == "__main__":
    main()

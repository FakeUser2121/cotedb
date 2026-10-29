"""P3 step 4: contextual speaker inference for untagged dialogue.

python3 kb/quote_infer.py

Runs AFTER quote_mine + quote_attr. Two conservative tiers, both honest
confidence, both idempotent (only touch context='speech' rows still NULL):

  T1 act-pre  — narration sentence right before the quote ends with
                `Name <action>.` (resolvable, unambiguous name) → speaker,
                conf 0.55 (action-subject usually speaks the next line)

  T2 run-alt  — maximal runs of whitespace-adjacent quote spans
                (gap < 60 chars of pure whitespace). Every interior segment
                BETWEEN two attributed anchors is filled only when strict
                alternation is forced by parity: anchors differ, distance
                odd → interior speakers alternate a1,a2,a1,... conf 0.45.
                Same-anchor segments and unanchored runs are left NULL
                (self-continuation vs reply is genuinely ambiguous — the
                honest call).

Everything else in the 49k speech pile stays unattributed on purpose:
without scene anchors speaker identity is not derivable, and noise at
scale would poison downstream quote banks. Coverage reports show the gap;
P6 audits sample it.
"""
import re
from collections import Counter, defaultdict

from roster_mine import DB_PATH, normalize

import sqlite3

ACTION = (
    "smiled|sighed|nodded|frowned|grinned|laughed|cried|shook|crossed|took|"
    "turned|leaned|gestured|whispered|muttered|stared|blinked|shrugged|"
    "paused|continued|added|murmured|exclaimed|shouted|put|placed|stood|sat|"
    "walked|came|looked|watched|glanced|rose|said|pointed|tapped|rubbed|"
    "clenched|folded|raised|lowered|dropped|flashed|grabbed|breathed|"
    "swallowed|groaned|chuckled|giggled|smirked|beamed|tilted|perked|"
    "flinched|winced|straightened|announced|shot|snapped"
)
NAME = r"([A-Z][a-zéèōūāīēü'’\-]+(?:\s+[A-Z][a-zéèōūāīēü'’\-]+)?)"
RE_PRE = re.compile(
    r"([A-Z][A-Za-z’\-\s]{2,40}?)\s+(?:" + ACTION + r")[a-z]*"
    r"(?:\s+[\w’]+){0,6}[\.\?…][”\"]?\s+$")
WS_GAP = re.compile(r"^[\s ]*$")


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
    files = {v: open(f"text/{s}.txt", encoding="utf-8").read()
             for v, s in db.execute("SELECT vol_id, file_stem FROM volumes")}
    stats = Counter()
    examples = defaultdict(list)

    rows = db.execute(
        "SELECT quote_id, vol_id, span_start, span_end FROM quotes "
        "WHERE context='speech' AND char_id IS NULL"
    ).fetchall()
    for qid, vol, s, e in rows:
        m = RE_PRE.search(files[vol][max(0, s - 130):s])
        if not m:
            continue
        cid = alias.get(normalize(m.group(1).strip()))
        if cid:
            db.execute(
                "UPDATE quotes SET char_id=?, attribution_confidence=0.55, "
                "context='act-pre' WHERE quote_id=?", (cid, qid))
            stats["T1 act-pre assigned"] += 1
            if len(examples["T1"]) < 8:
                examples["T1"].append((cid, m.group(1).strip()))

    by_vol = defaultdict(list)
    for qid, vol, s, e, cid, ctx in db.execute(
            "SELECT quote_id, vol_id, span_start, span_end, char_id, "
            "context FROM quotes"):
        by_vol[vol].append((s, e, cid, qid, ctx))
    for vol, spans in by_vol.items():
        spans.sort()
        text = files[vol]
        runs, cur = [], [spans[0]]
        for prev, cur_sp in zip(spans, spans[1:]):
            gap = text[prev[1]:cur_sp[0]]
            if len(gap) < 60 and WS_GAP.match(gap):
                cur.append(cur_sp)
            else:
                runs.append(cur)
                cur = [cur_sp]
        runs.append(cur)
        for run in runs:
            anchors = [(i, sp[2]) for i, sp in enumerate(run) if sp[2]]
            for (i1, a), (i2, b) in zip(anchors, anchors[1:]):
                if a == b or (i2 - i1) % 2 == 0:
                    continue
                interior = run[i1 + 1:i2]
                if not interior:
                    continue
                ok = True
                for k, sp in enumerate(interior, start=1):
                    want = b if k % 2 == 1 else a
                    if sp[2] and sp[2] != want:
                        ok = False
                        break
                if not ok:
                    stats["T2 parity conflict"] += 1
                    continue
                for k, sp in enumerate(interior, start=1):
                    want = b if k % 2 == 1 else a
                    if sp[2] or sp[4] != "speech":
                        continue
                    db.execute(
                        "UPDATE quotes SET char_id=?, "
                        "attribution_confidence=0.45, context='run-alt' "
                        "WHERE quote_id=?", (want, sp[3]))
                    stats["T2 run-alt assigned"] += 1
                    if len(examples["T2"]) < 8:
                        examples["T2"].append((want, a, b))

    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) "
        "VALUES ('quote_infer', datetime('now'), datetime('now'), '')")
    db.commit()
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    for t in examples["T1"]:
        print("  T1 ex:", t)
    for t in examples["T2"]:
        print("  T2 ex:", t)
    db.close()


if __name__ == "__main__":
    main()

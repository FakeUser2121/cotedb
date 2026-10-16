"""P3 step 6a: mention_stats + coverage grid.

python3 kb/mention_build.py

mention_stats (vol_id, token, count):
  for every non-noise alias, word-boundary occurrence count per volume
  file. token = canonical form (macron-folded + ou->o + doubled-vowel
  collapse, same map both sides, so 'Ōnuki'/'Onuki' or 'Kōenji'/
  'Kouenji' or 'Ryūen'/'Ryuuen' count together);
  map token -> chars through aliases at query time (a form may belong
  to several chars).

coverage (char_id, vol_id, status):
  every (char, vol) with total alias mentions > 0 gets a row —
  'quotes' if the char has >=1 attributed quote in that vol, else
  'occurrences'. Absent row = no detected presence.

Both are full-rebuild idempotent (DELETE + INSERT).
"""
import re
import sqlite3
from collections import defaultdict

from roster_mine import DB_PATH, fold


def canon(s):
    s = fold(s).replace("ou", "o")
    return re.sub(r"([aeiouAEIOU])\1", r"\1", s)


def main():
    db = sqlite3.connect(DB_PATH)
    forms = [r for r in db.execute(
        "SELECT DISTINCT raw_form FROM aliases WHERE is_noise=0 "
        "AND raw_form IS NOT NULL AND TRIM(raw_form)<>''")]
    forms = [canon(f) for (f,) in forms if re.search(r"\w", f)]
    forms = sorted({f for f in forms})
    comps = [(f, re.compile(r"\b" + re.escape(f) + r"\b")) for f in forms]

    db.execute("DELETE FROM mention_stats")
    n_stats = 0
    per_vol_mentions = defaultdict(lambda: defaultdict(int))
    quoted = {(c, v) for c, v in db.execute(
        "SELECT DISTINCT char_id, vol_id FROM quotes "
        "WHERE char_id IS NOT NULL")}
    alias_char = defaultdict(set)
    for f, c in db.execute(
            "SELECT DISTINCT raw_form, char_id FROM aliases "
            "WHERE is_noise=0"):
        alias_char[canon(f)].add(c)

    for vol, stem in db.execute(
            "SELECT vol_id, file_stem FROM volumes ORDER BY chrono_order"):
        text = canon(open(f"text/{stem}.txt", encoding="utf-8").read())
        for f, comp in comps:
            n = len(comp.findall(text))
            if n:
                db.execute(
                    "INSERT INTO mention_stats (vol_id, token, count) "
                    "VALUES (?,?,?)", (vol, f, n))
                n_stats += 1
                for cid in alias_char[f]:
                    per_vol_mentions[cid][vol] += n

    db.execute("DELETE FROM coverage")
    n_cov = 0
    for cid, vols in per_vol_mentions.items():
        for vol, cnt in vols.items():
            if cnt <= 0:
                continue
            status = "quotes" if (cid, vol) in quoted else "occurrences"
            db.execute(
                "INSERT INTO coverage (char_id, vol_id, status) "
                "VALUES (?,?,?)", (cid, vol, status))
            n_cov += 1

    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) "
        "VALUES ('mention_build', datetime('now'), datetime('now'), ?)",
        (f"stats={n_stats} coverage={n_cov}",))
    db.commit()
    print(f"mention_stats rows: {n_stats}  coverage rows: {n_cov}")
    print("coverage by status:",
          dict(db.execute("SELECT status, COUNT(*) FROM coverage "
                          "GROUP BY status")))
    db.close()


if __name__ == "__main__":
    main()

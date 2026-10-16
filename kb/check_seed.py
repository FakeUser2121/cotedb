#!/usr/bin/env python3
"""Verify external seed list against corpus + our extractor coverage.

For each seed entry: count surname / given-name occurrences across corpus,
check if normalized surname appears in roster_candidates (extractor found it).
Outputs TSV report + writes summary counts.
"""
import os
import re
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_mine import normalize, fold  # shared merge key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT = os.path.join(ROOT, "text")
SEED = os.path.join(ROOT, "kb", "external_seed_wattpad.txt")
DB = os.path.join(ROOT, "cote_kb.db")


def count_word(corpus, word):
    return len(re.findall(rf"\b{re.escape(word)}\b", corpus))


def main():
    # load corpus once
    corpus = {}
    total = ""
    for fn in sorted(os.listdir(TXT)):
        if fn.endswith(".txt"):
            t = open(os.path.join(TXT, fn), encoding="utf-8").read()
            corpus[fn[:-4]] = t
            total += fold(t) + "\n"

    db = sqlite3.connect(DB)
    found_norms = {r[0] for r in db.execute(
        "SELECT normalized FROM roster_candidates")}

    # corpus-side extraction of full names for cross-ref:
    # any two adjacent capitalized name tokens (rough)
    # (kept simple: seed only needs surname/given counts + candidate coverage)

    rows = []
    with open(SEED, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#") or "\t" not in line:
                continue
            parts = line.split("\t")
            name = parts[-1].strip()
            if not name or name.startswith("("):
                continue
            # parse "Family, Given" or surname-only
            if "," in name:
                fam, giv = [p.strip() for p in name.split(",", 1)]
            else:
                fam, giv = name.strip(), ""
            fam_fold = fold(fam)
            giv_fold = fold(giv) if giv else ""
            fam_norm = normalize(fam)
            fam_count = count_word(total, fam_fold)
            giv_count = count_word(total, giv_fold) if giv_fold else -1
            in_candidates = fam_norm in found_norms
            rows.append((fam, giv, fam_count, giv_count, int(in_candidates), name))

    print(f"{'SURNAME':20s} {'GIVEN':14s} {'fam#':>5s} {'giv#':>5s} {'cand':>4s}")
    miss = []
    cov_ok = 0
    for fam, giv, fc, gc, cand, name in rows:
        flag = "OK" if cand else "MISS"
        if fc == 0:
            flag = "ABSENT"
        if not cand and fc > 0:
            miss.append((fam, giv, fc))
        if cand:
            cov_ok += 1
        print(f"{fam:20.20s} {giv:14.14s} {fc:5d} {gc:5d} {flag:>6s}")

    found = sum(1 for r in rows if r[2] > 0)
    print(f"\nSeed entries: {len(rows)}  present-in-corpus: {found}  "
          f"absent: {len(rows)-found}")
    print(f"Extractor-candidate coverage of present surnames: {cov_ok}/{found}")
    if miss:
        print(f"\nIN CORPUS BUT MISSED BY EXTRACTORS ({len(miss)}):")
        for fam, giv, fc in miss:
            print(f"  {fam} {giv} (surname {fc} hits)")


if __name__ == "__main__":
    main()

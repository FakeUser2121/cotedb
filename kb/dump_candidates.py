#!/usr/bin/env python3
"""Dump roster candidates for review in frequency bands.

Usage: python3 kb/dump_candidates.py [band]   band: high(>=100) mid(10-99) low(<10) all
Prints: normalized | count | signals | up to 2 short contexts
"""
import json
import sqlite3
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "cote_kb.db")


def main():
    band = sys.argv[1] if len(sys.argv) > 1 else "high"
    if band == "high":
        where = "total_count >= 100"
    elif band == "mid":
        where = "total_count >= 10 AND total_count < 100"
    elif band == "low":
        where = "total_count < 10"
    else:
        where = "1=1"
    db = sqlite3.connect(DB)
    rows = db.execute(
        f"SELECT normalized, raw_form, total_count, signals, sample_contexts "
        f"FROM roster_candidates WHERE {where} ORDER BY total_count DESC"
    ).fetchall()
    for norm, raw, cnt, sigs, ctxs in rows:
        ctx_list = json.loads(ctxs)
        c1 = ctx_list[0]["snippet"][:110] if ctx_list else ""
        c2 = ctx_list[1]["snippet"][:110] if len(ctx_list) > 1 else ""
        print(f"{norm}\t{cnt}\t{sigs}\t{c1}\t{c2}")
    print(f"# {len(rows)} candidates in band {band}", file=sys.stderr)


if __name__ == "__main__":
    main()

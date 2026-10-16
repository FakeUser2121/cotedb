#!/usr/bin/env python3
"""Search the COTE corpus (text/ + search.db FTS5).

Usage:
  python3 search.py "exact phrase"
  python3 search.py "keyword" --volume Y2
  python3 search.py "Ayanokouji" --volume "Y2 V3" -n 50
"""
import argparse
import sqlite3
import sys


def main():
    ap = argparse.ArgumentParser(description="Full-text search across COTE volumes")
    ap.add_argument("query", help="FTS5 query (quote for exact phrase)")
    ap.add_argument("--volume", help="restrict to volumes matching substring, e.g. Y1 or 'Y2 V3'")
    ap.add_argument("-n", "--max-hits", type=int, default=30, help="max pages to show (default 30)")
    args = ap.parse_args()

    try:
        db = sqlite3.connect("file:search.db?mode=ro", uri=True)
    except sqlite3.Error as e:
        sys.exit(f"Cannot open search.db: {e}\nRun ./rebuild_index.sh first.")

    sql = (
        "SELECT volume, page, bm25(pages) AS rank, "
        "snippet(pages, 2, '[', ']', '...', 16) AS snip "
        "FROM pages WHERE pages MATCH ?"
    )
    params = [args.query]
    if args.volume:
        sql += " AND volume LIKE ?"
        params.append(f"%{args.volume}%")
    sql += " ORDER BY rank LIMIT ?"
    params.append(args.max_hits)

    try:
        rows = db.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        sys.exit(f"Bad query: {e}")

    if not rows:
        print("No hits.")
        return

    for vol, page, _rank, snip in rows:
        snip_one = " ".join(snip.split())
        print(f"{vol}  p.{page}: {snip_one}")
    print(f"\n{len(rows)} page hit(s)", end="")
    if len(rows) == args.max_hits:
        print(f" (limited to {args.max_hits}; raise with -n)", end="")
    print()


if __name__ == "__main__":
    main()

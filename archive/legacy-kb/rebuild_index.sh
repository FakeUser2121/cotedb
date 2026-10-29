#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p text

echo "Extracting PDFs -> text/ ..."
for f in gdrive_download/*.pdf; do
  base=$(basename "$f" .pdf)
  tmp=$(mktemp --suffix=.txt)
  pdftotext -enc UTF-8 "$f" "$tmp"
  python3 - "$tmp" "text/$base.txt" <<'PY'
import sys
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
pages = raw.split("\f")
out = []
for i, p in enumerate(pages, 1):
    if i == len(pages) and not p.strip():
        break  # trailing form feed after last page
    out.append(f"--- page {i} ---\n{p.rstrip()}\n")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out))
PY
  rm -f "$tmp"
done

echo "Building search.db (FTS5, one row per page) ..."
python3 - <<'PY'
import glob
import os
import sqlite3

if os.path.exists("search.db"):
    os.remove("search.db")

db = sqlite3.connect("search.db")
db.execute(
    "CREATE VIRTUAL TABLE pages USING fts5("
    "volume UNINDEXED, page UNINDEXED, text, tokenize='unicode61')"
)

def ingest(path):
    volume = os.path.splitext(os.path.basename(path))[0]
    page = None
    buf = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            s = line.rstrip("\n")
            if s.startswith("--- page ") and s.endswith(" ---"):
                if page is not None:
                    db.execute(
                        "INSERT INTO pages VALUES (?,?,?)",
                        (volume, page, "\n".join(buf).strip()),
                    )
                page = int(s.split()[2])
                buf = []
            else:
                buf.append(s)
        if page is not None:
            db.execute(
                "INSERT INTO pages VALUES (?,?,?)",
                (volume, page, "\n".join(buf).strip()),
            )

for path in sorted(glob.glob("text/*.txt")):
    ingest(path)
db.commit()

n, v = db.execute("SELECT COUNT(*), COUNT(DISTINCT volume) FROM pages").fetchone()
print(f"Indexed {n} pages from {v} volumes")
db.close()
PY
echo "Done."

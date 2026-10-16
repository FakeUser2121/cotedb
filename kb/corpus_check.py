#!/usr/bin/env python3
"""P0 corpus validation: PDFs vs text/, page markers, integrity, registry."""
import glob
import os
import re
import sqlite3
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(ROOT, "gdrive_download")
TXT_DIR = os.path.join(ROOT, "text")
DB_PATH = os.path.join(ROOT, "cote_kb.db")

# Chronological order (canonical COTE reading order)
VOLUMES = [
    ("y0",      "COTE V0",      0.0,   "side"),
    ("y1v1",    "COTE Y1 V1",   1.0,   "main"),
    ("y1v2",    "COTE Y1 V2",   2.0,   "main"),
    ("y1v3",    "COTE Y1 V3",   3.0,   "main"),
    ("y1v4",    "COTE Y1 V4",   4.0,   "main"),
    ("y1v4.5",  "COTE Y1 V4.5", 4.5,   "interquad"),
    ("y1v5",    "COTE Y1 V5",   5.0,   "main"),
    ("y1v6",    "COTE Y1 V6",   6.0,   "main"),
    ("y1v7",    "COTE Y1 V7",   7.0,   "main"),
    ("y1v7.5",  "COTE Y1 V7.5", 7.5,   "interquad"),
    ("y1v8",    "COTE Y1 V8",   8.0,   "main"),
    ("y1v9",    "COTE Y1 V9",   9.0,   "main"),
    ("y1v10",   "COTE Y1 V10",  10.0,  "main"),
    ("y1v11",   "COTE Y1 V11",  11.0,  "main"),
    ("y1v11.5", "COTE Y1 V11.5", 11.5, "interquad"),
    ("y1v11.75","COTE Y1 V11.75", 11.75, "side"),
    ("y2v1",    "COTE Y2 V1",   12.0,  "main"),
    ("y2v2",    "COTE Y2 V2",   13.0,  "main"),
    ("y2v3",    "COTE Y2 V3",   14.0,  "main"),
    ("y2v4",    "COTE Y2 V4",   15.0,  "main"),
    ("y2v4.5",  "COTE Y2 V4.5", 15.5,  "interquad"),
    ("y2v5",    "COTE Y2 V5",   16.0,  "main"),
    ("y2v6",    "COTE Y2 V6",   17.0,  "main"),
    ("y2v7",    "COTE Y2 V7",   18.0,  "main"),
    ("y2v8",    "COTE Y2 V8",   19.0,  "main"),
    ("y2v9",    "COTE Y2 V9",   20.0,  "main"),
    ("y2v9.5",  "COTE Y2 V9.5", 20.5,  "interquad"),
    ("y2v9.75", "COTE Y2 V9.75", 20.75, "side"),
    ("y2v10",   "COTE Y2 V10",  21.0,  "main"),
    ("y2v10.25","COTE Y2 V10.25", 21.25, "side"),
    ("y2v11",   "COTE Y2 V11",  22.0,  "main"),
    ("y2v12",   "COTE Y2 V12",  23.0,  "main"),
    ("y2v12.5", "COTE Y2 V12.5", 23.5, "interquad"),
    ("y3v1",    "COTE Y3 V1",   24.0,  "main"),
]

PAGE_RE = re.compile(r"^--- page (\d+) ---$", re.M)


def pdf_pages(stem):
    pdf = os.path.join(PDF_DIR, stem + ".pdf")
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else None


def main():
    problems = []
    rows = []
    pdfs = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(PDF_DIR, "*.pdf"))}
    txts = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(TXT_DIR, "*.txt"))}
    registered = {stem for _, stem, _, _ in VOLUMES}

    for extra in sorted(pdfs - registered):
        problems.append(f"PDF not in registry: {extra}")
    for extra in sorted(txts - registered):
        problems.append(f"TXT not in registry: {extra}")
    for missing in sorted(registered - pdfs):
        problems.append(f"Registry PDF missing: {missing}")
    for missing in sorted(registered - txts):
        problems.append(f"Registry TXT missing: {missing}")

    for vol_id, stem, order, kind in VOLUMES:
        pdf_path = os.path.join(PDF_DIR, stem + ".pdf")
        txt_path = os.path.join(TXT_DIR, stem + ".txt")
        if not (os.path.exists(pdf_path) and os.path.exists(txt_path)):
            continue
        n_pdf = pdf_pages(stem)
        text = open(txt_path, encoding="utf-8").read()
        pages = [int(m) for m in PAGE_RE.findall(text)]
        n_txt = len(pages)
        seq_ok = pages == list(range(1, n_txt + 1))
        chars = len(text)
        empty_pages = 0
        # count near-empty pages
        parts = PAGE_RE.split(text)  # odd indices are page numbers
        # simpler: iterate markers
        marks = list(PAGE_RE.finditer(text))
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            body = text[m.end():end].strip()
            if len(body) < 20:
                empty_pages += 1
        ok = (n_pdf == n_txt) and seq_ok
        if not ok:
            problems.append(f"{stem}: pdf_pages={n_pdf} txt_pages={n_txt} seq_ok={seq_ok}")
        # near-empty pages are expected (illustration/cover pages in LN PDFs) — informational only
        rows.append((vol_id, stem, order, kind, n_pdf, n_txt, chars, empty_pages, int(ok)))
        print(f"{vol_id:10s} pdf={n_pdf:4d} txt={n_txt:4d} seq={'ok' if seq_ok else 'BAD':3s} "
              f"chars={chars:8d} empty_pages={empty_pages:3d} {'OK' if ok else 'FAIL'}")

    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS volumes (
            vol_id TEXT PRIMARY KEY, title TEXT, file_stem TEXT,
            chrono_order REAL, kind TEXT, pdf_pages INTEGER, txt_pages INTEGER,
            chars INTEGER, empty_pages INTEGER, validated INTEGER
        );
        CREATE TABLE IF NOT EXISTS provenance (
            run_id INTEGER PRIMARY KEY, method TEXT, started TEXT, finished TEXT, notes TEXT
        );
    """)
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for vol_id, stem, order, kind, n_pdf, n_txt, chars, empty, ok in rows:
        db.execute(
            "INSERT OR REPLACE INTO volumes VALUES (?,?,?,?,?,?,?,?,?,?)",
            (vol_id, stem, stem, order, kind, n_pdf, n_txt, chars, empty, ok),
        )
    db.execute(
        "INSERT INTO provenance (method, started, finished, notes) VALUES (?,?,?,?)",
        ("corpus_validation", now, now,
         f"{len(rows)} volumes checked, {len(problems)} problems"),
    )
    db.commit()
    db.close()

    print()
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print(f"All {len(rows)} volumes validated. Registry + provenance written to {DB_PATH}")


if __name__ == "__main__":
    main()

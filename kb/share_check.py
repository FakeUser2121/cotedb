#!/usr/bin/env python3
"""P7 gate: share output consistency (read-only).

python3 kb/share_check.py [--site] [--print] [--pdf]

Checks (site):
  every href/src in share/site/**.html resolves to an existing file
  every #fragment resolves to an id/name in the target page
  search-index.js: every record URL + anchor resolves (and no record
  points at a missing page); index parses as JSON
  expected inventory: 82 dossiers + home = 83 pages, 6 print docs
Checks (print):
  every href/src in share/print/**.html resolves (assets + ../site/)
Checks (pdf):
  share/pdfs/*.pdf exist, open with pdfinfo, >= 1 page each

Exit 0 when everything asked for passes; non-zero otherwise.
"""

import argparse
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_share_site import md5_tree  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "share" / "site"
PRINT = ROOT / "share" / "print"
PDFS = SITE / "pdfs"
DOCS = ROOT / "docs"
HREF_RE = re.compile(r'(?:href|src)="([^"]+)"')
EXPECTED_PRINT = 6
EXPECTED_PDFS = ["guides", "people", "school", "story", "topics", "world"]


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "a" and d.get("name"):
            self.ids.add(d["name"])


def collect_ids(path, cache):
    if path not in cache:
        g = IdCollector()
        g.feed(path.read_text(encoding="utf-8"))
        cache[path] = g.ids
    return cache[path]


def check_links(files, base_errors):
    errors = list(base_errors)
    cache = {}
    checked = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        for u in HREF_RE.findall(text):
            if u.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            checked += 1
            path, _, frag = u.partition("#")
            if path:
                tgt = (f.parent / path).resolve()
                if not tgt.exists():
                    errors.append(f"{f}: missing target {u}")
                    continue
            else:
                tgt = f
            if frag and tgt.suffix == ".html":
                if frag not in collect_ids(tgt, cache):
                    errors.append(f"{f}: missing anchor {u}")
    return errors, checked


def check_search_index():
    errors = []
    idx = SITE / "assets" / "search-index.js"
    raw = idx.read_text(encoding="utf-8")
    if not raw.startswith("const SEARCH_INDEX = "):
        return ["search-index.js: missing const wrapper"]
    try:
        records = json.loads(raw[len("const SEARCH_INDEX = "):].rstrip().rstrip(";"))
    except json.JSONDecodeError as e:
        return [f"search-index.js: invalid JSON ({e})"]
    if not records:
        errors.append("search-index.js: empty index")
    cache = {}
    for r in records:
        for key in ("u", "t", "s", "x"):
            if key not in r:
                errors.append(f"record missing {key}: {r}")
                break
        else:
            path, _, frag = r["u"].partition("#")
            tgt = (SITE / path).resolve()
            if not tgt.exists():
                errors.append(f"index target missing: {r['u']}")
            elif frag and frag not in collect_ids(tgt, cache):
                errors.append(f"index anchor missing: {r['u']}")
    return errors


def check_inventory():
    """Architecture invariants instead of a frozen page count: every section
    in the spec is published, every volume in the database has a place on the
    Story spine, every named principal/recurring character has a page, and
    nothing is an orphan. Page count is reported, never asserted."""
    import posixpath
    from collections import deque
    import site_arch

    errors = []
    have = {f.relative_to(SITE).as_posix() for f in SITE.rglob("*.html")}

    for s in site_arch.SECTIONS:
        if s["href"] not in have:
            errors.append(f"section hub missing: {s['href']}")

    con = site_arch.open_db()
    vols = [r[0] for r in con.execute(
        "SELECT vol_id FROM volumes ORDER BY chrono_order")]
    principals = list(con.execute(
        "SELECT char_id, canonical_name FROM characters WHERE tier <= 2 "
        "ORDER BY tier, canonical_name"))
    con.close()
    for v in vols:
        want = f"story/v/{v}/index.html"
        if want not in have:
            errors.append(f"volume missing from the Story spine: {want}")
    for char_id, name in principals:
        want = f"people/{char_id}.html"
        if want not in have:
            errors.append(f"principal character page missing: {want} ({name})")

    # reachability: BFS over internal links from the home page
    text_cache = {}
    seen = {"index.html"}
    depth = {"index.html": 0}
    q = deque(["index.html"])
    while q:
        rel = q.popleft()
        if rel not in text_cache:
            text_cache[rel] = (SITE / rel).read_text(encoding="utf-8")
        for u in HREF_RE.findall(text_cache[rel]):
            if not u.startswith(("#", "http", "mailto:", "data:")):
                path = u.partition("#")[0]
                if path.endswith(".html") and not path.startswith("/"):
                    key = posixpath.normpath(posixpath.join(
                        posixpath.dirname(rel), path))
                    if key in have and key not in seen:
                        seen.add(key)
                        depth[key] = depth[rel] + 1
                        q.append(key)
    orphans = sorted(have - seen)
    for o in orphans:
        errors.append(f"orphan page (unreachable from Home): {o}")
    deep = sorted(d for d in depth.values() if d > 3)
    if deep:
        errors.append(f"{len(deep)} pages are more than 3 clicks from Home")
    notes = [f"inventory: {len(have)} pages, {len(seen)} reachable, "
             f"max depth {max(depth.values())}, {len(vols)} volumes, "
             f"{len(principals)} principal characters"]
    return errors, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", action="store_true")
    ap.add_argument("--print", dest="prn", action="store_true")
    ap.add_argument("--pdf", action="store_true")
    args = ap.parse_args()
    run_all = not (args.site or args.prn or args.pdf)
    errors = []
    notes = []

    if args.site or run_all:
        site_files = sorted(SITE.rglob("*.html"))
        inv_errs, inv_notes = check_inventory()
        errors.extend(inv_errs)
        notes.extend(inv_notes)
        errs, checked = check_links(site_files, [])
        errors.extend(errs)
        notes.append(f"site: {len(site_files)} pages, {checked} links checked, "
                     f"{len(errs)} bad")
        idx_errs = check_search_index()
        errors.extend(idx_errs)
        n_idx = len(json.loads(
            (SITE / "assets" / "search-index.js").read_text(encoding="utf-8")
            [len("const SEARCH_INDEX = "):].rstrip().rstrip(";")))
        notes.append(f"search index: {n_idx} records, {len(idx_errs)} bad")
        for f in ("style.css", "search.js", "search-index.js", "README.txt"):
            if not (SITE / "assets" / f if f.endswith((".css", ".js"))
                    else SITE / f).exists():
                errors.append(f"missing asset: {f}")
        if DOCS.exists():
            if md5_tree(DOCS) != md5_tree(SITE):
                errors.append("docs/ out of sync with share/site "
                              "(run build_share_site.py --docs)")
            else:
                notes.append("docs/: in sync with share/site")

    if args.prn or run_all:
        print_files = sorted(PRINT.glob("*.html"))
        if len(print_files) != EXPECTED_PRINT:
            errors.append(f"print docs: {len(print_files)} != {EXPECTED_PRINT}")
        errs, checked = check_links(print_files, [])
        errors.extend(errs)
        notes.append(f"print: {len(print_files)} docs, {checked} links checked, "
                     f"{len(errs)} bad")

    if args.pdf or run_all:
        for name in EXPECTED_PDFS:
            pdf = PDFS / f"{name}.pdf"
            if not pdf.exists():
                errors.append(f"missing pdf: {name}.pdf")
                continue
            try:
                out = subprocess.run(
                    ["pdfinfo", str(pdf)], capture_output=True, text=True,
                    check=True).stdout
                m = re.search(r"^Pages:\s+(\d+)", out, re.M)
                pages = int(m.group(1)) if m else 0
                if pages < 1:
                    errors.append(f"{name}.pdf: no pages")
                notes.append(f"{name}.pdf: {pages} pages, "
                             f"{pdf.stat().st_size // 1024} KB")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                errors.append(f"{name}.pdf: unreadable ({e})")

    for n in notes:
        print(f"  {n}")
    if errors:
        print(f"\nFAIL — {len(errors)} problem(s):")
        for e in errors[:30]:
            print(f"  - {e}")
        if len(errors) > 30:
            print(f"  … and {len(errors) - 30} more")
        return 1
    print("\nshare_check: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

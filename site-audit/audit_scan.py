#!/usr/bin/env python3
"""Read-only map of the built COTE site.

Parses every HTML file under share/site, extracts page facts and every link
with its region, then walks the link graph from index.html the way a crawler
would (resolving relative hrefs against the file tree, following anchors).

Nothing is written into the site tree; output goes to site-audit/.
"""
import csv
import html
import json
import posixpath
import re
import sys
from collections import defaultdict, deque
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path("/home/user3/Documents/unsafe/cote")
SITE = ROOT / "share" / "site"
OUT = ROOT / "site-audit"

VOL_CHIP_RE = re.compile(r"Vol\.\s*\d+[A-Za-z0-9.]*\s*p\.\d+")
CITE_RE = re.compile(r"\bVol\.?\s*\d+(?:\.\d+)?\s+pp?\.[\d\u2013,\-\s]+")
PAGE_CITE_RE = re.compile(r"\bp{1,2}\.\s?\d+(?:[\u2013\-]\d+)?")

VOID = {"br", "img", "input", "meta", "link", "hr", "source", "area",
        "base", "col", "embed", "param", "track", "wbr", "path", "circle",
        "rect", "line", "polyline", "polygon", "use", "stop"}


class PageParser(HTMLParser):
    """Collects text, headings, and links tagged with their region.

    Region comes from the nearest enclosing landmark: the masthead/tab bar,
    the left rail, the right rail, the breadcrumb, the footer, the body, or
    an inline cross-reference block.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = []
        self.headings = []          # (level, id, text)
        self.sections = []          # body data-section
        self.root = ""              # body data-root
        self.links = []             # (href, text, region)
        self.ids = set()
        self.anchors = set()        # hrefs starting with #
        self._stack = []            # region tags currently open
        self._in_title = False
        self._link_href = None
        self._link_text = []
        self._link_region = None
        self._heading = None        # (level, id) while capturing text
        self._heading_text = []
        self._skip = 0              # inside script/style/svg
        self.words = 0
        self.paris = 0              # <p> outside the rails
        self.quotes = 0             # quoted transcript rows
        self.lists = 0
        self.tables = 0
        self.tables_rows = 0
        self.scenes = 0
        self.ledger_rows = 0
        self.details = 0
        self.external = []

    def _region(self):
        for tag, cls, ident in reversed(self._stack):
            if tag == "header" or "masthead" in cls:
                return "masthead"
            if "tabs" in cls:
                return "tab bar"
            if "rail left" in cls or ident == "rail-nav":
                return "left rail"
            if "rail right" in cls:
                return "right rail"
            if "crumbs" in cls:
                return "breadcrumb"
            if tag == "footer" or "site-footer" in cls:
                return "footer"
            if "related" in cls or "recall" in cls:
                return "cross-reference"
            if tag == "main" or "content" in cls or "measure" in cls:
                return "body"
        return "body"

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "")
        ident = (a.get("id") or "")
        if ident:
            self.ids.add(ident)
        if tag in ("script", "style", "svg"):
            self._skip += 1
        if tag not in VOID:
            self._stack.append((tag, cls, ident))
        if tag == "body":
            self.sections.append(a.get("data-section", ""))
            self.root = a.get("data-root", "")
        if tag == "title":
            self._in_title = True
        if tag in ("h1", "h2", "h3", "h4") and self._skip == 0:
            self._heading = (int(tag[1]), ident)
            self._heading_text = []
        if tag == "a" and self._skip == 0:
            self._link_href = a.get("href", "")
            self._link_text = []
            self._link_region = self._region()
        if tag == "p":
            self.paris += 1
        if tag == "li":
            self.lists += 1
            if "e-quote" in cls or "quote" in cls:
                self.quotes += 1
        if tag == "table":
            self.tables += 1
        if tag == "tr":
            self.tables_rows += 1
        if "scene ev" in cls or cls.strip() == "scene":
            self.scenes += 1
        if cls.strip().startswith("e-"):
            self.ledger_rows += 1
        if tag == "details":
            self.details += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg"):
            self._skip = max(0, self._skip - 1)
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                break
        if tag == "title":
            self._in_title = False
        if tag in ("h1", "h2", "h3", "h4") and self._heading:
            level, ident = self._heading
            text = re.sub(r"\s+", " ", "".join(self._heading_text)).strip()
            if level == 1:
                self.h1.append(text)
            elif text:
                self.headings.append((level, ident, text))
            self._heading = None
        if tag == "a" and self._link_href is not None:
            text = re.sub(r"\s+", " ", "".join(self._link_text)).strip()
            href = html.unescape(self._link_href)
            self.links.append((href, text, self._link_region or "body"))
            self._link_href = None

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_title:
            self.title += data
        if self._link_href is not None:
            self._link_text.append(data)
        if self._heading is not None:
            self._heading_text.append(data)
        self.words += len(data.split())


def analyse(path):
    p = PageParser()
    raw = path.read_text(encoding="utf-8")
    p.feed(raw)
    rel = path.relative_to(SITE).as_posix()
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html.unescape(body)
    cites = VOL_CHIP_RE.findall(body) + CITE_RE.findall(body)
    # every page anchor the reader can see, whether or not a volume word sits
    # in front of it: the scene rows print "p.37–38", the role lines print
    # "Vol. 1 p.137–140", and both are citations of a printed page.
    pagedots = re.findall(r"\bp\.\s?\d+(?:[\u2013\-,]\s?\d+)*", body)
    markers = {
        "transcribed": "Transcribed line by line" in body,
        "unread": ("has not been read" in body or "not yet worked through" in body),
        "gap": "not read line by line yet" in body,
        "role_gap": "Role not stated" in body or "not stated on the pages" in body,
    }
    return {
        "path": rel,
        "title": re.sub(r"\s+", " ", p.title).strip(),
        "h1": " | ".join(p.h1),
        "section": p.sections[0] if p.sections else "",
        "root": p.root,
        "words": len(body.split()),
        "headings": p.headings,
        "ids": sorted(p.ids),
        "links": p.links,
        "paris": p.paris,
        "list_items": p.lists,
        "quote_rows": p.quotes,
        "ledger_rows": p.ledger_rows,
        "scenes": p.scenes,
        "details": p.details,
        "tables": p.tables,
        "table_rows": p.tables_rows,
        "markers": markers,
        "n_external": len([1 for h, _t, _r in p.links
                           if h.startswith(("http", "mailto:"))]),
        "cite_count": len(set(cites)),
        "page_refs": len(pagedots),
        "pageref_spans": len(re.findall(r'<span class="pageref">', raw)),
        "cite_total": len(cites),
        "vols": sorted(set(re.findall(r"Vol\.\s*(\d+)", " ".join(cites)))),
        "raw": raw,
    }


def norm(href, cur):
    """Resolve a site-relative href against the current page path."""
    if href.startswith(("http://", "https://", "mailto:", "data:", "javascript:")):
        return None
    path_part, _, frag = href.partition("#")
    if not path_part:
        return (cur, frag)
    if path_part.startswith("/"):
        resolved = posixpath.normpath(path_part.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(cur), path_part))
    return (resolved, frag)


def main():
    OUT.mkdir(exist_ok=True)
    files = sorted(p for p in SITE.rglob("*.html"))
    pages = {}
    for f in files:
        rec = analyse(f)
        pages[rec["path"]] = rec
    # BFS from index.html, exactly as a crawler would
    seen, depth, parents = set(), {}, defaultdict(list)
    start = "index.html"
    q = deque([start])
    seen.add(start)
    depth[start] = 0
    edges = []
    while q:
        cur = q.popleft()
        pg = pages.get(cur)
        if not pg:
            continue
        for href, text, region in pg["links"]:
            if href.startswith("#"):
                edges.append({"from": cur, "to": cur, "anchor": href[1:],
                              "text": text, "region": region})
                continue
            if href.startswith(("http", "mailto:", "data:", "javascript:")):
                edges.append({"from": cur, "to": href, "anchor": "",
                              "text": text, "region": region, "external": True})
                continue
            r = norm(href, cur)
            if not r:
                continue
            target, frag = r
            edges.append({"from": cur, "to": target, "anchor": frag,
                          "text": text, "region": region})
            if target in pages and target not in seen and not target.endswith(".pdf"):
                seen.add(target)
                depth[target] = depth[cur] + 1
                parents[target].append(cur)
                q.append(target)
            elif target.endswith(".pdf"):
                seen.add(target)
                depth[target] = depth[cur] + 1

    # reachability / broken checks against the real file list
    missing, broken_anchor = [], []
    incoming = defaultdict(int)
    for e in edges:
        if e.get("external"):
            continue
        t = e["to"]
        if t not in pages:
            if not (SITE / t).exists():
                missing.append(e)
            continue
        if e["anchor"] and t in pages:
            if e["anchor"] not in set(pages[t]["ids"]):
                broken_anchor.append(e)
    # count all internal edges in (excluding a page linking to itself)
    for e in edges:
        if not e.get("external") and e["to"] in pages and e["from"] != e["to"]:
            incoming[e["to"]] += 1

    unreachable = sorted(set(pages) - seen)
    orphans = sorted(p for p in pages
                     if incoming.get(p, 0) == 0 and p != start)
    dead_ends = sorted(p for p in seen
                       if not [e for e in edges if e["from"] == p
                               and not e["to"].startswith("http")])

    # duplicate ids inside a page break anchors
    dup_ids = []
    for path, pg in pages.items():
        ids = re.findall(r'\sid="([^"]+)"', pg["raw"])
        counts = {i: c for i, c in {x: ids.count(x) for x in set(ids)}.items() if c > 1}
        if counts:
            dup_ids.append({"path": path, "dups": counts})

    json.dump({
        "pages": {k: {kk: vv for kk, vv in v.items() if kk != "raw"}
                  for k, v in pages.items()},
        "reachable": sorted(seen),
        "depth": depth,
        "incoming": dict(incoming),
        "orphans": orphans,
        "unreachable": unreachable,
        "dead_ends": dead_ends,
        "missing": missing,
        "broken_anchor": broken_anchor,
        "dup_ids": dup_ids,
    }, open(OUT / "scan.json", "w"), ensure_ascii=False, indent=1)

    print(f"html pages: {len(pages)}   reachable from index.html: {len(seen)}")
    print(f"internal link edges: {len([e for e in edges if not e.get('external')])}")
    print(f"external: {len([e for e in edges if e.get('external')])}")
    print(f"missing targets: {len(missing)}   broken anchors: {len(broken_anchor)}")
    print(f"orphans (no incoming): {len(orphans)}   unreachable: {len(unreachable)}")
    print(f"pages with duplicate ids: {len(dup_ids)}")


if __name__ == "__main__":
    main()

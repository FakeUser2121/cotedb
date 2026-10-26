#!/usr/bin/env python3
"""P7: build the multi-page share site from dossiers/ (generated,
idempotent, no timestamps).

python3 kb/build_share_site.py

Outputs share/site/:
  index.html                    home (stats + section cards)
  background.html               background characters (single page)
  main/*.html  mid/*/*.html     character profiles (section-preserving)
  world/*.html  exams/*.html    location + exam profiles
  systems/*.html                system profiles
  vol1/*.html                   Year 1, Volume 1 — guides + transcripts
  assets/style.css              one stylesheet (tier/type colour coding)
  assets/search-index.js        SEARCH_INDEX as a JS constant (file:// safe)
  assets/search.js              client-side search UI
  README.txt                    what this folder is

Plus share/print/*.html — per-category print documents (cover + TOC +
page-broken entities) consumed by chromium for the PDFs.

Navigation comes from the authored dossiers/*/index.md link order; pages
keep their section-relative layout so in-page (#anchors) and sibling links
keep working. Every page: topbar search, sidebar nav (details/summary,
current section open), right TOC, footer. Deterministic — two builds must
be md5-identical (verified by --md5).
"""

import argparse
import hashlib
import html
import json
import posixpath
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH  # noqa: E402
from share_render import render, rewrite_links, slug  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOSSIERS = ROOT / "dossiers"
SITE = ROOT / "share" / "site"
PRINT = ROOT / "share" / "print"

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")

VOL1_SRC = ROOT / "drafts" / "people"
VOL1_FILES = [
    ("ayanokouji-kiyotaka.article", "Ayanokōji Kiyotaka — guide"),
    ("ayanokouji-kiyotaka.y1v1.transcript",
     "Ayanokōji Kiyotaka — transcript"),
    ("horikita-suzune.article", "Horikita Suzune — guide"),
    ("horikita-suzune.y1v1.transcript", "Horikita Suzune — transcript"),
    ("kushida-kikyou.article", "Kushida Kikyō — guide"),
    ("kushida-kikyou.y1v1.transcript", "Kushida Kikyō — transcript"),
]

CSS = """/* COTE knowledge base — one stylesheet, all pages */
:root {
  --ink: #1c2333; --muted: #5b6478; --line: #e3e6ee; --bg: #f7f8fb;
  --card: #ffffff; --brand: #2b3a67; --accent: #3b5bdb;
  --main: #b45309; --mid: #6d28d9; --bg-char: #64748b;
  --world: #0f766e; --exams: #be123c; --systems: #1d4ed8;
  --vol: #4338ca;
  --authority: #b91c1c; --rivals: #c2410c; --allies: #15803d;
  --peers: #1d4ed8; --family: #7e22ce; --outside: #0f766e;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0; color: var(--ink); background: var(--bg);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, sans-serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code { font: 0.9em/1.4 var(--mono); background: #eef0f6; padding: 0.1em 0.35em;
  border-radius: 4px; }
strong { font-weight: 650; }
mark { background: #fde68a; padding: 0 0.1em; }

.topbar {
  position: sticky; top: 0; z-index: 30; display: flex; gap: 16px;
  align-items: center; padding: 10px 18px; background: var(--brand);
  color: #fff; box-shadow: 0 1px 6px rgba(10,20,50,.25);
}
.topbar .brand { color: #fff; font-weight: 700; letter-spacing: .02em;
  font-size: 15px; white-space: nowrap; }
.topbar .brand:hover { text-decoration: none; opacity: .85; }
.searchwrap { position: relative; flex: 1; max-width: 520px; }
#q {
  width: 100%; padding: 7px 12px; border: 1px solid rgba(255,255,255,.35);
  border-radius: 8px; background: rgba(255,255,255,.14); color: #fff;
  font-size: 14px; outline: none;
}
#q::placeholder { color: rgba(255,255,255,.7); }
#q:focus { background: #fff; color: var(--ink); }
#q:focus::placeholder { color: #99a; }
#results {
  position: absolute; top: 42px; left: 0; right: 0; background: #fff;
  color: var(--ink); border: 1px solid var(--line); border-radius: 10px;
  box-shadow: 0 14px 40px rgba(10,20,50,.28); overflow: hidden;
  max-height: 70vh; overflow-y: auto;
}
#results a {
  display: block; padding: 9px 14px; border-bottom: 1px solid var(--line);
  color: var(--ink);
}
#results a:last-child { border-bottom: 0; }
#results a:hover, #results a.sel { background: #eef2ff; text-decoration: none; }
#results .rt { font-weight: 650; font-size: 14px; }
#results .rs { color: var(--muted); font-size: 12.5px; }
#results .rx { font-size: 12.5px; color: #444c60; margin-top: 2px; }
#results .none { padding: 10px 14px; color: var(--muted); font-size: 14px; }

.layout { display: grid; grid-template-columns: 250px minmax(0,1fr) 220px;
  gap: 0; max-width: 1440px; margin: 0 auto;
  min-height: calc(100vh - 52px); }
.sidebar {
  padding: 18px 12px 60px 16px; border-right: 1px solid var(--line);
  position: sticky; top: 52px; max-height: calc(100vh - 52px);
  overflow-y: auto; font-size: 14px; background: var(--card);
}
.sidebar ul { list-style: none; margin: 0; padding: 0; }
.sidebar details { margin-bottom: 4px; }
.sidebar summary {
  cursor: pointer; font-weight: 650; padding: 6px 8px; border-radius: 6px;
  color: var(--brand); user-select: none; list-style: none;
}
.sidebar summary::-webkit-details-marker { display: none; }
.sidebar summary::before { content: "\\25B8"; display: inline-block;
  width: 1em; color: var(--muted); transition: transform .15s; }
.sidebar details[open] > summary::before { transform: rotate(90deg); }
.sidebar summary:hover { background: #eef1f8; }
.sidebar a { display: block; padding: 3px 8px 3px 26px; color: #3b4357;
  border-radius: 6px; }
.sidebar a:hover { background: #eef1f8; text-decoration: none; }
.sidebar a.active { background: var(--accent); color: #fff; font-weight: 650; }
.sidebar .leaf { padding: 6px 8px 6px 14px; font-weight: 650; color: var(--brand); }
.sidebar .badge { display: inline-block; font-size: 11px; padding: 0 6px;
  border-radius: 99px; color: #fff; margin-left: 6px; vertical-align: 1px; }

.content { padding: 26px 34px 80px; min-width: 0; }
.toc {
  padding: 26px 16px 60px 8px; border-left: 1px solid var(--line);
  position: sticky; top: 52px; max-height: calc(100vh - 52px);
  overflow-y: auto; font-size: 12.5px;
}
.toc .toc-t { font-weight: 700; text-transform: uppercase; letter-spacing: .06em;
  color: var(--muted); font-size: 11px; margin-bottom: 8px; }
.toc a { display: block; color: #4a5268; padding: 2.5px 0; }
.toc a:hover { color: var(--accent); text-decoration: none; }
.toc a.l3 { padding-left: 12px; font-size: 12px; }

h1 { font-size: 30px; line-height: 1.25; margin: 4px 0 10px; color: var(--brand); }
h1 + p { color: var(--muted); }
h2 { font-size: 21px; margin: 34px 0 10px; padding-bottom: 6px;
  border-bottom: 2px solid var(--line); color: var(--brand); }
h3 { font-size: 16.5px; margin: 24px 0 8px; color: #323a52; }
p { margin: 10px 0; }
ul { margin: 10px 0; padding-left: 22px; }
li { margin: 4px 0; }
li ul { margin: 4px 0; }

.sec-main h1 { border-bottom: 4px solid var(--main); padding-bottom: 8px; }
.sec-mid h1 { border-bottom: 4px solid var(--mid); padding-bottom: 8px; }
.sec-background h1 { border-bottom: 4px solid var(--bg-char); padding-bottom: 8px; }
.sec-world h1 { border-bottom: 4px solid var(--world); padding-bottom: 8px; }
.sec-exams h1 { border-bottom: 4px solid var(--exams); padding-bottom: 8px; }
.sec-systems h1 { border-bottom: 4px solid var(--systems); padding-bottom: 8px; }
.sec-vol1 h1 { border-bottom: 4px solid var(--vol); padding-bottom: 8px; }

.kicker { font-size: 12.5px; color: var(--muted); margin-bottom: 18px; }
.kicker a { color: var(--muted); }
.kicker .dot { margin: 0 6px; }
.tag { display: inline-block; font-size: 11.5px; font-weight: 700;
  letter-spacing: .04em; text-transform: uppercase; color: #fff;
  padding: 1px 8px; border-radius: 99px; vertical-align: 2px; }
.tag-main { background: var(--main); } .tag-mid { background: var(--mid); }
.tag-background { background: var(--bg-char); }
.tag-world { background: var(--world); } .tag-exams { background: var(--exams); }
.tag-systems { background: var(--systems); }
.tag-vol1 { background: var(--vol); }
.tag-authority { background: var(--authority); }
.tag-rivals { background: var(--rivals); } .tag-allies { background: var(--allies); }
.tag-peers { background: var(--peers); } .tag-family { background: var(--family); }
.tag-outside { background: var(--outside); }

.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px; margin: 22px 0; }
.card.downloads { grid-column: 1 / -1; }
.card.downloads .dl a { display: inline-block; margin: 2px 18px 2px 0;
  font-weight: 650; font-size: 14.5px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
  padding: 16px 18px; box-shadow: 0 1px 3px rgba(20,30,60,.06); }
.card h3 { margin: 0 0 6px; font-size: 17px; }
.card p { margin: 0; color: var(--muted); font-size: 14px; }
.card .go { display: inline-block; margin-top: 10px; font-weight: 650; font-size: 14px; }
.hero { background: linear-gradient(135deg, #2b3a67, #3b5bdb); color: #fff;
  border-radius: 14px; padding: 30px 32px; margin: 8px 0 6px; }
.hero h1 { color: #fff; border: 0; margin: 0 0 6px; font-size: 32px; }
.hero p { color: #dce3ff; margin: 4px 0; }
.stats { display: flex; flex-wrap: wrap; gap: 10px 26px; margin-top: 16px; }
.stats b { display: block; font-size: 22px; }
.stats span { font-size: 12.5px; color: #cdd7ff; text-transform: uppercase;
  letter-spacing: .05em; }
footer.site {
  grid-column: 1 / -1; border-top: 1px solid var(--line); padding: 16px 34px;
  color: var(--muted); font-size: 13px; background: var(--card);
}

@media (max-width: 1100px) { .layout { grid-template-columns: 220px minmax(0,1fr); }
  .toc { display: none; } }
@media (max-width: 760px) { .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; max-height: none; border-right: 0;
    border-bottom: 1px solid var(--line); }
  .content { padding: 18px; } }

/* print documents (share/print) */
@media print {
  .topbar, .sidebar, .toc, footer.site { display: none !important; }
  .layout { display: block; max-width: none; }
  .content { padding: 0; }
  body { background: #fff; font-size: 11pt; }
  .print-cover { page-break-after: always; text-align: center;
    padding-top: 22vh; }
  .print-entity { page-break-before: always; }
  h1 { font-size: 22pt; } h2 { font-size: 15pt; }
  a { color: inherit; }
  .print-toc { page-break-after: always; }
  .print-toc li { margin: 3px 0; }
}
"""

SEARCH_JS = """(function () {
  var input = document.getElementById('q');
  var box = document.getElementById('results');
  if (!input || !box || typeof SEARCH_INDEX === 'undefined') return;
  var ROOT = document.body.getAttribute('data-root') || '';
  var sel = -1;

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function search(q) {
    q = q.trim().toLowerCase();
    if (q.length < 2) return [];
    var terms = q.split(/\\s+/);
    var hits = [];
    for (var i = 0; i < SEARCH_INDEX.length; i++) {
      var r = SEARCH_INDEX[i];
      var t = (r.t + ' ' + r.s + ' ' + r.x).toLowerCase();
      var score = 0, ok = true;
      for (var j = 0; j < terms.length; j++) {
        var w = terms[j];
        if (t.indexOf(w) < 0) { ok = false; break; }
        if (r.t.toLowerCase().indexOf(w) >= 0) score += 4;
        if (r.s.toLowerCase().indexOf(w) >= 0) score += 3;
        score += 1;
      }
      if (ok) hits.push({ r: r, score: score, at: t.indexOf(terms[0]) });
    }
    hits.sort(function (a, b) { return b.score - a.score || a.at - b.at; });
    return hits.slice(0, 12);
  }
  function snippet(x, terms) {
    var low = x.toLowerCase(), at = -1;
    for (var j = 0; j < terms.length && at < 0; j++) at = low.indexOf(terms[j]);
    if (at < 0) at = 0;
    var a = Math.max(0, at - 55), b = Math.min(x.length, at + 95);
    var s = (a > 0 ? '…' : '') + x.slice(a, b) + (b < x.length ? '…' : '');
    s = esc(s);
    for (var k = 0; k < terms.length; k++) {
      var re = new RegExp('(' + terms[k].replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + ')', 'ig');
      s = s.replace(re, '<mark>$1</mark>');
    }
    return s;
  }
  function render(q) {
    var terms = q.trim().toLowerCase().split(/\\s+/);
    var hits = search(q);
    sel = -1;
    if (!q.trim() || q.trim().length < 2) { box.hidden = true; return; }
    if (!hits.length) {
      box.innerHTML = '<div class="none">No matches for “' + esc(q) + '”</div>';
      box.hidden = false; return;
    }
    var html = '';
    for (var i = 0; i < hits.length; i++) {
      var r = hits[i].r;
      html += '<a href="' + ROOT + r.u + '">' +
        '<div class="rt">' + esc(r.t) + '</div>' +
        '<div class="rs">' + esc(r.s) + '</div>' +
        '<div class="rx">' + snippet(r.x, terms) + '</div></a>';
    }
    box.innerHTML = html;
    box.hidden = false;
  }
  input.addEventListener('input', function () { render(input.value); });
  input.addEventListener('focus', function () { render(input.value); });
  document.addEventListener('click', function (e) {
    if (!box.contains(e.target) && e.target !== input) box.hidden = true;
  });
  document.addEventListener('keydown', function (e) {
    var links = box.querySelectorAll('a');
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault(); input.focus(); input.select();
    } else if (e.key === 'Escape') { box.hidden = true; input.blur(); }
    else if (e.key === 'ArrowDown' && !box.hidden && links.length) {
      e.preventDefault(); sel = Math.min(sel + 1, links.length - 1); mark(links);
    } else if (e.key === 'ArrowUp' && !box.hidden && links.length) {
      e.preventDefault(); sel = Math.max(sel - 1, 0); mark(links);
    } else if (e.key === 'Enter' && !box.hidden && links.length && sel >= 0) {
      e.preventDefault(); links[sel].click();
    }
  });
  function mark(links) {
    for (var i = 0; i < links.length; i++)
      links[i].classList.toggle('sel', i === sel);
    if (links[sel]) links[sel].scrollIntoView({ block: 'nearest' });
  }
  if (location.hash.indexOf('#q=') === 0) {
    input.value = decodeURIComponent(location.hash.slice(3));
    input.focus();
    render(input.value);
  }
})();
"""

README = """COTE Knowledge Base — share site
===============================

Static HTML site over the evidence-backed knowledge base for the
Classroom of the Elite light novels.

  index.html            start here (stats + sections + PDF downloads)
  background.html       background characters
  main/ mid/            character profiles (section-preserving)
  world/                world / location profiles
  exams/                exam profiles + master chronology
  systems/              school systems (points, council, clubs, expulsion)
  vol1/                 Year 1, Volume 1 — guides + scene transcripts
  pdfs/                 6 per-category PDFs (print editions of the site)
  assets/               stylesheet + client-side search index

Search: press / (or click the box in the header). Works opened from
disk (file://) — the index is a JS constant, no server needed.

Developer notes: generated — never hand-edit. Regenerate:
  python3 kb/build_share_site.py
Built from the repository knowledge base. Verbatim quotes are cited
with volume + page anchors (e.g. y1v1 p.247).
"""


def md5_tree(path):
    h = hashlib.md5()
    for f in sorted(path.rglob("*")):
        if f.is_file() and f.suffix != ".pdf":
            h.update(str(f.relative_to(path)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def index_links(md_file, base_rel):
    """[(text, 'dir/link.html')] from a dossiers index, author order."""
    if not md_file.exists():
        return []
    out = []
    for m in LINK_RE.finditer(md_file.read_text(encoding="utf-8")):
        href = m.group(2)
        if href.startswith("#") or not href.endswith(".md"):
            continue
        out.append((m.group(1), f"{base_rel}{href[:-3]}.html"))
    return out


def mid_groups():
    """[(type, [(text, href)])] from mid/index.md ## groups."""
    groups = []
    if not (DOSSIERS / "mid" / "index.md").exists():
        return groups
    cur = None
    for line in (DOSSIERS / "mid" / "index.md").read_text(
            encoding="utf-8").splitlines():
        mh = re.match(r"^## (.+)$", line)
        if mh:
            label = mh.group(1).strip()
            m = re.match(r"^([a-z]+) \(\d+\)$", label)
            cur = (m.group(1) if m else label, [])
            groups.append(cur)
            continue
        ml = LINK_RE.search(line)
        if ml and cur is not None and ml.group(2).endswith(".md"):
            cur[1].append((ml.group(1),
                           f"mid/{ml.group(2)[:-3]}.html"))
    return groups


def build_nav():
    nav: list = [{"label": "Home", "href": "index.html", "id": "home"}]
    main = index_links(DOSSIERS / "main" / "index.md", "main/")
    mid = mid_groups()
    world = []
    for t, h in index_links(DOSSIERS / "world" / "index.md", "world/"):
        world.append((t, h))
    exams = index_links(DOSSIERS / "exams" / "index.md", "exams/")
    if not any(h == "exams/chronology.html" for _t, h in exams):
        exams.append(("Master Chronology", "exams/chronology.html"))
    systems = index_links(DOSSIERS / "systems" / "index.md", "systems/")
    nav.append({
        "label": "Characters", "id": "characters", "groups": [
            {"label": "Main", "id": "main", "href": "main/index.html",
             "items": main},
            {"label": "Mid", "id": "mid", "href": "mid/index.html",
             "groups": [{"label": t, "items": items} for t, items in mid]},
            {"label": "Background (226)", "id": "background",
             "href": "background.html", "items": []},
        ]})
    nav.append({"label": "Volume 1 (Year 1)", "id": "vol1",
                "href": "vol1/index.html",
                "items": [(label, f"vol1/{stem}.html")
                          for stem, label in VOL1_FILES]})
    nav.append({"label": "World & Locations", "id": "world",
                "href": "world/index.html",
                "items": world})
    nav.append({"label": "Exams", "id": "exams",
                "href": "exams/index.html", "items": exams})
    nav.append({"label": "School Systems", "id": "systems",
                "href": "systems/index.html", "items": systems})
    return nav


def section_of(out_path):
    top = out_path.split("/")[0]
    if out_path == "index.html":
        return "home"
    if out_path == "background.html":
        return "background"
    if top in ("main", "mid", "world", "exams", "systems", "vol1"):
        return top
    return "home"


def tag_of(out_path):
    sec = section_of(out_path)
    if sec == "mid":
        parts = out_path.split("/")
        label = "mid" if parts[1] == "index.html" else parts[1]
        return f'<span class="tag tag-{label}">{label}</span>'
    if sec in ("main", "background", "world", "exams", "systems", "vol1"):
        label = {"background": "background", "main": "main",
                 "vol1": "vol 1"}.get(sec, sec)
        return f'<span class="tag tag-{label}">{label}</span>'
    return ""


def nav_html(nav, current, root):
    sec = section_of(current)

    def active(href):
        return ' class="active"' if href == current else ""

    def leaf_a(href):
        cls = "leaf active" if href == current else "leaf"
        return f'<a class="{cls}" href="{root}{href}"'

    def items_list(items):
        if not items:
            return ""
        h = "<ul>"
        for text, href in items:
            h += (f'<li><a href="{root}{href}"{active(href)}>'
                  f'{text}</a></li>')
        return h + "</ul>"

    def groups_list(groups):
        h = "<ul>"
        for g in groups:
            if "groups" in g:
                is_open = g["id"] == sec
                h += f'<li><details{" open" if is_open else ""}>' \
                     f'<summary>{g["label"]}</summary>'
                if g.get("href"):
                    h += f'<ul><li>{leaf_a(g["href"])}>' \
                         f'{g["label"]} overview</a></li></ul>'
                for sub in g["groups"]:
                    is_sub = sec == "mid" and current.startswith(
                        f"mid/{sub['label']}/")
                    h += f'<details{" open" if is_sub else ""}>' \
                         f'<summary>{sub["label"]}</summary>' \
                         f'{items_list(sub["items"])}</details>'
                h += "</details></li>"
            else:
                is_open = g["id"] == sec
                h += f'<li><details{" open" if is_open else ""}>' \
                     f'<summary>{g["label"]}</summary>'
                if g.get("href"):
                    h += f'<ul><li>{leaf_a(g["href"])}>' \
                         f'{g["label"]} overview</a></li></ul>'
                h += f'{groups_list(g.get("groups", []))}' \
                     f'{items_list(g.get("items", []))}</details></li>'
        return h + "</ul>"

    def render_nav(entries):
        h = "<ul>"
        for e in entries:
            if "groups" in e or (e.get("groups") is not None):
                is_open = section_of(current) == e.get("id") or (
                    e["id"] == "characters" and sec in
                    ("main", "mid", "background"))
                h += f'<li><details{" open" if is_open else ""}>' \
                     f'<summary>{e["label"]}</summary>'
                if e.get("href"):
                    h += f'<ul><li>{leaf_a(e["href"])}>' \
                         f'{e["label"]} overview</a></li></ul>'
                h += groups_list(e.get("groups", []))
                h += items_list(e.get("items", []))
                h += "</details></li>"
            elif "items" in e:
                is_open = section_of(current) == e["id"]
                h += f'<li><details{" open" if is_open else ""}>' \
                     f'<summary>{e["label"]}</summary>'
                h += f'<ul><li>{leaf_a(e["href"])}>overview</a></li></ul>'
                h += items_list(e["items"])
                h += "</details></li>"
            else:
                h += f'<li><a href="{root}{e["href"]}"{active(e["href"])}>' \
                     f'{e["label"]}</a></li>'
        return h + "</ul>"

    return render_nav(nav)


def toc_html(headings):
    items = [(lv, hid, text) for lv, hid, text in headings
             if lv in (2, 3)]
    if len(items) < 2:
        return ""
    h = ['<div class="toc-t">On this page</div>']
    for lv, hid, text in items:
        h.append(f'<a class="l{lv}" href="#{hid}">{text}</a>')
    return "".join(h)


def page(title, body_html, headings, out_path, nav, kicker_extra=""):
    depth = out_path.count("/")
    root = "../" * depth
    sec = section_of(out_path)
    if out_path == "index.html":
        title_line = "COTE Knowledge Base"
    else:
        title_line = f"{title} · COTE Knowledge Base"
    tag = tag_of(out_path)
    kicker = f'<div class="kicker"><a href="{root}index.html">COTE KB</a>' \
             f'{kicker_extra}{tag}</div>'
    toc = toc_html(headings)
    nav_html_text = nav_html(nav, out_path, root)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_line}</title>
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body data-root="{root}" class="sec-{sec}">
<header class="topbar">
  <a class="brand" href="{root}index.html">COTE Knowledge Base</a>
  <div class="searchwrap">
    <input id="q" type="search" autocomplete="off"
           placeholder="Search characters, scenes, exams…  (press /)">
    <div id="results" hidden></div>
  </div>
</header>
<div class="layout">
  <nav class="sidebar">{nav_html_text}</nav>
  <main class="content">{kicker}{body_html}</main>
  <aside class="toc">{toc}</aside>
  <footer class="site">Quotes on this site are verbatim from the
    Classroom of the Elite light novels; citations like
    <code>y1v1 p.247</code> mean Year 1, Volume 1, page 247.</footer>
</div>
<script src="{root}assets/search-index.js"></script>
<script src="{root}assets/search.js"></script>
</body>
</html>
"""


def page_title(md_text, fallback):
    m = re.match(r"^# (.+)$", md_text, re.M)
    return m.group(1).strip() if m else fallback


VOL1_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+?)\)")
VOL1_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
VOL1_EM_RE = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?!\*)")
VOL1_CODE_RE = re.compile(r"`([^`]+)`")
VOL1_HEADING_RE = re.compile(r"^(#{1,6}) (.+)$")
VOL1_HR_RE = re.compile(r"^---$")
VOL1_TABLE_SEP = re.compile(r"^:?-{2,}:?$")


def vol1_inline(text):
    """escape, then links/code/bold/italic — guide files use them all."""
    out = html.escape(text, quote=False)
    out = VOL1_LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>',
                           out)
    out = VOL1_CODE_RE.sub(r"<code>\1</code>", out)
    out = VOL1_BOLD_RE.sub(r"<strong>\1</strong>", out)
    out = VOL1_EM_RE.sub(r"<em>\1</em>", out)
    return out


def render_vol1(md):
    """guide/transcript markdown (tables, blockquotes, hr, italics) →
    (html, headings)."""
    lines = md.splitlines()
    out, headings = [], []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        mh = VOL1_HEADING_RE.match(line)
        if mh:
            level = len(mh.group(1))
            text = mh.group(2).strip()
            hid = slug(text)
            headings.append((level, hid, text))
            out.append(f'<h{level} id="{hid}">{vol1_inline(text)}</h{level}>')
            i += 1
            continue
        if VOL1_HR_RE.match(line.strip()):
            out.append("<hr>")
            i += 1
            continue
        if line.startswith("|"):
            block = []
            while i < n and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            rows = []
            for j, bl in enumerate(block):
                cells = [c.strip() for c in bl.strip().strip("|").split("|")]
                if j == 1 and cells and all(VOL1_TABLE_SEP.match(c)
                                            for c in cells if c):
                    continue
                rows.append(cells)
            if rows:
                th = "".join(f"<th>{vol1_inline(c)}</th>" for c in rows[0])
                body = "".join(
                    "<tr>" + "".join(f"<td>{vol1_inline(c)}</td>"
                                     for c in r) + "</tr>"
                    for r in rows[1:])
                out.append(f"<table><thead><tr>{th}</tr></thead>"
                           f"<tbody>{body}</tbody></table>")
            continue
        if line.startswith(">"):
            block = []
            while i < n and lines[i].startswith(">"):
                block.append(lines[i].lstrip("> "))
                i += 1
            paras = "".join(
                f"<p>{vol1_inline(p.strip())}</p>"
                for p in "\n".join(block).split("\n\n") if p.strip())
            out.append(f"<blockquote>{paras}</blockquote>")
            continue
        if line.startswith("- "):
            items = [line[2:]]
            i += 1
            while i < n:
                nxt = lines[i]
                if nxt.startswith("- "):
                    items.append(nxt[2:])
                    i += 1
                elif nxt.strip() and not VOL1_HEADING_RE.match(nxt) \
                        and not nxt.startswith(("|", "> ")) \
                        and not VOL1_HR_RE.match(nxt.strip()):
                    items[-1] += " " + nxt.strip()
                    i += 1
                else:
                    break
            out.append("<ul>" + "".join(f"<li>{vol1_inline(it)}</li>"
                                        for it in items) + "</ul>")
            continue
        block = [line]
        i += 1
        while i < n and lines[i].strip() and not VOL1_HEADING_RE.match(
                lines[i]) and not lines[i].startswith(("- ", "|", ">")) \
                and not VOL1_HR_RE.match(lines[i].strip()):
            block.append(lines[i])
            i += 1
        out.append("<p>" + vol1_inline(" ".join(b.strip() for b in block))
                   + "</p>")
    return "\n".join(out), headings


def build_vol1():
    """[meta] for VOL1_FILES — same shape as other page metas."""
    pages = []
    for stem, label in VOL1_FILES:
        src = VOL1_SRC / f"{stem}.md"
        md = src.read_text(encoding="utf-8")
        pages.append({"rel": f"drafts/people/{stem}.md", "src": str(src),
                      "out": f"vol1/{stem}.html",
                      "title": page_title(md, label),
                      "search_title": label,
                      "section": "vol1", "label": label})
    return pages


def vol1_home(nav):
    links = "".join(
        f'<li><a href="{stem}.html">{html.escape(label)}</a> — '
        f'{"every scene in order, with page numbers" if "transcript" in stem else "personality, arcs, relationships, and key quotes"}'
        f'</li>'
        for stem, label in VOL1_FILES)
    hid = "year-1-volume-1"
    title = "Year 1, Volume 1 — guides and scene transcripts"
    body = f"""<h1 id="{hid}">{title}</h1>
<p>Read the first volume of Classroom of the Elite scene by scene, or open
a character guide. Every speech line, narration beat, and inner monologue
is quoted verbatim and carries its page number (e.g. p.247).</p>
<ul>{links}</ul>
<p>Character profiles for the whole cast live under
<a href="../main/index.html">Characters</a>; the point-of-view character
is <a href="../main/ayanokouji-kiyotaka.html">Ayanokōji Kiyotaka</a>.</p>"""
    headings = [(1, hid, title)]
    return page(title, body, headings, "vol1/index.html", nav,
                kicker_extra=' <span class="dot">›</span> '
                             'Volume 1 (Year 1)')


def home_page(nav, stats):
    cards = [
        ("Characters", "main/index.html",
         f"{stats['main']} main · {stats['mid']} mid · "
         f"{stats['bg']} background — profiles, arcs, and every quote "
         f"tied to a volume and page."),
        ("Volume 1 (Year 1)", "vol1/index.html",
         "Scene-by-scene transcripts and character guides for the "
         "first volume, every line with its page number."),
        ("World & Locations", "world/index.html",
         f"{stats['world']} locations — layout, narrative role, "
         f"and key scenes."),
        ("Exams", "exams/index.html",
         f"{stats['exams']} exams — rules, points, conditions, and "
         f"every run with evidence."),
        ("School Systems", "systems/index.html",
         f"{stats['systems']} systems — points, student council, "
         f"clubs, expulsion."),
        ("Search", "#", "Press / anywhere, or click here, to search "
         "every character, scene, exam, and quote."),
    ]
    card_html = ""
    for t, href, d in cards:
        go = (f'<a class="go" href="#" onclick="document.getElementById'
              f'(\'q\').focus();return false;">Open →</a>'
              if href == "#" else
              f'<a class="go" href="{href}">Open →</a>')
        card_html += (f'<div class="card"><h3>{t}</h3><p>{d}</p>'
                      f'{go}</div>')
    pdf_names = [("Background Characters", "background"),
                 ("Main Characters", "main"), ("Mid Characters", "mid"),
                 ("World & Locations", "world"), ("Exams", "exams"),
                 ("School Systems", "systems")]
    pdf_links = " ".join(
        f'<a href="pdfs/{n}.pdf">{label}</a>'
        for label, n in pdf_names)
    downloads = ('<div class="card downloads"><h3>Downloads (PDF)</h3>'
                 f'<p class="dl">{pdf_links}</p></div>')
    body = f"""<div class="hero">
<h1>COTE Knowledge Base</h1>
<p>Character profiles, scene-by-scene transcripts, exam rules, and world
guides for the Classroom of the Elite light novels — every statement
quoted verbatim with a volume and page number.</p>
<div class="stats">
<div><b>{stats['chars']}</b><span>characters</span></div>
<div><b>{stats['world']}</b><span>locations</span></div>
<div><b>{stats['exams']}</b><span>exams</span></div>
<div><b>{stats['systems']}</b><span>systems</span></div>
<div><b>{stats['quotes']:,}</b><span>verbatim quotes</span></div>
<div><b>{stats['events']:,}</b><span>scenes</span></div>
</div>
</div>
<div class="cards">{card_html}{downloads}</div>
<p>How to read a page: <strong>bold</strong> labels are written
analysis; “curly quotes” are verbatim text from the novels; citations
like <code>y2v9 p.13</code> mean Year 2, Volume 9, page 13.</p>"""
    return page("COTE Knowledge Base", body, [], "index.html", nav)


def search_records(pages):
    """per-heading records: {u, t, s, x} — u is site-root relative."""
    records = []
    for meta in pages:
        md = Path(meta["src"]).read_text(encoding="utf-8")
        title = meta.get("search_title", meta["title"])
        rec = {"u": meta["out"], "t": title, "s": title, "x": ""}
        current = rec
        for line in md.splitlines():
            mh = re.match(r"^#{1,6} (.+)$", line)
            if mh:
                level = len(line) - len(line.lstrip("#"))
                text = mh.group(1).strip()
                if level == 1:
                    current = rec
                    continue
                current = {"u": f"{meta['out']}#{slug(text)}",
                           "t": title, "s": text, "x": ""}
                records.append(current)
                continue
            clean = line.strip()
            if not clean:
                continue
            clean = LINK_RE.sub(r"\1", clean)
            clean = re.sub(r"[*`]", "", clean)
            current["x"] = (current["x"] + " " + clean).strip()
            if len(current["x"]) > 1200:
                current["x"] = current["x"][:1200] + " …"
    return records


def build_pages(nav):
    md_files = []
    for f in sorted(DOSSIERS.rglob("*.md")):
        rel = f.relative_to(DOSSIERS).as_posix()
        md_files.append((rel, f))
    pages = []
    for rel, f in md_files:
        out = rel[:-3] + ".html"
        md = f.read_text(encoding="utf-8")
        title = page_title(md, rel)
        pages.append({"rel": rel, "src": str(f), "out": out,
                      "title": title, "section": section_of(out)})
    return pages


HREF_RE = re.compile(r'href="([^"]+)"')


def print_links(html, out_path):
    """content links resolve relative to the page's site dir; print docs
    are flat in share/print/, so rebase them against ../site/<dir>/."""
    d = posixpath.dirname(out_path)

    def rep(m):
        u = m.group(1)
        if u.startswith(("http://", "https://", "#")):
            return m.group(0)
        rel = posixpath.normpath(posixpath.join(d, u)) if d else \
            posixpath.normpath(u)
        if rel.startswith(".."):
            return m.group(0)
        return f'href="../site/{rel}"'
    return HREF_RE.sub(rep, html)


def print_doc(label, sub, entries, out_name, cover):
    """cover + TOC + entities (page-broken) for chromium."""
    parts = [f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{label}</title>
<link rel="stylesheet" href="../site/assets/style.css">
</head><body class="sec-{sub}" data-root="../site/">
<div class="content">
<div class="print-cover">
<h1>{label}</h1>
<p>{cover}</p>
<p>Verbatim quotes from the novels — each cited to its volume and
page (e.g. y1v1 p.247).</p>
</div>
<div class="print-toc"><h2>Contents</h2><ul>"""]
    for title, _html, _out in entries:
        parts.append(f"<li>{title}</li>")
    parts.append("</ul></div>")
    for i, (title, html, out_path) in enumerate(entries):
        cls = "print-entity" if i else "print-entity first"
        parts.append(
            f'<section class="{cls}">{print_links(html, out_path)}'
            f'</section>')
    parts.append("</div></body></html>\n")
    (PRINT / out_name).write_text("\n".join(parts), encoding="utf-8")


def make_zip():
    """deterministic zip of share/site/ → share/cote-kb-share.zip
    (fixed timestamps + sorted order → md5-stable)."""
    out = ROOT / "share" / "cote-kb-share.zip"
    with zipfile.ZipFile(out, "w") as z:
        for f in sorted(SITE.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(SITE).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())
    h = hashlib.md5(out.read_bytes()).hexdigest()
    print(f"zip: {out.name} — {out.stat().st_size // 1024} KB, md5 {h}")
    return h


def make_docs():
    """share/site/ → docs/ (GitHub Pages serves /docs from main)."""
    docs = ROOT / "docs"
    if docs.exists():
        shutil.rmtree(docs)
    shutil.copytree(SITE, docs)
    n = sum(1 for _ in docs.rglob("*") if _.is_file())
    print(f"docs: {n} files → docs/ (md5 {md5_tree(docs)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md5", action="store_true",
                    help="print md5 of the site tree and exit")
    ap.add_argument("--zip", action="store_true",
                    help="zip share/site into share/cote-kb-share.zip")
    ap.add_argument("--docs", action="store_true",
                    help="copy share/site into docs/ for GitHub Pages")
    args = ap.parse_args()
    if args.md5:
        print(md5_tree(SITE))
        return 0
    if args.zip:
        make_zip()
        return 0
    if args.docs:
        make_docs()
        return 0

    shutil.rmtree(SITE, ignore_errors=True)
    shutil.rmtree(PRINT, ignore_errors=True)
    SITE.mkdir(parents=True, exist_ok=True)
    PRINT.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    stats = {
        "main": len(list((DOSSIERS / "main").glob("*.md"))) - 1,
        "mid": len(list((DOSSIERS / "mid").rglob("*.md"))) - 1,
        "bg": 0, "world": len(list((DOSSIERS / "world").glob("*.md"))) - 1,
        "exams": len(list((DOSSIERS / "exams").glob("*.md"))) - 2,
        "systems": len(list((DOSSIERS / "systems").glob("*.md"))) - 1,
        "quotes": con.execute("SELECT count(*) FROM quotes").fetchone()[0],
        "events": con.execute("SELECT count(*) FROM events").fetchone()[0],
    }
    bg_md = (DOSSIERS / "background.md").read_text(encoding="utf-8")
    stats["bg"] = len(re.findall(r"^### ", bg_md, re.M))
    stats["chars"] = stats["main"] + stats["mid"] + stats["bg"]
    con.close()

    nav = build_nav()
    pages = build_pages(nav)
    for meta in pages:
        md = Path(meta["src"]).read_text(encoding="utf-8")
        body, headings = render(md)
        body = rewrite_links(body)
        html = page(meta["title"], body, headings, meta["out"], nav,
                    kicker_extra=f' <span class="dot">›</span> '
                    f'{meta["title"]}' if meta["out"] != "index.html"
                    else "")
        out = SITE / meta["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    vol1_pages = build_vol1()
    for meta in vol1_pages:
        md = Path(meta["src"]).read_text(encoding="utf-8")
        body, headings = render_vol1(md)
        body = rewrite_links(body)
        html_doc = page(
            meta["title"], body, headings, meta["out"], nav,
            kicker_extra=' <span class="dot">›</span> Year 1 · Volume 1 '
                         f'<span class="dot">›</span> {meta["title"]}')
        out = SITE / meta["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html_doc, encoding="utf-8")
    (SITE / "vol1" / "index.html").write_text(vol1_home(nav),
                                               encoding="utf-8")

    (SITE / "index.html").write_text(home_page(nav, stats),
                                     encoding="utf-8")
    (SITE / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    (SITE / "assets" / "search.js").write_text(SEARCH_JS,
                                               encoding="utf-8")
    records = search_records(pages)
    records += search_records(vol1_pages)
    records.append({
        "u": "vol1/index.html",
        "t": "Year 1, Volume 1 — guides and scene transcripts",
        "s": "Year 1, Volume 1 — guides and scene transcripts",
        "x": "Scene-by-scene transcripts and character guides for the "
             "first volume of Classroom of the Elite. Every line quoted "
             "verbatim with its page number. Ayanokouji Kiyotaka, "
             "Horikita Suzune, Kushida Kikyou."})
    (SITE / "assets" / "search-index.js").write_text(
        "const SEARCH_INDEX = " + json.dumps(
            records, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    (SITE / "README.txt").write_text(README, encoding="utf-8")

    # print documents
    def group(sec, files=None):
        picked = [m for m in pages
                  if (files is None and m["section"] == sec)
                  or (files and m["rel"] in files)]
        entries = []
        for m in picked:
            body, _ = render(Path(m["src"]).read_text(encoding="utf-8"))
            body = rewrite_links(body)
            entries.append((m["title"], body, m["out"]))
        return entries

    print_doc("Background Characters", "background",
              group("background"), "background.html",
              "226 background characters")
    print_doc("Main Characters", "main", group("main"), "main.html",
              "7 main characters")
    print_doc("Mid Characters", "mid", group("mid"), "mid.html",
              "20 mid characters + group index")
    print_doc("World & Locations", "world", group("world"),
              "world.html", "28 locations")
    entries = group("exams")
    print_doc("Exams & Master Chronology", "exams", entries,
              "exams.html", "15 exams + master chronology")
    print_doc("School Systems", "systems", group("systems"),
              "systems.html", "5 school systems")

    pdf_bin = (shutil.which("chromium") or shutil.which("chromium-browser")
               or shutil.which("google-chrome"))
    if pdf_bin:
        pdf_dir = SITE / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        for src in sorted(PRINT.glob("*.html")):
            out = pdf_dir / f"{src.stem}.pdf"
            subprocess.run(
                [pdf_bin, "--headless", "--disable-gpu", "--no-sandbox",
                 "--disable-dev-shm-usage", f"--print-to-pdf={out}",
                 str(src)],
                check=True, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
        print("pdfs: 6 → share/site/pdfs/")
    else:
        print("pdfs: chromium not found — skipped", file=sys.stderr)

    n = len(pages) + len(vol1_pages) + 1
    print(f"build_share_site: {n} pages + assets + "
          f"{len(records)} search records + 6 print docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())

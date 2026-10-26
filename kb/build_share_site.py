#!/usr/bin/env python3
"""A6: build the encyclopedia site.

python3 kb/build_share_site.py [--md5] [--zip] [--docs] [--no-pdf]

Layout of the build (the old single-file version is replaced; navigation no
longer comes from the order of links in the dossier indexes):

  kb/site_arch.py       the information architecture: sections, volume
                        registry, human names, tier labels
  kb/site_data.py       cote_kb.db + ledgers/ access, plain dicts out
  kb/site_shell.py      masthead, tabs, rails, breadcrumbs, chips, footer
  kb/site_sections.py   home, people, story, school, world builders
  kb/site_topics.py     topics, reader doors, appendix, volume documents
  kb/site_assets/       style.css, search.js (source of the emitted assets)

Outputs share/site/ (the public tree), share/print/ (print bundles) and
share/site/pdfs/. Deterministic: two builds are byte-identical, verified
with --md5. share_check.py is the read-only gate.

Content rules baked in here:
  - dossier markdown keeps its body; its internal taxonomy is stripped and
    its counts reworded before it reaches a reader;
  - quote rows are served as text at a page, never as proof of a speaker;
  - a volume is labelled transcribed only when the ledgers say so.
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
import site_arch  # noqa: E402
import site_data as D  # noqa: E402
import site_sections as SEC  # noqa: E402
import site_topics as TOP  # noqa: E402
import site_shell as S  # noqa: E402
from roster_mine import DB_PATH  # noqa: E402
from share_render import render, slug  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOSSIERS = ROOT / "dossiers"
SITE = ROOT / "share" / "site"
PRINT = ROOT / "share" / "print"
ASSETS = Path(__file__).resolve().parent / "site_assets"

H2_RE = re.compile(r'<h([23]) id="([^"]+)">(.*?)</h\1>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
TEXT_JUNK_RE = re.compile(r"\s+")

DOC_STEM_RE = TOP.DOC_STEM_RE


def md5_tree(path):
    h = hashlib.md5()
    for f in sorted(path.rglob("*")):
        if f.is_file() and f.suffix != ".pdf":
            h.update(str(f.relative_to(path)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def extract_headings(body):
    out = []
    for m in H2_RE.finditer(body):
        text = TEXT_JUNK_RE.sub(" ", TAG_RE.sub("", m.group(3))).strip()
        out.append((int(m.group(1)), m.group(2), html.unescape(text)))
    return out


def page_factory(ctx):
    def page(title, section, body, crumb, *, out, rail, lede="", kicker="",
             tagline_label="", related=None, meter=None, headings=None,
             scope=None, **_ignored):
        return S.page({
            "title": title, "section": section, "body": body, "crumb": crumb,
            "out": out, "rail": rail, "lede": lede, "kicker": kicker,
            "tagline_label": tagline_label, "related": related or [],
            "meter": meter or [], "headings": headings
            or extract_headings(body), "scope": ctx["scope"],
        })
    return page


def scope_options(ctx):
    return [(int(v["order"]), v["label"]) for v in ctx["vol_list"]]


def memo_lookup(con):
    cache = {}

    def lookup(vol_id, page_no):
        key = (vol_id, page_no)
        if key not in cache:
            cache[key] = D.quotes_at(con, vol_id, page_no, 2)
        return cache[key]
    return lookup


def plan_vol_docs(ctx):
    if not D.DRAFTS.exists():
        return
    for f in sorted(D.DRAFTS.glob("*.md")):
        m = DOC_STEM_RE.match(f.stem)
        if not m:
            continue
        char_id = m.group("char")
        kind = "guide" if m.group("kind") == "article" else "transcript"
        md = f.read_text(encoding="utf-8")
        vol = m.group("vol") or SEC.dominant_vol(md)
        if vol not in ctx["vols"]:
            vol = SEC.dominant_vol(md)
        c = ctx["char_by_id"].get(char_id)
        char_name = c["name"] if c else site_arch.display_name("", char_id)
        out = f"story/v/{vol}/{char_id}.{'guide' if kind == 'guide' else 'transcript'}.html"
        ctx["vol_docs"][f"{char_id}.{vol}.{kind}"] = {
            "char_id": char_id, "char_name": char_name, "vol": vol,
            "kind": kind, "out": out,
            "title": f"{char_name} — {site_arch.volume_short(vol)} {kind}"}
        ctx["pathmap"][f"drafts/people/{f.name}"] = out


def build_pathmap(ctx):
    for f in sorted(DOSSIERS.rglob("*.md")):
        rel = f.relative_to(DOSSIERS).as_posix()
        key = f"dossiers/{rel}"
        parts = rel.split("/")
        if parts[0] == "main":
            ctx["pathmap"][key] = (
                "people/index.html" if parts[-1] == "index.md"
                else f"people/{parts[-1][:-3]}.html")
        elif parts[0] == "mid":
            ctx["pathmap"][key] = (
                "people/index.html" if parts[-1] == "index.md"
                else f"people/{parts[-1][:-3]}.html")
        elif parts[0] == "exams":
            if parts[-1] == "index.md":
                ctx["pathmap"][key] = "school/index.html"
            elif parts[-1] == "chronology.md":
                ctx["pathmap"][key] = "school/chronology.html"
            else:
                ctx["pathmap"][key] = f"school/exam/{parts[-1][:-3]}.html"
        elif parts[0] == "systems":
            ctx["pathmap"][key] = (
                "school/index.html" if parts[-1] == "index.md"
                else f"school/system/{parts[-1][:-3]}.html")
        elif parts[0] == "world":
            ctx["pathmap"][key] = (
                "world/index.html" if parts[-1] == "index.md"
                else f"world/{parts[-1][:-3]}.html")
        elif rel == "background.md":
            ctx["pathmap"][key] = "people/index.html"
        else:
            ctx["pathmap"][key] = f"appendix/index.html"
    for extra in ["index.html", "people/index.html", "story/index.html",
                  "school/index.html", "world/index.html",
                  "topics/index.html", "guides/index.html",
                  "appendix/index.html"]:
        ctx["pathmap"].setdefault(extra, extra)


def collect_metas(ctx):
    """Person, exam, system and place page metas."""
    metas = []
    for f in sorted((DOSSIERS / "main").glob("*.md")):
        if f.name == "index.md":
            continue
        cid = f.stem
        metas.append({"kind": "person", "char_id": cid,
                      "src": str(f), "src_rel": f"dossiers/main/{f.name}",
                      "out": f"people/{cid}.html",
                      "title": ctx["char_by_id"].get(cid, {}).get("name", cid)})
    for g in site_data_groups():
        for f in sorted((DOSSIERS / "mid" / g).glob("*.md")):
            if f.name == "index.md":
                continue
            cid = f.stem
            metas.append({"kind": "person", "char_id": cid,
                          "src": str(f),
                          "src_rel": f"dossiers/mid/{g}/{f.name}",
                          "out": f"people/{cid}.html",
                          "title": ctx["char_by_id"].get(cid, {}).get("name", cid)})
    for row in ctx["exam_rows"]:
        src = DOSSIERS / "exams" / f"{row['id']}.md"
        if not src.exists():
            continue
        metas.append({"kind": "exam", "row": row, "src": str(src),
                      "src_rel": f"dossiers/exams/{src.name}",
                      "out": f"school/exam/{row['id']}.html",
                      "title": row["name"]})
    chron = DOSSIERS / "exams" / "chronology.md"
    if chron.exists():
        metas.append({"kind": "chronology", "src": str(chron),
                      "src_rel": "dossiers/exams/chronology.md",
                      "out": "school/chronology.html",
                      "title": "Exam chronology"})
    for row in ctx["system_rows"]:
        src = DOSSIERS / "systems" / f"{row['id']}.md"
        if not src.exists():
            continue
        metas.append({"kind": "system", "row": row, "src": str(src),
                      "src_rel": f"dossiers/systems/{src.name}",
                      "out": f"school/system/{row['id']}.html",
                      "title": row["name"]})
    for row in ctx["loc_rows"]:
        src = DOSSIERS / "world" / f"{row['id']}.md"
        if not src.exists():
            continue
        metas.append({"kind": "place", "row": row, "src": str(src),
                      "src_rel": f"dossiers/world/{src.name}",
                      "out": f"world/{row['id']}.html", "title": row["name"]})
    return metas


def site_data_groups():
    d = DOSSIERS / "mid"
    return [p.name for p in sorted(d.iterdir()) if p.is_dir()]


def render_dossier_meta(ctx, meta):
    """Chronology keeps its authored body and joins the school section."""
    md = SEC.reword(Path(meta["src"]).read_text(encoding="utf-8"))
    body, headings = render(md)
    body = S.resolve_links(body, meta["src_rel"], ctx["pathmap"], meta["out"])
    body = S.chipify(body, ctx["lookup"])
    body = SEC.section_scope(body, ctx["vols"])
    rail = SEC.school_rail(ctx)
    crumb = [("Home", "index.html"),
             ("Exams & School", "school/index.html"), (meta["title"], None)]
    return ctx["page"](meta["title"], "school", body, crumb, out=meta["out"],
                       rail=rail, headings=headings, kicker="Reference",
                       tagline_label="Exams & School", scope=ctx["scope"])


def build_ctx(con, stats):
    ctx = {
        "con": con,
        "vols": site_arch.load_volumes(con),
        "chars": D.characters(con),
        "exam_pack": D.exams(con),
        "loc_rows": D.locations(con),
        "system_rows": D.systems(con),
        "timeline": D.status_timeline(con),
        "relations": D.relations(con),
        "claims": D.claims(con),
        "walk": D.walk_state(),
        "pathmap": {},
        "vol_docs": {},
        "stats": stats,
        "minor_letters": [],
    }
    ctx["char_by_id"] = {c["id"]: c for c in ctx["chars"]}
    ctx["exam_rows"] = ctx["exam_pack"]["list"]
    ctx["exam_list"] = ctx["exam_rows"]
    ctx["system_list"] = ctx["system_rows"]
    ctx["loc_list"] = ctx["loc_rows"]
    ctx["exams_by_vol"] = ctx["exam_pack"]["by_vol"]
    ctx["exam_name"] = {e["id"]: e["name"] for e in ctx["exam_rows"]}
    ctx["claims_by_char"] = {}
    for cl in ctx["claims"]:
        ctx["claims_by_char"].setdefault(cl["char_id"], []).append(cl)
    ctx["vol_list"] = [ctx["vols"][k] for k in ctx["vols"]]
    ctx["scope"] = scope_options(ctx)
    ctx["lookup"] = memo_lookup(con)
    ctx["page"] = page_factory(ctx)
    ctx["vol_titles"] = {}
    return ctx


def write(pages, ctx):
    written = 0
    for out, text in pages:
        p = SITE / out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        written += 1
        ctx["pathmap"].setdefault(out, out)
    return written


SEARCH_SECTION_LABEL = {
    "home": "Home", "people": "People", "story": "Story",
    "school": "Exams & School", "world": "World", "topics": "Topic",
    "guides": "Guide", "appendix": "Appendix",
}


def search_records():
    records = []
    for f in sorted(SITE.rglob("*.html")):
        if f.parts[-3:-2] == ("pdfs",) or "pdfs" in f.parts:
            continue
        rel = f.relative_to(SITE).as_posix()
        text = f.read_text(encoding="utf-8")
        m = re.search(r"<title>(.*?) · COTE Knowledge Base</title>", text, re.S)
        title = html.unescape(m.group(1)).strip() if m else rel
        sm = re.search(r'data-section="([^"]+)"', text)
        section = SEARCH_SECTION_LABEL.get(sm.group(1) if sm else "", "")
        main = re.search(r"<main class=\"content\">(.*?)</main>", text, re.S)
        body = main.group(1) if main else text
        chunks = re.split(r'(?=<h[23] id="[^"]+">)', body)
        for chunk in chunks:
            hm = re.match(r'<h[23] id="([^"]+)">(.*?)</h[23]>', chunk, re.S)
            if hm:
                heading = TEXT_JUNK_RE.sub(" ", TAG_RE.sub("", hm.group(2))).strip()
                anchor = f"#{hm.group(1)}"
                payload = chunk[hm.end():]
            else:
                heading, anchor, payload = title, "", chunk
            plain = TEXT_JUNK_RE.sub(" ", TAG_RE.sub(" ", payload)).strip()
            plain = html.unescape(plain)
            if anchor and len(plain) < 24:
                continue
            records.append({
                "u": f"{rel}{anchor}", "t": title, "s": heading,
                "k": section, "x": plain[:900],
            })
    return records


SEARCH_JS = r"""(function () {
  var input = document.getElementById("q");
  var box = document.getElementById("results");
  if (!input || !box || typeof SEARCH_INDEX === "undefined") return;
  var root = document.body.getAttribute("data-root") || "";
  var sel = -1, hits = [];
  var norm = function (s) {
    return s.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "");
  };
  var tokens = function (s) { return norm(s).replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter(Boolean); };
  var pool = SEARCH_INDEX.map(function (r) {
    return { r: r, hay: norm([r.t, r.s, r.k || "", r.x].join(" ")), toks: tokens(r.t + " " + r.s) };
  });
  function score(item, qtoks) {
    var hay = item.hay, s = 0, all = true;
    for (var i = 0; i < qtoks.length; i++) {
      var t = qtoks[i];
      if (hay.indexOf(t) === -1) { all = false; continue; }
      s += 1;
      if (item.toks.indexOf(t) !== -1) s += 3;
    }
    if (!all && qtoks.length > 1) return 0;
    if (all) s += 4;
    return s;
  }
  function run(q) {
    var qtoks = tokens(q);
    if (!qtoks.length) return [];
    var out = [];
    for (var i = 0; i < pool.length; i++) {
      var sc = score(pool[i], qtoks);
      if (sc > 0) out.push([sc, pool[i]]);
    }
    out.sort(function (a, b) { return b[0] - a[0]; });
    return out.slice(0, 24).map(function (p) { return p[1]; });
  }
  function snippet(item, qtoks) {
    var x = item.r.x || "";
    var low = norm(x);
    for (var i = 0; i < qtoks.length; i++) {
      var at = low.indexOf(qtoks[i]);
      if (at > -1) {
        var s = Math.max(0, at - 60), e = Math.min(x.length, at + 180);
        return (s ? "…" : "") + x.slice(s, e) + (e < x.length ? "…" : "");
      }
    }
    return x.slice(0, 200);
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function draw(q) {
    hits = run(q); sel = -1;
    if (!q) { box.hidden = true; box.innerHTML = ""; return; }
    if (!hits.length) {
      box.hidden = false;
      box.innerHTML = '<div class="none">Nothing matches “' + esc(q) + '”.</div>';
      return;
    }
    var qtoks = tokens(q);
    var out = hits.map(function (item, i) {
      var r = item.r;
      return '<a href="' + root + r.u + '" class="' + (i === sel ? "sel" : "") + '">'
        + '<div class="rt">' + esc(r.t) + '</div>'
        + (r.s && r.s !== r.t ? '<div class="rs">' + esc(r.k ? r.k + " · " : "") + esc(r.s) + '</div>' : '<div class="rs">' + esc(r.k || "") + '</div>')
        + '<div class="rx">' + esc(snippet(item, qtoks)) + '</div></a>';
    });
    box.hidden = false; box.innerHTML = out.join("");
  }
  input.addEventListener("input", function () { draw(input.value.trim()); });
  input.addEventListener("focus", function () { if (input.value) draw(input.value.trim()); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      var links = box.querySelectorAll("a"); if (!links.length) return;
      sel = e.key === "ArrowDown" ? Math.min(sel + 1, links.length - 1) : Math.max(sel - 1, 0);
      for (var i = 0; i < links.length; i++) links[i].className = i === sel ? "sel" : "";
      links[sel].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && sel >= 0) {
      var l = box.querySelectorAll("a")[sel]; if (l) window.location.href = l.href;
    } else if (e.key === "Escape") { box.hidden = true; input.blur(); }
  });
  document.addEventListener("click", function (e) {
    if (!box.contains(e.target) && e.target !== input) box.hidden = true;
  });
})();"""

README = """COTE Knowledge Base — static site
================================

Built by:  python3 kb/build_share_site.py
Serve:     open index.html (no server needed), or publish the folder.

Sections: People · Story · Exams & School · World & Places · Topics ·
Start here · Appendix.

Every quotation is verbatim from the translated light novels and carries a
volume + page citation (y1v1 p.247 = Year 1, Volume 1, page 247).
"""

HREF_RE = re.compile(r'href="([^"]+)"')


def print_links(text, out_path, anchor_by_path):
    """Rewrite links for a print bundle. A link to an entity that is inside
    this same bundle becomes an in-document anchor (that is the point of a
    bundle); anything else becomes an absolute-from-print-dir path back into
    the site tree, so a printed page still cites real pages."""
    src_dir = posixpath.dirname(out_path) or "."

    def rep(m):
        u = m.group(1)
        if u.startswith(("#", "http", "mailto:", "data:")):
            return f'href="{u}"'
        path, _, frag = u.partition("#")
        if not path or path.startswith("assets"):
            return f'href="{u}"'
        if path.startswith("../"):
            site_path = posixpath.normpath(posixpath.join(src_dir, path))
        elif path.startswith(site_arch.SITE_ROOTS):
            site_path = posixpath.normpath(path)
        else:
            site_path = posixpath.normpath(posixpath.join(src_dir, path))
        hid = anchor_by_path.get(site_path)
        if hid:
            return f'href="{hid}"' if not frag else f'href="{hid}"'
        return f'href="../site/{site_path}{("#" + frag) if frag else ""}"'

    return HREF_RE.sub(rep, text)


def print_doc(label, entries, out_name, cover):
    body = []
    toc = []
    anchor_by_path = {out: f"#{slug(title)}" for title, _b, out in entries}
    for title, html_body, out in entries:
        hid = slug(title)
        toc.append(f'<li><a href="#{hid}">{html.escape(title)}</a></li>')
        html_body = print_links(html_body, out, anchor_by_path)
        body.append(f'<section class="print-entity" id="{hid}">{html_body}</section>')
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{html.escape(label)} · COTE Knowledge Base</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body data-root="" data-section="print" class="print-doc">
<div class="layout"><main class="content">
<div class="print-cover"><h1>{html.escape(label)}</h1>
<p>{html.escape(cover)}</p><p>COTE Knowledge Base</p></div>
<div class="print-toc"><h2>Contents</h2><ul>{"".join(toc)}</ul></div>
{"".join(body)}
</main></div></body></html>"""
    (PRINT / out_name).write_text(doc, encoding="utf-8")
    return doc


def entities_from(ctx, pages):
    """(title, body, out) triples for the print bundles."""
    out = []
    for path, text in pages:
        m = re.search(r'<main class="content">(.*?)</main>', text, re.S)
        if not m:
            continue
        inner = m.group(1)
        inner = re.sub(r'<nav class="crumbs".*?</nav>', "", inner, flags=re.S)
        tm = re.search(r"<title>(.*?) · COTE", text, re.S)
        title = html.unescape(tm.group(1)).strip() if tm else path
        out.append((title, inner, path))
    return out


def section_of_path(path):
    return path.split("/")[0] if "/" in path else path


def make_zip():
    SITE_ZIP = ROOT / "share" / "cote-kb-share.zip"
    if SITE_ZIP.exists():
        SITE_ZIP.unlink()
    with zipfile.ZipFile(SITE_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(SITE.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(SITE.parent).as_posix())
    print(f"zip: {SITE_ZIP} ({SITE_ZIP.stat().st_size:,} bytes)")


def make_docs():
    docs = ROOT / "docs"
    if docs.exists():
        shutil.rmtree(docs)
    shutil.copytree(SITE, docs)
    n = sum(1 for _ in docs.rglob("*") if _.is_file())
    print(f"docs: {n} files → docs/ (md5 {md5_tree(docs)})")


def make_pdfs():
    pdf_bin = (shutil.which("chromium") or shutil.which("chromium-browser")
               or shutil.which("google-chrome"))
    if not pdf_bin:
        print("pdfs: chromium not found — skipped", file=sys.stderr)
        return 0
    pdf_dir = SITE / "pdfs"
    pdf_dir.mkdir(exist_ok=True)
    for src in sorted(PRINT.glob("*.html")):
        out = pdf_dir / f"{src.stem}.pdf"
        subprocess.run([pdf_bin, "--headless", "--disable-gpu", "--no-sandbox",
                        "--disable-dev-shm-usage", f"--print-to-pdf={out}",
                        str(src)], check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    print(f"pdfs: {len(list(pdf_dir.glob('*.pdf')))} → share/site/pdfs/")
    return len(list(pdf_dir.glob("*.pdf")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md5", action="store_true")
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--docs", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
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
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    PRINT.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    people = D.characters(con)
    walked = sum(1 for s in D.walk_state().values() if s.get("complete"))
    stats = {
        "chars": len(people),
        "vols": con.execute("SELECT count(*) FROM volumes").fetchone()[0],
        "exams": con.execute("SELECT count(*) FROM exams").fetchone()[0],
        "places": con.execute("SELECT count(*) FROM locations").fetchone()[0],
        "systems": con.execute("SELECT count(*) FROM systems").fetchone()[0],
        "quotes": con.execute("SELECT count(*) FROM quotes").fetchone()[0],
        "walked": walked,
    }

    ctx = build_ctx(con, stats)
    build_pathmap(ctx)
    SEC.plan_minor(ctx)
    plan_vol_docs(ctx)
    metas = collect_metas(ctx)
    for m in metas:
        ctx["pathmap"][m["src_rel"]] = m["out"]

    pages = []
    home = SEC.home(ctx)
    pages.append(("index.html", home))
    pages.append(("people/index.html", SEC.people_index(ctx)))
    pages.extend(SEC.minor_pages(ctx))
    for m in metas:
        if m["kind"] == "person":
            pages.append(SEC.person_page(ctx, m))
        elif m["kind"] == "exam":
            pages.append(SEC.exam_page(ctx, m))
        elif m["kind"] == "system":
            pages.append(SEC.system_page(ctx, m))
        elif m["kind"] == "place":
            pages.append(SEC.place_page(ctx, m))
        elif m["kind"] == "chronology":
            pages.append((m["out"], render_dossier_meta(ctx, m)))
    pages.append(("story/index.html", SEC.story_index(ctx)))
    for year in (0, 1, 2, 3):
        if any(v["year"] == year for v in ctx["vol_list"]):
            pages.append((f"story/y{year}.html", SEC.year_page(ctx, year)))
    for v in ctx["vol_list"]:
        pages.append(SEC.volume_page(ctx, v))
    pages.extend(TOP.build_vol_docs(ctx))
    pages.append(("school/index.html", SEC.school_index(ctx)))
    pages.append(("world/index.html", SEC.world_index(ctx)))
    pages.append(("topics/index.html", TOP.topics_index(ctx)))
    for topic in TOP.TOPICS:
        pages.append(TOP.TOPIC_BUILDERS[topic["id"]](ctx))
    pages.append(("guides/index.html", TOP.guides_index(ctx)))
    pages.append(TOP.writers_page(ctx))
    pages.append(TOP.powerscalers_page(ctx))
    pages.append(TOP.moment_page(ctx))
    pages.append(("appendix/index.html", TOP.appendix_index(ctx)))
    pages.append(TOP.citations_page(ctx))
    pages.append(TOP.coverage_page(ctx))
    pages.append(TOP.downloads_page(ctx))

    written = write(pages, ctx)

    (SITE / "assets" / "style.css").write_text(
        (ASSETS / "style.css").read_text(encoding="utf-8"), encoding="utf-8")
    (SITE / "assets" / "shell.js").write_text(
        (ASSETS / "shell.js").read_text(encoding="utf-8"), encoding="utf-8")
    (SITE / "assets" / "search.js").write_text(SEARCH_JS, encoding="utf-8")
    records = search_records()
    (SITE / "assets" / "search-index.js").write_text(
        "const SEARCH_INDEX = " + json.dumps(
            records, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    (SITE / "README.txt").write_text(README, encoding="utf-8")

    # print bundles are standalone documents (and the source of the PDFs), so
    # they get their own copy of the stylesheet rather than a web-only link
    (PRINT / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(SITE / "assets" / "style.css", PRINT / "assets" / "style.css")

    ents = entities_from(ctx, pages)
    by_sec = {}
    for title, body, out in ents:
        by_sec.setdefault(section_of_path(out), []).append((title, body, out))
    bundles = [
        ("People", "people", "Every character profile"),
        ("Story", "story", "Volumes, guides and scene transcripts"),
        ("Exams & School", "school", "Exams, systems and the chronology"),
        ("World & Places", "world", "Every location"),
        ("Topics", "topics", "Question pages"),
        ("Start here", "guides", "Reader doors and the appendix"),
    ]
    made = 0
    for label, sec, cover in bundles:
        rows = sorted(by_sec.get(sec, []), key=lambda r: r[2])
        if not rows:
            continue
        print_doc(label, rows, f"{sec}.html", cover)
        made += 1

    pdfs = 0 if args.no_pdf else make_pdfs()
    con.close()
    print(f"build_share_site: {written} pages + {len(records)} search records "
          f"+ {made} print bundles + {pdfs} pdfs")
    return 0


if __name__ == "__main__":
    sys.exit(main())

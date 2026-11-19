#!/usr/bin/env python3
"""Build the static site into docs/ from content/ and ledgers/.

    python3 gen/build.py            # writes docs/
    python3 gen/build.py --out DIR  # somewhere else

No database, no corpus. Same inputs give byte-identical output.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import model as M  # noqa: E402
import render as R  # noqa: E402
from model import fold  # noqa: E402
from render import (Page, card, cards_block, crumbs, dot, ent, esc, item, path, pg, pgify, row_item,  # noqa: E402
                    shell, toc)

ASSETS = Path(__file__).parent / "assets"
PAGES = {}
TIER = {"main": "Main", "supporting": "Supporting", "minor": "Minor"}


def add(rel, **kw):
    P = Page(rel)
    PAGES[rel] = shell(P, **kw)


def posts(c):
    return ", ".join(R.ROLE.get(r, r.replace("-", " ").title()) for r in c["roles"] if not r.startswith("class-"))


def yname(y):
    return "Side stories" if y == 0 else f"Year {y}"


def facts(rows):
    return ('<dl class="facts">' + "".join(
        f"<div><dt>{esc(k)}</dt><dd>{v}</dd></div>" for k, v in rows if v) + "</dl>")


def scope_bar(years):
    if len(years) < 2:
        return ""
    return ('<div class="chips scope" data-pagescope aria-label="Scope"><button type="button" class="on" data-y="">All years</button>'
            + "".join(f'<button type="button" data-y="{y}">{yname(y)}</button>' for y in years) + "</div>")


def vol_runs(P, vols_named, scenes_by_vol):
    """One line per read volume; unread neighbours collapse into one range."""
    m = R.m
    out, run = [], []

    def flush():
        if run:
            a, b = run[0], run[-1]
            span = a["short"] if a is b else f'{a["short"]}–{b["short"]}'
            out.append(f'<li class="run" data-y="{a["year"]}" data-o="{a["ord"]}">{dot("stub")} '
                       f'{esc(span)} <span class="n">named, not read yet</span></li>')
            run.clear()
    for v in vols_named:
        n = scenes_by_vol.get(v["id"], 0)
        if n:
            flush()
            out.append(f'<li data-y="{v["year"]}" data-o="{v["ord"]}">{dot("partial")} {ent(P, "volumes", v["id"])} '
                       f'<span class="n">{n} scene{"s" if n != 1 else ""} read</span></li>')
        else:
            if run and run[-1]["year"] != v["year"]:
                flush()
            run.append(v)
    flush()
    return f'<ul class="plain vols">{"".join(out)}</ul>'


# ------------------------------------------------------------------- home
def build_home():
    m = R.m
    P = Page("index.html")
    done = sum(1 for v in m.vols if m.vol_state(v["id"]) != "stub")
    tasks = [("Look up a character", "Who they are, what they did, and the scenes they are in.",
              "people/index.html", f"People · {len(m.chars)}"),
             ("Read a volume in order", "Chapter by chapter, with the scenes read from each.",
              "story/index.html", f"Story · {len(m.vols)} volumes"),
             ("Check how an exam worked", "Rules, how it ran, and the result.",
              "school/index.html", f"Exams & School · {len(m.exams)} exams"),
             ("Find where something happened", "Every named place and the scenes set there.",
              "world/index.html", f"World & Places · {len(m.places)}"),
             ("Check a claim", "Who knew what, expulsions, points, relationships, results.",
              "topics/index.html", f"Topics · {len(m.topics)}")]
    lis = "".join(f'<li><a class="task" href="{esc(to)}"><strong>{esc(a)}</strong><span>{esc(b)}</span>'
                  f'<span class="n">{esc(c)}</span></a></li>' for a, b, to, c in tasks)
    body = f"""<h2>What do you want to do?</h2><ul class="tasks">{lis}</ul>
<h2>How much is covered</h2>
<div class="bar" role="img" aria-label="{done} of {len(m.vols)} volumes read"><span style="width:{done / len(m.vols) * 100:.1f}%"></span></div>
<p>{done} of {len(m.vols)} volumes are read line by line. Every volume is still listed, with the names and exams it
mentions. <a href="about/coverage.html">See which volumes</a></p>
<h2>Reading a page</h2>
<ul class="plain legend"><li><span class="pg">p.47</span> printed page in the book; not a link</li>
<li>{dot("partial")} read line by line &nbsp; {dot("stub")} names and pages only</li>
<li><span class="mlabel">Spoken</span> a line from the book &nbsp; <span class="mlabel">Inner voice</span> a thought &nbsp; <span class="mlabel">What happens</span> an action</li>
<li>Read up to (top right) hides scenes from later volumes</li></ul>"""
    PAGES["index.html"] = shell(P, "Classroom of the Elite Knowledge Base", body, [],
                                lede="Notes from the novels, with a page number on every claim.", home=True)


# ----------------------------------------------------------------- people
def yrs_text(c):
    ys = sorted({R.m.vol[v]["year"] for v in c["volumes"]}, key=lambda y: y or 9)
    return " · ".join("Side" if y == 0 else f"Y{y}" for y in ys)


def dir_row(P, c):
    m = R.m
    ys = sorted({m.vol[v]["year"] for v in c["volumes"]}, key=lambda y: y or 9)
    t = c["tier"]
    roles = posts(c)
    attrs = (f'id="{c["id"]}" class="row" data-n="{esc(fold(c["name"] + " " + " ".join(c["aliases"])))}" '
             f'data-ta="{t["all"]}" data-t1="{t["1"]}" data-t2="{t["2"]}" data-t3="{t["3"]}" '
             f'data-y="{" ".join(map(str, ys))}" data-p="{1 if c["has_page"] else 0}" data-c="{c["class"]}" '
             f'data-r="{" ".join(c["roles"])}" data-l="{esc(fold(c["sort"])[:1].upper())}"')
    cells = (f'<span class="cls">{c["class"] or "—"}</span><span class="role">{esc(roles) or "—"}</span>'
             f'<span class="yrs">{yrs_text(c) or "—"}</span>')
    if c["has_page"]:
        return f'<li {attrs}>{dot("partial")}<a href="{c["id"]}.html">{esc(c["name"])}</a>{cells}</li>'
    named = " · ".join(ent(P, "volumes", v, m.vol[v]["short"]) for v in c["volumes"]) or "no volume recorded"
    also = f'<p class="n">Also written: {esc(", ".join(c["aliases"]))}</p>' if c["aliases"] else ""
    return (f'<li {attrs}><details><summary>{dot("stub")}<span class="nm">{esc(c["name"])}</span>{cells}</summary>'
            f'<p class="n">Named in: {named}</p>{also}</details></li>')


def build_people_index():
    m = R.m
    P = Page("people/index.html")
    chars = sorted(m.chars.values(), key=lambda c: (fold(c["sort"]), fold(c["name"])))
    groups = {k: [c for c in chars if c["tier"]["all"] == k] for k in ("main", "supporting", "minor")}
    classes = sorted({c["class"] for c in chars if c["class"]})
    roles = sorted({r for c in chars for r in c["roles"] if not r.startswith("class-")})
    letters = sorted({fold(c["sort"])[:1].upper() for c in chars if fold(c["sort"])})
    ctrl = f"""<div class="panel dirpanel"><input id="dq" type="search" placeholder="Search a name or nickname" aria-label="Search people">
<div class="chips scope" data-dirscope><button type="button" class="on" data-s="all">All years</button><button type="button" data-s="1">Year 1</button><button type="button" data-s="2">Year 2</button><button type="button" data-s="3">Year 3</button></div>
<label>Class <select id="dc"><option value="">any</option>{"".join(f'<option>{c}</option>' for c in classes)}</select></label>
<label>Role <select id="dr"><option value="">any</option>{"".join(f'<option value="{r}">{esc(R.ROLE.get(r, r))}</option>' for r in roles)}</select></label>
<label class="chk"><input id="dp" type="checkbox"> Only characters with a page</label></div>
<div class="alpha" aria-label="Jump to letter">{"".join(f'<button type="button" data-l="{l}">{l}</button>' for l in letters)}</div>"""
    secs = []
    for k, label in (("main", "Main characters"), ("supporting", "Supporting characters"), ("minor", "Minor characters")):
        secs.append(f'<section class="tier" data-tier="{k}"><h2 id="{k}">{label} <span class="n">(<b class="ct">{len(groups[k])}</b>)</span></h2>'
                    f'<ul class="rows dir">{"".join(dir_row(P, c) for c in groups[k])}</ul></section>')
    body = (ctrl + '<p class="count" id="dcount"></p>' + "".join(secs)
            + '<p class="n legend">Main: named in half the volumes or more. Supporting: a fifth or more. Minor: fewer. '
              'Counted per year when a year is chosen. A page exists once enough scenes have been read.</p>')
    add("people/index.html", h1="People", body=body, trail=[("People", "people/index.html")],
        kicker="", lede=f"{len(chars)} characters. Click a name for the page; names without a page open in place.")


def threads_block(P, cid):
    """Themed evidence for one character: ledger rows grouped under shared thread headings."""
    m = R.m
    kids = defaultdict(list)
    for t in m.threads:
        kids[t.get("parent") or ""].append(t)

    def collect(t):
        pat = re.compile(t["pattern"], re.I) if t.get("pattern") else None
        marks = {x for x in (t.get("markers") or "").split(",") if x}
        if (not pat and not marks) or (t.get("char") and t["char"] != cid):
            return []
        out = []
        for s in m.scenes_of("people", cid):
            for r in s["rows"]:
                if (not marks or r["m"] in marks) and (pat is None or pat.search(r["text"])):
                    out.append((s, r))
        return out

    def node(t):
        rows = collect(t)
        sub = [x for x in (node(c) for c in kids.get(t["id"], [])) if x]
        if not rows and not sub:
            return None
        return {"t": t, "rows": rows, "sub": sub}

    roots = [x for x in (node(t) for t in kids.get("", [])) if x]
    if not roots:
        return ""

    def scene_articles(rows):
        by_sc = {}
        for s, r in rows:
            by_sc.setdefault(s["id"], (s, []))[1].append(r)
        arts = []
        for s, rs in by_sc.values():
            lis = "".join(
                f'<li><span class="mlabel">{esc(M.MARKERS[r["m"]])}</span> {esc(r["text"])}{pg(r["pg"])}</li>'
                for r in rs)
            arts.append(
                f'<article class="card row"><p class="src">'
                f'<span class="n">{esc(m.vol[s["vol"]]["short"])} · </span>'
                f'<a href="#{s["id"]}">{esc(s["title"])}</a>'
                f'<span class="n"> · {esc(s["pages"])}</span></p>'
                f'<ul class="rows">{lis}</ul></article>')
        return "".join(arts)

    def node_html(n, lvl):
        lvl = min(lvl, 6)
        inner = scene_articles(n["rows"]) + "".join(node_html(c, lvl + 1) for c in n["sub"])
        return (f'<section class="threadgrp"><h{lvl}>{esc(n["t"]["title"])}</h{lvl}>'
                f'{inner}</section>')

    return '<h2 id="threads">Threads</h2>' + "".join(node_html(r, 3) for r in roots)


def build_character(c):
    m = R.m
    cid = c["id"]
    rel = f"people/{cid}.html"
    P = Page(rel)
    sc = m.scenes_of("people", cid)
    by_vol = Counter(s["vol"] for s in sc)
    named = [m.vol[v] for v in c["volumes"]]
    years = sorted({v["year"] for v in named}, key=lambda y: y or 9)
    first = sc[0] if sc else None
    lead = (f"{esc(c['name'])} is named in {len(named)} of {len(m.vols)} volumes. "
            f"{len(sc)} scenes from {len(c['read_vols'])} volume{'s' if len(c['read_vols']) != 1 else ''} "
            f"have been read line by line, with a page for every line.")
    roles = posts(c)
    info = facts([("Class", esc(c["class"])), ("Posts", esc(roles)),
                  ("Appears in", " · ".join(yname(y) for y in years)),
                  ("Named in", plural(len(named), "volume")),
                  ("Read so far", f"{len(sc)} scenes, {c['lines']} quoted lines"),
                  ("First read scene", f'{ent(P, "volumes", first["vol"])} <span class="pg">{esc(first["pages"])}</span>' if first else "")])
    items = [item(P, s, ("people", cid)) for s in sc]
    rels = m.relations(cid)
    rel_html = "".join(
        f'<li>{ent(P, "people", t)} <span class="n">{n} note{"s" if n != 1 else ""}</span> '
        f'<button type="button" class="chipbtn" data-with="{t}">Scenes together</button></li>' for t, n in rels)
    ex = Counter(e for s in sc for e in dict.fromkeys(s["exams"]))
    pl = Counter(p for s in sc for p in dict.fromkeys(s["places"]))
    related = "".join(f"<li>{ent(P, 'exams', e)}</li>" for e in ex) + "".join(f"<li>{ent(P, 'places', p)}</li>" for p in pl)
    aliases = ", ".join(c["aliases"])
    th = threads_block(P, cid)
    toc_items = ([("threads", "Threads")] if th else []) + [
        ("scenes", "Scenes"), ("volumes", "Volume by volume"),
        ("relationships", "Relationships"), ("names", "Names")]
    body = (scope_bar(years) + info
            + toc(toc_items) + th
            + '<h2 id="scenes">Scenes</h2>' + cards_block(P, items, with_id=cid)
            + '<h2 id="volumes">Volume by volume</h2>' + vol_runs(P, named, by_vol)
            + '<h2 id="relationships">Relationships</h2>'
            + (f'<ul class="plain">{rel_html}</ul>' if rel_html else '<p class="n">No relationship notes read yet.</p>')
            + '<h2 id="names">Names</h2>'
            + facts([("Shown as", esc(c["name"])), ("Also written", esc(aliases))])
            + (f'<h2 id="related">Exams and places in these scenes</h2><ul class="plain">{related}</ul>' if related else ""))
    state = "complete" if c["scenes"] and all(m.vol_state(v) == "complete" for v in c["volumes"]) else "partial"
    add(rel, h1=c["name"], body=body, trail=[("People", "people/index.html"), (c["name"], rel)],
        kicker=f"Character · {TIER.get(c['tier']['all'], 'Minor')} · {state}", lede=lead)


# ------------------------------------------------------------------ story
def vol_rows(P, vols):
    m = R.m
    lis = []
    for v in vols:
        n = len(m.scenes_in(v["id"]))
        st = m.vol_state(v["id"])
        lis.append(f'<li data-o="{v["ord"]}" data-y="{v["year"]}">{dot(st)} {ent(P, "volumes", v["id"])} '
                   f'<span class="n">{f"{n} scenes read" if n else "named only"}</span></li>')
    return f'<ul class="plain vols">{"".join(lis)}</ul>'


def build_story():
    m = R.m
    P = Page("story/index.html")
    body = ""
    for y in (1, 2, 3, 0):
        vs = [v for v in m.vols if v["year"] == y]
        body += f'<h2 id="y{y}"><a href="y{y}.html">{yname(y)}</a> <span class="n">{len(vs)} volume{"s" if len(vs) != 1 else ""}</span></h2>' + vol_rows(P, vs)
    add("story/index.html", h1="Story", body=body, trail=[("Story", "story/index.html")],
        lede="Every volume in reading order. Filled dots have been read line by line.")
    for y in (0, 1, 2, 3):
        P = Page(f"story/y{y}.html")
        vs = [v for v in m.vols if v["year"] == y]
        add(f"story/y{y}.html", h1=yname(y), body=vol_rows(P, vs), kicker="Story",
            trail=[("Story", "story/index.html"), (yname(y), f"story/y{y}.html")],
            lede=f"{len(vs)} volume{'s' if len(vs) != 1 else ''}.")


def build_volume(v):
    m = R.m
    vid = v["id"]
    rel = f"story/v/{vid}/index.html"
    P = Page(rel)
    sc = m.scenes_in(vid)
    led = m.vol_ledger.get(vid)
    i = m.vols.index(v)
    prev_, next_ = (m.vols[i - 1] if i else None), (m.vols[i + 1] if i + 1 < len(m.vols) else None)
    state = m.vol_state(vid)
    if led and led["chapters"]:
        lead = (f"{len([c for c in led['chapters']])} chapters read line by line"
                f"{f', {len(sc)} scenes' if sc else ''}. Every claim has a page.")
    else:
        lead = "Not read line by line yet. This page lists what the volume names; scenes appear once it is read."
    info = facts([("Year", esc(yname(v["year"]))), ("Order", f"{v['ord']} of {len(m.vols)}"),
                  ("Status", {"complete": "Read line by line", "partial": "Partly read", "stub": "Names and pages only"}[state]),
                  ("Before", ent(P, "volumes", prev_["id"]) if prev_ else ""), ("Next", ent(P, "volumes", next_["id"]) if next_ else "")])
    body = info
    sections = []
    if led and led["chapters"]:
        ch_html = []
        for k, ch in enumerate(led["chapters"]):
            inner = ""
            for sec in ch["secs"]:
                if sec["items"]:
                    lis = []
                    for t in sec["items"]:
                        if sec["key"] == "Narrative beats":
                            pm = re.match(r'^(pp?\.\s*[\d\u2013\u2014\-]+):\s*(.*)$', t, re.S)
                            if pm:
                                pref = pm.group(1).strip()
                                beats = [b.strip().rstrip(';').strip() for b in pm.group(2).split(';') if b.strip()]
                                sub = "".join(f"<li>{pgify(esc(b))}</li>" for b in beats)
                                rendered = f'<span class="pg">{esc(pref)}</span>.<ul class="beats">{sub}</ul>'
                            else:
                                rendered = pgify(esc(t)).replace("; ", ";<br>\n  ")
                        else:
                            rendered = pgify(esc(t))
                        lis.append(f"<li>{rendered}</li>")
                    inner += f'<h4>{pgify(esc(sec["key"]))}</h4><ul>{"".join(lis)}</ul>'
                    if sec["text"]:
                        inner = f'<p>{pgify(esc(sec["text"]))}</p>' + inner
                else:
                    inner += f'<p><strong>{pgify(esc(sec["key"]))}.</strong> {pgify(esc(sec["text"]))}</p>'
            ch_html.append(f'<details class="chap"{" open" if k == 0 else ""}><summary>{esc(ch["title"])} '
                           f'<span class="pg">{esc(ch["pages"])}</span></summary>{inner}</details>')
        sections.append(("chapters", "Chapters"))
        body += '<h2 id="chapters">Chapters</h2>' + "".join(ch_html)
    if sc:
        sections.append(("scenes", "Scenes"))
        body += '<h2 id="scenes">Scenes</h2>' + cards_block(P, [item(P, s) for s in sc])
    cast = [c for c in m.chars.values() if vid in c["volumes"]]
    cnt = Counter(s["owner"][1] for s in sc if s["owner"][0] == "people")
    cast.sort(key=lambda c: (-cnt.get(c["id"], 0), fold(c["sort"]), fold(c["name"])))
    sections.append(("cast", "Who is named"))
    body += (f'<h2 id="cast">Who is named <span class="n">{len(cast)}</span></h2><ul class="plain cols">'
             + "".join(f'<li>{ent(P, "people", c["id"])}</li>' for c in cast) + "</ul>")
    ex = [e for e in m.exams.values() if vid in e["volumes"]]
    pl = [p for p in m.places.values() if vid in p["volumes"]]
    if ex:
        sections.append(("exams", "Exams"))
        body += '<h2 id="exams">Exams named</h2><ul class="plain cols">' + "".join(f"<li>{ent(P, 'exams', e['id'])}</li>" for e in ex) + "</ul>"
    if pl:
        sections.append(("places", "Places"))
        body += '<h2 id="places">Places named</h2><ul class="plain cols">' + "".join(f"<li>{ent(P, 'places', p['id'])}</li>" for p in pl) + "</ul>"
    body = body.replace(info, info + toc(sections), 1)
    trail = [("Story", "story/index.html"), (yname(v["year"]), f"story/y{v['year']}.html"), (v["label"], rel)]
    add(rel, h1=v["label"], body=body, trail=trail, kicker="Volume", lede=lead)


# --------------------------------------------------- exams, systems, places
def first_last(e):
    vs = [R.m.vol[v] for v in e["volumes"]]
    return (vs[0], vs[-1]) if vs else (None, None)


LISTED = ("rule", "number", "result", "fact", "place", "trade", "impact")


def entity_page(kind, e, rel, section, sec_rel, kicker):
    m = R.m
    P = Page(rel)
    eid = e["id"]
    led = m.ledger.get((kind, eid))
    own = m.scenes_of(kind, eid)
    tag_field = {"places": "places", "exams": "exams"}.get(kind)
    tagged = m.scenes_tagged(tag_field, eid) if tag_field else []
    scenes = sorted({s["id"]: s for s in own + tagged}.values(), key=lambda s: (s["ord"], s["p0"], s["id"]))
    a, b = first_last(e)
    body = facts([("Kind", esc(e.get("kind", ""))), ("First named", ent(P, "volumes", a["id"]) if a else ""),
                  ("Last named", ent(P, "volumes", b["id"]) if b else "")])
    sections = []
    if led:
        rows = [(bl, r) for bl in led["blocks"] for r in bl["rows"] if r["m"] in LISTED]
        if rows:
            sections.append(("text", "What the text says"))
            body += ('<h2 id="text">What the text says</h2><ol class="rules">' + "".join(
                f'<li><span class="mlabel">{esc(M.MARKERS[r["m"]])}</span> {esc(r["text"])} '
                f'<span class="pg">{esc(m.vol[bl["vol"]]["short"])} {esc(r["pg"])}</span></li>' for bl, r in rows) + "</ol>")
    if scenes:
        sections.append(("scenes", "Scenes"))
        body += '<h2 id="scenes">Scenes</h2>' + cards_block(P, [item(P, s, (kind, eid), LISTED if s["owner"] == (kind, eid) else ()) for s in scenes])
    else:
        body += f'<p class="empty">Nothing here has been read line by line yet. It is named in {plural(len(e["volumes"]), "volume")}, listed below.</p>'
    sections.append(("named", "Named in"))
    body += '<h2 id="named">Named in</h2><ul class="plain cols">' + "".join(
        f'<li data-o="{m.vol[v]["ord"]}">{ent(P, "volumes", v)}</li>' for v in e["volumes"]) + "</ul>"
    body = body.replace("</dl>", "</dl>" + toc(sections), 1)
    add(rel, h1=e["name"], body=body, trail=[(section, sec_rel), (e["name"], rel)], kicker=kicker,
        lede=f"Named in {len(e['volumes'])} volume{'s' if len(e['volumes']) != 1 else ''}; {len(scenes)} scene{'s' if len(scenes) != 1 else ''} read.")


def build_school():
    m = R.m
    P = Page("school/index.html")
    ex = sorted(m.exams.values(), key=lambda e: (m.vol[e["volumes"][0]]["ord"] if e["volumes"] else 999, e["name"]))

    def lis(kind, ents):
        return "".join(f'<li>{dot("partial" if m.scenes_of(kind, e["id"]) else "stub")} {ent(P, kind, e["id"])} '
                       f'<span class="n">{esc(e.get("kind", ""))}{" · " if e.get("kind") else ""}{plural(len(e["volumes"]), "volume")}</span></li>' for e in ents)
    body = (f'<h2 id="exams">Exams <span class="n">{len(ex)}</span></h2><ul class="plain vols">{lis("exams", ex)}</ul>'
            f'<h2 id="systems">Systems <span class="n">{len(m.systems)}</span></h2><ul class="plain vols">{lis("systems", sorted(m.systems.values(), key=lambda e: e["name"]))}</ul>')
    add("school/index.html", h1="Exams & School", body=body, trail=[("Exams & School", "school/index.html")],
        lede="The exams, in the order they first appear, and the school systems behind them.")
    for e in m.exams.values():
        entity_page("exams", e, f"school/exam/{e['id']}.html", "Exams & School", "school/index.html", "Exam")
    for e in m.systems.values():
        entity_page("systems", e, f"school/system/{e['id']}.html", "Exams & School", "school/index.html", "System")


def build_world():
    m = R.m
    P = Page("world/index.html")
    kinds = defaultdict(list)
    for p in m.places.values():
        kinds[p["kind"] or "Other"].append(p)
    body = ""
    for k in sorted(kinds):
        lis = "".join(f'<li>{dot("partial" if m.scenes_of("places", p["id"]) or m.scenes_tagged("places", p["id"]) else "stub")} '
                      f'{ent(P, "places", p["id"])} <span class="n">{plural(len(p["volumes"]), "volume")}</span></li>'
                      for p in sorted(kinds[k], key=lambda p: p["name"]))
        body += f'<h2 id="{R.m and fold(k).replace(" ", "-")}">{esc(k)}</h2><ul class="plain vols">{lis}</ul>'
    add("world/index.html", h1="World & Places", body=body, trail=[("World & Places", "world/index.html")],
        lede=f"{len(m.places)} named places, grouped by kind.")
    for p in m.places.values():
        entity_page("places", p, f"world/{p['id']}.html", "World & Places", "world/index.html", "Place")


# ----------------------------------------------------------------- topics
def topic_rows(t):
    """Rows chosen by the topic's own columns in content/topics.tsv: markers, pattern, owners."""
    marks = {x for x in t["markers"].split(",") if x}
    pat = re.compile(t["pattern"], re.I) if t["pattern"] else None
    owners = t["owners"]
    out = []
    for s in R.m.scenes:
        if owners and s["owner"][0] != owners:
            continue
        for r in s["rows"]:
            if (not marks or r["m"] in marks) and (pat is None or pat.search(r["text"])):
                out.append({"scene": s, "row": r})
    return out


def build_topics():
    m = R.m
    P = Page("topics/index.html")
    counts = {}
    for t in m.topics:
        tid = t["id"]
        P = Page(f"topics/{tid}.html")
        if t["kind"] == "pairs":
            pairs = defaultdict(list)
            for s in m.scenes:
                if s["owner"][0] != "people":
                    continue
                for r in s["rows"]:
                    if r["m"] == "rel" and r["t"] in m.chars and r["t"] != s["owner"][1]:
                        pairs[tuple(sorted((s["owner"][1], r["t"])))].append((s, r))
            items = []
            for (a, b), lst in sorted(pairs.items(), key=lambda kv: (-len(kv[1]), kv[0])):
                lis = "".join(f'<li>{esc(r["text"])}<span class="pg">{esc(m.vol[s["vol"]]["short"])} {esc(r["pg"])}</span></li>' for s, r in lst[:4])
                more = f'<p class="n">+{len(lst) - 4} more notes on the two people’s pages</p>' if len(lst) > 4 else ""
                h = (f'<article class="card row"><h3><span class="ttl">{ent(P, "people", a)} and {ent(P, "people", b)}</span>'
                     f'<span class="meta">{len(lst)} note{"s" if len(lst) != 1 else ""}</span></h3><ul class="rows">{lis}</ul>{more}</article>')
                o = min(s["ord"] for s, _ in lst)
                items.append({"i": f"pair-{a}-{b}", "v": lst[0][0]["vol"], "y": lst[0][0]["year"], "o": o, "k": "",
                              "w": f"{a} {b}", "q": fold(m.name("people", a) + " " + m.name("people", b) + " " + " ".join(r["text"] for _, r in lst))[:1500], "h": h})
            noun = "pairs"
        else:
            rows = topic_rows(t)
            items = [row_item(P, r) for r in rows]
            noun = "entries"
        counts[tid] = (len(items), noun)
        body = cards_block(P, items, noun=noun, kinds=False)
        add(f"topics/{tid}.html", h1=t["title"], body=body, trail=[("Topics", "topics/index.html"), (t["title"], f"topics/{tid}.html")],
            kicker="Topic", lede=esc(t["lede"]) + f" {len(items)} {noun} from the volumes read so far.")
    P = Page("topics/index.html")
    lis = "".join(f'<li><a class="task" href="{t["id"]}.html"><strong>{esc(t["title"])}</strong><span>{esc(t["lede"])}</span>'
                  f'<span class="n">{counts[t["id"]][0]} {counts[t["id"]][1]}</span></a></li>' for t in m.topics)
    add("topics/index.html", h1="Topics", body=f'<ul class="tasks">{lis}</ul>', trail=[("Topics", "topics/index.html")],
        lede="Questions that cut across the whole series. Each entry carries its volume and page.")


# ------------------------------------------------------------ about, search
def build_about():
    m = R.m
    body = f"""<h2 id="citations">Citations</h2>
<p>A page reference such as <span class="pg">p.47</span> follows that volume's page numbering: the number is the page marker in the corpus file for that volume, which for some volumes runs ahead of the numbers printed in the book. Where a volume's printed numbers differ, its volume page explains the offset. It is plain text, never a link: nothing opens when you click it. The volume is named next to it, as in <span class="pg">Y1V1 p.47</span>.</p>
<h2 id="status">Status dots</h2>
<p>{dot("partial")} the volume, character or place has been read line by line. {dot("stub")} only names and pages are recorded.</p>
<h2 id="lines">Line types</h2>
<ul class="plain"><li><span class="mlabel">Spoken</span> a line said aloud, quoted as printed.</li><li><span class="mlabel">Inner voice</span> a thought or narration in the character's head.</li><li><span class="mlabel">What happens</span> an action, in plain words.</li><li><span class="mlabel">Inference, not stated</span> something the reader reasons out; it is never presented as fact.</li></ul>
<h2 id="scope">Read up to</h2>
<p>The menu at the top right hides every scene from volumes after the one you choose, so a page cannot spoil what you have not read. The choice is kept in this browser only.</p>
<h2 id="names">Names</h2>
<p>Names are shown with long-vowel marks. Search ignores them, so Kikyou and Kikyō find the same page.</p>"""
    add("about/how-to-read.html", h1="How to read this site", body=body, trail=[("How to read this site", "about/how-to-read.html")])
    P = Page("about/coverage.html")
    rows = "".join(
        f'<tr data-o="{v["ord"]}"><td>{ent(P, "volumes", v["id"])}</td><td>{dot(m.vol_state(v["id"]))} {m.vol_state(v["id"])}</td>'
        f'<td>{len(m.vol_ledger.get(v["id"], {"chapters": []})["chapters"])}</td><td>{len(m.scenes_in(v["id"]))}</td>'
        f'<td>{sum(1 for c in m.chars.values() if v["id"] in c["volumes"])}</td></tr>' for v in m.vols)
    body = ('<div class="scroll"><table><thead><tr><th>Volume</th><th>Status</th><th>Chapters read</th><th>Scenes</th><th>Characters named</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')
    add("about/coverage.html", h1="Coverage", body=body, trail=[("Coverage", "about/coverage.html")],
        lede="Which volumes have been read line by line, and what each page can therefore answer.")


def build_search():
    body = ('<input id="sq" class="bigsearch" type="search" placeholder="Search a name, scene or phrase" aria-label="Search" autocomplete="off" autofocus>'
            '<div id="sres"></div>')
    add("search/index.html", h1="Search", body=body, trail=[("Search", "search/index.html")])


def search_index():
    m = R.m
    recs = []

    def rec(title, typ, url, body=""):
        recs.append([title, typ, url, fold(title + " " + body)])
    for c in m.chars.values():
        rec(c["name"], "Character", path("people", c["id"]), " ".join(c["aliases"]))
    for v in m.vols:
        rec(v["label"], "Volume", path("volumes", v["id"]), v["short"])
    for k, label in (("exams", "Exam"), ("systems", "System"), ("places", "Place")):
        for e in m.kinds[k].values():
            rec(e["name"], label, path(k, e["id"]))
    for t in m.topics:
        rec(t["title"], "Topic", f"topics/{t['id']}.html", t["lede"])
    for s in m.scenes:
        ok, oid = s["owner"]
        u = path(ok, oid)
        if u.startswith("people/index.html"):
            continue
        body = " ".join([m.name(ok, oid)] + [r["text"] for r in s["rows"]])
        rec(s["title"], "Scene", f"{u}#{s['id']}", body)
    return "window.IDX=" + json.dumps(recs, ensure_ascii=False, separators=(",", ":")) + ";\n"


# -------------------------------------------------------------- redirects
def redirect_target(old, built):
    m = R.m
    if old in built:
        return None
    mm = re.match(r"people/([^/]+)\.html$", old)
    if mm:
        c = mm.group(1)
        if c == "tachibana":
            c = "tachibana-akane"
        return path("people", c) if c in m.chars else "people/index.html"
    if old.startswith("people/minor/"):
        return "people/index.html"
    mm = re.match(r"story/v/[^/]+/([a-z0-9-]+)\.(guide|transcript)\.html$", old)
    if mm:
        return path("people", mm.group(1)) if mm.group(1) in m.chars else "people/index.html"
    if old == "school/chronology.html":
        return "story/index.html"
    if old.startswith("appendix/"):
        return "about/coverage.html" if "coverage" in old else "about/how-to-read.html"
    return "index.html"


def build_redirects():
    old = (M.CONTENT / "old_urls.txt").read_text(encoding="utf-8").split()
    built = set(PAGES)
    for o in old:
        t = redirect_target(o, built)
        if not t:
            continue
        P = Page(o)
        to = P.u(t)
        PAGES[o] = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved · COTE Knowledge Base</title>'
                    f'<meta http-equiv="refresh" content="0; url={esc(to)}"><link rel="canonical" href="{esc(to)}"></head>'
                    f'<body><p>This page moved. <a href="{esc(to)}">Continue to the new page</a>.</p></body></html>\n')


# ------------------------------------------------------------------- main
def plural(n, word):
    """'1 volume', '14 volumes'."""
    return f"{n} {word}" + ("" if n == 1 else "s")


def service_worker(files):
    """Offline cache worker. Its version is a hash of every page and asset, so any change retires the old cache."""
    h = hashlib.md5()
    for rel in sorted(files):
        h.update(rel.encode())
        h.update(files[rel].encode("utf-8"))
    core = ["index.html", "assets/style.css", "assets/app.js", "assets/meta.js", "assets/telemetry.js", "assets/fx.js"]
    warm = sorted(PAGES) + ["assets/search-index.js"]
    text = (ASSETS / "sw.js").read_text(encoding="utf-8")
    h.update(text.encode("utf-8"))
    return (text.replace("__VERSION__", h.hexdigest()[:12])
            .replace("__CORE__", json.dumps(core)).replace("__WARM__", json.dumps(warm)))


def md5_tree(root):
    h = hashlib.md5()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(M.ROOT / "docs"))
    out = Path(ap.parse_args().out)
    model = M.Model()
    R.init(model)
    m = model
    build_home()
    build_people_index()
    for c in m.chars.values():
        if c["has_page"]:
            build_character(c)
    build_story()
    for v in m.vols:
        build_volume(v)
    build_school()
    build_world()
    build_topics()
    build_about()
    build_search()
    build_redirects()
    R.FILES["assets/search-index.js"] = search_index()
    vols = "window.VOLS=" + json.dumps([[v["ord"], v["label"], v["short"], v["id"]] for v in m.vols], ensure_ascii=False) + ";\n"
    R.FILES["assets/meta.js"] = vols + (ASSETS / "boot.js").read_text(encoding="utf-8")
    for name in ("style.css", "app.js", "telemetry.js", "fx.js"):
        R.FILES[f"assets/{name}"] = (ASSETS / name).read_text(encoding="utf-8")
    R.FILES["sw.js"] = service_worker({**PAGES, **R.FILES})
    if out.exists():
        shutil.rmtree(out)
    for rel, text in {**PAGES, **R.FILES}.items():
        f = out / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    print(f"built {len(PAGES)} pages, {len(R.FILES)} assets -> {out}")
    print("hash", md5_tree(out))


if __name__ == "__main__":
    main()

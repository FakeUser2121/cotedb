"""HTML pieces shared by every page: shell, links, scene cards, filter panel.

One link grammar: a name links as a whole, a citation (p.47) is plain text, a
control is a button. One card format for a scene wherever it appears.
"""
import html
import json
import posixpath

import model as M
from model import fold

esc = lambda s: html.escape(str(s), quote=True)
m = None  # the Model, set by init()
FILES = {}  # relative output path -> text

SECTIONS = [("people", "People", "people/index.html"),
            ("story", "Story", "story/index.html"),
            ("school", "Exams & School", "school/index.html"),
            ("world", "World & Places", "world/index.html"),
            ("topics", "Topics", "topics/index.html")]
ROLE = {"class-1b": "Class 1-B", "class-1d": "Class 1-D", "student-council": "Student council",
        "faculty": "Faculty"}
KIND_LABEL = {"spoken": "Spoken", "inner": "Inner voice", "action": "Action", "narration": "Narration"}


def init(model):
    global m
    m = model


class Page:
    def __init__(self, rel):
        self.rel = rel
        self.base = posixpath.dirname(rel) or "."
        self.root = "../" * rel.count("/")
        self.key = rel[:-5].replace("/", "-")

    def u(self, to):
        path, _, frag = to.partition("#")
        r = posixpath.relpath(path, self.base) if path else ""
        return r + ("#" + frag if frag else "")


def path(kind, eid):
    if kind == "people":
        return f"people/{eid}.html" if m.chars[eid]["has_page"] else f"people/index.html#{eid}"
    return {"exams": f"school/exam/{eid}.html", "systems": f"school/system/{eid}.html",
            "places": f"world/{eid}.html", "volumes": f"story/v/{eid}/index.html"}[kind]


def ent(P, kind, eid, text=None):
    if eid not in m.kinds.get(kind, {}) and not (kind == "volumes" and eid in m.vol):
        return esc(text or eid)
    name = text or (m.vol[eid]["label"] if kind == "volumes" else m.name(kind, eid))
    return f'<a href="{P.u(path(kind, eid))}">{esc(name)}</a>'


def dot(state):
    return '<span class="dot full" title="read line by line">●</span>' if state in ("partial", "complete") \
        else '<span class="dot" title="names and pages only">○</span>'


def crumbs(P, trail):
    parts = [f'<a href="{P.u("index.html")}">Home</a>']
    for label, to in trail[:-1]:
        parts.append(f'<a href="{P.u(to)}">{esc(label)}</a>')
    parts.append(f'<span class="here">{esc(trail[-1][0])}</span>')
    return ('<nav class="crumbs" aria-label="Breadcrumb">'
            + '<span class="sep">/</span>'.join(parts) + "</nav>")


def shell(P, h1, body, trail, kicker="", lede="", desc="", home=False):
    r = P.root
    cur_home = ' aria-current="page"' if home else ""
    tabs = [f'<a href="{r}index.html"{cur_home}>Home</a>']
    for sid, label, to in SECTIONS:
        cur = ' aria-current="page"' if P.rel == to or P.rel.startswith(sid + "/") else ""
        tabs.append(f'<a href="{r}{to}"{cur}>{esc(label)}</a>')
    title = "COTE Knowledge Base" if home else f"{h1} · COTE Knowledge Base"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or lede or h1)}">
<link rel="stylesheet" href="{r}assets/style.css">
<script src="{r}assets/meta.js"></script>
<script src="{r}assets/app.js" defer></script>
</head><body data-root="{r}">
<header class="top"><a class="brand" href="{r}index.html">COTE Knowledge Base</a>
<div class="tools"><input id="q" type="search" placeholder="Search a name, scene or phrase" aria-label="Search" autocomplete="off">
<label class="upto">Read up to <select id="upto"></select></label>
<button id="theme" type="button" aria-label="Dark or light">◐</button></div>
<div id="sr" hidden></div></header>
<nav class="tabs" aria-label="Sections">{"".join(tabs)}</nav>
<main class="content">{"" if home else crumbs(P, trail)}
{f'<div class="kicker">{esc(kicker)}</div>' if kicker else ""}<h1>{esc(h1)}</h1>
{f'<p class="lede">{lede}</p>' if lede else ""}
{body}
</main>
<footer><a href="{r}about/how-to-read.html">How to read this site</a> · <a href="{r}about/coverage.html">Coverage</a> · <a href="{m.cfg['repo_url']}">Contribute</a></footer>
</body></html>
"""


def toc(items):
    return ('<nav class="toc" aria-label="On this page">'
            + " · ".join(f'<a href="#{i}">{esc(t)}</a>' for i, t in items) + "</nav>")


# ------------------------------------------------------------------ scenes
def key_lines(s):
    spoken = [q for q in s["quotes"] if q["kind"] == "spoken"]
    other = [q for q in s["quotes"] if q["kind"] != "spoken"]
    pick = (spoken + other)[:3]
    if not pick:
        pick = [{"kind": "action", "who": "", "pg": r["pg"], "text": r["text"], "row": r}
                for r in s["rows"] if r["m"] == "action"][:2]
    return sorted(pick, key=lambda q: s["rows"].index(q["row"]))


def kinds_of(s):
    ks = {q["kind"] for q in s["quotes"]}
    if any(r["m"] == "action" for r in s["rows"]):
        ks.add("action")
    return " ".join(sorted(ks))


def excerpt(text, n=230):
    """A card shows the start of a long line; the whole line sits under 'more notes'."""
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…" + ("”" if text.startswith("“") else "")


def pg(label):
    return f'<span class="pg">{esc(label)}</span>' if label else ""


def card(P, s, here=None, skip=()):
    ok, oid = s["owner"]
    own_page = path(ok, oid)
    linked = not own_page.startswith("people/index.html")
    title = esc(s["title"])
    if here != s["owner"] and linked:
        title = f'<a href="{P.u(own_page)}#{s["id"]}">{title}</a>'
    by = ""
    if here != s["owner"]:
        by = f'<span class="by">notes on {ent(P, ok, oid)}</span>'
    out = [f'<article class="card" id="{s["id"]}"><h3><span class="ttl">{title}</span>'
           f'<span class="meta">{esc(m.vol[s["vol"]]["short"])} · {esc(s["pages"])}</span>{by}</h3>']
    if s["setup"]:
        out.append(f'<p class="setup">{esc(s["setup"])}</p>')
    tags = [ent(P, "places", p) for p in dict.fromkeys(s["places"]) if ("places", p) != here] + \
           [ent(P, "exams", e) for e in dict.fromkeys(s["exams"]) if ("exams", e) != here]
    if tags:
        out.append(f'<p class="tags">{" · ".join(tags)}</p>')
    people = [w for w in s["with"] if w in m.chars and (("people", w) != here)]
    if people:
        shown = " · ".join(ent(P, "people", w) for w in people[:6])
        more = f' <span class="n">+{len(people) - 6} more</span>' if len(people) > 6 else ""
        out.append(f'<p class="with">with {shown}{more}</p>')
    picks = key_lines(s)
    here_id = here[1] if here else ""
    if picks:
        lis = []
        for q in picks:
            who = ""
            if q["who"] and q["who"] != here_id:
                who = f'<b class="sp">{esc(m.name("people", q["who"]))}</b> '
            lis.append(f'<li class="q {q["kind"]}">{who}{esc(excerpt(q["text"]))}{pg(q["pg"])}</li>')
        out.append(f'<ul class="lines">{"".join(lis)}</ul>')
    shown_ids = {id(q["row"]) for q in picks if excerpt(q["text"]) == q["text"]}
    rest = [r for r in s["rows"] if r["m"] != "scene" and id(r) not in shown_ids and r["m"] not in skip]
    if rest:
        lis = []
        for r in rest:
            tgt = f'<b class="sp">{esc(m.name("people", r["t"]))}</b> ' if r["m"] == "rel" and r["t"] else ""
            lis.append(f'<li><span class="mlabel">{esc(M.MARKERS[r["m"]])}</span> {tgt}{esc(r["text"])}{pg(r["pg"])}</li>')
        out.append(f'<details class="more"><summary>{len(rest)} more note{"s" if len(rest) != 1 else ""}'
                   f'</summary><ul class="rows">{"".join(lis)}</ul></details>')
    ptr = []
    if s["prev"]:
        ptr.append(f'<button type="button" class="ptr" data-go="{s["prev"]["id"]}">← Before: {esc(s["prev"]["title"])}</button>')
    if s["next"]:
        ptr.append(f'<button type="button" class="ptr" data-go="{s["next"]["id"]}">→ After: {esc(s["next"]["title"])}</button>')
    if ptr:
        out.append(f'<div class="ptrs">{"".join(ptr)}</div>')
    out.append("</article>")
    return "".join(out)


def item(P, s, here=None, skip=()):
    w = list(s["with"]) + ([s["owner"][1]] if s["owner"][0] == "people" else [])
    text = " ".join([m.name(s["owner"][0], s["owner"][1]), s["title"]] + [r["text"] for r in s["rows"]])
    return {"i": s["id"], "v": s["vol"], "y": s["year"], "o": s["ord"], "k": kinds_of(s),
            "w": " ".join(dict.fromkeys(w)), "q": fold(text), "h": card(P, s, here, skip)}


def row_item(P, r):
    """A single ledger entry as a card (topic pages)."""
    s = r["scene"]
    ok, oid = s["owner"]
    own = path(ok, oid)
    title = esc(s["title"])
    if not own.startswith("people/index.html"):
        title = f'<a href="{P.u(own)}#{s["id"]}">{title}</a>'
    who = ent(P, ok, oid)
    tgt = f' <b class="sp">{esc(m.name("people", r["row"]["t"]))}</b>' if r["row"]["m"] == "rel" and r["row"]["t"] else ""
    h = (f'<article class="card row"><p><span class="mlabel">{esc(M.MARKERS[r["row"]["m"]])}</span>{tgt} '
         f'{esc(r["row"]["text"])}{pg(r["row"]["pg"])}</p>'
         f'<p class="src">{ent(P, "volumes", s["vol"])} · {who} · {title}</p></article>')
    return {"i": s["id"], "v": s["vol"], "y": s["year"], "o": s["ord"], "k": "",
            "w": s["owner"][1] + " " + r["row"]["t"], "q": fold(s["title"] + " " + r["row"]["text"])[:1500], "h": h}


def cards_block(P, items, noun="scenes", with_id=None, kinds=True, key=None):
    key = key or P.key
    payload = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    FILES[f"assets/s/{key}.js"] = f"window.CARDS=window.CARDS||{{}};CARDS[{json.dumps(key)}]={payload};\n"
    from collections import Counter
    wc = Counter(w for it in items for w in it["w"].split() if w in m.chars and w != with_id)
    wopts = "".join(f'<option value="{w}">{esc(m.name("people", w))}</option>'
                    for w, _ in sorted(wc.most_common(30), key=lambda x: fold(m.name("people", x[0]))))
    vols = sorted({it["v"] for it in items}, key=lambda v: m.vol[v]["ord"])
    vopts = "".join(f'<option value="{v}">{esc(m.vol[v]["label"])}</option>' for v in vols)
    years = sorted({it["y"] for it in items}, key=lambda y: y or 9)
    ychips = ""
    if len(years) > 1:
        ychips = ('<div class="chips scope" data-scope><button type="button" class="on" data-y="">All</button>'
                  + "".join(f'<button type="button" data-y="{y}">Year {y}</button>' for y in years if y) + "</div>")
    kchips = ""
    if kinds:
        kchips = ('<div class="chips" data-kinds>' + "".join(
            f'<button type="button" data-k="{k}">{l}</button>' for k, l in KIND_LABEL.items() if k != "narration")
            + "</div>")
    static = "".join(i["h"] for i in items[:m.cfg["static_cards"]])
    return (f'<div class="cards"><div class="panel">'
            f'<input class="fq" type="search" placeholder="Search these {noun}" aria-label="Search these {noun}">'
            f'{kchips}{ychips}'
            f'<label>With <select class="fw"><option value="">anyone</option>{wopts}</select></label>'
            f'<label>Volume <select class="fv"><option value="">any</option>{vopts}</select></label></div>'
            f'<p class="count" aria-live="polite">{len(items)} {noun}</p>'
            f'<div class="results" data-key="{key}" data-size="{m.cfg["page_size"]}">{static}</div>'
            f'<button type="button" class="morebtn" hidden>Load more</button>'
            f'<noscript><p class="n">The first {min(len(items), m.cfg["static_cards"])} of {len(items)} {noun} are shown; '
            f'filtering and the rest need JavaScript.</p></noscript>'
            f'<script src="{P.u("assets/s/" + key + ".js")}"></script></div>')

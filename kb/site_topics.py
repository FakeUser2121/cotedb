#!/usr/bin/env python3
"""Topics, reader doors, appendix, and the volume documents (guides and
scene transcripts authored in drafts/).

Topics are the 'reorganised by question' layer: each page is assembled
mechanically from the curated records (exam instances, character arcs,
relations, claims), never by inventing a summary. Where the records only
partially answer a question, the page says so at the top.

The reader doors are the three audiences the archive exists for: writers
(voice and exact lines), number-crunchers (feats, results, point maths),
and anyone trying to find the moment they half-remember.
"""

import posixpath
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arch  # noqa: E402
import site_data as D  # noqa: E402
import site_shell as S  # noqa: E402
from share_render import slug, render_full  # noqa: E402
from site_sections import (alpha_nav, door, dominant_vol, facts_strip,  # noqa: E402
                           grid_links, section_scope, volume_index_href)

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "drafts" / "people"

EXPEL_RE = re.compile(r"expel|drop out|leaving the school|vote", re.I)
POINT_RE = re.compile(r"\b([\d][\d,]{2,})\s*(?:private\s+)?points?\b", re.I)
WIN_RE = re.compile(r"win|place|first|second|third|fourth|victor|defeat", re.I)

REL_FAMILIES = [
    ("Rivalries", ["rival", "arch", "enemy", "hostile", "adversary", "prey",
                   "defeated", "envy", "benchmark"]),
    ("Alliances & class politics", ["ally", "support", "partner", "confidant",
                                    "co-leader", "circle", "friction",
                                    "friendly", "peripheral", "respect"]),
    ("Secrets & leverage", ["secret", "witness", "leverage", "keeper",
                            "blackmail", "pretend", "tool", "asset",
                            "watched", "ward-to"]),
    ("Authority & the board", ["authority", "enforcer", "observer",
                               "official", "loose"]),
    ("Family & wardship", ["family", "ward", "charge", "parent",
                           "resentment"]),
]


def vol_sorted(ctx, rows, key):
    return sorted(rows, key=lambda r: order(ctx, key(r)))


def order(ctx, vol_id):
    v = ctx["vols"].get(vol_id)
    return int(v["order"]) if v else 999


def vol_link(ctx, vol_id, base):
    v = ctx["vols"].get(vol_id)
    label = v["label"] if v else vol_id
    href = posixpath.relpath(volume_index_href(vol_id), base)
    return f'<a href="{href}">{S.esc(label)}</a>'


def rel_family(rel_type):
    low = (rel_type or "").lower()
    for label, keys in REL_FAMILIES:
        if any(k in low for k in keys):
            return label
    return "Other connections"


def topics_rail(ctx):
    return [{"kind": "link", "label": "All topics", "href": "topics/index.html"}] + [
        {"kind": "link", "label": t["title"], "href": f"topics/{t['id']}.html"}
        for t in TOPICS]


TOPICS = [
    {"id": "relationships", "title": "Every relationship, with evidence",
     "lede": "Who is aligned, opposed, or indebted to whom, and the page "
             "where each of those reads."},
    {"id": "who-knew-what", "title": "Who knew what, and when",
     "lede": "The knowledge state of the cast volume by volume — the layer "
             "that makes the reveals land."},
    {"id": "expulsions", "title": "Expulsions and near-misses",
     "lede": "Every moment the school put a student's place on the table."},
    {"id": "points", "title": "Points, prices and payouts",
     "lede": "The numbers the economy of the school actually moved on."},
    {"id": "results", "title": "Winners, placements and consequences",
     "lede": "What each exam decided, in the order it was decided."},
]


def topics_index(ctx):
    rows = "".join(
        f'<a class="door" href="topics/{t["id"]}.html">'
        f'<span class="q">{S.esc(t["title"])}</span>'
        f'<span class="d">{S.esc(t["lede"])}</span>'
        f'<span class="go">Open →</span></a>' for t in TOPICS)
    body = f"""<h2 id="questions">Question pages</h2>
<p>These pages cut across every volume: pick the question rather than
the entity. Each statement carries the page it came from.</p>
<div class="doors">{rows}</div>
<h2 id="building">How a topic page is built</h2>
<p>A topic is assembled from the records that already carry a page
citation — exam runs, character arc states, relationship notes, and named
narrator facts. Nothing is summarised from memory, so a topic page can
never be more current than the records behind it, and it says at the top
how far those records reach.</p>"""
    return ctx["page"]("Topics", "topics", body,
                      [("Home", "index.html"), ("Topics", None)],
                      out="topics/index.html", rail=topics_rail(ctx),
                      lede="Answers to the questions people actually ask, "
                           "assembled from the pages that hold them.",
                      kicker="By question", tagline_label="Topics",
                      scope=ctx["scope"])


def topic_shell(ctx, topic, coverage_note, body):
    base = "topics"
    note = (f'<div class="box note"><h4>Coverage</h4><p>{coverage_note}</p></div>'
            if coverage_note else "")
    html_out = ctx["page"](
        topic["title"], "topics", note + body,
        [("Home", "index.html"), ("Topics", "topics/index.html"),
         (topic["title"], None)],
        out=f"topics/{topic['id']}.html", rail=topics_rail(ctx),
        lede=topic["lede"], kicker="Topic", tagline_label="Topic",
        scope=ctx["scope"])
    return (f"topics/{topic['id']}.html", html_out)


def build_relationships(ctx):
    families = {}
    for r in ctx["relations"]:
        families.setdefault(rel_family(r["type"]), []).append(r)
    blocks = []
    for label, _keys in REL_FAMILIES + [("Other connections", [])]:
        rows = families.get(label)
        if not rows:
            continue
        items = []
        for r in sorted(rows, key=lambda x: (x["a_name"], x["b_name"])):
            a = ctx["char_by_id"].get(r["a"])
            b = ctx["char_by_id"].get(r["b"])
            names = []
            for cc, raw in ((a, r["a_name"]), (b, r["b_name"])):
                if cc:
                    names.append(
                        f'<a href="{posixpath.relpath(cc["href"], "topics")}">'
                        f'{S.esc(cc["name"])}</a>')
                else:
                    names.append(S.esc(raw))
            refs = re.findall(r"y[0-9v.]+\s+pp?\.?\s*\d+(?:\s*[–-]\s*\d+)?",
                              r["refs"] or "")
            chips = "".join(f'<span class="cite">{S.esc(x)}</span> '
                            for x in refs[:4])
            span = ""
            if r["from"] in ctx["vols"] or r["to"] in ctx["vols"]:
                bits = [x for x in (ctx["vols"].get(r["from"], {}).get("short"),
                                    ctx["vols"].get(r["to"], {}).get("short")) if x]
                if bits:
                    span = f' <span class="n">({"/".join(bits)})</span>'
            items.append(
                f'<div class="scene"><div class="head">'
                f'<span class="ttl">{" ↔ ".join(names)}</span>'
                f'<span class="who">{S.esc(r["type"])}{span}</span></div>'
                f'<p>{S.esc(D.clean(r["note"]))}</p>{chips}</div>')
        blocks.append(f'<h2 id="{slug(label)}">{S.esc(label)}</h2>'
                      f'{"".join(items)}')
    body = "".join(blocks)
    note = f"{len(ctx['relations'])} relationships recorded, concentrated on " \
           "the principal and recurring cast; the walk adds more as it " \
           "reaches each volume."
    return topic_shell(ctx, TOPICS[0], note, body)


def build_who_knew_what(ctx):
    by_vol = {}
    for t in ctx["timeline"]:
        by_vol.setdefault(t["vol_id"], []).append(t)
    items = []
    for vol in sorted(by_vol, key=lambda v: order(ctx, v)):
        rows = []
        for t in sorted(by_vol[vol], key=lambda t: t["name"]):
            c = ctx["char_by_id"].get(t["char_id"])
            name = f'<a href="{posixpath.relpath(c["href"], "topics")}">' \
                f'{S.esc(c["name"])}</a>' if c else S.esc(t["name"])
            bits = []
            if t["knowledge"]:
                bits.append(f'<li><strong>Knows</strong> — {S.esc(D.clean(t["knowledge"]))}</li>')
            if t["situation"]:
                bits.append(f'<li><strong>Position</strong> — {S.esc(D.clean(t["situation"]))}</li>')
            if t["changes"]:
                bits.append(f'<li><strong>Shift</strong> — {S.esc(D.clean(t["changes"]))}</li>')
            refs = re.findall(r"y[0-9v.]+\s+pp?\.?\s*\d+(?:\s*[–-]\s*\d+)?",
                              t["refs"] or "")
            chips = "".join(f'<span class="cite">{S.esc(x)}</span> '
                            for x in refs[:4])
            rows.append(f'<div class="scene"><div class="head">'
                        f'<span class="ttl">{name}</span></div>'
                        f'<ul>{"".join(bits)}</ul>{chips}</div>')
        items.append(f'<h2 id="v-{vol}">{S.esc(ctx["vols"].get(vol, {}).get("label", vol))}</h2>'
                     f'{"".join(rows)}')
    body = "".join(items)
    note = f"{len(ctx['timeline'])} arc records carry a knowledge state; " \
           "they exist only for volumes the analysis reached, so gaps are " \
           "silent rather than empty."
    return topic_shell(ctx, TOPICS[1], note, body)


def build_expulsions(ctx):
    rows = []
    for e in ctx["exam_rows"]:
        for r in e["instances"]:
            text = f'{r["chronology"]} {r["outcome"]}'
            if EXPEL_RE.search(text):
                rows.append((r["vol_id"], r["page"], e["name"], text,
                             r["refs"]))
    for t in ctx["timeline"]:
        text = f'{t["situation"]} {t["changes"]} {t["why"]}'
        if EXPEL_RE.search(text):
            rows.append((t["vol_id"], 0, t["name"], text, t["refs"]))
    for cl in ctx["claims"]:
        if EXPEL_RE.search(cl["claim"] or ""):
            rows.append((cl["vol_id"], cl["page"], cl["name"], cl["claim"],
                         f'{cl["vol_id"]} p.{cl["page"]}'))
    seen = set()
    items = []
    for vol, page, who, text, refs in sorted(
            rows, key=lambda r: (order(ctx, r[0]), r[1])):
        key = (vol, re.sub(r"\W+", "", text)[:60])
        if key in seen:
            continue
        seen.add(key)
        chips = "".join(
            f'<span class="cite">{m.group(0)}</span> '
            for m in list(site_arch.PAGE_IN_CITE_RE.finditer(refs or ""))[:4])
        items.append(
            f'<div class="scene"><div class="head">'
            f'<span class="pg">{vol_link(ctx, vol, "topics")}</span>'
            f'<span class="who">{S.esc(who)}</span></div>'
            f'<p>{S.esc(D.clean(text)[:400])}</p>{chips}</div>')
    body = "".join(items)
    note = "Matched on the words 'expel', 'drop out' and 'vote' inside the " \
           "curated exam, arc and narrator records. It is a locator, not a " \
           "ruling: the exact rule text lives on the " \
           "<a href='../school/system/expulsion.html'>expulsion system " \
           "page</a>."
    return topic_shell(ctx, TOPICS[2], note, body)


def build_points(ctx):
    rows = []
    for e in ctx["exam_rows"]:
        if e["points"]:
            rows.append((e["first_vol"], e["name"] + " — rules",
                         e["points"], ""))
        for r in e["instances"]:
            text = f'{r["chronology"]} {r["outcome"]}'
            for m in POINT_RE.finditer(text):
                s = max(0, m.start() - 110)
                snippet = D.clean(text[s:m.end() + 160])
                rows.append((r["vol_id"], f'{e["name"]}, run {r["seq"]}',
                             snippet, r["refs"]))
    for cl in ctx["claims"]:
        if POINT_RE.search(cl["claim"] or ""):
            rows.append((cl["vol_id"], cl["name"], cl["claim"],
                         f'{cl["vol_id"]} p.{cl["page"]}'))
    seen = set()
    items = []
    for vol, who, text, refs in sorted(rows, key=lambda r: order(ctx, r[0])):
        key = re.sub(r"\W+", "", text)[:70]
        if not text or key in seen:
            continue
        seen.add(key)
        chips = "".join(
            f'<span class="cite">{m.group(0)}</span> '
            for m in list(site_arch.PAGE_IN_CITE_RE.finditer(refs or ""))[:3])
        items.append(
            f'<div class="scene"><div class="head">'
            f'<span class="pg">{vol_link(ctx, vol, "topics")}</span>'
            f'<span class="who">{S.esc(who)}</span></div>'
            f'<p>{S.esc(D.clean(text)[:420])}</p>{chips}</div>')
    body = (
        f'<h2 id="the-numbers">Every figure the records carry</h2>'
        f'<p>Prices, payouts and point swings, in story order. A number only '
        f'appears here if a record cites the page it was stated on.</p>'
        f'{"".join(items)}')
    note = f"{len(items)} point figures located in the curated records; the " \
           "written rules behind them are on the " \
           "<a href='../school/system/class-points.html'>class points</a> " \
           "and <a href='../school/system/private-points.html'>private " \
           "points</a> pages."
    return topic_shell(ctx, TOPICS[3], note, body)


def build_results(ctx):
    items = []
    runs = []
    for e in ctx["exam_rows"]:
        for r in e["instances"]:
            runs.append((r, e))
    for r, e in sorted(runs, key=lambda x: (order(ctx, x[0]["vol_id"]),
                                            x[0]["seq"])):
        chips = "".join(
            f'<span class="cite">{m.group(0)}</span> '
            for m in list(site_arch.PAGE_IN_CITE_RE.finditer(r["refs"] or ""))[:5])
        items.append(
            f'<div class="scene"><div class="head">'
            f'<span class="pg">{vol_link(ctx, r["vol_id"], "topics")}'
            f'</span><span class="ttl">{S.esc(e["name"])} · run {r["seq"]}</span>'
            f'</div><p>{S.esc(D.clean(r["chronology"]))}</p>'
            f'<p><strong>What it decided</strong> — {S.esc(D.clean(r["outcome"]))}</p>'
            f'<p class="who">{S.esc(D.clean(r["participants"]))}</p>{chips}</div>')
    body = "".join(items)
    note = f"{len(items)} recorded exam runs, each with the volume it " \
           "happened in and the page the result is stated on."
    return topic_shell(ctx, TOPICS[4], note, body)


TOPIC_BUILDERS = {
    "relationships": build_relationships,
    "who-knew-what": build_who_knew_what,
    "expulsions": build_expulsions,
    "points": build_points,
    "results": build_results,
}


# ------------------------------------------------------------ reader doors


def guides_rail(ctx):
    return [{"kind": "link", "label": "Start here",
             "href": "guides/index.html"},
            {"kind": "link", "label": "For writers",
             "href": "guides/for-writers.html"},
            {"kind": "link", "label": "For number-crunchers",
             "href": "guides/for-powerscalers.html"},
            {"kind": "link", "label": "Find that moment",
             "href": "guides/find-that-moment.html"}]


def guides_index(ctx):
    body = f"""<h2 id="doors">Three ways in</h2>
<div class="doors">
{door("I write in this world", "How does this character actually talk?",
      "Voice samples, exact lines and scene context you can lift cadence from.",
      "guides/for-writers.html")}
{door("I settle arguments", "Who won, by how much, on what page?",
      "Feats, exam results, point maths and the anchors behind them.",
      "guides/for-powerscalers.html")}
{door("I half-remember it", "Where is that moment?",
      "Browse by volume, place, exam or relationship until the search box "
      "finds it.", "guides/find-that-moment.html")}
</div>
<h2 id="new">If you are new to the series</h2>
<p>Start at <a href="story/y1.html">Year 1</a> and open
<strong>Volume 1</strong>: it is the one volume transcribed line by line,
so you can read the whole shape of it with page numbers attached, or open a
character's scene transcript and see exactly how the first mask is worn.</p>
<h2 id="trust">How much to trust a page here</h2>
<p>Analysis is written; everything inside quotation marks is the novel's own
text; every claim carries a volume and page. Where the archive is thin, the
page says so instead of filling the gap.</p>"""
    return ctx["page"]("Start here", "guides", body,
                      [("Home", "index.html"), ("Start here", None)],
                      out="guides/index.html", rail=guides_rail(ctx),
                      lede="Pick the door that matches why you opened this.",
                      kicker="Reader doors", tagline_label="Start here",
                      scope=ctx["scope"])


def writers_page(ctx):
    docs = [i for i in ctx["vol_docs"].values() if i["kind"] == "transcript"]
    guides = [i for i in ctx["vol_docs"].values() if i["kind"] == "guide"]
    named = [c for c in ctx["chars"] if c["tier"] <= 2 and c["quotes"]]
    named.sort(key=lambda c: -c["quotes"])
    rows = grid_links([(c["name"], f'{c["quotes"]:,} quoted lines · '
                       f'{c["quote_vols"]} volumes', c["href"])
                       for c in named[:28]])
    body = f"""<h2 id="lines">Where the actual lines live</h2>
<p>A transcript is a character's own words in scene order, each with its
page. Open one when you need cadence, vocabulary, and what they say when
they think nobody is listening.</p>
<ul>
{"".join(f'<li><a href="{posixpath.relpath(i["out"], "guides")}">'
         f'{S.esc(i["char_name"])} — {S.esc(site_arch.volume_label(i["vol"]))}'
         f' transcript</a></li>' for i in docs)}
</ul>
<h2 id="guides">Character guides for a single volume</h2>
<ul>
{"".join(f'<li><a href="{posixpath.relpath(i["out"], "guides")}">'
         f'{S.esc(i["char_name"])} — {S.esc(site_arch.volume_label(i["vol"]))}'
         f' guide</a></li>' for i in guides)}
</ul>
<h2 id="by-person">Every named character with lines to quote</h2>
{rows}
<div class="box note"><h4>What is not here yet</h4><p>Voice analysis — the
deliberate study of how each character constructs sentences — currently
exists for the transcribed volume. Character profiles carry speech lines
from every volume, but the written voice notes only reach as far as the
transcripts do.</p></div>"""
    topic = {"id": "for-writers", "title": "For writers",
             "lede": "Voice, exact lines and scene context — the material "
                     "you need to sound like the book."}
    html_out = ctx["page"](
        topic["title"], "guides", body,
        [("Home", "index.html"), ("Start here", "guides/index.html"),
         ("For writers", None)],
        out="guides/for-writers.html", rail=guides_rail(ctx), lede=topic["lede"],
        kicker="Reader door", tagline_label="For writers", scope=ctx["scope"])
    return ("guides/for-writers.html", html_out)


def powerscalers_page(ctx):
    rows = []
    for c in sorted([c for c in ctx["chars"] if c["tier"] <= 2],
                    key=lambda c: -c["quotes"]):
        rows.append(
            f'<tr><td><a href="{posixpath.relpath(c["href"], "guides")}">'
            f'{S.esc(c["name"])}</a></td>'
            f'<td>{site_arch.TIER_LABEL[c["tier"]]}</td>'
            f'<td>{c["quotes"]:,}</td><td>{c["quote_vols"]}</td>'
            f'<td>{c["coverage"]}</td></tr>')
    body = f"""<h2 id="numbers">The measurable layer</h2>
<p>What the books themselves can prove is presence and speech, not power. These counts
are the honest floor: quoted lines, volumes with lines, volumes the locator
found the name in.</p>
<table><thead><tr><th>Character</th><th>Role</th><th>Quoted lines</th>
<th>Vols quoting</th><th>Vols present</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
<h2 id="feats">Where the feats actually live</h2>
<ul>
<li><a href="topics/results.html">Winners, placements and consequences</a> —
every exam run with what it decided and the page it was stated on.</li>
<li><a href="topics/points.html">Points, prices and payouts</a> — the
numbers the economy moved on.</li>
<li><a href="topics/expulsions.html">Expulsions and near-misses</a> — every
time the threat was real.</li>
<li><a href="school/chronology.html">Exam chronology</a> — the schedule the
results sit in.</li>
</ul>
<div class="box warn"><h4>Read this before you argue</h4><p>No page here
ranks two characters against each other. The novels never state a power
level, so any ranking is a reader's inference — and an inference printed as
fact is the failure mode this archive was built to avoid.</p></div>"""
    html_out = ctx["page"](
        "For number-crunchers", "guides", body,
        [("Home", "index.html"), ("Start here", "guides/index.html"),
         ("For number-crunchers", None)],
        out="guides/for-powerscalers.html", rail=guides_rail(ctx),
        lede="Feats, results and point maths, with the page each figure was "
             "stated on — and no invented power rankings.",
        kicker="Reader door", tagline_label="For powerscalers",
        scope=ctx["scope"])
    return ("guides/for-powerscalers.html", html_out)


def moment_page(ctx):
    vols = ctx["vol_list"]
    by_year = {}
    for v in vols:
        by_year.setdefault(v["year"], []).append(v)
    vol_links = []
    for year in sorted(by_year):
        items = "".join(
            f'<a href="{posixpath.relpath(volume_index_href(v["id"]), "guides")}">'
            f'{S.esc(site_arch.volume_short(v["id"]))}</a>' for v in by_year[year])
        label = {0: "Side stories", 1: "Year 1", 2: "Year 2",
                 3: "Year 3"}[year]
        vol_links.append(f'<p><strong>{label}</strong> — {items}</p>')
    places = ctx["loc_list"]
    place_rows = grid_links([(l["name"], (l["function"] or "")[:70],
                              f'world/{l["id"]}.html') for l in places])
    why_rows = []
    for t in vol_sorted(ctx, ctx["timeline"], lambda r: r["vol_id"]):
        if not t["why"]:
            continue
        c = ctx["char_by_id"].get(t["char_id"])
        name = c["name"] if c else t["name"]
        why_rows.append(
            f'<div class="scene"><div class="head">'
            f'<span class="pg">{vol_link(ctx, t["vol_id"], "guides")}</span>'
            f'<span class="who">{S.esc(name)}</span></div>'
            f'<p>{S.esc(D.clean(t["why"]))}</p></div>')
    body = f"""<h2 id="search">Say it in your own words</h2>
<p>Press <code>/</code> and type the fragment you remember — a name, a line,
an exam. Search runs over every page here, including the quoted text.</p>
<h2 id="volumes">I remember roughly when</h2>
{"".join(vol_links)}
<h2 id="places">I remember where</h2>
{place_rows}
<h2 id="beats">I remember it mattered</h2>
<p>The turning points the records flag, in order.</p>
{"".join(why_rows[:80])}"""
    html_out = ctx["page"](
        "Find that moment", "guides", body,
        [("Home", "index.html"), ("Start here", "guides/index.html"),
         ("Find that moment", None)],
        out="guides/find-that-moment.html", rail=guides_rail(ctx),
        lede="The recall page: hunt by time, place, or why it stuck.",
        kicker="Reader door", tagline_label="Recall", scope=ctx["scope"])
    return ("guides/find-that-moment.html", html_out)


# --------------------------------------------------------------- appendix


def appendix_rail(ctx):
    return [{"kind": "link", "label": "Appendix index",
             "href": "appendix/index.html"},
            {"kind": "link", "label": "How to read a citation",
             "href": "appendix/citations.html"},
            {"kind": "link", "label": "Coverage: what the evidence reaches",
             "href": "appendix/coverage.html"},
            {"kind": "link", "label": "Downloads",
             "href": "appendix/downloads.html"}]


def citations_page(ctx):
    rows = []
    for v in ctx["vol_list"]:
        rows.append(
            f'<tr><td><code>{S.esc(v["id"])}</code></td>'
            f'<td><a href="{posixpath.relpath(volume_index_href(v["id"]), "appendix")}">'
            f'{S.esc(v["label"])}</a></td>'
            f'<td>{S.esc(site_arch.volume_kind_label(v["kind"]))}</td>'
            f'<td>{v["pages"]}</td></tr>')
    body = f"""<h2 id="key">The citation key</h2>
<p>A citation is three parts: year, volume, page.
<code>y2v9 p.13</code> is Year 2, Volume 9, page 13. A range
(<code>pp. 118–121</code>) means the passage runs across those pages. Side
stories are numbered between the main volumes — <code>y1v4.5</code> is the
interlude that sits after Volume 4 — and the Year 0 material is cited
<code>y0</code>.</p>
<p>Pages follow the printed volumes, so they match the English ebook and the
physical book rather than any fan transcription.</p>
<h2 id="volumes">Every volume and its key</h2>
<table><thead><tr><th>Cite key</th><th>What it is</th><th>Kind</th>
<th>Pages</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
<h2 id="sound">How to read a quote here</h2>
<p>Everything between quotation marks is the novel's own text, copied from
the file rather than recalled. Click a citation chip to see the words the
archive found on that page. Where the archive is inferring something — that
an unnamed girl is Kushida, for instance — it says 'inference' in the
sentence that makes the claim.</p>"""
    return ("appendix/citations.html", ctx["page"](
        "How to read a citation", "appendix", body,
        [("Home", "index.html"), ("Appendix", "appendix/index.html"),
         ("Citations", None)],
        out="appendix/citations.html", rail=appendix_rail(ctx),
        lede="What the keys mean and why the text between quote marks can "
             "be trusted.",
        kicker="Reference", tagline_label="Appendix", scope=ctx["scope"]))


def coverage_page(ctx):
    rows = []
    for v in ctx["vol_list"]:
        st = ctx["walk"].get(v["id"], {})
        chs = len(st.get("chapters", []))
        docs = [i for i in ctx["vol_docs"].values() if i["vol"] == v["id"]]
        ledgers = []
        for f in sorted(D.LEDGERS.rglob("*.md")):
            text = f.read_text(encoding="utf-8", errors="replace")
            if re.search(rf"walk:\s*{re.escape(v['id'])}\s", text):
                ledgers.append(f)
        state = ("Transcribed line by line" if st.get("complete")
                 else ("Partway" if st.get("markers") else "Records only"))
        rows.append(
            f'<tr><td><a href="{posixpath.relpath(volume_index_href(v["id"]), "appendix")}">'
            f'{S.esc(v["label"])}</a></td><td>{S.esc(state)}</td>'
            f'<td>{chs}</td><td>{len(ledgers)}</td><td>{len(docs)}</td>'
            f'<td>{v["pages"]}</td></tr>')
    body = f"""<h2 id="state">Evidence by volume</h2>
<p>The archive is built in two layers. <strong>Records</strong> come from the
indexing pass and cover every volume: exam runs, arc states, relationships,
quoted lines with page numbers. <strong>Transcription</strong> is slower and
finer — a volume read chapter by chapter, with every line and beat captured.
Only transcribed volumes can support the scene-by-scene documents.</p>
<table><thead><tr><th>Volume</th><th>Evidence</th><th>Chapters transcribed</th>
<em></em><th>Ledgers touched</th><th>Documents</th><th>Pages</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
<h2 id="limits">What this does not do</h2>
<ul>
<li>It does not settle attribution beyond what the novel states. Where the
speaker is only implied, the entry says so.</li>
<li>It does not summarise from memory. If a page cannot cite a page number,
it does not assert the fact.</li>
<li>It is not complete yet: transcription has reached the first volume, and
each new volume widens every section at once.</li>
</ul>"""
    return ("appendix/coverage.html", ctx["page"](
        "Coverage", "appendix", body,
        [("Home", "index.html"), ("Appendix", "appendix/index.html"),
         ("Coverage", None)],
        out="appendix/coverage.html", rail=appendix_rail(ctx),
        lede="How far the evidence reaches, volume by volume.",
        kicker="Reference", tagline_label="Appendix", scope=ctx["scope"]))


def downloads_page(ctx):
    pdf_dir = ROOT / "share" / "site" / "pdfs"
    names = sorted(p.stem for p in pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    rows = "".join(
        f'<li><a href="../pdfs/{n}.pdf">{S.esc(n.replace("-", " ").title())}'
        f'</a></li>' for n in names)
    body = f"""<h2 id="pdf">PDF bundles</h2>
<p>Print-ready bundles of the reference sections, generated from the same
build as this site.</p>
<ul>{rows or '<li>No bundles in this build.</li>'}</ul>
<h2 id="offline">Opening the archive without a server</h2>
<p>The whole site is static files. Save the folder and open
<code>index.html</code>; search and the citation chips still work with no
network.</p>"""
    return ("appendix/downloads.html", ctx["page"](
        "Downloads", "appendix", body,
        [("Home", "index.html"), ("Appendix", "appendix/index.html"),
         ("Downloads", None)],
        out="appendix/downloads.html", rail=appendix_rail(ctx),
        lede="PDF bundles and how to use the archive offline.",
        kicker="Reference", tagline_label="Appendix", scope=ctx["scope"]))


def appendix_index(ctx):
    stats = ctx["stats"]
    walked = sum(1 for s in ctx["walk"].values() if s.get("complete"))
    body = f"""<h2 id="reference">Reference pages</h2>
<div class="doors">
{door("Citations", "What does y2v9 p.13 mean?",
      "The key, the page convention, and why the quoted text is exact.",
      "appendix/citations.html")}
{door("Coverage", "How much of the series is in here?",
      "Volume by volume: transcribed, partway, or records only.",
      "appendix/coverage.html")}
{door("Downloads", "Can I take it with me?",
      "PDF bundles and the offline folder.", "appendix/downloads.html")}
</div>
<h2 id="method">How this archive was made</h2>
<p>Thirty-six translated volumes were converted to text with their page
breaks intact, indexed, and then read through volume by volume. Character
ledgers were written chapter by chapter; the pages you are reading are
assembled from those ledgers and the curated records beside them. Every
statement carries the page it came from so you can check it rather than
trust it.</p>
<div class="box note"><h4>At a glance</h4><p>{stats['chars']} characters ·
{stats['vols']} volumes · {stats['quotes']:,} quoted lines indexed ·
{walked} volume{'' if walked == 1 else 's'} transcribed line by line.</p></div>"""
    return ctx["page"]("Appendix", "appendix", body,
                      [("Home", "index.html"), ("Appendix", None)],
                      out="appendix/index.html", rail=appendix_rail(ctx),
                      lede="The machinery of the archive: citations, "
                           "coverage, downloads and method.",
                      kicker="Reference", tagline_label="Appendix",
                      scope=ctx["scope"])


# --------------------------------------------------- volume documents


DOC_STEM_RE = re.compile(r"^(?P<char>[a-z0-9-]+?)(?:\.(?P<vol>y[0-9v.]+?))?"
                         r"\.(?P<kind>article|transcript)$")


def build_vol_docs(ctx):
    """Render drafts/people/*.md into story/v/<vol>/<char>-(guide|transcript).html."""
    pages = []
    for f in sorted(DRAFTS.glob("*.md")) if DRAFTS.exists() else []:
        m = DOC_STEM_RE.match(f.stem)
        if not m:
            continue
        char_id = m.group("char")
        kind = "guide" if m.group("kind") == "article" else "transcript"
        md = f.read_text(encoding="utf-8")
        vol = m.group("vol") or dominant_vol(md)
        if vol not in ctx["vols"]:
            vol = dominant_vol(md)
        c = ctx["char_by_id"].get(char_id)
        char_name = c["name"] if c else site_arch.display_name("", char_id)
        out = f"story/v/{vol}/{char_id}.{'guide' if kind == 'guide' else 'transcript'}.html"
        body, headings = render_full(md)
        body = S.resolve_links(body, f"drafts/people/{f.name}",
                               ctx["pathmap"], out)
        body = S.chipify(body, ctx["lookup"])
        body = section_scope(body, ctx["vols"])
        label = "Volume guide" if kind == "guide" else "Scene transcript"
        title = f"{char_name} — {site_arch.volume_short(vol)} {label.lower()}"
        docs_here = [i for i in ctx["vol_docs"].values()
                     if i["vol"] == vol and i["char_id"] == char_id]
        related = [((("Scene transcript" if i["kind"] == "transcript"
                      else "Volume guide")), posixpath.basename(i["out"]))
                   for i in docs_here]
        related.append(("Back to the volume",
                        posixpath.relpath(volume_index_href(vol),
                                          posixpath.dirname(out))))
        html_out = ctx["page"](
            title, "story", body,
            [("Home", "index.html"), ("Story", "story/index.html"),
             (f"Year {ctx['vols'][vol]['year'] or 0}",
              f"story/y{ctx['vols'][vol]['year']}.html"),
             (site_arch.volume_short(vol), volume_index_href(vol)),
             (title, None)],
            out=out, rail=story_rail_for(ctx, vol),
            lede=f"{label} for {char_name} in "
                 f"{site_arch.volume_label(vol)}.",
            kicker=f'{site_arch.volume_label(vol)} · {label}',
            tagline_label="Person", headings=headings,
            related=related, scope=ctx["scope"])
        ctx["vol_docs"][f"{char_id}.{vol}.{kind}"] = {
            "char_id": char_id, "char_name": char_name, "vol": vol,
            "kind": kind, "out": out, "title": title}
        pages.append((out, html_out))
    return pages


def story_rail_for(ctx, vol_id):
    v = ctx["vols"].get(vol_id)
    items = [{"kind": "link", "label": "The story in order",
              "href": "story/index.html"}]
    if not v:
        return items
    peers = [x for x in ctx["vol_list"] if x["year"] == v["year"]]
    items.append({
        "kind": "details",
        "label": {0: "Side stories", 1: "Year 1", 2: "Year 2",
                  3: "Year 3"}[v["year"]],
        "href": f"story/y{v['year']}.html", "count": len(peers), "open": True,
        "sub": [{"label": f'{x["short"]} · '
                          f'{site_arch.volume_number(x["id"])}',
                 "href": volume_index_href(x["id"])} for x in peers]})
    return items

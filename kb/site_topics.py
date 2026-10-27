#!/usr/bin/env python3
"""Topics, reader doors, appendix, and the volume documents (the guides and
scene transcripts the walk produced into drafts/).

Topics are the 'reorganised by question' layer: each page is a query over
the walk ledgers (site_ledgers.scan), never a summary written from memory
or from the retired dossier layer. Where the ledgers only partially answer
a question, the page says so at the top and names the volumes it covers.

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
import site_evidence as E  # noqa: E402
import site_ledgers as L  # noqa: E402
import site_shell as S  # noqa: E402
from share_render import slug, render_full  # noqa: E402
from site_sections import (alpha_nav, door, dominant_vol, entity_page_href,  # noqa: E402
                           facts_strip, grid_links, section_scope,
                           volume_index_href)

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
    {"id": "relationships", "title": "Relationships, with evidence",
     "lede": "Who is aligned, opposed, or indebted to whom, on the pages "
             "that have actually been read."},
    {"id": "who-knew-what", "title": "Who knew what, and when",
     "lede": "What each character is recorded as knowing, volume by volume "
             "— the layer that makes the reveals land."},
    {"id": "expulsions", "title": "Expulsions and near-misses",
     "lede": "Every moment, so far, that the school put a student's place "
             "on the table."},
    {"id": "points", "title": "Points, prices and payouts",
     "lede": "The numbers the volumes read so far actually moved on."},
    {"id": "results", "title": "Winners, placements and consequences",
     "lede": "What each exam decided in the volumes read so far, in the "
             "order it was decided."},
]


def topics_index(ctx):
    rows = "".join(
        f'<a class="door" href="topics/{t["id"]}.html">'
        f'<span class="q">{S.esc(t["title"])}</span>'
        f'<span class="d">{S.esc(t["lede"])}</span>'
        f'<span class="go">Open →</span></a>' for t in TOPICS)
    body = f"""<h2 id="questions">Question pages</h2>
<p>These pages cut across the volumes that have been read line by line: pick the question
rather than the entity. Each statement carries the page it came from.</p>
<div class="doors">{rows}</div>
<h2 id="building">How a topic page is built</h2>
<p>A topic is a query over the line-by-line notes — the same notes that
build the character and volume pages. Each note is one observation written
against a page number, so a topic page can only be as broad as the volumes
that have been read, and it says at the top how far they reach. Volumes not
yet read simply do not appear.</p>"""
    return ctx["page"]("Topics", "topics", body,
                      [("Home", "index.html"), ("Topics", None)],
                      out="topics/index.html", rail=topics_rail(ctx),
                      lede="Answers to the questions people actually ask, "
                           "assembled from the pages that hold them.",
                      kicker="By question", tagline_label="Topics",
                      scope=ctx["scope"])


def topic_related(ctx, topic):
    """The neighbouring questions, plus where the evidence for this one is
    kept: the volume pages the entries came from."""
    links = [(t["title"], f"topics/{t['id']}.html")
             for t in TOPICS if t["id"] != topic["id"]]
    links.append(("Every relationship note", "topics/relationships.html"))
    for vol in sorted(ctx["evidence"],
                      key=lambda v: ctx["vols"][v]["order"] if v in ctx["vols"] else 999):
        v = ctx["vols"].get(vol)
        if v:
            links.append((f"Read in {v['label']}", volume_index_href(vol)))
    return links


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
        related=topic_related(ctx, topic), scope=ctx["scope"])
    return (f"topics/{topic['id']}.html", html_out)


# ------------------------------------------------------------- ledger topics
#
# A topic page answers one question across the whole series. The old version
# of this file answered them by reading the pre-walk analysis tables, which
# is where the fabricated claims came from. Every topic now scans the walk
# ledgers and shows the anchored entries themselves.

# Which section index to fall back on when a ledger has no page of its own.
KIND_INDEX = {"people": "people/index.html", "exams": "school/index.html",
              "systems": "school/index.html", "places": "world/index.html",
              "concepts": "topics/index.html"}


def entity_href(ctx, kind, stem):
    """Site-relative page for a ledger stem, or '' when the build makes no
    page for it. One resolver, so a link built here lands on the same URL the
    entity's own name links to."""
    c = ctx["char_by_id"].get(stem) if kind == "people" else None
    if c:
        return c["href"]
    if kind == "people":
        # collect_metas gives every walked stem its own page
        return f"people/{stem}.html"
    return entity_page_href(ctx, kind, stem)


def scene_anchor(block):
    """The id site_evidence.scene_block writes on a scene. Kept in step with
    that function: same slug source (the heading), same 48-character cut."""
    return re.sub(r"[^a-z0-9]+", "-", block["heading"].lower()).strip("-")[:48]


def scene_href(ctx, kind, stem, block):
    """Where a scene is actually written: its own block on the entity page,
    fragment included. Falls back to the section index only when the build
    makes no page for the entity."""
    page = entity_href(ctx, kind, stem)
    if not page:
        return KIND_INDEX[kind]
    # minor characters live under an anchor on a letter page
    # (people/minor/i.html#ike-kanji); a URL takes one fragment, and the
    # scene id is the more specific one
    page = page.split("#", 1)[0]
    return f"{page}#ev-{scene_anchor(block)}"


def pin_for(ctx, kind, stem, vol, block, entry, base="topics"):
    """The page number on a summary row, as a link to the scene it was read
    from. Rows on a topic or recall page are second-hand: the scene itself, with
    the verbatim lines it produced, lives on the entity's page, so the number is
    the reader's way back to it."""
    if not entry["pages"]:
        return ""
    href = posixpath.relpath(scene_href(ctx, kind, stem, block), base)
    return E.pin(entry["pages"], href=href)


def entity_link(ctx, kind, stem, base="topics"):
    """Name a ledger's subject as a link to its page. Ledgers are filed under
    the id the walk wrote, pages under the database's; entity_page_href
    resolves that and returns '' when the build makes no page, so the link
    falls back to the section index instead of pointing at nothing."""
    href = entity_href(ctx, kind, stem) or KIND_INDEX[kind]
    c = ctx["char_by_id"].get(stem) if kind == "people" else None
    if c:
        name = c["name"]
    else:
        led = L.load(kind, stem)
        name = (led["title"].split(" — ")[0]) if led else site_arch.display_name("", stem)
    return f'<a href="{posixpath.relpath(href, base)}">{S.esc(name)}</a>'


def entry_row(ctx, kind, stem, vol, block, entry, base="topics"):
    """One anchored ledger entry as a row: who/what, the scene it came from,
    the text, and the page it is on. The scene title and the page open the
    block on the entity page, so a row can be followed to its source."""
    link = posixpath.relpath(scene_href(ctx, kind, stem, block), base)
    pin = pin_for(ctx, kind, stem, vol, block, entry, base=base)
    return (
        f'<div class="scene"><div class="head">'
        f'<span class="pg">{E.vol_chip(ctx, vol, f"{base}/x.html")}</span>'
        f'<span class="who">{entity_link(ctx, kind, stem, base)}'
        f' — <a href="{link}">{S.esc(block["title"])}</a></span></div>'
        f'<p>{S.esc(entry["text"])}</p>'
        f'{pin}</div>')


def grouped(ctx, rows, key):
    """Rows grouped under h2 headings, in the order the story tells them."""
    buckets = {}
    for row in rows:
        buckets.setdefault(key(row), []).append(row)
    out = []
    for label, items in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        out.append(f'<h2 id="{slug(str(label))}">{S.esc(str(label))}</h2>'
                   f'{"".join(items)}')
    return "".join(out), len(buckets)


def evidence_volumes(ctx):
    return sorted(ctx["evidence"],
                  key=lambda v: ctx["vols"][v]["order"] if v in ctx["vols"] else 999)


def coverage_line(ctx):
    vols = evidence_volumes(ctx)
    labels = ", ".join(site_arch.volume_short(v) for v in vols)
    blocks = sum(ctx["evidence"][v]["blocks"] for v in vols)
    return (f"{blocks} scene entries anchored to a page, from "
            f"{labels}. This page grows as each volume is read line by line; "
            f"nothing here is summarised from memory.")


def build_relationships(ctx):
    pairs = {}
    for kind, stem, vol, block, entry in L.scan(("people", "places")):
        if entry["marker"] != "rel" or not entry["target"]:
            continue
        a, b = sorted([stem, entry["target"]])
        pairs.setdefault((a, b), []).append((kind, stem, vol, block, entry))
    rows = []
    for (a, b), hits in pairs.items():
        names = []
        for cid in (a, b):
            c = ctx["char_by_id"].get(cid)
            if c:
                names.append(f'<a href="{posixpath.relpath(c["href"], "topics")}">'
                             f'{S.esc(c["name"])}</a>')
            else:
                names.append(S.esc(site_arch.display_name("", cid)))
        inner = "".join(
            f'<div class="scene"><div class="head">'
            f'<span class="pg">{E.vol_chip(ctx, vol, "topics/x.html")}</span>'
            f'<span class="who">{S.esc(block["title"])}</span></div>'
            f'<p>{S.esc(e["text"])}</p>'
            f'{pin_for(ctx, _k, _s, vol, block, e)}'
            f'</div>'
            for _k, _s, vol, block, e in sorted(hits, key=lambda h: (
                ctx["vols"][h[2]]["order"] if h[2] in ctx["vols"] else 999)))
        rows.append((len(hits), a,
                     f'<div class="scene pair"><div class="head">'
                     f'<span class="ttl">{" ↔ ".join(names)}</span>'
                     f'<span class="n">{len(hits)} anchored note'
                     f'{"s" if len(hits) != 1 else ""}</span></div>{inner}</div>'))
    rows.sort(key=lambda r: (-r[0], r[1].lower()))
    body = f'<h2 id="pairs">Every pair the pages record</h2>{"".join(r[2] for r in rows)}'
    return topic_shell(ctx, TOPICS[0], coverage_line(ctx), body)


def build_who_knew_what(ctx):
    """The knowledge layer as the text states it: what a character thinks,
    what the walk flagged as inference rather than fact, and where their
    standing changed."""
    rows = []
    for kind, stem, vol, block, entry in L.scan(("people",)):
        if entry["marker"] not in ("thinks", "note", "status", "limit"):
            continue
        c = ctx["char_by_id"].get(stem)
        label = L.marker_info(entry["marker"], entry["target"])[1]
        rows.append((
            ctx["vols"][vol]["order"] if vol in ctx["vols"] else 999,
            f'<div class="scene"><div class="head">'
            f'<span class="pg">{E.vol_chip(ctx, vol, "topics/x.html")}</span>'
            f'<span class="who">{entity_link(ctx, "people", stem)}</span>'
            f'<span class="n">{S.esc(label)} · {S.esc(block["title"])}</span></div>'
            f'<p>{S.esc(entry["text"])}</p>'
            f'{pin_for(ctx, "people", stem, vol, block, entry)}'
            f'</div>'))
    rows.sort(key=lambda r: r[0])
    body = "".join(r[1] for r in rows)
    return topic_shell(ctx, TOPICS[1], coverage_line(ctx), body)


def scan_pattern(ctx, pattern, markers=None):
    rows = []
    for kind, stem, vol, block, entry in L.scan():
        if markers and entry["marker"] not in markers:
            continue
        if not pattern.search(entry["text"]):
            continue
        rows.append((kind, stem, vol, block, entry))
    return rows


def build_expulsions(ctx):
    hits = scan_pattern(ctx, EXPEL_RE)
    rows = [entry_row(ctx, kind, stem, vol, block, e)
            for kind, stem, vol, block, e in sorted(
                hits, key=lambda h: (ctx["vols"][h[2]]["order"]
                                     if h[2] in ctx["vols"] else 999))]
    body = f"".join(rows)
    note = (f"{len(rows)} entries use the words 'expel', 'drop out', "
            f"'vote' or 'leaving the school'. It is a locator, not a ruling: "
            f"the rule text lives on the <a href=\"school/system/expulsion.html\">"
            f"expulsion system page</a>, and that page is only as full as the "
            f"volumes that have been read.")
    return topic_shell(ctx, TOPICS[2], note + " " + coverage_line(ctx), body)


def build_points(ctx):
    hits = scan_pattern(ctx, POINT_RE)
    rows = [entry_row(ctx, kind, stem, vol, block, e)
            for kind, stem, vol, block, e in sorted(
                hits, key=lambda h: (ctx["vols"][h[2]]["order"]
                                     if h[2] in ctx["vols"] else 999))]
    body = f'<h2 id="the-numbers">Every figure the pages anchor</h2>{"".join(rows)}'
    note = (f"{len(rows)} point figures anchored to a page. The written rules "
            f"behind them are on the <a href=\"school/system/class-points.html\">"
            f"class points</a> and <a href=\"school/system/private-points.html\">"
            f"private points</a> pages. {coverage_line(ctx)}")
    return topic_shell(ctx, TOPICS[3], note, body)


def build_results(ctx):
    """Exam outcomes as the walk wrote them: the exam ledgers' result, rule,
    fact and impact entries, plus anything a person's ledger calls a
    placement."""
    rows = []
    for kind, stem, vol, block, entry in L.scan(("exams", "systems", "people")):
        if entry["marker"] not in ("result", "rule", "fact", "impact", "number",
                                   "feat", "status") and not WIN_RE.search(entry["text"]):
            continue
        rows.append((
            ctx["vols"][vol]["order"] if vol in ctx["vols"] else 999,
            f'<div class="scene"><div class="head">'
            f'<span class="pg">{E.vol_chip(ctx, vol, "topics/x.html")}</span>'
            f'<span class="who">{entity_link(ctx, kind, stem)}</span>'
            f'<span class="n">{S.esc(block["title"])}</span></div>'
            f'<p>{S.esc(entry["text"])}</p>'
            f'{pin_for(ctx, kind, stem, vol, block, entry)}'
            f'</div>'))
    rows.sort(key=lambda r: r[0])
    body = "".join(r[1] for r in rows)
    note = f"{len(rows)} recorded outcomes, each with the volume and page it " \
           f"was read on. {coverage_line(ctx)}"
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
    walked = sorted(ctx["evidence"], key=lambda k: order(ctx, k))
    wlist = ", ".join(site_arch.volume_label(w) for w in walked)
    stats = ctx["stats"]
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
<strong>{S.esc(site_arch.volume_label(walked[0]) if walked else "Volume 1")}</strong>:
it is the first volume transcribed line by line, so you can read the whole
shape of it with page numbers attached, or open a character's scene
transcript and see exactly how the first mask is worn.</p>
<h2 id="trust">How much to trust a page here</h2>
<p>Everything inside quotation marks is the novel's own text; every note
carries a volume and a page; and the notes were taken off the page, not from
anyone's memory of the plot. {len(walked)} of {stats['vols']} volumes have been read that way
— {wlist} — so everywhere else the page is a roster of mechanical facts
plus a plain statement of what has not been checked yet.</p>"""
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
    places = sorted(ctx["loc_list"], key=lambda l: l["name"])
    place_rows = grid_links([(l["name"],
                              f'named {l["mentions"]:,} times',
                              f'world/{l["id"]}.html') for l in places])
    why_rows = []
    for kind, stem, vol, block, entry in L.scan(("people", "exams", "systems")):
        if entry["marker"] not in ("feat", "status", "impact", "trait", "rule"):
            continue
        # the note is only useful if it can be followed back to the scene it
        # came from: title and page both open that block on the entity page
        link = posixpath.relpath(scene_href(ctx, kind, stem, block), "guides")
        pin = (f'<a class="cite" href="{link}">{S.esc(entry["pages"])}</a>'
               if entry["pages"] else "")
        why_rows.append(
            (order(ctx, vol),
             f'<div class="scene"><div class="head">'
             f'<span class="pg">{vol_link(ctx, vol, "guides")}</span>'
             f'<span class="who">{entity_link(ctx, kind, stem, "guides")}'
             f' — <a href="{link}">{S.esc(block["title"])}</a></span></div>'
             f'<p>{S.esc(entry["text"])}</p>{pin}</div>'))
    why_rows.sort(key=lambda r: r[0])
    why_rows = [r[1] for r in why_rows]
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
<p>A citation on these pages is written the way a reader says it:
<code>Vol. 1 p.247</code> — Year 1, Volume 1, page 247. Each volume also
has a short key used inside the archive, <code>y1v1</code>, so Year 1
Volume 1; a range
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
the file rather than recalled. Those copied lines live as rows inside the scene
they were read into, which is why a page number is never a button here: the
scene's own <strong>+</strong> already opens them, and a second control over the
same pages would only show a shorter version of what is on screen. Where a
citation sits in prose instead — a volume guide, an appendix note — the number
stays grey for the same reason in reverse: the archive holds the lines it
located inside scenes, not the book, so there is nothing there to open.
A bright chip with an arrow, <span class="cite">p.247 ↗</span>, is the one
citation that does something: it sits on a summary row whose scene is written
up on another page. Where the archive is inferring something — that an unnamed
girl is Kushida, for instance — it says 'inference' in the sentence that makes
the claim.</p>"""
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
<em></em><th>Notes anchored</th><th>Documents</th><th>Pages</th></tr></thead>
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
<code>index.html</code>; search and every page reference still work with no
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
    walked = sorted(ctx["evidence"], key=lambda k: order(ctx, k))
    body = f"""<h2 id="reference">Reference pages</h2>
<div class="doors">
{door("Citations", "What does “Vol. 1 p.247” mean?",
      "The key behind it, the page convention, and why the quoted text is exact.",
      "appendix/citations.html")}
{door("Coverage", "How much of the series is in here?",
      "Volume by volume: read line by line, or roster only.",
      "appendix/coverage.html")}
{door("Downloads", "Can I take it with me?",
      "PDF bundles and the offline folder.", "appendix/downloads.html")}
</div>
<h2 id="method">How this archive was made</h2>
<p>{stats['vols']} translated volumes were converted to text with their page
breaks intact and indexed, then read through one at a time. For each volume
it is worked through chapter by chapter, writing down scenes, spoken lines,
inner voice, numbers and rules — every entry pinned to the page it was read
on. The prose pages you are reading are assembled from those notes and nothing
else; a volume that has not been read that way shows only its mechanical record
(who is named on which page) and says so plainly. Every statement carries
the page it came from so you can check it rather than trust it.</p>
<div class="box note"><h4>At a glance</h4><p>{stats['chars']} characters ·
{stats['vols']} volumes · {stats['quotes']:,} quoted lines indexed ·
{len(walked)} of {stats['vols']} volumes read line by line
({', '.join(site_arch.volume_label(w) for w in walked)}),
{stats['scenes']} anchored scenes between them.</p></div>"""
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
        body = S.reference_cites(body)
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

#!/usr/bin/env python3
"""Page builders for every section of the site. Each builder returns
(out_path, html) pairs and registers its outputs in ctx['pathmap'] so that
links authored in the dossier markdown land on the new URLs.

The public taxonomy is deliberately small and in plain words:
  People · Story · Exams & School · World & Places · Topics · Start here ·
  Appendix
and inside People only 'Principal characters / Recurring characters /
Minor characters' plus the role groups a reader already expects from the
novel (allies, rivals, faculty, family). The database's tier numbers and
mid_type keys are never shown.
"""

import json
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
from share_render import render, slug  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOSSIERS = ROOT / "dossiers"

ROLE_GROUPS = ["allies", "rivals", "peers", "authority", "family", "outside"]

WEEK_NOTE = ("<p class='muted'>Evidence is quoted from the novels only. "
             "A page number you can check beats any summary here.</p>")

def reword(md):
    """Strip internal taxonomy and database phrasing out of authored dossier
    markdown before a reader sees it. The rules live in site_arch."""
    md = site_arch.public_words(md, site_arch.DOC_REWORD,
                                site_arch.PROSE_REWORD)
    return re.sub(r"\n{3,}", "\n\n", md)


def humanize(text):
    """Same wording rules, applied to a single line of curated prose (arc
    notes, 'why it mattered') rather than a whole document."""
    return site_arch.public_words(text or "", site_arch.PROSE_REWORD)


def dominant_vol(md):
    """The volume a document mostly cites — used to file a guide under the
    right volume page."""
    counts = {}
    for m in site_arch.PAGE_IN_CITE_RE.finditer(md):
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    if not counts:
        for m in site_arch.VOL_CITE_RE.finditer(md):
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return max(counts, key=lambda k: counts[k]) if counts else "y1v1"


def max_order(md, vols):
    order = 0
    for vol, _page in site_arch.parse_cites(md):
        v = vols.get(vol)
        if v:
            order = max(order, int(v["order"]))
    return order


def section_scope(text, vols):
    """Wrap each <h2> block in a spoiler marker using the latest volume the
    block cites."""
    parts = re.split(r"(?=<h2 )", text)
    out = []
    for block in parts:
        if not block.startswith("<h2 "):
            out.append(block)
            continue
        order = 0
        for m in site_arch.PAGE_IN_CITE_RE.finditer(block):
            v = vols.get(m.group(1))
            if v:
                order = max(order, int(v["order"]))
        if not order:
            out.append(block)
            continue
        label = f"after volume {order}"
        out.append(
            f'<section class="later" data-since-order="{order}">'
            f'{block}<button class="reveal" type="button" '
            f'title="This covers story material beyond your chosen point">'
            f'Spoiler · reveal anyway</button></section>')
    return "".join(out)


def facts_strip(pairs):
    cells = []
    for k, v in pairs:
        if not v:
            continue
        cells.append(f'<div><div class="k">{S.esc(k)}</div>'
                     f'<div class="v">{v}</div></div>')
    return f'<div class="facts">{"".join(cells)}</div>' if cells else ""


def pills(items):
    return "".join(f'<span class="pill">{S.esc(t)}</span>' for t in items)


def grid_links(rows):
    out = []
    for row in rows:
        label, note, href = row[:3]
        tags = row[3] if len(row) > 3 else label.lower()
        out.append(f'<a href="{href}" data-tags="{S.esc(tags)}">'
                   f'{S.esc(label)}<span class="n">{S.esc(note)}</span></a>')
    return f'<div class="grid-list" data-filterable>{"".join(out)}</div>'


def filter_chip(label, want, on=False):
    return (f'<button type="button" class="{"on" if on else ""}" '
            f'data-filter="{want}">{S.esc(label)}</button>')


def filter_host(chips, inner):
    return (f'<div class="filter-host"><div class="filters">'
            f'{chips}</div>{inner}</div>')


def alpha_nav(current="", letters=None):
    """A–Z strip. Links are written from the site root so the shell can
    rebase them for whatever page embeds the strip; letters with no page
    are shown as disabled, never as a dead link."""
    have = {l.upper() for l in (letters or [chr(c) for c in range(65, 91)])}
    out = []
    for l in [chr(c) for c in range(65, 91)]:
        if l in have:
            on = " on" if l == current else ""
            out.append(f'<a class="{on.strip()}" '
                       f'href="people/minor/{l.lower()}.html">{l}</a>')
        else:
            out.append(f'<span class="off" aria-disabled="true">{l}</span>')
    return f'<nav class="alpha-nav">{"".join(out)}</nav>'


def door(label, question, desc, href, root=""):
    return (f'<a class="door" href="{root}{href}">'
            f'<span class="q">{S.esc(question)}</span>'
            f'<span class="d">{S.esc(desc)}</span>'
            f'<span class="go">{S.esc(label)} →</span></a>')


# ---------------------------------------------------------------- home


def home(ctx):
    stats = ctx["stats"]
    v = ctx["vols"]
    walked = sorted(ctx["evidence"], key=lambda k: order_of(ctx, k))
    doors = "".join([
        door("Find a person", "Who is this character, and what do they do?",
             "Every named character, with page-anchored notes for the "
             "volumes that have been read line by line.",
             "people/index.html"),
        door("Read in order", "What happens in a given volume?",
             "The chronological spine: year by year, volume by volume.",
             "story/index.html"),
        door("Check a rule", "How did that exam actually work?",
             "Each exam's runs and point swings, scene by scene, in the "
             "words the pages use.",
             "school/index.html"),
        door("Ask a question", "Who got expelled, and when?",
             "Cross-cutting topic pages built from the volumes read line "
             "by line.",
             "topics/index.html"),
        door("Write in the world", "I need Ayanokōji's actual voice.",
             "Doors built for writers, number-crunchers and the rusty.",
             "guides/index.html"),
        door("Locate a scene", "Where exactly did that happen?",
             "Every named place and the pages it appears on.",
             "world/index.html"),
    ])
    sections = "".join(
        f'<div class="card"><h3>{S.esc(s["label"])}</h3>'
        f'<p>{S.esc(s["blurb"])}</p>'
        f'<a class="go" href="{s["href"]}">Open →</a></div>'
        for s in site_arch.SECTIONS)
    body = f"""<div class="hero">
<h1>The book, reorganised by question</h1>
<p>An annotated archive of the <em>Classroom of the Elite</em> light novels
built from the translated volumes themselves. Every claim here is a note
taken off a printed page: the line quoted as written, the page number
attached, and a marker wherever nothing has been read line by line yet.</p>
<div class="stats">
<div><b>{stats['chars']}</b><span>characters</span></div>
<div><b>{stats['vols']}</b><span>volumes</span></div>
<div><b>{stats['exams']}</b><span>exams</span></div>
<div><b>{stats['places']}</b><span>places</span></div>
<div><b>{stats['quotes']:,}</b><span>quoted lines</span></div>
<div><b>{stats['walked']}</b><span>volumes read line by line</span></div>
</div>
</div>
<h2 id="start">Where do you want to start?</h2>
<div class="doors">{doors}</div>
<h2 id="library">The library</h2>
<div class="cards">{sections}</div>
<h2 id="reading-a-page">Reading a page</h2>
<p><strong>Bold labels</strong> say what kind of note the page produced —
<em>Spoken</em> is dialogue, <em>Inner voice</em> is the narrator's thoughts,
<em>What happens</em> is action. “Curly quotes” inside them are the novel's own
words. Each scene is tagged with its volume and a page such as
<span class="cite">p.247</span> — click it to see the text sitting on that page.</p>
<p>Reading in progress? Choose <em>I've read up to…</em> in the bar above and
anything later in the story stays folded until you open it. Your choice is
remembered on this device.</p>
<p>Prose on this site comes from one place: a line-by-line reading pass, which
takes a volume page by page and writes down only what is on a named page.
That has reached {len(walked)} volume{'' if len(walked) == 1 else 's'} so far
({', '.join(S.esc(site_arch.volume_label(w)) for w in walked)}, {stats['scenes']}
anchored scenes between them). Everything those volumes do not cover is
clearly marked as not yet worked through, and shows the mechanical facts —
who is named on which page — rather than remembered summaries.</p>"""
    return ctx["page"]("COTE Knowledge Base", "home", body,
                      [("Home", "index.html")], out="index.html",
                      rail=[], lede="", kicker="Annotated archive",
                      title_note="home")


# --------------------------------------------------------------- people


def people_rail(ctx, root=""):
    items = [{"kind": "link", "label": "All people",
              "href": "people/index.html"}]
    items.append({"kind": "link", "label": "Principal characters",
                  "href": "people/index.html#principal"})
    items.append({"kind": "link", "label": "Recurring characters",
                  "href": "people/index.html#recurring"})
    items.append({"kind": "link", "label": "Minor characters A–Z",
                  "href": "people/minor/a.html"})
    named = [c for c in ctx["chars"] if c["tier"] <= 2]
    principals = [c for c in named if c["tier"] == 1]
    if principals:
        items.append({"kind": "details", "label": "Principal", "open": False,
                      "sub": [{"label": c["name"], "href": c["href"]}
                              for c in principals]})
    for g in ROLE_GROUPS:
        grp = [c for c in named if c["group"] == g]
        if grp:
            items.append({
                "kind": "details", "label": site_arch.GROUP_LABEL[g],
                "count": len(grp), "open": ctx.get("open_group") == g,
                "sub": [{"label": c["name"], "href": c["href"]}
                        for c in sorted(grp, key=lambda c: c["name"])]})
    return items


def people_index(ctx):
    by_id = ctx["char_by_id"]
    principals = [c for c in ctx["chars"] if c["tier"] == 1]
    recurring = [c for c in ctx["chars"] if c["tier"] == 2]
    minor = [c for c in ctx["chars"] if c["tier"] >= 3]

    def rows(pool):
        out = []
        for c in pool:
            note = f'{c["quotes"]:,} quoted lines · {c["quote_vols"]} vols'
            out.append((c["name"], note, c["href"]))
        return grid_links(out)

    group_blocks = []
    for g in ROLE_GROUPS:
        grp = sorted([c for c in recurring if c["group"] == g],
                     key=lambda c: c["name"])
        if not grp:
            continue
        inner = []
        for c in grp:
            inner.append(f'<li><a href="{c["href"]}">{S.esc(c["name"])}</a>'
                         f' <span class="n">· {c["quotes"]:,} lines</span>'
                         f'</li>')
        group_blocks.append(
            f'<div class="box note"><h4 id="g-{g}">'
            f'{S.esc(site_arch.GROUP_LABEL[g])}</h4><ul>{"".join(inner)}</ul>'
            f'</div>')

    # counts come from the plan, not the database tier, so a letter is only
    # linked when a page for it was actually built
    buckets = ctx.get("minor_buckets") or {}
    alpha = "".join(
        f'<a href="people/minor/{l.lower()}.html">{l} '
        f'<span class="n">{len(buckets[l])}</span></a>'
        if buckets.get(l) else '<span class="off" aria-disabled="true">' + l + '</span>'
        for l in [chr(i) for i in range(65, 91)])

    body = f"""<h2 id="principal">Principal characters</h2>
<p>The seven the series follows closest. Each profile carries a full arc,
relationships, and voice samples quoted from the pages.</p>
{rows(principals)}
<h2 id="recurring">Recurring characters</h2>
<p>Twenty people who keep coming back — grouped by where they stand to
Ayanokōji's class, the same way the novels introduce them.</p>
{"".join(group_blocks)}
<h2 id="minor">Minor characters</h2>
<p>{len(minor)} further names appear on the page — classmates in other
grades, staff, family, one-off strangers. They are indexed by initial and
each entry lists what the text actually says about them.</p>
<div class="alpha-nav">{alpha}</div>
<h2 id="all">Everyone, alphabetically</h2>
<p>The whole cast of {len(ctx['chars'])} in one list, sorted by family name
as the novels print it. Filter by role, or start typing in the search box
above.</p>
{filter_host(
    filter_chip("All of them", "", True)
    + filter_chip("Principal", "principal")
    + filter_chip("Recurring", "recurring")
    + filter_chip("Minor", "minor"),
    grid_links([(c['name'],
                 f'{site_arch.TIER_LABEL[c["tier"]]} · {c["quotes"]:,} lines',
                 c['href'],
                 "principal" if c["tier"] == 1 else
                 ("recurring" if c["tier"] == 2 else "minor"))
                for c in sorted(ctx['chars'],
                                 key=lambda c: (c['name'].split()[0],
                                                c['name']))]))}"""
    return ctx["page"]("People", "people", body,
                      [("Home", "index.html"), ("People", None)],
                      out="people/index.html", rail=people_rail(ctx),
                      lede="Everyone named in the Classroom of the Elite "
                           "novels, with what they do and where they do it.",
                      kicker="The cast", tagline_label="People",
                      scope=ctx["scope"])


def plan_minor(ctx):
    """Decide, before any page is rendered, which initial-page each minor
    character lands on and what anchor its entry uses. Everything else in the
    build (the roster, the A–Z rail, cross-links from story and topic pages)
    reads the href off the character record, so this has to run first.

    The list is the roster itself — the people table and its mention counts —
    not the old background dossier, which described characters from memory."""
    extra = []
    for stem in L.all_ledgers("people"):
        if stem not in ctx["char_by_id"]:
            extra.append({"id": stem,
                          "name": site_arch.display_name("", stem),
                          "canon": "", "tier": 3, "coverage": 0,
                          "href": f"people/{stem}.html"})
    minors = [c for c in ctx["chars"] if c["tier"] >= 3] + extra
    buckets = {}
    for c in minors:
        letter = (c["name"].split()[0][:1].upper() if c["name"] else "?")
        buckets.setdefault(letter, []).append((c["id"], c["name"], c))
    letters = sorted(buckets)
    for l, rows in buckets.items():
        for key, name, c in rows:
            c["href"] = f"people/minor/{l.lower()}.html#{c['id']}"
    ctx["minor_buckets"] = buckets
    ctx["minor_entries"] = buckets
    ctx["minor_letters"] = letters
    return ctx


def minor_pages(ctx):
    """One page per initial. Each entry carries what can be counted — the
    spellings the text uses and the volumes the name appears in — plus the
    transcribed scenes themselves where the walk reached that person."""
    plan_minor(ctx)
    pages = []
    letters = ctx["minor_letters"]
    buckets = ctx["minor_entries"]
    for l in letters:
        rows = sorted(buckets[l], key=lambda r: r[1])
        blocks = []
        for key, name, c in rows:
            led = L.load_for("people", key)
            note = (f'<span class="n">{site_arch.TIER_LABEL[c["tier"]]} · '
                    f'named in {c["coverage"]} volumes</span>')
            if led:
                inner = E.volume_sections(ctx, led, f"people/minor/{l.lower()}.html")
            else:
                inner = (f'<p class="mentions">'
                         f'{E.mentions_by_volume(ctx, key, f"people/minor/{l.lower()}.html")}'
                         f'</p>')
            blocks.append(f'<h3 id="{key}">{S.esc(name)}</h3>{note}'
                          f'<div class="measure">{inner}</div>')
        nav = alpha_nav(l, letters)
        listing = "".join(blocks)
        html_out = ctx["page"](
            f"Minor characters — {l}", "people",
            f"{nav}{listing}",
            [("Home", "index.html"), ("People", "people/index.html"),
             ("Minor characters", f"people/minor/{letters[0].lower()}.html"),
             (l, None)],
            out=f"people/minor/{l.lower()}.html",
            rail=people_rail(ctx),
            lede=f"{len(rows)} names beginning with {l}. Each entry lists "
                 f"where the text writes that name; scenes appear only where "
                 f"the volume has been read line by line.",
            kicker="Minor characters", tagline_label="People",
            related=[("Everyone, alphabetically", "people/index.html"),
                     ("Scenes read so far", "story/v/y1v1/index.html")],
            scope=ctx["scope"])
        pages.append((f"people/minor/{l.lower()}.html", html_out))
    return pages


def ledger_related(ctx, c, led=None):
    """Cross-links derived from the walk, not the old relations table: the
    people this character's own ledger names in [rel:…] entries, plus the
    volume guides and transcripts written for them."""
    links = []
    seen = set()
    for label, href in guide_links(ctx, c["id"]):
        links.append((label, href))
        seen.add(href)
    if not led:
        return links
    for section in led["vols"]:
        for block in section["blocks"]:
            for e in block["entries"]:
                if e["marker"] != "rel" or not e["target"]:
                    continue
                oc = ctx["char_by_id"].get(e["target"])
                if not oc or oc["href"] in seen or oc["id"] == c["id"]:
                    continue
                seen.add(oc["href"])
                links.append((oc["name"],
                              posixpath.relpath(oc["href"], "people")))
    return links


def person_page(ctx, meta):
    """A character page is the walk ledger for that character, and nothing
    else. Identity facts (spellings, which volumes the name is written in)
    are mechanical and always shown; the arc is only shown where someone has
    read it page by page."""
    cid = meta["char_id"]
    out_rel = meta["out"]
    c = ctx["char_by_id"].get(cid)
    title = c["name"] if c else meta["title"]
    if not c:
        c = {"id": cid, "name": title, "tier": 4, "coverage": 0,
             "quotes": 0, "quote_vols": 0, "href": out_rel,
             "letter": title[:1].upper()}
    led = L.load_for("people", cid)
    identity = (f'<h2 id="identity">Who this is</h2>'
                f'{E.identity_block(ctx, c, out_rel)}')
    if led:
        body = (E.volume_sections(ctx, led, out_rel, fold=True)
                + identity)
        lede = ("Read line by line: every scene below carries the page it was "
                "found on, and every page chip opens the text on that page.")
        meter = E.evidence_meters(ctx, led)
    else:
        body = identity + E.coverage_stub(ctx, subject=title, base="people")
        lede = (f"{site_arch.TIER_LABEL.get(c['tier'], 'Character')} — named "
                f"in {c['coverage']} of {ctx['stats']['vols']} volumes. Not "
                f"worked through line by line yet, so this page carries only "
                f"what can be counted.")
        meter = [("Named in", f'{c["coverage"]} volumes')]
    body = section_scope(S.chipify(body, ctx["lookup"]), ctx["vols"])
    related = ledger_related(ctx, c, led)
    rail_extra = [{"kind": "grp", "label": "This character"}]
    html_out = ctx["page"](
        title, "people", body,
        [("Home", "index.html"), ("People", "people/index.html"),
         (title, None)],
        out=out_rel, rail=people_rail(ctx) + rail_extra,
        lede=lede, kicker=site_arch.TIER_LABEL.get(c["tier"], "Character"),
        tagline_label="Person", related=related, meter=meter,
        scope=ctx["scope"])
    return (out_rel, html_out)


def first_sentence(md):
    for line in md.splitlines():
        t = line.strip()
        if not t or t.startswith(("#", "**", "`", "-", "<")):
            continue
        return re.sub(r"[*`]", "", t)[:240]
    return ""


def footprint(ctx, c):
    if not c:
        return []
    return [("Characters like this", f'{c["quotes"]:,} lines'),
            ("Cited across", f'{c["coverage"]} of {ctx["stats"]["vols"]} vols')]


def guide_links(ctx, char_id):
    out = []
    for stem, info in ctx["vol_docs"].items():
        if info["char_id"] != char_id:
            continue
        label = ("Volume guide" if info["kind"] == "guide"
                 else "Scene transcript")
        out.append((f'{label} — {site_arch.volume_short(info["vol"])}',
                    posixpath.relpath(info["out"], "people")))
    return out


def related_links(ctx, c):
    """Removed: relationship rows came from the pre-walk curated layer.
    Cross-links now come from ledger markers only — see ledger_related()."""
    return []


# ---------------------------------------------------------------- story


def story_rail(ctx):
    items = [{"kind": "link", "label": "The story in order",
              "href": "story/index.html"}]
    for year, label in [(1, "Year 1"), (2, "Year 2"), (3, "Year 3"),
                        (0, "Side stories")]:
        vols = [v for v in ctx["vol_list"] if v["year"] == year]
        if not vols:
            continue
        items.append({
            "kind": "details", "label": label, "href": f"story/y{year}.html",
            "count": len(vols), "open": ctx.get("open_year") == year,
            "sub": [{"label": f'{v["short"]} · {S.esc(v["label"])}'.replace(
                f'{v["short"]} · ', f'Vol. {site_arch.volume_number(v["id"])}'),
                     "href": volume_index_href(v["id"])} for v in vols]})
    return items


def volume_index_href(vol_id):
    return f"story/v/{vol_id}/index.html"


def doc_href_for(vol_id, kind):
    return f"story/v/{vol_id}/"


def story_index(ctx):
    years = []
    for year, label, blurb in [
        (1, "Year 1", "Classes D through A, the first four exams, and the "
                      "mask Ayanokōji wears."),
        (2, "Year 2", "A new class lineup, the festival wars, and the "
                      "expulsion votes."),
        (3, "Year 3", "Graduation year: the board's endgame."),
        (0, "Side stories", "Year 0 and the short volumes that fill the "
                            "gaps between years."),
    ]:
        vols = [v for v in ctx["vol_list"] if v["year"] == year]
        if not vols:
            continue
        rows = []
        for v in vols:
            st = ctx["walk"].get(v["id"], {})
            pill = ('<span class="pill done">line-by-line</span>'
                    if st.get("complete") else
                    ('<span class="pill part">in progress</span>'
                     if st.get("markers") else ""))
            ex = ctx["exams_by_vol"].get(v["id"], [])
            rows.append(
                f'<a class="vol-item" href="{volume_index_href(v["id"])}" '
                f'data-tags="vol">'
                f'<span class="num">{S.esc(site_arch.volume_number(v["id"]))}'
                f'<small>{S.esc(site_arch.volume_short(v["id"]))}</small></span>'
                f'<span><span class="ttl">{S.esc(story_title(ctx, v["id"]))}'
                f'</span><span class="sub">{v["pages"]} pages · '
                f'{len(ex)} exam run{"" if len(ex) == 1 else "s"} · '
                f'{len(D.present_chars(ctx["con"], v["id"]))} named '
                f'characters</span>'
                f'<span class="pills">{pill}</span></span></a>')
        years.append(
            f'<h2 id="y{year}">{S.esc(label)}</h2><p>{S.esc(blurb)}</p>'
            f'<div class="vol-list">{"".join(rows)}</div>')
    body = "".join(years) + f"""<h2 id="order">Reading order</h2>
<p>The novels run 36 volumes across three school years. Publication order and
story order are the same here, apart from the short side volumes, which slot
between the main arcs and are listed at each year's end.</p>"""
    return ctx["page"]("Story", "story", body,
                      [("Home", "index.html"), ("Story", None)],
                      out="story/index.html", rail=story_rail(ctx),
                      lede="Everything that happens, in the order it "
                           "happens — year by year, volume by volume.",
                      kicker="The spine", tagline_label="Story",
                      scope=ctx["scope"])


def story_title(ctx, vol_id):
    titles = ctx.get("vol_titles", {})
    if vol_id in titles:
        return titles[vol_id]
    return site_arch.volume_label(vol_id)


def year_page(ctx, year):
    vols = [v for v in ctx["vol_list"] if v["year"] == year]
    rows = []
    for v in vols:
        st = ctx["walk"].get(v["id"], {})
        ex = ctx["exams_by_vol"].get(v["id"], [])
        pill = ('<span class="pill done">line-by-line</span>'
                if st.get("complete") else
                ('<span class="pill part">in progress</span>'
                 if st.get("markers") else ""))
        rows.append(
            f'<a class="vol-item" href="{volume_index_href(v["id"])}">'
            f'<span class="num">{S.esc(site_arch.volume_number(v["id"]))}'
            f'<small>{S.esc(site_arch.volume_kind_label(v["kind"]))}'
            f'</small></span><span><span class="ttl">'
            f'{S.esc(story_title(ctx, v["id"]))}</span>'
            f'<span class="sub">{v["pages"]} pages · {len(ex)} exam run'
            f'{"s" if len(ex) != 1 else ""}</span>'
            f'<span class="pills">{pill}</span></span></a>')
    label = {0: "Side stories", 1: "Year 1", 2: "Year 2",
             3: "Year 3"}[year]
    blurb = {
        1: "The entrance year: Class D, the point economy, the first four "
           "special exams, and the reveal of what Ayanokōji is willing to do.",
        2: "Second year: the class lineup changes after the vote, the "
           "festivals become a battlefield, and the school starts cutting.",
        3: "Third year: the last year of the advanced course, and the end "
           "of the game the board has been running.",
        0: "Side stories and interludes — the short volumes that fill in "
           "what the main arcs skip.",
    }[year]
    body = f'<div class="vol-list">{"".join(rows)}</div>'
    return ctx["page"](label, "story", body,
                      [("Home", "index.html"),
                       ("Story", "story/index.html"), (label, None)],
                      out=f"story/y{year}.html", rail=story_rail(ctx),
                      lede=blurb, kicker="Reading order",
                      tagline_label=label, scope=ctx["scope"])


def volume_evidence(ctx, vol_id, out_rel):
    """Everything the walk wrote about this volume, from the entity ledgers.

    Scenes are grouped by the kind of thing they are about — a person, an
    exam, a system, a place — because that is how a reader arrives: 'what
    happens to Kushida in Volume 1' and 'how the point economy is described
    in Volume 1' are different questions with different pages.
    """
    base = posixpath.dirname(out_rel) or "."
    kinds = [("people", "Scenes, line by line"),
             ("exams", "The exam as it was actually run"),
             ("systems", "How the system is described on the page"),
             ("places", "What happens here")]
    out = []
    for kind, heading in kinds:
        stems = ctx["evidence"].get(vol_id, {}).get(kind, [])
        for stem in sorted(stems):
            led = L.load(kind, stem)
            if not led:
                continue
            blocks = [b for sec in led["vols"] if sec["vol"] == vol_id
                      for b in sec["blocks"]]
            if not blocks:
                continue
            if kind == "people":
                c = ctx["char_by_id"].get(stem)
                label = c["name"] if c else site_arch.display_name("", stem)
                href = posixpath.relpath(c["href"] if c else f"people/{stem}.html", base)
                title = f'<a href="{href}">{S.esc(label)}</a>'
            else:
                title = S.esc(led["title"].split(" — ")[0])
            scenes = "".join(E.scene_block(ctx, b, out_rel, show_vol=False,
                                           fold=True) for b in blocks)
            anchor = re.sub(r"[^a-z0-9]+", "-", f"{kind}-{stem}").strip("-")
            out.append(f'<h3 id="ev-{anchor}">{title}</h3>{scenes}')
    if not out:
        return ""
    return f'<h2 id="evidence">What was read in this volume</h2>{"".join(out)}'


ENTITY_ROWS = {"exams": "exam_rows", "systems": "system_rows",
               "places": "loc_rows"}
ENTITY_DIR = {"exams": "school/exam", "systems": "school/system",
              "places": "world"}


def entity_page_href(ctx, kind, stem):
    """Page url for a ledger stem (the id the walk wrote in `ledgers/`), which
    is not always the database id the page is built under. site_ledgers.
    LEDGER_ALIAS is the only place that knows the pairing. Returns '' when this
    build makes no page for it, so callers can fall back rather than link at
    nothing."""
    pid = L.page_id_for(kind, stem)
    if pid not in {r["id"] for r in ctx[ENTITY_ROWS[kind]]}:
        return ""
    return f"{ENTITY_DIR[kind]}/{pid}.html"


def named_exams_here(ctx, vol_id, out_rel):
    """Exams whose name appears in this volume (a string count in the text),
    linked to their page. No analysis — that only comes from a ledger."""
    base = posixpath.dirname(out_rel) or "."
    rows = ctx["con"].execute(
        "SELECT m.exam_id, count(*) FROM exam_mentions m "
        "WHERE m.vol_id = ? GROUP BY m.exam_id ORDER BY count(*) DESC",
        (vol_id,)).fetchall()
    out = []
    for eid, n in rows:
        name = ctx["exam_name"].get(eid, eid)
        walked = L.exists_for("exams", eid)
        out.append(
            f'<li><a href="{posixpath.relpath(f"school/exam/{eid}.html", base)}">'
            f'{S.esc(name)}</a> <span class="n">{n:,} times named'
            f'{" · read line by line" if walked else ""}</span></li>')
    if not out:
        return ""
    return (f'<h2 id="exams">Exams named in this volume</h2>'
            f'<ul class="plain">{"".join(out)}</ul>')


def chronology_page(ctx, meta):
    """The schedule the walk has actually filled: every volume in reading
    order, marked read or unread, with the scene count it contributed."""
    rows = []
    for v in sorted(ctx["vol_list"], key=lambda x: x["order"]):
        rec = ctx["evidence"].get(v["id"], {})
        blocks = rec.get("blocks", 0)
        pill = (f'<span class="pill done">{blocks} scenes read</span>' if blocks
                else '<span class="pill part">not read yet</span>')
        href = posixpath.relpath(volume_index_href(v["id"]), "school")
        rows.append(
            f'<tr><th><a href="{href}">{S.esc(v["label"])}</a></th>'
            f'<td>{v["pages"]} pages</td><td>{pill}</td></tr>')
    read = sum(1 for v in ctx["vol_list"] if ctx["evidence"].get(v["id"], {}).get("blocks"))
    body = f"""<h2 id="schedule">Volumes in reading order</h2>
<p>Two columns of truth: what the book is, and what this project has read
page by page. {read} of {len(ctx["vol_list"])} volumes have been read line by
line so far; the rest are listed so you can see the shape of what is left.</p>
<table class="facts chron">{"".join(rows)}</table>"""
    return ctx["page"](
        meta["title"], "school", body,
        [("Home", "index.html"), ("Exams & School", "school/index.html"),
         (meta["title"], None)],
        out=meta["out"], rail=school_rail(ctx),
        lede=f"{read} of {len(ctx['vol_list'])} volumes read line by line; "
             f"the rest are listed with their length only.",
        kicker="Coverage", tagline_label="Exams & School",
        meter=[("Volumes", str(len(ctx["vol_list"]))),
               ("Read", str(read))],
        scope=ctx["scope"])


def volume_page(ctx, v):
    vol_id = v["id"]
    st = ctx["walk"].get(vol_id, {})
    chapters = D.volume_ledger(vol_id)
    present = D.present_chars(ctx["con"], vol_id)
    docs = [info for info in ctx["vol_docs"].values() if info["vol"] == vol_id]
    rec = ctx["evidence"].get(vol_id, {})
    out = volume_index_href(vol_id)

    if rec.get("volume_ledger") and st.get("complete"):
        status_note = (
            "<div class='box note'><h4>Evidence state</h4><p>Read line by "
            "line. Every chapter and scene below is anchored to a page you "
            "can open in the book, and every page chip shows the text that "
            "sits there.</p></div>")
    elif rec.get("blocks"):
        status_note = (
            "<div class='box warn'><h4>Evidence state</h4><p>Partway: "
            f"{rec['blocks']} scene{'' if rec['blocks'] == 1 else 's'} of this "
            "volume have been read and anchored so far. The rest of this volume is "
            "still being read; nothing else about it is published.</p></div>")
    else:
        status_note = (
            "<div class='box warn'><h4>Evidence state</h4><p>Not read line by "
            "line yet, so this page carries only what can be counted: the "
            "volume's length, and the names and exams the text mentions in "
            "it. It fills up as this volume is read line by line.</p></div>")

    chapter_html = ""
    if chapters:
        items = []
        for ch in chapters:
            beats = "".join(f"<li>{S.esc(b)}</li>" for b in ch["beats"][:8])
            extras = "".join(
                f'<li><strong>{S.esc(label)}</strong> — {S.esc(value)}</li>'
                for label, value in ch.get("extras", [])[:10])
            setting = (f'<p class="who">{S.esc(ch["setting"])}</p>'
                       if ch["setting"] else "")
            items.append(
                f'<div class="scene"><div class="head">'
                f'<span class="pg">Ch. {S.esc(ch["n"])}'
                f'{"" if not ch["pp"] else " · pp. " + S.esc(ch["pp"])}</span>'
                f'<span class="ttl">{S.esc(ch["title"])}</span></div>'
                f'{setting}<ul>{extras or beats}</ul></div>')
        chapter_html = ("<h2 id=\"chapters\">What happens, chapter by "
                        f"chapter</h2>{''.join(items)}")

    evidence_html = volume_evidence(ctx, vol_id, out)

    docs_html = ""
    if docs:
        rows = []
        for info in sorted(docs, key=lambda i: (i["char_name"], i["kind"])):
            kind = "Scene transcript" if info["kind"] == "transcript" \
                else "Volume guide"
            rows.append(f'<li><a href="{posixpath.basename(info["out"])}">'
                        f'{S.esc(info["char_name"])} — {kind.lower()}</a></li>')
        docs_html = (f'<h2 id="documents">Full documents for this volume</h2>'
                     f'<ul class="plain">{"".join(rows)}</ul>')

    cast_html = ""
    if present:
        named = [p for p in present if p["tier"] <= 2]
        extra = len(present) - len(named)
        base = f"story/v/{vol_id}"
        chips = "".join(
            f'<a href="{posixpath.relpath(ctx["char_by_id"][p["id"]]["href"], base)}"'
            f' style="margin-right:12px">{S.esc(p["name"])}</a>'
            for p in named if p["id"] in ctx["char_by_id"])
        more = f" <span class='n'>plus {extra} further names</span>" if extra else ""
        cast_html = (f'<h2 id="cast">Who is named in it</h2><p>{chips}{more}</p>'
                     f'<p class="muted">From the mention table: where a name '
                     f'appears in the text of this volume.</p>')

    exam_html = named_exams_here(ctx, vol_id, out)

    body = f"""<h2 id="at-a-glance">At a glance</h2>
{facts_strip([
    ("School year", site_arch.volume_label(vol_id).split(",")[0]),
    ("Volume", site_arch.volume_number(vol_id)),
    ("Kind", site_arch.volume_kind_label(v["kind"])),
    ("Length", f'{v["pages"]} pages'),
])}
{status_note}
{chapter_html}
{evidence_html}
{docs_html}
{exam_html}
{cast_html}"""
    crumbs = [("Home", "index.html"), ("Story", "story/index.html"),
              (f"Year {v['year'] or 0}", f"story/y{v['year']}.html"),
              (site_arch.volume_short(vol_id), None)]
    ctx["open_year"] = v["year"]
    scenes = rec.get("blocks", 0)
    html_out = ctx["page"](
        story_title(ctx, vol_id), "story",
        S.chipify(body, ctx["lookup"]), crumbs, out=out,
        rail=story_rail(ctx),
        lede=f'{story_title(ctx, vol_id)} — {v["pages"]} pages'
             f'{", " + str(len(chapters)) + " chapters transcribed" if chapters else ""}'
             f'{", " + str(scenes) + " scenes read" if scenes else ""}.',
        kicker=site_arch.volume_label(vol_id),
        tagline_label="Volume",
        meter=[("Chapters read", str(len(chapters))),
               ("Scenes anchored", str(scenes)),
               ("Named in it", str(len(present)))],
        related=volume_related(ctx, v, present, docs),
        scope=ctx["scope"])
    ctx["open_year"] = None
    return (out, html_out)


def volume_related(ctx, v, present, docs):
    """The rail that makes the Story axis a graph instead of 36 islands:
    where you came from, where you go next, and the people, exams and
    documents this volume is made of."""
    vol_id = v["id"]
    order = [x["id"] for x in ctx["vol_list"]]
    links = []
    i = order.index(vol_id) if vol_id in order else -1
    if i > 0:
        prev_id = order[i - 1]
        links.append((f"← {site_arch.volume_short(prev_id)}",
                      volume_index_href(prev_id)))
    if 0 <= i < len(order) - 1:
        next_id = order[i + 1]
        links.append((f"{site_arch.volume_short(next_id)} →",
                      volume_index_href(next_id)))
    links.append((f"Year {v['year'] or 0} in order",
                  f"story/y{v['year']}.html"))
    rec = ctx["evidence"].get(v["id"], {})
    for stem in rec.get("exams", [])[:4]:
        href = entity_page_href(ctx, "exams", stem)
        if not href:
            continue
        links.append((f"Exam read here: "
                      f"{ctx['exam_name'].get(L.page_id_for('exams', stem), stem)}",
                      href))
    for p in [p for p in present if p["tier"] <= 2][:6]:
        c = ctx["char_by_id"].get(p["id"])
        if c:
            links.append((c["name"], c["href"]))
    for info in docs[:3]:
        links.append((f'{info["char_name"]} — '
                      f'{"transcript" if info["kind"] == "transcript" else "guide"}',
                      info["out"]))
    return links


# ---------------------------------------------------------------- school


def school_rail(ctx):
    items = [{"kind": "link", "label": "Exams & school index",
              "href": "school/index.html"},
             {"kind": "link", "label": "Exam chronology",
              "href": "school/chronology.html"}]
    exams = sorted(ctx["exam_list"], key=lambda e: e["name"])
    items.append({"kind": "details", "label": "Exams", "count": len(exams),
                  "open": True,
                  "sub": [{"label": e["name"],
                           "href": f"school/exam/{e['id']}.html"}
                          for e in exams]})
    systems = sorted(ctx["system_list"], key=lambda s: s["name"])
    items.append({"kind": "details", "label": "School systems",
                  "count": len(systems), "open": True,
                  "sub": [{"label": s["name"],
                           "href": f"school/system/{s['id']}.html"}
                          for s in systems]})
    return items


EXAM_KIND_LABEL = {
    "special": "Special exam", "event": "School event",
    "written": "Written exam", "entrance": "Entrance exam",
}

LOC_KIND_LABEL = {
    "campus-building": "Campus buildings", "campus-zone": "Campus grounds",
    "exam-venue": "Exam venues", "off-site": "Off campus",
    "city": "Cities & regions", "dorm": "Halls & residences",
}


def ledger_vol_related(ctx, led, base):
    """Volume links a ledger earns: every volume it wrote up, by reading order."""
    order = {v["id"]: v["order"] for v in ctx["vol_list"]}
    links = []
    for section in sorted(led["vols"], key=lambda s: order.get(s["vol"], 999)):
        v = ctx["vols"].get(section["vol"])
        if v:
            links.append((v["label"],
                          posixpath.relpath(volume_index_href(section["vol"]), base)))
    return links


MENTION_TABLE = {
    "exams": ("exam_mentions", "exam_id"),
    "systems": ("system_mentions", "sys_id"),
    "places": ("location_mentions", "loc_id"),
}


def mentioned_volumes(ctx, table, id_col, entity_id):
    """Where a name is written in the text files — mechanical, safe before the
    walk. Ordered by reading order, not by the vol_id string, which sorts
    'y1v10' before 'y1v2'."""
    rows = ctx["con"].execute(
        f"SELECT vol_id FROM {table} WHERE {id_col} = ? "
        "GROUP BY vol_id", (entity_id,)).fetchall()
    order = {v["id"]: int(v["order"]) for v in ctx["vol_list"]}
    return sorted((r[0] for r in rows), key=lambda v: order.get(v, 999))


def ledger_entity_page(ctx, meta, *, ledger_kind, section, rail, kicker,
                       tagline, facts, lede, crumb_parent, crumb_href):
    """One page shape for exams, systems and places: the walk ledger when it
    exists, mechanical facts always, a coverage stub when the walk has not
    reached it. The pre-walk authored prose is gone from this path."""
    eid = meta["row"]["id"]
    out_rel = meta["out"]
    base = posixpath.dirname(out_rel) or "."
    led = L.load_for(ledger_kind, eid)
    parts = []
    if led:
        parts.append(E.volume_sections(ctx, led, out_rel))
        parts.append(f'<h2 id="facts">What the records say it is</h2>'
                     f'{facts_strip(facts)}')
        related = ledger_vol_related(ctx, led, base)
        meter = E.evidence_meters(ctx, led)
        state = lede
    else:
        parts.append(f'<h2 id="facts">What the records say it is</h2>'
                     f'{facts_strip(facts)}')
        table, id_col = MENTION_TABLE[ledger_kind]
        vols = mentioned_volumes(ctx, table, id_col, eid)
        vols = [v for v in vols if v in ctx["vols"]]
        parts.append(E.coverage_stub(ctx, subject=meta["title"], base=base,
                                     vol_ids=vols))
        related = [(ctx["vols"][v]["label"],
                    posixpath.relpath(volume_index_href(v), base))
                   for v in vols[:10] if v in ctx["vols"]]
        meter = [("Volumes naming it", str(len(vols)))]
        state = lede
    body = section_scope(S.chipify("".join(parts), ctx["lookup"]), ctx["vols"])
    html_out = ctx["page"](
        meta["title"], section, body,
        [("Home", "index.html"), (crumb_parent, crumb_href), (meta["title"], None)],
        out=out_rel, rail=rail(ctx), lede=state, kicker=kicker,
        tagline_label=tagline, related=related, meter=meter, scope=ctx["scope"])
    return (out_rel, html_out)


def exam_page(ctx, meta):
    e = meta["row"]
    runs = e["instances"]
    facts = [
        ("Type", EXAM_KIND_LABEL.get(e["kind"], e["kind"] or "")),
        ("First named in", site_arch.volume_label(e["first_vol"])
         if e["first_vol"] in ctx["vols"] else ""),
        ("Last named in", site_arch.volume_label(e["last_vol"])
         if e["last_vol"] in ctx["vols"] else ""),
        ("Runs recorded from the pages",
         str(len([r for r in runs if r["vol_id"] in ctx["evidence"]])) if runs else ""),
    ]
    return ledger_entity_page(
        ctx, meta, ledger_kind="exams", section="school", rail=school_rail,
        kicker="Exam", tagline=EXAM_KIND_LABEL.get(e["kind"], "Exam"),
        facts=facts,
        lede=("Read page by page in "
              + ", ".join(site_arch.volume_label(sec["vol"])
                          for sec in (L.load_for("exams", e["id"]) or {"vols": []})["vols"])
              + ".") if L.exists_for("exams", e["id"]) else
             "Named in the text; not worked through page by page yet.",
        crumb_parent="Exams & School", crumb_href="school/index.html")


def system_page(ctx, meta):
    s = meta["row"]
    facts = [("Category", s["kind"] or ""),
             ("Times named", f'{ctx["con"].execute("SELECT count(*) FROM system_mentions WHERE sys_id = ?", (s["id"],)).fetchone()[0]:,}')]
    return ledger_entity_page(
        ctx, meta, ledger_kind="systems", section="school", rail=school_rail,
        kicker="School system", tagline="System", facts=facts,
        lede="How the school's machinery is described in the volumes read "
             "line by line, entry by entry with page numbers."
             if L.exists_for("systems", s["id"]) else
             "Named in the text; the rules behind it have not been read page "
             "by page yet.",
        crumb_parent="Exams & School", crumb_href="school/index.html")


def evidence_state_label(ctx, kind, eid):
    """A door's subtitle is now an evidence state, not a summary: it tells the
    reader how much of this page was read page by page."""
    led = L.load_for(kind, eid)
    if not led:
        return "Not read line by line yet — the page lists what can be counted."
    blocks = sum(len(sec["blocks"]) for sec in led["vols"])
    vols = ", ".join(site_arch.volume_short(sec["vol"]) for sec in led["vols"])
    return f"{blocks} scene{'' if blocks == 1 else 's'} read on the page ({vols})."


def school_index(ctx):
    exam_rows = []
    for e in sorted(ctx["exam_list"], key=lambda e: order_of(ctx, e["first_vol"])):
        exam_rows.append(
            f'<a class="door" href="school/exam/{e["id"]}.html">'
            f'<span class="q">{S.esc(e["name"])}</span>'
            f'<span class="d">{S.esc(evidence_state_label(ctx, "exams", e["id"]))}</span>'
            f'<span class="go">{S.esc(EXAM_KIND_LABEL.get(e["kind"], "Exam"))}'
            f' · named in {len(e["instances"])} recorded run'
            f'{"" if len(e["instances"]) == 1 else "s"}</span></a>')
    sys_rows = []
    for s in sorted(ctx["system_list"], key=lambda s: s["name"]):
        sys_rows.append(
            f'<a class="door" href="school/system/{s["id"]}.html">'
            f'<span class="q">{S.esc(s["name"])}</span>'
            f'<span class="d">{S.esc(evidence_state_label(ctx, "systems", s["id"]))}</span>'
            f'<span class="go">System</span></a>')
    body = f"""<h2 id="exams">The exams</h2>
<p>An exam page holds what the pages themselves say: the rules as they were
stated on the page, the point figures with their page anchors, and the scenes
where the exam was actually run. Where a volume has not been read yet, the
page says so instead of guessing.</p>
<div class="doors">{"".join(exam_rows)}</div>
<h2 id="systems">The systems behind them</h2>
<div class="doors">{"".join(sys_rows)}</div>
<h2 id="timeline">What has been read</h2>
<p><a href="school/chronology.html">Chronology of this project</a> — every
volume in reading order, marked read or unread, with the scene count each one
contributed.</p>"""
    return ctx["page"]("Exams & School", "school", body,
                      [("Home", "index.html"), ("Exams & School", None)],
                      out="school/index.html", rail=school_rail(ctx),
                      lede="The rules of Advanced Nurturing High School as "
                           "the pages state them: exams, point swings, systems, "
                           "each with its page.",
                      kicker="Rules & results", tagline_label="Exams & School",
                      scope=ctx["scope"])


def order_of(ctx, vol_id):
    v = ctx["vols"].get(vol_id)
    return int(v["order"]) if v else 999


# ----------------------------------------------------------------- world


def place_state(ctx, l):
    """One line under a place name: how much of it has been read, never a
    summary of what it is for — that was the old authored layer."""
    led = L.load_for("places", l["id"])
    if led:
        blocks = sum(len(sec["blocks"]) for sec in led["vols"])
        return f'{blocks} scene{"" if blocks == 1 else "s"} read on the page'
    return f'named {l["mentions"]:,} times · not read yet'


def world_rail(ctx):
    items = [{"kind": "link", "label": "Places index",
              "href": "world/index.html"}]
    groups = {}
    for l in ctx["loc_list"]:
        groups.setdefault(l["kind"], []).append(l)
    for kind in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        rows = sorted(groups[kind], key=lambda l: l["name"])
        items.append({"kind": "details",
                      "label": LOC_KIND_LABEL.get(kind, kind),
                      "count": len(rows),
                      "open": ctx.get("open_kind") == kind,
                      "sub": [{"label": r["name"], "href": f"world/{r['id']}.html"}
                              for r in rows]})
    return items


def place_page(ctx, meta):
    l = meta["row"]
    facts = [
        ("Kind", LOC_KIND_LABEL.get(l["kind"], l["kind"] or "")),
        ("First named in", site_arch.volume_label(l["first_vol"])
         if l["first_vol"] in ctx["vols"] else ""),
        ("Last named in", site_arch.volume_label(l["last_vol"])
         if l["last_vol"] in ctx["vols"] else ""),
        ("Times named", f'{l["mentions"]:,}'),
    ]
    return ledger_entity_page(
        ctx, meta, ledger_kind="places", section="world", rail=world_rail,
        kicker="Place", tagline=LOC_KIND_LABEL.get(l["kind"], "Place"),
        facts=[f for f in facts if f[1]],
        lede="Scenes that happen here, with the page each one is on."
             if L.exists_for("places", l["id"]) else
             "Named in the text; not worked through page by page yet.",
        crumb_parent="World & Places", crumb_href="world/index.html")


def world_index(ctx):
    groups = {}
    for l in ctx["loc_list"]:
        groups.setdefault(l["kind"], []).append(l)
    blocks = []
    for kind in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        rows = sorted(groups[kind], key=lambda l: l["name"])
        cells = "".join(
            f'<a href="world/{l["id"]}.html">{S.esc(l["name"])}'
            f'<span class="n">{place_state(ctx, l)}</span></a>'
            for l in rows)
        blocks.append(f'<h2 id="{slug(LOC_KIND_LABEL.get(kind, kind))}">'
                      f'{S.esc(LOC_KIND_LABEL.get(kind, kind))}</h2>'
                      f'<div class="grid-list">{cells}</div>')
    body = "".join(blocks) + """<h2 id="reading">Why places matter here</h2>
<p>The school is deliberately closed: the campus is the whole world for most
of the first two years, and the exams drag the classes out to a ship, an
island, a ski slope. Each place page records what the text says about its
layout and which scenes it hosts.</p>"""
    return ctx["page"]("World & Places", "world", body,
                      [("Home", "index.html"), ("World & Places", None)],
                      out="world/index.html", rail=world_rail(ctx),
                      lede="Every place the novels put a scene in, grouped "
                           "the way a reader would look for it.",
                      kicker="Where it happens", tagline_label="World",
                      scope=ctx["scope"])

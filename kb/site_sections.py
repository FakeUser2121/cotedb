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
    walked = sorted(k for k, s in ctx["walk"].items() if s["markers"])
    doors = "".join([
        door("Find a person", "Who is this character, and what do they do?",
             "Every named character with their moments, pages attached.",
             "people/index.html"),
        door("Read in order", "What happens in a given volume?",
             "The chronological spine: year by year, volume by volume.",
             "story/index.html"),
        door("Check a rule", "How did that exam actually work?",
             "Rules, numbers and every run of each exam, with evidence.",
             "school/index.html"),
        door("Ask a question", "Who got expelled, and when?",
             "Cross-cutting topic pages assembled from every volume.",
             "topics/index.html"),
        door("Write in the world", "I need Ayanokōji's actual voice.",
             "Doors built for writers, number-crunchers and the rusty.",
             "guides/index.html"),
        door("Locate a scene", "Where exactly did that happen?",
             "Twenty-eight places, and what each one is used for.",
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
built from the translated volumes themselves. Character profiles, the
story in reading order, every exam's rules and outcomes, and the lines
themselves — each one quoted as written and tied to a page you can check.</p>
<div class="stats">
<div><b>{stats['chars']}</b><span>characters</span></div>
<div><b>{stats['vols']}</b><span>volumes</span></div>
<div><b>{stats['exams']}</b><span>exams</span></div>
<div><b>{stats['places']}</b><span>places</span></div>
<div><b>{stats['quotes']:,}</b><span>quoted lines</span></div>
<div><b>{stats['walked']}</b><span>volumes walked line-by-line</span></div>
</div>
</div>
<h2 id="start">Where do you want to start?</h2>
<div class="doors">{doors}</div>
<h2 id="library">The library</h2>
<div class="cards">{sections}</div>
<h2 id="reading-a-page">Reading a page</h2>
<p><strong>Bold labels</strong> are written analysis. “Curly quotes” are the
novel's own words. A citation such as
<span class="cite">y1v1 p.247</span> means Year 1, Volume 1, page 247 —
click one to see the text sitting on that page.</p>
<p>Reading in progress? Choose <em>I've read up to…</em> in the bar above and
anything later in the story stays folded until you open it. Your choice is
remembered on this device.</p>
<p>Only volume 1 has been transcribed line by line so far
({len(walked)} volume{'' if len(walked) == 1 else 's'}:
{', '.join(S.esc(site_arch.volume_label(w)) for w in walked)}).
Everything else is assembled from the curated records, and each page says
plainly how far its evidence reaches.</p>"""
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
    reads the href off the character record, so this has to run first."""
    src = DOSSIERS / "background.md"
    entries = {}
    if src.exists():
        cur = None
        for line in src.read_text(encoding="utf-8").splitlines():
            mh = re.match(r"^### (.+)$", line)
            if mh:
                raw = mh.group(1).strip()
                cid = re.sub(r"\s*\(.+?\)\s*$", "", raw)
                key = re.sub(r"[^a-z0-9]+", "-", cid.lower()).strip("-")
                cur = {"name": raw, "id": key, "lines": []}
                entries.setdefault(key, cur)
                continue
            if cur is not None and line.strip():
                cur["lines"].append(line.strip())
    minor_by_id = {c["id"]: c for c in ctx["chars"] if c["tier"] >= 3}
    # the dossier headings are prose ("Takanashi (Kō)"), the database ids are
    # slugs, and they drift apart. Match on the letters-and-digits of the
    # family name as a second pass so the anchor we publish is the id every
    # other page links to.
    def norm(text):
        return re.sub(r"[^a-z0-9]", "", (text or "").lower())

    by_norm = {}
    for c in ctx["chars"]:
        if c["tier"] >= 3:
            by_norm.setdefault(norm(c["canon"] or c["name"]), c)
    buckets = {}
    for key, ent in entries.items():
        c = minor_by_id.get(key) or by_norm.get(
            norm(re.sub(r"\s*\(.+?\)\s*$", "", ent["name"])))
        name = c["name"] if c else site_arch.display_name(ent["name"], key)
        letter = (name.split()[0][:1].upper() if name else "?")
        buckets.setdefault(letter, []).append((key, name, ent["lines"], c))
    letters = sorted(buckets)
    href_by_id = {}
    for l, rows in buckets.items():
        for key, name, lines, c in rows:
            anchor = c["id"] if c else slug(name)
            href = f"people/minor/{l.lower()}.html#{anchor}"
            href_by_id[key] = href
            if c:
                c["href"] = href
    ctx["minor_buckets"] = buckets
    ctx["minor_letters"] = letters
    ctx["minor_href_by_id"] = href_by_id
    return ctx


def minor_pages(ctx):
    """One page per initial, replacing the single 225 KB background page."""
    plan_minor(ctx)
    pages = []
    letters = ctx["minor_letters"]
    buckets = ctx["minor_buckets"]
    for l in letters:
        rows = sorted(buckets[l], key=lambda r: r[1])
        blocks = []
        for key, name, lines, c in rows:
            body, headings = render(reword("\n".join(lines)))
            body = S.resolve_links(body, "dossiers/background.md",
                                   ctx["pathmap"], f"people/minor/{l.lower()}.html")
            body = S.chipify(body, ctx["lookup"])
            note = ""
            if c:
                note = (f'<span class="n">{site_arch.TIER_LABEL[c["tier"]]}'
                        f' · {c["quotes"]:,} quoted lines</span>')
            anchor = c["id"] if c else slug(name)
            blocks.append(f'<h3 id="{anchor}">{S.esc(name)}</h3>'
                          f'<div class="measure">{body}</div>')
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
            lede=f"{len(rows)} characters whose entries start with {l}.",
            kicker="Minor characters", tagline_label="People",
            scope=ctx["scope"])
        pages.append((f"people/minor/{l.lower()}.html", html_out))
    return pages


def person_page(ctx, meta):
    md = reword(Path(meta["src"]).read_text(encoding="utf-8"))
    c = ctx["char_by_id"].get(meta["char_id"])
    body, headings = render(md)
    body = S.resolve_links(body, meta["src_rel"], ctx["pathmap"], meta["out"])
    body = S.chipify(body, ctx["lookup"])
    body = section_scope(body, ctx["vols"])
    pairs = []
    if c:
        pairs = [
            ("Role in the story", site_arch.TIER_LABEL[c["tier"]]),
            ("Quoted lines", f"{c['quotes']:,}"),
            ("Volumes with lines", str(c["quote_vols"])),
            ("Appears in", f"{c['coverage']} volumes"),
        ]
    related = related_links(ctx, c) if c else []
    docs = guide_links(ctx, c["id"]) if c else []
    if docs:
        related = docs + related
    title = c["name"] if c else meta["title"]
    rail_extra = [{"kind": "grp", "label": "This character"}]
    html_out = ctx["page"](
        title, "people", body,
        [("Home", "index.html"), ("People", "people/index.html"),
         (title, None)],
        out=meta["out"], rail=people_rail(ctx) + rail_extra,
        lede=first_sentence(md) or "", kicker=site_arch.TIER_LABEL.get(
            c["tier"] if c else 4, "Character"),
        tagline_label="Person", related=related,
        meter=footprint(ctx, c), scope=ctx["scope"])
    return (meta["out"], html_out)


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
    links = []
    seen = set()
    for r in ctx["relations"]:
        other = None
        if r["a"] == c["id"]:
            other = r["b"]
        elif r["b"] == c["id"]:
            other = r["a"]
        if not other:
            continue
        oc = ctx["char_by_id"].get(other)
        if not oc or other in seen:
            continue
        seen.add(other)
        links.append((f'{oc["name"]} · {r["type"]}', oc["href"]))
    return links


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


def volume_page(ctx, v):
    vol_id = v["id"]
    st = ctx["walk"].get(vol_id, {})
    chapters = D.volume_ledger(vol_id)
    timeline = [t for t in ctx["timeline"] if t["vol_id"] == vol_id]
    exams = ctx["exams_by_vol"].get(vol_id, [])
    present = D.present_chars(ctx["con"], vol_id)
    docs = [info for info in ctx["vol_docs"].values() if info["vol"] == vol_id]

    status_note = ""
    if st.get("complete"):
        status_note = ("<div class='box note'><h4>Evidence state</h4>"
                       "<p>This volume has been transcribed line by line: "
                       "every chapter below is anchored to page numbers you "
                       "can open in the book, and the scene transcripts are "
                       "quoted verbatim.</p></div>")
    elif st.get("markers"):
        status_note = (
            "<div class='box warn'><h4>Evidence state</h4><p>Partway: "
            f"{len(st['chapters'])} chapter{'' if len(st['chapters']) == 1 else 's'} "
            "of this volume have been worked through in full. The rest of "
            "the page is assembled from the curated records, which are "
            "reliable but sparser.</p></div>")
    else:
        status_note = (
            "<div class='box warn'><h4>Evidence state</h4><p>Not yet "
            "transcribed line by line. What follows comes from the curated "
            "records — exams, character arcs, and page-level citations — "
            "and grows as the walk reaches this volume.</p></div>")

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

    arc_html = ""
    if timeline:
        rows = []
        for t in timeline:
            c = ctx["char_by_id"].get(t["char_id"])
            name = c["name"] if c else t["name"]
            link = f'<a href="{posixpath.relpath(c["href"], "story/v/" + vol_id)}">{S.esc(name)}</a>' if c else S.esc(name)
            bits = []
            if t["situation"]:
                bits.append(f'<li><strong>Situation</strong> — {S.esc(D.clean(t["situation"]))}</li>')
            if t["knowledge"]:
                bits.append(f'<li><strong>What they know</strong> — {S.esc(D.clean(t["knowledge"]))}</li>')
            if t["changes"]:
                bits.append(f'<li><strong>What changes</strong> — {S.esc(D.clean(t["changes"]))}</li>')
            if t["why"]:
                bits.append(f'<li><strong>Why it matters</strong> — {S.esc(D.clean(t["why"]))}</li>')
            refs = re.findall(r"y[0-9v.]+ pp?\. \d+", t["refs"] or "")
            ref_html = "".join(f'<span class="cite">{S.esc(r)}</span> '
                               for r in refs[:4])
            rows.append(f'<div class="scene"><div class="head">'
                        f'<span class="ttl">{link}</span></div>'
                        f'<ul>{"".join(bits)}</ul>{ref_html}</div>')
        arc_html = (f'<h2 id="arcs">Arcs that move in this volume</h2>'
                    f'{"".join(rows)}')

    exam_html = ""
    if exams:
        rows = []
        for e in exams:
            eid = e["exam_id"]
            href = posixpath.relpath(f"school/exam/{eid}.html",
                                     f"story/v/{vol_id}")
            rows.append(
                f'<li><a href="{href}">{S.esc(ctx["exam_name"].get(eid, eid))}'
                f'</a> — {S.esc(D.clean(e["chronology"][:180]))}</li>')
        exam_html = (f'<h2 id="exams">Exams run here</h2><ul>{"".join(rows)}</ul>')

    docs_html = ""
    if docs:
        rows = []
        for info in sorted(docs, key=lambda i: (i["char_name"], i["kind"])):
            kind = "Scene transcript" if info["kind"] == "transcript" \
                else "Volume guide"
            rows.append(f'<li><a href="{posixpath.basename(info["out"])}">'
                        f'{S.esc(info["char_name"])} — {kind.lower()}</a></li>')
        docs_html = (f'<h2 id="documents">Full documents for this volume</h2>'
                     f'<ul>{"".join(rows)}</ul>')

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
        cast_html = (f'<h2 id="cast">Who is in it</h2><p>{chips}{more}</p>')

    body = f"""<h2 id="at-a-glance">At a glance</h2>
{facts_strip([
    ("School year", site_arch.volume_label(vol_id).split(",")[0]),
    ("Volume", site_arch.volume_number(vol_id)),
    ("Kind", site_arch.volume_kind_label(v["kind"])),
    ("Length", f'{v["pages"]} pages'),
])}
{status_note}
{docs_html}
{chapter_html}
{arc_html}
{exam_html}
{cast_html}"""
    crumbs = [("Home", "index.html"), ("Story", "story/index.html"),
              (f"Year {v['year'] or 0}", f"story/y{v['year']}.html"),
              (site_arch.volume_short(vol_id), None)]
    ctx["open_year"] = v["year"]
    out = volume_index_href(vol_id)
    html_out = ctx["page"](
        story_title(ctx, vol_id), "story",
        S.chipify(body, ctx["lookup"]), crumbs, out=out,
        rail=story_rail(ctx),
        lede=f'{story_title(ctx, vol_id)} — {v["pages"]} pages, '
             f'{len(exams)} exam run{"" if len(exams) == 1 else "s"}, '
             f'{len(chapters)} chapter{"" if len(chapters) == 1 else "s"} '
             f"transcribed.",
        kicker=site_arch.volume_label(vol_id),
        tagline_label="Volume",
        meter=[("Chapters", str(len(chapters))),
               ("Exams", str(len(exams))),
               ("Named in it", str(len(present)))],
        scope=ctx["scope"])
    ctx["open_year"] = None
    return (out, html_out)


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


def exam_page(ctx, meta):
    md = reword(Path(meta["src"]).read_text(encoding="utf-8"))
    body, headings = render(md)
    body = S.resolve_links(body, meta["src_rel"], ctx["pathmap"], meta["out"])
    body = S.chipify(body, ctx["lookup"])
    body = section_scope(body, ctx["vols"])
    e = meta["row"]
    runs = e["instances"]
    related = []
    for r in runs:
        vol = ctx["vols"].get(r["vol_id"])
        if vol:
            related.append((f'Run {r["seq"]} — {vol["label"]}',
                            posixpath.relpath(volume_index_href(r["vol_id"]),
                                              posixpath.dirname(meta["out"]))))
    pairs = [
        ("Type", EXAM_KIND_LABEL.get(e["kind"], e["kind"] or "")),
        ("First seen", site_arch.volume_label(e["first_vol"])
         if e["first_vol"] in ctx["vols"] else ""),
        ("Last run", site_arch.volume_label(e["last_vol"])
         if e["last_vol"] in ctx["vols"] else ""),
        ("Runs recorded", str(len(runs)) if runs else ""),
    ]
    run_rows = []
    for r in runs:
        vol = ctx["vols"].get(r["vol_id"])
        href = volume_index_href(r["vol_id"])
        label = vol["label"] if vol else r["vol_id"]
        run_rows.append(
            f'<li><a href="{posixpath.relpath(href, posixpath.dirname(meta["out"]))}">'
            f'{S.esc(label)}</a> — {S.esc(D.clean(r["chronology"]))}'
            f'<ul><li><strong>Outcome</strong> — {S.esc(D.clean(r["outcome"]))}</li>'
            f'<li><strong>Who took part</strong> — {S.esc(D.clean(r["participants"]))}</li>'
            f'</ul></li>')
    run_html = (f'<h2 id="runs">Every time it was run</h2>'
                f'<ul>{"".join(run_rows)}</ul>') if run_rows else ""
    title = e["name"]
    html_out = ctx["page"](
        title, "school", f'{facts_strip(pairs)}{run_html}{body}',
        [("Home", "index.html"),
         ("Exams & School", "school/index.html"), (title, None)],
        out=meta["out"], rail=school_rail(ctx),
        lede=(e["rules"] or "")[:260], kicker="Exam",
        tagline_label=EXAM_KIND_LABEL.get(e["kind"], "Exam"),
        related=related, scope=ctx["scope"])
    return (meta["out"], html_out)


def system_page(ctx, meta):
    md = reword(Path(meta["src"]).read_text(encoding="utf-8"))
    body, headings = render(md)
    body = S.resolve_links(body, meta["src_rel"], ctx["pathmap"], meta["out"])
    body = S.chipify(body, ctx["lookup"])
    body = section_scope(body, ctx["vols"])
    s = meta["row"]
    title = s["name"]
    html_out = ctx["page"](
        title, "school",
        f'{facts_strip([("Category", s["kind"]), ("Function", s["function"])])}'
        f'{body}',
        [("Home", "index.html"),
         ("Exams & School", "school/index.html"), (title, None)],
        out=meta["out"], rail=school_rail(ctx),
        lede=(s["function"] or "")[:260], kicker="School system",
        tagline_label="System", scope=ctx["scope"])
    return (meta["out"], html_out)


def school_index(ctx):
    exam_rows = []
    for e in sorted(ctx["exam_list"], key=lambda e: order_of(ctx, e["first_vol"])):
        exam_rows.append(
            f'<a class="door" href="school/exam/{e["id"]}.html">'
            f'<span class="q">{S.esc(e["name"])}</span>'
            f'<span class="d">{S.esc((e["rules"] or "")[:150])}</span>'
            f'<span class="go">{S.esc(EXAM_KIND_LABEL.get(e["kind"], "Exam"))}'
            f' · {len(e["instances"])} run{"" if len(e["instances"]) == 1 else "s"}</span></a>')
    sys_rows = []
    for s in sorted(ctx["system_list"], key=lambda s: s["name"]):
        sys_rows.append(
            f'<a class="door" href="school/system/{s["id"]}.html">'
            f'<span class="q">{S.esc(s["name"])}</span>'
            f'<span class="d">{S.esc((s["function"] or "")[:150])}</span>'
            f'<span class="go">System</span></a>')
    body = f"""<h2 id="exams">The exams</h2>
<p>Each exam page holds the rules as the school stated them, the point
figures, and every run in chronological order with the page it happened
on.</p>
<div class="doors">{"".join(exam_rows)}</div>
<h2 id="systems">The systems behind them</h2>
<div class="doors">{"".join(sys_rows)}</div>
<h2 id="timeline">The whole schedule</h2>
<p><a href="school/chronology.html">Exam chronology</a> — every exam and
event in the order the classes met it, volume by volume.</p>"""
    return ctx["page"]("Exams & School", "school", body,
                      [("Home", "index.html"), ("Exams & School", None)],
                      out="school/index.html", rail=school_rail(ctx),
                      lede="The rules of Advanced Nurturing High School: "
                           "every exam, every point swing, every system.",
                      kicker="Rules & results", tagline_label="Exams & School",
                      scope=ctx["scope"])


def order_of(ctx, vol_id):
    v = ctx["vols"].get(vol_id)
    return int(v["order"]) if v else 999


# ----------------------------------------------------------------- world


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
    md = reword(Path(meta["src"]).read_text(encoding="utf-8"))
    body, headings = render(md)
    body = S.resolve_links(body, meta["src_rel"], ctx["pathmap"], meta["out"])
    body = S.chipify(body, ctx["lookup"])
    body = section_scope(body, ctx["vols"])
    l = meta["row"]
    vols = ctx["con"].execute(
        "SELECT vol_id, count(*) FROM location_mentions WHERE loc_id = ? "
        "GROUP BY vol_id ORDER BY vol_id", (l["id"],)).fetchall()
    related = []
    for vol, _n in vols[:8]:
        v = ctx["vols"].get(vol)
        if v:
            related.append((v["label"],
                            posixpath.relpath(volume_index_href(vol), "world")))
    html_out = ctx["page"](
        l["name"], "world",
        facts_strip([
            ("Type", LOC_KIND_LABEL.get(l["kind"], l["kind"])),
            ("Used for", S.esc(l["function"] or "")),
            ("Page mentions", f'{l["mentions"]:,}'),
        ]) + body,
        [("Home", "index.html"), ("World & Places", "world/index.html"),
         (l["name"], None)],
        out=meta["out"], rail=world_rail(ctx),
        lede=(l["function"] or "")[:260], kicker="Place",
        tagline_label=LOC_KIND_LABEL.get(l["kind"], "Place"),
        related=related, scope=ctx["scope"])
    ctx["open_kind"] = None
    return (meta["out"], html_out)


def world_index(ctx):
    groups = {}
    for l in ctx["loc_list"]:
        groups.setdefault(l["kind"], []).append(l)
    blocks = []
    for kind in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        rows = sorted(groups[kind], key=lambda l: l["name"])
        cells = "".join(
            f'<a href="world/{l["id"]}.html">{S.esc(l["name"])}'
            f'<span class="n">{S.esc((l["function"] or "")[:90])}</span></a>'
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

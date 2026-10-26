#!/usr/bin/env python3
"""Page shell for the encyclopedia site: masthead, section tabs, the two
rails, breadcrumbs, citation chips, footer. Every page on the site is
produced by page() so the frame can only be changed once.

Design rules encoded here:
  - a reader is never more than two clicks from anywhere: the tab bar is
    the seven top-level destinations, and it appears on every page;
  - the left rail shows only the current section's contents, so the
    navigation does't become a 90-item wall;
  - internal taxonomy (tier numbers, char ids, mid_type keys, volume ids as
    section names) never reaches the reader's eye;
  - assets come from kb/site_assets/ so the stylesheet and behaviour can be
    iterated without touching Python strings.
"""

import html
import posixpath
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arch  # noqa: E402
from share_render import slug  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "site_assets"
SITE_TITLE = "COTE Knowledge Base"
SITE_TAGLINE = "Classroom of the Elite · annotated archive"

CITE_TAIL_RE = re.compile(r"^(?:\s*(?:pp?\.|p)\s*)(\d+)(?:\s*[–-]\s*\d+)?")


def read_asset(name):
    return (ASSETS / name).read_text(encoding="utf-8")


def esc(text):
    return html.escape(text or "", quote=False)


def crumbs_html(root, crumbs):
    """Breadcrumbs never repeat what the tab bar already says, so a leading
    'Home' crumb is dropped — the Home tab and the brand both reach it."""
    crumbs = list(crumbs)
    if crumbs and crumbs[0][1] in ("index.html", ""):
        crumbs = crumbs[1:]
    if not crumbs:
        return ""
    parts = []
    for i, (label, href) in enumerate(crumbs):
        last = i == len(crumbs) - 1
        if last or not href:
            parts.append(f'<span class="here">{esc(label)}</span>')
        else:
            parts.append(f'<a href="{root}{href}">{esc(label)}</a>')
            parts.append('<span class="sep">/</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' \
        + "".join(parts) + "</nav>"


def tabs_html(root, section_id):
    out = [f'<a class="home{" here" if section_id == "home" else ""}"'
           f' href="{root}index.html">Home</a>']
    for s in site_arch.SECTIONS:
        here = " here" if s["id"] == section_id else ""
        out.append(f'<a class="s-{s["id"]}{here}"'
                   f' href="{root}{s["href"]}">{esc(s["label"])}</a>')
    return f'<nav class="tabs" aria-label="Sections">{"".join(out)}</nav>'


def masthead(root, section_id, opts):
    scope = opts.get("scope") or []
    scope_html = ""
    if scope:
        options = ['<option value="all">Spoil nothing yet</option>']
        for order, label in scope:
            options.append(f'<option value="{order}">{esc(label)}</option>')
        scope_html = (
            '<label for="scope">I\'ve read up to</label>'
            f'<select id="scope">{"".join(options)}</select>')
    menu = ('<button id="menu" class="icon-btn menu-btn" '
            'aria-label="Open contents">☰</button>')
    return f"""<header class="masthead">
<div class="mast-row">
  <div class="brandline">
    {menu}<a href="{root}index.html">{SITE_TITLE}</a>
    <span class="sub">{SITE_TAGLINE}</span>
  </div>
  <div class="searchwrap">
    <input id="q" type="search" autocomplete="off"
           placeholder="Search people, volumes, exams, quotes…  (press /)">
    <div id="results" hidden></div>
  </div>
  <div class="mast-tools">
    {scope_html}
    <button id="theme" class="icon-btn" type="button">Dark</button>
  </div>
</div>
<div class="mast-row two">{tabs_html(root, section_id)}</div>
</header>"""


def rail_left(section, current, root, items, title=None):
    """items: [{kind:'link'|'group'|'details', label, href, sub:[...]}]"""
    head = title or section["label"]
    head_link = ""
    if section["id"] != "home" and current != section["href"]:
        head_link = f' <a href="{root}{section["href"]}">index</a>'
    if not items:
        # the tab bar already says where you are; an empty rail is not worth
        # an element, a border or a screen-reader landmark
        return ""
    body = []
    for it in items:
        kind = it.get("kind", "link")
        if kind == "grp":
            body.append(f'<div class="grp">{esc(it["label"])}</div>')
        elif kind == "details":
            open_attr = " open" if it.get("open") else ""
            count = (f' <span class="count">{it["count"]}</span>'
                     if it.get("count") is not None else "")
            inner = "".join(
                link_line(root, current, sub["label"], sub["href"])
                for sub in it.get("sub", []))
            head_line = ""
            if it.get("href"):
                head_line = link_line(root, current, it["label"], it["href"])
            body.append(
                f'<details{open_attr}><summary>{esc(it["label"])}{count}'
                f'</summary>{head_line}{inner}</details>')
        else:
            body.append(link_line(root, current, it["label"], it["href"]))
    return (f'<nav class="rail left" id="rail-nav" aria-label="Contents">'
            f'<div class="rail-h"><a href="{root}index.html">{esc(head)}</a>'
            f'{head_link}</div>{"".join(body)}</nav>')


def link_line(root, current, label, href):
    active = " active" if href == current else ""
    return f'<a href="{root}{href}" class="item{active}">{esc(label)}</a>'


def rail_right(modules):
    """modules: [(title, inner_html)] — 'On this page', evidence footprint,
    related links."""
    if not modules:
        return ""
    out = []
    for title, inner in modules:
        out.append(f'<div class="mod"><div class="rail-h">{esc(title)}</div>'
                   f'{inner}</div>')
    return ('<aside class="rail right" aria-label="Page context">'
            + "".join(out) + "</aside>")


def toc_block(headings):
    items = [(lv, hid, text) for lv, hid, text in headings if lv in (2, 3)]
    if len(items) < 2:
        return ""
    out = []
    for lv, hid, text in items:
        out.append(f'<a class="l{lv}" href="#{hid}">{esc(text)}</a>')
    return "".join(out)


def related_block(links):
    if not links:
        return ""
    return "".join(
        f'<a href="{href}">{esc(label)}</a>' for label, href in links[:14])


def meter_block(pairs):
    if not pairs:
        return ""
    out = []
    for k, v in pairs:
        out.append(f"<span>{esc(k)}</span><b>{esc(v)}</b>")
    return f'<div class="meter">{"".join(out)}</div>'


FOOTER = """<footer class="site">
  Quotes are verbatim from the Classroom of the Elite light novels.
  A citation such as <code>y1v1 p.247</code> means Year 1, Volume 1,
  page 247; page numbers follow the printed volume.
  <div class="fl">
    <a href="{root}appendix/citations.html">How to read a citation</a>
    <a href="{root}appendix/coverage.html">Which volumes this covers</a>
    <a href="{root}appendix/downloads.html">Download as PDF</a>
    <a href="{root}guides/index.html">Start here</a>
  </div>
</footer>"""


def rebase_site_links(text, out_rel):
    """Rewrite site-rooted hrefs ("world/rooftop.html") to this page's depth.
    Idempotent: already-relative links ("../world/…", "assets/…") at the
    correct depth come back unchanged."""
    out_dir = posixpath.dirname(out_rel)

    def rep(m):
        target = m.group(1)
        if target.startswith(("#", "/", "http:", "https:", "mailto:",
                              "javascript", "../", "./")):
            return f'href="{target}"'
        base, frag = (target.split("#", 1) + [""])[:2] if "#" in target \
            else (target, "")
        if not base:
            return f'href="{target}"'
        frag = "#" + frag if frag else ""
        norm = posixpath.normpath(base)
        if not norm.startswith(site_arch.SITE_ROOTS):
            return f'href="{target}"'
        return f'href="{posixpath.relpath(norm, out_dir or ".")}{frag}"'

    return re.sub(r'href="([^"]+)"', rep, text)


def page(spec):
    """spec keys: title, section, crumb (list), body, headings, rail
    (left items), modules (right rail), root, out, scope, lede, tagline."""
    out_rel = spec["out"]
    spec = dict(spec)
    root = spec.get("root") or "../" * out_rel.count("/")
    section = site_arch.SECTION_BY_ID.get(
        spec["section"], {"id": spec["section"], "label": "Home",
                          "href": "index.html"})
    tagline = ""
    if spec.get("tagline_label"):
        tagline = f'<div class="tagline">{esc(spec["tagline_label"])}</div>'
    kicker = ""
    if spec.get("kicker"):
        kicker = f'<div class="kicker">{esc(spec["kicker"])}</div>'
    lede = ""
    if spec.get("lede"):
        lede = f'<p class="lede">{esc(spec["lede"])}</p>'
    modules = []
    toc = toc_block(spec.get("headings") or [])
    if toc:
        modules.append(("On this page", toc))
    if spec.get("meter"):
        modules.append(("Evidence footprint", meter_block(spec["meter"])))
    if spec.get("related"):
        modules.append(("Related", related_block(spec["related"])))
    # an empty rail is not a design element: when a page has nothing to put in
    # one, the column collapses instead of showing a blank bordered strip
    layout_classes = []
    if not (spec.get("rail") or []):
        layout_classes.append("no-left")
    if not modules:
        layout_classes.append("no-right")
    body_class = " ".join(
        [f"sec-{spec['section']}"] + layout_classes)
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(spec['title'])} · {SITE_TITLE}</title>
<meta name="description" content="{esc(spec.get('lede') or spec['title'])}">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body data-root="{root}" data-section="{spec['section']}"
      class="{body_class}">
{masthead(root, spec['section'], spec)}
<div class="layout">
  {rail_left(section, spec['out'], root, spec.get('rail') or [])}
  <main class="content">{crumbs_html(root, spec['crumb'])}{kicker}{tagline}
    {lede}<div class="measure">{spec['body']}</div></main>
  {rail_right(modules)}
  {FOOTER.format(root=root)}
</div>
<script src="{root}assets/search-index.js"></script>
<script src="{root}assets/search.js"></script>
<script src="{root}assets/shell.js"></script>
</body>
</html>
"""
    # One choke point: nav, rails and body alike are rebased here, so every
    # builder can write links from the site root and ignore page depth.
    return rebase_site_links(doc, out_rel)


def resolve_links(text, src_rel, pathmap, out_rel):
    """Rewrite dossier-local or drafts-local .md/.html hrefs onto the new
    public URL tree, rebased against the page being written."""
    src_dir = posixpath.dirname(src_rel)
    out_dir = posixpath.dirname(out_rel)

    def rep(m):
        target = m.group(1)
        if target.startswith(("#", "http:", "https:", "mailto:", "javascript")):
            return f'href="{target}"'
        frag = ""
        base = target
        if "#" in target:
            base, frag = target.split("#", 1)
            frag = "#" + frag
        if not base or base.startswith("/"):
            return f'href="{target}"'
        if base.endswith(".md"):
            key = posixpath.normpath(posixpath.join(src_dir, base))
        else:
            key = posixpath.normpath(posixpath.join(src_dir, base))
        new = pathmap.get(key)
        if new is None:
            key2 = posixpath.normpath(base)
            new = pathmap.get(key2)
        if new is None:
            # Builders also write site-rooted links ("world/rooftop.html").
            # They are absolute from the site root, so rebase them onto this
            # page's depth instead of leaving a path that only works at root.
            norm = posixpath.normpath(base)
            if norm.startswith(site_arch.SITE_ROOTS):
                return f'href="{posixpath.relpath(norm, out_dir or ".")}{frag}"'
            return f'href="{target}"'
        rel = posixpath.relpath(new, out_dir or ".")
        return f'href="{rel}{frag}"'

    return re.sub(r'href="([^"]+)"', rep, text)


def chipify(text, lookup):
    """Turn 'y1v1 p.247' style citations into chips that expand to the
    verbatim text sitting on that page. lookup(vol_id, page) -> [str]."""
    if lookup is None:
        return text

    def rep(m):
        vol, page = m.group(1), int(m.group(2))
        label = m.group(0)
        if not site_arch.VOL_CITE_RE.fullmatch(vol):
            return label
        try:
            proof = lookup(vol, page)
        except Exception:
            proof = []
        if not proof:
            return f'<span class="cite">{esc(label)}</span>'
        lines = "".join(
            f'<div class="verb">{esc(p[:400])}</div>' for p in proof)
        src = f'<span class="src">{esc(site_arch.volume_label(vol))}, ' \
              f'page {page}</span>'
        return (f'<details class="citebox"><summary class="cite" '
                f'title="Show the text on this page">{esc(label)}</summary>'
                f'<span class="citeproof">{lines}{src}</span></details>')

    return re.sub(
        r"\b(y0|y[123]v\d+(?:\.\d+)?)\s+(?:pp?\.|p)\s*(\d+)"
        r"(?:\s*[–-]\s*\d+)?", rep, text)

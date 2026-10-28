#!/usr/bin/env python3
"""Render walk-ledger evidence into the site's HTML vocabulary.

Every block here comes from ledgers/ (see site_ledgers.py): a scene heading
with a page range, and typed entries underneath. Two things happen on the way
out that the old dossier layer could not do:

  - the verbatim lines a reading pass copied off the page are published as
    rows in the scene, next to the paraphrase they came from, so a claim is
    checkable without leaving the page;
  - each [rel:other-character] entry becomes a link to that character's page,
    which is where the People graph now comes from — not from the pre-walk
    relations table.

One disclosure per region, and a control may only reveal what is not already
visible above it. A scene is one region: its fold is the only expander, the
rows inside are all shown once it is open, and the page range in the heading is
reference text, never a chip. A second control over the same pages would open
a shorter version of what the reader is already looking at — and where the
ledger has no line for a page, the site has nothing to show, because it holds
located lines, not the book. The gate in share_check.py fails the build if a
`details.citebox` is ever placed inside a scene again.

The chip that used to sit beside a citation is gone everywhere, not just inside
scenes: a <details> is flow content, so in prose it closes the paragraph around
it and splits the page. Citations in guide and appendix prose are reference
text now, the same grey a scene heading uses — see site_shell.reference_cites.

Nothing in this module invents prose. If a page has no ledger it gets
coverage_stub(), which states the evidence state and links to what exists.
"""

import posixpath
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arch  # noqa: E402
import site_ledgers as L  # noqa: E402
import site_roles  # noqa: E402
import site_shell as S  # noqa: E402

esc = S.esc


def _dir_of(path):
    """Accept either a page's output path ('school/exam/x.html') or a plain
    directory ('school/exam') and always return the directory."""
    return posixpath.dirname(path) if path.endswith(".html") else path


def vol_chip(ctx, vol_id, out_rel, tag=False):
    """Volume name as a link to that volume's page, safe from any depth.
    `tag` picks the compact 'Y1 V3' form for lists that mix years."""
    label = site_arch.volume_tag(vol_id) if tag else site_arch.volume_short(vol_id)
    href = posixpath.relpath(f"story/v/{vol_id}/index.html",
                             _dir_of(out_rel) or ".")
    return f'<a class="vlink" href="{href}">{esc(label)}</a>'


def pages_ref(pages):
    """A printed page range as reference text: the numbers a reader takes to
    the physical book, with nothing to click.

    Deliberately not a control. Inside a scene the rows below already carry
    every line the archive located on those pages, so a disclosure over the same
    range could only open a subset of what is on screen (module docstring)."""
    if not pages:
        return ""
    return f'<span class="pageref">{esc(pages)}</span>'


def pin(pages, href=None):
    """A page anchor on a note.

    On a scene row this is reference text — the number tells you which page of
    the printed volume to open, and the site has no book to link it to. The
    quoted wording, when there is any, is already a row in the same scene.

    `href` is only for rows on other pages (topics and recall lists) where the
    number genuinely navigates: those rows are summaries, and the scene they
    were read from — with its rows — lives on the entity's page."""
    if not pages:
        return ""
    if href:
        return (f'<a class="cite" href="{esc(href)}" '
                f'title="Open the scene this note was read from">'
                f'{esc(pages)}</a>')
    return f'<span class="pageref">{esc(pages)}</span>'


def entry_html(ctx, entry, out_rel):
    group, label, target = L.marker_info(entry["marker"], entry["target"])
    text = entry["text"] or ""
    cite_html = pin(entry["pages"])
    cls = f'e-{group}'
    lead = trail = ""
    if entry["marker"] == "role":
        # the marker's value is a closed-set key, not a person: show the
        # human bucket, never "class-1d", at the head of the note
        lead = (f'<span class="rel">'
                f'{esc(site_roles.bucket_label(entry["target"]))}</span> — ')
    elif target:
        other = ctx["char_by_id"].get(target)
        if other:
            other_href = posixpath.relpath(other["href"],
                                           posixpath.dirname(out_rel) or ".")
            trail = (f' <span class="by">— '
                     f'<a class="rel" href="{other_href}">'
                     f'{esc(other["name"])}</a></span>')
        else:
            trail = (f' <span class="by">— '
                     f'{esc(site_arch.display_name("", target))}</span>')
    pcls = ' class="verb"' if entry["quote"] else ""
    pin_html = f' <span class="pin">{cite_html}</span>' if cite_html else ""
    # One body cell per row. The label is the only thing in column one; the
    # note, its speaker and its page all flow together in column two, so a
    # long name wraps under the sentence rather than inside the 104px gutter.
    return (f'<li class="{cls}"><span class="mlabel">{esc(label)}</span>'
            f'<div class="ebody"><p{pcls}>{lead}{esc(text)}{trail}{pin_html}'
            f'</p></div></li>')


def scene_block(ctx, block, out_rel, *, show_vol=True, fold=False, uid=""):
    """One ledger scene: heading (volume + pages + title) and its entries.

    fold=True puts the entries behind a disclosure so a page with two hundred
    scenes still reads as a list of moments, not a wall of transcript; the fold
    is the only expander the scene gets. The heading names the printed pages as
    plain reference text — see the module docstring for why it is not a chip.

    `uid` namespaces the anchor when several ledgers share one page (an A–Z
    initial page holds one block per person), so two people's scenes can never
    collide on the same id.
    """
    vol = block["vol"]
    anchor = re.sub(r"[^a-z0-9]+", "-", block["heading"].lower()).strip("-")[:48]
    # Never re-strip after slicing: the published ids keep the hyphen a
    # 48-character cut leaves behind, and every cross-link is built from the
    # same slug. The uid only prefixes, so an A–Z page can hold several people.
    anchor = f"{uid}{anchor}"
    head = ['<div class="head">']
    if show_vol:
        head.append(f'<span class="pg">{vol_chip(ctx, vol, out_rel)}</span>')
    head.append(f'<span class="ttl">{esc(block["title"])}</span>')
    if block["pages"]:
        head.append(f'<span class="pgs">{pages_ref(block["pages"])}</span>')
    head.append("</div>")
    items = [entry_html(ctx, e, out_rel)
             for e in block["entries"] if e["text"]]
    if not items:
        return ""
    list_html = f'<ul class="ledger">{"".join(items)}</ul>'
    if fold:
        n_lines = sum(1 for b in [block] for e in b["entries"] if e["quote"])
        count = (f'{len(items)} entries'
                 f'{f" · {n_lines} quoted" if n_lines else ""}')
        return (f'<details class="scene ev" id="ev-{anchor}">'
                f'<summary>{"".join(head)}'
                f'<span class="n">{count}</span></summary>{list_html}</details>')
    return (f'<div class="scene ev" id="ev-{anchor}">'
            + "".join(head) + list_html + "</div>")


def volume_sections(ctx, led, out_rel, *, only=None, with_heading=True,
                    fold=False, uid="", heading_tag="h2",
                    heading=lambda vol: site_arch.volume_label(vol)):
    """All scene blocks of a parsed ledger, grouped by volume, oldest first.

    `uid` namespaces both the volume heading and every scene anchor inside it,
    which is what keeps an A–Z page — several people, several ledgers, one file
    — from emitting the same id twice.
    """
    order = {v["id"]: v["order"] for v in ctx["vol_list"]}
    out = []
    sections = [s for s in led["vols"] if only is None or s["vol"] in only]
    sections.sort(key=lambda s: order.get(s["vol"], 999))
    for section in sections:
        blocks = [scene_block(ctx, b, out_rel, fold=fold, uid=uid)
                  for b in section["blocks"]]
        blocks = [b for b in blocks if b]
        if not blocks:
            continue
        if with_heading:
            out.append(f'<{heading_tag} id="ev-{uid}{section["vol"]}">'
                       f'{esc(heading(section["vol"]))}</{heading_tag}>')
        out.append("".join(blocks))
    return "".join(out)


def evidence_count(led, vol=None):
    """Scenes and quoted lines a ledger contributes — used in meters."""
    scenes = quotes = 0
    for section in led["vols"]:
        if vol and section["vol"] != vol:
            continue
        scenes += len(section["blocks"])
        for b in section["blocks"]:
            quotes += sum(1 for e in b["entries"] if e["quote"] and e["text"])
    return scenes, quotes


def evidence_meters(ctx, led, vol=None):
    scenes, quotes = evidence_count(led, vol)
    vols = [s["vol"] for s in led["vols"] if vol is None or s["vol"] == vol]
    return [("Volumes worked", str(len(vols))),
            ("Scenes transcribed", f"{scenes:,}"),
            ("Quoted lines", f"{quotes:,}")]


def coverage_stub(ctx, *, subject, vol_ids=(), base=".", extra=""):
    """The honest page: what the walk has not reached yet, and where the
    evidence will land when it does. `base` is the page's own directory (or
    its output path), so every link here is depth-correct. No analysis, no summary, no spoilers.
    Unread volumes fall back to a single line of reference links rather than
    one repeated bullet per volume."""
    if vol_ids:
        shown = list(vol_ids)[:14]
        chips = " · ".join(vol_chip(ctx, v, base, tag=True) for v in shown)
        more = "" if len(vol_ids) <= 14 else \
            f' <span class="n">and {len(vol_ids) - 14} more</span>'
        vols = (f'<p>Named in {len(vol_ids)} volume'
                f'{"s" if len(vol_ids) != 1 else ""} — {chips}{more} — and '
                f'read line by line in none of them yet. Each link goes to '
                f'that volume\'s page, where the notes appear once it has '
                f'been read. See '
                f'<a href="{posixpath.relpath("appendix/coverage.html", _dir_of(base) or ".")}">'
                f'what has been read</a>.</p>')
    else:
        vols = (f'<p>This has not been worked through page by page yet, so '
                f'there is nothing to show beyond the mechanical facts above.</p>')
    return (f'<div class="box warn stub"><h4>Evidence state</h4>'
            f'<p>Nothing about {esc(subject)} has been read line by line yet. '
            f'This encyclopedia only publishes what someone has read and '
            f'anchored to a page, so this page lists what exists rather than '
            f'filling the gap.</p>'
            f'{vols}{extra}</div>')


def mechanical_facts(pairs):
    """Facts that need no reading: counts, lengths, which volumes a name is
    written in. Everything here is a query result, not an interpretation."""
    rows = "".join(f'<tr><th>{esc(k)}</th><td>{v}</td></tr>'
                   for k, v in pairs if v not in (None, "", 0, "0"))
    return f'<table class="facts">{rows}</table>' if rows else ""


def mentions_by_volume(ctx, char_id, out_rel, limit=None):
    """'Named in these volumes' — the extractor's mention table, so it is safe
    to publish on a volume the walk has not read yet. It says where a name is
    written, nothing more."""
    rows = ctx["mentions_by_char"].get(char_id) or []
    order = {v["id"]: v["order"] for v in ctx["vol_list"]}
    by_vol = {}
    for r in rows:
        by_vol.setdefault(r["vol_id"], set()).add(r["status"])
    vols = sorted(by_vol, key=lambda v: order.get(v, 999))
    if limit:
        vols = vols[:limit]
    chips = []
    for v in vols:
        spoken = "quotes" in by_vol[v]
        chips.append(
            f'{vol_chip(ctx, v, out_rel)}'
            f'<span class="n">{"speaks" if spoken else "named"}</span>')
    return f'<p class="mentions">{"".join(chips)}</p>' if chips else ""


def identity_block(ctx, c, out_rel):
    """Who this is, mechanically: the name, the spellings the text uses, and
    the volumes the name appears in. No interpretation, so it is usable on an
    unwalked character page."""
    aliases = ctx["aliases_by_char"].get(c["id"]) or []
    shown = [a for a in aliases if a and a.lower() != c["name"].lower()][:12]
    rows = [("Known as", esc(", ".join(shown)) if shown else ""),
            # This used to say "Role in the story" while printing the presence
            # band, which is not a role. Presence is what is actually counted.
            ("How often they appear",
             esc(site_arch.TIER_LABEL.get(c["tier"], "Character"))),
            ("Named in", f'{c["coverage"]} of {ctx["stats"]["vols"]} volumes')]
    placed = site_roles.facts_for(ctx.get("role_facts") or {}, c["id"])
    if placed:
        # Plain page numbers: the ledger note is a paraphrase, so there is no
        # scene to open. Kept in the "Vol. 1 p.224" shape the footer explains.
        rows.insert(0, ("Where the pages place them", esc("; ".join(
            f'{label} ({site_arch.volume_short(vol)} {f["page"]})'
            for vol, label, f in placed))))
    head = mechanical_facts([(k, v) for k, v in rows if v])
    where = mentions_by_volume(ctx, c["id"], out_rel)
    return head + (f'<p class="subhead">Where the name appears</p>{where}'
                   if where else "")

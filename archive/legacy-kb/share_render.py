#!/usr/bin/env python3
"""P7: markdown → HTML renderer + page templates for the share site.

Pure functions used by kb/build_share_site.py. Handles exactly the
markdown subset the dossiers use (verified by scan, 82 files):
   ATX headings 1-6 · bullet lists (0/2-space indent, one nesting level)
   · **bold** · `code` · [text](links) · plain paragraphs.
   Lines abutting a bullet join it (CommonMark lazy continuation) — the
   dossiers keep multi-line verbatim quotes byte-faithful in the md.
No tables, italics, fences or blockquotes appear in the corpus.

Slug rule matches the authored in-page anchors (GitHub-style):
lowercase, drop everything but [a-z0-9 space hyphen], spaces→hyphens
("Wang Mei-Yu" → "wang-mei-yu").
"""

import html
import re

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
HEADING_RE = re.compile(r"^(#{1,6}) (.+)$")
BULLET_RE = re.compile(r"^( *)- (.*)$")


def slug(text):
    """GitHub-style anchor id for a heading."""
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9 -]", "", t)
    return t.replace(" ", "-")


def inline(text):
    """escape HTML, then code/bold/links (patterns survive escaping)."""
    out = html.escape(text, quote=False)
    out = LINK_RE.sub(
        lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    out = CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", out)
    out = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)
    return out


def render(md):
    """markdown → (html, headings) where headings = [(level, id, text)]."""
    lines = md.splitlines()
    out = []
    headings = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            hid = slug(text)
            headings.append((level, hid, text))
            out.append(f'<h{level} id="{hid}">{inline(text)}</h{level}>')
            i += 1
            continue
        mb = BULLET_RE.match(line)
        if mb:
            base = len(mb.group(1))
            items = [(base, mb.group(2))]
            i += 1
            while i < n:
                li = lines[i]
                mi = BULLET_RE.match(li)
                if mi:
                    items.append((len(mi.group(1)), mi.group(2)))
                    i += 1
                    continue
                if li.strip() and not HEADING_RE.match(li):
                    prev_b, prev_t = items[-1]
                    items[-1] = (prev_b, f"{prev_t} {li.strip()}")
                    i += 1
                    continue
                break
            out.append(render_list(items, base))
            continue
        block = [line]
        i += 1
        while i < n and lines[i].strip() and not HEADING_RE.match(lines[i]) \
                and not BULLET_RE.match(lines[i]):
            block.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(b.strip() for b in block))
                   + "</p>")
    return "\n".join(out), headings


def render_list(items, base):
    """nested bullets (corpus: 0 vs 2 spaces); sub-<ul> lives inside its
    <li> so the output is valid HTML."""
    parts = ["<ul>"]
    sub_open = False
    li_open = False
    for ind, text in items:
        want = 0 if ind <= base else 1
        if want == 1 and li_open:
            if not sub_open:
                parts.append("<ul>")
                sub_open = True
            parts.append(f"<li>{inline(text)}</li>")
            continue
        if sub_open:
            parts.append("</ul></li>")
            sub_open = False
            li_open = False
        elif li_open:
            parts.append("</li>")
            li_open = False
        parts.append(f"<li>{inline(text)}")
        li_open = True
    if sub_open:
        parts.append("</ul></li>")
        li_open = False
    if li_open:
        parts.append("</li>")
    parts.append("</ul>")
    return "".join(parts)


def rewrite_links(html_text):
    """dossier-local .md hrefs → .html (keeps #anchors)."""
    def sub(m):
        target = m.group(1)
        if ".md#" in target:
            target = target.replace(".md#", ".html#")
        elif target.endswith(".md"):
            target = target[:-3] + ".html"
        return f'href="{target}"'

    return re.sub(r'href="([^"]+)"', sub, html_text)


TABLE_SEP_RE = re.compile(r"^:?-{2,}:?$")
EM_RE = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?!\*)")


def inline_full(text):
    """escape, then links/code/bold/italic — authored guide files use all
    four."""
    out = html.escape(text, quote=False)
    out = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    out = CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", out)
    out = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)
    out = EM_RE.sub(lambda m: f"<em>{m.group(1)}</em>", out)
    return out


def render_full(md):
    """authored markdown (headings, lists, tables, blockquotes, rules,
    emphasis) → (html, headings). Used for the guide and transcript files;
    the dossiers stay on render() so their output cannot drift."""
    lines = md.splitlines()
    out, headings = [], []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        mh = HEADING_RE.match(line)
        if mh:
            level = len(mh.group(1))
            text = mh.group(2).strip()
            hid = slug(text)
            headings.append((level, hid, text))
            out.append(f'<h{level} id="{hid}">{inline_full(text)}</h{level}>')
            i += 1
            continue
        if line.strip() == "---":
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
                if j == 1 and cells and all(TABLE_SEP_RE.match(c)
                                            for c in cells if c):
                    continue
                rows.append(cells)
            if rows:
                th = "".join(f"<th>{inline_full(c)}</th>" for c in rows[0])
                body = "".join(
                    "<tr>" + "".join(f"<td>{inline_full(c)}</td>"
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
                f"<p>{inline_full(p.strip())}</p>"
                for p in "\n".join(block).split("\n\n") if p.strip())
            out.append(f'<blockquote class="verb">{paras}</blockquote>')
            continue
        if line.startswith("- "):
            items = [line[2:]]
            i += 1
            while i < n:
                nxt = lines[i]
                if nxt.startswith("- "):
                    items.append(nxt[2:])
                    i += 1
                elif nxt.strip() and not HEADING_RE.match(nxt) \
                        and not nxt.startswith(("|", "> ")) and nxt.strip() != "---":
                    items[-1] += " " + nxt.strip()
                    i += 1
                else:
                    break
            out.append("<ul>" + "".join(f"<li>{inline_full(it)}</li>"
                                        for it in items) + "</ul>")
            continue
        block = [line]
        i += 1
        while i < n and lines[i].strip() and not HEADING_RE.match(lines[i]) \
                and not lines[i].startswith(("- ", "|", ">")) \
                and lines[i].strip() != "---":
            block.append(lines[i])
            i += 1
        out.append("<p>" + inline_full(" ".join(b.strip() for b in block))
                   + "</p>")
    return "\n".join(out), headings


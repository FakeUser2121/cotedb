#!/usr/bin/env python3
"""Second pass: turn scan.json into the deliverables.

pages.csv / links.csv / graph.json / graph.html / sitemap.mermaid plus the
diagnostics (mismatched link text, repeated content, layout drift) that feed
summary.md and problems.md. Still read-only with respect to the site.
"""
import csv
import html as H
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/user3/Documents/unsafe/cote")
SITE = ROOT / "share" / "site"
OUT = ROOT / "site-audit"
scan = json.load(open(OUT / "scan.json"))
P = scan["pages"]


def page_type(path):
    if path == "index.html":
        return "home"
    if re.match(r"people/minor/[a-z]\.html$", path):
        return "minor A–Z index"
    if path == "people/index.html":
        return "section index"
    if path.startswith("people/"):
        return "character page"
    if path == "story/index.html":
        return "section index"
    if re.match(r"story/y\d\.html$", path):
        return "year hub"
    if re.match(r"story/v/[^/]+/index\.html$", path):
        return "volume page"
    if re.match(r"story/v/[^/]+/.+\.(guide|transcript)\.html$", path):
        return "volume transcript" if path.endswith("transcript.html") else "volume guide"
    if path == "school/index.html":
        return "section index"
    if path.startswith("school/exam/"):
        return "exam page"
    if path.startswith("school/system/"):
        return "system page"
    if path == "school/chronology.html":
        return "chronology page"
    if path == "world/index.html":
        return "section index"
    if path.startswith("world/"):
        return "place page"
    if path == "topics/index.html":
        return "section index"
    if path.startswith("topics/"):
        return "topic page"
    if path == "guides/index.html":
        return "section index"
    if path.startswith("guides/"):
        return "guide page"
    if path == "appendix/index.html":
        return "section index"
    if path.startswith("appendix/"):
        return "appendix page"
    return "other"


CRUMBS_RE = re.compile(r'<nav class="crumbs".*?</nav>', re.S)


def menu_parent(path):
    """What the page itself says its parent is: the crumb before the current
    one, as "label -> /href". This is the *intended* hierarchy."""
    m = CRUMBS_RE.search(main_body(path))
    if not m:
        return "(no breadcrumb)"
    seg = m.group(0)
    links = re.findall(r'<a href="([^"]*)">([^<]*)</a>', seg)
    if not links:
        return "(top level)"
    href, label = links[-1]
    norm = re.sub(r"^\.\./+", "", href)
    return f"{strip(label)} -> /{norm}"


def composition(pg):
    """Dominant form of the page body, from the element counts."""
    s = {"prose": pg["paris"], "quotes": pg["quote_rows"] + pg["ledger_rows"],
         "lists": pg["list_items"], "tables": pg["table_rows"]}
    scenes = pg["scenes"]
    total = sum(s.values()) or 1
    top = max(s, key=s.get)
    if scenes and scenes * 4 >= total:
        return "transcribed scene entries"
    return top


def status(pg):
    m = pg["markers"]
    if m["transcribed"]:
        return "transcribed line by line"
    if m["unread"]:
        return "not yet worked through"
    if m["gap"]:
        return "partial: names with no role line yet"
    if pg["words"] < 220:
        return "thin"
    return "complete"


MAIN_RE = re.compile(r'<main class="content">(.*?)</main>', re.S)
SECTION_SPLIT = re.compile(r'<h([23])(?: [^>]*)?id="([^"]*)"[^>]*>(.*?)</h\1>', re.S)


def body_of(path):
    return (SITE / path).read_text(encoding="utf-8")


def main_body(path):
    m = MAIN_RE.search(body_of(path))
    return m.group(1) if m else ""


strip = lambda s: re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def content_chunks():
    """(hash, heading, kind, page) for every h2/h3 section of every page body.

    Used to find the same content repeated in more than one place. The rails
    are outside <main>, so shell navigation never counts as repetition.
    """
    rows = []
    for path in P:
        inner = main_body(path)
        ms = list(SECTION_SPLIT.finditer(inner))
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(inner)
            text = strip(inner[m.start():end])
            if len(text) < 60:
                continue
            rows.append((hash(text), strip(m.group(3)), m.group(2), path,
                         len(text)))
    return rows


def main():
    all_edges = scan_all_edges()
    edges_by_src = defaultdict(list)
    for e in all_edges:
        edges_by_src[e["from"]].append(e)
    # actual parent = who links here from body/cross-reference regions
    body_parents = defaultdict(list)
    for e in all_edges:
        if not e.get("external") and e["region"] in ("body", "cross-reference") \
                and e["from"] != e["to"]:
            body_parents[e["to"]].append(e["from"])
    types = Counter()
    with open(OUT / "pages.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["url", "title", "h1", "page_type", "parent_section",
                    "depth_from_home", "menu_parent", "most_linked_from",
                    "words", "composition",
                    "status", "volumes_cited", "verified_line_by_line",
                    "out_links", "in_links", "external_links",
                    "citations_unique", "citations_total", "page_anchors", "pageref_spans", "scenes",
                    "quote_rows", "tables", "details_expanders", "headings"])
        for path, pg in sorted(P.items()):
            t = page_type(path)
            types[t] += 1
            out_links = len([e for e in edges_by_src[path]
                             if not e.get("external")])
            bp = Counter(body_parents.get(path, []))
            w.writerow([
                "/" + path, pg["title"], pg["h1"] or "(no <h1> element on this page)", t,
                path.split("/")[0] if "/" in path else "(root)",
                scan["depth"].get(path, ""),
                menu_parent(path),
                "|".join(p for p, _n in bp.most_common(3)),
                pg["words"], composition(pg), status(pg),
                " ".join("V" + v for v in pg["vols"]) or "none",
                "yes" if pg["markers"]["transcribed"] else "no",
                out_links, scan["incoming"].get(path, 0), pg["n_external"],
                pg["cite_count"], pg["cite_total"], pg["page_refs"], pg["pageref_spans"], pg["scenes"],
                pg["quote_rows"], pg["tables"], pg["details"],
                " / ".join(h[2] for h in pg["headings"][:12]),
            ])

    # ---- links.csv, every edge with region and purpose
    with open(OUT / "links.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "target", "anchor", "link_text", "region",
                    "purpose", "target_title"])
        for e in sorted(all_edges, key=lambda x: (x["from"], x["to"])):
            tgt = e["to"]
            w.writerow([
                "/" + e["from"],
                tgt if e.get("external") else ("/" + tgt),
                e.get("anchor", ""), e["text"][:120], e["region"],
                purpose(e), P.get(tgt, {}).get("title", "")[:80]
                if not e.get("external") else "EXTERNAL",
            ])

    # ---- graph.json
    nodes = []
    for path, pg in sorted(P.items()):
        nodes.append({
            "id": path, "label": pg["h1"] or pg["title"], "type": page_type(path),
            "section": path.split("/")[0] if "/" in path else "root",
            "words": pg["words"], "depth": scan["depth"].get(path),
            "in": scan["incoming"].get(path, 0),
            "out": len([e for e in edges_by_src[path] if not e.get("external")]),
            "status": status(pg),
        })
    agg = defaultdict(lambda: {"count": 0, "texts": Counter(), "regions": Counter(),
                               "anchors": Counter()})
    for e in all_edges:
        if e.get("external"):
            continue
        k = (e["from"], e["to"])
        a = agg[k]
        a["count"] += 1
        a["texts"][e["text"][:60]] += 1
        a["regions"][e["region"]] += 1
        if e.get("anchor"):
            a["anchors"][e["anchor"]] += 1
    edges = [{"source": s, "target": t, "count": v["count"],
              "text": v["texts"].most_common(1)[0][0],
              "region": v["regions"].most_common(1)[0][0],
              "anchors": v["anchors"].most_common(3)}
             for (s, t), v in sorted(agg.items())]
    json.dump({"nodes": nodes, "edges": edges},
              open(OUT / "graph.json", "w"), ensure_ascii=False)

    # ---- diagnostics
    diag = {}
    diag["types"] = dict(types)
    diag["edges_total"] = len(all_edges)
    diag["edges_external"] = len([e for e in all_edges if e.get("external")])
    diag["region_counts"] = dict(Counter(e["region"] for e in all_edges))
    diag["hubs"] = sorted(((scan["incoming"].get(p, 0), p) for p in P),
                          reverse=True)[:15]
    diag["lowest_in"] = sorted(((scan["incoming"].get(p, 0), p) for p in P))[:15]
    diag["largest_out"] = sorted(
        ((len([e for e in edges_by_src[p] if not e.get("external")]), p)
         for p in P), reverse=True)[:12]
    diag["dead_end_pages"] = [p for p in sorted(scan["reachable"])
                              if not edges_by_src.get(p)]
    diag["word_extremes"] = sorted(
        ((P[p]["words"], p) for p in P), reverse=True)[:10]
    diag["thinnest"] = sorted((P[p]["words"], p) for p in P)[:15]
    diag["dup_ids"] = scan["dup_ids"]
    diag["missing"] = scan["missing"]
    diag["broken_anchors"] = scan["broken_anchor"]

    # repeated content
    chunks = content_chunks()
    by_hash = defaultdict(list)
    for h, head, hid, path, n in chunks:
        by_hash[h].append((head, hid, path, n))
    repeats = {h: v for h, v in by_hash.items() if len({p for _a, _b, p, _c in v}) > 1}
    diag["repeated_sections"] = sorted(
        [{"heading": v[0][0], "pages": sorted({p for _a, _b, p, _c in v}),
          "n_pages": len({p for _a, _b, p, _c in v}), "chars": v[0][3]}
         for v in repeats.values()], key=lambda d: -d["n_pages"])[:40]
    diag["repeated_same_page"] = sorted(
        [{"heading": v[0][0], "path": v[0][2], "ids": [x[1] for x in v]}
         for v in by_hash.values()
         if len({p for _a, _b, p, _c in v}) == 1 and len(v) > 1],
        key=lambda d: -len(d["ids"]))[:20]

    # link text vs destination title
    mism = []
    for e in all_edges:
        if e.get("external") or e["region"] in ("masthead", "tab bar", "left rail",
                                                "right rail", "breadcrumb", "footer"):
            continue
        tgt = P.get(e["to"])
        if not tgt or not e["text"]:
            continue
        t = strip(e["text"])
        dest = tgt["h1"] or tgt["title"]
        if t.lower() in dest.lower() or dest.lower().split(" ·")[0] in t.lower():
            continue
        mism.append({"source": e["from"], "target": e["to"], "text": t[:70],
                     "dest": dest[:70], "anchor": e.get("anchor", "")})
    diag["text_mismatch_examples"] = mism[:60]
    diag["text_mismatch_count"] = len(mism)

    # spelling variants: link texts pointing at one page that differ
    variants = defaultdict(set)
    for e in all_edges:
        if e.get("external") or not e["text"]:
            continue
        variants[e["to"]].add(strip(e["text"]))
    diag["multi_text_targets"] = sorted(
        [{"target": t, "n": len(v), "examples": sorted(v)[:8]}
         for t, v in variants.items()
         if len(v) > 3 and t in P], key=lambda d: -d["n"])[:25]

    # nav elements: which regions appear on which pages
    region_pages = defaultdict(set)
    for path, pg in P.items():
        for _h, _t, r in pg["links"]:
            region_pages[r].add(path)
    diag["region_coverage"] = {r: len(v) for r, v in region_pages.items()}
    diag["pages_without_left_rail"] = sorted(set(P) - region_pages.get("left rail", set()))
    diag["pages_without_right_rail"] = sorted(set(P) - region_pages.get("right rail", set()))
    diag["pages_without_crumbs"] = sorted(set(P) - region_pages.get("breadcrumb", set()))

    json.dump(diag, open(OUT / "diag.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in diag.items()
                      if k in ("types", "edges_total", "region_counts",
                               "text_mismatch_count", "region_coverage",
                               "pages_without_left_rail", "pages_without_crumbs",
                               "dead_end_pages")}, indent=1)[:2600])




def scan_all_edges():
    """Rebuild every edge with the same walk the crawler used."""
    posixpath_join = __import__("posixpath").join
    posixpath_norm = __import__("posixpath").normpath
    posixpath_dirname = __import__("posixpath").dirname
    edges = []
    for path, pg in sorted(P.items()):
        for href, text, region in pg["links"]:
            if href.startswith("#"):
                edges.append({"from": path, "to": path, "anchor": href[1:],
                              "text": text, "region": region})
                continue
            if href.startswith(("http", "mailto:", "data:", "javascript:")):
                edges.append({"from": path, "to": href, "anchor": "",
                              "text": text, "region": region, "external": True})
                continue
            p_part, _, frag = href.partition("#")
            if not p_part:
                target = path
            elif p_part.startswith("/"):
                target = posixpath_norm(p_part.lstrip("/"))
            else:
                target = posixpath_norm(posixpath_join(posixpath_dirname(path) or ".",
                                                       p_part))
            edges.append({"from": path, "to": target, "anchor": frag,
                          "text": text, "region": region})
    return edges


def purpose(e):
    if e.get("external"):
        return "other (external)"
    if e["region"] in ("masthead", "tab bar"):
        return "navigation"
    if e["region"] == "left rail":
        return "navigation (contents)"
    if e["region"] == "right rail":
        return "navigation (page context)"
    if e["region"] == "breadcrumb":
        return "back to parent"
    if e["region"] == "footer":
        return "navigation (footer)"
    if e.get("anchor") and e["from"] == e["to"]:
        return "other (in-page jump)"
    if re.search(r"Vol\.|p\.\d", e["text"]) or "transcript" in e.get("anchor", ""):
        return "citation"
    return "cross-reference"


def composition_of(pg):
    return composition(pg)


if __name__ == "__main__":
    main()

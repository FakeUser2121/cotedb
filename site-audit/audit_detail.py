#!/usr/bin/env python3
"""Third pass: the checks that need both ends of a link.

For every anchor link, read the text of the element it points at and compare
it with the link text; fingerprint content blocks so repetition across pages
is counted, not guessed; measure per-page volume coverage from the citation
markup; and compare the layout signature of pages that share a type.
"""
import html as H
import json
import re
import unicodedata
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path("/home/user3/Documents/unsafe/cote")
SITE = ROOT / "share" / "site"
OUT = ROOT / "site-audit"
scan = json.load(open(OUT / "scan.json"))
P = scan["pages"]

HEAD_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "summary"}


class IdText(HTMLParser):
    """id -> (tag, first text inside that element)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.map = {}
        self._open = []      # stack of (tag, id)
        self._capture = None
        self._buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        ident = a.get("id")
        if ident and ident not in self.map:
            self.map[ident] = [tag, ""]
            self._capture = ident
            self._buf = []
        self._open.append(tag)

    def handle_data(self, data):
        if self._capture:
            self._buf.append(data)
            if len(" ".join(self._buf)) > 90:
                self.map[self._capture][1] = re.sub(
                    r"\s+", " ", " ".join(self._buf)).strip()[:90]
                self._capture = None


def strip(s):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def norm(s):
    """case- and accent-folded, for text comparison that does not trip over
    macrons in names."""
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ō", "o").replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def id_texts(path):
    p = IdText()
    p.feed((SITE / path).read_text(encoding="utf-8"))
    return {k: (v[0], strip(v[1]) if len(v[1]) <= 90 else v[1])
            for k, v in p.map.items()}


CLASS_MARK = re.compile(r'class="(masthead|tabs|rail left|rail right|crumbs|meter|kicker|tagline|lede|print-doc)')


def layout_sig(path, raw):
    marks = set(CLASS_MARK.findall(raw))
    m = re.search(r'<body[^>]*class="([^"]*)"', raw)
    if m:
        marks.update(m.group(1).split())
    tm = re.search(r"<title>(.*?)</title>", raw, re.S)
    lvl = [h[0] for h in P[path]["headings"]]
    return {
        "regions": tuple(sorted(marks)),
        "heading_levels": tuple(sorted(set(lvl))),
        "has_rail_left": 'class="rail left"' in raw,
        "has_rail_right": 'class="rail right"' in raw,
        "has_meter": 'class="meter"' in raw,
        "has_crumbs": 'class="crumbs"' in raw,
        "has_lede": 'class="lede"' in raw,
        "has_kicker": 'class="kicker"' in raw,
        "h1_count": len(re.findall(r"<h1", raw)),
        "h2_count": len(re.findall(r"<h2", raw)),
        "details": P[path]["details"],
        "title_suffix_ok": bool(tm and " · COTE" in tm.group(1)),
    }


def page_volumes(raw):
    """Volumes a page cites, read off the citation markup itself."""
    cites = re.findall(r'<span class="pageref">([^<]*)</span>', raw)
    cites += [strip(x) for x in re.findall(r'<span class="pg">(.*?)</span>', raw, re.S)]
    vols = Counter()
    for c in cites:
        for m in re.finditer(r"Vol\.\s*(\d+(?:\.\d+)?)", c):
            vols[m.group(1)] += 1
        for m in re.finditer(r"\b([yw]\d+v\d+(?:\.\d+)?)\b", c):
            vols[m.group(1)] += 1
    return vols


def block_fingerprints():
    """Scene blocks and role-group lists, fingerprinted by their visible text,
    so repetition across pages is counted from what is actually on the page."""
    scene_pages = defaultdict(set)
    row_pages = defaultdict(set)
    group_pages = defaultdict(set)
    for path in P:
        raw = (SITE / path).read_text(encoding="utf-8")
        main = re.search(r'<main class="content">(.*?)</main>', raw, re.S)
        body = main.group(1) if main else ""
        for m in re.finditer(r'<(?:div|details) class="scene ev"[^>]*id="([^"]*)"[^>]*>(.*?)</(?:div|details)>',
                             body, re.S):
            txt = strip(m.group(2))
            if len(txt) > 40:
                scene_pages[hash(txt)].add(path)
        for m in re.finditer(r'<li class="e-[a-z]+">.*?</li>', body, re.S):
            row_pages[hash(m.group(0))].add(path)
        for m in re.finditer(r'<h4[^>]*>(.*?)</h4>\s*<ul>(.*?)</ul>', body, re.S):
            group_pages[hash(strip(m.group(1)) + strip(m.group(2)))].add(path)
    return scene_pages, row_pages, group_pages


def main():
    out = {}
    # ---- anchor text vs link text
    bad_anchor_text = []
    anchor_missing = []
    for path, pg in sorted(P.items()):
        texts = None
        for href, ltxt, region in pg["links"]:
            if not href.startswith("#") or not ltxt:
                continue
            frag = href[1:]
            if texts is None:
                texts = id_texts(path)
            if frag not in texts:
                anchor_missing.append({"page": path, "anchor": frag,
                                       "text": strip(ltxt)[:60]})
                continue
            tag, atext = texts[frag]
            if tag not in HEAD_TAGS or not atext:
                continue
            n1, n2 = norm(strip(ltxt)), norm(atext)
            if not n1 or not n2:
                continue
            if n1 in n2 or n2 in n1:
                continue
            bad_anchor_text.append({"page": path, "anchor": frag,
                                    "link_text": strip(ltxt)[:70],
                                    "target_text": atext[:70], "region": region})
    out["anchor_text_mismatch"] = bad_anchor_text
    out["anchor_missing"] = anchor_missing

    # ---- cross-page anchor links: same check, target page
    cache = {}
    cross_bad = []
    for path, pg in sorted(P.items()):
        for href, ltxt, region in pg["links"]:
            if not href.startswith("#") and "#" in href and not href.startswith(("http", "mailto:")):
                target = re.sub(r"^\.\./+", "", href.split("#")[0])
                if not re.match(r"^[\w./-]+$", target):
                    continue
                frag = href.split("#", 1)[1]
                if target not in P:
                    continue
                if target not in cache:
                    cache[target] = id_texts(target)
                t = cache[target].get(frag)
                if not t or not ltxt:
                    continue
                tag, atext = t
                if tag not in HEAD_TAGS or not atext:
                    continue
                n1, n2 = norm(strip(ltxt)), norm(atext)
                if n1 and n2 and (n1 in n2 or n2 in n1):
                    continue
                cross_bad.append({"from": path, "to": target, "anchor": frag,
                                  "link_text": strip(ltxt)[:70],
                                  "target_text": atext[:70], "region": region})
    out["cross_page_anchor_text_mismatch"] = cross_bad

    # ---- naming: link text spelling variants per target
    variants = defaultdict(set)
    for path, pg in P.items():
        for href, ltxt, region in pg["links"]:
            if not ltxt or href.startswith(("#", "http", "mailto:")):
                continue
            t = re.sub(r"^\.\./+", "", href.split("#")[0])
            if t in P:
                variants[t].add(strip(ltxt))
    multi = [{"target": t, "n": len(v),
              "variants": sorted(v, key=len)[:6]}
             for t, v in variants.items() if len(v) > 2 and t in P]
    out["many_text_variants"] = sorted(multi, key=lambda d: -d["n"])[:30]

    # ---- h1 vs file stem spelling (romanisation drift)
    h1_mismatch = []
    for path, pg in sorted(P.items()):
        if not path.startswith("people/") or "#" in path:
            continue
        stem = path.split("/")[-1].replace(".html", "")
        if stem in ("index",) or path.startswith("people/minor/"):
            continue
        h = norm(pg["h1"])
        s = norm(stem.replace("-", " "))
        if s and s not in h:
            h1_mismatch.append({"page": path, "h1": pg["h1"], "stem": stem})
    out["h1_vs_stem"] = h1_mismatch

    # ---- layout drift per type
    import audit_build as AB
    sigs = defaultdict(list)
    for path, pg in sorted(P.items()):
        raw = (SITE / path).read_text(encoding="utf-8")
        sigs[AB.page_type(path)].append(layout_sig(path, raw))
    drift = {}
    for t, lst in sigs.items():
        keys = ("has_rail_left", "has_rail_right", "has_meter", "has_crumbs",
                "has_lede", "has_kicker", "title_suffix_ok")
        combos = Counter(tuple(l[k] for k in keys) for l in lst)
        if len(combos) > 1:
            drift[t] = {"n_variants": len(combos),
                        "minority": [dict(zip(keys, c)) for c, n in
                                     list(combos.most_common())[1:]],
                        "counts": combos.most_common()}
    out["layout_variants"] = drift

    # ---- heading level usage by type
    hl = defaultdict(Counter)
    for path, pg in P.items():
        for lvl, _i, _t in pg["headings"]:
            hl[AB.page_type(path)][lvl] += 1
    out["heading_levels_by_type"] = {k: dict(v) for k, v in hl.items()}

    # ---- coverage: volumes cited per page
    cov = {}
    for path in sorted(P):
        raw = (SITE / path).read_text(encoding="utf-8")
        v = page_volumes(raw)
        cov[path] = dict(v)
    out["volume_citations"] = cov

    # ---- repetition
    sp, rp, gp = block_fingerprints()
    out["scene_blocks"] = {"distinct": len(sp),
                           "total_occurrences": sum(len(v) for v in sp.values()),
                           "on_2plus_pages": sum(1 for v in sp.values() if len(v) > 1),
                           "worst": sorted(((len(v), k) for k, v in sp.items()),
                                           reverse=True)[:3][:0]}
    out["ledger_rows"] = {"distinct": len(rp),
                          "total_occurrences": sum(len(v) for v in rp.values()),
                          "on_2plus_pages": sum(1 for v in rp.values() if len(v) > 1)}
    out["role_groups"] = {"distinct": len(gp),
                          "on_2plus_pages": sorted(
                              [(len(v), list(v)[:3]) for v in gp.values() if len(v) > 1],
                              reverse=True)[:10]}

    json.dump(out, open(OUT / "detail.json", "w"), ensure_ascii=False, indent=1)
    print("anchor text mismatches (same page):", len(bad_anchor_text))
    print("missing same-page anchors:", len(anchor_missing))
    print("cross-page anchor text mismatches:", len(cross_bad))
    print("targets with >2 link-text variants:", len(multi))
    print("person pages whose h1 does not contain the file stem:", len(h1_mismatch))
    print("types with more than one layout signature:", list(drift))
    print("scene blocks:", out["scene_blocks"]["distinct"],
          "occurrences:", out["scene_blocks"]["total_occurrences"],
          "repeated:", out["scene_blocks"]["on_2plus_pages"])
    print("ledger rows:", out["ledger_rows"])


if __name__ == "__main__":
    main()

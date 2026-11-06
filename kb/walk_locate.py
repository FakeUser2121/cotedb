#!/usr/bin/env python3
"""Walk tooling: locate alias hits per volume, extract page-range text, track walk positions."""
import argparse
import csv
import os
import re
import sys
import unicodedata

TEXT_DIR = "text"
TSV_PATH = "content/characters.tsv"

PAGE_RE = re.compile(r"^--- page (\d+) ---\s*$", re.MULTILINE)


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def vol_files():
    out = {}
    for fn in sorted(os.listdir(TEXT_DIR)):
        if not fn.endswith(".txt"):
            continue
        stem = fn[:-4]
        key = fold(stem).replace("cote", "").replace(" ", "").replace(".", "")
        out[key] = os.path.join(TEXT_DIR, fn)
    return out


def parse_pages(path):
    text = open(path, encoding="utf-8").read()
    pages = []
    marks = list(PAGE_RE.finditer(text))
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        pages.append((int(m.group(1)), text[start:end].strip("\n")))
    return pages


def alias_patterns(char_id):
    forms = set()
    with open(TSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["id"] != char_id:
                continue
            for field in ("name", "sort", "aliases"):
                for raw in (row.get(field) or "").split(";"):
                    if raw.strip():
                        forms.add(raw.strip())
            break
    if not forms:
        sys.exit(f"no aliases for {char_id}")
    return sorted({fold(f) for f in forms})


def page_hits(pages, patterns):
    hits = []
    for num, body in pages:
        fb = fold(body)
        n = sum(1 for line in fb.splitlines() if any(p in line for p in patterns))
        if n:
            hits.append((num, n))
    return hits


def cluster(hits):
    out = []
    for num, n in hits:
        if out and num == out[-1][1] + 1:
            out[-1][1] = num
            out[-1][2] += n
        else:
            out.append([num, num, n])
    return out


SECTION_RE = re.compile(
    r"(?i)^(chapter\s*(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    r"|prologue|epilogue|short\s+stori?e?s?|postscript|afterword)\b[:\.]?\s*(.*)$"
)
# running headers / noise that must never count as section starts
HEADER_NOISE = re.compile(
    r"(?i)(classroom of the elite|legacyemtls|royalmtls|goldenagato|mp4directs|https?://|translations? by|compilation)"
)


def _parse_toc(pages, head_limit=16):
    """Parse TOC titles with continuation-line joining from early pages."""
    toc = {}          # tag-key (e.g. 'chapter 1') -> title
    order = []        # display labels in TOC order
    for p_num, body in pages[:head_limit]:
        lines = [l.strip() for l in body.splitlines()]
        in_toc = any("table of contents" in l.lower() for l in lines)
        if not in_toc and p_num > 8:
            continue
        i = 0
        while i < len(lines):
            l = lines[i]
            m = SECTION_RE.match(l)
            if not m:
                i += 1
                continue
            tag = re.sub(r"\s+", " ", m.group(1).lower().rstrip(":.")).replace(" ", "")
            if tag.endswith("s") and "chapter" not in tag:      # normalize shortstory(ies)
                tag = tag.rstrip("s")
            title = (m.group(2) or "").strip(" :.")
            # join continuation lines (not section starts, not bare page numbers)
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt or SECTION_RE.match(nxt) or HEADER_NOISE.search(nxt):
                    break
                if re.fullmatch(r"\d{1,4}", nxt):
                    break
                title = (title + " " + nxt).strip()
                j += 1
            if tag not in toc:
                toc[tag] = title
                order.append(tag)
            i = j
    return toc, order


def _clean_heading_line(line):
    line = re.sub(r"\s+", " ", line).strip(" :.")
    return HEADER_NOISE.sub("", line).strip(" :-")


def parse_sections(text, pages):
    toc, _order = _parse_toc(pages)
    total_pages = pages[-1][0] if pages else 0

    # body scan: standalone section markers, skipping TOC pages & running headers
    candidates = []
    for p_num, body in pages:
        low = body.lower()
        if "table of contents" in low or low.strip() == "table of contents":
            continue
        page_hits = []
        for raw in body.splitlines():
            l = raw.strip()
            if not l:
                continue
            # running-header suffixes (｜LegacyEMTLs etc.): keep the heading part
            cut = re.split(r"[｜|]", l, maxsplit=1)[0].strip()
            l = cut if cut else l
            m = SECTION_RE.match(l)
            if not m:
                continue
            # reject mid-sentence hits: heading-like only (short; not a dialogue opener)
            if len(l) > 80 or l[0] in "“\"„'’":
                continue
            # 'Chapter N' standalone or 'Chapter N: Title' / 'Prologue' / 'Prologue: X'
            tag = re.sub(r"\s+", " ", m.group(1).lower().rstrip(":.")).replace(" ", "")
            if tag.endswith("s") and "chapter" not in tag:
                tag = tag.rstrip("s")
            title = (m.group(2) or "").strip(" :.")
            if not title and tag in toc:
                title = toc[tag]
            clean = _clean_heading_line(l)
            page_hits.append((p_num, tag, clean, title))
        # TOC continuation pages list many chapter markers at once — drop whole page
        if len({t for _, t, _, _ in page_hits}) >= 2:
            continue
        candidates.extend(page_hits)

    # dedupe: first occurrence of each tag wins; sort by page
    sections = []
    seen = set()
    for pg, tag, clean, title in candidates:
        if tag in seen:
            continue
        seen.add(tag)
        if title and title.lower() in clean.lower() and clean.lower().startswith(tag.replace("chapter", "chapter")):
            display = clean                      # body line already has title
        elif title:
            display = f"{clean}: {title}" if title.lower() not in clean.lower() else clean
        else:
            display = clean
        sections.append((pg, display))
    sections.sort(key=lambda x: x[0])

    # TOC-title fill-in: locate unfound TOC sections by standalone title lines
    # (translations like y1v11 print the chapter TITLE only, no "CHAPTER N" prefix).
    # Strict matching only: exact full-line equality, or wrapped title (line +
    # following line together equal the TOC title). Never substring-in-prose.
    missing = [tag for tag in toc if tag not in seen]
    if missing:
        last_toc_pg = 8
        extra = []
        used = {pg for pg, _ in sections}
        for tag in missing:
            title = toc.get(tag, "")
            if not title:
                continue
            needle = fold(title)
            for p_num, body in pages:
                if p_num <= last_toc_pg or p_num in used:
                    continue
                lines = [raw.strip() for raw in body.splitlines()]
                for li, raw in enumerate(lines):
                    lf = fold(raw)
                    if not lf or HEADER_NOISE.search(raw):
                        continue
                    exact = lf == needle
                    wrap = False
                    if not exact and len(lf) >= 12 and needle.startswith(lf + " "):
                        for nxt in lines[li + 1:li + 3]:
                            if not nxt or HEADER_NOISE.search(nxt):
                                continue
                            if fold(lf + " " + nxt) == needle:
                                wrap = True
                            break
                    if exact or wrap:
                        extra.append((p_num, f"{tag}: {title}"))
                        used.add(p_num)
                        break
        sections.extend(extra)
        sections.sort(key=lambda x: x[0])

    if not sections:
        step = 25
        results = []
        for s in range(1, total_pages + 1, step):
            e = min(s + step - 1, total_pages)
            results.append((s, e, e - s + 1, f"Section (p.{s}–{e})"))
        return results

    results = []
    for i, (pg, display) in enumerate(sections):
        next_pg = sections[i + 1][0] - 1 if i + 1 < len(sections) else total_pages
        if next_pg < pg:
            next_pg = pg
        results.append((pg, next_pg, next_pg - pg + 1, display))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["vols", "locate", "extract", "chapters"])
    ap.add_argument("--char")
    ap.add_argument("--vol")
    ap.add_argument("--pages", help="e.g. 1-20 or 17")
    args = ap.parse_args()

    vols = vol_files()

    if args.cmd == "vols":
        for k, p in sorted(vols.items()):
            n = len(parse_pages(p))
            print(f"{k}\t{n}\tpages\t{p}")
        return

    if not args.vol:
        sys.exit("--vol required for this command")
    vol_key = args.vol.replace(".", "")  # canonical ids are dotted (y1v4.5); disk keys are not (y1v45)
    if vol_key == "y0":
        vol_key = "v0"  # disk key for Volume 0
    if vol_key not in vols:
        sys.exit(f"unknown vol key {args.vol!r}; try: {', '.join(sorted(vols))}")
    vol_path = vols[vol_key]
    pages = parse_pages(vol_path)

    if args.cmd == "chapters":
        text = open(vol_path, encoding="utf-8").read()
        secs = parse_sections(text, pages)
        bad = sum(1 for s, e, c, _ in secs if c <= 0)
        print(f"=== {vol_key} ({len(pages)} pages, {len(secs)} sections, bad={bad}) ===")
        for s, e, count, title in secs:
            print(f"  p.{s:3d}–{e:3d} ({count:3d} pp)  {title}")
        return

    if args.cmd == "locate":
        if not args.char:
            sys.exit("--char required")
        pats = alias_patterns(args.char)
        hits = page_hits(pages, pats)
        cl = cluster(hits)
        total_lines = sum(h[1] for h in hits)
        print(f"patterns({len(pats)}): {', '.join(pats)}")
        print(f"pages with hits: {len(hits)} / {len(pages)}; hit-lines: {total_lines}")
        print("clusters (start-end hit-lines):")
        for a, b, n in cl:
            span = f"p.{a}" if a == b else f"p.{a}-{b}"
            print(f"  {span}\t{n}")
        return

    if args.cmd == "extract":
        if not args.pages:
            sys.exit("--pages required")
        if "-" in args.pages:
            a, b = args.pages.split("-")
            lo, hi = int(a), int(b)
        else:
            lo = hi = int(args.pages)
        for num, body in pages:
            if lo <= num <= hi:
                print(f"--- page {num} ---")
                print(body)
                print()


if __name__ == "__main__":
    main()

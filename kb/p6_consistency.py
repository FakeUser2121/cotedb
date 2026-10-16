"""P6-6 chronology / relationship consistency gate (read-only).

python3 kb/p6_consistency.py

Checks the authored and derived tables against the corpus:
  status_timeline - unique (char, vol), vol chronology non-decreasing
                     per char, evidence_refs resolvable to an actual
                     quote/claim page
  relations        - chars exist, rel_type ASCII token, valid_from_vol
                     <= valid_to_vol, no evidence predating valid_from
  interpretations  - char exists, confidence in (0, 1], basis_refs
                     resolvable
  events           - vol exists, confidence in [0, 1], span_start inside
                     its own pdf_page, span_end on some page of the same
                     volume at/after pdf_page (scenes deliberately cross
                     page breaks: event_build clusters volume-wide with
                     GAP_MAX=400, page breaks are layout)
  quotes           - attributed quotes reference existing chars and
                     carry a confidence value

Exit 0 = all clean; exit 1 = violations (printed one per line).
"""

import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402

REF = re.compile(r"^(?P<vol>[a-z0-9.]+) p\.(?P<page>\d+)$")


def load_pages():
    max_page = {}
    page_counts = {}
    for vol, _stem, page, _pstart, _ptext in iter_pages():
        max_page[vol] = page
        page_counts[vol] = page_counts.get(vol, 0) + 1
    return max_page


def ref_pages(refs_json, where, out, max_page, has_content):
    try:
        refs = json.loads(refs_json or "[]")
    except (ValueError, TypeError):
        out.append(f"{where}: unparseable refs {refs_json!r}")
        return
    for ref in refs:
        m = REF.match(ref.strip())
        if not m:
            out.append(f"{where}: bad ref format {ref!r}")
            continue
        vol, page = m.group("vol"), int(m.group("page"))
        if vol not in max_page:
            out.append(f"{where}: unknown vol {vol!r}")
        elif page > max_page[vol]:
            out.append(f"{where}: page {vol} p.{page} > {max_page[vol]}")
        elif not has_content(vol, page):
            out.append(f"{where}: no quote/claim at {vol} p.{page}")


def main():
    con = sqlite3.connect(DB_PATH)
    max_page = load_pages()
    vol_order = {v: i for i, (v,) in enumerate(
        con.execute("SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    content = set()
    for vol, pg in con.execute(
            "SELECT DISTINCT vol_id, pdf_page FROM quotes"):
        content.add((vol, pg))
    for vol, pg in con.execute(
            "SELECT DISTINCT vol_id, pdf_page FROM claims"):
        content.add((vol, pg))
    has_content = lambda vol, pg: (vol, pg) in content  # noqa: E731
    out = []

    # status_timeline
    seen = set()
    last_order = {}
    for cid, vol, refs in con.execute(
            "SELECT char_id, vol_id, evidence_refs FROM status_timeline"):
        key = (cid, vol)
        if key in seen:
            out.append(f"status_timeline: duplicate {key}")
        seen.add(key)
        if vol not in vol_order:
            out.append(f"status_timeline: unknown vol {vol} ({cid})")
            continue
        if vol in last_order and vol_order[vol] < last_order[cid]:
            out.append(
                f"status_timeline: {cid} goes back {last_order[cid]} "
                f"-> {vol_order[vol]} at {vol}")
        last_order[cid] = vol_order[vol]
        ref_pages(refs, f"status_timeline {cid} {vol}", out, max_page,
                  has_content)

    # relations
    chars = {r for r, in con.execute("SELECT char_id FROM characters")}
    for rel_id, a, b, rtype, note, vfrom, vto, refs in con.execute(
            "SELECT rel_id, char_a, char_b, rel_type, direction_note, "
            "valid_from_vol, valid_to_vol, evidence_refs FROM relations"):
        where = f"relations {rel_id} {a}/{b}"
        if a not in chars or b not in chars:
            out.append(f"{where}: unknown char")
        if a == b:
            out.append(f"{where}: self relation")
        if not re.fullmatch(r"[a-z0-9-]+", rtype or ""):
            out.append(f"{where}: rel_type {rtype!r} not ASCII token")
        if not (note or "").strip():
            out.append(f"{where}: empty direction_note")
        if vfrom not in vol_order:
            out.append(f"{where}: unknown valid_from_vol {vfrom!r}")
        if vto is not None and vto not in vol_order:
            out.append(f"{where}: unknown valid_to_vol {vto!r}")
        if (vfrom in vol_order and vto in vol_order
                and vol_order[vfrom] > vol_order[vto]):
            out.append(f"{where}: valid_from {vfrom} after {vto}")
        try:
            refs_list = json.loads(refs or "[]")
        except (ValueError, TypeError):
            out.append(f"{where}: unparseable refs {refs!r}")
            refs_list = []
        ev_vols = []
        for ref in refs_list:
            m = REF.match(ref.strip()) if isinstance(ref, str) else None
            if m and m.group("vol") in vol_order:
                ev_vols.append(vol_order[m.group("vol")])
        if ev_vols and vfrom in vol_order:
            if min(ev_vols) < vol_order[vfrom]:
                out.append(
                    f"{where}: evidence before valid_from "
                    f"({vfrom})")
        ref_pages(refs, where, out, max_page, has_content)

    # interpretations
    for iid, cid, refs, conf in con.execute(
            "SELECT interp_id, char_id, basis_refs, confidence "
            "FROM interpretations"):
        where = f"interpretations {iid} {cid}"
        if cid not in chars:
            out.append(f"{where}: unknown char")
        if conf is None or not (0 < conf <= 1):
            out.append(f"{where}: confidence {conf!r}")
        ref_pages(refs, where, out, max_page, has_content)

    # events
    for eid, vol, pg, s, e, conf in con.execute(
            "SELECT event_id, vol_id, pdf_page, span_start, span_end, "
            "confidence FROM events"):
        where = f"events {eid}"
        if vol not in vol_order:
            out.append(f"{where}: unknown vol {vol}")
        if conf is None or not (0 <= conf <= 1):
            out.append(f"{where}: confidence {conf!r}")
        if s is None or e is None or s < 0 or e < s:
            out.append(f"{where}: bad span {s},{e}")
    page_bounds = {}
    vol_pages = defaultdict(list)
    for vol, _stem, page, pstart, ptext in iter_pages():
        page_bounds[(vol, page)] = (pstart, pstart + len(ptext))
        vol_pages[vol].append((page, pstart, pstart + len(ptext)))
    for pages in vol_pages.values():
        pages.sort()
    for eid, vol, pg, s, e in con.execute(
            "SELECT event_id, vol_id, pdf_page, span_start, span_end "
            "FROM events"):
        bounds = page_bounds.get((vol, pg))
        if bounds is None:
            continue
        if not bounds[0] <= s <= bounds[1]:
            out.append(
                f"events {eid}: span_start {s} outside "
                f"{vol} p.{pg} bounds {bounds}")
        if e < s:
            out.append(f"events {eid}: span_end {e} before start {s}")
            continue
        if not any(p >= pg and lo <= e <= hi
                   for p, lo, hi in vol_pages.get(vol, [])):
            out.append(
                f"events {eid}: span_end {e} not on any page of "
                f"{vol} at/after p.{pg}")

    # quotes: attributed => char exists + confidence set
    for qid, cid, conf in con.execute(
            "SELECT quote_id, char_id, attribution_confidence "
            "FROM quotes WHERE char_id IS NOT NULL"):
        if cid not in chars:
            out.append(f"quotes {qid}: unknown char {cid}")
        if conf is None:
            out.append(f"quotes {qid}: attributed without confidence")

    con.close()
    if out:
        print(f"p6_consistency: {len(out)} violation(s)")
        for line in out:
            print("  ", line)
        return 1
    print("p6_consistency: all checks clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

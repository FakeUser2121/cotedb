#!/usr/bin/env python3
"""P8-6 locations consistency gate (read-only).

python3 kb/p8_consistency.py

Checks the locations layer end to end:
  locations        kind in the documented set · function/notes
                   authored (non-empty) · first/last_vol exist and
                   match the chronological min/max of own mentions
  location_aliases every raw/normalized form maps to an existing
                   loc and is globally unique (one form, one entity);
                   form_type in {full, short, variant, epithet}
  location_mentions loc/vol exist · span inside its page bounds
                   (absolute offsets, same check as events) ·
                   provenance recorded
  location_claims  loc exists · kind valid · confidence in (0, 1] ·
                   refs are real pages and >=1 ref carries a mention
                   of this location · evidence_quote verbatim (exact
                   substring of the anchor page's raw text)
  locations_fts    one row per location
  dossiers/world   one .md per location + index.md on disk

Exit 0 = clean; exit 1 = violations (printed one per line).
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402

KINDS = {"campus-building", "campus-zone", "dorm", "exam-venue",
         "off-site", "city", "other"}
FORM_TYPES = {"full", "short", "variant", "epithet"}
KIND_CLAIMS = {"narrator_fact", "character_claim", "other_reported",
               "inference"}
WORLD = Path(__file__).resolve().parent.parent / "dossiers" / "world"

REF_VOLS = None


def main():
    global REF_VOLS
    con = sqlite3.connect(DB_PATH)
    out = []

    vols = {v for v, in con.execute("SELECT vol_id FROM volumes")}
    mentions = {}  # (loc, vol, page) -> [(s, e)]
    for loc, vol, page, s, e in con.execute(
            "SELECT loc_id, vol_id, pdf_page, span_start, span_end "
            "FROM location_mentions"):
        mentions.setdefault((loc, vol, page), []).append((s, e))
    pages = {}
    for vol, _stem, page, pstart, ptext in iter_pages():
        pages[(vol, page)] = (pstart, ptext)

    # locations
    chrono = {v: i for i, (v,) in enumerate(
        con.execute("SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    for loc_id, kind, func, notes, first, last in con.execute(
            "SELECT loc_id, kind, function, notes, first_vol, last_vol "
            "FROM locations"):
        where = f"locations {loc_id}"
        if kind not in KINDS:
            out.append(f"{where}: kind {kind!r} not in set")
        if not (func or "").strip() or not (notes or "").strip():
            out.append(f"{where}: function/notes not authored")
        if first is not None and first not in vols:
            out.append(f"{where}: first_vol {first!r} unknown")
        if last is not None and last not in vols:
            out.append(f"{where}: last_vol {last!r} unknown")
        vols_here = [k[1] for k in mentions if k[0] == loc_id]
        if vols_here:
            exp_first = min(vols_here, key=lambda v: chrono[v])
            exp_last = max(vols_here, key=lambda v: chrono[v])
            if first != exp_first or last != exp_last:
                out.append(
                    f"{where}: footprint {first}->{last} != "
                    f"{exp_first}->{exp_last} (mentions)")

    # location_aliases
    form_owner = {}
    for alias_id, loc_id, raw, norm, ftype in con.execute(
            "SELECT alias_id, loc_id, raw_form, normalized, form_type "
            "FROM location_aliases ORDER BY alias_id"):
        where = f"location_aliases {raw!r}"
        if loc_id not in {r for r, in
                          con.execute("SELECT loc_id FROM locations")}:
            out.append(f"{where}: orphan loc {loc_id}")
        if ftype not in FORM_TYPES:
            out.append(f"{where}: form_type {ftype!r}")
        for key in (raw, norm):
            if key in form_owner and form_owner[key] != loc_id:
                out.append(
                    f"{where}: form shared with {form_owner[key]}")
            form_owner[key] = loc_id

    # location_mentions
    for loc, vol, page, s, e, prov in con.execute(
            "SELECT loc_id, vol_id, pdf_page, span_start, span_end, "
            "provenance FROM location_mentions"):
        where = f"location_mentions {loc} {vol} p.{page}"
        if vol not in vols:
            out.append(f"{where}: unknown vol")
        bounds = pages.get((vol, page))
        if bounds is None:
            out.append(f"{where}: unknown page")
            continue
        pstart, text = bounds
        ls, le = s - pstart, e - pstart
        if ls < 0 or le < ls or le > len(text):
            out.append(f"{where}: span {s}-{e} outside page bounds "
                       f"(local {ls}-{le} vs len {len(text)})")
        if prov != "p8_mentions":
            out.append(f"{where}: provenance {prov!r}")

    # location_claims: refs must be real pages, >=1 ref must carry a
    # mention of this location; evidence_quote is checked ONLY against
    # the claim's own anchor page (vol_id/pdf_page = first ref).
    for cid, loc, kind, conf, refs_json, eq, evol, epage in con.execute(
            "SELECT claim_id, loc_id, kind, confidence, "
            "corroboration_refs, evidence_quote, vol_id, pdf_page "
            "FROM location_claims"):
        where = f"location_claims {cid} ({loc})"
        if kind not in KIND_CLAIMS:
            out.append(f"{where}: kind {kind!r}")
        if conf is None or not (0 < conf <= 1):
            out.append(f"{where}: confidence {conf!r}")
        if not (eq or "").strip():
            out.append(f"{where}: empty evidence_quote")
        try:
            refs = json.loads(refs_json or "[]")
        except ValueError:
            out.append(f"{where}: unparseable refs")
            continue
        anchored = 0
        for ref in refs:
            vol_pg = ref.split(" p.")
            if len(vol_pg) != 2 or not vol_pg[1].isdigit():
                out.append(f"{where}: bad ref {ref!r}")
                continue
            vol, page = vol_pg[0], int(vol_pg[1])
            if (vol, page) not in pages:
                out.append(f"{where}: ref {ref!r} not a real page")
                continue
            if (loc, vol, page) in mentions:
                anchored += 1
        if refs and anchored == 0:
            out.append(f"{where}: no ref carries a mention "
                       f"of this location")
        text = pages.get((evol, epage), (0, ""))[1]
        if eq and text and eq not in text:
            out.append(f"{where}: evidence_quote not verbatim at "
                       f"anchor {evol} p.{epage}")

    # fts + dossier files
    n_locs = con.execute("SELECT count(*) FROM locations").fetchone()[0]
    n_fts = con.execute("SELECT count(*) FROM locations_fts").fetchone()[0]
    if n_fts != n_locs:
        out.append(f"locations_fts: {n_fts} rows != {n_locs} locations")
    for loc_id, in con.execute("SELECT loc_id FROM locations"):
        if not (WORLD / f"{loc_id}.md").exists():
            out.append(f"dossiers/world: missing {loc_id}.md")
    if not (WORLD / "index.md").exists():
        out.append("dossiers/world: missing index.md")
    con.close()

    if out:
        print(f"p8_consistency: {len(out)} violation(s)")
        for line in out:
            print("  ", line)
        return 1
    print("p8_consistency: all checks clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

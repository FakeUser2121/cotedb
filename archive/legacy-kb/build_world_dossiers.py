#!/usr/bin/env python3
"""P8-5: world/location dossier views (generated, idempotent).

python3 kb/build_world_dossiers.py

Writes dossiers/world/<loc_id>.md for every location plus
dossiers/world/index.md. Pure generated views — never hand-edit;
prose lives in kb/location_analysis.py, identity in kb/p8_import.py.

Per dossier: function · notes (layout, narrative importance, changes
over time) · footprint (per-vol anchored mentions) · scene partners
(characters speaking in dialogue events co-paged with this location's
mentions — vol+page join; span-overlap is too strict because dialogue
rarely contains the location's literal words) · claims with verbatim
evidence · evidence anchors.

Deterministic: every list sorted (chrono / count desc then id), no
timestamps — two consecutive runs must be md5-identical.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dossiers" / "world"

def one(con, loc, chrono_idx):
    loc_id, name, kind, func, notes, first, last = loc
    total = con.execute(
        "SELECT count(*) FROM location_mentions WHERE loc_id=?",
        (loc_id,)).fetchone()[0]
    by_vol = con.execute(
        "SELECT vol_id, count(*) FROM location_mentions WHERE loc_id=? "
        "GROUP BY vol_id ORDER BY vol_id", (loc_id,)).fetchall()
    by_vol.sort(key=lambda r: chrono_idx[r[0]])
    vols = [v for v, _c in by_vol]

    partners = con.execute(
        "SELECT ep.char_id, c.canonical_name, "
        "count(DISTINCT ep.event_id) AS scenes "
        "FROM location_mentions m "
        "JOIN events e ON e.vol_id = m.vol_id "
        "  AND e.pdf_page = m.pdf_page "
        "JOIN event_participants ep ON ep.event_id = e.event_id "
        "JOIN characters c ON c.char_id = ep.char_id "
        "WHERE m.loc_id = ? "
        "GROUP BY ep.char_id, c.canonical_name "
        "ORDER BY scenes DESC, ep.char_id",
        (loc_id,)).fetchall()
    scenes = con.execute(
        "SELECT count(DISTINCT e.event_id) "
        "FROM location_mentions m "
        "JOIN events e ON e.vol_id = m.vol_id "
        "  AND e.pdf_page = m.pdf_page "
        "WHERE m.loc_id = ?", (loc_id,)).fetchone()[0]

    claims = con.execute(
        "SELECT claim, kind, claimant, confidence, vol_id, pdf_page, "
        "evidence_quote, corroboration_refs "
        "FROM location_claims WHERE loc_id=? ORDER BY claim_id",
        (loc_id,)).fetchall()

    anchors = con.execute(
        "SELECT vol_id, pdf_page FROM location_mentions WHERE loc_id=? "
        "ORDER BY vol_id, pdf_page LIMIT 8", (loc_id,)).fetchall()

    L = []
    L.append(f"# {name}\n")
    L.append(f"**{kind}**\n")
    L.append(f"`{total} mentions · {len(vols)} vols · "
             f"{scenes} co-paged scenes · {len(claims)} claims`\n")
    L.append("## Function\n")
    L.append(f"{func}\n")
    L.append("## Notes\n")
    L.append(f"{notes}\n")
    L.append("## Footprint\n")
    L.append(f"- **Span:** {first or '-'} → {last or '-'}")
    L.append("- **Anchored mentions by vol:** "
             + ", ".join(f"{v} ×{c}" for v, c in by_vol))
    L.append("")
    if partners:
        L.append("## Scene partners (co-paged dialogue)")
        L.append("")
        L.append(", ".join(f"{n} ({c})" for _cid, n, c in partners[:12])
                 + (f" (+{len(partners) - 12} more)"
                    if len(partners) > 12 else ""))
        L.append("")
    if claims:
        L.append("## Claims")
        L.append("")
        for claim, kind_c, claimant, conf, vol, page, eq, refs in claims:
            who = claimant or "unattributed"
            L.append(f"- “{claim}” ({vol} p.{page}) — {kind_c}, "
                     f"{who}, conf {conf}")
            L.append(f"  - evidence: “{eq}”")
        L.append("")
    if anchors:
        L.append("## Evidence anchors")
        L.append("")
        L.append(", ".join(f"{v} p.{p}" for v, p in anchors))
        L.append("")
    return "\n".join(L)


def index(con, chrono_idx):
    rows = con.execute(
        "SELECT loc_id, name, kind, first_vol, last_vol FROM locations "
        "ORDER BY kind, loc_id").fetchall()
    counts = dict(con.execute(
        "SELECT loc_id, count(*) FROM location_mentions "
        "GROUP BY loc_id").fetchall())
    claims_n = dict(con.execute(
        "SELECT loc_id, count(*) FROM location_claims "
        "GROUP BY loc_id").fetchall())
    L = ["# All Locations\n",
         f"{len(rows)} locations — layout, narrative role, and the "
         f"scenes that happen there\n"]
    kind = None
    for loc_id, name, k, first, last in rows:
        if k != kind:
            kind = k
            L.append(f"## {kind}\n")
        L.append(f"- [{name}]({loc_id}.md) — "
                 f"{counts.get(loc_id, 0)} mentions · "
                 f"{first or '-'}→{last or '-'} · "
                 f"{claims_n.get(loc_id, 0)} claims")
    L.append("")
    return "\n".join(L)


def main():
    con = sqlite3.connect(DB_PATH)
    chrono_idx = {v: i for i, (v,) in enumerate(
        con.execute("SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    locs = con.execute(
        "SELECT loc_id, name, kind, function, notes, first_vol, "
        "last_vol FROM locations ORDER BY loc_id").fetchall()
    OUT.mkdir(parents=True, exist_ok=True)
    written = 0
    for loc in locs:
        (OUT / f"{loc[0]}.md").write_text(one(con, loc, chrono_idx))
        written += 1
    (OUT / "index.md").write_text(index(con, chrono_idx))
    con.close()
    print(f"build_world_dossiers: {written} location dossiers + index")
    return 0


if __name__ == "__main__":
    sys.exit(main())

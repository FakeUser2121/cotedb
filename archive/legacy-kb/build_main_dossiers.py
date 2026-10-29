"""P5: main-character dossiers — one file per tier-1 char.

python3 kb/build_main_dossiers.py [--pack CHAR_ID] [--limit N]

Renders dossiers/main/<char_id>.md from the DB: identity, footprint,
per-volume arc timeline, recurring scene partners, claims, a
volume-grouped quote bank (<=4 per active vol, <=60 total), plus the
authored sections seeded by `kb/author_main.py` from
`kb/main_analysis.py`:
  status_timeline   -> ## Arc        (per-vol situation/knowledge/why)
  interpretations   -> ## Psychology (competing readings; basis_refs
                       resolved to human anchors)
  relations         -> ## Relationships
basis_refs convention (JSON list): "q<quote_id>" -> quote anchor,
"claim<claim_id>" -> claim text, anything else passes through as a
plain anchor like "y1v4 p.93".
--pack CHAR_ID prints the authoring evidence pack (quotes grouped by
volume, partners, claims, timeline, gaps) to stdout instead.
Deterministic; regenerate from DB, never hand-edit.
"""
import argparse
import json
import os
import sqlite3

from mention_build import canon
from roster_mine import DB_PATH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bank(db, cid, per_vol=4, cap=60):
    rows = db.execute(
        "SELECT q.text_verbatim, q.vol_id, v.chrono_order, q.pdf_page "
        "FROM quotes q JOIN volumes v ON v.vol_id=q.vol_id "
        "WHERE q.char_id=? ORDER BY v.chrono_order, q.pdf_page, q.span_start",
        (cid,)).fetchall()
    picked, per = [], {}
    for text, vol, _c, page in rows:
        if len(picked) >= cap:
            break
        if per.get(vol, 0) >= per_vol:
            continue
        per[vol] = per.get(vol, 0) + 1
        picked.append((text, vol, page))
    return picked


def resolve_refs(db, refs):
    out = []
    for r in refs:
        if r.startswith("q") and r[1:].isdigit():
            row = db.execute(
                "SELECT text_verbatim, vol_id, pdf_page FROM quotes "
                "WHERE quote_id=?", (int(r[1:]),)).fetchone()
            if row:
                text, vol, page = row
                frag = text if len(text) <= 200 else text[:197] + "…"
                out.append(f"“{frag}” ({vol} p.{page})")
            else:
                out.append(f"quote {r[1:]} (missing)")
        elif r.startswith("claim") and r[5:].isdigit():
            row = db.execute(
                "SELECT claim, vol_id, pdf_page FROM claims "
                "WHERE claim_id=?", (int(r[5:]),)).fetchone()
            if row:
                claim, vol, page = row
                out.append(f"“{claim}” ({vol} p.{page})")
            else:
                out.append(f"claim {r[5:]} (missing)")
        else:
            out.append(r)
    return out


def partners(db, cid, limit=12):
    return db.execute(
        "SELECT p2.char_id, c.canonical_name, COUNT(*) AS n "
        "FROM event_participants p1 "
        "JOIN event_participants p2 ON p2.event_id=p1.event_id "
        "AND p2.char_id<>p1.char_id "
        "JOIN characters c ON c.char_id=p2.char_id "
        "WHERE p1.char_id=? GROUP BY p2.char_id "
        "ORDER BY n DESC, c.canonical_name LIMIT ?",
        (cid, limit)).fetchall()


def timeline(db, cid):
    return db.execute(
        "SELECT e.vol_id, COUNT(DISTINCT e.event_id) AS n "
        "FROM event_participants p JOIN events e ON e.event_id=p.event_id "
        "JOIN volumes v ON v.vol_id=e.vol_id "
        "WHERE p.char_id=? GROUP BY e.vol_id ORDER BY v.chrono_order",
        (cid,)).fetchall()


def footprint(db, cid):
    aliases = [r[0] for r in db.execute(
        "SELECT raw_form FROM aliases WHERE char_id=? AND is_noise=0",
        (cid,))]
    cn = sorted({canon(a) for a in aliases})
    fp = []
    if cn:
        qs = ",".join("?" * len(cn))
        fp = db.execute(
            "SELECT m.vol_id, SUM(m.count) FROM mention_stats m "
            "JOIN volumes v ON v.vol_id=m.vol_id "
            f"WHERE m.token IN ({qs}) GROUP BY m.vol_id "
            "ORDER BY SUM(m.count) DESC, v.chrono_order", cn).fetchall()
    return aliases, fp


def render(db, cid):
    (name, notes,) = db.execute(
        "SELECT canonical_name, notes FROM characters "
        "WHERE char_id=?", (cid,)).fetchone()
    aliases, fp = footprint(db, cid)
    cov = db.execute(
        "SELECT c.vol_id, c.status FROM coverage c "
        "JOIN volumes v ON v.vol_id=c.vol_id WHERE c.char_id=? "
        "ORDER BY v.chrono_order", (cid,)).fetchall()
    spoken = [v for v, s in cov if s == "quotes"]
    gaps = [v for v, s in cov if s == "occurrences"]
    scenes = db.execute(
        "SELECT COUNT(*) FROM event_participants WHERE char_id=?",
        (cid,)).fetchone()[0]
    qcount = db.execute("SELECT COUNT(*) FROM quotes WHERE char_id=?",
                        (cid,)).fetchone()[0]
    lines = [
        f"# {name}",
        "",
        "**Main character**",
        "",
        f"`{sum(n for _v, n in fp):,} mentions · "
        f"{qcount:,} attributed lines · {scenes} scenes`",
        "",
        "## Identity",
        "",
    ]
    if aliases:
        shown = ", ".join(aliases[:14])
        extra = f" (+{len(aliases)-14} more)" if len(aliases) > 14 else ""
        lines.append(f"- **Aliases:** {shown}{extra}")
    if notes and notes.strip() not in ("KNOWN curated", "KNOWN", "seed",
                                       "curated"):
        lines.append(f"- **Notes:** {notes}")
    lines += ["", "## Footprint", ""]
    if spoken:
        lines.append(f"- **Spoken in ({len(spoken)} vols):** "
                     f"{', '.join(spoken)}")
    if gaps:
        lines.append(f"- **Gap queue (mentioned, no attributed line):** "
                     f"{', '.join(gaps)}")
    if fp:
        top = ", ".join(f"{v} ×{n}" for v, n in fp[:10])
        more = f" (+{len(fp)-10} more vols)" if len(fp) > 10 else ""
        lines.append(f"- **Top mentions:** {top}{more}")
    tl = timeline(db, cid)
    if tl:
        lines.append("- **Arc timeline (scenes per vol):** " +
                     ", ".join(f"{v} ×{n}" for v, n in tl))
    arcs = db.execute(
        "SELECT vol_id, situation, knowledge_state, changes, why, "
        "evidence_refs FROM status_timeline WHERE char_id=? "
        "ORDER BY (SELECT chrono_order FROM volumes "
        "WHERE vol_id=status_timeline.vol_id)", (cid,)).fetchall()
    if arcs:
        lines += ["", "## Arc", ""]
        for vol, sit, ks, chg, why, refs in arcs:
            lines.append(f"### {vol}")
            lines.append("")
            if sit:
                lines.append(f"- **Situation:** {sit}")
            if ks:
                lines.append(f"- **Knowledge state:** {ks}")
            if chg:
                lines.append(f"- **Changes:** {chg}")
            if why:
                lines.append(f"- **Why it matters:** {why}")
            if refs:
                rr = resolve_refs(db, json.loads(refs))
                lines.append(f"- **Evidence:** {' · '.join(rr)}")
            lines.append("")
    interps = db.execute(
        "SELECT claim, basis_refs, confidence, notes FROM interpretations "
        "WHERE char_id=? ORDER BY confidence DESC, claim", (cid,)).fetchall()
    if interps:
        lines += ["## Psychology & competing readings", ""]
        for claim, basis, conf, notes2 in interps:
            lines.append(f"- **{claim}** (confidence {conf})")
            if basis:
                rr = resolve_refs(db, json.loads(basis))
                lines.append(f"  - Evidence: {' · '.join(rr)}")
            if notes2:
                lines.append(f"  - Reading: {notes2}")
        lines.append("")
    rels = db.execute(
        "SELECT char_b, rel_type, direction_note, valid_from_vol, "
        "valid_to_vol, evidence_refs FROM relations "
        "WHERE char_a=? ORDER BY rel_type, char_b", (cid,)).fetchall()
    if rels:
        lines += ["## Relationships", ""]
        for cb, rt, dn, vf, vt, refs in rels:
            cb_name = db.execute(
                "SELECT canonical_name FROM characters WHERE char_id=?",
                (cb,)).fetchone()
            cb_name = cb_name[0] if cb_name else cb
            span = ""
            if vf and vt:
                span = f" [{vf}→{vt}]"
            elif vf:
                span = f" [from {vf}]"
            elif vt:
                span = f" [until {vt}]"
            row = f"- **{cb_name}** — {rt}{span}"
            if dn:
                row += f": {dn}"
            lines.append(row)
            if refs:
                rr = resolve_refs(db, json.loads(refs))
                lines.append(f"  - Evidence: {' · '.join(rr)}")
        lines.append("")
    pt = partners(db, cid)
    if pt:
        lines += ["## Recurring scene partners", "",
                  ", ".join(f"{nm} ({n})" for _c, nm, n in pt), ""]
    claims = db.execute(
        "SELECT c.claim, c.vol_id, c.pdf_page FROM claims c "
        "JOIN volumes v ON v.vol_id=c.vol_id WHERE c.char_id=? "
        "ORDER BY v.chrono_order, c.pdf_page LIMIT 10", (cid,)).fetchall()
    if claims:
        lines += ["## Claims", ""]
        for claim, vol, page in claims:
            lines.append(f"- “{claim}” ({vol} p.{page})")
        lines.append("")
    qrows = bank(db, cid)
    if qrows:
        lines += ["## Quote bank", ""]
        cur = None
        for text, vol, page in qrows:
            if vol != cur:
                lines.append(f"**{vol}**")
                lines.append("")
                cur = vol
            text = " ".join(text.split())
            frag = text if len(text) <= 300 else text[:297] + "…"
            lines.append(f"- “{frag}” (p.{page})")
        lines.append("")
    return "\n".join(lines)


def pack(db, cid):
    name, = db.execute(
        "SELECT canonical_name FROM characters WHERE char_id=?",
        (cid,)).fetchone()[0:1]
    print(f"EVIDENCE PACK — {name} ({cid})")
    aliases, fp = footprint(db, cid)
    print("aliases:", ", ".join(aliases))
    print("mentions:", ", ".join(f"{v} ×{n}" for v, n in fp))
    print("timeline:", ", ".join(f"{v} ×{n}" for v, n in timeline(db, cid)))
    print("partners:", ", ".join(
        f"{nm}({n})" for _c, nm, n in partners(db, cid)))
    print("gaps:", ", ".join(
        v for v, s in db.execute(
            "SELECT c.vol_id, c.status FROM coverage c "
            "JOIN volumes v ON v.vol_id=c.vol_id WHERE c.char_id=? "
            "ORDER BY v.chrono_order", (cid,)) if s == "occurrences"))
    print("\nCLAIMS:")
    for claim, vol, page in db.execute(
            "SELECT c.claim, c.vol_id, c.pdf_page FROM claims c "
            "JOIN volumes v ON v.vol_id=c.vol_id WHERE c.char_id=? "
            "ORDER BY v.chrono_order, c.pdf_page", (cid,)):
        print(f"  ({vol} p.{page}) {claim}")
    print("\nQUOTES BY VOL:")
    rows = db.execute(
        "SELECT q.text_verbatim, q.vol_id, v.chrono_order, q.pdf_page "
        "FROM quotes q JOIN volumes v ON v.vol_id=q.vol_id "
        "WHERE q.char_id=? ORDER BY v.chrono_order, q.pdf_page",
        (cid,)).fetchall()
    cur = None
    for text, vol, _c, page in rows:
        if vol != cur:
            print(f"\n[{vol}]")
            cur = vol
        frag = text if len(text) <= 240 else text[:237] + "…"
        print(f"  p.{page} {frag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", metavar="CHAR_ID")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out-root", default=os.path.join(ROOT, "dossiers",
                                                       "main"))
    args = ap.parse_args()
    db = sqlite3.connect(DB_PATH)
    if args.pack:
        pack(db, args.pack)
        db.close()
        return
    chars = db.execute(
        "SELECT char_id, canonical_name FROM characters "
        "WHERE tier=1 AND status<>'merged' ORDER BY canonical_name"
    ).fetchall()
    if args.limit:
        chars = chars[:args.limit]
    n = 0
    for cid, _name in chars:
        os.makedirs(args.out_root, exist_ok=True)
        with open(os.path.join(args.out_root, f"{cid}.md"), "w",
                  encoding="utf-8") as f:
            f.write(render(db, cid))
        n += 1
    idx = ["# Main Characters", "",
           "The main cast of the story — open any name for the full "
           "profile.", ""]
    for cid, name in chars:
        idx.append(f"- [{name}]({cid}.md)")
    idx.append("")
    with open(os.path.join(args.out_root, "index.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(idx))
    print(f"wrote {n} main dossiers + index under {args.out_root}")
    db.close()


if __name__ == "__main__":
    main()

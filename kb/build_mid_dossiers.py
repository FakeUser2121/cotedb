"""P5: mid-character dossiers — one file per tier-2 char in typed folders.

python3 kb/build_mid_dossiers.py

Routes on characters.mid_type (authority|rivals|allies|peers|family|
outside) into dossiers/mid/<type>/<char_id>.md + dossiers/mid/index.md.
Mid sections are richer than background: recurring scene partners
(co-participant counts from event_participants), per-volume arc
timeline, claims, and a 14-quote bank spread across the char's volume
range. Deterministic; regenerate from DB, never hand-edit.
"""
import argparse
import os
import sqlite3

from build_background import batch_evidence, quotes_for
from mention_build import canon
from roster_mine import DB_PATH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPES = ["authority", "rivals", "allies", "peers", "family", "outside"]


def partners(db, cid, limit=10):
    return db.execute(
        "SELECT p2.char_id, c.canonical_name, COUNT(*) AS n "
        "FROM event_participants p1 "
        "JOIN event_participants p2 ON p2.event_id=p1.event_id "
        "AND p2.char_id<>p1.char_id "
        "JOIN characters c ON c.char_id=p2.char_id "
        "WHERE p1.char_id=? GROUP BY p2.char_id "
        "ORDER BY n DESC, c.canonical_name LIMIT ?", (cid, limit)).fetchall()


def timeline(db, cid):
    return db.execute(
        "SELECT e.vol_id, COUNT(DISTINCT e.event_id) AS n "
        "FROM event_participants p JOIN events e ON e.event_id=p.event_id "
        "JOIN volumes v ON v.vol_id=e.vol_id "
        "WHERE p.char_id=? GROUP BY e.vol_id "
        "ORDER BY v.chrono_order", (cid,)).fetchall()


def mentions_footprint(db, aliases):
    cn = sorted({canon(a) for a in aliases})
    if not cn:
        return []
    qs = ",".join("?" * len(cn))
    return db.execute(
        "SELECT m.vol_id, SUM(m.count) FROM mention_stats m "
        "JOIN volumes v ON v.vol_id=m.vol_id "
        f"WHERE m.token IN ({qs}) GROUP BY m.vol_id "
        "ORDER BY SUM(m.count) DESC, v.chrono_order", cn).fetchall()


def render(db, cid, name, mtype, notes, mention_total, ev):
    qrows = quotes_for(db, cid, limit=14)
    claims = db.execute(
        "SELECT c.claim, c.vol_id, c.pdf_page FROM claims c "
        "JOIN volumes v ON v.vol_id=c.vol_id WHERE c.char_id=? "
        "ORDER BY v.chrono_order, c.pdf_page LIMIT 8", (cid,)).fetchall()
    cov = db.execute(
        "SELECT c.vol_id, c.status FROM coverage c "
        "JOIN volumes v ON v.vol_id=c.vol_id WHERE c.char_id=? "
        "ORDER BY v.chrono_order", (cid,)).fetchall()
    aliases = [r[0] for r in db.execute(
        "SELECT raw_form FROM aliases WHERE char_id=? AND is_noise=0 "
        "ORDER BY form_type, raw_form", (cid,))]
    scenes = db.execute(
        "SELECT COUNT(*) FROM event_participants WHERE char_id=?",
        (cid,)).fetchone()[0]
    spoken = [v for v, s in cov if s == "quotes"]
    gaps = [v for v, s in cov if s == "occurrences"]
    lines = [
        f"# {name}",
        "",
        f"**{mtype}** · tier 2 · generated view (source: `cote_kb.db`; "
        "regenerate with `python3 kb/build_mid_dossiers.py`)",
        "",
        f"`{mention_total} mentions · {len(qrows)} quoted lines · "
        f"{scenes} scenes`",
        "",
        "## Identity",
        "",
        f"- **char_id:** `{cid}`",
    ]
    if aliases:
        shown = ", ".join(aliases[:12])
        extra = f" (+{len(aliases)-12} more)" if len(aliases) > 12 else ""
        lines.append(f"- **Aliases:** {shown}{extra}")
    if notes and notes.strip() not in ("KNOWN curated", "KNOWN", "seed",
                                       "curated"):
        lines.append(f"- **Notes:** {notes}")
    lines += ["", "## Footprint", ""]
    if spoken:
        lines.append(f"- **Spoken in:** {', '.join(spoken)}")
    if gaps:
        lines.append(f"- **Gap queue (mentioned, no attributed line):** "
                     f"{', '.join(gaps)}")
    fp = mentions_footprint(db, aliases)
    if fp:
        top = ", ".join(f"{v} ×{n}" for v, n in fp[:8])
        more = f" (+{len(fp)-8} more vols)" if len(fp) > 8 else ""
        lines.append(f"- **Top mentions:** {top}{more}")
    tl = timeline(db, cid)
    if tl:
        lines.append("- **Arc timeline (scenes per vol):** " +
                     ", ".join(f"{v} ×{n}" for v, n in tl))
    for vol, page, frag in ev:
        lines.append(f"- **Mention evidence:** “{frag}” ({vol} p.{page})")
    pt = partners(db, cid)
    if pt:
        lines += ["", "## Recurring scene partners", ""]
        lines.append(", ".join(f"{nm} ({n})" for _c, nm, n in pt))
    if claims:
        lines += ["", "## Claims", ""]
        for claim, vol, page in claims:
            lines.append(f"- “{claim}” ({vol} p.{page})")
    if qrows:
        lines += ["", "## Quote bank", ""]
        for text, vol, page in qrows:
            frag = text if len(text) <= 260 else text[:257] + "…"
            lines.append(f"- “{frag}” ({vol} p.{page})")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root",
                    default=os.path.join(ROOT, "dossiers", "mid"))
    args = ap.parse_args()
    db = sqlite3.connect(DB_PATH)
    counts = {tok: n for tok, n in db.execute(
        "SELECT token, SUM(count) FROM mention_stats GROUP BY token")}
    mention = {}
    for cid, f in db.execute(
            "SELECT char_id, raw_form FROM aliases WHERE is_noise=0 "
            "AND char_id IS NOT NULL"):
        mention[cid] = mention.get(cid, 0) + counts.get(canon(f), 0)
    chars = db.execute(
        "SELECT char_id, canonical_name, tier, mid_type, notes "
        "FROM characters WHERE tier=2 AND status<>'merged' "
        "ORDER BY canonical_name").fetchall()
    chars = sorted(chars, key=lambda r: (TYPES.index(r[3]) if r[3] in TYPES
                                         else 99, -mention.get(r[0], 0)))
    thin = {cid for (cid,) in db.execute(
        "SELECT c.char_id FROM characters c WHERE c.tier=2 "
        "AND NOT EXISTS (SELECT 1 FROM quotes q WHERE q.char_id=c.char_id)")}
    pending = {cid: [r[0] for r in db.execute(
        "SELECT raw_form FROM aliases WHERE char_id=? AND is_noise=0",
        (cid,))] for cid in thin}
    evmap = batch_evidence(pending) if pending else {}
    n = 0
    for cid, name, tier, mtype, notes in chars:
        mt = mtype or "untyped"
        d = os.path.join(args.out_root, mt)
        os.makedirs(d, exist_ok=True)
        body = render(db, cid, name, mt, notes, mention.get(cid, 0),
                      evmap.get(cid, ()))
        with open(os.path.join(d, f"{cid}.md"), "w",
                  encoding="utf-8") as f:
            f.write(body)
        n += 1
    idx = ["# Mid Characters", "",
           "Generated index — regenerate with "
           "`python3 kb/build_mid_dossiers.py`.", ""]
    for mt in TYPES:
        rows = [c for c in chars if c[3] == mt]
        if not rows:
            continue
        idx.append(f"## {mt} ({len(rows)})")
        idx.append("")
        for cid, name, _t, _m, _n in sorted(
                rows, key=lambda r: -mention.get(r[0], 0)):
            idx.append(f"- [{name}]({mt}/{cid}.md)")
        idx.append("")
    with open(os.path.join(args.out_root, "index.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(idx))
    print(f"wrote {n} mid dossiers + index under {args.out_root}")
    db.close()


if __name__ == "__main__":
    main()

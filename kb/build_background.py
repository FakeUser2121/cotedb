"""P4: background dossier view — all tier-3/tier-4 chars in one file.

python3 kb/build_background.py [--limit N] [--out PATH]

Per locked decision: background characters ALL live in one
`dossiers/background.md` — dense structured sections (no prose dumps):
stats line, aliases, volume footprint incl. gap-queue, mined claims,
representative verbatim quotes (<=6, spread across the char's volume
range), event-scene count. Sections ordered tier 3 then 4, mentions
descending. Deterministic; regenerate from DB, never hand-edit.
"""
import argparse
import os
import sqlite3

from mention_build import canon
from roster_mine import DB_PATH, fold, iter_pages

import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


TWIN = {"a": "ā", "e": "ē", "i": "ī", "o": "ō", "u": "ū"}


def _pat(alias):
    """Pattern matching every corpus spelling of an alias: macron twins
    (Onuki/Ōnuki) and ou~ō swaps (Kouenji/Kōenji)."""
    s = fold(alias)
    parts, i = [], 0
    while i < len(s):
        if s[i:i + 2].lower() == "ou":
            ou = s[i:i + 2]
            oh = "Ō" if ou[0].isupper() else "ō"
            parts.append(f"(?:{ou}|{oh})")
            i += 2
            continue
        ch = s[i]
        low = ch.lower()
        if low in TWIN:
            m = TWIN[low]
            parts.append(f"[{ch}{m.upper() if ch.isupper() else m}]")
        else:
            parts.append(re.escape(ch))
        i += 1
    return re.compile(r"(?<!\w)" + "".join(parts) + r"(?!\w)")


def batch_evidence(pending, want=2):
    """pending: cid -> alias forms. One corpus pass -> cid -> [(vol,page,frag)]."""
    comps = {}
    for cid, forms in pending.items():
        comps[cid] = [_pat(a) for a in dict.fromkeys(forms) if re.search(r"\w", a)]
    found = {cid: [] for cid in pending}
    left = set(pending)
    for vol, stem, page, _pstart, ptext in iter_pages():
        if not left:
            break
        for cid in list(left):
            for comp in comps[cid]:
                m = comp.search(ptext)
                if not m:
                    continue
                s, e = max(0, m.start() - 70), min(len(ptext), m.end() + 130)
                frag = re.sub(r"\s+", " ", ptext[s:e]).strip()
                if s:
                    frag = "…" + frag
                if e < len(ptext):
                    frag += "…"
                found[cid].append((vol, page, frag[:240]))
                if len(found[cid]) >= want:
                    left.discard(cid)
                break
    return found


def quotes_for(db, cid, limit=6):
    rows = db.execute(
        "SELECT q.text_verbatim, q.vol_id, v.chrono_order, q.pdf_page "
        "FROM quotes q JOIN volumes v ON v.vol_id=q.vol_id "
        "WHERE q.char_id=? ORDER BY v.chrono_order, q.pdf_page, q.span_start",
        (cid,)).fetchall()
    if len(rows) <= limit:
        picked = rows
    else:
        step = len(rows) / limit
        picked = [rows[int(i * step)] for i in range(limit)]
    return [(re.sub(r"\s+", " ", t).strip(), vol, page)
            for t, vol, _c, page in picked]


def section(db, cid, name, tier, notes, mention_total, ev=()):
    qrows = quotes_for(db, cid)
    claims = db.execute(
        "SELECT c.claim, c.vol_id, c.pdf_page FROM claims c "
        "JOIN volumes v ON v.vol_id=c.vol_id WHERE c.char_id=? "
        "ORDER BY v.chrono_order, c.pdf_page LIMIT 4", (cid,)).fetchall()
    cov = db.execute(
        "SELECT c.vol_id, c.status FROM coverage c "
        "JOIN volumes v ON v.vol_id=c.vol_id WHERE c.char_id=? "
        "ORDER BY v.chrono_order", (cid,)).fetchall()
    vols_with_quotes = [v for v, s in cov if s == "quotes"]
    vols_gap = [v for v, s in cov if s == "occurrences"]
    aliases = [r[0] for r in db.execute(
        "SELECT raw_form FROM aliases WHERE char_id=? AND is_noise=0 "
        "ORDER BY form_type, raw_form", (cid,))]
    ev_n = db.execute(
        "SELECT COUNT(*) FROM event_participants WHERE char_id=?",
        (cid,)).fetchone()[0]
    out = [f"### {name}", ""]
    out.append(f"`tier {tier} · {mention_total} mentions · "
               f"{len(qrows)} quoted lines · {ev_n} scene(s)`")
    out.append("")
    if aliases:
        shown = ", ".join(aliases[:10])
        extra = f" (+{len(aliases)-10} more)" if len(aliases) > 10 else ""
        out.append(f"- **Aliases:** {shown}{extra}")
    if qrows:
        if vols_with_quotes:
            out.append(f"- **Spoken in:** {', '.join(vols_with_quotes)}")
        if vols_gap:
            out.append("- **Gap queue (mentioned, no attributed line):** "
                       f"{', '.join(vols_gap)}")
    else:
        cn = sorted({canon(a) for a in aliases})
        if cn:
            qs = ",".join("?" * len(cn))
            fp = db.execute(
                "SELECT m.vol_id, SUM(m.count) FROM mention_stats m "
                "JOIN volumes v ON v.vol_id=m.vol_id "
                f"WHERE m.token IN ({qs}) GROUP BY m.vol_id "
                "ORDER BY SUM(m.count) DESC, v.chrono_order", cn).fetchall()
            if fp:
                top = ", ".join(f"{v} ×{n}" for v, n in fp[:8])
                more = f" (+{len(fp)-8} more vols)" if len(fp) > 8 else ""
                out.append(f"- **Mentions:** {top}{more}")
        if not cov and not cn:
            out.append("- **Coverage:** no mentions found")
        for vol, page, frag in ev:
            out.append(f"- **Mention evidence:** “{frag}” ({vol} p.{page})")
    if notes and notes.strip() not in ("KNOWN curated", "KNOWN", "seed",
                                       "curated"):
        out.append(f"- **Notes:** {notes}")
    for claim, vol, page in claims:
        out.append(f"- **Claim:** “{claim}” ({vol} p.{page})")
    for text, vol, page in qrows:
        frag = text if len(text) <= 220 else text[:217] + "…"
        out.append(f"- **Quote:** “{frag}” ({vol} p.{page})")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(ROOT, "dossiers",
                                                   "background.md"))
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
        "SELECT char_id, canonical_name, tier, notes FROM characters "
        "WHERE tier IN (3,4) AND status<>'merged' "
        "ORDER BY tier, canonical_name").fetchall()
    chars = sorted(chars, key=lambda r: (r[2],
                                         -mention.get(r[0], 0)))
    if args.limit:
        chars = chars[:args.limit]
    thin_ids = {cid for (cid,) in db.execute(
        "SELECT c.char_id FROM characters c WHERE c.tier IN (3,4) "
        "AND c.status<>'merged' AND NOT EXISTS ("
        "SELECT 1 FROM quotes q WHERE q.char_id=c.char_id)")}
    pending = {}
    for cid, _n, _t, _no in chars:
        if cid in thin_ids:
            pending[cid] = [r[0] for r in db.execute(
                "SELECT raw_form FROM aliases WHERE char_id=? "
                "AND is_noise=0", (cid,))]
    evmap = batch_evidence(pending) if pending else {}
    total_m = sum(mention.get(c[0], 0) for c in chars)
    lines = [
        "# Background Characters",
        "",
        "One-line profiles for minor and background roles. Every quote "
        "is verbatim, cited with volume and page.",
        "",
        f"**{len(chars)} characters** · {total_m:,} total mentions",
        "",
        "## Contents",
        "",
    ]
    for cid, name, tier, _n in chars:
        lines.append(f"- [{name}](#{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')})")
    lines.append("")
    for cid, name, tier, notes in chars:
        lines.append(section(db, cid, name, tier, notes,
                             mention.get(cid, 0), evmap.get(cid, ())))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.out}: {len(chars)} sections, "
          f"{os.path.getsize(args.out):,} bytes")
    db.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""P9-6: exam / system dossier views (generated, idempotent).

python3 kb/build_exam_dossiers.py

Writes dossiers/exams/<exam_id>.md + index.md + chronology.md and
dossiers/systems/<sys_id>.md + index.md. Pure generated views — never
hand-edit; prose lives in kb/p9_analysis.py, identity in kb/p9_import.py.

Per exam dossier: rules · points · conditions · organizer · notes ·
footprint (per-vol anchored mentions) · runs (every instance with
chronology / participants / outcome / verbatim evidence / refs) ·
claims with verbatim evidence · evidence anchors. Chronology.md is the
master timeline: every instance across all exams ordered by
volumes.chrono_order then pdf_page.

Deterministic: every list sorted (chrono / count desc then id), no
timestamps — two consecutive runs must be md5-identical.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_EXAMS = ROOT / "dossiers" / "exams"
OUT_SYSTEMS = ROOT / "dossiers" / "systems"

def _footprint(con, table, col, ent, chrono_idx, first, last):
    by_vol = con.execute(
        f"SELECT vol_id, count(*) FROM {table} WHERE {col}=? "
        "GROUP BY vol_id ORDER BY vol_id", (ent,)).fetchall()
    by_vol.sort(key=lambda r: chrono_idx[r[0]])
    lines = [
        f"- **Span:** {first or '-'} → {last or '-'}",
        "- **Anchored mentions by vol:** "
        + ", ".join(f"{v} ×{c}" for v, c in by_vol),
        "",
    ]
    return lines


def one_exam(con, exam, chrono_idx):
    exam_id, name, kind, rules, points, cond, org, notes, first, last = exam
    total = con.execute(
        "SELECT count(*) FROM exam_mentions WHERE exam_id=?",
        (exam_id,)).fetchone()[0]
    vols_n = con.execute(
        "SELECT count(DISTINCT vol_id) FROM exam_mentions WHERE exam_id=?",
        (exam_id,)).fetchone()[0]
    runs = con.execute(
        "SELECT instance_id, seq, vol_id, pdf_page, chronology, "
        "participants, outcome, corroboration_refs, evidence_quote, "
        "confidence FROM exam_instances WHERE exam_id=? "
        "ORDER BY vol_id, pdf_page, seq", (exam_id,)).fetchall()
    runs.sort(key=lambda r: (chrono_idx[r[2]], r[3], r[1]))
    claims = con.execute(
        "SELECT claim, kind, claimant, confidence, vol_id, pdf_page, "
        "evidence_quote, corroboration_refs, reliability_note "
        "FROM exam_claims WHERE exam_id=? ORDER BY claim_id",
        (exam_id,)).fetchall()
    anchors = con.execute(
        "SELECT vol_id, pdf_page FROM exam_mentions WHERE exam_id=? "
        "ORDER BY vol_id, pdf_page LIMIT 8", (exam_id,)).fetchall()

    L = []
    L.append(f"# {name}\n")
    L.append(f"**{kind}**\n")
    L.append(f"`{total} mentions · {vols_n} vols · {len(runs)} runs · "
             f"{len(claims)} claims`\n")
    L.append("## Rules\n")
    L.append(f"{rules}\n")
    L.append("## Points\n")
    L.append(f"{points}\n")
    L.append("## Conditions\n")
    L.append(f"{cond}\n")
    L.append("## Organizer\n")
    L.append(f"{org}\n")
    L.append("## Notes\n")
    L.append(f"{notes}\n")
    L.append("## Footprint\n")
    L.extend(_footprint(con, "exam_mentions", "exam_id", exam_id,
                        chrono_idx, first, last))
    if runs:
        L.append("## Runs\n")
        for (_iid, seq, vol, page, chron, part, out, refs, eq,
             conf) in runs:
            L.append(f"### {vol} p.{page} (run #{seq}, conf {conf})\n")
            L.append(f"- **Chronology:** {chron}")
            L.append(f"- **Participants:** {part}")
            L.append(f"- **Outcome:** {out}")
            L.append(f"- **Evidence:** “{eq}”")
            L.append(f"- **Refs:** {refs}")
            L.append("")
    if claims:
        L.append("## Claims\n")
        for claim, kind_c, claimant, conf, vol, page, eq, refs, rel in claims:
            who = claimant or "unattributed"
            L.append(f"- “{claim}” ({vol} p.{page}) — {kind_c}, "
                     f"{who}, conf {conf}")
            L.append(f"  - evidence: “{eq}”")
            L.append(f"  - {rel}")
        L.append("")
    if anchors:
        L.append("## Evidence anchors\n")
        L.append("")
        L.append(", ".join(f"{v} p.{p}" for v, p in anchors))
        L.append("")
    return "\n".join(L)


def one_system(con, sys_row, chrono_idx):
    sys_id, name, kind, func, notes, first, last = sys_row
    total = con.execute(
        "SELECT count(*) FROM system_mentions WHERE sys_id=?",
        (sys_id,)).fetchone()[0]
    vols_n = con.execute(
        "SELECT count(DISTINCT vol_id) FROM system_mentions WHERE sys_id=?",
        (sys_id,)).fetchone()[0]
    claims = con.execute(
        "SELECT claim, kind, claimant, confidence, vol_id, pdf_page, "
        "evidence_quote, corroboration_refs, reliability_note "
        "FROM system_claims WHERE sys_id=? ORDER BY claim_id",
        (sys_id,)).fetchall()
    anchors = con.execute(
        "SELECT vol_id, pdf_page FROM system_mentions WHERE sys_id=? "
        "ORDER BY vol_id, pdf_page LIMIT 8", (sys_id,)).fetchall()

    L = []
    L.append(f"# {name}\n")
    L.append(f"**{kind}**\n")
    L.append(f"`{total} mentions · {vols_n} vols · {len(claims)} claims`\n")
    L.append("## Function\n")
    L.append(f"{func}\n")
    L.append("## Notes\n")
    L.append(f"{notes}\n")
    L.append("## Footprint\n")
    L.extend(_footprint(con, "system_mentions", "sys_id", sys_id,
                        chrono_idx, first, last))
    if claims:
        L.append("## Claims\n")
        for claim, kind_c, claimant, conf, vol, page, eq, _refs, rel in claims:
            who = claimant or "unattributed"
            L.append(f"- “{claim}” ({vol} p.{page}) — {kind_c}, "
                     f"{who}, conf {conf}")
            L.append(f"  - evidence: “{eq}”")
            L.append(f"  - {rel}")
        L.append("")
    if anchors:
        L.append("## Evidence anchors\n")
        L.append("")
        L.append(", ".join(f"{v} p.{p}" for v, p in anchors))
        L.append("")
    return "\n".join(L)


def exam_index(con):
    rows = con.execute(
        "SELECT exam_id, name, kind, first_vol, last_vol FROM exams "
        "ORDER BY kind, exam_id").fetchall()
    mentions = dict(con.execute(
        "SELECT exam_id, count(*) FROM exam_mentions GROUP BY exam_id"
    ).fetchall())
    runs_n = dict(con.execute(
        "SELECT exam_id, count(*) FROM exam_instances GROUP BY exam_id"
    ).fetchall())
    claims_n = dict(con.execute(
        "SELECT exam_id, count(*) FROM exam_claims GROUP BY exam_id"
    ).fetchall())
    L = ["# All Exams\n",
         f"{len(rows)} exams — rules, points, conditions, and every run "
         f"with evidence\n"]
    kind = None
    for exam_id, name, k, first, last in rows:
        if k != kind:
            kind = k
            L.append(f"## {kind}\n")
        L.append(f"- [{name}]({exam_id}.md) — "
                 f"{mentions.get(exam_id, 0)} mentions · "
                 f"{first or '-'}→{last or '-'} · "
                 f"{runs_n.get(exam_id, 0)} runs · "
                 f"{claims_n.get(exam_id, 0)} claims")
    L.append("")
    L.append("[Master chronology](chronology.md)")
    L.append("")
    return "\n".join(L)


def system_index(con):
    rows = con.execute(
        "SELECT sys_id, name, kind, first_vol, last_vol FROM systems "
        "ORDER BY kind, sys_id").fetchall()
    mentions = dict(con.execute(
        "SELECT sys_id, count(*) FROM system_mentions GROUP BY sys_id"
    ).fetchall())
    claims_n = dict(con.execute(
        "SELECT sys_id, count(*) FROM system_claims GROUP BY sys_id"
    ).fetchall())
    L = ["# All Systems\n",
         f"{len(rows)} systems — how the school runs: points, council, "
         f"clubs, expulsion\n"]
    kind = None
    for sys_id, name, k, first, last in rows:
        if k != kind:
            kind = k
            L.append(f"## {kind}\n")
        L.append(f"- [{name}]({sys_id}.md) — "
                 f"{mentions.get(sys_id, 0)} mentions · "
                 f"{first or '-'}→{last or '-'} · "
                 f"{claims_n.get(sys_id, 0)} claims")
    L.append("")
    return "\n".join(L)


def chronology(con, chrono_idx):
    rows = con.execute(
        "SELECT i.vol_id, i.pdf_page, i.seq, e.name, i.chronology, "
        "i.confidence FROM exam_instances i "
        "JOIN exams e ON e.exam_id = i.exam_id").fetchall()
    rows.sort(key=lambda r: (chrono_idx[r[0]], r[1], r[3], r[2]))
    L = ["# Master Chronology\n",
         f"{len(rows)} exam runs in story order — volume and page for "
         f"every attempt\n"]
    vol = None
    for v, page, seq, name, chron, conf in rows:
        if v != vol:
            vol = v
            if len(L) > 3:
                L.append("")
            L.append(f"## {v}\n")
        L.append(f"- **p.{page}** — {name} #{seq} (conf {conf}): {chron}")
    L.append("")
    return "\n".join(L)


def main():
    con = sqlite3.connect(DB_PATH)
    chrono_idx = {v: i for i, (v,) in enumerate(
        con.execute("SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    exams = con.execute(
        "SELECT exam_id, name, kind, rules_summary, points, conditions, "
        "organizer, notes, first_vol, last_vol FROM exams "
        "ORDER BY exam_id").fetchall()
    systems = con.execute(
        "SELECT sys_id, name, kind, function, notes, first_vol, last_vol "
        "FROM systems ORDER BY sys_id").fetchall()
    OUT_EXAMS.mkdir(parents=True, exist_ok=True)
    OUT_SYSTEMS.mkdir(parents=True, exist_ok=True)
    for exam in exams:
        (OUT_EXAMS / f"{exam[0]}.md").write_text(one_exam(
            con, exam, chrono_idx))
    for sys_row in systems:
        (OUT_SYSTEMS / f"{sys_row[0]}.md").write_text(one_system(
            con, sys_row, chrono_idx))
    (OUT_EXAMS / "index.md").write_text(exam_index(con))
    (OUT_EXAMS / "chronology.md").write_text(chronology(con, chrono_idx))
    (OUT_SYSTEMS / "index.md").write_text(system_index(con))
    con.close()
    print(f"build_exam_dossiers: {len(exams)} exam dossiers + index + "
          f"chronology, {len(systems)} system dossiers + index")
    return 0


if __name__ == "__main__":
    sys.exit(main())

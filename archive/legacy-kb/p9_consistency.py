#!/usr/bin/env python3
"""P9-7 exams/systems consistency gate (read-only).

python3 kb/p9_consistency.py

Checks the exam/system layer end to end:
  exams             kind in the documented set · rules_summary / points /
                    conditions / organizer / notes authored (non-empty) ·
                    first/last_vol exist and match the chronological
                    min/max of own mentions
  systems           kind in the documented set · function/notes authored ·
                    first/last_vol match own mentions
  exam_aliases      every raw/normalized form maps to an existing exam and
                    is globally unique (one form, one entity); form_type
                    in {full, short, variant, epithet, alias}
  system_aliases    same rules over the system table
  exam_mentions     exam/vol exist · span inside its page bounds (local
                    coords: ls = span_start - pstart) · provenance
                    recorded
  system_mentions   same over system_mentions
  exam_instances    exam exists · seq > 0 · confidence in (0, 1] ·
                    chronology/participants/outcome authored · refs are
                    real pages and EVERY ref carries a mention of this
                    exam · evidence_quote verbatim (exact substring of the
                    anchor page's raw text) · stored span inside bounds
  exam_claims       entity exists · kind valid · confidence in (0, 1] ·
                    claimant NULL / 'narrator' / existing char · claim /
                    perspective / reliability authored · refs real and
                    EVERY ref carries a mention · evidence verbatim at
                    anchor
  system_claims     same over system_claims
  exams_fts         one row per exam · systems_fts one row per system
  dossiers/exams    one .md per exam + index.md + chronology.md on disk
  dossiers/systems  one .md per system + index.md on disk

Refs rule is STRICTER than p8_consistency (>=1 anchored ref): here all
refs must be anchored, matching kb/p9_analysis.py's fail-before-write.

Exit 0 = clean; exit 1 = violations (printed one per line).
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402

EXAM_KINDS = {"written", "special", "event", "entrance", "other"}
SYS_KINDS = {"points", "governance", "activity", "discipline",
             "admissions", "other"}
FORM_TYPES = {"full", "short", "variant", "epithet", "alias"}
CLAIM_KINDS = {"narrator_fact", "character_claim", "other_reported",
               "inference"}
ROOT = Path(__file__).resolve().parent.parent
EXAM_DOSSIERS = ROOT / "dossiers" / "exams"
SYS_DOSSIERS = ROOT / "dossiers" / "systems"


def check_refs(where, refs, ent, kind_key, mentions, pages, out):
    """refs must be real pages and every one anchored to this entity."""
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
        if (kind_key, ent, vol, page) in mentions:
            anchored += 1
    if refs and anchored != len(refs):
        out.append(f"{where}: only {anchored}/{len(refs)} refs carry a "
                   f"mention of {ent}")
    return anchored


def main():
    con = sqlite3.connect(DB_PATH)
    out = []

    vols = {v for v, in con.execute("SELECT vol_id FROM volumes")}
    chrono = {v: i for i, (v,) in enumerate(
        con.execute("SELECT vol_id FROM volumes ORDER BY chrono_order"))}
    char_ids = {c for c, in con.execute("SELECT char_id FROM characters")}
    exam_ids = {e for e, in con.execute("SELECT exam_id FROM exams")}
    sys_ids = {s for s, in con.execute("SELECT sys_id FROM systems")}

    mentions = {}
    for eid, vol, page, s, e in con.execute(
            "SELECT exam_id, vol_id, pdf_page, span_start, span_end "
            "FROM exam_mentions"):
        mentions.setdefault(("exam", eid, vol, page), []).append((s, e))
    for sid, vol, page, s, e in con.execute(
            "SELECT sys_id, vol_id, pdf_page, span_start, span_end "
            "FROM system_mentions"):
        mentions.setdefault(("sys", sid, vol, page), []).append((s, e))
    pages = {}
    for vol, _stem, page, pstart, ptext in iter_pages():
        pages[(vol, page)] = (pstart, ptext)

    # exams
    for eid, kind, rules, points, cond, org, notes, first, last in con.execute(
            "SELECT exam_id, kind, rules_summary, points, conditions, "
            "organizer, notes, first_vol, last_vol FROM exams"):
        where = f"exams {eid}"
        if kind not in EXAM_KINDS:
            out.append(f"{where}: kind {kind!r} not in set")
        for field, val in (("rules_summary", rules), ("points", points),
                           ("conditions", cond), ("organizer", org),
                           ("notes", notes)):
            if not (val or "").strip():
                out.append(f"{where}: {field} not authored")
        if first is not None and first not in vols:
            out.append(f"{where}: first_vol {first!r} unknown")
        if last is not None and last not in vols:
            out.append(f"{where}: last_vol {last!r} unknown")
        here = [k[2] for k in mentions if k[0] == "exam" and k[1] == eid]
        if here:
            exp_first = min(here, key=lambda v: chrono[v])
            exp_last = max(here, key=lambda v: chrono[v])
            if first != exp_first or last != exp_last:
                out.append(f"{where}: footprint {first}->{last} != "
                           f"{exp_first}->{exp_last} (mentions)")

    # systems
    for sid, kind, func, notes, first, last in con.execute(
            "SELECT sys_id, kind, function, notes, first_vol, last_vol "
            "FROM systems"):
        where = f"systems {sid}"
        if kind not in SYS_KINDS:
            out.append(f"{where}: kind {kind!r} not in set")
        if not (func or "").strip() or not (notes or "").strip():
            out.append(f"{where}: function/notes not authored")
        if first is not None and first not in vols:
            out.append(f"{where}: first_vol {first!r} unknown")
        if last is not None and last not in vols:
            out.append(f"{where}: last_vol {last!r} unknown")
        here = [k[2] for k in mentions if k[0] == "sys" and k[1] == sid]
        if here:
            exp_first = min(here, key=lambda v: chrono[v])
            exp_last = max(here, key=lambda v: chrono[v])
            if first != exp_first or last != exp_last:
                out.append(f"{where}: footprint {first}->{last} != "
                           f"{exp_first}->{exp_last} (mentions)")

    # aliases
    for table, col, known, label in (
            ("exam_aliases", "exam_id", exam_ids, "exams"),
            ("system_aliases", "sys_id", sys_ids, "systems")):
        form_owner = {}
        for raw, norm, ftype, ent in con.execute(
                f"SELECT raw_form, normalized, form_type, {col} "
                f"FROM {table} ORDER BY alias_id"):
            where = f"{table} {raw!r}"
            if ent not in known:
                out.append(f"{where}: orphan {col} {ent}")
            if ftype not in FORM_TYPES:
                out.append(f"{where}: form_type {ftype!r}")
            for key in (raw, norm):
                if key in form_owner and form_owner[key] != ent:
                    out.append(f"{where}: form shared with "
                               f"{form_owner[key]}")
                form_owner[key] = ent

    # mentions (both tables, span bounds are page-local)
    for table, col, prov_expect in (
            ("exam_mentions", "exam_id", "p9_mentions"),
            ("system_mentions", "sys_id", "p9_mentions")):
        for ent, vol, page, s, e, prov in con.execute(
                f"SELECT {col}, vol_id, pdf_page, span_start, span_end, "
                f"provenance FROM {table}"):
            where = f"{table} {ent} {vol} p.{page}"
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
            if prov != prov_expect:
                out.append(f"{where}: provenance {prov!r}")

    # instances
    for iid, eid, seq, conf, chron, part, outc, refs_json, eq, evol, \
            epage, s, e in con.execute(
            "SELECT instance_id, exam_id, seq, confidence, chronology, "
            "participants, outcome, corroboration_refs, evidence_quote, "
            "vol_id, pdf_page, span_start, span_end FROM exam_instances"):
        where = f"exam_instances {iid} ({eid})"
        if eid not in exam_ids:
            out.append(f"{where}: orphan exam")
        if not (isinstance(seq, int) and seq > 0):
            out.append(f"{where}: seq {seq!r}")
        if conf is None or not (0 < conf <= 1):
            out.append(f"{where}: confidence {conf!r}")
        for field, val in (("chronology", chron), ("participants", part),
                           ("outcome", outc)):
            if not (val or "").strip():
                out.append(f"{where}: {field} not authored")
        if not (eq or "").strip():
            out.append(f"{where}: empty evidence_quote")
        try:
            refs = json.loads(refs_json or "[]")
        except ValueError:
            out.append(f"{where}: unparseable refs")
            continue
        check_refs(where, refs, eid, "exam", mentions, pages, out)
        bounds = pages.get((evol, epage))
        if bounds is None:
            out.append(f"{where}: anchor {evol} p.{epage} not a page")
        else:
            pstart, text = bounds
            ls = s - pstart
            if not (0 <= ls <= len(text)):
                out.append(f"{where}: anchor span {s} outside page bounds")
            if eq and eq not in text:
                out.append(f"{where}: evidence_quote not verbatim at "
                           f"anchor {evol} p.{epage}")
        if refs:
            first_ref = refs[0].split(" p.")
            if len(first_ref) == 2 and (first_ref[0], int(first_ref[1])) \
                    != (evol, epage):
                out.append(f"{where}: anchor {evol} p.{epage} != first "
                           f"ref {refs[0]!r}")

    # claims (both tables)
    for table, col, known, kind_key, label in (
            ("exam_claims", "exam_id", exam_ids, "exam", "EXAM"),
            ("system_claims", "sys_id", sys_ids, "sys", "SYS")):
        for cid, ent, claim, kind, claimant, pers, conf, rel, \
                refs_json, eq, evol, epage in con.execute(
                f"SELECT claim_id, {col}, claim, kind, claimant, "
                "perspective, confidence, reliability_note, "
                "corroboration_refs, evidence_quote, vol_id, pdf_page "
                f"FROM {table}"):
            where = f"{table} {cid} ({ent})"
            if ent not in known:
                out.append(f"{where}: orphan entity")
            if kind not in CLAIM_KINDS:
                out.append(f"{where}: kind {kind!r}")
            if conf is None or not (0 < conf <= 1):
                out.append(f"{where}: confidence {conf!r}")
            if claimant is not None and claimant != "narrator" \
                    and claimant not in char_ids:
                out.append(f"{where}: unknown claimant {claimant!r}")
            for field, val in (("claim", claim), ("perspective", pers),
                               ("reliability_note", rel)):
                if not (val or "").strip():
                    out.append(f"{where}: {field} not authored")
            if not (eq or "").strip():
                out.append(f"{where}: empty evidence_quote")
            try:
                refs = json.loads(refs_json or "[]")
            except ValueError:
                out.append(f"{where}: unparseable refs")
                continue
            check_refs(where, refs, ent, kind_key, mentions, pages, out)
            text = pages.get((evol, epage), (0, ""))[1]
            if eq and text and eq not in text:
                out.append(f"{where}: evidence_quote not verbatim at "
                           f"anchor {evol} p.{epage}")
            if refs:
                first_ref = refs[0].split(" p.")
                if len(first_ref) == 2 and (first_ref[0],
                                            int(first_ref[1])) \
                        != (evol, epage):
                    out.append(f"{where}: anchor {evol} p.{epage} != "
                               f"first ref {refs[0]!r}")

    # fts + dossier files
    n_exams = con.execute("SELECT count(*) FROM exams").fetchone()[0]
    n_syst = con.execute("SELECT count(*) FROM systems").fetchone()[0]
    n_efs = con.execute("SELECT count(*) FROM exams_fts").fetchone()[0]
    n_sfs = con.execute("SELECT count(*) FROM systems_fts").fetchone()[0]
    if n_efs != n_exams:
        out.append(f"exams_fts: {n_efs} rows != {n_exams} exams")
    if n_sfs != n_syst:
        out.append(f"systems_fts: {n_sfs} rows != {n_syst} systems")
    for eid in sorted(exam_ids):
        if not (EXAM_DOSSIERS / f"{eid}.md").exists():
            out.append(f"dossiers/exams: missing {eid}.md")
    for name in ("index.md", "chronology.md"):
        if not (EXAM_DOSSIERS / name).exists():
            out.append(f"dossiers/exams: missing {name}")
    for sid in sorted(sys_ids):
        if not (SYS_DOSSIERS / f"{sid}.md").exists():
            out.append(f"dossiers/systems: missing {sid}.md")
    if not (SYS_DOSSIERS / "index.md").exists():
        out.append("dossiers/systems: missing index.md")
    con.close()

    if out:
        print(f"p9_consistency: {len(out)} violation(s)")
        for line in out:
            print("  ", line)
        return 1
    print("p9_consistency: all checks clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

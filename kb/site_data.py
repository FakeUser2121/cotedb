#!/usr/bin/env python3
"""Data access for the site build: one place that knows the cote_kb.db
schema and the ledger file layout, and hands the builders plain dicts.

Read rules inherited from the walk:
  - cote_kb.db attribution is diagnosed broken, so quote rows are served as
    TEXT AT A PAGE (support for a claim), never as proof of who spoke.
  - the curated layers (exam_instances, status_timeline, relations, claims)
    carry written analysis and are the only rows that generate prose.
  - ledgers/ are the truth layer for walk coverage; a volume is presented as
    evidence-complete only when its ledger markers say so.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LEDGERS = ROOT / "ledgers"
DRAFTS = ROOT / "drafts" / "people"

WALK_START_RE = re.compile(r"<!--\s*walk:\s*(\S+)\s+→\s*start\s*-->")
WALK_CH_RE = re.compile(r"<!--\s*walk:\s*(\S+)\s+ch([\d.]+)\s*→")
LEDGER_HEAD_RE = re.compile(r"^### (.+)$", re.M)
BOLD_LABEL_RE = re.compile(r"^- \*\*([^*]+):\*\*\s*(.*)$")
BULLET_RE = re.compile(r"^- (.*)$")
SUB_BULLET_RE = re.compile(r"^  - (.*)$")
ITALIC_RE = re.compile(r"\*\"([^\"]*)\"(\*|\*)")
ARROW_RE = re.compile(r"\$?\\(?:rightarrow|to)\$?|→")

PAPER_CHARS = {"“": '"', "”": '"', "’": "'"}


def clean(text):
    """Plain-text a ledger line for public reading: no markdown stars, no
    LaTeX arrows, typographic quotes normalised, and the archive's own
    vocabulary replaced by reader-facing wording (site_arch.PROSE_REWORD —
    safe because those words have zero hits in the novel text)."""
    if not text:
        return ""
    t = text.replace("**", "").replace("*", "")
    t = re.sub(r"\$\\(?:rightarrow|to)\$", "→", t)
    t = t.replace("\\rightarrow", "→").replace("$", "")
    t = site_arch.public_words(t, site_arch.PROSE_REWORD)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def characters(con):
    """All characters with display names and footprint counts, tier order."""
    rows = con.execute(
        "SELECT c.char_id, c.canonical_name, c.tier, c.status, "
        "(SELECT count(*) FROM quotes q WHERE q.char_id = c.char_id), "
        "(SELECT count(DISTINCT q.vol_id) FROM quotes q "
        " WHERE q.char_id = c.char_id), "
        "(SELECT count(*) FROM coverage cv WHERE cv.char_id = c.char_id) "
        "FROM characters c WHERE c.merged_into IS NULL "
        "ORDER BY c.tier, c.canonical_name"
    ).fetchall()
    out = []
    for (cid, canon, tier, status, quotes, qvols, cov) in rows:
        name = site_arch.display_name(canon, cid)
        letter = name.split()[0][:1].upper() if name else "?"
        out.append({
            "id": cid, "name": name, "canon": canon or "", "tier": tier or 4,
            "status": status or "", "quotes": quotes or 0,
            "quote_vols": qvols or 0, "coverage": cov or 0,
            "letter": letter,
            "href": person_href(cid, tier or 4, letter),
        })
    return out


# Tier 1 and 2 get a page of their own. Everyone else is an entry on the
# page for their initial — a profile page per one-line character would be
# 226 pages of almost nothing.
OWN_PAGE_TIERS = (1, 2)


def person_href(char_id, tier=1, letter=""):
    if tier in OWN_PAGE_TIERS:
        return f"people/{char_id}.html"
    return f"people/minor/{(letter or char_id[:1]).lower()}.html#{char_id}"


def coverage_by_char(con):
    """{char_id: [{'vol_id', 'status'}]} — which volumes a name is written in.

    This is the extractor's mention table, not an interpretation: 'quotes'
    means the name is attached to speech on some page of that volume,
    'occurrences' means the name appears in the text. Safe to publish on a
    volume the walk has not read yet, which is why stubs are built from it.
    """
    out = {}
    for cid, vol, status in con.execute(
            "SELECT char_id, vol_id, status FROM coverage"):
        out.setdefault(cid, []).append({"vol_id": vol, "status": status or ""})
    return out


def aliases_by_char(con):
    """{char_id: [raw form]} — the spellings the walk anchored on."""
    out = {}
    for cid, raw in con.execute(
            "SELECT char_id, raw_form FROM aliases "
            "WHERE COALESCE(is_noise, 0) = 0 ORDER BY char_id, raw_form"):
        forms = out.setdefault(cid, [])
        if raw and raw not in forms:
            forms.append(raw)
    return out


def walk_state():
    """{vol_id: {'start': bool, 'chapters': set, 'markers': n}}."""
    state = {}
    for f in sorted(LEDGERS.rglob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in WALK_START_RE.finditer(text):
            state.setdefault(m.group(1), {"start": True, "chapters": set(),
                                          "markers": 0})["markers"] += 1
        for m in WALK_CH_RE.finditer(text):
            s = state.setdefault(m.group(1), {"start": True,
                                              "chapters": set(), "markers": 0})
            s["chapters"].add(m.group(2))
            s["markers"] += 1
    for vol, s in state.items():
        s["complete"] = volume_ledger_exists(vol) and len(s["chapters"]) >= 8
    return state


def volume_ledger_exists(vol_id):
    return (LEDGERS / "volumes" / f"{vol_id}.md").exists()


def volume_ledger(vol_id):
    """[{n,title,pp,setting,beats}] parsed from ledgers/volumes/<vol>.md."""
    f = LEDGERS / "volumes" / f"{vol_id}.md"
    if not f.exists():
        return []
    chapters = []
    cur = None
    in_beats = False
    for raw in f.read_text(encoding="utf-8", errors="replace").splitlines():
        mh = LEDGER_HEAD_RE.match(raw.strip())
        if mh:
            title = clean(mh.group(1))
            mp = re.search(r"\((?:pp?\.|p)\s*([\d–\-]+)\)", title)
            pp = mp.group(1) if mp else ""
            name = re.sub(r"\s*\((?:pp?\.|p)[^)]*\)\s*$", "", title)
            name = re.sub(r"^Chapter\s+\d+:\s*", "", name)
            num = re.match(r"^(?:Chapter\s+)?([\d.]+)", title)
            cur = {"n": num.group(1) if num else str(len(chapters) + 1),
                   "title": name, "pp": pp, "setting": "", "beats": [],
                   "heading": title}
            chapters.append(cur)
            in_beats = False
            continue
        if cur is None:
            continue
        ml = BOLD_LABEL_RE.match(raw.strip())
        if ml:
            label, value = ml.group(1).strip(), clean(ml.group(2))
            if label.lower().startswith("setting"):
                cur["setting"] = value
                in_beats = False
            elif "beat" in label.lower():
                in_beats = True
            else:
                cur.setdefault("extras", []).append((label, value))
                in_beats = False
            continue
        ms = SUB_BULLET_RE.match(raw)
        mb = BULLET_RE.match(raw.strip())
        if ms:
            cur["beats"].append(clean(ms.group(1)))
        elif mb and not raw.startswith("  "):
            cur["beats"].append(clean(mb.group(1)))
            in_beats = False
    return [c for c in chapters if c["beats"] or c["setting"]]


def volume_chapter_count(vol_id):
    return len(volume_ledger(vol_id))


def status_timeline(con):
    rows = con.execute(
        "SELECT char_id, vol_id, situation, knowledge_state, changes, why, "
        "evidence_refs FROM status_timeline ORDER BY vol_id"
    ).fetchall()
    names = dict(
        (r[0], r[1]) for r in con.execute(
            "SELECT char_id, canonical_name FROM characters")
    )
    return [{
        "char_id": cid, "vol_id": vol, "situation": situation,
        "knowledge": knowledge, "changes": changes, "why": why,
        "refs": evidence or "", "name": site_arch.display_name(
            names.get(cid, cid), cid),
    } for cid, vol, situation, knowledge, changes, why, evidence in rows]


def exams(con):
    rows = con.execute(
        "SELECT exam_id, name, kind, rules_summary, points, conditions, "
        "organizer, notes, first_vol, last_vol FROM exams ORDER BY name"
    ).fetchall()
    inst = con.execute(
        "SELECT instance_id, exam_id, seq, vol_id, pdf_page, chronology, "
        "participants, outcome, corroboration_refs, confidence "
        "FROM exam_instances ORDER BY exam_id, seq"
    ).fetchall()
    by_exam = {}
    by_vol = {}
    for iid, eid, seq, vol, page, chrono, parts, outcome, refs, conf in inst:
        row = {"id": iid, "exam_id": eid, "seq": seq, "vol_id": vol,
               "page": page, "chronology": chrono or "", "participants": parts or "",
               "outcome": outcome or "", "refs": refs or "", "conf": conf}
        by_exam.setdefault(eid, []).append(row)
        by_vol.setdefault(vol, []).append(row)
    out = []
    for (eid, name, kind, rules, points, cond, org, notes, fvol, lvol) in rows:
        out.append({"id": eid, "name": name, "kind": kind or "",
                    "rules": rules or "", "points": points or "",
                    "conditions": cond or "", "organizer": org or "",
                    "notes": notes or "", "first_vol": fvol or "",
                    "last_vol": lvol or "", "instances": by_exam.get(eid, [])})
    return {"list": out, "by_vol": by_vol}


def locations(con):
    return [
        {"id": lid, "name": name, "kind": kind or "", "function": fn or "",
         "notes": notes or "", "first_vol": fv or "", "last_vol": lv or "",
         "mentions": con.execute(
             "SELECT count(*) FROM location_mentions WHERE loc_id = ?",
             (lid,)).fetchone()[0]}
        for lid, name, kind, fn, notes, fv, lv in con.execute(
            "SELECT loc_id, name, kind, function, notes, first_vol, last_vol "
            "FROM locations ORDER BY name")
    ]


def systems(con):
    return [
        {"id": sid, "name": name, "kind": kind or "", "function": fn or "",
         "notes": notes or ""}
        for sid, name, kind, fn, notes in con.execute(
            "SELECT sys_id, name, kind, function, notes FROM systems "
            "ORDER BY name")
    ]


def relations(con):
    rows = con.execute(
        "SELECT char_a, char_b, rel_type, direction_note, valid_from_vol, "
        "valid_to_vol, evidence_refs FROM relations").fetchall()
    names = dict(con.execute(
        "SELECT char_id, canonical_name FROM characters").fetchall())
    out = []
    for a, b, rtype, note, vfrom, vto, refs in rows:
        out.append({
            "a": a, "b": b, "type": rtype or "", "note": note or "",
            "from": vfrom or "", "to": vto or "", "refs": refs or "",
            "a_name": site_arch.display_name(names.get(a, a), a),
            "b_name": site_arch.display_name(names.get(b, b), b),
        })
    return out


def claims(con):
    rows = con.execute(
        "SELECT char_id, claim, kind, reliability_note, vol_id, pdf_page, "
        "evidence_quote FROM claims ORDER BY char_id, vol_id").fetchall()
    names = dict(con.execute(
        "SELECT char_id, canonical_name FROM characters").fetchall())
    return [{
        "char_id": cid, "claim": claim or "", "kind": kind or "",
        "note": rel or "", "vol_id": vol or "", "page": page or 0,
        "quote": quote or "",
        "name": site_arch.display_name(names.get(cid, cid), cid),
    } for cid, claim, kind, rel, vol, page, quote in rows]


def quotes_at(con, vol_id, page, limit=3):
    """Verbatim text located at a page — support for a citation, not a
    claim about who said it."""
    rows = con.execute(
        "SELECT text_verbatim FROM quotes WHERE vol_id = ? AND pdf_page = ? "
        "ORDER BY span_start LIMIT ?", (vol_id, page, limit)).fetchall()
    return [clean(r[0]) for r in rows if r[0]]


def present_chars(con, vol_id):
    """Characters the locator found in a volume, roster-ordered."""
    rows = con.execute(
        "SELECT cv.char_id, cv.status, c.canonical_name, c.tier FROM coverage "
        "cv JOIN characters c ON c.char_id = cv.char_id WHERE cv.vol_id = ? "
        "ORDER BY c.tier, c.canonical_name", (vol_id,)).fetchall()
    return [{
        "id": cid, "status": st or "", "tier": tier or 4,
        "name": site_arch.display_name(canon or cid, cid),
    } for cid, st, canon, tier in rows]


def drafts():
    """(stem, kind) for the authored transcript/guide files in drafts/."""
    if not DRAFTS.exists():
        return []
    out = []
    for f in sorted(DRAFTS.glob("*.md")):
        stem = f.stem
        kind = "transcript" if stem.endswith(".transcript") else "guide"
        out.append((stem, kind, f))
    return out


def mention_totals(con, vol_id):
    return con.execute(
        "SELECT count(*) FROM mention_stats WHERE vol_id = ?",
        (vol_id,)).fetchone()[0]

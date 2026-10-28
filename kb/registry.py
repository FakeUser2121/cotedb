#!/usr/bin/env python3
"""The entity registry: one record per thing in the encyclopedia.

Every page, index entry, rail count, citation label and search hit is built
from the records assembled here. The inputs are only ever data — cote_kb.db
rows, `ledgers/` files and `drafts/` — and the rules live in `kb/schema.json`.
Adding a character, volume, exam, system, place or topic therefore means
adding its row (and its ledger, once the walk has read it): no builder,
template or navigation file has to change.

Identity is the one thing that used to be scattered. A ledger is named after
the id the walk wrote into it (`tachibana`), the roster after the id it was
imported with (`tachibana-akane`); the same person therefore had two ids and
half the site could not see the other half. `site_ledgers.LEDGER_ALIAS` is now
the only table that pairs them, and every builder goes through `page_id_for`.

Records carry the fields `kb/schema.json` declares for every entity:
id, display_name, aliases, sort_key, type, status, tier, parents.
"""

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arch  # noqa: E402
import site_bands as B  # noqa: E402
import site_data as D  # noqa: E402
import site_ledgers as L  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "cote_kb.db"
SCHEMA_PATH = Path(__file__).with_name("schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

TYPES = tuple(SCHEMA["types"])


def fold(text):
    """Accent- and case-insensitive form used for sorting and alias matching."""
    s = unicodedata.normalize("NFKD", text or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def sort_name(name):
    """Family name first, as the novels print it, folded for sorting."""
    parts = (name or "").split()
    return fold(parts[0]) if parts else ""


def _ledger_blocks(led):
    return sum(len(s["blocks"]) for s in (led or {}).get("vols") or [])


def _ledger_vols(led):
    return {s["vol"] for s in (led or {}).get("vols") or []}


def char_status(scenes, coverage_vols, done_vols):
    rule = SCHEMA["status_rules"]["character"]
    if not scenes:
        return "stub"
    if coverage_vols and all(v in done_vols for v in coverage_vols):
        return "complete"
    return "partial"


def volume_status(vol_id, done_vols, blocks, chapters):
    if vol_id in done_vols:
        return "complete"
    if blocks or chapters:
        return "partial"
    return "stub"


def ledger_status(led, done_vols):
    if not led:
        return "stub"
    vols = _ledger_vols(led)
    if vols and all(v in done_vols for v in vols):
        return "complete"
    return "partial"


def _person_aliases(con):
    out = {}
    for cid, raw, form in con.execute(
            "SELECT char_id, raw_form, form_type FROM aliases "
            "WHERE COALESCE(is_noise, 0) = 0 ORDER BY char_id, raw_form"):
        if raw:
            out.setdefault(cid, []).append((raw, form or ""))
    return out


def _ledger_aliases(led):
    """The `aliases used for anchors:` meta line the walk writes."""
    raw = ((led or {}).get("meta") or {}).get("aliases_used_for_anchors", "")
    return [a.strip() for a in raw.split(",") if a.strip()]


def load(con=None):
    """Assemble every entity record. Returns a plain dict so a caller can
    serialise it (see the __main__ block) and a builder can read it."""
    con = con or sqlite3.connect(DB_PATH)
    done_vols = {v for v in L.walk_done()}
    vols = site_arch.load_volumes(con)
    vol_index = L.volume_index()
    title_rows = dict(con.execute("SELECT vol_id, title FROM volumes"))
    people = {c["id"]: c for c in D.characters(con)}
    db_aliases = _person_aliases(con)
    coverage = D.coverage_by_char(con)

    entities = {t: {} for t in TYPES}
    ledger_stems = {kind: set(L.all_ledgers(kind)) for kind in
                    ("people", "exams", "systems", "places", "volumes")}

    # ---------------------------------------------------------- characters
    evidence = B.transcribed()  # keyed by page id (site_bands resolves stems)
    for cid, c in people.items():
        stem = L.stem_for("people", cid)
        led = L.load("people", stem) if stem in ledger_stems["people"] else None
        scenes, quoted = evidence.get(cid, (0, 0))
        c_vols = {r["vol_id"] for r in coverage.get(cid, [])}
        aliases = [a for a, _f in db_aliases.get(cid, [])]
        aliases += _ledger_aliases(led)
        if c["canon"] and c["canon"] != c["name"]:
            aliases.append(c["canon"])
        entities["character"][cid] = {
            "type": "character", "id": cid,
            "display_name": c["name"],
            "aliases": _dedupe(aliases, c["name"]),
            "sort_key": sort_name(c["name"]),
            "status": char_status(scenes, c_vols, done_vols),
            "tier": c["tier"],
            "band": c["tier"],
            "parents": {"section": "people",
                        "roles": [f["label"] for f in
                                  _role_rows(con, cid, led)]},
            "href": c["href"],
            "ledger": stem if led else "",
            "scenes": scenes, "quoted_lines": quoted,
            "sources": sorted(c_vols),
        }
    # a ledger whose stem the roster does not carry (tachibana) still resolves
    for stem in ledger_stems["people"]:
        cid = L.page_id_for("people", stem)
        if cid in entities["character"]:
            continue
        led = L.load("people", stem)
        scenes, quoted = evidence.get(cid, (0, 0))
        name = site_arch.display_name((led or {}).get("title", ""), cid)
        letter = (name.split()[0][:1].upper() if name else cid[:1].upper())
        entities["character"][cid] = {
            "type": "character", "id": cid, "display_name": name,
            "aliases": _dedupe(_ledger_aliases(led), name),
            "sort_key": sort_name(name),
            "status": char_status(scenes, set(), done_vols),
            "tier": B.band_for(B.MINOR, scenes, quoted), "band": 3,
            "parents": {"section": "people", "roles": []},
            "href": f"people/minor/{letter.lower()}.html#{cid}",
            "ledger": stem, "scenes": scenes, "quoted_lines": quoted,
            "sources": [],
        }

    # ------------------------------------------------------------- volumes
    for vol_id, v in vols.items():
        blocks = (vol_index.get(vol_id) or {}).get("blocks", 0)
        chapters = len(D.volume_ledger(vol_id))
        entities["volume"][vol_id] = {
            "type": "volume", "id": vol_id,
            "display_name": v["label"],
            "short_label": v["short"],
            "title": title_rows.get(vol_id, ""),
            "aliases": [v["short"], v["id"]] if v["short"] != v["label"] else [v["id"]],
            "sort_key": v["order"],
            "status": volume_status(vol_id, done_vols, blocks, chapters),
            "tier": None,
            "parents": {"year": v["year"], "kind": v["kind"]},
            "href": f"story/v/{vol_id}/index.html",
            "ledger": "volumes" if vol_id in ledger_stems["volumes"] else "",
            "blocks": blocks, "chapters": chapters,
            "pages": v["pages"],
            "sources": [vol_id],
        }

    # --------------------------------------------------------------- exams
    pack = D.exams(con)
    for e in pack["list"]:
        stem = L.stem_for("exams", e["id"])
        led = L.load("exams", stem) if stem in ledger_stems["exams"] else None
        inst_vols = sorted({i["vol_id"] for i in e["instances"] if i["vol_id"]})
        order = min((vols[v]["order"] for v in inst_vols if v in vols),
                    default=vols.get(e["first_vol"], {}).get("order", 999))
        entities["exam"][e["id"]] = {
            "type": "exam", "id": e["id"], "display_name": e["name"],
            "aliases": _dedupe(_db_aliases(con, "exam_aliases", "exam_id", e["id"]),
                               e["name"]),
            "sort_key": order,
            "status": ledger_status(led, done_vols),
            "tier": None,
            "parents": {"section": "school"},
            "href": f"school/exam/{e['id']}.html",
            "ledger": stem if led else "",
            "sources": inst_vols,
            "instances": len(e["instances"]),
        }

    # ------------------------------------------------------------- systems
    for s in D.systems(con):
        stem = L.stem_for("systems", s["id"])
        led = L.load("systems", stem) if stem in ledger_stems["systems"] else None
        entities["system"][s["id"]] = {
            "type": "system", "id": s["id"], "display_name": s["name"],
            "aliases": _dedupe(_db_aliases(con, "system_aliases", "sys_id", s["id"]),
                               s["name"]),
            "sort_key": fold(s["name"]),
            "status": ledger_status(led, done_vols),
            "tier": None,
            "parents": {"section": "school"},
            "href": f"school/system/{s['id']}.html",
            "ledger": stem if led else "",
            "sources": sorted(_ledger_vols(led)),
        }

    # -------------------------------------------------------------- places
    for p in D.locations(con):
        stem = L.stem_for("places", p["id"])
        led = L.load("places", stem) if stem in ledger_stems["places"] else None
        entities["place"][p["id"]] = {
            "type": "place", "id": p["id"], "display_name": p["name"],
            "aliases": _dedupe(_db_aliases(con, "location_aliases", "loc_id", p["id"]),
                               p["name"]),
            "sort_key": fold(p["name"]),
            "status": ledger_status(led, done_vols),
            "tier": None,
            "parents": {"section": "world"},
            "href": f"world/{p['id']}.html",
            "ledger": stem if led else "",
            "sources": sorted(_ledger_vols(led)),
        }

    # -------------------------------------------------------------- topics
    from site_topics import TOPICS  # deferred: site_topics imports site_shell
    evidence_vols = set(vol_index)
    closed = evidence_vols <= done_vols
    for t in TOPICS:
        entities["topic"][t["id"]] = {
            "type": "topic", "id": t["id"], "display_name": t["title"],
            "aliases": [], "sort_key": fold(t["title"]),
            "status": "complete" if closed else "partial",
            "tier": None, "parents": {"section": "topics"},
            "href": f"topics/{t['id']}.html",
            "ledger": "", "sources": sorted(evidence_vols),
        }

    # --------------------------------------------------------------- years
    for year in sorted({v["year"] for v in vols.values()}):
        ys = [v for v in vols.values() if v["year"] == year]
        label = ("Side stories" if year == 0 else f"Year {year}")
        entities["year"][f"y{year}"] = {
            "type": "year", "id": f"y{year}", "display_name": label,
            "aliases": [], "sort_key": year,
            "status": ("complete" if all(volume_status(v["id"], done_vols,
                                                      (vol_index.get(v["id"]) or {}).get("blocks", 0),
                                                      len(D.volume_ledger(v["id"]))) == "complete"
                                        for v in ys) else
                       ("partial" if any((vol_index.get(v["id"]) or {}).get("blocks") for v in ys)
                        else "stub")),
            "tier": None, "parents": {"section": "story"},
            "href": f"story/y{year}.html",
            "ledger": "", "sources": [v["id"] for v in sorted(ys, key=lambda x: x["order"])],
        }

    # ------------------------------------------------- aliases and the id map
    alias_index = {}
    ambiguous = {}
    for t in ("character", "exam", "system", "place"):
        for e in entities[t].values():
            keep = []
            for a in e["aliases"]:
                key = fold(a)
                if not key:
                    continue
                owners = alias_index.setdefault(key, [])
                if owners and owners[-1][1] != e["id"]:
                    ambiguous.setdefault(key, []).extend(owners + [(t, e["id"], a)])
                    keep.append(a)
                    continue
                owners.append((t, e["id"], a))
                keep.append(a)
            e["aliases_kept"] = keep
    # an alias owned by more than one record is searchable but is not an alias:
    # the schema forbids two entities sharing one
    for t in ("character", "exam", "system", "place"):
        for e in entities[t].values():
            shared = {fold(a) for a in e.get("aliases_kept", [])} & set(ambiguous)
            e["aliases"] = [a for a in e.get("aliases_kept", [])
                            if fold(a) not in shared]

    ids = {}
    for t, recs in entities.items():
        m = ids.setdefault(t, {})
        for eid, e in recs.items():
            m[eid] = eid
            m[e["display_name"].lower()] = eid
            for a in e["aliases"]:
                m.setdefault(fold(a), eid)
    # ledger stems resolve to the page id they belong to
    for kind in ("people", "exams", "systems", "places"):
        for stem in ledger_stems.get(kind, ()):
            target = L.page_id_for(kind == "people" and "people" or kind, stem) \
                if kind != "people" else L.page_id_for("people", stem)
            t = {"people": "character", "exams": "exam",
                 "systems": "system", "places": "place"}[kind]
            ids.setdefault(t, {})[stem] = target

    return {
        "schema": SCHEMA,
        "entities": entities,
        "ids": ids,
        "ambiguous": ambiguous,
        "done_volumes": sorted(done_vols),
        "ledger_stems": {k: sorted(v) for k, v in ledger_stems.items()},
    }


def _role_rows(con, cid, led):
    """Role bucket keys a ledger states, as human labels."""
    import site_roles
    out = []
    for section in (led or {}).get("vols") or []:
        for block in section["blocks"]:
            for e in block["entries"]:
                if e["marker"] == "role" and e["target"]:
                    out.append({"label": site_roles.bucket_label(e["target"])})
    return out


def _db_aliases(con, table, col, eid):
    return [r[0] for r in con.execute(
        f"SELECT raw_form FROM {table} WHERE {col} = ? "
        f"AND COALESCE(is_noise, 0) = 0", (eid,)) if r[0]]


def _dedupe(items, name):
    out, seen = [], {fold(name)}
    for a in items:
        k = fold(a)
        if k and k not in seen:
            seen.add(k)
            out.append(a)
    return out


def find(reg, kind, token):
    """Resolve an id, a display name, an alias or a ledger stem to one id."""
    return reg["ids"].get(kind, {}).get(token) or \
        reg["ids"].get(kind, {}).get(token.lower()) or \
        reg["ids"].get(kind, {}).get(fold(token))


def all_of(reg, kind, sort=True):
    recs = list(reg["entities"].get(kind, {}).values())
    if sort:
        recs.sort(key=lambda e: (e["sort_key"], e["display_name"]))
    return recs


def names_in_use(reg):
    """[(type, id, display, [(spelling, source)])] for every record whose
    display name is not the only spelling that reaches a reader. Used to write
    the decision list in docs/SCHEMA.md, never to pick a spelling."""
    out = []
    for t in ("character", "exam", "system", "place", "volume"):
        for e in reg["entities"].get(t, {}).values():
            variants = [(e["display_name"], "display")]
            for a in e["aliases"]:
                if fold(a) != fold(e["display_name"]):
                    variants.append((a, "alias"))
            if len({fold(v) for v, _s in variants}) > 1:
                out.append((t, e["id"], variants))
    return out


if __name__ == "__main__":
    reg = load()
    for t in TYPES:
        recs = reg["entities"].get(t, {})
        if recs:
            print(f"{t:10} {len(recs):4} records · status "
                  + " ".join(f"{s}={sum(1 for e in recs.values() if e['status'] == s)}"
                             for s in ("stub", "partial", "complete")))
    print(f"\nledger stems: " + " ".join(
        f"{k}={len(v)}" for k, v in reg["ledger_stems"].items()))
    print(f"ambiguous aliases (searchable, not redirects): {len(reg['ambiguous'])}")
    for k, owners in sorted(reg["ambiguous"].items())[:20]:
        print("  ", k, "→", sorted({o[1] for o in owners}))

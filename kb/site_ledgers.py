#!/usr/bin/env python3
"""The walk ledger is the only public content source.

Why one source: everything the site used to render out of `dossiers/` and the
pre-walk database prose layers (status_timeline, the exam/system/claim
analysis) was written from whole-series memory before any volume had been read
line by line. That layer carried fabricated lines and unsourced claims, so it
is out of the build. A ledger entry, by contrast, is only ever written with a
page anchor next to it, and the quote-fidelity gate proves the anchored lines
against the text files.

Ledger grammar (written by the walk, append-only):

    # Kushida Kikyō — walk ledger
    char_id: kushida-kikyou · class: Class 1-D · status: main
    ## y1v1                                  <- volume section
    <!-- walk: y1v1 → start -->              <- progress marker, not content
    ### y1v1 p.19–24 — Bus: the public champion   <- scene block
    [scene] Crowded city bus ...             <- typed entry
    [says] (p.21) “Um… I think that the lady is right.”
    [rel:kouenji-rokusuke] (p.21) Direct moral clash.
    [note] (p.19–24) The text never names her here — inference.

Nothing else renders: a page either shows scene blocks from here, mechanical
facts from the database (counts, lengths, which volumes a name appears in), or
says plainly that the volume has not been worked through yet.
"""

import re
from pathlib import Path

import site_arch

ROOT = Path(__file__).resolve().parent.parent
LEDGERS = ROOT / "ledgers"

KINDS = ("people", "exams", "systems", "places", "concepts", "volumes")

H1_RE = re.compile(r"^# (.+?)\s*$", re.M)
VOL_RE = re.compile(r"^##\s+(y\d+v[\d.]+|y0)\s*$", re.M)
BLOCK_RE = re.compile(r"^###\s+(.+?)\s*$", re.M)
MARKER_RE = re.compile(r"^\[([a-z]+)(?::([A-Za-z0-9._-]+))?\]\s*(.*)$")
PAGES_PREFIX_RE = re.compile(r"^\((p\.[^)]*)\)\s*")
PAGES_RE = re.compile(r"p\.(\d+)")
VOL_IN_HEADING_RE = re.compile(r"^(y\d+v[\d.]+|y0)\s+(.*)$")
PAGES_IN_HEADING_RE = re.compile(r"^(.*?)\s+((?:p\.[^—]|[0-9,–\-–— ])*?)\s*—\s*(.*)$")
META_RE = re.compile(r"^[a-z_][a-z_ ]*(?:used for anchors)?:\s*(.*)$")
SEP_RE = re.compile(r"\s+·\s+")

# Pipeline bookkeeping lines: a progress stamp or a coverage tally addressed
# to whoever reads the ledger file, never to a reader of the site. They are
# dropped before any prose is rendered.
BOOKKEEPING_RE = re.compile(
    r"^(walk|coverage|chunks?|progress)\s*:", re.I)

# what each marker contributes to a reader-facing page: (group, label)
MARKERS = {
    "scene": ("scene", "Scene"),
    "action": ("action", "What happens"),
    "says": ("line", "Spoken"),
    "say": ("line", "Spoken"),
    "ask": ("line", "Asked"),
    "think": ("thought", "Inner voice"),
    "thinks": ("thought", "Inner voice"),
    "narrates": ("thought", "Narration"),
    "feat": ("feat", "Feat"),
    "trait": ("trait", "Trait"),
    "voice": ("voice", "Voice"),
    "status": ("status", "Position"),
    "back": ("back", "Backstory"),
    "trivia": ("detail", "Detail"),
    "rule": ("rule", "Rule"),
    "number": ("number", "Numbers"),
    "result": ("result", "Result"),
    "place": ("place", "The place"),
    "rel": ("relation", "Relationship"),
    "note": ("note", "Caveat"),
    "flag": ("note", "Unverified"),
}

# entries whose text is a verbatim line from the book
QUOTE_MARKERS = {"says", "say", "ask", "thinks", "think", "narrates"}


def marker_info(marker, target):
    group, label = MARKERS.get(marker, ("detail", marker.replace("_", " ").title()))
    return group, label, target


def pages_of(text):
    """Page numbers carried by an entry or a scene-block heading, in order."""
    return [int(n) for n in PAGES_RE.findall(text or "")]


def page_label(text):
    """'p.21' / 'p.21–22' / 'p.156, 171–180' out of an entry or heading."""
    m = re.search(r"\((p\.[^)]*)\)", text or "")
    if m:
        return m.group(1)
    m = re.search(r"\bp\.[^—]*", text or "")
    return m.group(0).strip().rstrip(",") if m else ""


# A volume key used as a word inside a note ("her y1v2 arc") is file shorthand,
# not something a reader uses. Keys that belong to a citation ("y1v1 p.247")
# are left alone so the citation can still be turned into a page chip.
VOL_WORD_RE = re.compile(r"\b(y0|y[123]v\d+(?:\.\d+)?)(?!\s+pp?\.?\s*\d)")


def humanize(text):
    """Ledger shorthand -> the labels the site shows everywhere else."""
    if not text:
        return text
    return VOL_WORD_RE.sub(lambda m: site_arch.volume_short(m.group(1)), text)


def _entries(lines):
    """Typed entry lines with their continuations, in file order."""
    out = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        # A heading of any level belongs to the file's structure, not to the
        # scene it follows; "## y1v1 WALK COMPLETE" style stamps stay internal.
        if stripped.startswith("#"):
            continue
        if BOOKKEEPING_RE.match(stripped):
            continue
        m = MARKER_RE.match(stripped)
        if m:
            marker, target, rest = m.group(1), m.group(2) or "", m.group(3)
            pages = ""
            pm = PAGES_PREFIX_RE.match(rest)
            if pm:
                pages = pm.group(1)
                rest = rest[pm.end():]
            out.append({"marker": marker, "target": target,
                        "pages": pages, "text": humanize(rest.strip()),
                        "quote": marker in QUOTE_MARKERS})
        elif out:
            prev = out[-1]
            bullet = humanize(re.sub(r"^[-*]\s+", "", stripped))
            prev["text"] = f'{prev["text"]}\n{bullet}'.strip()
        else:
            out.append({"marker": "note", "target": "", "pages": "",
                        "text": humanize(stripped), "quote": False})
    return out


def parse(text):
    """Ledger text -> {title, meta, vols:[{vol, blocks:[{...}]}]}."""
    h1 = H1_RE.search(text)
    body = text
    if h1:
        body = text[h1.end():]
    meta = {}
    head = body.split("\n## ", 1)[0]
    for line in head.splitlines():
        s = line.strip()
        if not s or s.startswith("<!--"):
            continue
        for part in SEP_RE.split(s):
            m = META_RE.match(part.strip())
            if m:
                key = part.split(":", 1)[0].strip()
                val = part[len(key) + 1:].strip()
                meta.setdefault(key.replace(" ", "_"), val)
            elif meta and s and not part.startswith(("aliases",)):
                continue
    vols = []
    for vm in VOL_RE.finditer(body):
        vol_id = vm.group(1)
        start = vm.end()
        nxt = VOL_RE.search(body, start)
        section = body[start:nxt.start() if nxt else len(body)]
        blocks = []
        heads = list(BLOCK_RE.finditer(section))
        for i, bm in enumerate(heads):
            stop = heads[i + 1].start() if i + 1 < len(heads) else len(section)
            raw = section[bm.end():stop]
            heading = bm.group(1)
            hm = VOL_IN_HEADING_RE.match(heading)
            pages = ""
            title = heading
            if hm:
                pages_all = PAGES_IN_HEADING_RE.match(hm.group(2))
                title = heading.split("—", 1)[-1].strip() if "—" in heading else heading
                pages = page_label(hm.group(2)) or ""
            blocks.append({
                "vol": vol_id,
                "pages": pages,
                "page_list": pages_of(pages or heading),
                "title": humanize(title or heading),
                "heading": heading,
                "entries": _entries(raw.splitlines()),
            })
        if blocks:
            vols.append({"vol": vol_id, "blocks": blocks})
    return {"title": h1.group(1) if h1 else "", "meta": meta, "vols": vols}


def path_for(kind, stem):
    return LEDGERS / kind / f"{stem}.md"


# The walk names an entity ledger after the id it wrote into that ledger; the
# database keys its page on its own id. When the two differ the page still has
# exactly one URL (the database's) and exactly one ledger (the walk's), and
# this table is the only place that knows the pairing. Adding a volume to the
# walk means adding a row here if its ledger id and the database id disagree.
LEDGER_ALIAS = {
    "exams": {"midterm-final-written": "midterm-exam"},
    "systems": {"private-points": "point-economy"},
    "places": {"library": "school-library"},
}


def stem_for(kind, page_id):
    """The ledger file that backs the page for this database id."""
    return LEDGER_ALIAS.get(kind, {}).get(page_id, page_id)


def page_id_for(kind, stem):
    """Inverse of stem_for(): which page a ledger's entries belong to."""
    alias = LEDGER_ALIAS.get(kind, {})
    return {v: k for k, v in alias.items()}.get(stem, stem)


def exists(kind, stem):
    return path_for(kind, stem).exists()


def exists_for(kind, page_id):
    return exists(kind, stem_for(kind, page_id))


def load(kind, stem):
    p = path_for(kind, stem)
    if not p.exists():
        return None
    return parse(p.read_text(encoding="utf-8"))


def load_for(kind, page_id):
    """Load the ledger behind a page id, following LEDGER_ALIAS."""
    return load(kind, stem_for(kind, page_id))


def all_ledgers(kind):
    """Every ledger of one kind: {stem: parsed}."""
    d = LEDGERS / kind
    if not d.exists():
        return {}
    return {p.stem: parse(p.read_text(encoding="utf-8"))
            for p in sorted(d.glob("*.md"))}


def scan(kinds=("people", "exams", "systems", "places", "concepts")):
    """Every ledger entry in the project: (kind, stem, vol, block, entry).

    Topic pages are questions that cut across the ledger, so they read this
    instead of the old analysis tables. Nothing is paraphrased on the way."""
    cache = {k: all_ledgers(k) for k in kinds}
    for kind in kinds:
        for stem, led in cache[kind].items():
            for section in led["vols"]:
                for block in section["blocks"]:
                    for entry in block["entries"]:
                        if entry["text"]:
                            yield kind, stem, section["vol"], block, entry


def volume_index():
    """Which volumes the walk has actually written up, and what was written.

    Returns {vol_id: {"people": [stem…], "exams": […], "systems": […],
                      "places": […], "blocks": total scene blocks}}.
    A volume with no key here has no evidence on the site at all."""
    out = {}
    for kind in ("people", "exams", "systems", "places", "concepts"):
        for stem, led in all_ledgers(kind).items():
            for section in led["vols"]:
                rec = out.setdefault(section["vol"], {
                    "people": [], "exams": [], "systems": [], "places": [],
                    "concepts": [], "blocks": 0})
                if kind in rec and stem not in rec[kind]:
                    rec[kind].append(stem)
                rec["blocks"] += len(section["blocks"])
    for stem in all_ledgers("volumes"):
        rec = out.setdefault(stem, {"people": [], "exams": [], "systems": [],
                                    "places": [], "concepts": [], "blocks": 0})
        rec["volume_ledger"] = True
    for rec in out.values():
        rec.setdefault("volume_ledger", False)
    return out


def walked_vols():
    return set(volume_index())


if __name__ == "__main__":
    import json
    vi = volume_index()
    print(f"volumes with evidence: {sorted(vi)}")
    for vol, rec in sorted(vi.items()):
        print(f"  {vol}: {rec['blocks']} blocks · people={len(rec['people'])} "
              f"exams={rec['exams']} systems={rec['systems']} places={rec['places']} "
              f"volume_ledger={rec['volume_ledger']}")
    led = load("people", "kushida-kikyou")
    print(json.dumps(led["vols"][0]["blocks"][0], indent=1, ensure_ascii=False)[:900])

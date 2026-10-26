#!/usr/bin/env python3
"""Information architecture for the encyclopedia site — the single place
that decides what sections exist, what they are called in public, and how
a volume id or a character id becomes a human-readable label.

Nothing here renders HTML. kb/site_shell.py and kb/site_sections.py build
on this spec; kb/build_share_site.py orchestrates them. The old build
derived its navigation from the order of links inside the dossier
indexes, which is how internal database taxonomy (main / mid / background,
"allies", "rivals") leaked into the public site; the spec below replaces
that with reader-facing structure.

Volume ids (y1v2, y2v12.5, y0) are the citation keys used in the corpus
and stay valid as machine tokens; they are only ever shown to readers
inside a citation chip, never as a section name.
"""

import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "cote_kb.db"

SECTIONS = [
    {
        "id": "people",
        "label": "People",
        "href": "people/index.html",
        "line": "Who is who — every named character, with their moments.",
        "blurb": "Profiles, arcs, relationships and verbatim lines for "
                 "every named character, each claim tied to a volume and "
                 "page.",
    },
    {
        "id": "story",
        "label": "Story",
        "href": "story/index.html",
        "line": "Read it in order — year by year, volume by volume.",
        "blurb": "The chronological spine: what happens in each volume, "
                 "which exams run inside it, who is present, and the "
                 "scene-by-scene transcripts where they exist.",
    },
    {
        "id": "school",
        "label": "Exams & School",
        "href": "school/index.html",
        "line": "The rules, the point maths, every exam.",
        "blurb": "Each exam and school system with its rules, its numbers, "
                 "and every time it was run — with the page it happened on.",
    },
    {
        "id": "world",
        "label": "World & Places",
        "href": "world/index.html",
        "line": "Where things happen, and why there.",
        "blurb": "Campus, city, and the places beyond them — layout, "
                 "narrative role, and the scenes that use them.",
    },
    {
        "id": "topics",
        "label": "Topics",
        "href": "topics/index.html",
        "line": "Answers to the questions people actually ask.",
        "blurb": "Cross-cutting pages: expulsions, the point economy, "
                 "who knew what and when, relationships, feats.",
    },
    {
        "id": "guides",
        "label": "Start here",
        "href": "guides/index.html",
        "line": "Pick the way you read: writer, number-cruncher, or rusty.",
        "blurb": "Three doors into the library — one for writers, one for "
                 "powerscalers, one for 'I forgot that thing'.",
    },
    {
        "id": "appendix",
        "label": "Appendix",
        "href": "appendix/index.html",
        "line": "Citations, coverage, downloads.",
        "blurb": "How to read a citation, which volumes the evidence covers "
                 "so far, and the PDF bundles.",
    },
]

SECTION_BY_ID = {s["id"]: s for s in SECTIONS}

# Path prefixes that are always read from the site root. Builders may write a
# body link as "world/rooftop.html" without knowing how deep its own page
# sits; site_shell.resolve_links rebases these against the page being
# written, so the navigation depth lives in exactly one place.
SITE_ROOTS = tuple(f"{s['id']}/" for s in SECTIONS) + ("assets/", "pdfs/")

TIER_LABEL = {
    1: "Principal character",
    2: "Recurring character",
    3: "Minor character",
    4: "Minor character",
}

GROUP_LABEL = {
    "allies": "Allies",
    "authority": "Faculty & student council",
    "peers": "Classmates",
    "rivals": "Rivals",
    "family": "Family & the White Room",
    "outside": "Outside the school",
    "main": "Principal characters",
    "background": "Minor characters",
}

NAME_FIX = {
    "Ayanokouji Kiyotaka": "Ayanokōji Kiyotaka",
    "Ayanokouji Atsuomi": "Ayanokōji Atsuomi",
    "Horikita Suzune": "Horikita Suzune",
    "Horikita Manabu": "Horikita Manabu",
    "Kushida Kikyou": "Kushida Kikyō",
    "Karuizawa Kei": "Karuizawa Kei",
    "Sakayanagi Arisu": "Sakayanagi Arisu",
    "Ichinose Honami": "Ichinose Honami",
    "Ryuuen Kakeru": "Ryūen Kakeru",
    "Sudou Ken": "Sudō Ken",
    "Hirata Yousuke": "Hirata Yōsuke",
    "Sakura Airi": "Sakura Airi",
    "Ike Kanji": "Ike Kanji",
    "Yamauchi Haruki": "Yamauchi Haruki",
    "Kouenji Rokusuke": "Kōenji Rokusuke",
    "Chabashira Sae": "Chabashira Sae",
    "Hoshinomiya Chie": "Hoshinomiya Chie",
    "Tsubaki Sakurako": "Tsubaki Sakurako",
    "Mashima Tomonari": "Mashima Tomonari",
    "Nagumo Miyabi": "Nagumo Miyabi",
    "Katsuragi Kouhei": "Katsuragi Kōhei",
    "Hashimoto Masayoshi": "Hashimoto Masayoshi",
    "Ishizaki Daichi": "Ishizaki Daichi",
    "Nanase Tsubasa": "Nanase Tsubasa",
    "Housen Kazuomi": "Hōsen Kazuomi",
    "Yagami Takuya": "Yagami Takuya",
    "Shiina Hiyori": "Shiina Hiyori",
    "Amasawa Ichika": "Amasawa Ichika",
}

NO_MACRON = {"atsuomi", "yuitsu", "nonomura", "kuyou"}


# ------------------------------------------------------- public wording
#
# The corpus and the curated records are written for the archive, in the
# vocabulary of the pipeline that built it. These two tables are the only
# place that decides what a reader is shown instead. PROSE_REWORD is safe for
# a single line of text (verified: 'dossier', 'tier' and the pipeline markers
# have zero hits in the novel text, so no verbatim quote can be altered).
# DOC_REWORD is for whole authored documents and uses line-anchored patterns.

def _vol_words(m):
    return volume_label(m.group(1))


def _tier_words(m):
    return TIER_LABEL.get(int(m.group(1)), "character")


def _named_in_line(m):
    body = VOL_CITE_RE.sub(_vol_words, m.group(1))
    return f"- **Named in:** {body}"


PROSE_REWORD = [
    (re.compile(r"^(#{2,4}) (y[0-9]v[0-9.]+)$"),
     lambda m: f"{m.group(1)} {volume_label(m.group(2))}"),
    (re.compile(r"\btier (\d)\b"), _tier_words),
    (re.compile(r"\bDossiers?\b"), "Profiles"),
    (re.compile(r"\bdossiers?\b"), "profiles"),
    (re.compile(r"\bvol_id\b"), "volume"),
    # 'corpus' is archive-speak for the novels; zero hits in the text itself,
    # so replacing it can never touch a verbatim quote
    (re.compile(r"\bthe whole corpus\b"), "every volume"),
    (re.compile(r"\bthe corpus\b"), "the novels"),
    (re.compile(r"\bCorpus\b"), "The novels"),
    (re.compile(r"\bcorpus\b"), "the novels"),
    (re.compile(r"corpus surname hits (\d+)"), r"name appears \1 times"),
    (re.compile(r"\s*\[P\d[a-z]?-band\]"), ""),
    (re.compile(r"attributed lines"), "quoted lines"),
    (re.compile(r"Top mentions:"), "Where they appear most"),
    (re.compile(r"\bMention evidence\b"), "Where the name appears"),
    (re.compile(r"Gap queue \(mentioned, no (?:quoted|attributed) line\)"),
     "Mentioned but not yet transcribed"),
    (re.compile(r"Spoken in \((\d+) vols\)"), r"Volumes with quoted lines (\1)"),
    (re.compile(r"Arc timeline \(scenes per vol\)"), "Scenes per volume"),
    (re.compile(r"^## Identity$"), "## Names the book uses"),
    (re.compile(r"^## Footprint$"), "## Where they appear"),
]

DOC_REWORD = [
    (re.compile(r"^\*\*(?:Main|Mid|Background) character\*\*\s*$", re.M), ""),
    (re.compile(r"^`[^`]*mentions[^`]*`\s*$", re.M), ""),
    (re.compile(r"^-\s*\*\*Mentions:\*\*\s*(.+)$", re.M), _named_in_line),
    (re.compile(r"^- \*\*Notes:\*\*[^*\n]*"
                r"(?:shell promotion|band|corpus|seed|promotion)[^\n]*$", re.M),
     ""),
]


def public_words(text, *tables):
    """Apply wording tables in order. Never touches quote content (see note
    above), only the archive's own vocabulary."""
    for table in tables:
        for pat, rep in table:
            text = pat.sub(rep, text)
    return text

VOL_CITE_RE = re.compile(r"\b(y0|y[123]v\d+(?:\.\d+)?)\b")
PAGE_IN_CITE_RE = re.compile(
    r"\b(y0|y[123]v\d+(?:\.\d+)?)\s+(?:p{1,2}\.?\s*)(\d+)(?:\s*[–-]\s*(\d+))?",
)


def load_volumes(con):
    """{vol_id: {order,label,short,kind,pages,year,narr}} in reading order."""
    rows = con.execute(
        "SELECT vol_id, kind, chrono_order, pdf_pages FROM volumes "
        "ORDER BY chrono_order"
    ).fetchall()
    out = {}
    for vol_id, kind, order, pages in rows:
        out[vol_id] = {
            "id": vol_id,
            "order": float(order or 0),
            "kind": kind,
            "pages": int(pages or 0),
            "label": volume_label(vol_id),
            "short": volume_short(vol_id),
            "year": volume_year(vol_id),
        }
    return out


def volume_year(vol_id):
    if vol_id == "y0":
        return 0
    m = re.match(r"y([123])v", vol_id)
    return int(m.group(1)) if m else 0


def volume_number(vol_id):
    if vol_id == "y0":
        return 0
    m = re.match(r"y[123]v(\d+(?:\.\d+)?)", vol_id)
    return m.group(1) if m else "?"


def volume_short(vol_id):
    if vol_id == "y0":
        return "Side Stories"
    return f"Vol. {volume_number(vol_id)}"


def volume_label(vol_id):
    if vol_id == "y0":
        return "Side Stories (Year 0)"
    year = {1: "Year 1", 2: "Year 2", 3: "Year 3"}.get(volume_year(vol_id), "Year ?")
    return f"{year}, Volume {volume_number(vol_id)}"


def volume_kind_label(kind):
    return {
        "main": "Main story",
        "interquad": "Interlude volume",
        "side": "Side story",
    }.get(kind, "Volume")


def display_name(canonical, char_id=""):
    fixed = NAME_FIX.get(canonical or "")
    if fixed:
        return fixed
    return macronize(canonical or char_id or "Unknown")


def macronize(text):
    """Mechanical long-vowel fix for the romanisations in the database.

    'ou' → 'ō' and 'uu' → 'ū' are the regular Hepburn patterns behind the
    corpus's inconsistent spellings; a small exception list protects the
    few names where the doubled vowel spans two syllables.
    """
    if not text:
        return text
    lowered = text.lower()
    if any(exc in lowered for exc in NO_MACRON):
        return text
    out = re.sub(r"([KkHhMmNnRrSsTtYyGgDdBbPpFf])ou", lambda m: m.group(1) + "ō", text)
    out = re.sub(r"([AaEeIiOoUuYy])uu", lambda m: m.group(1) + "ū", out)
    out = out.replace("Kou", "Kō").replace("kou", "kō")
    out = re.sub(r"\bRyuuen", "Ryūen", out)
    return out


def initials_first(name):
    """'Ayanokōji Kiyotaka' → sort key on the family name."""
    parts = (name or "").split()
    if not parts:
        return ""
    return parts[0]


def cite_marker(vol_id, page):
    return f"{vol_id} p.{page}"


def parse_cites(text):
    """Every (vol_id, first_page) cited inside a blob of prose."""
    return [(m.group(1), int(m.group(2))) for m in PAGE_IN_CITE_RE.finditer(text)]


def open_db():
    return sqlite3.connect(DB_PATH)

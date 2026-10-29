#!/usr/bin/env python3
"""Which characters get a page, and what they are called — decided by evidence.

The database carries a curated `characters.tier` column written before any
volume was read line by line. It is a guess about the series, and it goes stale
in both directions: it filed Ike Kanji as a minor character even though two
volumes of notes hold twenty scenes and over a hundred quoted lines of him, and
it would keep a name with no evidence at all on a page of its own.

So the site does not read that column as the answer. It reads it as a floor —
nothing the curators called principal is demoted by an evidence count that only
covers the two volumes walked so far — and then lets what has actually been
copied off the pages promote a name:

  Principal  a volume followed through them: 40+ scenes and 300+ quoted lines
             transcribed, or the curators already called them principal
  Medium     a name the notes keep returning to: 3+ scenes or 10+ quoted lines
             transcribed, or the curators called them recurring
  Minor      named on the page, never worked through

Both bands 1 and 2 get a page of their own; band 3 stays an entry on the page
for its initial. The numbers are the whole rule, they are computed from
ledgers/people/ on every build, and a name moves up as more volumes are walked —
which is the honest behaviour for an archive that is still being filled.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arch  # noqa: E402
import site_data as D  # noqa: E402
import site_evidence as E  # noqa: E402
import site_ledgers as L  # noqa: E402

PRINCIPAL, MEDIUM, MINOR = 1, 2, 3

BAND_LABEL = {PRINCIPAL: "Principal character",
              MEDIUM: "Medium character",
              MINOR: "Minor character"}
BAND_PLURAL = {PRINCIPAL: "Principal characters",
               MEDIUM: "Medium characters",
               MINOR: "Minor characters"}
BAND_SLUG = {PRINCIPAL: "principal", MEDIUM: "medium", MINOR: "minor"}

# The bands whose members get a page of their own.
OWN_PAGE_BANDS = (PRINCIPAL, MEDIUM)

# What it takes to leave each band behind, in scenes and quoted lines copied
# off the printed pages. Kept deliberately round: the point is not a precise
# score, it is that a name with real transcribed evidence is not a footnote.
PRINCIPAL_SCENES, PRINCIPAL_LINES = 40, 300
MEDIUM_SCENES, MEDIUM_LINES = 3, 10


def transcribed():
    """{page id: (scenes, quoted lines)} for every person ledger.

    Keyed by the id the *page* uses, not the ledger's filename: a ledger whose
    stem differs from the roster id (`tachibana` / `tachibana-akane`) is the
    same person, and counting it under the stem hid its scenes from its page.
    """
    out = {}
    for stem in L.all_ledgers("people"):
        out[L.page_id_for("people", stem)] = E.evidence_count(L.load("people", stem))
    return out


def evidence_band(scenes=0, quoted=0):
    """The band the transcribed evidence alone supports."""
    if scenes >= PRINCIPAL_SCENES and quoted >= PRINCIPAL_LINES:
        return PRINCIPAL
    if scenes >= MEDIUM_SCENES or quoted >= MEDIUM_LINES:
        return MEDIUM
    return MINOR


def band_for(curated=MINOR, scenes=0, quoted=0):
    """Curated tier as a floor, evidence as the ladder. Tier 4 collapses to 3.

    `min` is the whole trick: a lower number is a higher band, so the evidence
    can lift a name out of the minor pool but no count of pages already read can
    push a principal down.
    """
    curated = min(int(curated or MINOR), MINOR)
    return min(curated, evidence_band(scenes, quoted))


def apply(ctx):
    """Rewrite every roster record's band, label and href, in place.

    Runs before any page is built, because `href` is how every other builder —
    the A–Z rail, cross-links from story and topic pages, the People index —
    finds a character, and the number of own pages depends on it.

    A person the walk wrote a ledger for but the roster has no row for is added
    to the cast list here rather than in the minor-page builder, so they appear
    in the People index and get the same band treatment as everyone else.
    """
    ev = transcribed()
    ctx["ledger_evidence"] = ev
    for c in ctx["chars"]:
        scenes, quoted = ev.get(c["id"], (0, 0))
        c["scenes"], c["quoted_lines"] = scenes, quoted
        c["band"] = band_for(c["tier"], scenes, quoted)
        c["tier"] = c["band"]
        c["href"] = D.person_href(c["id"], c["band"], c["letter"])
    by_id = ctx["char_by_id"]
    for pid in sorted(ev):
        if pid in by_id:
            continue
        scenes, quoted = ev[pid]
        led = L.load_for("people", pid)
        name = (led or {}).get("title", "").split(" — ")[0].strip()
        name = site_arch.display_name(name, pid)
        letter = (name.split()[0][:1].upper() if name else pid[:1].upper())
        band = band_for(MINOR, scenes, quoted)
        rec = {"id": pid, "name": name, "canon": "", "tier": band,
               "band": band, "status": "", "scenes": scenes,
               "quoted_lines": quoted, "quotes": 0, "quote_vols": 0,
               "coverage": 0, "letter": letter,
               "href": D.person_href(pid, band, letter)}
        ctx["chars"].append(rec)
        by_id[pid] = rec
    # Keep the cast in band order, family name inside it — the same order the
    # roster query returns, so a band's list stays presentable as one block.
    ctx["chars"].sort(key=lambda c: (c["tier"], c["name"]))
    ctx["stats"]["chars"] = len(ctx["chars"])
    ctx["band_label"] = BAND_LABEL
    return ctx


def label(char):
    """The band name a page prints, for roster and non-roster characters alike."""
    return BAND_LABEL.get(char.get("band") or char.get("tier") or MINOR,
                          "character")

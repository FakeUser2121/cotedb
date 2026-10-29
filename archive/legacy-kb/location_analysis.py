#!/usr/bin/env python3
"""P8-4: authored location prose + evidence-cited claims (apply).

python3 kb/location_analysis.py           apply LOCATIONS + CLAIMS
python3 kb/location_analysis.py --pack    evidence packs for authoring

Authored-content model (same as main_analysis): all prose lives HERE in
the LOCATIONS dict (function one-liner + notes: layout facts, narrative
importance, changes over time) and CLAIMS list (narrator_fact |
character_claim | other_reported | inference, claimant, corroboration,
confidence, refs). apply() replace-per-location into locations.function /
locations.notes and DELETE+INSERT into location_claims. Digest-excluded
tables — dossiers stay pure generated views.

Refs are "vol p.N" strings and MUST resolve to a page where this
location is mentioned (location_mentions) — hard gate, fail-before-write.
evidence_quote is auto-derived: raw corpus slice ±80 chars around the
mention span at the first ref page (verbatim by construction).

Claim ids: deterministic 28-series (loc index *100 + n), stable slugs
never renumber.

Run order: p8_init -> p8_import -> p8_mentions -> location_analysis
           -> p8_init (FTS refresh, auto-called here) ->
           build_world_dossiers.
"""

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402
from p8_init import FTS_REBUILD  # noqa: E402
from p8_import import LOCATIONS as LOC_IDS  # noqa: E402


class Claim(TypedDict):
    loc: str
    kind: str
    claimant: str
    claim: str
    perspective: str
    corroboration: str
    refs: list[str]
    confidence: float
    reliability_note: str


# loc_id -> {function, notes}
LOCATIONS: dict[str, dict[str, str]] = {
    "uninhabited-island": {
        "function": "Tropical resort island used for first-year "
                    "special exams (base camp, lodge, survival zones).",
        "notes": "First-year introduction (y1v3): students boat in for "
                 "a one-week stay at a summer lodge, then cruise "
                 "onward; the base camp splits into class zones with "
                 "school-issued safety watches (y1v3 p.30). "
                 "MTL drift: 'deserted island' (y1v3 p.14) and "
                 "'uninhabited island' (y1v3 p.26) are the same place; "
                 "corpus later keeps referencing it as the template "
                 "exam venue (367 mentions, 27 vols through y3v1).",
    },
    "white-room": {
        "function": "Underground rearing/education facility where "
                    "Ayanokouji Kiyotaka and other selected children "
                    "were trained into engineered elites.",
        "notes": "The single most referenced off-site location "
                 "(508 mentions, 24 vols, present from y0 through "
                 "y3v1) despite never being a campus site: it is "
                 "discussed, remembered and used as a threat far more "
                 "than it is visited. y1v11.5 p.159 frames it as a "
                 "temporary residence no different from a hotel — the "
                 "place Ayanokouji's father keeps returning to as a "
                 "lever.",
    },
    "keyaki-mall": {
        "function": "Shopping-and-dining complex on the school "
                    "grounds; the standard off-duty meeting spot.",
        "notes": "Defined at y1v4.5 p.12 as 'a complex on the school "
                 "grounds that students often went to'. Because "
                 "students live on campus, the mall functions as the "
                 "town square: fortune-tellers, casual dates, class "
                 "meetings on neutral ground (309 mentions, 24 vols).",
    },
    "ski-resort": {
        "function": "Hokkaido ski slopes of the second-year winter "
                    "school trip (training + skiing days).",
        "notes": "Single-volume venue (y2v8): Day 1 route is school "
                 "-> Haneda -> Shin Chitose -> ski resort -> ryokan "
                 "(y2v8 p.19 schedule box). Slopes host the trip's "
                 "training block; evenings move to the ryokan.",
    },
    "ryokan": {
        "function": "Hokkaido inn hosting the second-year winter "
                    "trip; East Wing (girls) and main building "
                    "(boys) joined by a lobby.",
        "notes": "y2v8-only (30 mentions): rooming split and lobby "
                 "layout are stated at y2v8 p.67; sightseeing legs "
                 "run from here (Sapporo Station, Sapporo Clock "
                 "Tower, y2v8 p.130). Canteen/social pressure scenes "
                 "of the trip play out in its common areas.",
    },
    "special-building": {
        "function": "Low-traffic campus building used as an alibi/"
                    "incident site in the first-year midterm cover-up.",
        "notes": "y1v2 investigation: characters weigh who 'went to "
                 "the special building on the day of the incident' — "
                 "the entrance sits in eyeshot of a witness route, "
                 "which is why the site matters (y1v2 p.75). 57 "
                 "mentions across 9 vols; thin but plot-critical.",
    },
    "student-council-room": {
        "function": "Seat of the Student Council: interrogation/"
                    "summoning venue for student discipline and "
                    "council business.",
        "notes": "Both 'room' (98) and 'office' (15) forms are the "
                 "same venue. First big use y1v2 p.209 (students "
                 "ordered to leave after council pressure); "
                 "recurring for presidential politics (y1v4.5 p.91 "
                 "summer-vacation meeting with Katsuragi). 113 "
                 "mentions / 13 vols through y3v1.",
    },
    "staff-room": {
        "function": "Teachers' workroom; the default venue for "
                    "calling a homeroom teacher to a confrontation.",
        "notes": "y1v6 p.178-179: Horikita and Ayanokouji walk in to "
                 "call Chabashira while Ryuuen's group calls "
                 "Sakagami — the parallel-call framing makes it the "
                 "neutral ground for teacher-mediated disputes. 39 "
                 "mentions / 10 vols.",
    },
    "classroom": {
        "function": "Each class's home classroom: default stage for "
                    "daily scenes, aptitude tests and in-class votes.",
        "notes": "Highest-mention venue in the corpus (1,011 "
                 "mentions / 31 vols; y3v1 alone carries 311 as the "
                 "third-year reset puts everyone back in class "
                 "frames). Almost every dialogue-heavy chapter opens "
                 "or closes here, so it doubles as the series' "
                 "narrative home position.",
    },
    "dormitory": {
        "function": "Campus residences (dorms) where every student "
                    "lives; rooms double as private-meeting sites.",
        "notes": "430 mentions / 29 vols. Dorm life carries the "
                 "logistics of the point economy (room quality "
                 "follows class standing) and half the series' "
                 "backroom conversations happen in or between dorm "
                 "rooms.",
    },
    "campus": {
        "function": "The ANHS grounds as a whole — school building, "
                    "dorms, pool/gym cluster and Keyaki Mall inside "
                    "one enclosed territory.",
        "notes": "106 mentions ('campus' 86 + 'school grounds' 20) "
                 "/ 22 vols. Students are confined to campus "
                 "outside sanctioned trips, which is what turns the "
                 "mall, dorms and rooftop into the entire social "
                 "world of the series. y1v1 p.30 states the scale "
                 "(over 600,000 m², facilities compared to a small "
                 "city) and the ID-card economy that runs it.",
    },
    "school-building": {
        "function": "Main academic building: classrooms, back "
                    "entrances and the after-school meeting corners.",
        "notes": "60 mentions / 17 vols. Its quiet backside is the "
                 "corpus's default private-confrontation spot "
                 "(Ryuuen cornering Ayanokouji at y1v10 p.318 and "
                 "p.347); routes from it lead to dorm, Keyaki Mall "
                 "or the special building. Interior life of the "
                 "building is tracked by the classroom entity.",
    },
    "gymnasium": {
        "function": "Sports and ceremony hall: entrance ceremony, "
                    "club fairs, PE and indoor exam/logistics use.",
        "notes": "228 mentions / 24 vols. Hosts the entrance "
                 "ceremony (y1v1 p.30) and the club fair in "
                 "Gymnasium No. 1 (y1v1 p.59); heavy in y2v9/"
                 "y2v9.5 (55 + 39) around festival/exam logistics. "
                 "One y0 hit is 'jungle gym' playground apparatus — "
                 "harmless prefix match, not this facility.",
    },
    "swimming-pool": {
        "function": "Indoor fifty-meter pool for swim class; also "
                    "the White Room training pool (y0) and cruise-"
                    "ship leisure pools.",
        "notes": "168 mentions / 18 vols. ANHS pool is introduced "
                 "with swim class (y1v1 p.76: Ike at the fifty-"
                 "meter pool); y0 p.136 describes a heated pool in "
                 "the White Room curriculum; the large y1v4.5/y2v4.5 "
                 "spikes (51 / 71) are cruise-ship pool scenes. "
                 "Three distinct physical pools share this token.",
    },
    "cafeteria": {
        "function": "Main student dining hall; free/cheap meal sets "
                    "matter to the point economy.",
        "notes": "82 mentions / 15 vols. Default lunch destination "
                 "(Hirata's group, y1v1 p.55); the free vegetable "
                 "meal set is a running yardstick of student "
                 "budgets (y1v1 p.110).",
    },
    "library": {
        "function": "Quiet study venue: the original study-group "
                    "home and tutoring site.",
        "notes": "130 mentions / 15 vols. Horikita proposes moving "
                 "the study group here (y1v1 p.156) and the group "
                 "takes a long table at the far end (y1v1 p.172); "
                 "later volumes lean on it for private meetings "
                 "(y2v1 21, y2v9.5 32 mentions).",
    },
    "rooftop": {
        "function": "Upper-floor roof terrace: lunchtime-open, "
                    "locked after class — the series' secret-talk "
                    "floor.",
        "notes": "102 mentions / 20 vols. y1v1 p.181 establishes "
                 "the access rule (free during lunch, locked after) "
                 "while Ayanokouji eavesdrops on Kushida through the "
                 "door; the terrace carries the y1v7/y1v7.5 "
                 "conversation cluster (36 + 23 mentions).",
    },
    "auditorium": {
        "function": "Assembly hall doubling as the school's movie "
                    "screening room during events.",
        "notes": "Thin but concrete: 7 mentions, all y1v7.5 "
                 "p.44-46 — a screening night (couples seated, "
                 "commercial before the feature) where Ayanokouji "
                 "watches the film next to Ibuki. No other volume "
                 "uses the venue.",
    },
    "guidance-office": {
        "function": "Guidance counsellor's office — Manabu "
                    "Horikita's recruitment room.",
        "notes": "Exactly 1 mention (y1v1 p.141): summoned here, "
                 "Ayanokouji is asked to join Horikita's group — "
                 "the offer he declines. Thin by count, pivotal by "
                 "plot: the series' first cross-class invitation "
                 "happens inside this room.",
    },
    "convenience-store": {
        "function": "Campus store for snacks, bread and daily "
                    "supplies; default solo-running errand site.",
        "notes": "120 mentions / 21 vols. First shown as "
                 "Ayanokouji's solo bread run where he collides "
                 "with Horikita (y1v1 p.41-43); pairs with the "
                 "cafeteria as the two food economies. One y0 hit "
                 "is generic city retail, not the campus store.",
    },
    "infirmary": {
        "function": "School nurse's office: injured or unwell "
                    "students are processed here.",
        "notes": "19 mentions / 6 vols. y1v5 p.144 walks straight "
                 "'to the nurse's office… got to the infirmary' "
                 "(both wordings, one place); Chabashira waits here "
                 "during the island-exam medical beats (Kinoshita "
                 "carried in). A y0 hit is a different adult "
                 "context.",
    },
    "athletic-field": {
        "function": "Outdoor field for sports festivals and mass "
                    "distributions.",
        "notes": "Thin: 2 mentions, both y2v6 sports festival — "
                 "electronic scoreboard tracking class standings "
                 "(p.250) and boxed-lunch pickup (p.255). Other "
                 "field events are narrated without this exact "
                 "form, so anchors stay minimal.",
    },
    "cruise-ship": {
        "function": "Passenger liner: second week of the first-year "
                    "island trip and the Cruise Ship Special Exam "
                    "stage.",
        "notes": "78 mentions / 16 vols. Trip structure per y1v3 "
                 "p.14: one week island lodge, one week 'enjoy the "
                 "cruise ship'; later volumes reference the Cruise "
                 "Ship Special Exam as canonical exam history "
                 "(y1v10 p.143, p.337 — the Manabe/Kei incident). "
                 "y2v4.5 (19 mentions) is a retrospective wave.",
    },
    "haneda-airport": {
        "function": "Tokyo departure airport of the y2v8 winter "
                    "trip (class buses -> flight north).",
        "notes": "Thin: 4 mentions, all y2v8 — schedule box p.19, "
                 "exam rules p.23, boarding sequence p.46/p.49 "
                 "(class-bus to flight transfer, group-based "
                 "processing in the lobby).",
    },
    "shin-chitose-airport": {
        "function": "Hokkaido arrival airport of the y2v8 winter "
                    "trip (flight from Haneda, buses to ski "
                    "resort).",
        "notes": "Thin: 2 mentions (y2v8 p.19 schedule, p.46 "
                 "itinerary) — arrival leg before local buses to "
                 "the slopes. Spelled 'Shin-Chitose'/'ShinChitose' "
                 "in different MTL passages; matcher accepts both.",
    },
    "tokyo": {
        "function": "Capital-region backdrop: y0 political/business "
                    "setting and later travel references.",
        "notes": "20 mentions / 11 vols, concentrated in y0 (7: "
                 "factories, University of Tokyo graduates, virtual "
                 "city walks) with scattered y1/y2 name-checks. ANHS "
                 "itself is never pinned to a city district in the "
                 "corpus, so Tokyo stays an off-site backdrop.",
    },
    "hokkaido": {
        "function": "Northern trip destination: winning school-trip "
                    "choice, then the y2v8 venue.",
        "notes": "56 mentions / 4 vols: y1v4 (Hokkaido-ben dialect "
                 "gag, not a visit), y2v5 ballot (25 — Hokkaido vs "
                 "Kyoto vs Okinawa; Okinawa 19 / Hokkaido 17 / "
                 "Kyoto 3 first round), y2v8 trip (29), y2v9 (1). "
                 "The dialect hit is a false location — kept for "
                 "transparency.",
    },
    "sapporo": {
        "function": "Hokkaido sightseeing city of the y2v8 free "
                    "day (scavenger point locations).",
        "notes": "9 mentions, all y2v8 p.130-131: bus starts near "
                 "Sapporo Station; Clock Tower, TV Tower, Hokkaido "
                 "Museum of Modern Art (1 pt), Nakanaka Island Park "
                 "and Hokkaido Shrine (2 pt), Enmaruyama Zoo and "
                 "Central Wholesale Market among the scored stops.",
    },
}

CLAIMS: list[Claim] = [
    Claim(loc="white-room", kind="narrator_fact", claimant="narrator",
         claim="The White Room is the facility where Ayanokouji "
               "Kiyotaka spent his childhood under engineered "
               "education, and it remains his father's pressure "
               "lever against him.",
         perspective="Ayanokouji narration", corroboration="supported",
         refs=["y1v11.5 p.159", "y1v5 p.15"], confidence=0.9,
         reliability_note="Ayanokouji's own retrospective account — "
                          "first-party but self-interested."),
    Claim(loc="keyaki-mall", kind="narrator_fact", claimant="narrator",
         claim="Keyaki Mall is a complex on the school grounds that "
               "students often visited, functioning as the campus's "
               "commercial centre.",
         perspective="Ayanokouji narration", corroboration="supported",
         refs=["y1v4.5 p.12"], confidence=0.95,
         reliability_note="Direct definitional narration."),
    Claim(loc="uninhabited-island", kind="narrator_fact",
         claimant="narrator",
         claim="The island exam opens with first-years staying a week "
               "at a summer lodge on a deserted island before "
               "boarding a cruise ship for the second week.",
         perspective="Ayanokouji narration", corroboration="supported",
         refs=["y1v3 p.14", "y1v3 p.26"], confidence=0.9,
         reliability_note="Schedule narration; 'deserted' and "
                          "'uninhabited' wording varies by passage."),
    Claim(loc="ryokan", kind="narrator_fact", claimant="narrator",
         claim="The winter-trip ryokan splits rooms by sex: girls in "
               "the East Wing, boys in the main building, connected "
               "by a lobby.",
         perspective="Ayanokouji narration", corroboration="supported",
         refs=["y2v8 p.67"], confidence=0.95,
         reliability_note="Layout stated directly in narration."),
    Claim(loc="special-building", kind="character_claim",
         claimant="ayanokouji-kiyotaka",
         claim="The special building is a suitable incident site "
               "because few students pass through it, yet its "
               "entrance is within eyeshot of a witness route.",
         perspective="Ayanokouji reasoning during the y1v2 "
                     "investigation", corroboration="supported",
         refs=["y1v2 p.75"], confidence=0.8,
         reliability_note="Investigative inference, argued in-scene "
                          "and not contradicted later in the volume."),
    Claim(loc="ski-resort", kind="narrator_fact", claimant="narrator",
         claim="The second-year winter trip route runs school -> "
               "Haneda Airport -> Shin Chitose Airport -> ski "
               "resort, returning to the ryokan each night.",
         perspective="Schedule box narration", corroboration="supported",
         refs=["y2v8 p.19"], confidence=0.95,
         reliability_note="Direct schedule text."),
    Claim(loc="student-council-room", kind="character_claim",
         claimant="horikita-manabu",
         claim="Summoning students to the student council room is "
               "the council's standard instrument of pressure.",
         perspective="Scene action in y1v2/y1v4.5",
         corroboration="supported", refs=["y1v2 p.209"],
         confidence=0.7,
         reliability_note="Derived from repeated scene usage rather "
                          "than an explicit rule statement."),
    Claim(loc="campus", kind="narrator_fact", claimant="narrator",
         claim="Students are effectively confined to campus: their "
               "private points and daily life are managed entirely "
               "inside school-controlled facilities.",
         perspective="Ayanokouji narration", corroboration="supported",
         refs=["y1v4.5 p.12"], confidence=0.85,
         reliability_note="Stated as the reason the mall functions "
                          "as the students' only town."),
    Claim(loc="gymnasium", kind="narrator_fact", claimant="narrator",
         claim="The gymnasium hosts whole-cohort events: the "
               "entrance ceremony and the club fair in Gymnasium "
               "No. 1 both run there in the opening volume.",
         perspective="Announcement + scene narration",
         corroboration="supported", refs=["y1v1 p.59"],
         confidence=0.9,
         reliability_note="Event announcements state the venue "
                          "directly."),
    Claim(loc="rooftop", kind="narrator_fact", claimant="narrator",
         claim="The roof is open to students during lunchtime and "
               "locked after class, which makes it usable for "
               "secret meetings only at specific hours.",
         perspective="Ayanokouji narration",
         corroboration="supported", refs=["y1v1 p.181"],
         confidence=0.9,
         reliability_note="Rule observed in passing while "
                          "eavesdropping; no later contradiction."),
    Claim(loc="library", kind="character_claim",
         claimant="horikita-suzune",
         claim="Horikita proposes the library as the study group's "
               "venue, on the condition that Ayanokouji bring his "
               "friends along.",
         perspective="Horikita speaking to Ayanokouji",
         corroboration="supported", refs=["y1v1 p.156"],
         confidence=0.85,
         reliability_note="On-page proposal; the group then meets "
                          "there (y1v1 p.172)."),
    Claim(loc="guidance-office", kind="narrator_fact",
         claimant="narrator",
         claim="Manabu Horikita uses the guidance office to summon "
               "Ayanokouji and invite him into Horikita Suzune's "
               "group — an offer Ayanokouji declines.",
         perspective="Ayanokouji narration",
         corroboration="supported", refs=["y1v1 p.141"],
         confidence=0.9,
         reliability_note="Single-page anchor; scene content is "
                          "explicit."),
    Claim(loc="cruise-ship", kind="narrator_fact", claimant="narrator",
         claim="The first-year island trip splits in two: a week at "
               "the island lodge, then a week aboard the cruise "
               "ship.",
         perspective="Schedule narration",
         corroboration="supported", refs=["y1v3 p.14"],
         confidence=0.9,
         reliability_note="Trip structure stated in narration; the "
                          "ship later hosts the named Cruise Ship "
                          "Special Exam."),
    Claim(loc="hokkaido", kind="narrator_fact", claimant="narrator",
         claim="The Unanimous Vote exam's trip ballot opens "
               "Okinawa 19 / Hokkaido 17 / Kyoto 3, and the trip "
               "ultimately runs to Hokkaido.",
         perspective="Vote-results box narration",
         corroboration="supported",
         refs=["y2v5 p.91", "y2v8 p.19"],
         confidence=0.85,
         reliability_note="Ballot numbers are box text; the final "
                          "destination follows the later exam "
                          "outcome (y2v8 schedule)."),
]

REF_RE = re.compile(r"^(?P<vol>[a-z0-9.]+) p\.(?P<page>\d+)$")


def load_context():
    """mention pages per (loc, vol, page) + raw page text cache."""
    con = sqlite3.connect(DB_PATH)
    mentions = {}
    for loc, vol, page, s, e in con.execute(
            "SELECT loc_id, vol_id, pdf_page, span_start, span_end "
            "FROM location_mentions"):
        mentions.setdefault((loc, vol, page), []).append((s, e))
    con.close()
    pages = {}
    for vol, _stem, page, pstart, text in iter_pages():
        pages[(vol, page)] = (pstart, text)
    return mentions, pages


def evidence_for(loc, refs, mentions, pages):
    for ref in refs:
        m = REF_RE.match(ref.strip())
        if not m:
            return None, f"bad ref format {ref!r}"
        vol, page = m.group("vol"), int(m.group("page"))
        spans = mentions.get((loc, vol, page))
        if spans is None:
            return None, f"no mention of {loc} at {vol} p.{page}"
        bounds = pages.get((vol, page))
        if bounds is None:
            return None, f"unknown page {vol} p.{page}"
        pstart, text = bounds
        s, e = spans[0]
        a = max((s - pstart) - 80, 0)
        b = min((e - pstart) + 80, len(text))
        quote = text[a:b]
        if not quote.strip():
            return None, f"empty evidence slice at {vol} p.{page}"
        return quote, None
    return None, "no valid refs"


def main():
    pack = "--pack" in sys.argv
    con = sqlite3.connect(DB_PATH)
    known = {r for r, in con.execute("SELECT loc_id FROM locations")}

    if pack:
        _mentions, pages = load_context()
        chrono = [v for v, in con.execute(
            "SELECT vol_id FROM volumes ORDER BY chrono_order")]
        for loc_id, name, _kind, _a in LOC_IDS:
            counts = con.execute(
                "SELECT vol_id, count(*) FROM location_mentions "
                "WHERE loc_id=? GROUP BY vol_id", (loc_id,)).fetchall()
            print(f"=== {loc_id} ({name}) — "
                  f"{sum(c for _v, c in counts)} mentions ===")
            print("  by vol:", ", ".join(f"{v}:{c}" for v, c in sorted(
                counts, key=lambda x: chrono.index(x[0]))))
            samples = con.execute(
                "SELECT vol_id, pdf_page, span_start, span_end "
                "FROM location_mentions WHERE loc_id=? "
                "ORDER BY vol_id, pdf_page LIMIT 5", (loc_id,)).fetchall()
            for vol, page, s, e in samples:
                pstart, text = pages[(vol, page)]
                frag = re.sub(r"\s+", " ", text[
                    max(0, s - pstart - 70):e - pstart + 70])
                print(f"  {vol} p.{page}: …{frag}…")
        con.close()
        return 0

    # validate authored content before any write
    errors = []
    for loc_id in LOCATIONS:
        if loc_id not in known:
            errors.append(f"LOCATIONS: unknown loc {loc_id}")
    loc_index = {l: i for i, (l, _n, _k, _a) in enumerate(LOC_IDS)}
    for n, c in enumerate(CLAIMS, start=1):
        if c["loc"] not in known:
            errors.append(f"CLAIMS: unknown loc {c['loc']}")
        if c["kind"] not in ("narrator_fact", "character_claim",
                             "other_reported", "inference"):
            errors.append(f"CLAIMS: bad kind {c['kind']}")
        if not (0 < c["confidence"] <= 1):
            errors.append(f"CLAIMS: confidence {c['confidence']}")
        if not c["refs"]:
            errors.append(f"CLAIMS {c['loc']}: no refs")
    if errors:
        for e in errors:
            print("location_analysis:", e)
        con.close()
        return 1

    mentions, pages = load_context()
    evidence = {}
    for n, c in enumerate(CLAIMS, start=1):
        quote, err = evidence_for(c["loc"], c["refs"], mentions, pages)
        if err:
            print(f"location_analysis: claim {c['loc']} — {err}")
            con.close()
            return 1
        evidence[n] = quote

    for loc_id, prose in LOCATIONS.items():
        con.execute(
            "UPDATE locations SET function=?, notes=? WHERE loc_id=?",
            (prose["function"], prose["notes"], loc_id))
    con.execute("DELETE FROM location_claims")
    applied = 0
    for n, c in enumerate(CLAIMS, start=1):
        claim_id = loc_index[c["loc"]] * 100 + n
        first = REF_RE.match(c["refs"][0].strip())
        if first is None:
            print(f"location_analysis: claim {c['loc']} bad first ref")
            con.close()
            return 1
        con.execute(
            "INSERT INTO location_claims (claim_id, loc_id, claim, kind, "
            "claimant, perspective, corroboration, corroboration_refs, "
            "reliability_note, confidence, vol_id, pdf_page, span_start, "
            "span_end, evidence_quote) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (claim_id, c["loc"], c["claim"], c["kind"], c["claimant"],
             c["perspective"], c["corroboration"],
             json.dumps(c["refs"]), c["reliability_note"],
             c["confidence"], first.group("vol"),
             int(first.group("page")), None, None, evidence[n]))
        applied += 1
    con.executescript(FTS_REBUILD)
    con.commit()
    n_notes = con.execute(
        "SELECT count(*) FROM locations WHERE notes IS NOT NULL"
    ).fetchone()[0]
    con.close()
    print(f"location_analysis: applied {len(LOCATIONS)} prose rows "
          f"({n_notes} locations with notes)  {applied} claims  fts ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

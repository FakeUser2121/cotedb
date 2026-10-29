#!/usr/bin/env python3
"""P9-5: authored exam/system prose + instances + evidence-cited claims.

python3 kb/p9_analysis.py           apply PROSE + INSTANCES + CLAIMS
python3 kb/p9_analysis.py --pack    evidence packs for re-authoring

Authored-content model (same as location_analysis): prose lives in
EXAMS_PROSE (rules_summary / points / conditions / organizer / notes),
SYSTEMS_PROSE (function / notes), INSTANCES (one row per exam
occurrence: chronology / participants / outcome / refs / verbatim
evidence) and EXAM_CLAIMS + SYSTEM_CLAIMS (kind, claimant, refs,
confidence). apply() replace-per-entity into exams/systems prose
columns and DELETE+INSERT into exam_instances / exam_claims /
system_claims. All four are digest-excluded (like location prose) —
dossiers stay pure generated views.

Refs are "vol p.N" strings and MUST resolve to a page where this entity
is mentioned (mentions table) — hard gate, fail-before-write. Every ref
is checked; evidence_quote is auto-derived as the raw corpus slice ±80
chars (page-local) around the first mention span on refs[0], so quotes
are verbatim by construction. Anchored spans are stored alongside.

Instance ids: (exam_index+1)*100 + seq. Claim ids: exam_index*100+n /
sys_index*100+n per-table series (stable slugs, never renumber).

Authoring sources: p9_mine report, evidence packs in
/tmp/opencode/p9_packs/, and page-level context probes (2026-10-16).

Run order: p9_init -> p9_import -> p9_mentions -> p9_analysis
           (FTS rebuild auto-called here) -> build_exam_dossiers.
"""

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402
from p9_init import FTS_REBUILD  # noqa: E402
from p9_import import EXAMS as EXAM_IDS  # noqa: E402
from p9_import import SYSTEMS as SYS_IDS  # noqa: E402


class Instance(TypedDict):
    exam: str
    seq: int
    vol: str
    page: int
    refs: list[str]
    chronology: str
    participants: str
    outcome: str
    confidence: float


class Claim(TypedDict):
    ent: str
    claim: str
    kind: str
    claimant: str | None
    perspective: str
    corroboration: str
    refs: list[str]
    confidence: float
    reliability_note: str


# exam_id -> prose fields
EXAMS_PROSE: dict[str, dict[str, str]] = {
    "midterm-final-written": {
        "rules_summary": "School-designed written exams sat every "
                         "semester (midterms, finals, the year-end "
                         "written). Results are posted class-wide with "
                         "no privacy (y1v6 p.30). The first-midterm "
                         "pass line was computed as half the class "
                         "average (79.6/2 = 39.8, y1v1 p.247); later "
                         "sitings use a fixed threshold over the class "
                         "distribution (y1v6 p.30). Finals run two "
                         "days, four subjects per day (y1v6 p.36).",
        "points": "Results move standing: second-semester finals rank "
                  "the classes with first place earning 50 class "
                  "points (y2v8 p.12), and final-exam averages seed "
                  "later specials — December's head-to-head paired "
                  "classes by those averages (y2v9 p.11). Private "
                  "points can buy extra test points: Chabashira sells "
                  "one for 100,000 (y1v1 p.253).",
        "conditions": "Failing a midterm or final forces drop-out: "
                      "'If you fail on a midterm or final exam in "
                      "this school, then you have to drop out' "
                      "(y1v1 p.128); the year-end written restates "
                      "immediate expulsion for a failing grade "
                      "(y1v9 p.39) and the results post carries the "
                      "below-the-line expulsion rule (y1v10 p.14). "
                      "Unexcused absence scores zero (y1v6 p.36).",
        "organizer": "The school designs questions and cutoffs; "
                     "homeroom teachers (Chabashira for Class D) "
                     "announce results and enforce consequences.",
        "notes": "Highest-frequency exam entity (256 mentions, 23 "
                 "vols, y0-y2v12.5). Carries the core academic-arc "
                 "set pieces: Kushida's old-test leak (y1v1 p.236), "
                 "Sudou's near-expulsion and Ayanokouji's point "
                 "purchase (y1v1 p.247, p.253; y1v2 p.16, p.27), the "
                 "Y1 year-end all-pass (y1v10 p.31), and the Y2 "
                 "second-semester finals whose averages seeded the "
                 "December head-to-head (y2v8 p.12). y0 hits are "
                 "White Room / generic-written senses.",
    },
    "uninhabited-island-exam": {
        "rules_summary": "First-years spend the opening week of the "
                         "summer cruise trip at a lodge on a deserted "
                         "island; classes run a base camp split into "
                         "zones with school-issued safety watches "
                         "(y1v3 p.30). The Y2 return, 'Uninhabited "
                         "Island Survival', runs about two weeks with "
                         "student groups working tasks across grid "
                         "areas such as E7/G3/H5/D8 (overview y2v3 "
                         "p.17).",
        "points": "Task performance converts to points and class "
                  "standing; Y2 first place paid 300 class points "
                  "(y2v5 p.187: 'the 300 class points that Koenji "
                  "got in the desert island exam'). Y1's version is "
                  "remembered as the template class victory (y1v7 "
                  "p.20).",
        "conditions": "Safety-watch failures and rule breaches cost "
                      "participation; groups move through island "
                      "zones across the week (rules narrated y1v3 "
                      "p.27-40). The Y2 rerun adds cross-year "
                      "competition and task pacing.",
        "organizer": "School-designed survival exam run on the trip's "
                     "island leg; homeroom teachers observe.",
        "notes": "244 mentions / 25 vols — the template special, "
                 "cited as the yardstick by nearly every later "
                 "volume. Footprint starts y1v4: the y1v3 chapters "
                 "narrate the trip without the later exam-name "
                 "tokens, so the Y1 instance anchors on the y1v4 "
                 "retrospective (p.69, Ryuuen challenging Horikita's "
                 "island 'victory').",
    },
    "cruise-ship-exam": {
        "rules_summary": "Second week of the first-year cruise trip: "
                         "the liner becomes a twelve-sign zodiac "
                         "test. Students form zodiac-named groups "
                         "(rabbit, dragon, ...) each with a hidden "
                         "VIP identity puzzle and a traitor embedded "
                         "in the group; rules are walked through in "
                         "the private post-trip briefing (y1v4 p.34) "
                         "and the group/VIP logic is re-derived over "
                         "the map at y1v5 p.13-14.",
        "points": "Group-level scores plus traitor sabotage decide "
                  "outcomes; the ship results are accounted "
                  "together with the island week (y1v4.5 p.69: "
                  "'results from the island test, and the test on "
                  "the ship').",
        "conditions": "Groups must complete the week's tasks while "
                      "neutralizing their traitor; Koenji "
                      "unilaterally ended his group's participation "
                      "(y1v4 p.125).",
        "organizer": "School-run special exam staged aboard the "
                     "luxury liner during the trip.",
        "notes": "22 mentions / 9 vols — smallest footprint of the "
                 "trip pair, because the corpus mostly recalls it "
                 "as aftermath ('Ryuuen defeated us on the zodiac "
                 "test', y1v7 p.20) rather than restating rules. "
                 "Forms 'zodiac test' (y1v7, y2v9) and 'zodiac "
                 "game' (y1v7) added after pack reads; 'double-"
                 "question' (y1v4 chapter title) folded in here.",
    },
    "paper-shuffle": {
        "rules_summary": "Named in the y1v6 chapter title 'The Paper "
                         "Shuffle' (p.30): the first-year "
                         "second-semester final pairs students so "
                         "results interlock — two examinees cover "
                         "eight subjects (16 scores), a 43.75 average "
                         "per subject needed against a ~700-point "
                         "overall line (y1v6 p.36). Later specials "
                         "reuse the pairing logic: the Event "
                         "Selection decides opponents 'similar to "
                         "how it was during the Paper Shuffle exam' "
                         "(y1v11 p.28).",
        "points": "Paired finals shift class standing through the "
                  "combined scores; the format is cited as last "
                  "year's contrast when standardized school-designed "
                  "finals return (y2v8 p.12).",
        "conditions": "The midterm/final expulsion rule still "
                      "applies (restated y1v6 p.30); unexcused "
                      "absence scores zero on all missed tests "
                      "(y1v6 p.36).",
        "organizer": "School-run written final; Chabashira announces "
                     "pairings and thresholds.",
        "notes": "27 mentions / 7 vols (y1v6-y2v8). Named at "
                 "y1v6 p.30 and remembered as the exam Horikita's "
                 "strategy turned around (comeback narration y1v7 "
                 "p.19-22), plus a mechanics recap at y2v1 p.42-43 "
                 "when a later volume re-explains it.",
    },
    "mixed-training-camp": {
        "rules_summary": "Autumn third-semester opener: the whole "
                         "school boards buses for a joint road-trip "
                         "camp — first-, second- and third-years "
                         "together (announce chapter y1v8 p.11, "
                         "named 'Mixed Camp' at p.14). Students "
                         "travel in jerseys with designated seats "
                         "and no advance briefing on the tasks.",
        "points": "Point effects are narrated through the camp "
                  "chapters rather than a posted results board; "
                  "the Y2 rerun was explicitly scaled down "
                  "(y2v11 p.53: 'compared to last year's mixed "
                  "training camp, this one is a significant step "
                  "down').",
        "conditions": "Participation is compulsory for the entire "
                      "year group on the bus; format differences "
                      "between the Y1 and Y2 runs are announced "
                      "beforehand (y2v11 p.34).",
        "organizer": "School-run camp special across all three "
                     "grades.",
        "notes": "13 mentions / 7 vols (y1v8-y2v11). The Y1 run is "
                 "the first mixed-grade exam of the series; the Y2 "
                 "announcement stresses the changed nature of the "
                 "event (y2v11 p.34, p.53). Thin outcomes: no "
                 "results board appears on mention pages.",
    },
    "class-poll": {
        "rules_summary": "Class vote: each student casts three "
                         "praise and three censure votes; praise "
                         "minus censure is the result, self-voting "
                         "and blanks are banned, voting repeats "
                         "until first and last are determined, last "
                         "place is expelled, and one dedicated "
                         "praise vote must go to another class's "
                         "student (full rule box y1v10 p.45; name "
                         "and basics y1v10 p.37). The February "
                         "'provisional' rerun was debated by faculty "
                         "before announcement (y1v11 p.13-18).",
        "points": "Main run: no class-point changes came from the "
                  "expulsions themselves (results board y1v10 "
                  "p.315). Provisional run: class points were "
                  "expected to fluctuate without any expulsions "
                  "(y1v11 p.318).",
        "conditions": "First run: last-place students in each class "
                      "are expelled (y1v10 p.315). Provisional: no "
                      "expulsions — defeated classes instead "
                      "forfeit a protection point earned during the "
                      "exam (aftermath y1v11 p.318).",
        "organizer": "School-run supplementary special exam; "
                     "faculty debate preceded the provisional "
                     "rerun (Mashima objects that it risks "
                     "expulsions, Tsukishiro insists, y1v11 "
                     "p.15-18).",
        "notes": "43 mentions / 8 vols (y1v10-y2v9.5). The y1v10 "
                 "run produced three expulsions — Totsuka (A), "
                 "Yamauchi (C), Manabe (D), none from B (y1v10 "
                 "p.315) — the series' first mass-expulsion set "
                 "piece; the provisional rerun is where Ayanokouji "
                 "obtains a protection point (y1v11 p.37).",
    },
    "event-selection-exam": {
        "rules_summary": "Year-one final special: classes show "
                         "cumulative ability — knowledge, physical "
                         "skill, cooperation and luck — with "
                         "opponents decided 'similar to how it was "
                         "during the Paper Shuffle exam' (announce "
                         "y1v11 p.28); schedule set at y1v11 p.33.",
        "points": "Runs as the closing exam of the first year "
                  "(final-special slot from March 8, y1v10 p.31); "
                  "class outcomes feed the year-end standings "
                  "discussed in the y1v11.5 aftermath.",
        "conditions": "Expulsion stakes from the class-vote era "
                      "hang over it — after Yamauchi's expulsion "
                      "students fear being 'next in line' "
                      "(y1v11 p.28).",
        "organizer": "School-run final special of the academic "
                     "year, announced by Chabashira.",
        "notes": "14 mentions / 2 vols only, but narratively it is "
                 "Year 1's end-of-year special: y1v11.5 calls it "
                 "'the final examination of our 1st year, the event "
                 "selection exam' (p.145), and the y1v11.5 "
                 "'end-of-year exam' retrospectives (p.19, p.343) "
                 "refer back to it — those y1v11.5 'end-of-year "
                 "special' mentions belong to this event, not to "
                 "the Y2 special.",
    },
    "unanimous-vote-exam": {
        "rules_summary": "Announced same-day for the next day: "
                         "'a series of multiple-choice votes which "
                         "you will have to repeat as a class until "
                         "you reach a unanimous decision' (y2v5 "
                         "p.31), with the full overview at y2v5 "
                         "p.35-41. Decision topics include whether "
                         "to expel a member (any single no vetoes) "
                         "and the school-trip destination ballot.",
        "points": "Stakes are large: failure modes put 350 class "
                  "points on the line in the protection vote (y2v5 "
                  "p.187), and defeated classes in the exam family "
                  "forfeit protection points (y1v11 p.318).",
        "conditions": "Unanimity is the hard gate — the class "
                      "cannot expel without every yes, and the "
                      "trip ballot runs in rounds (Okinawa 19 / "
                      "Hokkaido 17 / Kyoto 3 first round, y2v5 "
                      "p.91).",
        "organizer": "School-run special exam; classes stage the "
                     "votes internally, the school tallies them.",
        "notes": "89 mentions / 10 vols (y2v5-y3v1). The exam that "
                 "nearly expelled Airi Sakura — Kushida pushed her "
                 "out, the votes failed to unify (y2v5 p.237) — "
                 "and the exam whose ballot picked Hokkaido for the "
                 "trip (y2v8 p.17).",
    },
    "survival-elimination-exam": {
        "rules_summary": "Named in its overview box '[Survival and "
                         "Elimination Special Exam]' (y2v10 p.32): "
                         "diversified tasks by category — each "
                         "class chooses a category, selects a "
                         "difficulty and issues a task to its target "
                         "class in a set order; the name itself "
                         "evokes expulsion (p.32), full name at "
                         "p.144.",
        "points": "Class points swing on placement; the losing side "
                  "of the final standings absorbs the damage "
                  "(Sakayanagi's class took the loss, y2v11 p.11).",
        "conditions": "Elimination mechanics include a chosen "
                      "dropout on the losing side: Kamuro Masumi "
                      "dropped out (y2v11 p.11).",
        "organizer": "School-run second-year special; task issuance "
                     "runs through the class-representative chain.",
        "notes": "15 mentions / 4 vols. Direct predecessor of the "
                 "end-of-year special's high-stakes framing; the "
                 "third-years' winter advice about forced "
                 "expulsion quotas is retold against it (y2v11 "
                 "p.197).",
    },
    "end-of-year-special-exam": {
        "rules_summary": "Y2's closing special: announced with rules "
                         "at y2v11 p.203-210 and run in mid-March. "
                         "Class representatives receive rule sets "
                         "different from what participants see in "
                         "the classroom — 'the information that was "
                         "given between your representatives and the "
                         "participants waiting in the classroom was "
                         "different' (y2v12.5 p.11).",
        "points": "Decisive for the standings: the class still "
                  "gains class points from the end-of-year special "
                  "under partial-win conditions (y2v12 p.36).",
        "conditions": "Expulsions are possible and did occur — "
                      "anticipated pre-match ('the loser will be "
                      "expelled', y2v12 p.41) and confirmed at the "
                      "close, with PM Kijima noting 'it's truly "
                      "regrettable that there were expulsions' "
                      "(y2v12.5 p.9).",
        "organizer": "School-run; Chairman Sakayanagi presides with "
                     "homeroom teachers; sitting Prime Minister "
                     "Kijima attends as observer (y2v12.5 p.9).",
        "notes": "86 mentions / 5 vols. The corpus names it both "
                 "'end-of-year special' and plain 'end-of-year "
                 "exam' — both tokens on y2v11 p.203 — so Y2's "
                 "end-of-year slot IS this special, unlike Y1 "
                 "where the end-of-year written sat separately "
                 "(y1v9 p.39, all-pass y1v10 p.31). The two y1v11.5 "
                 "mentions are event-selection retrospectives. "
                 "First-years run their own concurrent end-of-year "
                 "special (y2v12 p.26-28), and Horikita's class "
                 "ascends to Class A by the third year on the "
                 "strength of this arc (y3v1 p.9 synopsis).",
    },
    "comprehensive-academic-exam": {
        "rules_summary": "Y3 opener (announce y3v1 p.9; overview box "
                         "y3v1 p.100): 'Comprehensive Academic "
                         "Ability Exam: Full-Class and Small-Group "
                         "Battles' — 100 questions drawn from 21 "
                         "topics across 7 subjects, scored out of "
                         "100; classes compete in two categories, "
                         "Full-Class Battles and Small-Group "
                         "Battles.",
        "points": "Scoring is out of 100 points per the overview; "
                  "class-point consequences sit beyond the corpus "
                  "horizon (y3v1 is the final volume).",
        "conditions": "Announced to third-years as their first "
                      "special exam of the year (y3v1 p.9); no "
                      "elimination terms appear inside the "
                      "overview text.",
        "organizer": "School-run third-year written special.",
        "notes": "2 mentions / 1 vol — the thinnest entity in the "
                 "layer, anchoring the third-year arc's opening "
                 "exam and the Ayanokouji-transfer frame (y3v1 "
                 "p.9 synopsis).",
    },
    "sports-festival": {
        "rules_summary": "Annual autumn field event. Y1: physical "
                         "ability week announced for October (y1v5 "
                         "p.13) with individual and team scoring. "
                         "Y2: 'Some rules will differ this time "
                         "around, but the base concept is still the "
                         "same' (announce y2v5 p.13; rules y2v6 "
                         "p.30).",
        "points": "Class results move the standings — after the "
                  "Y2 contests Ryuuen-side classes had won both "
                  "their matches and sat 100 class points ahead "
                  "(y2v7 p.29). Private-point side stakes: MVP of "
                  "each grade earns 100,000 private points (y1v5 "
                  "p.19) and roster substitutes cost 100,000 per "
                  "competition (y1v5 p.23).",
        "conditions": "Roster rules bill substitutes per "
                      "competition (y1v5 p.23); the event is "
                      "compulsory class competition.",
        "organizer": "School-run PE event; homeroom and PE staff "
                     "coordinate.",
        "notes": "326 mentions / 18 vols — the highest-count event "
                 "entity, dense across y1v5 and y2v6. Announced "
                 "together with the cultural festival each year "
                 "(y2v5 p.13 covers both slots).",
    },
    "school-festival": {
        "rules_summary": "First cultural festival in school history "
                         "(announce y2v5 p.13): an all-year sales "
                         "competition. Outline box (y2v5 p.14): "
                         "prep budget as private points — 2nd-years "
                         "5,000, 1st-years 5,500, 3rd-years 4,500 — "
                         "extra funds for student-council or club "
                         "service, unused funds confiscated.",
        "points": "100 class points to places 1-4, 50 to places "
                  "5-8, 9th-12th unchanged, no penalty below 8th "
                  "(y2v5 p.14); final standings posted in the "
                  "aftermath (y2v7 p.202).",
        "conditions": "Budget discipline: initial cost and "
                      "additional funds are excluded from final "
                      "sales and confiscated if unused (y2v5 p.14). "
                      "An unexpected expulsion surfaced during the "
                      "festival (y2v7 p.193).",
        "organizer": "School-run festival; classes compete as "
                     "sales booths across all three grades.",
        "notes": "92 mentions / 10 vols. Footprint starts y1v11 "
                 "p.19 (first-years propose holding one 'next "
                 "year'); the Y2 event anchors y2v5 p.13. "
                 "Horikita's class took first place (y2v7 p.200).",
    },
    "entrance-exam": {
        "rules_summary": "Admission test that sorts applicants into "
                         "ANHS classes. It predates enrollment, so "
                         "the corpus only ever discusses it in "
                         "retrospect or by analogy; no rules box "
                         "exists.",
        "points": "Admission fixes the starting class-point "
                  "baseline for the intake (1000 points at "
                  "enrollment, y2v1 p.19 context), but the exam "
                  "itself never scores inside the story.",
        "conditions": "Pre-enrollment only — zero instances by "
                      "design (see p9_import exclusion log).",
        "organizer": "School admissions (advanced-nurturing "
                     "entrance testing).",
        "notes": "29 mentions / 12 vols. The token is ambiguous: "
                 "admissions framing (y1v1 p.143, p.146) versus "
                 "university entrance exams characters discuss "
                 "(y0 p.83, y2v9.5 p.15, y2v11 p.54-55). Kept as "
                 "an entity with footnotes but no instances so "
                 "the sweep stays complete.",
    },
    "coop-written-head-to-head": {
        "rules_summary": "Official bracket (y2v9 p.13): '[Special "
                         "exam at the end of the second semester. A "
                         "cooperative comprehensive written test in "
                         "which the whole class will solve a total "
                         "of 100 questions.]' Students solve in "
                         "predetermined order, at least 2 and at "
                         "most 5 questions each, 10 minutes per "
                         "turn; overtime disqualifies; leaving "
                         "clues terminates the exam with zero "
                         "points. Time-remaining bonuses: +10 per "
                         "hour left, +5 over 30 minutes, +2 over 10 "
                         "minutes; each question scores by the "
                         "solver's OAA band (A=1 ... E=5, OAA as of "
                         "December 1).",
        "points": "Class-versus-class results transfer 50 class "
                  "points winner-takes (y2v9 p.11); pairings come "
                  "from recent final-exam averages — 1st vs 2nd, "
                  "3rd vs 4th (y2v9 p.11-12); December standings "
                  "A 1250 / B 985 / C 684 / D 655 (y2v9 p.12).",
        "conditions": "No expulsions — explicitly 'not the most "
                      "feared kind of special exam that will cause "
                      "students to drop out' (y2v9 p.11); questions "
                      "cover all regular midterm/final subjects "
                      "from relatively easy to extremely hard "
                      "(y2v9 p.12).",
        "organizer": "School-run special exam; Chabashira "
                     "announces, classes self-organize study "
                     "strategy.",
        "notes": "4 mentions / 1 vol — smallest footprint of any "
                 "special. Found late in P9 as the unresolved "
                 "'mystery exam': the official name appears only "
                 "in the p.13 bracket, so alias forms use the "
                 "dialogue phrasings. Results: Horikita's class "
                 "beat Sakayanagi's; Ichinose's class beat "
                 "Ryuuen's despite sabotage (y2v9 p.215).",
    },
}

# sys_id -> prose fields
SYSTEMS_PROSE: dict[str, dict[str, str]] = {
    "private-points": {
        "function": "Personal currency of ANHS: issued to every "
                    "student, worth one yen each, spent on comfort, "
                    "services, exam points and institutional "
                    "loopholes.",
        "notes": "Issued at enrollment — 100,000 points at the "
                 "start (y1v2 p.27) and a monthly allowance tied "
                 "to standing: 1000 class points = 100,000 points, "
                 "stated yen-equivalent (y2v1 p.14; y1v2 p.15). "
                 "Transfers are unrestricted (y1v10 p.46), which "
                 "enables: buying exam points (sale price 100,000, "
                 "y1v1 p.253; bought for Sudou, y1v2 p.16, p.27), "
                 "revoking an expulsion at 20,000,000 (y1v10 p.46), "
                 "class transfers at 20,000,000 (y3v1 p.19), "
                 "bounties grey-area-legal (y2v2 p.71), event "
                 "stakes (festival prep grants y2v5 p.14; sports "
                 "substitutes 100,000 each y1v5 p.23). Protection "
                 "points enter as a parallel instrument y1v10 "
                 "p.38. 722 mentions / 31 vols, present y0-y3v1.",
    },
    "class-points": {
        "function": "Standing currency of the four classes: starts "
                    "at intake, moves with every exam, sets the "
                    "monthly private-point payout, and reaches "
                    "Class A graduation value.",
        "notes": "Intake baseline 1000 points — 'We had been given "
                 "1000 class points when we first came here' "
                 "(y2v1 p.19) — though later intakes differ (this "
                 "year's first-years started at 800, y2v12 p.28). "
                 "Outside special-exam windows the index can only "
                 "be lowered (decay periods, y2v5 p.30). Snapshot "
                 "at March 1 of the second year: A 1098 "
                 "(Sakayanagi) / B 983 (Horikita) / C 730 "
                 "(Ryuuen) / D 654 (Ichinose), y2v12 p.13. "
                 "Festival awards 100/50 (y2v5 p.14) and island "
                 "first-place 300 (y2v5 p.187) are typical "
                 "movement sizes. 616 mentions / 30 vols.",
    },
    "student-council": {
        "function": "Student self-government: discipline "
                    "summonses, budget oversight of events, and "
                    "the annual presidential election.",
        "notes": "Manabu Horikita's presidency opens the series "
                 "(y1v1 p.64-67); the mid-October election "
                 "ceremony swears in Nagumo Miyabi as next "
                 "president (y1v6 p.14), with the Horikita-Nagumo "
                 "race recalled at y1v4.5 p.180. Suzune joins the "
                 "council in the second year (y2v2 p.350) and the "
                 "council's budget hands out festival service "
                 "funds (y2v7 p.7-9); Nagumo-era entanglements "
                 "peak in y2v9. The council room doubles as the "
                 "pressure venue (see student-council-room "
                 "location). 1189 mentions / 28 vols.",
    },
    "clubs": {
        "function": "Extracurricular organizations with schedules, "
                    "funding and fair-based recruitment.",
        "notes": "Club fair runs in Gymnasium No. 1 at the start "
                 "of the year (y1v1 p.59) with membership handled "
                 "as a funding decision (y1v1 p.64). Clubs carry "
                 "strict practice schedules (y1v4.5 p.13) and "
                 "their own budgets that also feed festival "
                 "service funds (y2v7 p.7). Sudou's basketball "
                 "club is the recurring example. 346 mentions / "
                 "28 vols.",
    },
    "expulsion": {
        "function": "Drop-out discipline: failing grades, class "
                    "votes, eliminations and buybacks all end in "
                    "the same forced exit.",
        "notes": "The base rule lands in the first weeks — fail a "
                 "midterm or final and you drop out (y1v1 p.128) — "
                 "with results posts carrying the below-the-line "
                 "threat (y1v10 p.14). Instruments beyond written "
                 "grades: class-vote expulsions (three names y1v10 "
                 "p.315), elimination-loss dropouts (Kamuro, y2v11 "
                 "p.11), bounties (20,000,000 to have someone "
                 "removed, y2v2 p.71) and the 20,000,000 revocation "
                 "off-ramp (y1v10 p.46). Voluntary and "
                 "forced-exit counts are quoted in the y1v11.5 "
                 "aftermath and the Maezono case (y2v12.5 p.81, "
                 "p.143). 1634 mentions / 30 vols — the largest "
                 "system footprint after student-council.",
    },
}

# occurrence rows, filled in stage 2
INSTANCES: list[Instance] = [
    {
        "exam": "midterm-final-written", "seq": 1,
        "vol": "y1v1", "page": 128,
        "refs": ["y1v1 p.128", "y1v1 p.236", "y1v1 p.247", "y1v1 p.253"],
        "chronology": "First-semester midterm for the first-year classes, "
                      "sat and graded inside the first volume; Chabashira "
                      "posts results class-wide.",
        "participants": "All first-year students; Chabashira Sae (posts "
                        "Class D results); Sudou Kakeru (failing grade); "
                        "Ayanokōji Kiyotaka (buys the make-up point).",
        "outcome": "Sudou's English score of 32 sits under the 39.8 pass "
                   "line (79.6 class average divided by two, y1v1 p.247); "
                   "Chabashira sells him a test point for 100,000 private "
                   "points (y1v1 p.253) and Ayanokōji pays for it (y1v2 "
                   "p.16, p.27).",
        "confidence": 0.95,
    },
    {
        "exam": "midterm-final-written", "seq": 2,
        "vol": "y1v3", "page": 13,
        "refs": ["y1v3 p.13"],
        "chronology": "The third volume opens on the summer cruise, after "
                      "the first-semester finals of the first year have "
                      "already been graded.",
        "participants": "First-year students aboard the cruise; Yamauchi "
                        "Haruki; Ayanokōji Kiyotaka.",
        "outcome": "Yamauchi taunts Ayanokōji about finishing with the "
                   "lowest score on the final — the deliberate last place "
                   "that keeps his profile unremarkable (y1v3 p.13).",
        "confidence": 0.9,
    },
    {
        "exam": "midterm-final-written", "seq": 3,
        "vol": "y1v6", "page": 30,
        "refs": ["y1v6 p.30", "y1v6 p.33", "y1v6 p.36"],
        "chronology": "Second first-year midterm: results day falls in "
                      "Chapter 3 ('The Paper Shuffle'), with Chabashira "
                      "restating the fail-and-expel rule before reading "
                      "the board.",
        "participants": "All first-year students; Chabashira Sae; Sudou "
                        "Kakeru (passed after Horikita's tutoring); "
                        "Yamauchi Haruki (bottom of Class D).",
        "outcome": "Sports-festival bonuses and penalties adjust the "
                   "posted scores and nobody fails — 'no one has to drop "
                   "out of school due to their midterm scores this time' "
                   "(y1v6 p.33).",
        "confidence": 0.95,
    },
    {
        "exam": "midterm-final-written", "seq": 4,
        "vol": "y1v9", "page": 39,
        "refs": ["y1v9 p.39", "y1v10 p.31"],
        "chronology": "The end-of-year written exam is announced late in "
                      "the first year — roughly ten days out, with a "
                      "practice test on the 15th (y1v9 p.39).",
        "participants": "All first-year students; school administration; "
                        "Class D under Chabashira.",
        "outcome": "Every first-year passes: recorded on March 2, 'we "
                   "passed the end-of-year exam without any problems' "
                   "(y1v10 p.31).",
        "confidence": 0.95,
    },
    {
        "exam": "midterm-final-written", "seq": 5,
        "vol": "y2v8", "page": 12,
        "refs": ["y2v8 p.12", "y2v8 p.11", "y2v9 p.11"],
        "chronology": "Late November of the second year: results of the "
                      "second-semester final examinations are posted "
                      "before the December special exam.",
        "participants": "All four second-year classes; Chabashira Sae "
                        "(announces to Class B).",
        "outcome": "First place gains 50 class points, second +25, third "
                   "-25 and fourth -50, and students below the cutoff "
                   "(subject averages of 39) are expelled (y2v8 p.12); "
                   "the averages fix the December head-to-head pairings — "
                   "1st vs 2nd, 3rd vs 4th (y2v9 p.11-12).",
        "confidence": 0.95,
    },
    {
        "exam": "uninhabited-island-exam", "seq": 1,
        "vol": "y1v4", "page": 69,
        "refs": ["y1v4 p.69", "y1v4.5 p.69", "y1v7 p.20"],
        "chronology": "First-year uninhabited-island test, run and graded "
                      "before the summer cruise; its result is still being "
                      "argued over a volume later.",
        "participants": "The four first-year classes; Ryuuen Kakeru "
                        "(contests the result); Horikita Suzune's class "
                        "(claims the win).",
        "outcome": "Class D is recorded as having beaten every other class "
                   "on the island (y1v7 p.20), while Ryuuen publicly "
                   "challenges Horikita's claimed 'victory' (y1v4 p.69).",
        "confidence": 0.9,
    },
    {
        "exam": "uninhabited-island-exam", "seq": 2,
        "vol": "y2v2", "page": 119,
        "refs": ["y2v2 p.119", "y2v3 p.17", "y2v5 p.187"],
        "chronology": "Announced in the second year as the next special "
                      "exam during summer vacation (y2v2 p.119) and run "
                      "across y2v3.",
        "participants": "All second-year classes; Kōenji Kakeru (works "
                        "alone for Class A).",
        "outcome": "Kōenji's individual effort banks 300 class points — "
                   "called 'a miracle' by a classmate (y2v5 p.187).",
        "confidence": 0.95,
    },
    {
        "exam": "cruise-ship-exam", "seq": 1,
        "vol": "y1v4", "page": 34,
        "refs": ["y1v4 p.34", "y1v4 p.35", "y1v7 p.20", "y1v4.5 p.69"],
        "chronology": "The two-week luxury-liner trip doubles as a special "
                      "exam: Class D gets a private briefing on the Zodiac "
                      "grouping before activities begin (y1v4 p.34-35).",
        "participants": "First-year classes in twelve Zodiac groups (Class "
                        "D split into three); Mashima (instructor, refuses "
                        "questions); Kōenji Kakeru.",
        "outcome": "Ryuuen's class defeats Class D on the Zodiac round "
                   "while Class D wins the rest of the trip (y1v7 p.20); "
                   "Kōenji's unilateral play ends his group's cooperation "
                   "(y1v4 p.125).",
        "confidence": 0.9,
    },
    {
        "exam": "paper-shuffle", "seq": 1,
        "vol": "y1v6", "page": 30,
        "refs": ["y1v6 p.30", "y1v6 p.36", "y1v7 p.19", "y2v1 p.42"],
        "chronology": "First-year first-semester final: pairs are fixed by "
                      "a mock quiz (y1v6 p.35), then the two-day paired "
                      "written exam runs under the Paper Shuffle name "
                      "(chapter 3, y1v6 p.30).",
        "participants": "First-year students in fixed pairs; Chabashira "
                        "Sae (explains the rules); Hirata, Horikita, "
                        "Yukimura and Sudou among the pairs.",
        "outcome": "Eight subjects, 400 questions; a pair under sixty in "
                   "any subject, or under the ~700-point overall bar "
                   "(43.75 average across sixteen scores), loses both "
                   "members — 'one or two pairs are usually expelled… most "
                   "of them are from Class D' (y1v6 p.36). The result "
                   "narrows the gap to Class C (y1v7 p.19).",
        "confidence": 0.95,
    },
    {
        "exam": "mixed-training-camp", "seq": 1,
        "vol": "y1v8", "page": 11,
        "refs": ["y1v8 p.11", "y1v8 p.14"],
        "chronology": "'A New Special Exam: Mixed Training Camp' opens the "
                      "vacation — all year groups board buses (y1v8 p.11) "
                      "and Chabashira names the exam in class (y1v8 p.14).",
        "participants": "All three year groups mixed into inter-class "
                        "teams; first-year classes under their homeroom "
                        "teachers.",
        "outcome": "Eight days and seven nights of inter-class group "
                   "activities with senior students, positioned as 'a step "
                   "beyond the Sports Festival' (y1v8 p.14).",
        "confidence": 0.95,
    },
    {
        "exam": "mixed-training-camp", "seq": 2,
        "vol": "y2v11", "page": 34,
        "refs": ["y2v11 p.34", "y2v11 p.53"],
        "chronology": "Second-year Mixed Training Camp: nine buses instead "
                      "of the expected twelve (y2v11 p.34); the term "
                      "'special exam' is deliberately avoided.",
        "participants": "Second- and third-year students; Nagumo Miyabi "
                        "(laments the downgraded stakes, y2v11 p.53).",
        "outcome": "Repositioned as an exchange meeting — no expulsion "
                   "risk and not even a penalty specified, 'a significant "
                   "step down' from the previous year's camp (y2v11 p.53).",
        "confidence": 0.95,
    },
    {
        "exam": "class-poll", "seq": 1,
        "vol": "y1v10", "page": 37,
        "refs": ["y1v10 p.37", "y1v10 p.45", "y1v10 p.315"],
        "chronology": "Named and explained in March of the first year "
                      "('The name of the special exam is the Class Poll', "
                      "y1v10 p.37), then run to the volume's close.",
        "participants": "First-year classes; Chabashira Sae (rules: three "
                        "praise and three censure votes, y1v10 p.45); "
                        "every voting member of Class D.",
        "outcome": "The posted results board records three expulsions — "
                   "Totsuka Yahiko (Class A), Yamauchi Haruki (Class C) "
                   "and Manabe Shiho (Class D), none from Class B — and "
                   "no class-point changes (y1v10 p.315).",
        "confidence": 0.95,
    },
    {
        "exam": "class-poll", "seq": 2,
        "vol": "y1v11", "page": 13,
        "refs": ["y1v11 p.13", "y1v11 p.15", "y1v11 p.18"],
        "chronology": "February of the first year: a provisional Class "
                      "Vote is imposed on the first-years over the "
                      "faculty's objection.",
        "participants": "First-year classes; Mashima (protests to "
                        "Tsukishiro); Chabashira (calls Mashima off); "
                        "Tsukishiro, Acting Director (decides).",
        "outcome": "Implementation is already decided (y1v11 p.18) despite "
                   "the warned expulsion risk (y1v11 p.15); the vote ends "
                   "without expulsions, defeated classes forfeit a "
                   "protection point (y1v11 p.318), Ayanokōji takes a "
                   "protection point (y1v11 p.37) and Ryuuen's class "
                   "survives (y1v11 p.381).",
        "confidence": 0.9,
    },
    {
        "exam": "event-selection-exam", "seq": 1,
        "vol": "y1v11", "page": 28,
        "refs": ["y1v11 p.28", "y1v11 p.33", "y1v11.5 p.34",
                 "y1v11.5 p.145"],
        "chronology": "The final special of the first year: announced "
                      "March 8 with matchups set, event selection locked "
                      "March 15, exam day March 22 (y1v11 p.33).",
        "participants": "First-year classes paired by Paper-Shuffle-style "
                        "rules (y1v11 p.28); Chabashira Sae (explains); "
                        "Horikita Suzune (clarifies the bluff mechanic).",
        "outcome": "Each class narrows the opponent's ten events to five "
                   "submissions, five of them bluffs (y1v11 p.33); the "
                   "conclusion is recalled from the aftermath volume "
                   "(y1v11.5 p.34, p.145).",
        "confidence": 0.95,
    },
    {
        "exam": "unanimous-vote-exam", "seq": 1,
        "vol": "y2v5", "page": 31,
        "refs": ["y2v5 p.31", "y2v5 p.35", "y2v5 p.41", "y2v5 p.237",
                 "y2v8 p.17"],
        "chronology": "Second-year spring: the Unanimous Vote Exam is "
                      "announced and its rules board goes up in class "
                      "(y2v5 p.31, p.41).",
        "participants": "All classmates must vote; Hirata Yōsuke (pushes "
                        "for unanimity); Horikita Suzune; Sakura Airi (the "
                        "proposed sacrifice, y2v5 p.237).",
        "outcome": "Five questions, up to four options each, repeated "
                   "until unanimous, timeout voids the question (y2v5 "
                   "p.41); the class avoids expelling Airi (y2v5 p.237) "
                   "while weighing a 350-class-point loss (y2v5 p.187); "
                   "the later Hokkaido ballot reuses the mechanism (y2v8 "
                   "p.17).",
        "confidence": 0.95,
    },
    {
        "exam": "survival-elimination-exam", "seq": 1,
        "vol": "y2v10", "page": 32,
        "refs": ["y2v10 p.32", "y2v10 p.144", "y2v10 p.197", "y2v11 p.11"],
        "chronology": "The [Survival and Elimination Special Exam] "
                      "overview is issued (y2v10 p.32) and the exam runs "
                      "across the volume to its close (y2v10 p.144, p.197).",
        "participants": "Sakayanagi's Class A, Ichinose's Class D, Ryuuen's "
                        "Class C (takes the first attack, y2v10 p.144); "
                        "Kamuro Minori (the class's sacrificial lamb, "
                        "y2v10 p.197).",
        "outcome": "Chabashira closes the completed exam (y2v10 p.197); "
                   "Kamuro's loss ends in expulsion (y2v11 p.11).",
        "confidence": 0.95,
    },
    {
        "exam": "end-of-year-special-exam", "seq": 1,
        "vol": "y2v11", "page": 203,
        "refs": ["y2v11 p.203", "y2v12 p.11", "y2v12.5 p.9",
                 "y2v12.5 p.11"],
        "chronology": "Announced late in y2v11 (Hashimoto commits to "
                      "making Ryuuen win 'no matter what the content of "
                      "the end-of-year special exam is', y2v11 p.203); "
                      "opens in y2v12 (y2v12 p.11) and concludes on the "
                      "calendar's end — March 14 (y2v12.5 p.9).",
        "participants": "Second-year classes; Hashimoto Noriaki; Kijima "
                        "(outside observer at the conclusion, y2v12.5 "
                        "p.9); Maezono (expelled — y2v12.5 p.81, p.143).",
        "outcome": "Fought under asymmetric information (y2v12.5 p.11); a "
                   "single expulsion lands; by the third year Horikita's "
                   "class has ascended to Class A (y3v1 p.9).",
        "confidence": 0.9,
    },
    {
        "exam": "comprehensive-academic-exam", "seq": 1,
        "vol": "y3v1", "page": 9,
        "refs": ["y3v1 p.9", "y3v1 p.100"],
        "chronology": "The third year opens with the announcement of its "
                      "first special exam (y3v1 p.9) and the overview "
                      "board in class (y3v1 p.100).",
        "participants": "The four third-year classes; Chabashira Sae "
                        "(announces to Ayanokōji's Class C).",
        "outcome": "100 written questions randomised from 21 topics "
                   "across 7 subjects, scored out of 100, split into "
                   "Full-Class Battles and Small-Group Battles (y3v1 "
                   "p.100).",
        "confidence": 0.95,
    },
    {
        "exam": "sports-festival", "seq": 1,
        "vol": "y1v5", "page": 13,
        "refs": ["y1v5 p.13", "y1v5 p.16", "y1v6 p.14"],
        "chronology": "First-year sports festival: PE preparation is "
                      "announced from September to early October (y1v5 "
                      "p.16); the festival finishes before mid-October "
                      "(y1v6 p.14).",
        "participants": "First-year classes; Chabashira Sae (schedule "
                        "handouts); Student Council under Horikita Manabu.",
        "outcome": "Sports-festival performance is scored into the next "
                   "midterm (y1v6 p.31); the post-festival mid-October "
                   "ceremony swears in Nagumo Miyabi as student council "
                   "president (y1v6 p.14).",
        "confidence": 0.9,
    },
    {
        "exam": "sports-festival", "seq": 2,
        "vol": "y2v5", "page": 13,
        "refs": ["y2v5 p.13", "y2v6 p.30", "y2v7 p.29"],
        "chronology": "Second-year sports festival announced alongside "
                      "the cultural festival (y2v5 p.13) and explained "
                      "after the Unanimous Vote Exam closes (y2v6 p.30).",
        "participants": "Second-year classes; Chabashira Sae (new special "
                        "rules set by the Student Council President); "
                        "Ryuuen Kakeru (engineers the upset).",
        "outcome": "Ryuuen admits helping Horikita's class 'destroy Class "
                   "A': both classes picked up wins and Ryuuen's class "
                   "finished 100 class points ahead as a result (y2v7 "
                   "p.29).",
        "confidence": 0.9,
    },
    {
        "exam": "school-festival", "seq": 1,
        "vol": "y2v5", "page": 13,
        "refs": ["y2v5 p.13", "y2v5 p.14", "y2v7 p.19", "y2v7 p.200"],
        "chronology": "The first cultural festival in the school's history "
                      "is announced with the sports festival (y2v5 p.13) "
                      "and its sales outline is briefed (y2v5 p.14); it "
                      "runs across y2v7.",
        "participants": "All three years of classes competing on total "
                        "sales with guests on campus; Ryuuen and Horikita "
                        "trade a matching-stall declaration of war (y2v7 "
                        "p.29).",
        "outcome": "Horikita's class takes first place — 'we did manage to "
                   "get first place at the school festival' (y2v7 p.200) "
                   "— with 100 class points for 1st-4th and 50 for 5th-8th "
                   "(y2v5 p.14); an unexpected expulsion lands on the "
                   "first-years' side (y2v7 p.193).",
        "confidence": 0.95,
    },
    {
        "exam": "coop-written-head-to-head", "seq": 1,
        "vol": "y2v9", "page": 11,
        "refs": ["y2v9 p.11", "y2v9 p.12", "y2v9 p.13", "y2v9 p.215"],
        "chronology": "Announced after the second-semester finals in "
                      "December: Chabashira introduces a one-on-one "
                      "academic competition between classes (y2v9 p.11) "
                      "and the official outline follows (y2v9 p.13).",
        "participants": "The four second-year classes in rank pairings "
                        "(1st vs 2nd, 3rd vs 4th); Chabashira Sae; Ryuuen "
                        "against Ichinose's class.",
        "outcome": "100 cooperative questions with winner-takes 50 class "
                   "points (y2v9 p.11); results at y2v9 p.215 — Horikita's "
                   "class beats Sakayanagi's and Ichinose's class beats "
                   "Ryuuen's despite his sabotage.",
        "confidence": 0.95,
    },
]

# claim rows, filled in stages 3-4
EXAM_CLAIMS: list[Claim] = [
    {
        "ent": "midterm-final-written",
        "claim": "The first-midterm pass line was half the class average "
                 "— 79.6 divided by 2 equals 39.8 — so Sudou's English "
                 "score of 32 failed by less than a point.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Results-day narration of Chabashira's blackboard "
                       "formula",
        "corroboration": "none",
        "refs": ["y1v1 p.247"],
        "confidence": 0.9,
        "reliability_note": "Formula written on the board during the "
                            "scene; Chabashira rounds it to 'at least a "
                            "forty' in dialogue (y1v1 p.247).",
    },
    {
        "ent": "midterm-final-written",
        "claim": "Failing a midterm or final exam means immediate "
                 "expulsion from the school.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira stating school policy to Class D",
        "corroboration": "supported",
        "refs": ["y1v1 p.128", "y1v6 p.30", "y1v9 p.39"],
        "confidence": 0.95,
        "reliability_note": "Restated at every results day (y1v6 p.30) "
                            "and before the year-end exam (y1v9 p.39); "
                            "never contradicted.",
    },
    {
        "ent": "midterm-final-written",
        "claim": "The second-semester finals were a class-based "
                 "competition — 1st place +50 class points, 2nd +25, 3rd "
                 "-25, 4th -50 — with expulsion for anyone below the "
                 "cutoff average of 39.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Ayanokōji narration of the results announcement",
        "corroboration": "none",
        "refs": ["y2v8 p.12"],
        "confidence": 0.9,
        "reliability_note": "Announcement and rules summarized in the "
                            "same passage (y2v8 p.12).",
    },
    {
        "ent": "midterm-final-written",
        "claim": "The end-of-year written exam falls roughly ten days "
                 "after the practice test on the 15th.",
        "kind": "character_claim", "claimant": None,
        "perspective": "Yukimura outlining the study-group plan",
        "corroboration": "none",
        "refs": ["y1v9 p.39"],
        "confidence": 0.85,
        "reliability_note": "Class conversation rather than an official "
                            "schedule (y1v9 p.39).",
    },
    {
        "ent": "uninhabited-island-exam",
        "claim": "Horikita's class beat every other class in the "
                 "first-year uninhabited island exam.",
        "kind": "character_claim", "claimant": None,
        "perspective": "Class D classmate recounting the result",
        "corroboration": "supported",
        "refs": ["y1v7 p.20", "y1v4 p.69"],
        "confidence": 0.85,
        "reliability_note": "Dialogue statement (y1v7 p.20) alongside "
                            "Ryuuen's public challenge of the claimed "
                            "victory (y1v4 p.69).",
    },
    {
        "ent": "uninhabited-island-exam",
        "claim": "Kōenji's individual effort in the second-year island "
                 "exam took first place and banked 300 class points, "
                 "called 'a miracle' on-page.",
        "kind": "character_claim", "claimant": None,
        "perspective": "Keisei speaking during the unanimous-vote "
                       "expulsion debate",
        "corroboration": "supported",
        "refs": ["y2v5 p.187", "y2v5 p.114"],
        "confidence": 0.9,
        "reliability_note": "300-point figure and 'miracle' framing at "
                            "y2v5 p.187; Horikita's protection promise "
                            "for that first place at y2v5 p.114.",
    },
    {
        "ent": "paper-shuffle",
        "claim": "The Paper Shuffle pairs students for an eight-subject, "
                 "400-question final: a pair under sixty in any subject "
                 "or under the ~700-point overall bar (43.75 across "
                 "sixteen scores) loses both members.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira briefing Class D on the final",
        "corroboration": "supported",
        "refs": ["y1v6 p.36", "y1v6 p.30"],
        "confidence": 0.9,
        "reliability_note": "Direct rule briefing (y1v6 p.36); the "
                            "pair-setting quiz is announced on y1v6 p.35 "
                            "and the exam carries the chapter title "
                            "(y1v6 p.30).",
    },
    {
        "ent": "class-poll",
        "claim": "Each student receives three praise votes and three "
                 "censure votes that cancel each other; voting is "
                 "repeated until first and last place are determined, "
                 "and the last-place student is expelled.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Rules narration of the supplementary exam",
        "corroboration": "supported",
        "refs": ["y1v10 p.45", "y1v10 p.37"],
        "confidence": 0.9,
        "reliability_note": "Five numbered rules on-page (y1v10 p.45); "
                            "exam name and basics at y1v10 p.37.",
    },
    {
        "ent": "class-poll",
        "claim": "The first Class Poll ended with three expulsions — "
                 "Totsuka Yahiko (Class A), Yamauchi Haruki (Class C) "
                 "and Manabe Shiho (Class D), none from Class B — and no "
                 "class-point changes.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Vote-results board narration",
        "corroboration": "none",
        "refs": ["y1v10 p.315"],
        "confidence": 0.95,
        "reliability_note": "Verbatim results statement on the bulletin "
                            "board (y1v10 p.315).",
    },
    {
        "ent": "class-poll",
        "claim": "The provisional Class Vote went ahead over faculty "
                 "objection: Mashima protested to Acting Director "
                 "Tsukishiro, but implementation had already been "
                 "decided.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Narration of the teachers' battle",
        "corroboration": "supported",
        "refs": ["y1v11 p.15", "y1v11 p.18"],
        "confidence": 0.9,
        "reliability_note": "Mashima's warnings and Chabashira calling "
                            "him off (y1v11 p.15, p.18); the chapter "
                            "opens the day before the announce (y1v11 "
                            "p.13).",
    },
    {
        "ent": "event-selection-exam",
        "claim": "The first year's final special is the Event Selection "
                 "Exam: matchups are decided like the Paper Shuffle and "
                 "each class submits five of the opponent's ten events.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira announcing the exam",
        "corroboration": "supported",
        "refs": ["y1v11 p.28", "y1v11 p.33"],
        "confidence": 0.9,
        "reliability_note": "Naming and matchup rule at y1v11 p.28; the "
                            "submission rule and timeline at y1v11 p.33, "
                            "where Horikita adds that five of the ten "
                            "events are bluffs.",
    },
    {
        "ent": "unanimous-vote-exam",
        "claim": "The Unanimous Voting Exam runs within each class only "
                 "— five school questions of up to four options, "
                 "repeated until the class votes unanimously, with a "
                 "timeout voiding the question.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira presenting the rules board",
        "corroboration": "supported",
        "refs": ["y2v5 p.31", "y2v5 p.41"],
        "confidence": 0.95,
        "reliability_note": "Verbal announce and written overview agree "
                            "(y2v5 p.31, p.41).",
    },
    {
        "ent": "unanimous-vote-exam",
        "claim": "The winter school-trip destination was chosen by a "
                 "three-way class ballot (Hokkaido, Kyoto, Okinawa); "
                 "Hokkaido took three of the class votes.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Ayanokōji narration of the ballot results",
        "corroboration": "none",
        "refs": ["y2v8 p.17"],
        "confidence": 0.95,
        "reliability_note": "Chabashira reads the same result in scene "
                            "(y2v8 p.17).",
    },
    {
        "ent": "survival-elimination-exam",
        "claim": "In the Survival and Elimination Exam each class "
                 "chooses a task category, selects a difficulty, and "
                 "issues a task to its target class in a set order.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira explaining the test content",
        "corroboration": "none",
        "refs": ["y2v10 p.32"],
        "confidence": 0.9,
        "reliability_note": "Read directly from the exam announcement "
                            "(y2v10 p.32); students immediately associate "
                            "the name with expulsion.",
    },
    {
        "ent": "end-of-year-special-exam",
        "claim": "The second year's end-of-year special gave the "
                 "representatives and the waiting classroom different "
                 "information; the only shared facts were the class's "
                 "victory or defeat and whether any expulsions occurred.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira briefing the representatives after "
                       "the exam",
        "corroboration": "none",
        "refs": ["y2v12.5 p.11"],
        "confidence": 0.9,
        "reliability_note": "Stated by the teacher on the walk back "
                            "(y2v12.5 p.11) and echoed by the "
                            "participants' confusion.",
    },
    {
        "ent": "comprehensive-academic-exam",
        "claim": "The Comprehensive Academic Ability Exam is a "
                 "100-question written test randomised from 21 topics "
                 "across 7 subjects, scored out of 100 and split into "
                 "Full-Class Battles and Small-Group Battles.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Exam overview board",
        "corroboration": "none",
        "refs": ["y3v1 p.100"],
        "confidence": 0.95,
        "reliability_note": "Read verbatim from the class monitor "
                            "overview (y3v1 p.100).",
    },
    {
        "ent": "sports-festival",
        "claim": "Ryuuen's class helped Horikita's class destroy Class A "
                 "at the second-year sports festival: both classes won "
                 "their matches and Ryuuen finished 100 class points "
                 "ahead as a result.",
        "kind": "character_claim", "claimant": "ryuuen-kakeru",
        "perspective": "Ryuuen speaking to Horikita",
        "corroboration": "none",
        "refs": ["y2v7 p.29"],
        "confidence": 0.9,
        "reliability_note": "Self-reported in dialogue (y2v7 p.29); no "
                            "contradicting account.",
    },
    {
        "ent": "school-festival",
        "claim": "Cultural-festival preparation grants are 5,500 / 5,000 "
                 "/ 4,500 private points for first / second / third "
                 "years, and placements pay 100 class points for 1st-4th "
                 "and 50 for 5th-8th, with no penalty below eighth.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Festival outline box",
        "corroboration": "supported",
        "refs": ["y2v5 p.14"],
        "confidence": 0.95,
        "reliability_note": "Bulleted outline on-page (y2v5 p.14); 9th "
                            "to 12th place stand unchanged.",
    },
    {
        "ent": "coop-written-head-to-head",
        "claim": "The head-to-head pairs classes by standing (1st vs "
                 "2nd, 3rd vs 4th) and the winner takes 50 class points "
                 "from the loser.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira announcing the exam",
        "corroboration": "supported",
        "refs": ["y2v9 p.11", "y2v9 p.12"],
        "confidence": 0.95,
        "reliability_note": "Stakes and pairing logic stated in scene "
                            "(y2v9 p.11) with December standings on "
                            "y2v9 p.12.",
    },
    {
        "ent": "coop-written-head-to-head",
        "claim": "In the December head-to-head, Horikita's class beat "
                 "Sakayanagi's and Ichinose's class beat Ryuuen's "
                 "despite his sabotage.",
        "kind": "character_claim", "claimant": "ichinose-honami",
        "perspective": "Post-exam dialogue between Ichinose and Ryuuen",
        "corroboration": "none",
        "refs": ["y2v9 p.215"],
        "confidence": 0.9,
        "reliability_note": "First result stated by Ichinose, second by "
                            "Ryuuen's own account of his failed "
                            "sabotage (y2v9 p.215).",
    },
]
SYSTEM_CLAIMS: list[Claim] = [
    {
        "ent": "private-points",
        "claim": "Private points exchange one-to-one with the yen and "
                 "are paid out monthly at 100 points per class point, "
                 "with 100,000 granted at enrollment.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "System explanation narration",
        "corroboration": "supported",
        "refs": ["y2v1 p.14", "y1v2 p.15", "y1v2 p.27"],
        "confidence": 0.95,
        "reliability_note": "Exchange rate and monthly formula at y2v1 "
                            "p.14; the 100,000 enrollment figure at y1v2 "
                            "p.15, p.27.",
    },
    {
        "ent": "private-points",
        "claim": "Exam points can be bought with private points — "
                 "Ayanokōji purchased Sudou's midterm point after "
                 "Chabashira's offer.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Ayanokōji narration",
        "corroboration": "supported",
        "refs": ["y1v2 p.16", "y1v2 p.27"],
        "confidence": 0.9,
        "reliability_note": "Purchase recounted first-hand, backing "
                            "Chabashira's line 'at this school, you can "
                            "buy anything with your points' (y1v2 p.16); "
                            "sale price 100,000 stated at y1v1 p.253.",
    },
    {
        "ent": "private-points",
        "claim": "A payment of 20,000,000 private points forces the "
                 "school to revoke an expulsion.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira answering a classmate's question",
        "corroboration": "supported",
        "refs": ["y1v10 p.46"],
        "confidence": 0.9,
        "reliability_note": "Stated as school policy with no "
                            "loopholes; explained why she called the "
                            "expulsion 'probably impossible' (y1v10 "
                            "p.46).",
    },
    {
        "ent": "private-points",
        "claim": "Twenty million private points buy a transfer to "
                 "another class — presented as a well-known but "
                 "unrealistic fact.",
        "kind": "character_claim", "claimant": "chabashira-sae",
        "perspective": "Chabashira announcing transfer terms in class",
        "corroboration": "none",
        "refs": ["y3v1 p.19"],
        "confidence": 0.85,
        "reliability_note": "Students treat the announcement as a joke "
                            "because of the sum (y3v1 p.19).",
    },
    {
        "ent": "private-points",
        "claim": "A private bounty of 20,000,000 points to get a student "
                 "expelled sits in a grey area that breaks no school "
                 "rule.",
        "kind": "inference", "claimant": "horikita-suzune",
        "perspective": "Horikita reasoning through the first-year "
                       "expulsion attempt",
        "corroboration": "none",
        "refs": ["y2v2 p.71"],
        "confidence": 0.7,
        "reliability_note": "Horikita's on-page reconstruction of the "
                            "plot; the narrator confirms the grey-area "
                            "reading (y2v2 p.71).",
    },
    {
        "ent": "private-points",
        "claim": "Festival preparation grants are private points that "
                 "cannot carry over: unused initial cost and additional "
                 "funds are confiscated.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Festival outline box",
        "corroboration": "supported",
        "refs": ["y2v5 p.14"],
        "confidence": 0.9,
        "reliability_note": "Bulleted outline (y2v5 p.14); grants restated "
                            "in the y2v7 p.7 outline.",
    },
    {
        "ent": "class-points",
        "claim": "Classes open with 1000 class points — 'We had been "
                 "given 1000 class points when we first came here' — "
                 "while the following year's intake started at 800.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Class-debt narration",
        "corroboration": "supported",
        "refs": ["y2v1 p.19", "y2v12 p.28"],
        "confidence": 0.9,
        "reliability_note": "Both baselines stated in scene; the 800 "
                            "figure covers the concurrent first-year "
                            "intake (y2v12 p.28).",
    },
    {
        "ent": "class-points",
        "claim": "At March 1 of the second year the standings stood at "
                 "A 1098 / B 983 / C 730 / D 654.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Standings-board narration",
        "corroboration": "none",
        "refs": ["y2v12 p.13"],
        "confidence": 0.95,
        "reliability_note": "Explicit snapshot with date (y2v12 p.13).",
    },
    {
        "ent": "class-points",
        "claim": "When special exams are not being held, class points "
                 "can only be lowered — earning them outside exams is "
                 "extremely difficult.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Ayanokōji narration",
        "corroboration": "none",
        "refs": ["y2v5 p.30"],
        "confidence": 0.9,
        "reliability_note": "Spoken reflection right after Chabashira's "
                            "special-exam briefing (y2v5 p.30).",
    },
    {
        "ent": "student-council",
        "claim": "Horikita Manabu's presidency ends at the mid-October "
                 "election ceremony, where Nagumo Miyabi is sworn in.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Schedule and ceremony narration",
        "corroboration": "supported",
        "refs": ["y1v1 p.64", "y1v6 p.14"],
        "confidence": 0.9,
        "reliability_note": "Manabu's term opens the series (y1v1 p.64) "
                            "and the handover lands mid-October (y1v6 "
                            "p.14).",
    },
    {
        "ent": "student-council",
        "claim": "Horikita Suzune joins the student council in the "
                 "second year, welcomed by President Nagumo as its only "
                 "second-year member besides Honami Ichinose.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Suzune's narration of her first day",
        "corroboration": "none",
        "refs": ["y2v2 p.350"],
        "confidence": 0.9,
        "reliability_note": "Joining narrated first-hand with Nagumo's "
                            "welcome on-page (y2v2 p.350).",
    },
    {
        "ent": "student-council",
        "claim": "Student council service is a budget channel: "
                 "festival preparation pays additional funds for it.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Festival outline box",
        "corroboration": "supported",
        "refs": ["y2v7 p.7"],
        "confidence": 0.85,
        "reliability_note": "Listed as additional-funds line in the "
                            "cultural-festival outline (y2v7 p.7).",
    },
    {
        "ent": "clubs",
        "claim": "The club fair runs in Gymnasium No. 1 at the start of "
                 "the school year, with membership settled as a funding "
                 "decision.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Start-of-year schedule narration",
        "corroboration": "supported",
        "refs": ["y1v1 p.59", "y1v1 p.64"],
        "confidence": 0.9,
        "reliability_note": "Fair venue and sign-up mechanics both "
                            "narrated in the first volume.",
    },
    {
        "ent": "clubs",
        "claim": "Club activities sit outside coursework but still run "
                 "under the school's strict rules.",
        "kind": "character_claim", "claimant": "sudou-ken",
        "perspective": "Sudou recounting his away game to Ayanokōji",
        "corroboration": "none",
        "refs": ["y1v4.5 p.13"],
        "confidence": 0.8,
        "reliability_note": "Second-hand from Sudou's playing experience "
                            "(y1v4.5 p.13); basketball is the recurring "
                            "example.",
    },
    {
        "ent": "expulsion",
        "claim": "Failing a written exam means forced expulsion: results "
                 "posts draw a red line and anyone under it is removed.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Results-day narration",
        "corroboration": "supported",
        "refs": ["y1v9 p.39", "y1v10 p.14"],
        "confidence": 0.9,
        "reliability_note": "Rule anticipated before the year-end exam "
                            "(y1v9 p.39) and drawn literally on the "
                            "board (y1v10 p.14).",
    },
    {
        "ent": "expulsion",
        "claim": "Class votes are an expulsion instrument: the first "
                 "Class Poll removed Totsuka Yahiko, Yamauchi Haruki "
                 "and Manabe Shiho, none from Class B.",
        "kind": "narrator_fact", "claimant": "narrator",
        "perspective": "Vote-results board narration",
        "corroboration": "none",
        "refs": ["y1v10 p.315"],
        "confidence": 0.95,
        "reliability_note": "Posted results statement with no "
                            "class-point changes (y1v10 p.315).",
    },
    {
        "ent": "expulsion",
        "claim": "A senior's quota theory: last year's zero dropouts "
                 "were 'forcibly changed from zero to one expulsion', so "
                 "more may fall at the end-of-year exam.",
        "kind": "other_reported", "claimant": None,
        "perspective": "Third-year senior advising over winter break",
        "corroboration": "none",
        "refs": ["y2v11 p.197"],
        "confidence": 0.6,
        "reliability_note": "The speaker explicitly calls it speculation "
                            "with no concrete evidence (y2v11 p.197).",
    },
    {
        "ent": "expulsion",
        "claim": "Rumor holds that Maezono's end-of-year expulsion was "
                 "delivered on purpose as punishment for betraying her "
                 "class.",
        "kind": "other_reported", "claimant": "karuizawa-kei",
        "perspective": "Karuizawa relaying class gossip",
        "corroboration": "none",
        "refs": ["y2v12.5 p.81"],
        "confidence": 0.7,
        "reliability_note": "Gossip explicitly framed as what 'some even "
                            "say', offered without proof (y2v12.5 p.81).",
    },
]

REF_RE = re.compile(r"^(?P<vol>[a-z0-9.]+) p\.(?P<page>\d+)$")
CLAIM_KINDS = {"narrator_fact", "character_claim", "other_reported",
               "inference"}


def load_context():
    """mention spans per (entity, vol, page) for exams and systems,
    plus the raw page-text cache."""
    con = sqlite3.connect(DB_PATH)
    mentions = {}
    for eid, vol, page, s, e in con.execute(
            "SELECT exam_id, vol_id, pdf_page, span_start, span_end "
            "FROM exam_mentions"):
        mentions.setdefault(("exam", eid, vol, page), []).append((s, e))
    for sid, vol, page, s, e in con.execute(
            "SELECT sys_id, vol_id, pdf_page, span_start, span_end "
            "FROM system_mentions"):
        mentions.setdefault(("sys", sid, vol, page), []).append((s, e))
    char_ids = {r for r, in con.execute("SELECT char_id FROM characters")}
    con.close()
    pages = {}
    for vol, _stem, page, pstart, text in iter_pages():
        pages[(vol, page)] = (pstart, text)
    return mentions, pages, char_ids


def validate_refs(kind, ent, refs, mentions, pages, label):
    """every ref: real page + entity mention + in-bounds span.
    returns (anchor_span, error)."""
    if not refs:
        return None, f"{label}: no refs"
    span = None
    for i, ref in enumerate(refs):
        m = REF_RE.match(ref.strip())
        if not m:
            return None, f"{label}: bad ref format {ref!r}"
        vol, page = m.group("vol"), int(m.group("page"))
        bounds = pages.get((vol, page))
        if bounds is None:
            return None, f"{label}: unknown page {vol} p.{page}"
        spans = mentions.get((kind, ent, vol, page))
        if not spans:
            return None, f"{label}: no mention of {ent} at {vol} p.{page}"
        pstart, text = bounds
        for s, e in spans:
            ls, le = s - pstart, e - pstart
            if ls < 0 or le < ls or le > len(text):
                return None, f"{label}: bad span {s}-{e} at {vol} p.{page}"
        if i == 0:
            span = (vol, page, spans[0][0], spans[0][1])
    return span, None


def evidence_quote(kind, ent, refs, mentions, pages):
    """verbatim slice ±80 (page-local) around first mention of refs[0]."""
    m = REF_RE.match(refs[0].strip())
    if not m:
        raise ValueError(f"bad ref format {refs[0]!r}")
    vol, page = m.group("vol"), int(m.group("page"))
    pstart, text = pages[(vol, page)]
    s, e = mentions[(kind, ent, vol, page)][0]
    a = max((s - pstart) - 80, 0)
    b = min((e - pstart) + 80, len(text))
    return text[a:b]


def main():
    con = sqlite3.connect(DB_PATH)

    if "--pack" in sys.argv:
        _mentions, pages, _c = load_context()
        chrono = [v for v, in con.execute(
            "SELECT vol_id FROM volumes ORDER BY chrono_order")]
        order = {v: i for i, v in enumerate(chrono)}
        for table, col in (("exam_mentions", "exam_id"),
                           ("system_mentions", "sys_id")):
            ents = [r for r, in con.execute(f"SELECT DISTINCT {col} FROM {table}")]
            for ent in sorted(ents):
                counts = con.execute(
                    f"SELECT vol_id, count(*) FROM {table} WHERE {col}=? "
                    "GROUP BY vol_id", (ent,)).fetchall()
                print(f"=== {ent} — {sum(c for _v, c in counts)} mentions ===")
                print("  by vol:", ", ".join(f"{v}:{c}" for v, c in sorted(
                    counts, key=lambda x: order.get(x[0], 999))))
                samples = con.execute(
                    f"SELECT vol_id, pdf_page, span_start, span_end FROM "
                    f"{table} WHERE {col}=? ORDER BY vol_id, pdf_page "
                    "LIMIT 5", (ent,)).fetchall()
                for vol, page, s, e in samples:
                    pstart, text = pages[(vol, page)]
                    frag = re.sub(r"\s+", " ", text[
                        max(0, s - pstart - 70):e - pstart + 70])
                    print(f"  {vol} p.{page}: …{frag}…")
        con.close()
        return 0

    mentions, pages, char_ids = load_context()
    known_exams = {e for e, _n, _k, _a in EXAM_IDS}
    known_sys = {s for s, _n, _k, _a in SYS_IDS}

    # validate authored content before any write
    errors = []
    for eid, prose in EXAMS_PROSE.items():
        if eid not in known_exams:
            errors.append(f"EXAMS_PROSE: unknown exam {eid}")
        for field in ("rules_summary", "points", "conditions",
                      "organizer", "notes"):
            if not prose.get(field, "").strip():
                errors.append(f"EXAMS_PROSE {eid}: empty {field}")
    for eid in known_exams:
        if eid not in EXAMS_PROSE:
            errors.append(f"EXAMS_PROSE: missing prose for {eid}")
    for sid, prose in SYSTEMS_PROSE.items():
        if sid not in known_sys:
            errors.append(f"SYSTEMS_PROSE: unknown system {sid}")
        for field in ("function", "notes"):
            if not prose.get(field, "").strip():
                errors.append(f"SYSTEMS_PROSE {sid}: empty {field}")
    for sid in known_sys:
        if sid not in SYSTEMS_PROSE:
            errors.append(f"SYSTEMS_PROSE: missing prose for {sid}")

    spans_cache = {}
    for inst in INSTANCES:
        label = f"instance {inst['exam']}#{inst['seq']}"
        if inst["exam"] not in known_exams:
            errors.append(f"{label}: unknown exam")
            continue
        if not (0 < inst["confidence"] <= 1):
            errors.append(f"{label}: confidence {inst['confidence']}")
        for field in ("chronology", "participants", "outcome"):
            if not inst[field].strip():
                errors.append(f"{label}: empty {field}")
        span, err = validate_refs("exam", inst["exam"], inst["refs"],
                                  mentions, pages, label)
        if err:
            errors.append(err)
        else:
            spans_cache[("inst", inst["exam"], inst["seq"],
                         inst["refs"][0])] = span
    seq_seen = {}
    for inst in INSTANCES:
        k = (inst["exam"], inst["seq"])
        seq_seen[k] = seq_seen.get(k, 0) + 1
    for (eid, seq), n in seq_seen.items():
        if n > 1:
            errors.append(f"duplicate instance seq {eid}#{seq}")

    for tag, claims in (("EXAM", EXAM_CLAIMS), ("SYS", SYSTEM_CLAIMS)):
        seen_n = {}
        for n, c in enumerate(claims, start=1):
            label = f"{tag} claim #{n} {c['ent']}"
            known = known_exams if tag == "EXAM" else known_sys
            if c["ent"] not in known:
                errors.append(f"{label}: unknown entity")
            if c["kind"] not in CLAIM_KINDS:
                errors.append(f"{label}: bad kind {c['kind']}")
            if not (0 < c["confidence"] <= 1):
                errors.append(f"{label}: confidence {c['confidence']}")
            if c["claimant"] is not None and c["claimant"] != "narrator" \
                    and c["claimant"] not in char_ids:
                errors.append(f"{label}: unknown claimant {c['claimant']}")
            for field in ("claim", "perspective", "reliability_note"):
                if not c[field].strip():
                    errors.append(f"{label}: empty {field}")
            kind = "exam" if tag == "EXAM" else "sys"
            span, err = validate_refs(kind, c["ent"], c["refs"],
                                      mentions, pages, label)
            if err:
                errors.append(err)
            else:
                spans_cache[("claim", tag, c["ent"], n)] = span
            seen_n[c["ent"]] = seen_n.get(c["ent"], 0) + 1
            if seen_n[c["ent"]] > 99:
                errors.append(f"{label}: >99 claims per entity")
    if errors:
        for e in errors:
            print("p9_analysis:", e)
        con.close()
        return 1

    # apply prose
    for eid, prose in EXAMS_PROSE.items():
        con.execute(
            "UPDATE exams SET rules_summary=?, points=?, conditions=?, "
            "organizer=?, notes=? WHERE exam_id=?",
            (prose["rules_summary"], prose["points"], prose["conditions"],
             prose["organizer"], prose["notes"], eid))
    for sid, prose in SYSTEMS_PROSE.items():
        con.execute("UPDATE systems SET function=?, notes=? WHERE sys_id=?",
                    (prose["function"], prose["notes"], sid))

    # apply instances
    exam_index = {e: i for i, (e, _n, _k, _a) in enumerate(EXAM_IDS)}
    con.execute("DELETE FROM exam_instances")
    for inst in INSTANCES:
        instance_id = (exam_index[inst["exam"]] + 1) * 100 + inst["seq"]
        span = spans_cache[("inst", inst["exam"], inst["seq"],
                            inst["refs"][0])]
        quote = evidence_quote("exam", inst["exam"], inst["refs"],
                               mentions, pages)
        con.execute(
            "INSERT INTO exam_instances (instance_id, exam_id, seq, "
            "vol_id, pdf_page, span_start, span_end, chronology, "
            "participants, outcome, corroboration_refs, evidence_quote, "
            "confidence) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (instance_id, inst["exam"], inst["seq"], span[0], span[1],
             span[2], span[3], inst["chronology"], inst["participants"],
             inst["outcome"], json.dumps(inst["refs"]), quote,
             inst["confidence"]))

    # apply claims (per-entity id series)
    con.execute("DELETE FROM exam_claims")
    sys_index = {s: i for i, (s, _n, _k, _a) in enumerate(SYS_IDS)}
    for n, c in enumerate(EXAM_CLAIMS, start=1):
        claim_id = exam_index[c["ent"]] * 100 + \
            sum(1 for x in EXAM_CLAIMS[:n] if x["ent"] == c["ent"])
        span = spans_cache[("claim", "EXAM", c["ent"], n)]
        quote = evidence_quote("exam", c["ent"], c["refs"], mentions, pages)
        con.execute(
            "INSERT INTO exam_claims (claim_id, exam_id, claim, kind, "
            "claimant, perspective, corroboration, corroboration_refs, "
            "reliability_note, confidence, vol_id, pdf_page, span_start, "
            "span_end, evidence_quote) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (claim_id, c["ent"], c["claim"], c["kind"], c["claimant"],
             c["perspective"], c["corroboration"], json.dumps(c["refs"]),
             c["reliability_note"], c["confidence"], span[0], span[1],
             span[2], span[3], quote))
    con.execute("DELETE FROM system_claims")
    for n, c in enumerate(SYSTEM_CLAIMS, start=1):
        claim_id = sys_index[c["ent"]] * 100 + \
            sum(1 for x in SYSTEM_CLAIMS[:n] if x["ent"] == c["ent"])
        span = spans_cache[("claim", "SYS", c["ent"], n)]
        quote = evidence_quote("sys", c["ent"], c["refs"], mentions, pages)
        con.execute(
            "INSERT INTO system_claims (claim_id, sys_id, claim, kind, "
            "claimant, perspective, corroboration, corroboration_refs, "
            "reliability_note, confidence, vol_id, pdf_page, span_start, "
            "span_end, evidence_quote) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (claim_id, c["ent"], c["claim"], c["kind"], c["claimant"],
             c["perspective"], c["corroboration"], json.dumps(c["refs"]),
             c["reliability_note"], c["confidence"], span[0], span[1],
             span[2], span[3], quote))

    con.executescript(FTS_REBUILD)
    con.commit()
    n_notes = con.execute(
        "SELECT count(*) FROM exams WHERE notes IS NOT NULL").fetchone()[0]
    n_snotes = con.execute(
        "SELECT count(*) FROM systems WHERE notes IS NOT NULL").fetchone()[0]
    n_inst = con.execute("SELECT count(*) FROM exam_instances").fetchone()[0]
    n_ec = con.execute("SELECT count(*) FROM exam_claims").fetchone()[0]
    n_sc = con.execute("SELECT count(*) FROM system_claims").fetchone()[0]
    con.close()
    print(f"p9_analysis: prose exams {n_notes}/{len(EXAMS_PROSE)} "
          f"systems {n_snotes}/{len(SYSTEMS_PROSE)}  instances {n_inst}  "
          f"exam_claims {n_ec}  system_claims {n_sc}  fts ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

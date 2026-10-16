#!/usr/bin/env python3
"""P9-3: curated exam + system entities and aliases (idempotent, gate on hits).

python3 kb/p9_import.py

Run order: p9_init -> p9_import -> p9_mentions -> p9_analysis ->
           build_exam_dossiers.

Owns: exams identity (exam_id, name, kind), exam_aliases, systems
identity (sys_id, name, kind), system_aliases. Rebuilds exam_mentions /
system_mentions (they derive from the alias sets — any entity/alias
change invalidates them; p9_mentions restores them). Instances, claims
and authored prose (rules_summary/points/conditions/organizer/notes,
function) live in p9_analysis — not touched here; ids are stable slugs
so those rows survive. FTS refreshed at the end.

GATE: every curated alias form must hit the corpus >=1 time (macron
classes, word-aware) — a zero form means a typo and fails the run;
forms must be unique across exams AND systems.

Curation decisions came from kb/p9_mine.py + context probes (2026-10-16):

  exam arc pinning (probe evidence)
    cruise trip y1v3 = island week + ship week; island test rules y1v3
      p.27-40 (300 points / 7 days / wristwatch); ship week = zodiac
      twelve groups + traitor rules, narrated y1v4 (p.34 announce,
      p.45-47 traitor, p.125 Kouenji ends his group's test)
    y1v4.5 p.69 "results from the island test, and the test on the
      ship" = two named tests, one summer trip
    y2v2 p.119-120 "Uninhabited Island Survival" announced, explicitly
      compared to "last year's" island test -> one exam entity, two
      instances (Y1, Y2); y2v3 p.17 overview box (two weeks, groups,
      tasks in grid areas E7/G3/H5/D8...)
    class poll = class vote (y1v10 p.37 name + TOC chapter "The Class
      Vote"); unanimous vote = "Unanimous Voting exam" overview y2v5
      p.41; event selection named y1v11 p.28; survival and elimination
      named y2v10 p.144; end-of-year special (y2v11-12, expulsion
      stakes, traitor-heavy) distinct from written end-of-year exam
      (y1v9); comprehensive academic named y3v1 p.100 overview box
    y2v9 December exam = its own entity (coop-written-head-to-head):
      official bracket y2v9 p.13 "cooperative comprehensive written
      test" (100 questions, in-class turn order, OAA-weighted scoring),
      announced p.11 as "one-on-one academic competition" (rank
      pairings 1v2/3v4, 50 class points winner-takes, no expulsions),
      results p.215 (Horikita's class beat Sakayanagi's; Ichinose beat
      Ryuuen despite sabotage); distinct from end-of-year special
      (March, y2v12) and from regular written exams
    cultural festival = school festival variant (82 hits: y2v5 26 /
      y2v7 44 during the held Y2 festival, y1v11 p.19 the Y1 proposal
      to hold one "next year")
    zodiac test / zodiac game (y1v7 aftermath retrospectives + y2v9
      p.11) and mixed camp (y1v8 p.14 "Mixed Camp" naming) added after
      evidence-pack reads; each form >=1 hit verified by the gate

  excluded (recorded so the sweep is reproducible)
    student numbers   FULL PLAN suggested; ZERO corpus hits
    graduation-desire reward  probes ("any desire", "will be granted",
                      "graduating from class a") found no canonical
                      "desires granted" system phrasing — Class A
                      standing lives in class-points notes instead
    double-question   y1v4 chapter title for zodiac-ship test events,
                      not a separate exam
    written exam      bare form context-mixed (White Room y0 p.114
                      "7th written exam" vs monthly exams)
    zodiac (bare)     birth-year zodiac noise risk; "zodiac exam",
                      "zodiac test", "zodiac game" and "signs of the
                      zodiac" cover the exam
    traitor (as exam) traitor = zodiac-ship test mechanics, folded
                      into cruise-ship-exam conditions/notes
    field trip        7 hits, no rules/points documents (kyoto trip
                      already ballot-only in P8)
    ssh               8 hits, funding designation, no mechanics docs
    committee         2 hits, folds into clubs notes
    business/personal contracts (y0 tower deal, y2v11 Nagumo deals,
                      y2v12 Kōenji breach talk, y1v1 p.204 Horikita's
                      joke contract)  no formal student-contract
                      system found — expulsion entity covers the real
                      fail-midterm -> drop-out mechanics (y1v1 p.128-153)
    dropout/drop out  "drop out" 184 hits spread over exam-withdrawal
                      and White Room senses — too ambiguous to anchor
    special admission ZERO hits
    monthly exam      ZERO hits (corpus says midterm/final)
"""

import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster_mine import DB_PATH, iter_pages  # noqa: E402
from p9_init import FTS_REBUILD  # noqa: E402
from p8_mine import form_pattern  # noqa: E402

EXAM_KINDS = {"written", "special", "event", "entrance", "other"}
SYS_KINDS = {"points", "governance", "activity", "discipline",
             "admissions", "other"}

# exam_id, name, kind, [(raw_form, form_type), ...]
EXAMS = [
    ("midterm-final-written", "Midterm and Final Written Exams", "written",
     [("midterm", "full"), ("midterms", "variant"),
      ("final exam", "full"), ("end-of-year exam", "variant")]),
    ("uninhabited-island-exam", "Uninhabited Island Exam", "special",
     [("uninhabited island exam", "full"),
      ("uninhabited island survival", "variant"),
      ("uninhabited island special exam", "variant"),
      ("uninhabited island test", "variant"),
      ("island exam", "short"), ("island test", "short"),
      ("deserted island exam", "variant"),
      ("deserted island test", "variant")]),
    ("cruise-ship-exam", "Cruise Ship Exam", "special",
      [("cruise ship exam", "full"), ("cruise ship test", "variant"),
       ("test on the ship", "variant"), ("ship exam", "short"),
       ("ship test", "short"), ("zodiac exam", "alias"),
       ("zodiac test", "alias"), ("zodiac game", "alias"),
       ("signs of the zodiac", "epithet")]),
    ("paper-shuffle", "Paper Shuffle", "special",
     [("paper shuffle", "full")]),
    ("mixed-training-camp", "Mixed Training Camp", "special",
      [("mixed training camp", "full"), ("mixed camp", "variant")]),
    ("class-poll", "Class Poll", "special",
     [("class poll", "full"), ("class vote", "variant")]),
    ("event-selection-exam", "Event Selection Exam", "special",
     [("event selection", "full")]),
    ("unanimous-vote-exam", "Unanimous Vote Exam", "special",
     [("unanimous vote", "full"), ("unanimous voting", "variant"),
      ("unanimous special exam", "variant")]),
    ("survival-elimination-exam", "Survival and Elimination Exam", "special",
     [("survival and elimination", "full")]),
    ("end-of-year-special-exam", "End-of-Year Special Exam", "special",
     [("end-of-year special", "full")]),
    ("comprehensive-academic-exam",
     "Comprehensive Academic Ability Exam", "special",
     [("comprehensive academic", "full")]),
    ("sports-festival", "Sports Festival", "event",
     [("sports festival", "full")]),
    ("school-festival", "School Festival", "event",
      [("school festival", "full"), ("cultural festival", "variant")]),
    ("entrance-exam", "Entrance Exam", "entrance",
      [("entrance exam", "full")]),
    ("coop-written-head-to-head", "Cooperative Comprehensive Written Exam",
     "special",
      [("cooperative comprehensive written test", "full"),
       ("one-on-one academic competition", "variant"),
       ("in the academic competition", "variant"),
       ("head-to-head matchup", "short")]),
]

# sys_id, name, kind, [(raw_form, form_type), ...]
SYSTEMS = [
    ("private-points", "Private Points", "points",
     [("private points", "full")]),
    ("class-points", "Class Points", "points",
     [("class points", "full")]),
    ("student-council", "Student Council", "governance",
     [("student council", "full"), ("election", "variant")]),
    ("clubs", "Clubs", "activity",
     [("club", "full")]),
    ("expulsion", "Expulsion Rules", "discipline",
     [("expulsion", "full"), ("expelled", "variant")]),
]


def corpus_hits(forms):
    """forms -> {form: total hits}; one corpus pass, all regexes."""
    compiled = {f: re.compile(rf"\b{form_pattern(f)}", re.I)
                for f in forms}
    hits = dict.fromkeys(forms, 0)
    for _vol, _stem, _page, _s, text in iter_pages():
        for form, rx in compiled.items():
            n = len(rx.findall(text))
            if n:
                hits[form] += n
    return hits


def main():
    forms = [f for _i, _n, _k, aliases in EXAMS + SYSTEMS
             for f, _t in aliases]
    dup = {f for f in forms if forms.count(f) > 1}
    if dup:
        print(f"p9_import: duplicate alias forms {sorted(dup)}")
        return 1
    for exam_id, _name, kind, _a in EXAMS:
        if kind not in EXAM_KINDS:
            print(f"p9_import: {exam_id} bad kind {kind!r}")
            return 1
    for sys_id, _name, kind, _a in SYSTEMS:
        if kind not in SYS_KINDS:
            print(f"p9_import: {sys_id} bad kind {kind!r}")
            return 1
    hits = corpus_hits(forms)
    zero = [f for f in forms if hits[f] == 0]
    if zero:
        print(f"p9_import: zero-hit alias forms {zero}")
        return 1

    db = sqlite3.connect(DB_PATH)
    db.execute("DELETE FROM exam_mentions")
    db.execute("DELETE FROM exam_aliases")
    db.execute("DELETE FROM exams")
    db.execute("DELETE FROM system_mentions")
    db.execute("DELETE FROM system_aliases")
    db.execute("DELETE FROM systems")
    for exam_id, name, kind, aliases in EXAMS:
        db.execute(
            "INSERT INTO exams (exam_id, name, kind) VALUES (?,?,?)",
            (exam_id, name, kind))
        for raw, ftype in aliases:
            db.execute(
                "INSERT INTO exam_aliases "
                "(exam_id, raw_form, normalized, form_type) "
                "VALUES (?,?,?,?)",
                (exam_id, raw, raw, ftype))
    for sys_id, name, kind, aliases in SYSTEMS:
        db.execute(
            "INSERT INTO systems (sys_id, name, kind) VALUES (?,?,?)",
            (sys_id, name, kind))
        for raw, ftype in aliases:
            db.execute(
                "INSERT INTO system_aliases "
                "(sys_id, raw_form, normalized, form_type) "
                "VALUES (?,?,?,?)",
                (sys_id, raw, raw, ftype))
    db.executescript(FTS_REBUILD)
    db.commit()
    n_ex = db.execute("SELECT count(*) FROM exams").fetchone()[0]
    n_ea = db.execute("SELECT count(*) FROM exam_aliases").fetchone()[0]
    n_sy = db.execute("SELECT count(*) FROM systems").fetchone()[0]
    n_sa = db.execute("SELECT count(*) FROM system_aliases").fetchone()[0]
    db.close()

    print(f"p9_import: {n_ex} exams  {n_ea} exam aliases  "
          f"{n_sy} systems  {n_sa} system aliases  "
          f"(mentions cleared — rerun p9_mentions)")
    for exam_id, name, kind, aliases in EXAMS:
        detail = " · ".join(f"{f}={hits[f]}" for f, _t in aliases)
        print(f"  exam  [{kind:8s}] {exam_id:28s} {detail}")
    for sys_id, name, kind, aliases in SYSTEMS:
        detail = " · ".join(f"{f}={hits[f]}" for f, _t in aliases)
        print(f"  sys   [{kind:11s}] {sys_id:28s} {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

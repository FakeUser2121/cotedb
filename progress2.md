# PROGRESS 2 — Encyclopedia Walk (Phase 10)

Status: ACTIVE — pilot A1 (Ayanokōji × y1v1)

## Method (locked, plan v5 / user GO)
Walk loop per entity×volume: locate (alias regex, macron-folded) → read pages
linearly in chunks → write ledger entries immediately → append position marker.
POV characters: full linear volume read (name-hits are anchors for others' moments).
Ledgers: `ledgers/people/<char_id>.md` (+ exams/places/systems/concepts/volumes).
Every locator-hit page gets an entry or an explicit `passing mention` note.
Ledger tag grammar: [scene] [says] [thinks] [trait] [voice] [feat] [limit]
[rel:<id>] [status] [back] [rule] [exam:<id>] [place:<id>] [class:<id>] [trivia]

## Tooling
- kb/walk_locate.py — vols | locate --char --vol | extract --vol --pages
- aliases from cote_kb.db (aliases table, is_noise=0), fold = NFKD + strip combining

## Walk accounting
| entity | vol | pages | chunks done | hit-lines | coverage | status |
|---|---|---|---|---|---|---|
| ayanokouji-kiyotaka | y1v1 | 264 | 13/13 | 121 | 264/264 | DONE |

## Session log
- A1 start: walk_locate.py written + tested (35 vols listed, y1v1=264 pp).
- y1v1 linear walk COMPLETE (13 chunks, pp.1-264): ledger
  ledgers/people/ayanokouji-kiyotaka.md (55 scene entries, order verified
  p.14→p.263; orphan p.162-180 block reinserted).
- Key ledgered beats: equality monologue; Horikita coercion; all-50s reveal;
  pawn offer; rooftop Kushida unmasking; Manabu night fight; past-paper heist;
  Sudou fake-expulsion + point purchase; party recruitment to Class A plan.
- Corrections vs old DB: red-haired delinquent = Sudou (not Ryuuen); the
  bus-seat uniformed girl = Kushida (unnamed until p.35).
- Pilot deliverables assembled (kb/ledger_transcript.py renders ledger →
  transcript view; 194 speech/thought lines):
  drafts/people/ayanokouji-kiyotaka.y1v1.transcript.md
  drafts/people/ayanokouji-kiyotaka.article.md (Person skeleton, y1v1-scoped)
- Fact-trace spot gate: 12/12 key article quotes verified vs corpus after
  fixing one page anchor (couldn't-go-lower: p.126→p.127).
- READY FOR USER CHECKPOINT (A1): review transcript + article.

## LLM extraction test track (T0–T3)
- Local server up: llama.cpp, MiMo-V2.6-Distill-Qwen-9B-Q6_K, :9931, n_ctx 32000.
- kb/llm_extract.py: chapters/smoke/extract; JSON-schema constrained; snippets
  located in corpus bytes (model never authors final quote text or pages);
  auto-split on truncation; drafts → drafts/llm/.
- T0 smoke PASS (35 items). T1 gold y1v1 ch1-2: 390 items, 88% recall vs ledger.
- T2 blind y1v2 ch1: 245 items, 700s. 100% review done:
  precision 91.8% (13 wrong-speaker + 6 wrong-type + 1 minor),
  utterance recall 85% (29/192 missed, mostly short lines),
  page claims 13.5% wrong pre-correction → 0 post,
  judgment tags trait/voice/limit = 0 (model cannot do judgment layer).
- Review tooling built (context dump + auto-flagger) → ~10-15 min/chapter review.
- T3 verdict written: drafts/llm/T3-verdict.md → CONDITIONAL PASS
  (mechanical assistant + mandatory review; ~30-40% walk savings est.).
- USER DECISION: SKIP LLM — test did not justify the review overhead vs
  unchanged reading requirement. Pipeline deleted (kb/llm_extract.py,
  drafts/llm/ incl. T3-verdict, server stopped). Numbers above stand as the
  record of why. Walk proceeds manual per plan v6.
- Side queue: ledger_transcript.py DISPLAY map still has pre-rename ids
  (sudou, chiyabashira-sae, koenji-souta, yamauchi) → update + regenerate.

## Walk: chapter detector & y1v1 fidelity repair
- kb/walk_locate.py `chapters` final: ALL 36 volumes clean (bad=0). Fixes:
  spelled-out chapter numbers; TOC-continuation skip (≥2 section tags/page);
  exact-or-wrap TOC title fill-in (loose substring fallback removed); dialogue
  guard rejects quote-openers/long lines (fixes y1v10 titles); running-header
  ｜-cut (v0); HEADER_NOISE applied only to non-section lines.
- y1v1 sections: 13 (ch1=p.14-15, ch2=p.16-53, ch3=54-71, ch4=72-88,
  ch5=89-101, ch6=102-119, ch7=120-151, ch8=152-202, ch9=203-235,
  ch10=236-245, ch11=246-255, ch12=256-262, postscript=263-264).
- FIDELITY CRISIS found & fixed: prior-session fill-pass ledgers contained
  ~55 fabricated [says] quotes (Yen-Press/anime memory). Repair pass done
  file-by-file vs corpus extracts (verifier = NFKC + alnum-stream containment,
  page windows ±5 then full, footer/header lines stripped).
- Final state: 474 [says] lines ALL PASS; 177 non-says quoted lines checked —
  all corpus-exact except 2 confirmed extractor artifacts (labels verified
  manually). Verifiers: /tmp/opencode/verify2.py (says) + verify3.py (non-says;
  handles (p.N)/(pp. N) anchors, ±5-page then full-volume).
- Notable corpus-exact keeps: EMTL "Kouejin-kun" (p.87), "would be been fine
  either way" (p.53), "When did I stab with you a compass needle" (p.152).
- Attribution corrections: bus-challenger lines (p.19-20) are the office
  lady's, uniformed girl enters p.21; her identity as Kushida = inference,
  noted in ledger. horikita club-"betrayal" section rewritten to actual
  p.59-62 club/violence content ("betrayal" has zero corpus hits).
- Volume-ledger fabrication sweep (found when verify3 gained pp.-anchor
  support): ch2 "I don't need you", ch3 corridor lunch-invite/"truly prefers
  alone" quote/contact-swap, ch3 betrayal philosophy, ch4 "natural muscle",
  ch5 "accidentally", ch7 "defective goods", ch7 "holding hands with dead
  weight" — all replaced with corpus-exact content (actuals: "Do you mind if
  I refuse?" + "avoids trouble" verdict; "hasn't talked to anybody yet, so
  I'm a little worried"; handshake not number-swap; violence-justification
  speech; "born naturally muscular"; staged coincidence; "last bastion for
  failures… You're defective"; "I refuse. I won't participate.").
- ch8 (p.152-202) entries WRITTEN for sudou-ken, ike-kanji, yamauchi-haruki,
  hirata-yousuke, chabashira-sae, point-economy, volumes/y1v1 (Ch.8: The
  Association of Failures), and NEW places/school-library.md. horikita/
  kushida/manabu/AK already had ch8; absent-from-ch8 ledgers get no marker
  by rule. NEXT: ch9 (p.203-235).

## Walk: y1v1 ch9 done (p.203-235)
- Entries written: horikita (reunion/"I hate you"/in-class plan), kushida
  (Class A ask, ally test, secret bond), sudou (apology standoff → date bribe
  → club-break pledge, Yamawaki collar), ike (Bacon triumph, 51-pt bid),
  yamauchi (52-pt bid), hirata (avoided rival + test-notice recipient),
  chabashira (test-change "mistake" section), ichinose (LIBRARY DEBUT scene,
  Yamawaki de-escalation), hoshinomiya (faculty smile), kouenji (Palate
  third-year court), point-economy (15,000-pt old-test trade, free-meal
  seller strategy), NEW ledgers/exams/midterm-exam.md (stakes/scope change/
  old-test pipeline), school-library (comeback sessions + Class C incident),
  keyaki-mall (Palate truce + rankings lunch), volumes/y1v1 Ch.9.
- Verifiers post-ch9: 522 [says] ALL PASS; 198 non-says (2 known artifacts).
  7 paraphrase-in-quote-marks fails found & fixed ("there was a way for us
  to pass this test", "like I was his ancestral enemy", "a third-year student
  you're close to", "workhorse" contract quote).
- NEXT: ch10 (p.236-245), ch11 (p.246-255), ch12 (p.256-262), postscript
  (p.263-264) → Checkpoint A1.

## Walk: y1v1 ch10 done (p.236-245)
- Entries: horikita (hate-confirmation 2.0 + basketball-court apology),
  kushida (podium call-out + "I really hate you"), sudou (English-gap
  crush→despair, Kang Soo-jin reference), ike (test-day conduct), yamauchi,
  hirata (test-day conduct), chabashira (leftover-drug lines + island-
  vacation reward reveal), NEW ledgers/exams/midterm-exam.md (execution
  rules/day-of conduct), volumes/y1v1 Ch.10.
- Verifiers post-ch10: 554 [says] ALL PASS; 207 non-says (2 known artifacts).

## Walk: y1v1 ch11 done (p.246-255) — the crisis chapter
- Entries: chabashira (red line, 40-not-32 bombshell, pass-grade formula
  79.6/2 rounded up, guardian processing, rounding-kill of Horikita's decimal
  trap, hallway fairness debate, "at this stage" hedge, old-test praise,
  100,000-pt single-point sale, "watch over you"), horikita (first-ever
  voluntary remark, 51-point English sacrifice revealed, "did this for my
  own sake", joins the point purchase, "defective, not trash / with repairs,
  a defective product may become a superior article", side-chop), sudou
  (celebration→red line→rage, learns who saved him), hirata (first protest,
  answer-sheet audit), ike ("You said so, sensei!"), yamauchi (cheer),
  kushida (shared relief glance), point-economy (buying an exam point =
  100,000 pts, two-payer ID transfer), midterm-exam (results + true pass
  rule + buyback), volumes/y1v1 Ch.11.
- Fixed 1 self-inflicted glue artifact (volume ch11 line: "too bad" 7-char
  span → widened to "Well, too bad."). Verifiers: 591 says ALL PASS;
  221 non-says (2 known artifacts).

## Walk: y1v1 ch12 + postscript done (p.256-264) — VOLUME COMPLETE
- ch12 entries: horikita (party presence, own-sake line, secret-keeping,
  points reality, no-burden warning), kushida (Class A recruitment pitch +
  proverb volley), sudou (reformed bickering, enlistment, headlock),
  ike (room-choice banter, Class A shock, Gladly, tease), yamauchi
  (braggart retcon, Gladly), point-economy (no points for worst class,
  free-offerings survival), volumes/y1v1 Ch.12 + Postscript section
  (Kinugasa thesis: academics aren't everything; Tomose Shunsaku; editor
  I-sama; spring 2015; insomnia).
- Verifiers FINAL y1v1: 626 [says] ALL PASS (10 short/skipped, all
  manually corpus-verified); 230 non-says — only the 2 known extractor
  artifacts (AK L272, Sudou L25).
- **y1v1 walk COMPLETE** (ch1→ch12 + postscript). All 16 census ledgers +
  3 places + midterm-exam + volumes/y1v1 carry chapter markers.

## Checkpoint A1 deliverables ready — awaiting USER REVIEW
- Transcripts rendered via kb/ledger_transcript.py:
  drafts/people/horikita-suzune.y1v1.transcript.md (174 lines),
  drafts/people/kushida-kikyou.y1v1.transcript.md (91 lines).
- Articles hand-written to the AK pilot template (lede, spoiler scope,
  infobox, personality, abilities table, story summary, relationships,
  voice samples, transcript link, trivia, sources, categories):
  drafts/people/horikita-suzune.article.md,
  drafts/people/kushida-kikyou.article.md.
- New verifier /tmp/opencode/verify_articles.py: all quoted spans in
  drafts/*/*.article.md vs y1v1 corpus — 87 spans ALL PASS. Fixed 1 genuine
  fidelity error found in the approved AK pilot article (voice sample had
  dropped "on the other hand,": now exact p.127 corpus) + 1 self-inflicted
  double-dialogue glue in the Horikita article (split into two spans).

## Site pass — human naming, navigation, no jargon (user directives)
- User feedback: "walk", "Phase 10", "Checkpoint A1", "dossier", and
  cote_kb.db/regenerate notes mean nothing to visitors; organization + search
  matter more than encyclopedic mass; design must be good-looking,
  human-navigable, final.
- Section renamed walk → **Volume 1 (Year 1)** (paths vol1/, 6 pages — the
  approved AK guide+transcript now published alongside the A1 pair).
  Sidebar final: Home · Characters · Volume 1 (Year 1) · World & Locations ·
  Exams · School Systems. Home cards reworded (profiles/guides/transcripts,
  no separate Background card); search placeholder "Search characters,
  scenes, exams… (press /)"; footer explains "y1v1 p.247 = Year 1, Volume 1,
  page 247" instead of db instructions; kicker "Year 1 · Volume 1".
- Transcript renderer humanized: titles/headings "Year 1, Volume 1, p.NN–MM",
  dropped the "Source ledger / rendered by" line; re-rendered AK/Horikita/
  Kushida transcripts.
- Articles humanized (Sources, transcript links, spoiler lines, "Vol. 1"
  citations instead of y1v1); verifiers stay green: 87 article spans ALL
  PASS, 626 says ALL PASS, 230 non-says = the 2 known extractor artifacts.
- Dossier generators: removed "generated view (source: cote_kb.db…)", tier
  and char_id lines; new index intros and titles (All Exams, All Systems,
  All Locations); regeneration also caught footprint stats up to y3v2/y3v3
  already present in the db.
- Nav fixes: current section auto-expands; overview leaves highlight (fixed
  duplicate class attribute); Mid overview link added (mid index was
  unreachable from the sidebar); ghost "INDEX.HTML" tag on mid index fixed.
- PDFs now built inside build_share_site (chromium print-to-pdf →
  share/site/pdfs) so the clean-build wipe cannot drop them; *.pdf excluded
  from md5 determinism (chromium timestamps). Build output: 89 pages + 899
  search records + 6 print docs + 6 PDFs; md5
  91185875b554ca9c1b5d6786789b3404 stable across rebuilds.
- Verified: local crawl 90 pages / 99 links / 0 bad; jargon grep over
  docs/ clean; screenshots reviewed (home, vol1 hub, transcript, main, mid).

## Checkpoints
- [x] A1 deliverables built — awaiting USER REVIEW of the 4 Horikita +
      Kushida files in drafts/people/ (AK pair already approved)
      (deliverables ready in drafts/people/)
- [ ] A2 mains (6 more)
- [ ] A3 exams/systems/places
- [ ] A4 mid + background
- [ ] A5 volumes/topics/timelines
- [ ] A6 site v2 + publish

## Phase 11 — site architecture (this file is the WALK log; site work moved on)
- The user redirected: make the website good-looking, organized and intuitive
  FIRST — "if the main architecture is bad, no matter how much information
  there is it won't matter". No subagents for it.
- That work is logged turn-by-turn in **progress3.md** (new architecture spec,
  design system, link gate, wording table, publish). Read it before assuming
  anything about the site layer; progress2.md no longer carries site history.
- Consequence for the walk: y1v2…y3v3 ledger data now has a place to land —
  `story/v/<vol>/` pages, per-character volume guides and transcripts render
  from `drafts/` automatically, and minor characters go to initial pages by
  rule, so ledger output does not need bespoke pages.
- Walk state unchanged by the site pass: y1v1 COMPLETE (626 [says] ALL PASS).
  `ledgers/*` carries **uncommitted y1v2 entries** written 19:56–20:03 by the
  walk session that was interrupted; they were deliberately left out of the
  site commit and still need the y1v2 coverage gate (task #3 here).

## Site pass 2026-10-26 22:3x — what the walk needs to know

- The site now publishes **only** ledger + y1v1-draft evidence; the pre-walk
  dossier layer is out of the build and moved to `archive/dossiers/` (its text
  must never be copied into a ledger, draft or page). Full detail in progress3.md.
- The interrupted y1v2 ledger entries were verified before publishing:
  `kb/verify2.py y1v2` → 172 [says] ALL PASS (4 too short/skipped);
  `kb/verify3.py y1v2` → 96 non-says ALL PASS. They render as "Partway" pages, so
  task #2/#3 here remain open — the volume still needs finishing to p.261.
- Writing rule learned by the renderers, not the walk: `## <vol> WALK COMPLETE`
  and `walk:/coverage:` stamps stay in the file and are now filtered at build
  time; volume keys used as words inside a note ("her y1v2 arc") are humanized to
  "Vol. 2" on render. Keep writing them however the walk likes — the build
  translates.

## Role facts — the new `[role:…]` line (2026-10-27)

The People index no longer files anyone under allies/rivals/classmates. That
column (`characters.mid_type`) is retired: it stored a relation as if it were
a property, named no subject, carried no volume, and 13 of its 27 rows had no
ledger behind them. Full write-up in progress3.md.

**What the walk writes instead.** When a page states where someone stands in
the school, record it as an entry, in their own ledger, inside the volume and
scene block it was read in:

```
[role:class-1d] (p.102) Named in Class 1-D's "Idiot Trio" with Ike and Yamauchi.
[role:student-council] (p.141) Member and liaison for the Student Council.
[role:faculty] (p.30–32) Japanese history; Class D homeroom for three years.
```

Rules the gate now enforces (`kb/share_check.py`):

- the value is one of `class-1a` `class-1b` `class-1c` `class-1d`
  `student-council` `faculty` — a closed set, so the build never interprets
  prose;
- the entry **must** carry a page anchor; an unanchored role is dropped and
  reported;
- one line per person per volume. A transfer, a promotion or a change of class
  is a **new line under the new volume**, never an edit to the old one. That is
  the whole point: the old scheme could not represent a change.

**Do not** put the typing back in the meta header. `status: mid (allies)` and
the bare `class: Class 1-D (enrolled April 2015)` are ignored by the build and
must not be extended — they are the pre-walk classification, and a permanent
header is the wrong shape for a fact that changes by volume.

**Open for the walk.** Three ledgers have scenes but no role line, so the index
lists them as "not stated": `hirata-yousuke` (scenes in the 1-D room,
p.32–34, 37–40, 55–56), `kouenji-rokusuke` (p.38–39), `sakura-airi` (scenes at
the store and in y1v2, none in a classroom). Add one anchored `[role:…]` line
the next time any of them is touched. Of the 27 principal/recurring names, 18
have no stated post yet: 3 have a ledger without a role line (the three above)
and 15 have no ledger at all; they fill in as their volumes are walked. Ike and
Yamauchi sit on tier 3 by quoted-line count but do have ledgers and role lines,
so they appear under Class 1-D — the role section is not limited to tier 1–2.

Role facts are shown on the site as plain page numbers, not proof chips,
because the note beside them is a paraphrase — the chip would open the page's
quote bank, which may not contain the supporting line. Do not turn them into
chips without adding the actual quoted line to the ledger.

### Rail hierarchy (site, 2026-10-27)

The People rail is now a real tree — `All people` contains its sections, and
`Roles in Vol. N` contains the institutional buckets. The component change
(`site_shell._rail_node`, depth classes, `.sub` guide) affects every rail but
only changes markup shape; no ledger or walk state was touched.

### Prologue re-walk and quote repair (2026-10-27)

y1v1 p.14–15 in `ayanokouji-kiyotaka.md` was a summary with one verbatim
sentence; it is now the full Chapter 1 monologue, eleven `[narrates]`
paragraphs, page-anchored, copied from `text/COTE Y1 V1.txt`. Checked by
normalized containment per paragraph (0 mismatches) and by confirming every
source line on p.14–15 appears in the ledger except the chapter title.

Rule reinforced: a quotation marks must wrap text that exists on the cited
page. Nine violations were repaired across ayanokouji/horikita/kushida and
the y1v1 volume ledger; see progress3 for the list. `verify3.py` now pairs
quotes correctly instead of matching closing quote → opening quote, which
had produced two false failures and could mask real ones.

### Layout pass (site, 2026-10-27)

CSS and the home template only: the `.measure` width cap, the hero grid, the
home prose columns. No ledger, walk state or coverage number changed; y1v2
remains unstarted at the same chapter mark. See progress3 for measurements.

### Scene links (site, 2026-10-27)

Recall and topic rows use the anchors `scene_block` already writes; no
ledger entry was edited and the walk position is unchanged.

### Ledger row fix (site, 2026-10-27)

Rendering only: `site_evidence.entry_html` now keeps a row's note, speaker
and page inside one body cell, and the phone masthead no longer overflows.
No ledger line was edited; the walk position (y1v2 ch1 still unstarted) and
every coverage number are unchanged. See progress3 for measurements.

### Page-number affordance (site, 2026-10-27)

Markup and CSS only: row page numbers are plain reference text again, the
scene chip keeps the only click target and now shows a caret, and cross-page
summary numbers link with an arrow. No ledger line was edited and the walk
position is unchanged (y1v2 ch1 still unstarted). See progress3 for counts.

### One disclosure per scene, then no citation chip at all (site, 2026-10-27)

Supersedes the caret in the entry above: the page chip is gone from the site
entirely, not just from scene headings.

Rendering, CSS and gate only: a scene has one expander, its fold, and the page
range in its heading prints as the same grey reference text a row uses; a
citation in guide or appendix prose is reference text too, because an inline
`<details>` closes the paragraph around it and split a guide's 21 paragraphs
into 53 blocks. `share_check.check_disclosures()` fails the build if a chip is
ever placed inside a scene or a ledger again.

No ledger line was edited; the walk position (y1v2 ch1 still unstarted) and
every coverage number are unchanged — 388 scenes, 764 search records, 668
cross-page arrow links, 3872 plain page references where 3477 were. See
progress3 for the measurements.

### y1v2 Chapters 1–3 are now in every ledger they touched (walk, 2026-10-27)

Walk position moves for the first time in this run: **y1v2 ch1–ch3 read and
written, next unit is Ch.4 "An Unexpected Witness" (pp.66–151, two sub-reads)**.
Chapters 1–3 had been read earlier and recorded only in Ayanokōji's own file,
so this pass was not a new read — it was pp.40–65 re-opened and the chapter's
owed entries written into the other ledgers from the same scenes.

Fanned out this pass: Ike Kanji (3 scene blocks — homeroom accusation pp.41–48,
the phone/ranking/contest confession pp.50–53, Class B doorway pp.61–64),
Yamauchi Haruki (3 — the one sentence that breaks Kushida's appeal pp.42–45,
the crush council pp.48–52, the doorway pp.54–63), Sakura Airi (1 — the
witness who sits in the room and says nothing, pp.40–65),
`systems/point-economy` (the disciplinary case as a points problem, pp.40–61),
`exams/midterm-exam` (new `## y1v2` section: the midterm's social residue being
spent on Sudou, pp.45 and pp.52–53) and `volumes/y1v2` (Chapter 3 section with
setting, four beats, page map, entities, open threads). Ayanokōji's file gained
two interior lines it had skipped (his "just like stalking" verdict, p.50; his
pity for Kushida, p.50) and one anchor that had been sitting on the wrong page.

Attribution discipline, because Chapter 3 is a crowded lunch table: every line
above is written only where the translation names the speaker or fixes it by an
act ("Ike was the first to talk", "said a disappointed Ike", "Ike put his arm
around my shoulder", "Yamauchi said it twice", "Yamauchi glanced at Horikita").
Where two boys could have said it — the pool-and-girlfriend plan, the Envy Tax,
the contest proposal, the "7 outta 10" replies — the line was left out and the
ambiguity recorded in the volume section instead. Nothing in Sakura's block is
asserted as fact: her presence in the homeroom is labelled as inference, and
Ayanokōji's p.62 feeling of being watched stays an open thread rather than a
link to her.

Two pre-existing bugs surfaced by the fan-out and fixed: Kushida's and Sudou's
y1v2 scenes were filed under `## y1v1`, which is why their volume pages showed
Vol. 1 content, and Ayanokōji's Ike answer was anchored p.50 when the exchange
is on p.64.

Verification after the writing: `verify2 y1v2` 276 [says] lines (was 245),
`verify3 y1v2` 185 other quoted lines (was 149), both ALL PASS. The reader
wording gate then caught five lines of pipeline vocabulary that this fan-out
had introduced ("this ledger", "the walk to the entrance") and they are
rewritten in reader language; see progress3 for the site numbers.

### y1v2 Chapter 4: An Unexpected Witness is closed (walk, 2026-10-27)

Read pp.66–151 in three sub-reads (66–96, 97–115, 116–151) and fanned out to
every ledger the chapter touches: ayanokouji-kiyotaka, ichinose-honami,
sakura-airi, kushida-kikyou, horikita-suzune, sudou-ken, hirata-yousuke,
karuizawa-kei, ike-kanji, yamauchi-haruki, kouenji-rokusuke,
systems/point-economy, exams/midterm-exam, volumes/y1v2. 995 ledger lines added
against the previous commit; one brand-new volume section (Ichinose) and the
first Chapter 4 rows for Sakura, Kōenji, Karuizawa, Hirata, Ike and Yamauchi's
second halves.

What the chapter actually turns on, in the order the book spends it: the class's
homeroom audience about buying a class change (pp.68–72), Horikita naming a
witness off an observation nobody else logged (p.77), the approach failing in
public (pp.86–90), the special-building walk where Class B offers help (pp.97–
107), Horikita alone in his room saying the dangerous sentence (p.112), then
eleven pages that are not about Sudō at all — the walk to school, the point
figures, the class-sorting theory and the confession behind the gymnasium
(pp.116–127) — before the witness is finally secured in a shopping mall by a
camera repair (pp.132–146). The chapter ends on three phone calls, none of them
finished (pp.147–151).

Attribution discipline, because this chapter is a two-hander with untagged
lines: a [says] row was written only where the translation names the speaker or
fixes it by an act ("I asked", "she replied", "the clerk said", "Kushida
murmured", "I cut Ichinose off before she could finish"). Four places where the
speaker is genuinely undecidable are recorded as gaps in the volume section
instead of being guessed — the modest reply in the p.129–130 phone exchange, the
"does she photograph people" question (p.142), the opening exchange of the p.147
night call, and "You kind of look suspicious…" (p.136).

Forward-only knowledge stays out of these rows. What the store clerk actually
recognises, and what the unnamed mall purchase becomes later in the volume, are
recorded as open threads at their real pages (pp.140, 143–144) and not written
into Chapter 4; the two-week repair is noted as outlasting the chapter, which is
what the chapter itself knows.

New named entities recorded: Ichinose's first name (p.109), Hoshinomiya-sensei
through Class B's report (p.108), Chihiro (pp.125–127), Sotomura "the Professor"
returning by name (p.143), Yukimura named once (p.119), the P.E. instructor
Higashiyama-sensei's 5000-point promise (p.71), and the school-licensed mall
stores with their clerk (pp.138–141).

Translation defects kept as printed rather than silently tidied: "My dry
laugher echoed" (p.118), "That…wasn’t in the any of the hundred million books"
(p.121), "I don’t how to respond" (p.124), "wellinformed" (p.142),
"Sudoukun"/"Ayanokoujikun" run-togethers (pp.116, 129). Each is flagged in the
row that carries it.

Housekeeping the fan-out exposed: repeated identical position stamps had
accumulated in six files (one per append, instead of one per chapter boundary).
A dedupe pass kept the last stamp of each kind, so each ledger now carries one
marker per chapter at its boundary. Verification after the writing:
`verify2 y1v2` **522** [says] lines (8 too short/skipped), `verify3 y1v2` **439**
other quoted lines, both ALL PASS. See progress3 for the site numbers and for
the renderer bug this chapter exposed.

### y1v2 Chapter 5: Each and Every Prediction is closed (walk, 2026-10-27)

Read pp.152–189 as one pass (the night before the deliberation through the
verdict and the aftermath), then fanned out to the ledgers the chapter actually
touches: ayanokouji-kiyotaka, sakura-airi, kushida-kikyou, horikita-suzune,
ichinose-honami, chabashira-sae, sudou-ken, ike-kanji, yamauchi-haruki,
systems/point-economy, volumes/y1v2. The chapter is a verdict, not a rescue:
the class spends pp.152–168 preparing and being examined, the deliberation and
its aftermath run pp.171–181, and the volume's second engine — the idol
photograph and the anonymous payout — is lit in the same stretch.

What the chapter turns on: Chabashira interrogating Sakura in the faculty room
and refusing to take the witness on trust (pp.163–165), the class's own
rehearsal and the two-seat limit for the hearing (pp.165–168), the deliberation
itself with the two observers (pp.171–178), the verdict and Sudou's release
(pp.178–181), and then the private consequences — the anonymous transfer, the
message board, and the magazine photograph that turns Sakura's secret into a
class problem (pp.181–189).

Attribution discipline: this chapter runs on untagged dialogue in the faculty
room and in the deliberation. A [says] row was written only where the
translation names the speaker or fixes it by an act; two places where the
speaker is genuinely undecidable are recorded as gaps in the volume section
instead of being guessed — the manga line at p.167 and the opening exchange of
the reveal at p.179 ("Wait, is that a picture of Shizuku?" / "Shizuku?" /
"She's a gravure idol…" are untagged until the next question names her). The
Kushida row that had guessed at the gravure line was corrected to a [note]
recording the gap rather than a [says] inventing a speaker.

Forward-only knowledge stays out. What the anonymous payer's design becomes and
what the magazine fight costs later are recorded as open threads at their real
pages (pp.157–158, 181–189), not written into this chapter's rows.

New named entities recorded: Kanzaki Ryūji (p.153), Shizuku (p.179, the idol
name and the girl behind it), and the detail that Ishizaki's grudge has a past
behind it (p.156). New system facts: the class homepage board (p.153), the
token key and its anonymous payout path (pp.157–158), the girls' floor curfew
after 8 PM (pp.169–170), and the two-observer rule at the deliberation (p.165).

Translation defects kept as printed: the p.167 manga line, whose speaker the
page never fixes, and the run-together names in the deliberation exchanges.

Housekeeping: the intended Chabashira [limit] row for the frog image (p.164)
was missing after the first fan-out even though the quote rendered on Sakura's
page; it was added at the faculty-room section and the site rebuilt. A places
ledger for the club-activities building was written and then deleted, because
world pages enumerate curated location rows and a new places ledger renders
nowhere; the building stays described in Sakura's 5.5 rows and the volume
setting. Verification after the writing: `verify2 y1v2` **624** [says] lines
(11 too short/skipped), `verify3 y1v2` **501** other quoted lines, both ALL
PASS. See progress3 for the site numbers and the determinism hash.

### y1v2 Chapter 6: Truth and Lies is closed (walk, 2026-10-27)

Read pp.190–219 in one pass (the hearing day from the morning check through the
retrial order and the entranceway), then fanned out to every ledger the chapter
touches: ayanokouji-kiyotaka, horikita-suzune, sakura-airi, sudou-ken,
ichinose-honami, chabashira-sae, hoshinomiya-chie, kushida-kikyou,
horikita-manabu, plus ike-kanji and yamauchi-haruki for the single look they
share on p.190, and three ledgers created for people the chapter gives a seat
at the table: kanzaki-ryuuji, tachibana (secretary, surname only), and sakagami
(the roster id already carried a mention-only stub). The volume also gains its
Chapter 6 section. Fourteen ledger files in all: eleven updated, three new.

What the chapter turns on, in the order the book spends it: the morning check
that Sakura came anyway (p.190), the student council room and the people in it
(pp.192–194), her twenty-second silence and the outburst that breaks it
(pp.199–200), the photographs — including the one the president finds that shows
the fight itself (pp.203–204), Sakagami's settlement offer and Chabashira's
acceptance of it (pp.205–206), Ayanokōji's performed surrender, Horikita's
damning closing statement and her refusal to sit (pp.206–208), the retrial order
with expulsion on the table (p.209), then the corridor with the president
(pp.210–212), the walk to the entranceway (pp.213–214), Class B's assessment and
offer (pp.214–215), and Horikita's request, the borrowed phone and the blow that
closes the account (pp.216–218).

Attribution discipline: this is the volume's most heavily untagged chapter. A
[says] row was written only where the translation names the speaker or fixes it
by an act; seven exchanges are recorded as gaps in the volume section instead
of being guessed — the opening courtesy at p.193, the procedural question at
p.196, the witness introduction and "You may begin your testimony" at p.199,
"What are those?" at p.203, "I think that you'll believe I was there after
seeing…this." at p.204, Class D's "I haven't lied…" at p.209, and the "eye for
an eye" reply at p.217. Quotes from other characters that are relevant to a
ledger but spoken by someone else are carried as [note], never as that
character's [says] — Kushida's p.191 send-off appears that way in three files.

Forward-only knowledge stays out: the retrial's outcome, the plan's content, the
Professor's device, and the borrowed phone's use are all recorded as open
threads at their real pages (pp.216–218), not written into this chapter.

New named entities: Horikita Manabu is named in narration for the first time in
this volume (p.208); Sakagami-sensei, Class C's homeroom teacher (p.193);
Secretary Tachibana (p.193, surname only); the Class C trio is fixed by name —
Komiya, Kondou and Ishizaki (pp.194–198). New system facts: the hearing's
composition and venue (p.192), the president's power to take over and the
secretary's role (p.193), the retrial window with expulsion as a possible
judgment (p.209), no extensions on request (p.209), and differentiated
suspension lengths within a settlement (p.205).

Translation defects kept as printed: "This are inadequate evidence" (p.204),
"Sakagamisensei's" as a run-together name (p.203–204), "Would be possible to
have a little more time" with the subject dropped (p.209).

housekeeping: creating a ledger named `sakagami-sensei` produced a second page
beside the roster's existing `sakagami` stub, because page ids come from the
roster or the ledger stem. The ledger was renamed to `sakagami.md` with
`char_id: sakagami`, so the full chapter now renders on the one page instead of
splitting the character in two. The audit that caught it also caught two
absences: Ike's and Yamauchi's p.190 glance at Sakura existed only on Sakura's
page, so two rows went into each of their ledgers, which moved the site hash
from `1d13757fddce1fb2e377854b95c65fc4` to the shipped
`4d4c5047d6dcf80f90afad6178a91bda`. Verification after the writing:
`verify2 y1v2` **843** [says] lines (22 too short/skipped), `verify3 y1v2`
**577** other quoted lines, both ALL PASS. See progress3 for the site numbers.

### y1v2 Chapter 7: Only One Solution is closed (walk, 2026-10-27)

pp.220–257 read whole in two passes (220–238, 239–257) and fanned into
fourteen ledgers: ayanokouji-kiyotaka, horikita-suzune, ichinose-honami,
sakura-airi, sudou-ken, chabashira-sae, horikita-manabu, sakagami, tachibana,
kanzaki-ryuuji, kushida-kikyou, hirata-yousuke, systems/point-economy,
volumes/y1v2, plus a new ledgers/people/ryuuen-kakeru.md — the roster already
carried the id, so he arrived as one principal-character page and the page count
stayed at 162. +443 lines in the tracked ledgers, 22 in the new file.

The chapter's own shape drove the fan-out: §7.0–7.4 is Ayanokōji on the path, in
the classroom, in the special-building corridor and at the shuttered electronics
store; §7.5 is Horikita's first-person retrial — the volume's second
different-narrator section after Sakura's cold open — which is where Chabashira's
lecture, the point fee and the private "defective products" session land; §7.6
returns to Ayanokōji for the secretary offer, the puppet question and the
corridor brush-off that names Ryuuen. The camera bluff belongs to Ichinose, the
hardware to Kanzaki, the email to Kushida, and the withdrawal's cost to the point
economy, so each of those went to its own ledger rather than being narrated twice
on one page.

This chapter was walked in a companion session and closed here, which meant an
audit pass against the source before anything shipped. Four real attribution
errors came out of it, all caught by reading the page rather than the row:
"Maybe because of what happened yesterday, she took a step forward on the path to
adulthood?" (p.222) and "Would you be happy if we'd compromised?" (p.220) are
printed with no speaker and had been logged as Ayanokōji's and Horikita's
respectively — both are now [note] rows and gaps in the volume section; Sakura's
"That's…" (p.238) is the narrator's stalled answer, since the page says he
"hesitated to speak without Sakura's permission" — moved to his ledger; and
"I'm done talking." sits on p.254, not p.255. Five lines that the chapter gives
these characters had also gone unrecorded (Ayanokōji's "I have no intension of
arguing…" at p.226, "Well. I'll be heading back now." and "You sort of forced me
to…" at p.254, Horikita's "Who are you?" at p.254), and Ichinose's §7.2 entrance
was worded as her leaving the building when the page has her stepping into a
corridor where the group already stands.

Attribution gaps now recorded in the volume section instead of guessed: the two
untagged p.220 lines, "Maybe because of what happened yesterday…" (p.222),
"What's going on? Why are you here?" (p.225), the accomplices' "You can't trick us
like that…" (p.229), "H-hey, Ishizaki. It's not too late…" (p.231–232),
"G-good morning…" (p.222), the three untagged delinquent-act lines (p.237),
"I couldn't believe you wanted to install security cameras." (p.234),
"Sorry. For being quiet for so long." and its reply (p.240), and the deliberation
-fee regulations line (p.245).

Forward-only knowledge stays out: Ishizaki's unheard call to "that person" is an
open thread at p.232, and Ryuuen is named only where the volume names him —
Ichinose's warning (p.241) and Ayanokōji's inventory (p.255) — while the corridor
scene itself (p.254) still withholds his name, as printed.

New named entities: Ryuuen Kakeru, first named in this volume (pp.241, 255); the
electronics-store clerk who is Sakura's fan stays nameless, as in the text. New
system facts: a withdrawn case closes with no verdict and still costs the
withdrawing side a point payment for deliberation expenses (p.245); the school
sells surveillance equipment as study tools and the only cameras in that building
sit by the faculty room and the science lab (pp.229, 234); the president can
appoint a secretary on the spot, one first-year Class A applicant having already
been rejected after the first interview (pp.252–253); hearing witnesses are to be
rewarded, the form unstated (p.246). Defects kept as printed: "the today's
Sakura" (p.222), "intension" (p.226), "Ishizaki and the other" (p.229), "brought
produced" (p.232), "cover of miscellaneous expenses" (p.245), "as if he just
shaken off" (p.248), and the two unclosed quotation marks at pp.248 and 253.

Verification after the fixes: `verify2 y1v2` **1066** [says] lines (33 too
short/skipped), `verify3 y1v2` **653** other quoted lines, both ALL PASS. See
progress3 for the site numbers.

### y1v2 is closed: the Postscript is walked (walk, 2026-10-27)

pp.258–261 read whole, and they are not story. The Postscript is the author's
afterword — Syougo Kinugasa writing to the reader four months after the last
book — so it went into `ledgers/volumes/y1v2.md` as one section and into no
character ledger: no page of it carries a character fact, a point total or a
school rule, and the first line of the section says so, because a reader of the
volume page needs to know that the evidence stops at p.257. This follows how
y1v1's Postscript was handled: one section, one `postscript → DONE` stamp, in the
volume file only.

What the afterword does supply is the book's own account of itself, which is worth
anchoring: the volume "focuses on a disturbance centered on Sudou, following the
midterms" (p.258), it was "the first act… a fierce battle waged over class
points", and "the classmates also revealed things about themselves that weren't
visible before". The rest is the illustrator material — the cover with Kushida on
it, the tongue-clicking over new male characters, the 1280 Yen plan that ended at
3980 Yen (p.258) — the editor and reader acknowledgements (p.259), his health,
which the afterword keeps returning to (pp.258, 260), and the two printed
biographies with the eight-kilogram PlayStation 4 wager (p.260). p.261 is the
publisher's newsletter notice and is recorded as a page with no prose of the
book's own.

Defects kept as printed: "a long ways off" and "Doing physical examinations is
impossible, though." (p.258), and the illustrator appearing as "Shunsaku-sama" in
the afterword against "Tomoseshunsaku" in the biography (pp.258, 260). One quote
was corrected during verification: the biography reads "Primarily responsible",
capitalised, and the section had lowered it.

**Volume 2 of Year 1 is now walked end to end** — 7 chapters plus the Postscript,
pp.10–261, every page anchored. Verification: `verify2 y1v2` **1066** [says] lines
(33 too short/skipped), `verify3 y1v2` **659** other quoted lines, both ALL PASS.
Next volume: **y1v3**, starting from `cote_walk next`. See progress3 for the site
numbers.

### The walk tools stopped needing the volume named (walk tooling, 2026-10-28)

Closing y1v2 exposed three places where the tooling remembered the previous
volume instead of reading the ledgers.

`cote.py next`, `cote.py chapters` and `ledger_new` carried `y1v2` as a literal
default, so a fresh session that omitted `--vol` was pointed back at a finished
book. They now resolve the first volume in reading order whose ledger has no
closing stamp (`first_unfinished_volume`, built from `volume_done` over the
`text/COTE Y*.txt` files, side stories last), and `--vol` still overrides it.
Checked: `python3 kb/cote.py next` with no arguments prints y1v3's eight
sections, every one of them `[TODO]`.

"Is this volume done?" was answered by counting chapter stamps (`>= 8`), which is
wrong twice over: y1v2 has seven chapters and is complete, and any volume whose
chapters happen to number eight would read as complete without its Postscript.
The walk already writes the real answer — the `→ DONE` boundary stamp on the
Postscript line of `ledgers/volumes/<vol>.md` — so both `kb/cote.py volume_done`
and `kb/site_data.py volume_walk_complete` now key on that stamp alone. Nothing
else counts.

`ledger_new` used to write `<!-- walk: <vol> → start -->` twice (once above the
`## <vol>` heading and once below it), which made the new file's own marker count
read as two. It now writes one heading with one start marker, using the resolved
first-unfinished volume when `--start-vol` is omitted.

No ledger content changed, so the quote verifiers were not re-run; the site
rebuild and its numbers are in progress3.

---

## HANDOFF — walk state and the exact next steps (updated 2026-10-28, after y1v2 is closed)

Read this whole section before touching a ledger. It is the resume point for a
fresh session or a different model.

**Where the walk is.** `ledgers/volumes/y1v1.md` is DONE (12 chapters +
postscript). `ledgers/volumes/y1v2.md` is **DONE** — Chapters 1–7 and the
Postscript, pp.10–261, every page anchored, ending with
`<!-- walk: y1v2 postscript → DONE -->`. The next unit is a new volume:
**y1v3**, and the way into it is `python3 kb/cote.py next` (or the `cote_walk`
`next` tool), which reports the first unwalked chapter and its page range. Start
a `## y1v3` heading in each ledger you write, with one `<!-- walk: y1v3 → start -->`
marker, exactly as the y1v2 files do. 34 volume pages exist on the site with no
line-by-line evidence (y1v3 → y1v11.75, y2v1 → y2v12.5, y3v1 → y3v3). Source text
lives in `text/COTE Y1 V3.txt` style files with `--- page N ---` markers; the page
numbers in those markers are the numbers every citation uses — in y1v2 the marker
numbers ran 9 above the printed footers, and the markers are what the ledgers
cite.

**Ledger state (from `cote_walk status`).** At the end of y1v2: ayanokouji,
chabashira, horikita-manabu, horikita-suzune, ichinose, kanzaki-ryuuji,
kushida, hirata, ryuuen-kakeru, sakagami, sakura, sudou, tachibana,
systems/point-economy, volumes/y1v2. One chapter behind, because Chapter 7 does
not feature them — checked, not forgotten: hoshinomiya (ch6), karuizawa (ch4),
kouenji (ch4), ike (ch6), yamauchi (ch6), exams/midterm-exam (ch4). Places
ledgers stop where y1v1 stopped.

**Tools.** MCP server `cote_walk` (code: `kb/cote_mcp.py` over `kb/cote.py`)
exposes: `status`, `next`, `chapters`, `read_pages`, `append`, `ledger_new`,
`verify`, `build`, `gate`, `hash`, `ship`. Skill:
`.qoder/skills/cote-walk/SKILL.md` with `references/ledger-grammar.md`. CLI
fallback with the same subcommands: `python3 kb/cote.py <cmd>`. Two gotchas: a
running MCP server keeps the code it imported at start, so after editing
`kb/cote.py` reload the server or use the CLI; and `build_share_site.py --docs`
is a mirror-only step, never a substitute for the full rebuild. `next`,
`chapters` and `ledger_new` take no volume argument by default and resolve the
first unfinished volume from the `→ DONE` stamps — for the session resuming now
that is **y1v3**; pass `--vol` only to work on another book.

**The chapter loop, in order.** (1) `chapters` / `next` to fix the page range.
(2) Read the **entire chapter in one pass** (`read_pages`, or read the
`--- page N ---` span of the text file directly) before writing anything.
(3) Fan out to **every** ledger the chapter touches — people, volume, systems,
exams — in subsection-sized `append` calls; one `append` per scene block, not
one giant write (large single writes get blocked by the client classifier).
(4) Write the chapter's section in `ledgers/volumes/<vol>.md` (setting, numbered
beats, structural note, page-map note, new named entities, new system facts,
threads left open, attribution gaps, defects kept as printed).
(5) `verify2.py <vol>` and `verify3.py <vol>` must both print ALL PASS; fix the
ledger, never the checker. (6) Full rebuild, then `--docs`, then
`share_check --site --print --pdf`, then hash two consecutive builds and require
the same value. (7) Grep the built HTML under `docs/` to confirm the new rows
actually render where they are supposed to. (8) Update **both** progress files,
then ship.

**Writing rules that are not negotiable.** Quotes are verbatim from the page,
curly punctuation and all, including translation defects ("This are inadequate
evidence"). `[says]` only where the translation names the speaker or fixes it by
an act; everything else is `[note]` with the gap stated. No other character's
line goes into a person's `[says]` row. No forward-only knowledge: later-volume
facts stay out, and chapter-external consequences become open threads at their
real page. Gaps stay gaps — an undecidable speaker is recorded as undecidable.
Exactly one `<!-- walk: <vol> chN → p.X -->` marker per chapter per file;
`append --stamp` de-duplicates. Prose on the page is reader-facing: no pipeline
vocabulary ("the walk", "the ledger records", "the fan-out"), because
`share_check` fails the build on it.

**Work that arrives from another session gets audited before it ships.** Chapter 7
was written in a companion session and closed here; the verifiers passed and still
missed four attribution errors, because they check that a quote exists in the
volume, not who said it. Re-read the chapter's own pages, line by line against
each `[says]`, before a build. That pass is what turned "That's…" (p.238) from
Sakura's line back into the narrator's stalled answer and moved two untagged p.220
lines into the gap list.

**Ship mechanics.** Commits use the GitHub noreply identity through environment
overrides only — `GIT_AUTHOR_NAME=FakeAn GIT_AUTHOR_EMAIL=FakeAn@users.noreply.github.com
GIT_COMMITTER_NAME=FakeAn GIT_COMMITTER_EMAIL=FakeAn@users.noreply.github.com`
— and `git config` is never modified. Ship paths: `.qoder docs kb ledgers
progress2.md progress3.md system-prompt.md`. Never stage `session-*.md`;
`share/` is generated and stays out of git. Push to `origin main`; the remote
answers with a redirect to `FakeUser2121/cotedb` and that is expected. Cloudflare
deploys from the push; there is deliberately no github.io site and no live URL
to quote. Standing user instructions: no subagents, do not open his screenshots,
use the progress files every chapter, installs go to `/mnt/D`.

**2026-10-29 — sqlite layer removed.** Per the merge contract (site built from
`content/*.tsv` + `ledgers/`, no database in the walk chain): `cote_kb.db` and
`search.db` deleted from disk (both were gitignored, never in git); the local
`site-v2` branch deleted (identical to `origin/main`); `kb/corpus_check.py`
(P0-era PDF↔txt checker, its only DB consumer) removed; `kb/walk_locate.py`
`alias_patterns` rewired from the DB `aliases` table to
`content/characters.tsv` (`name`/`sort`/`aliases`, folded). Note: the old DB
held 357 folded forms the TSV does not carry (MTL typo variants like
`ayakoji`, `chabasira`, plus a few surname-only forms) — `locate` now searches
published roster forms only; ledgers remain the truth layer. Verified:
`locate` runs on y1v2/y1v3, `next` → y1v3 ch1 p.10-12, `make check` OK.

**2026-10-29 — y1v3 Chapter 1 walked (pp.10–12, "Chabashira Sae's Soliloquy").**
Volume ledger created (`ledgers/volumes/y1v3.md`, start stamp). Chapter is a pure
first-person cold open: the Wings of Icarus retelling (p.10), the comparison to
"a certain young boy," and the confession that she turned his quiet rage onto
herself because she had been "pushed into a corner" (p.11). p.12 carries no
prose. Chabashira's ledger got the full sweep (`## y1v3` block, 10 rows); no
other roster character is present — the boy is never named on these pages, so
no stamp or row was written for anyone else and the attribution gap is listed
in the volume section (AGENTS.md §7: never assign from context alone). New
entities: none (only the myth figures inside her retelling). Verifiers pass;
the wording gate caught one row that said "in the ledgers" — rewritten to
"he stays unnamed in the records" before the commit. No defects kept as
printed. Next: y1v3 ch2 pp.13–99 (87 pp → two sub-reads).

**2026-10-29 — Ichinose's student-council rows removed (owner correction).**
p.141 shows only the light-pink-haired girl delivering a message ("The student
council wishes to discuss something with you"); the ledger had promoted that
into `[role:student-council]`, `[status]` and `[trait]` rows asserting
membership "under President Horikita Manabu" — none of it on the page. Per the
owner: removed the three rows, reworded the scene heading and the two
supporting rows (Hoshinomiya's ledger row lost "on student council business"),
left the verbatim quote intact, and added a `[note]` recording that the pages
never state a role. Her role gets re-walked when later volumes record it.

**2026-10-31 — y1v3 Chapter 2 walked (pp.13–99, "The Boundary Between Heaven and Hell").**
Full chapter read in two sub-reads (13–55, 56–99); pp.21, 37, 79 and 99 carry
no prose. The island special test is announced (Mashima, p.24), the class
splits three ways over the 300-point budget, Horikita takes the leadership
card, and Kouenji retires on day one costing the class thirty points. Eight
sections appended to the volume file with stamp `y1v3 ch2 → p.99`. Present
roster characters stamped with full sweeps: Ayanokōji, Horikita, Hirata, Ike,
Sudō, Yamauchi, Kushida, Sakura, Kōenji, Chabashira, Mashima, Hoshinomiya,
Karuizawa, Shinohara, Yukimura, Katsuragi, Totsuka, Ibuki, Satō. New ledgers
created for Mashima, Katsuragi, Totsuka, Ibuki, Shinohara, Yukimura and Satō
(`ledger-new … --start-vol y1v3`). Sakayanagi and Miyake are passing mentions
only (reported speech / a phone call) and are listed in the volume section
without stamps. New named entities: Mashima Tomonari, Katsuragi Kōhei, Totsuka
Yahiko, Ibuki Mio, Shinohara Satsuki, Yukimura Teruhiko, Satō Maya; unnamed:
the sick Class A student, Ibuki's assailant, the Class A deck bullies.
Eight non-says quote failures were fixed before commit (wrong pages, quotes
spanning page footers split with `…`, and two paraphrases corrected to
corpus text). The wording gate fired on "both ledgers"/"Ike's ledger" in the
attribution-gaps row — rewritten to "classmates' pages"/"under Ike".
Doubled `## y1v3` heading in Mashima's new file removed. Verifiers pass;
no defects kept as printed. Next: y1v3 ch3 pp.100–130.

**2026-11-01 — y1v3 Chapter 3 walked (pp.100–130, "Rivals on the Move").**
Full chapter read in two sub-reads (100–115, 116–130); pp.110, 119 and 130
carry no prose. Morning roll call and exploration; Kanzaki hands over the
Class B campsite (p.103); Komiya and Kondou's chip provocation (pp.105–106);
the Class C beach burned to zero with Ryūen's first-name call (pp.108–116);
Class B's seventy-point camp, the renewed cooperation and the Class A cave
directions (pp.117–125); the Class A cave turned back by Katsuragi's
unspoken one-spot rule (pp.126–130). Fourteen people ledgers plus the volume
file carry the stamp `y1v3 ch3 → p.130`: Ayanokōji, Horikita, Hirata, Ibuki,
Ike, Ryūen, Ishizaki, Komiya, Kondō, Ichinose, Kanzaki, Katsuragi, Totsuka
and Kaneda. One new ledger: kaneda-satoru (Class 1-C, sheltered by Class B,
p.124). Nakanishi and Chihiro-chan are named only (p.124) and are listed in
the volume section; Kōenji, Karuizawa, Sudō and Kushida are passing mentions;
Sakazaki (p.111) is a named Class C extra with no roster row and is recorded
as a new named entity only. Attribution gaps recorded in the volume section:
the p.105 provocation retort and the two Ryūen explanations, the p.112
perseverance rebuke, the pp.121–122 visitor questions, the p.123–124 Class C
report (either Class D speaker is possible), the p.125 walk-away verdicts and
the p.126 approach line. The two multi-page quotes (well water, vinyl sheets)
were split with `…` before the first verify run, so no verifier failed;
136 [says] lines (three micro-quotes under ten characters are skipped by
design) and 166 non-says spans all corpus-exact. No defects kept as printed.
Next: y1v3 ch4 pp.131–143.

**2026-11-01 — y1v3 Chapter 4 walked (pp.131–143, "The Meaning of Freedom").**
Third day: Ayanokōji walks out to Kōenji's vantage point with Sakura —
the stalker's resignation and her idol photography years (p.133), the
friendship beat against one tree (pp.134–135), the caterpillar removed
without her knowing (pp.137–138), about fifty ears of cultivated corn
whose soil and weed cover prove the school uses the island (p.139), the
shirt-bag harvest (pp.139–140), Katsuragi and Yahiko's partnership offer
refused with a fabricated class order while Katsuragi stays to watch the
spot (pp.140–142), and the camp close — full bag by one o'clock, Yamauchi's
jealousy over the shirtless pairing, Hirata getting the report first
(pp.141–142). Seven people ledgers plus the volume file carry the stamp
`y1v3 ch4 → p.143`: Ayanokōji, Sakura, Katsuragi, Totsuka, Ike, Yamauchi
and Hirata. No new ledgers, no new roster rows, no new named entities —
the electronics-store stalker stays unnamed. Named but absent, listed in
the volume section: Kōenji, Kushida, Horikita, Ichinose and Ibuki.
Attribution gaps: the p.139 bags line, the p.139 corn question and answer,
and the two camp-close lines (p.142). The locator did not surface Totsuka
on these pages — the text calls him Yahiko only and his row's published
name forms do not match that alone; matched by eye and kept as a coverage
note for the volume-end gate. Locator substring hits checked against the
text and discarded: aga/against, iki/like, chie/handkerchief, Mori/memories,
Yano/Ayanokōji, Ichino/Ichinose, Horikita as Suzune on p.133. Verification
passed on the first run: 205 [says] lines (three micro-quotes under ten
characters skipped by design) and 169 non-says spans, all corpus-exact; the
one cross-page quote (shirt bag, pp.139–140) was split with `…` before
verify. No defects kept as printed beyond the flagged "didn’t had the time"
(p.131). Next: y1v3 ch5 pp.144–158.

**2026-11-01 — y1v3 Chapter 5 walked (pp.144–158, "The Quiet Outbreak of War").**
Fourth day: morale turns on the river — fish, fruit and the ~100-point
spend with Kōenji's retirement in it, Yukimura satisfied (p.144); the 80:20
offensive reading taken as the order to attack (p.144); on the Class A
side the hut spot below the cliff — fishing gear, four hours shown, tools
dusty — marked on the map (p.145), and the tower left empty because
holding it invites observation (p.146); two Class A boys ambush and search
him, keep the map, and offer 100,000/200,000 points under a memorandum for
the leader's identity while correcting him that Sakayanagi — not Katsuragi
— is Class A's representative (pp.146–148); with Ichinose and Kanzaki at
the emptied Class C camp he reads the retired class and pumps the pair on
the Class A split under Horikita's cover (pp.149–151); then the flashback —
Sudou's failed summer invitation, and Chabashira's faculty-room story: her
own student past, the unnamed man who demanded Ayanokōji's expulsion, the
Class A bargain, the collar grab, the answer never spoken (pp.152–157).
p.158 carries no prose (blank/short scan page). Six people ledgers plus
the volume file carry the stamp `y1v3 ch5 → p.158`: Ayanokōji, Chabashira,
Sudō, Horikita, Ichinose and Kanzaki — Sudō, Horikita, Ichinose and Kanzaki
each get their first y1v3 block here; Chabashira's carries the full student-
past and expel-deal section. No new ledgers (Kanzaki already had one), no
new roster rows, no new named entities — Sakagami, Hoshinomiya, Yukimura
and Sakayanagi are references only; the two Class A ambush boys and the
man who demanded the expulsion stay unnamed. Named but absent, listed in
the volume section: Katsuragi, Hirata, Kushida, Kōenji, Ryūen, Hoshinomiya
and Sakagami (named but not on-page). Attribution gaps: the p.149 pair
arrival lines, the pp.149–150 points/strategy block (seven quoted lines),
the p.150 Class A answer ("It's said they really don't get along…"), the
p.150 "Complete opposites?", the p.151 secrecy reply ("Ha ha, don't worry…"),
and "Hey, Sudou!" (p.152) plus the closing "Bye." (p.153); the flashback
classroom banter turns are recorded by turn on both pages instead. Locator
substring hits checked against the text and discarded: aga/against,
ike/like, iki/like, yano/Ayanokōji, ichino/Ichinose, Etou/detour,
kaga/Sakagami, Kimura/Yukimura, Miya/Hoshinomiya, Oda/today,
Yanagi/Sakayanagi, Yuki/Yukimura, andou-sayo/hoshinomiya-p156 NOT FOUND.
Totsuka/Yahiko and all roster volume cells already covered — no
content/*.tsv change. Verification failed on the first run only: the
cross-page Chabashira verdict (pp.154–155) ran through the printed page
footer, split with `…` at the footer (ch4 pattern) and re-verified —
283 [says] lines (five micro-quotes skipped by design) and 175 non-says
spans, all corpus-exact. No defects kept as printed this chapter. Next:
y1v3 ch6 pp.159–239 ("False Teamwork", 81 pages — read in two halves).

y1v3 ch6: False Teamwork (pp.159–239)

Read and shipped in two halves (pp.159–199, then pp.200–239), one stamp
`y1v3 ch6 → p.239` on thirteen people ledgers plus the volume file:
Ayanokōji, Horikita, Ibuki, Hirata, Ike, Sudō, Yamauchi, Karuizawa,
Kushida, Sakura, Shinohara, Ryūen, Katsuragi. First half: the planted
underwear in Ike's bag and Hirata's conceal-the-truth pact (pp.159–170),
the meeting that splits the camp with Ibuki as the new suspect
(pp.171–178), tent stakes, Horikita's partnership and her fever near
38°C (pp.180–188), the sixth-day forage, the card colour doubt and the
mud bribe (pp.191–199). Second half: the river wash and the key-card
confession (pp.200–205), the burned manual and Hirata's crack
(pp.206–212), Horikita's chase and knockout from her own viewpoint
(pp.213–220), Ibuki's handover and the Class A–C alliance from hers
(pp.221–224), the night carry and the 7:58 retirement (pp.226–239).
Ryūen and Katsuragi are on scene only in the handover (§6.9);
Shinohara is absent after p.178 and gets an absence section
carrying her p.182 passing mention. No new ledgers, no roster rows, no
new tags. Named but absent, listed in the volume section: Kōenji
(p.186), Yukimura (p.174), Chabashira (p.198), Sakayanagi (p.223 —
still no ledger file, opened at the volume-end coverage gate);
"Mii-chan" (p.192) stays unidentified with a note; Ibuki's unnamed man
(p.220) and the ship teacher (p.237) stay unnamed. Defects kept as
printed: four — "Karuizawasan" (p.161), "turns out to the be the
culprit" (p.169), the broken three-quarter mark (p.181), "hadn't had
recommended" (p.184) — each flagged at the page and listed in the
volume section. Attribution gaps left out: the p.172 taunt and retort,
the p.178 Ibuki pair, the p.201 swim invite, "Does this mean she didn't
do it?" (p.206), the p.207 three-line confrontation, and the p.208
block; every other untagged line is placed with a note (pp.161, 165,
171, 173, 197, 206, 207, 208, 222, 223, 224, 235) and the forest
dialogue of pp.230–235 is recorded by turn. Both halves passed verify on
the first run — 928 [says] lines (11 micro-quotes skipped by design)
and 203 non-says spans, all corpus-exact. Locator coverage not run for
this chapter; it stays with the volume-end gate. Next: y1v3 ch7
pp.240–258 ("The Curtain Rises", 19 pages), then the ch8 postscript
pp.259–262.

y1v3 ch7: The Curtain Rises (pp.240–258)

Read and recorded in two halves (pp.240–249, then §7.1 pp.250–258), one
stamp `y1v3 ch7 → p.258` on fifteen people ledgers plus the volume file:
Ayanokōji, Horikita, Hirata, Sudō, Ike, Yamauchi, Karuizawa, Ryūen,
Kōenji, Chabashira, Katsuragi, Totsuka/Yahiko, Kaneda, Mashima, Ibuki.
First half: the results announcement and Ryūen's leader-name reveal on
the beach (pp.240–245), the deck — Kōenji's drink, Horikita's
first-name withdrawal, Karuizawa's apology (pp.245–247), Chabashira's
Icarus talk and the father reveal (pp.248–249). Second half: §7.1, the
whole explanation on the silence condition — the circling-ship hints,
Yahiko as Class A's leader, the card with his own name, the
leader-change clause, Ibuki's camera and eye-contact tell, Kaneda the
spy, and the closing handshake deal (pp.250–258). Mashima and Kaneda get
ledger entries only — no pages; Totsuka/Yahiko's page extends. No new
ledgers, no roster rows, no new tags. Defects kept as printed: five —
"Horikitasan" (p.241), "That's¾" (p.242), "The lowest class is¾Class
C" (p.244), "But I retired¾" and "what did you¾" (p.247) — each flagged
at the page and listed in the volume section. Two sentences break across
pages and are left unquoted: the poor-health question (pp.253–254) and
the camera-or-theft answer (pp.255–256). Attribution gaps left out: the
p.240 close-question, the p.241 pair, the p.242 four-line block, the
p.244 zero-points line, the p.245 Class A cry, the p.246 ranked-first
question, and the p.247 praise block; every other untagged line is
placed with a note (pp.240, 241, 242, 244, 246, 247). Verify: two
failures on the first run, both cross-page rows, fixed by unquoting them
— 1264 [says] lines (23 micro-quotes skipped by design) and 233 non-says
spans, all corpus-exact. The handshake narration briefly pushed R19 to
90; wrapping the corpus line in quote marks restored the ratchet to
82/82. Locator coverage not run for this chapter; it stays with the
volume-end gate. Next: y1v3 ch8 postscript pp.259–262, then the
volume-end coverage gate and the closing stamp.

y1v3 ch8: Postscript (pp.259–262)

Read and recorded in one section, no people stamps — the postscript
names no roster character in-world. One stamp `y1v3 postscript → DONE`
on the volume file, doubling as the volume closing stamp (the y1v2
pattern). Content: Kinugasa's afterword — health-consciousness and
sake, the volume's stated theme (each class's goals and policies through
the special test), the Volume 2 sashimi bet paid ("Maguuroo!"), the
manga announcement (Ichino Yuyu-sama, serialization in January), the
early-manuscript shame bit — plus the author/illustrator bios (p.261)
and the publisher's newsletter notice (p.262). New named entities
listed in the section: Syougo Kinugasa, Tomoseshunsaku, Ichino Yuyu,
Shunaku-shi. Defects kept as printed: three — "healthconscious"
without its hyphen (p.259), "a through medical check-up" (p.261),
"Shunaku-shi" (p.259). One first-run verify failure: the bios quote had
"gathered" the y1v2 wording — the corpus prints "Primarily responsible
for scenario and PC game planning" without "the" (p.261) — fixed to the
printed words; 1264 [says] and 241 non-says spans then all pass.

y1v3 volume-end coverage gate

Full-roster locator sweep (253 ids, `walk_locate.py locate --vol y1v3`):
46 produced hits; 15 of those are substring collisions, checked against
the text and discarded with the page evidence — aga/against,
iki/like, yano/Ayanokōji, mori/memories, yanagi/Sakayanagi,
kimura and yuki/Yukimura, miya/Hoshinomiya and Komiya, kaga/Sakagami,
eto/etou in "detour", ando/…, oda/…, nishi/Nakanishi, hosen/housen
(no printed form in the volume at all), and horikita-manabu sharing
Suzune's surname pages. Every remaining real hit page is cited by a
y1v3 ledger row — 231 distinct pages carry citations; the only content
page with none is p.143, which carries no prose. The president's one
real reference is p.107's "student council president's younger
sister", recorded on both Ayanokōji's and Horikita's ledgers.
Totsuka/Yahiko: the locator still returns zero (the volume prints
"Yahiko" only and his row's published forms do not match that alone —
the ch4 note), so the by-eye sweep stands: pp.60, 127–129, 140–141 and
251 were already in his ledger, and p.252's two retelling lines got a
new section (stamp `y1v3 ch7 → p.258`, de-duplicated by append).
Sakayanagi: all four real pages (p.60, p.148, pp.150–151, p.223) are
recorded — the volume section's bullets plus mirrored rows on
Ayanokōji, Ibuki, Ichinose and Kanzaki — but she still has no ledger
file; the ch6 deferral closes with the finding that coverage is
complete and the file should open at her first scene-presence volume,
the Miyake precedent (owner can override at the report). Named-only
pages confirmed recorded without ledgers: Sakagami (p.155), Nakanishi
(p.124), Miyake (p.16), Tomose (p.261), Ichino (p.259), Chihiro-chan
(p.124). Every named id's `volumes` cell already carries y1v3 — no
content/*.tsv change. Open question for the owner (§11): whether
"Yahiko" should join totsuka-yahiko's aliases so the locator can
surface him (the volume never prints "Totsuka"). Verifiers, gate and
make check all pass; hash 5ad45779effcb8153e1f603096d13b84 twice.

y1v3 follow-up: Sakayanagi ledger opened (owner decision)

Per the owner at the volume report — "keep it in the KB" — the ch6
deferral was overridden: `ledgers/people/sakayanagi-arisu.md` created
(`ledger-new people sakayanagi-arisu --start-vol y1v3`, header
`class: Class 1-A (enrolled April 2015) · status: minor (Class A)`).
Four mention sections carry her four real locator pages, in page order,
one stamp per chapter touched: p.60 with `ch2 → p.99` (the scouts' talk,
mirroring Totsuka's existing `[rel:sakayanagi-arisu]` row), p.148 and
pp.150–151 with `ch5 → p.158` (the ambush correction, the beach absentee
read with Ichinose's and Kanzaki's lines verbatim), p.223 with
`ch6 → p.239` (the handover argument, Ryūen's and Katsuragi's lines
verbatim). No content/*.tsv change, no new tags. Verify: 1268 [says]
(23 skipped) and 244 non-says spans, all corpus-exact; gate exit 0;
make check OK (R19 82/82); hash `cad4562da7d06fb9aea02e2ed02ef868`
twice. Her four scenes put her over the page threshold, so her existing
roster page now carries the cards. The alias question stays open with
the owner: whether "Yahiko" joins totsuka-yahiko's aliases.

y1v3 follow-up: "Yahiko" added to Totsuka's aliases (owner decision)

Owner confirmed at the report that Yahiko is plainly Totsuka Yahiko's
alias; `content/characters.tsv` row `totsuka-yahiko` now carries
`yahiko` in its aliases cell (the only content change; row id, name and
volumes untouched). The locator immediately surfaces the eight pages the
by-eye sweep had found — p.60, pp.127–129, pp.140–141, pp.251–252 —
every one already cited in his ledger, so the coverage gate closes on
machine confirmation. Verify 1268 [says] / 244 non-says ALL PASS; gate
exit 0; make check OK (R19 82/82); hash `7f6fd436a889ba9afdab57a9bc545155`
twice. Both owner decisions from the volume report are now applied.

y1v4 ch1: Karuizawa Kei's Soliloquy (pp.10–11)

Walk position moves to Year 1 Volume 4. Volume file opened —
`ledgers/volumes/y1v4.md`, header pages: 248 · chapters: 5 + postscript —
and chapter read in one pass (p.10 prose, p.11 blank/short scan), one
stamp `y1v4 ch1 → p.11` on one people ledger plus the volume file:
Karuizawa. Her first y1v4 section is the cold-open soliloquy — the
mirror, the unnamed old wound, the parasite self-assessment; no other
roster character is present and the page names no one. No roster rows,
no new tags, no alias changes (the page reveals no name forms). Defect
kept as printed: the doubled verb "Why did I have to have to go through"
(p.10). One first-run verify failure — the class-line quote had "boys
and girls" where the corpus prints "boys or girls" — fixed to the
printed words; 13 non-says spans then ALL PASS (0 [says]: the chapter
has no dialogue). gate exit 0; make check OK (R19 82/82); hash
`ee21f656d3ea278b734a18cd864dbf63` twice. Session notes kept here for
memory: the roster-wide alias-audit plan is dropped — the owner's rule is
that code never fills data, only helps reading, so aliases are logged by
hand while reading each chapter from now on; Totsuka's `yahiko` alias had
already shipped (a579e57). Two commits remain local: the GitHub token
died mid-session, push stays blocked until the owner refreshes it. Next:
y1v4 ch2 pp.12–62.

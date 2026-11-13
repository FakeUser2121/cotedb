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

y1v4 ch2: the Summer Group Test (pp.12-62)

Chapter read in two halves (pp.12-36, then pp.37-62 with --blank:
p.59 and p.62 carry no prose). 42 sections appended across 21 people
ledgers plus one volume section, one stamp `y1v4 ch2 -> p.62` per file
(first-half appends un-stamped, final append stamped). New file:
ledgers/people/sotomura-hideo.md (ledger-new, --start-vol y1v4); `## y1v4`
start blocks added to 18 existing ledgers. Alias logged by hand while
reading: sotomura-hideo's aliases cell now `The Professor;Professor` —
the nickname is printed at p.32 and the bare form carries the vocatives;
walk_locate immediately returns his ch2 pages (p.32-37, 39, 41, 46,
50-51) plus later-chapter hits. Mention-only, no files (Sakagami
precedent): ichihashi-ruri and maezono on Sakura's rel rows; the roster-
only names Takemoto, Machida, Morishige, Hamaguchi, Beppu, Manabe, Yabu,
Yamashita, Morimiya and Tokitou in the volume bullet (Tokitou at p.54 is
printed without a first name — which Tokitou is not printed, both roster
rows keep y1v4). New tags: none; roster rows: none (every name already
on the roster with y1v4). Attribution gaps recorded in the volume section:
five untagged lines (p.42 x3, p.43, p.60) plus the two unassigned
Horikita-chat lines of §2.2 (pp.30-31). Verify: 167 [says] (1 skipped
micro-quote "Hmph.") and 69 non-says, ALL PASS. Three first-run verify
failures were cross-page quotes — durable note for this volume: y1v4's
footers print `Page N` (space form), which verify2/3 do not strip (they
strip `Page|N` and Goldenagato), so a page-break join fails; fixed by
trimming to one page (Karuizawa) or splitting with `…` and a `p.N-M`
citation (Mashima, Yukimura). First-run R18 5 / R19 85: the word
"ledger" in three rows and a prose "you" in Ayanokōji's p.13 action row
(it renders on his page and the volume index) — all rewritten, gate back
to R18 0 / R19 82. build 173 pages, 44 assets (yukimura-teruhiko crosses
the scenes threshold and gains a page); gate exit 0; make check OK
(R19 82/82); hash `49c55c22ec9ec301ffac9d1b2d5c5e29` twice. No new
defects printed. Open for the volume-end coverage gate: the p.39 roster
row is cited by Ayanokouji, Ichinose and Ibuki but not yet by Karuizawa,
Yukimura or Sotomura — passing-mention rows if the sweep flags them.
Push still blocked (token dead); four commits will be local after ship.
Next: y1v4 ch3 pp.63-124.

y1v4 ch3: An Infinite Variety of Wishes (pp.63-124)

Chapter read in two halves (pp.63-93, then pp.94-124 with --blank:
p.99, p.119, p.120, p.124 carry no prose). 21 people ledgers + one
volume section stamped `y1v4 ch3 → p.124` (first-half bodies un-stamped;
the two first-half-only files, sakayanagi-arisu and kanzaki-ryuuji, got
the stamp appended after their sections). Three new files via ledger-new
--start-vol y1v4: machida-kouji (Class 1-A), hamaguchi-tetsuya (Class
1-B), manabe-shiho (Class 1-C). ## y1v4 headings added by hand to
hoshinomiya-chie, sakagami, sakayanagi-arisu, kanzaki-ryuuji. Roster
edit: new row yashima-mariko (Cow roster, p.100) — the only entity row
this chapter. First-half verify: 9 cross-page quote failures fixed with
p.N-M + … fragment splits (fragments each wholly on one page); one exact
substring fix (aka "assume that no one here is the VIP"); one plural fix
(ibuki/kei "as if isolating themselves"). Second half: 5 more fixes —
machida/sakura cross-page, katsuragi/ryuuen non-say cross-page, sotomura
"a hour"→"an hour". Volume-file first-run failure: “not chosen,” was a
paraphrase in quote marks (p.63-66 join) — reworded without quotes.
Final: 479 [says] + 161 non-says ALL PASS. Attribution care: Karuizawa’s
p.80 "Ugh…" kept [note] unassigned; teachers’ p.121-122 exchange kept
as [note] gaps in the volume section. Rule-6 questions left open for the
owner (do not decide): (1) corpus p.64 "Andou Saya" vs TSV "Andō Sayo";
(2) Horse VIP "Minami-kun" p.113 ambiguous — minami-hakuo vs
minami-setsuya both in TSV with y1v4, neither assigned; (3) bare alias
"Rika" for morofuji-rika on p.93 withheld (locator substring risk —
patterns only morofuji / morofuji rika). First-run R18 6 / R19 84: the
word "dossier" in three Ayanokōji/Karuizawa rows and a prose "your" in
Ayanokōji’s VIP trait row — all rewritten ("write-up", "the class");
gate back to R18 0 / R19 82. build 177 pages, 48 assets; gate exit 0;
make check OK (R19 82/82); hash `72491977fbf49c39926376ce9cf0cda4`
twice. New tags: none. Open for the volume-end coverage gate: the p.39
roster row still needs passing-mention rows for karuizawa/yukimura/
sotomura if the sweep flags them; andou p.64 hit needs an entry or
passing mention; morofuji p.174. Push still blocked (token dead); five
commits will be local after ship. Next: y1v4 ch4 pp.125-204.

y1v4 ch4: Double Question (pp.125-204)

Chapter read in three passes (pp.125-151, 152-178 --blank p.162,
179-204 --blank p.197,p.204). 30 people ledgers + one volume section
stamped `y1v4 ch4 → p.204` (intermediate bodies un-stamped; stamps
inserted after the last Ch.4 section in each file). Six new files via
ledger-new --start-vol y1v4: morishige-takurou, takemoto-shigeru,
yamashita-saki, yabu-nanami, morofuji-rika, sugimura (Sugimura already
in the TSV with y1v4 — first scene-presence this chapter). First-run
verify: 13 failures — six cross-page quote splits (chabashira so-late
substring was also wrong: corpus prints “so late”; hamaguchi, hirata ×2,
yukimura stairwell), four exact-substring fixes (aka “honest as much as
possible”, hirata “didn’t she?”, karuizawa/shinohara “I didn’t have any
choice!”, sotomura/yukimura full “I can’t say that I noticed anything of
the sort”), one paraphrase-in-quotes note rewrite (hamaguchi). Final:
844 [says] + 239 non-says ALL PASS. Attribution: the anonymous Manabe
chat is Ayanokōji’s outgoing text by construction (sub-account);
friend’s “Whoa, Shiho…” (p.192) left unassigned; Yabu has no separately
tagged stairwell line. Mention mirrors added for ike-kanji, yamauchi-
haruki, sudou-ken, sakayanagi-arisu, kushida-kikyou (named-only rows).
No roster TSV edits this chapter (Yashima was ch3). New tags: none.
First-run R18/R19 both clean — gate R18 0 / R19 82, no wording churn.
build 177 pages, 48 assets; gate exit 0; make check OK (R19 82/82);
hash `6682b58f7d27f9fb0b6c434dee5845fb` twice. Open for volume-end
coverage gate: p.39 roster row still pending karuizawa/yukimura/
sotomura passing mentions; andou p.64; morofuji p.174 (now has a file
and p.160-174 rows — locator should surface). Push still blocked
(token dead); six commits will be local after ship. Next: y1v4 ch5
pp.205-243.

y1v4 ch5: Each and Every Difference (pp.205-243)

Chapter read in two halves (pp.205-224 --blank p.211,p.221;
225-243 --blank p.229). 22 people ledgers + one volume section
stamped `y1v4 ch5 → p.243` (first-half bodies un-stamped; second-half
appends then stamped — one stamp per chapter per file, inserted under
`## y1v4`). One new file: beppu-ryouta (ledger-new --start-vol y1v4;
roster row already had y1v4). First-half verify: 5 failures — three
cross-page … splits (aka “But this school…”, yukimura “Do you really
think that…”, ichinose downer line p.205-206), one paraphrase-in-quotes
(horikita “doesn’t particularly want” → exact “I don’t particularly
want that”), one exact-substring (machida Hamaguchi “please be quiet
and just watch”). Second-half verify: 1 failure — hirata rel row
“not preternatural talent” dequoted to prose. Final: 1074 [says] +
314 non-says ALL PASS. Attribution: “Minami-kun” Horse VIP (p.236)
left unwritten to any ledger — two Minami roster rows, rule-6 open;
volume row records the ambiguity. Morishige traitor (p.233) kept as
Ichinose’s “probably” prediction. No roster TSV edits. New tags: none.
gate R18 0 / R19 82; make check OK (R19 82/82); build 177 pages,
48 assets; hash `03811810f8fa172c42a189cf2c5f6c55` twice. Open for
volume-end coverage gate: p.39 roster row (karuizawa/yukimura/
sotomura passing mentions); andou p.64; morofuji locator; Minami
identity question. Push still blocked (token dead). Next: y1v4 ch6
postscript pp.244-248, then the volume coverage gate.

y1v4 ch6: Postscript (pp.244-248)

Postscript read in one pass (p.244 author note; pp.245-246 short;
p.247 author/illustrator bios; p.248 newsletter). No roster characters
present — volume section only, stamped `y1v4 ch6 → p.248`. Quotes: two
new non-says spans (Kinugasa’s redacted-manuscript joke and the Volume
5 tease), 1074 [says] + 316 non-says ALL PASS. No people-ledger
stamps, no TSV edits, new tags: none. gate R18 0 / R19 82; make check
OK; build 177 pages, 48 assets; hash `29604b69da3781b89e6104819458ef95`
twice. Next: volume-end coverage gate (roster locator, p.39/andou/
morofuji hits), closing DONE stamp, then ship.

y1v4 volume-end coverage gate

Full-roster locator sweep (walk_locate.py locate --vol y1v4, all 255
ids) classified against every ledger citation by a read-only comparison
script (/tmp/opencode/finalgap3.py — prints only, never writes a
ledger): 280 real gap pages vs substring/honourific false positives.
FP discards with page evidence: aga/against (239 hits), iki/like (82),
ike “like” (174), yano/Ayanokōji (69), yanagi/Sakayanagi (4),
kimura and yuki/Yukimura (68 each), miya/Hoshinomiya and Komiya (9),
kaga/Sakagami (1), etou in “detour” (1), fuji (1), housen (10 — no
printed form in the volume at all), ichino/ichinose (77), mori-nene
(11), satou (1), toba (1), kitou (2), nishi/Nakanishi (1), oda (16),
sonoda-chiyo (1), ninomiya-kuranosuke (1), minami-setsuya (2),
horikita-manabu sharing Suzune’s surname pages (81), hoshinomiya
achien* substring (9), tokitou (2), andou substring hits (7),
karuizawa p.2 (the table of contents), and the STOP-word filter on
sotomura/the single-token noise. Every remaining real gap page
carrying a roster ledger got hand-written rows this session — 30
people ledgers, 605 added lines, paraphrase rows in page order placed
at each chapter’s boundary stamp (no quotation marks, so no new quote
surface for verify). Three characters crossed the scenes threshold and
gained pages: morishige-takurou, morofuji-rika, takemoto-shigeru
(build 177 → 180 pages, 48 → 51 assets).

Mid-gate R19 regression caught by make check: baseline 82 → 142 from
second-person paraphrases in the new rows (reported speech written
unquoted). Fixed by rewriting all twenty offending rows to third
person across ayanokouji-kiyotaka (7), horikita-suzune (8),
karuizawa-kei (3), hirata-yousuke (1), yukimura-teruhiko (1); R19
back to 82/82 with no wording churn. The repair pass also corrected
four attribution/scene errors the evidence pages showed: p.13’s counter
is Hirata’s, not Kushida’s; p.171 and p.178 are Ayanokōji’s cover
lines, not Hirata’s; p.166 is the middle-of-the-night Chabashira call
at the pool deck, not the Ichinose meeting; p.65’s café question is
Horikita’s, p.188’s realisation is Manabe’s, p.198’s stammer is
Karuizawa’s.

Named-only entities (no ledger file; recorded in the chapter sections
or here): 24 ids — the ch3 p.64 roster dump (andou-sayo,
matoba-shinji, nishikawa-ryouko, oda-takumi, sonoda-masashi,
suzuki-hidetoshi, tsube-hitomi, yano-koharu), the ch3 p.100 roster
dump (kobashi-yume, matsushita-chiaki, ninomiya-yui, nishi-haruka,
nomura-yuuji, sawada-yasumi, shimizu-naoki, watanabe-norihito,
yashima-mariko, tokitou-hiroya), ichihashi-ruri and maezono (p.27),
morimiya (p.54), tomose-shunsaku (p.247), and minami-hakuo (pp.113,
236 as “Minami-kun”, first name not printed). Name resolutions:
characters.tsv andou-sayo aliases extended to Andou Saya; Ando Saya
(both spellings printed by the corpus), morofuji-rika gained the rika
alias (bare “Rika” in the stairwell lines is her); the p.54 Tokitō is
hiroya or katsumi, not printed — excluded from both ledgers and noted
in ch2; p.2 is the table of contents (no prose); p.244’s author-note
reference to Ayanokouji Kiyotaka’s past carries a real row on his
ledger; the ch2 roster-only note is superseded — every p.39 name that
now has a ledger carries a row (machida, hamaguchi, manabe, ibuki,
beppu, takemoto, yabu, yamashita, morishige, ichinose, and the ch4-opened
files). The volume file gained its closing stamp
<!-- walk: y1v4 postscript → DONE -->; the byte-identical duplicate
ch5 and ch6 boundary stamps were reduced to one each (§6 one stamp per
chapter; no content rows touched).

Verify 1074 [says] + 316 non-says ALL PASS; gate exit 0 (R18 0, R19
82/82); make check OK (R19 82/82); build 180 pages, 51 assets; hash
`deae8e046450e1f875866cd52c55febc` twice. New tags: none. Open:
search Tier 2/3 (fuzzy/typo tolerance and speed) is next per the
owner, then y1v5.

search: fuzzy matching and focus preload

Search Tier 2/3 per the owner's task order (faster + fuzzy). Edits
confined to gen/assets/app.js and gen/tests/browser_test.js — no index
format change, no content, no ledgers. What changed: the index now
preloads on focus of the header or search-page box instead of on the
first keystroke, and loadIdx keeps a callback queue — the old one-shot
onload let a second show() during load run find() against an undefined
IDX and drop that render. Every exact miss now falls back to
edit-distance-1 variants (deletes, transposes, a-z substitutes and
inserts; cached; tokens of 4+ letters only): global find() resolves a
missed token through a word-to-rows map built once after load, the
character scope resolves a missed name through the name-word map only
when exactly one roster id matches (ambiguity falls back to global, so
the kei karuizawa isolation rule holds), the scene filter and the people
directory fall back per item against a word list. Exact substring
behaviour is untouched, so every existing query returns what it did.
The stale browser-suite counts (253 rows, 17 with a page, 88 scenes)
now derive from the DOM and the payload file instead of hardcoding, and
three typo assertions were added: directory "horikta", scene filter
"conveniance", header "horikta". make browser 25/25 — it failed 4/29
before (jsdom was missing; npm install jsdom --no-save, node_modules
left untracked) and those four failures were the stale counts. make
check OK (R18 0, R19 82/82); gate exit 0; build 180 pages, 51 assets;
hash `251c3c38a7b4e2e11d99b2d66116a18c` twice. New tags: none. Open:
y1v5.

kb: dotted volume ids accepted by read, chapters and verify

Owner-approved normalization (the y1v4.5 walk was blocked before its
first chapter): volumes.tsv, every ledger heading and verify's own
VOL_TOKEN_RE use canonical dotted ids (y1v4.5), but walk_locate folds
dots out of filenames and only special-cased y0, so read/chapters/next
exited with "unknown vol key 'y1v4.5'" and verify2/3 either refused the
dotted arg or, given the folded key y1v45, matched zero ledger lines
and passed vacuously. Fix, three files, mechanical: walk_locate strips
dots from the incoming --vol the same way it folds filenames; verify2
and verify3 look the text file up through fold_vol(volkey) and compare
contexts folded on both sides (not ctx or fold_vol(ctx) != key).
Canonical ids stay dotted everywhere on the ledger and content side —
no TSV, ledger or site change; the site hash is unchanged. Proof:
read --vol y1v4.5 --pages 1-2 prints pages; next --vol y1v4.5 lists
the 8 real sections (ch1 p.10 … postscript p.224-227); verify
--vol y1v4.5 runs (0 lines, nothing written yet); control
verify --vol y1v2 still checks 1066 [says] + 659 non-says, ALL PASS —
not vacuous. Nine dotted volumes (y1v4.5 … y2v12.5) unblocked. Known
gap left alone: y0's volume-ledger token is not a VOL_TOKEN match, so
y0 lines would not associate — y0 is walked last; noted for then. make
check OK (R18 0, R19 82/82); gate exit 0; hash
`251c3c38a7b4e2e11d99b2d66116a18c` twice (kb changes do not touch the
site). New tags: none. Open: y1v4.5 walk, chapter 1 p.10.

y1v4.5 ch1: Summer Vacation is Nearly Over (p.10)

First section of the vignette collection, a single page: the
collection’s first-person frame — the Sazae-san syndrome, the case that
the free years of life are the school years and most of a life is
spent sacrificing for society, and the thesis line naming the book “a
selection of vignettes about students wavering in that space between
childhood and adulthood.” No named character and no school business on
the page: one new scene on Ayanokōji’s file (the first volume’s
opening-monologue precedent; the page prints no name, recorded as a
[note]), and the new volume file ledgers/volumes/y1v4.5.md opened in
the volume bullet dialect with the ch1 section. Page-map notes: the
printed footer reads “Page 1” although the marker is p.10; front matter
pp.1–9; translator watermark at the foot, not story text. Sazae-san is
the TV cartoon of the opening, not a character — no new entities. The
walk tools now track the dotted volume end to end (next shows ch1
done, ch2 pp.11-48 next). Quotes: verify 2 non-says ALL PASS (0 says);
make check OK (R18 0, R19 82/82); gate exit 0; build 180 pages, 52
assets (the volume’s first scene payload); hash
`31b9bbdd79993ecc0bd1d4b64778800d` twice. New tags: none. Open: ch2
pp.11-48 (read 11-29, then 30-48 --blank).

y1v4.5 ch2: Ibuki Mio has Surprisingly Good Sense (pp.11–48)

The collection’s first real story, five sections. Setup: Sudou’s
fortune-teller call on his tournament rest day (the 100,000-point
transfer arrives first; the real motive is a Horikita invitation; the
failed invite gets “Then forget about it”); Horikita’s phone take on
cold reading and her refusal; the couples-only fifth floor where the
attendant names Ukon-sensei; Ibuki refused in the next line — the
queue talk (island fistfight recap, Ryuuen hatred, the Class D leader
question), the awareness lecture and the mass-murderer jibe; the
no-partner list (Horikita, Kushida, Sakura, the guys) and the next-day
reunion; the pair queues and Ibuki’s grudge worry is dismissed on
ability-versus-feelings grounds; §2.4 the reading — hooded fortune-
teller, Basic Plan, balance “barely enough” at roughly 6,000 points,
the fate tenchuusatsu pronouncement and the no-detour advice; §2.5 the
detour taken on purpose, the elevator trapped on the third floor (dead
emergency line, phones at four percent and dead, magic-marker number,
heat, hatch, button schemes, the floor-plus-close press coinciding
with the adults’ remote), and Katsuragi at the doors — the cut-off
call, Sudou “performed brilliantly,” the friendship flash-forward.

Entities: new file ledgers/people/ukon.md (roster row pre-existed;
role: visiting fortune-teller; her tent lines filed there, the
one-fortune-teller inference recorded in the volume file). Passing
mentions anchored: yamauchi (pp.13, 28), ryuuen (pp.23, 31), kushida
(pp.28, 41), sakura (pp.28, 41), ike (p.28), karuizawa (p.41),
horikita (pp.23, 28, 30, 41, 43), sudou (pp.28, 48), katsuragi’s
first scene (p.48). Places: keyaki-mall gains the queue and elevator
sections; content/places.tsv keyaki-mall volumes cell +y1v4.5
(add-only). Systems: private-points gains the transfer (p.11) and the
Basic Plan spend (p.34).

Defects kept as printed: “tenchuusatsu !” (p.36, space before the
exclamation); the “N ext, please.” drop-cap split not quoted; p.22
blank scan; footers run nine behind the markers throughout. Quotes:
verify 46 [says] (3 too short/skipped) + 48 non-says ALL PASS. make
check OK (R18 0, R19 82/82); gate exit 0; build 180 pages, 52
assets; hash `ddd34299d8ca9caacfd9a80af72c6aa3` twice. New tags:
none. Open: ch3 pp.49-107 (read 49-78, then 79-107 --blank).

y1v4.5 ch3: Katsuragi Kouhei is Surprisingly Troubled (pp.49–107)

Read in two halves (49–78, then 79–107 --blank) and written between
them; ten subsections 3.1–3.10. Setup: Kushida's group-chat invite for
Inogashira's birthday, the class broke until the September 1 deposit,
the pooled 500-point gift. Beats: the shopping trip where Ike blows up
at Shinohara over the orange-character keychain and Katsuragi is caught
buying chocolate with an August 29 birthday card (p.57 blank scan); the
room scene where Kushida supplies Horikita's February 15 and Sudou's
jealousy plan is banned, leaving AK the investigation; the crossroads
stakeout intercepted by Manabu and Tachibana — island leader-name leak,
sister rejection, vice-president offer, Nagumo warning, all refused;
the tail to the school building and the chocolate-shelf cleanup that
raises the outside-contact disadvantage; the self-gift theory flip and
the 1,500-point ask; Kushida joining the run and the bench talk with
Horikita (Ryuuen loss, rock bottom, island contradiction); the birthday
ambush turning into the student council visit — package refused, points
cannot buy explicit rules, twin sister and orphans revealed, Manabu's
free hand; the lobby defeat, AK's room plan, Sudou recruited for
100,000 points (20,000 advance / 80,000 after, routed through AK,
lunchbox transport, hidden phone, video proof) and a perfect run; the
closing Katsuragi-POV section with Ike and Yamauchi's party poppers and
Kushida's melted ice cream cake.

Ledgers: 23 files carry `<!-- walk: y1v4.5 ch3 → p.107 -->` — 12
appended in both halves, 3 half-2-only (ryuuen-kakeru,
student-council-room, the volume file), 8 half-1-only stamped by hand
(inogashira, nagumo, ibuki, keyaki-mall, hirata, ichinose, kouenji,
shinohara). New files: ledgers/people/inogashira-kokoro.md,
ledgers/people/nagumo-miyabi.md (roster rows pre-existed with y1v4.5
in their volumes cells), ledgers/places/student-council-room.md (place
row pre-existed; the site dot flips to read-line-by-line). Mention
anchors: chabashira p.71+87, kouenji/ichinose p.72, hirata p.64,
sakura p.49+83, ryuuen p.86, shinohara p.53–55+61, ibuki p.49+61.
Attribution gaps kept: p.74 chat sender unprinted; the second
party-popper boy of p.105 inferred as Yamauchi (only Ike is named); the
p.82 contribution and celebrate-tomorrow lines untagged.

Defects kept as printed: short pages p.57, p.85, p.107 (one line
each), p.59 (three lines); footers run nine behind the markers (p.49
prints “Page 40”). Quote fixes during the walk: the island question
spans p.70/71 (retargeted to a p.70 fragment) and Tachibana's line
corrected to “You're glad…” (p.69). Quotes: verify 349 [says] (5 too
short/skipped) + 57 non-says ALL PASS. make check OK (R18 0, R19
82/82); gate exit 0; build 180 pages, 53 assets; hash
`a4367c75078ad5c359625972ec57080a` twice. New tags: none. Open: ch4
pp.108–131.

y1v4.5 ch4: Dangers Lurk in Everyday Life (pp.108–131)

Read in two halves (108–119, then 120–131 --blank) and written between
them; six subsections 4.1–4.6. Setup: the 6:00 P.M. water-department
failure cuts the dormitory until early morning and Horikita's two
unanswered calls turn a quiet dinner into a worry. Beats: the 9:00 P.M.
turtle parable and the past-nine request; the right hand stuck in a
small water bottle for over two hours; every local source dry —
cafeteria out, vending machines sold out, Ike and Sudou refused on
principle, Hirata unreachable; the Kushida grudge with the ship-exam
recap (Outcome #1's 500,000/1,000,000, "I assume she's guilty",
responsibility both ways); the disguise run — handkerchief, bath
towel, going as they are — down the corridor where Maezono's door
opens and Kushida offers water that Horikita presses away; the locked
east stairwell, the lobby camera, the elevator where Kouenji orders the
top floor and never leaves the mirror; Sakura's late reply, the bottle
off, gratitude extracted, and Ayanokōji trapping his own hand testing
the same bottle.

Ledgers: 17 files carry `<!-- walk: y1v4.5 ch4 → p.131 -->` — 14
appended in both halves (including the volume file), 3 half-1-only
stamped by hand (ike, sudou, cafeteria). New files:
ledgers/people/maezono.md, ledgers/exams/cruise-ship-exam.md,
ledgers/places/cafeteria.md, ledgers/places/dormitory.md (all roster
and place rows pre-existed with y1v4.5 in their cells; no TSV edits).
Mention anchors: hirata p.120, sakura p.122+130, kouenji p.129–130,
maezono p.125–127, ryuuen/katsuragi p.122 speculation, kushida
p.120–121 as subject and p.125–127 in the corridor, keyaki-mall
p.108+122. Quote rows were pre-split to one sentence per pair before
append; three half-1 rows fixed the same way before verify.

Attribution gaps kept: none — every spoken line names its speaker;
unnamed on the page: the karaoke friends (p.123), the lobby students
and stairwell voice (p.128), the cafeteria lady. Defects kept as
printed: blank scan p.117; footers run nine behind the markers (p.108
prints “Page 99”). Quotes: verify 447 [says] (8 too short/skipped) +
58 non-says ALL PASS. make check OK (R18 0, R19 82/82); gate exit 0;
build 180 pages, 56 assets; hash
`ec89b51796f06012fa6aa88093943f2d` twice. New tags: none. Open: ch5
pp.132–152.

y1v4.5 ch5: A Day of Girl Troubles and Disaster (pp.132–152)

Read in one pass (21 pages, --blank) and written at once; three
subsections 5.1–5.3. Setup: Yamauchi bursts in on the last vacation
days with a printed love letter to Sakura and drafts AK to proofread
and deliver it — the tribute line and scary font go, the Kokugikan
sumo final stays as a probable lie. Beats: the reverse-comparison plan
(Kushida lures Sakura out, nothing said, AK made to look like the
confessor); the handover and Sakura's panic — Horikita worry, the
refusal to read together, she leaves to read alone; Yamauchi's faith
in her averted eyes and "sigh of love"; the midnight call —
responsibility talk, the dating question that perks up at zero
experience; the answer in the rain behind the school building —
soaked, Sakura turns him down in person while AK watches the first
confession he has ever seen; Yamauchi leaves relieved and matured,
lending AK a phone as an exception.

Ledgers: 8 files stamped `<!-- walk: y1v4.5 ch5 → p.152 -->` — ak,
yamauchi, sakura, kushida, horikita, school-building, dormitory, the
volume file. New file: ledgers/places/school-building.md (place row
pre-existed with y1v4.5; no TSV edits). Kushida and Horikita are
named-but-absent: entries are other people speaking about them, noted
as such. Mention anchors: none extra — no other roster names in the
chapter.

Attribution gaps kept: none — every spoken line names its speaker.
Defects kept as printed: short page p.140 (one line); footers run nine
behind the markers (p.132 prints “Page 123”). Quotes: verify 539
[says] (10 too short/skipped) + 58 non-says ALL PASS. make check OK
(R18 0, R19 82/82); gate exit 0; build 180 pages, 57 assets; hash
`8a0bb5345101c36556e7f772ea5c09f2` twice. New tags: none. Open: ch6
pp.153–204.

y1v4.5 ch6: A Gathering Between Classes (pp.153–204)

The last day of vacation, read in two halves (153–178, 179–204). The
rest-area deal: Karuizawa's hidden VIP points and bullying history, the
anti-bullying order with Sakura's protection, Hirata and Chabashira
named as enforcers, the liquid-or-clay self-model, Horikita as a magic
cloak of invisibility. The group chat coerces Horikita into an 8:30
lobby attendance on the water-bottle favor; Sudou oversleeps from club
exhaustion; Ichinose arrives with three friends. The locker room: the
heavy-bag suspicion, Sudou's ~3,000 club points, the headlock on Ike
and Yamauchi. At the pool: rash guards funded by Katsuragi's payment,
Ichinose assessing Ayanokōji's build, Sakura's growth, Kanzaki and
Shibata's Class B group joining to make thirteen, and Nagumo Miyabi's
volleyball show — his first physical appearance in the walk (student
council vice president, second-year Class A, elections history with
President Horikita, Ichinose's application decided by him). The
volleyball bet: lunch worth up to 10,000 points, Sudou as the wall,
Ayanokōji's deliberate fumble with Ichinose watching, Class D's
two-set victory. The poolside deal: Karuizawa hands over the hard
plastic object, the expulsion talk aimed at her three former bullies,
the distrust of Hirata, the crush-and-toss of the object, and the shove
that ends with both of them in the water. Dusk: the convenience store
ice cream (Ultra Choco Monaka, Sakura's freezer freeze, Ayanokōji's
soft-serve revelation), lobby farewells, and the sunset walk where
Horikita admits she had fun and keeps her reflections a secret.

Ledgers: 24 files stamped `<!-- walk: y1v4.5 ch6 → p.204 -->` — ak,
karuizawa, horikita, ichinose, kushida, hirata, sudou, ike, yamauchi,
sakura, kanzaki, kouenji, nagumo, horikita-manabu, hoshinomiya,
private-points, swimming-pool, dormitory, the volume file; plus
half1-only hand-stamps on chabashira, katsuragi and cruise-ship-exam.
New files: ledgers/people/shibata-sou.md (roster row pre-existed;
created mid-chapter after his p.177 greeting — a duplicate heading
introduced by the first append was removed before verify) and
ledgers/places/convenience-store.md (place row pre-existed with
y1v4.5; no TSV edits). Nagumo, Manabu and Hoshinomiya are
named-but-absent: entries are others speaking about them or a back
reference, noted as such.

Attribution gaps kept: the question "Wait, are you paying for the
whole thing yourself?" (p.190) has no tagged speaker. Defects kept as
printed: blank pages p.173 and p.198 (footer only); Sudou's meathead
definition and the "winners gets" grammar slip stay as printed and are
flagged in notes; footers run nine behind the markers (p.153 prints
"Page 144"). Two quotes straddled page breaks (the anti-bullying
sentence p.158→159, "Nagumo's limited potential is obvious" p.180→181)
and were trimmed to the text wholly on the cited page before verify.
Quotes: verify 718 [says] (13 too short/skipped) + 63 non-says ALL
PASS. make check OK (R18 0, R19 82/82 after rewording one rel row
whose unquoted "you" counted twice on the volume page); gate exit 0;
build 180 pages, 58 assets; hash `f66222d80c77fc6cf6bdf2f7def67566`
twice. New tags: none. Open: ch7 pp.205–223, ch8 postscript
pp.224–227, volume-end coverage gate.

y1v4.5 ch7: Ike, Yamauchi, and Sudou's Summer Vacation (Extra Stories) (pp.205–223)

The extra-stories chapter, read in one pass. Operation Delta: the
three idiots pitch a peeping plan in Ayanokōji's room; Ike's detailed
facility map and roof-camera RC car turn out to come from the
Professor (Sotomura, by his established nickname — the page never
prints the name); the floor vent connects the year-matched locker
rooms at fifteen by forty centimeters. Ayanokōji agrees to form the
human wall only on a one-time condition, with a report to the school
as the threat, and tells the group to arrive at nine on the dot. The
locker-room execution reaches the monitor; Ayanokōji leaves early so
the girls won't grow suspicious. On the recorded girls' side: Kushida
and Ichinose's figure talk, Sakura hiding in her rash guard, Ichinose's
Kanzaki intelligence run for a girl in Kushida's class, and Karuizawa
— with Sonada and Ishikura as cover, locker keys pre-procured —
swapping the recording card for an empty one exactly as Ayanokōji
instructed her ahead of time. The payoff: the empty folder on his
computer annihilates the three's ambitions.

Ledgers: 17 files stamped `<!-- walk: y1v4.5 ch7 → p.223 -->` — ak,
ike, yamauchi, sudou, karuizawa, horikita, kushida, ichinose, sakura,
kanzaki, sotomura (new y1v4.5 block), swimming-pool, dormitory,
private-points, the volume file. New files: ledgers/people/sonada.md
and ledgers/people/ishikura.md. TSV edits: sonada row added (y1v4.5);
y1v4.5 added to sotomura-hideo's volumes cell (named via the Professor
nickname). The roster also holds ishikura-kayoko with the same sort
and volumes — left untouched, flagged as an open roster question.

Attribution gaps kept: the untagged p.207 "I agree" line, p.210
"So, what's the plan?", p.214 "Got it.", and p.222 "We're all in this
together."; Sudou's Suzune claim is recorded under him with a note
that the translation leaves it untagged. Defects kept as printed:
short pages p.216 (three lines) and p.217 (two lines); Ike's "peeping
on some uggo" and Sudou's grammar stay as printed; footers run nine
behind (p.205 prints "Page 196"). Quotes: verify 776 [says] (14 too
short/skipped) + 65 non-says ALL PASS on the first run. make check OK
(R18 0, R19 82/82); gate exit 0; build 180 pages, 58 assets; hash
`cef5f60f91273bd2ffaed86780e83237` twice. New tags: none. Open: ch8
postscript pp.224–227, volume-end coverage gate.

y1v4.5 ch8: Postscript (pp.224–227)

The author’s afterword closes the volume: Kinugasa’s four-month
gap and party anecdote, the swimsuit scene and the editor’s rebuke,
the growing circle of girls around Ayanokōji and the promise that
the next volume opens his past, the three kinds of students named for
the stretch ahead, the manga’s first-volume credits to Yuyu-sama,
Ichino-sama and Tomoseshunsaku-sama, the bonus-story teaser, then the
author/illustrator bios and the publisher newsletter page. Author’s
note only — no in-world evidence; attribution gaps: none.

Ledgers: 3 files stamped — ayanokouji-kiyotaka (passing mention,
p.224–225), ichino-yuyu (passing mention, p.224; new ledger via
ledger-new, her roster row already carried y1v4.5), and the volume
file with the ch8 stamp and the closing
`<!-- walk: y1v4.5 postscript → DONE -->`. No TSV edits. Defects
kept as printed: footers run nine behind (p.224 prints “Page 215”).
Quotes: verify 776 [says] + 65 non-says ALL PASS (the postscript rows
are unquoted paraphrase, as in y1v4). make check OK (R18 0, R19
82/82); gate exit 0; build 180 pages; hash
`1ba241f64ee5c8a97153336ceb17073b` twice. New tags: none. Open:
volume-end coverage gate.

y1v4.5 volume-end coverage gate

Full-roster locator sweep (walk_locate.py locate --vol y1v4.5, all 255
ids) classified against every ledger citation by a read-only comparison
script (/tmp/opencode — prints only, never writes a ledger).
Substring/referent false positives discarded with page evidence: aga
p.218 (against), andou-sayo p.6 (random), chiba p.9 (Tachibana), etou
p.8 (detour/retorted/veto), housen-kazuomi p.121/135 (chosen), iki
p.100 (Horikita), miya p.2 (okonomiyaki/Hoshinomiya), mori-nene p.4
(memorize), nishi-haruka p.4 (finishing), oda-takumi p.25
(today/yesterday), shiba-katsunori p.177–187 (Shibata — same pages as
shibata-sou), yano-koharu p.57 (Ayanokouji), ichino-yuyu p.32
(Ichinose). TOC and chapter-title pages excluded (p.2, p.11, p.49).
Referent splits kept apart: Manabu-only pages off Suzune's ledger
(p.67–69, 72–73, 91–94, 104), Suzune-only pages off Manabu's (the
fortune/birthday runs p.13–65 and the pool/sunset runs p.160–224).
Ledger titles like "p.49, 51–55" re-parsed so bare page spans after the
first p. count as cited (false gaps inogashira p.55, tachibana p.71,
ike p.52 dropped).

Every remaining real gap page got hand-written paraphrase sections
placed before the chapter's boundary stamp — 37 sections across 20
ledgers, plus a new ledgers/people/tomose-shunsaku.md (p.224, 226;
ledger-new; roster row already carried y1v4.5). No quotation marks in
the new rows, so no new quote surface for verify. No TSV edits and no
cell adds: every cell=False candidate was a false positive. Two roster
oddities left untouched and flagged: ayanokouji-atsuomi's volumes cell
has carried y1v4.5 since the baseline file (8b6cb25) but the volume
never names him (locator 0 hits, no Atsuomi/father in the text); the
duplicate row ishikura-kayoko shares ishikura's sort and volumes — its
locator hit p.220 is recorded on ishikura only.

Quotes: verify 776 [says] (14 too short/skipped) + 65 non-says ALL
PASS. make check OK (R18 0, R19 82/82 — no second person in the new
rows); gate exit 0; build 181 pages, 60 assets (shibata-sou crosses the
scenes threshold and gains a page; nagumo-miyabi and shibata-sou gain
search assets); hash `32205736de3595c8d44eca7197f4fe2a` twice. New
tags: none. Volume complete — DONE stamp in place. Next: y1v5.

y1v5 ch1: Sudou Ken’s Soliloquy (pp. 11–12)

The volume opens with the fourth consecutive non-Ayanokōji cold-open
soliloquy: Sudou alone with his backstory — mother gone to the
nightclub business, father hunched over janitor’s work, tennis and
pingpong never top-tier, basketball and the pulled recommendation,
“trash, born from trash,” and the free school that could guarantee his
future. Dialect kept as printed. p.12 is a blank scan (footer only).
Two ledgers stamped (sudou-ken, the new ledgers/volumes/y1v5.md). No
TSV edits — Sudou’s row already carried y1v5. Quotes: verify 0 [says]
+ 8 non-says ALL PASS. make check OK (R18 0, R19 82/82); gate exit 0;
build 181 pages, 61 assets; hash `3799ce92a44fe3385b66dab7a958d50d`
twice. New tags: none. Open: ch2 pp.13–38.

y1v5 ch2: The School Sports Festival Begins (pp. 13–38)

The festival takes over the volume: the Pallet café zodiac debrief
(rabbit-group alphabetical VIP order; Hirata’s Kushida proposal,
refused), Chabashira’s full rules briefing — Red A+D vs White B+C,
15/12/10/8 and 50/30/15/10 scoring, losing-team and grade-rank class
point swings, private-point and written-test-point prizes, MVP 100,000,
ten-lowest exam penalty, 100,000-point substitutes — Sudou/Ike/Yamauchi’s
huddle with Horikita, the Gymnasium assembly (Fujimaki takes Red Team
command; Katsuragi–Hirata pact; Ryuuen walks Class C out; Sakayanagi
Arisu fully introduced), Ayanokōji’s not-a-special-exam argument, and the
Chabashira gate warning. New files: ledgers/people/fujimaki.md and
ledgers/exams/sports-festival.md (both roster/exam rows pre-existed);
café Pallet noted as a named location without a places row. 22 ledger
files stamped with y1v5 ch2 → p.38; no TSV edits. Quotes: verify 91
[says] + 18 non-says ALL PASS. make check OK (R18 0, R19 82/82); gate
exit 0; build 181 pages, 62 assets; hash
`211625d520c12d9eb5b3b4697d06103b` twice. New tags: none. Open: ch3
pp.39–53.

### y1v5 ch3 (pp.39–53) — Class D's Objective — walked
Read the full chapter with blank flags (549-line extract). The blackboard
meeting: Hirata's "Raising Hands" versus "Ability", Sudou claims every
recommended event, Shinohara's objection, Karuizawa/Kushida's counter and
Horikita's private-point compromise, the 16–13 vote, Kōenji's refusal.
§3.1: the entrance meeting — Karuizawa's text message, the Class A answer,
the classmate-will-betray-us prediction, the life-jacket parable. §3.2:
grip strength (Sudou 82.4, Ayanokōji 60.6 second, Hirata 57.9, Ike 42.6),
four-way tug-of-war order, rock-paper-scissors roster, top-secret notebook.
Ledgers touched: 24 files stamped y1v5 ch3 → p.53 — volumes/y1v5,
ayanokouji-kiyotaka, hirata-yousuke, horikita-suzune, sudou-ken,
shinohara-satsuki, karuizawa-kei, kushida-kikyou, chabashira-sae,
sakura-airi, ike-kanji, kouenji-rokusuke, sotomura-hideo,
yukimura-teruhiko, maezono, exams/sports-festival, systems/private-points.
New files (ledger-new, start y1v5): onodera, hondou-ryoutaro,
miyamoto-soshi, miyake-akito, mori-nene — all roster rows pre-existed;
no TSV edits. Quotes: verify 125 [says] + 78 non-says ALL PASS. Pre-verify
audit caught and fixed fabricated/incorrect rows (an invented opening
thought, a Chabashira chiding that is not in the text, a three-times RPS
that is two rounds, Miyamoto/Kōenji tug-of-war misattributions) before
commit. make check OK (R18 0, R19 82/82); gate exit 0; build 181 pages,
62 assets; hash `bfc0ce9e40792479cf8bbc9187ba29f1` twice. New tags: none.
Open: ch4 pp.54–67.

### y1v5 ch4 (pp.54–67) — Everyone's Calculations — walked
Read the full chapter with blank flags (463-line extract). First independent
practice: Class A/B watch from the windows, Class C’s silence reads as
Ryuuen’s strategy already set; the Sudou–Horikita name bet (first in grade
buys the first name, failure forbids it forever); §4.1 aptitude tests —
Sakura last, Sudou unbeatable, Kushida names him leader and Horikita gives
a cold half-approval; §4.2 Sudou coaches (tug-of-war, cavalry, dirt-kicked
Ike and Yamauchi) while Horikita drives partners away and Ayanokōji boxes
her in on the holding-back question, then outpaces her in the three-legged
demo; §4.3 mid-September, two named problems — Horikita’s partnerships and
Kushida’s rooftop hatred. Ledger appends: 15 files stamped y1v5 ch4 → p.67
(volumes/y1v5, ayanokouji-kiyotaka, horikita-suzune, sudou-ken, hirata-yousuke,
ike-kanji, kushida-kikyou, kouenji-rokusuke, sakura-airi, yamauchi-haruki,
onodera, inogashira-kokoro, katsuragi-kouhei, ryuuen-kakeru, sotomura-hideo);
no new files, no TSV edits. Two fixes pre-verify: an untagged praise line
moved out of Hirata’s ledger into an attribution-gap note, and an inverted
Katsuragi/Ryuuen cooperation row corrected. An append re-pass briefly
duplicated the Ayanokōji section; the duplicate was removed before verify.
Quotes: verify 131 [says] + 118 non-says ALL PASS. make check OK (R18 0,
R19 82/82); gate exit 0; build hash
`84cb0fa45e1f945543e8a69c9d0083c2` twice. New tags: none. Open: ch5
pp.68–85.

### y1v5 ch5 (pp.68–85) — There's a Reason for Their Relationship — walked
Read the full chapter with blank flags (602-line extract; blank scans p.78
and p.85). The Saturday outing: Ayanokōji recruits Horikita and Kushida,
lays the cruise-ship theory (Kushida may have sold her own VIP identity),
noodles with Sudou/Ike/Yamauchi, then the grounds — Shibata's goal, Nagumo
outclassing Hirata and Shibata, Kushida's “It’s me,” Horikita’s direct VIP
question and ally demand, and Ayanokōji’s exit. §5.3: the participation
table, the anchor fight, and the brother reveal (student council president).
Ledger appends: 16 files stamped y1v5 ch5 → p.85 (volumes/y1v5,
ayanokouji-kiyotaka, horikita-suzune, kushida-kikyou, sudou-ken, ike-kanji,
yamauchi-haruki, hirata-yousuke, nagumo-miyabi, shibata-sou,
sakayanagi-arisu, ryuuen-kakeru, katsuragi-kouhei, sakura-airi,
karuizawa-kei, horikita-manabu); nagumo and shibata ledgers gained their
first y1v5 headings; no TSV edits. Open question kept as printed: p.79’s
“Sonoda-kun from Class C” matches both sonoda-masashi and sonoda-chiyo
(locator hits both) — left in the attribution gaps, no person row filled.
Three non-says quote mismatches caught by verify and fixed to corpus-exact
(“the bomb waiting to go off inside Class D”; “aren’t really on speaking
terms”). Quotes: verify 141 [says] + 181 non-says ALL PASS. make check OK
(R18 0, R19 82/82); gate exit 0; build hash
`fd05909784782d880bf27cb7bbdc344b` twice. New tags: none. Open: ch6
pp.86–143.

### y1v5 ch6 (pp.86–143) — The Curtains Rise — walked
Full chapter read in two halves (first half pp.86–114, second half
pp.115–143; blank/short scans p.93, p.122, p.134, p.139, p.143). Morning
half: festival opening and Fujimaki’s speech, Sudou’s dash/hurdle/obstacle
firsts, Kōenji’s cottage pose, capture-the-flag and tug-of-war (Hashimoto’s
rebellion, Ryuuen’s bow), girls’ obstacle fall with Kinoshita’s name-call.
Second half: three-legged firsts, Class C’s sole-target cavalry on Horikita,
Karuizawa’s blocked rescue, boys’ cavalry bait and sticky headband, Sudou’s
punch on Hirata and the cover, Chabashira’s preventative report, the
200-metre and Ayanokōji’s “burden/weapon” push, lunch with the traitor lie.
Ledger appends: 56 files stamped across both halves (ch6a 28, ch6b 29
including sports-festival; volume chapter section extended once and stamped
y1v5 ch6 → p.143). New ledgers: hashimoto-masayoshi, yamada-albert,
nomura-yuuji, suzuki-hidetoshi, yajima-mariko, kinoshita-minori (first
y1v5 headings). First y1v5 headings also: kanzaki-ryuuji, komiya-kyogo,
ishizaki-daichi, kondou-reo. A duplicate Chapter 6 section in
volumes/y1v5.md from a double first-half append was removed before the
second-half update. Quote hygiene: single-sentence [says] pairs, page
straddles trimmed or noted (Hirata’s “something interesting” p.135–136,
Ryuuen beast-of-burden p.125–126), short cries moved to [note] (“Aaahhh!”,
“Go, Suzune!”), “Sudou-kun” hyphen verified via norm (corpus prints
“Sudoukun” across a line break). R18 wording fixed (volume row said
“ledgers created this chapter”); R19 second person restored to 82/82 by
rewriting Chabashira’s unquoted “keep your distance.” Quotes: verify 301
[says] + 199 non-says ALL PASS (0 too short). make check OK (R18 0,
R19 82/82); gate exit 0; build hash `919b2428e7ea373295286796ebc08a4b`
twice. New tags: none. Open: ch7 pp.144–159.

### y1v5 ch7 (pp.144–159) — For Whose Sake? — walked
Full chapter read in one pass (blank/short scans p.150, p.159). Horikita
POV: alone after Ayanokouji’s beatdown to the nurse’s office; 300,000-point
substitute plan; Kushida’s summons; Kinoshita’s deliberate-fall accusation
and the Devil’s Proof; Ryuuen’s million-point deal and kneeling condition;
Kushida’s points refused; “Your strategy beat mine”; brother at the
entrance; failed Sudou search; Ayanokouji declines to come along.
Ledger appends: 9 files stamped y1v5 ch7 → p.159 (horikita-suzune,
chabashira-sae, kushida-kikyou, kinoshita-minori, ryuuen-kakeru,
horikita-manabu, ayanokouji-kiyotaka, tachibana-akane first y1v5 heading,
volumes/y1v5 Chapter 7 section). Quote hygiene: single-sentence pairs,
short cries as notes (“No, I can’t,”), one says line with trailing narration
trimmed. Append defect fixed: tmp bodies carried a second full ledger
header (title + char_id + aliases) into eight mid-file positions — headers
stripped, blank line restored after the ch6 stamp; R18 had spiked to 16 on
char_id in search assets and returned to 0. Quotes: verify 425 [says] +
204 non-says ALL PASS (0 too short). make check OK (R18 0, R19 82/82);
gate exit 0; build hash `a6497eb8051f36898e69ec9702eccd44` twice. New tags:
none. Open: ch8 pp.160–180.

### y1v5 ch8 (pp.160–180) — What You and I Lack — walked
Full chapter read in one pass (blank/short scans p.171, p.177, p.180).
Split POV: Ayanokouji’s scavenger-hunt last place (three bad lots);
§8.1 Horikita finds Sudou in the dorm lobby and the worthless-parents
argument; §8.2 Hirata’s 500,000-point substitute burden, Kushida’s
volunteer offer, Ayanokouji taking Sudou’s place, and the traitor
confrontation — Kushida admits leaking the participation table and her
expel-Horikita goal; §8.3 Sudou returns and the ally bargain until
graduation. Ledger appends: 13 files stamped y1v5 ch8 → p.180 (12 people
+ volume Chapter 8 section). Quote hygiene: single-sentence pairs kept
where corpus-exact; short cries as notes (“Horikita.”, “Shut up!”,
“Okay.”); one mis-tagged says line retagged to Ayanokouji. R19: the
chapter title “What You and I Lack” added a second-person hit on the
volume page (+1 over baseline 82); fixed by quoting the title in the
volume heading so the validator strips it as a quotation — count back to
82/82 without touching gen/. Quotes: verify 538 [says] + 206 non-says
ALL PASS (0 too short). make check OK (R18 0, R19 82/82); gate exit 0;
build hash `7137b59766f8c38d10f5167421302f36` twice. New tags: none.
Open: ch9 pp.181–204.

### y1v5 ch9 (pp.181–204) — The Turning Point — walked
Full chapter read in one pass (blank/short scans p.186, p.197). Relay
and closing: Sudou’s return and public apology; Horikita and Miyake
withdraw; Ayanokouji takes the anchor and meets Horikita Manabu’s
standing start; Red Team wins with first-year Class D fourth (−100);
Shibata MVP; the first-name and no-violence bargain; Kamuro’s five-
o’clock summons; Sakayanagi’s White Room greeting (“eight years and 243
days”). Section 9.3 is Horikita’s hallway confrontation: junior-high
past, Ryuuen’s paid Kinoshita injury, the recording bluff, the counter-
recording of his trap plan, Class C traitor, Ayanokouji named mastermind.
Ledger appends: 19 files stamped y1v5 ch9 → p.204 (18 people + volume
Chapter 9 section). New ledger: kamuro-masumi (roster row pre-existed).
Tmp bodies were header-free this time (no duplicate char_id, stamps 1
each). Quote hygiene: short cries/“White Room,”/“Go ahead.” as notes;
the “bury false genius” sentence spans the p.203–204 break and is a note;
trailing “said Sudou/Ike/Hirata” attributions stripped from says rows.
R18 fix before ship: volume “her ledger opens this chapter” → “her notes
were opened this chapter” (pipeline word \bledgers?\b). Quotes: verify
697 [says] (2 too short/skipped) + 212 non-says ALL PASS. make check OK
(R18 0, R19 82/82); gate exit 0; build hash
`860cec3a25ebfa4a6e3aaca3681dd1e3` twice. New tags: none. Open: ch10
postscript pp.205–207 (y1v5 final).

### y1v5 ch10 postscript (pp.205–207) + volume-end coverage gate — walked
Postscript only: Kinugasa’s four-month note, author/illustrator bios,
newsletter block; no in-story dialogue and no roster character on the
page. Volume stamped y1v5 ch10 → p.207 and closed with
`<!-- walk: y1v5 postscript → DONE -->`. Coverage gate: page locator run
for all 49 roster cells carrying y1v5; real gaps (name present, not yet
cited) filled as grouped passing-mention sections across 27 people files
without new chapter stamps. Documented exceptions in the volume coverage
notes: ayanokouji-atsuomi never named; Sonoda-kun p.79 ambiguous between
both sonoda rows; Onodera pp.44/62/182/184 recorded under onodera (full
name “Onodera Kayano” never printed); Kamuro appears only as Masumi on
p.202 (locator misses the surname). Quote hygiene: fill rows use
paraphrase notes where lines were already covered or short; verify 697
[says] (2 too short/skipped) + 251 non-says ALL PASS. make check OK
(R18 0, R19 82/82); gate exit 0; build hash
`76e9e5764687d3400ee0e9c044e103a3` twice. New tags: none. Volume complete.
Next volume per owner order: y1v6.

### y1v6 ch1 (pp.10–13) — walked
New volume opens with Kushida Kikyou’s cold-open soliloquy (first y1v6
heading + start marker on her ledger and Horikita Suzune’s; volume ledger
created via ledger-new). Beats: ideal-self inventory, junior-high incident,
trust-as-currency, bus bump into Suzune. People stamped kushida-kikyou,
horikita-suzune; volume stamped `y1v6 ch1 → p.13`. Short/blank p.13
recorded as a note. verify y1v6: 6 [says] ALL PASS + 7 non-says ALL
PASS; make check OK (R18 0, R19 82/82); gate exit 0; hash
`620b39f6c8f086e584418aa61b1275cf` twice. New tags: none. Next: ch2
p.14–29.

### y1v6 ch2 (pp.14–29) — walked
Student-council handover (Horikita Manabu out, Nagumo in with
indefinite-term/meritocracy pledges); Class D’s second-semester drift;
Satou’s gym-passage phone-number approach; Katsuragi’s corridor Ryuuen
warning with October point totals (A 874 / B 753 / C 542 / D 262);
Karuizawa’s night call about Satou, Manabe and erased call records.
People stamped: ayanokouji-kiyotaka, hirata-yousuke, horikita-manabu,
horikita-suzune, ichinose-honami, ike-kanji, karuizawa-kei,
katsuragi-kouhei, kushida-kikyou, manabe-shiho, nagumo-miyabi,
ryuuen-kakeru, sakayanagi-arisu, sakura-airi, satou-maya,
sotomura-hideo, sudou-ken, totsuka-yahiko, yamauchi-haruki; volume
stamped `y1v6 ch2 → p.29`. Blanks p.20 and p.29 noted. verify y1v6: 40
[says] ALL PASS + 19 non-says ALL PASS; make check OK (R18 0, R19
82/82); gate exit 0; hash `c97c59ab5fd290194fcb0b0f5ddb57cc` twice. New
tags: none. Next: ch3 p.30–59 (30 pp).

### y1v6 ch3 (pp.30–59) — walked
The Paper Shuffle: midterms post from the bottom (Sudou avg 57),
Chabashira’s full final-exam briefing (pairs, ~700 aggregate, question
creation, class-vs-class 50-point swings), meeting call, the junior-high
Kushida incident on the campus detour (lies as the class-destroying
weapon; threat list; Ryuuen alliance), Horikita refuses to expel her,
sports-festival recording put to Ayanokouji, Pallet balanced-pair
strategy and Class C nomination. People stamped: ayanokouji-kiyotaka,
chabashira-sae, hirata-yousuke, horikita-suzune, ike-kanji,
ichinose-honami, inogashira-kokoro, karuizawa-kei, katsuragi-kouhei,
kouenji-rokusuke, kushida-kikyou, manabe-shiho, ryuuen-kakeru,
sakayanagi-arisu, satou-maya, sotomura-hideo, sudou-ken,
yamauchi-haruki, yukimura-teruhiko; volume stamped `y1v6 ch3 → p.59`.
Horikita Manabu not named this chapter (scan false positive from
“Horikita”). R19 regression caught pre-ship: “roundabout thank-you”
matched \byou\b via the hyphen — reworded to “words of thanks” in
ayanokouji and volume rows; baseline restored 82/82. verify y1v6: 159
[says] ALL PASS + 50 non-says ALL PASS; make check OK (R18 0, R19
82/82); gate exit 0; hash `ee9036a4b4578c50d8b966d45e91ec92` twice. New
tags: none. Next: ch4 p.60–75.

### y1v6 ch4 (pp.60–75) — walked
Class C Makes Its Move: Ryuuen’s spy theatre on Class D’s “X” (phone
game with six hand-raisers cleared as innocent; X-audio of the kneel he
was denied; violence-versus-authority speech contrasting former-president
Horikita and Nagumo); Manabe unmasked as lead spy with Yabu and Yamashita;
cruise-ship Karuizawa payback and photo naming Yukimura and Ayanokouji;
closing move — “How about we try using him?” and a text. People stamped:
ayanokouji-kiyotaka, hirata-yousuke, horikita-manabu, horikita-suzune,
ibuki-mio, ishizaki-daichi, kaneda-satoru, karuizawa-kei, manabe-shiho,
morofuji-rika, nagumo-miyabi, nishino-takeko, nomura-yuuji, oda-takumi,
ryuuen-kakeru, yabu-nanami, yamada-albert, yamashita-saki,
yukimura-teruhiko; volume stamped `y1v6 ch4 → p.75`. First y1v6 ledgers
created: nishino-takeko, oda-takumi. Manabu named only as
“former-president Horikita” on p.70 (verified). Blanks p.61 and p.75
noted. verify y1v6: 262 [says] ALL PASS + 50 non-says ALL PASS; make
check OK (R18 0, R19 82/82); gate exit 0; hash
`012e79edde139ed439624bcf98b43625` twice. New tags: none. Next: ch5
p.76–131 (56 pp).

### y1v6 ch5 (pp.76–131) — walked
A Means of Escape (56 pp, two halves): the exam team settles (Hasebe
exits and returns; identical wrong answers; Class C cake roar);
Yukimura’s team-thesis speech and Kaneda as likely question-writer;
Ayanokouji’s management lecture and Ryuuen’s “What are you?” dummy
email; joint Class B library session with Satou and Ichinose; the
pocket-phone eavesdrop and mathematics bet witnessed by Horikita
Manabu; Kushida’s extra condition (Ayanokouji’s expulsion) refused and
Ayanokouji joins the wager. People stamped: ayanokouji-kiyotaka,
chabashira-sae, hasebe-haruka, hirata-yousuke, horikita-manabu,
horikita-suzune, ichihashi-ruri, ichinose-honami, ike-kanji,
inogashira-kokoro, ishizaki-daichi, kaneda-satoru, kanzaki-ryuuji,
karuizawa-kei, katsuragi-kouhei, kouenji-rokusuke, kushida-kikyou,
manabe-shiho, miyake-akito, okiya-kyousuke, onodera, ryuuen-kakeru,
sakayanagi-arisu, sakura-airi, satou-maya, sotomura-hideo, sudou-ken,
yamauchi-haruki, yukimura-teruhiko; volume stamped `y1v6 ch5 → p.131`.
First y1v6 ledgers created: hasebe-haruka, ichihashi-ruri,
okiya-kyousuke. Inogashira duplicate `## y1v6` heading fixed
post-append. R18 regression pre-ship: volume New-named-entities rows
used “ledger(s)” — reworded to plain notes; gate restored to 0. Blanks
pp.90–91, 117, 128, 131 noted. verify y1v6: 651 [says] ALL PASS + 64
non-says ALL PASS; make check OK (R18 0, R19 82/82); gate exit 0; hash
`2f738b9aaacb24c55f04f37f4b9178de` twice. New tags: none. Next: ch6
p.132–176.

### y1v6 ch6 (pp.132–176) — walked
The Ayanokouji Group’s Formation (45 pp, two halves): fifth Yukimura
session moved to the mall café; Ryuuen’s party crashes with Ishizaki,
Komiya, Kondou and Shiina Hiyori; Hiyori’s sugar-estimation coffee and
the Class D master-tactician rumour; Satou-partner anxiety and the
Kyo-chan referral; nicknames and the Ayanokouji Group named with a
first-name rule; Yukimura rejects Teruhiko and takes Keisei; Sakura
joins after Haruka’s test; group-chat movie; Horikita prep call;
Karuizawa’s Hiyori errand and belated birthday sticker (March 8);
Satou arm-grab and Airi’s jealousy check; karaoke meeting with Sudou’s
pi ceiling and Karuizawa’s grape-juice dump on Kushida; Katsuragi
fountain talk; Ryuuen’s signed mass letter alleging Ichinose collects
points illegally; Ichinose routes proof to the school and is cleared.
People stamped: ayanokouji-kiyotaka, hasebe-haruka, hirata-yousuke,
horikita-suzune, ichinose-honami, ike-kanji, ishizaki-daichi,
karuizawa-kei, katsuragi-kouhei, komiya-kyogo, kondou-reo,
kouenji-rokusuke, kushida-kikyou, miyake-akito, ryuuen-kakeru,
sakura-airi, satou-maya, shiina-hiyori, sotomura-hideo, sudou-ken,
yamauchi-haruki, yoshimoto-kosetsu, yukimura-teruhiko; volume stamped
`y1v6 ch6 → p.176`. New ledgers: shiina-hiyori, yoshimoto-kosetsu.
First y1v6 blocks: komiya-kyogo, kondou-reo, katsuragi-kouhei,
shiina-hiyori, yoshimoto-kosetsu. R18/R19 regressions pre-ship:
sakura “ledger so far” reworded to “record”; ryuuen rel “What are you?”
reworded to earlier dummy-account email (mirrored onto the volume
page). Blanks pp.139, 172, 175, 176 noted. verify y1v6: 895 [says]
ALL PASS (8 too short/skipped) + 69 non-says ALL PASS; make check OK
(R18 0, R19 82/82); gate exit 0; hash
`632cf1772c1ef4ec692d7a46f0462094` twice. New tags: none. Next: ch7
p.177–209.

### y1v6 ch7 (pp.177–209) — walked
Exam-eve: Ryuuen shadows Horikita’s manila envelope to the staff room;
Chabashira’s secrecy conditions and 6 p.m. deadline; Kushida’s prior
acceptance revealed; Horikita’s preemptive counter with the teacher;
Ryuuen’s checkmate mockery and the rooftop admission he switched the
questions after X’s warning. Exam morning: Satou partner talk, Karuizawa
interrupt, Hirata names Ayanokōji the mastermind and offers backup;
first subject, Keisei’s predictions hold, Kushida’s agitated math slip.
Post-day: Horikita’s ninety-eight math claim, Sudou’s forty-point
apology, bet settled — Kushida concedes under eighty and refuses the
handshake. §7.4 photo declaration of war; §7.5 rooftop cheat-sheet
plant, juice-and-cleaners deduction, Ichinose letter, Transaction email,
three options, “destroy her.” People stamped: ayanokouji-kiyotaka,
chabashira-sae, hasebe-haruka, hirata-yousuke, horikita-suzune,
ike-kanji, kaneda-satoru, karuizawa-kei, katsuragi-kouhei,
kushida-kikyou, miyake-akito, ryuuen-kakeru, sakagami,
sakayanagi-arisu, satou-maya, shiina-hiyori, sudou-ken,
yamauchi-haruki; volume stamped `y1v6 ch7 → p.209`. First y1v6 block:
sakagami. Cross-footer quotes split at page breaks (ayanokouji
prostrate line; ryuuen results and battle lines). Blanks pp.186, 198,
209 noted. verify y1v6: 1135 [says] ALL PASS (18 too short/skipped) +
69 non-says ALL PASS; make check OK (R18 0, R19 82/82); gate exit 0;
hash `2cac97c2b888d1f4aaf4298a986c15e8` twice. New tags: none. Next:
ch8 postscript pp.210–211.

### y1v6 ch8 postscript (pp.210–211) + volume coverage gate — walked
Postscript: Seven Seas newsletter signup block only (footer Page 201–212);
no story beats. Volume-end locator pass for all 49 roster names carrying
y1v6: strict word-boundary recheck (substring false positives on bare
horikita / ike / kanji / oda discarded); passing-mention sections appended
after the last chapter stamp for 19 people (ayanokouji-kiyotaka,
chabashira-sae, hasebe-haruka, hirata-yousuke, horikita-suzune, ibuki-mio,
ichinose-honami, ike-kanji, inogashira-kokoro, ishizaki-daichi,
karuizawa-kei, kushida-kikyou, manabe-shiho, miyake-akito, ryuuen-kakeru,
satou-maya, sudou-ken, yamauchi-haruki, yukimura-teruhiko); fill-in notes
for residual hasebe / miyake / yukimura gaps; volume Coverage-notes bullet
in the postscript section (atsuomi / ishigami / shibata / shiranami never
named; Chihiro only as “Chihiro-chan” p.115; onodera-kayano p.77 under
onodera; oda real hit only p.65; manabu bare-horikita false positives,
real pp.14–15, 47, 70, 120–122, 168 cited; ike/kanji substring false
positives ignored — real ike gaps pp.149, 193 filled). Real-gap recheck:
0 missing for all strict-pattern roster chars except onodera-kayano (no
file — covered by volume note). R19 regression from unquoted paraphrases
fixed by converting to corpus-exact [says] rows (miyake p.149 Hasebe line;
yukimura p.135 own line); inogashira sections reordered page-wise with
ch3/ch5 stamps; ch5 stamps added for hasebe, ichihashi, kaneda, katsuragi,
kouenji, okiya, onodera, sakayanagi, sakura, sotomura; ch7 stamps for
ichinose, manabe, yukimura; ch8 stamp for ayanokouji; blank line before
kushida p.202–208. Volume stamped `ch8 → p.211` and
`y1v6 postscript → DONE`. verify y1v6: 1137 [says] ALL PASS (18 too
short/skipped) + 69 non-says ALL PASS; make check OK (R18 0, R19 82/82);
gate exit 0; hash `32cc51b89fef404700801208dbf6b93e` twice. New tags:
none. Next volume per owner order.

### y1v7 ch1–ch2 (pp.10–31) — walked
Ch1 (pp.11–13): Ryuuen’s childhood soliloquy — snake kill, violence as elite, boredom with no one to overthrow; p.10 ToC leaf; p.13 blank. Ch2 (pp.14–31): mid-December Keyaki Mall — Ayanokōji’s group (Yukimura, Hasebe, Sakura, Miyake) on class-point maths and Christmas; Komiya/Ishizaki surveillance; island retelling under Horikita’s credit; Ayanokōji confronts Kamuro with photo proof and strikes a mutual-silence bargain; p.31 blank. Volume ledger created (`ledgers/volumes/y1v7.md`). People stamped: ryuuen-kakeru (ch1+ch2), ayanokouji-kiyotaka, yukimura-teruhiko, hasebe-haruka, sakura-airi, miyake-akito, kamuro-masumi, komiya-kyogo, ishizaki-daichi, karuizawa-kei, hirata-yousuke, horikita-suzune, sudou-ken, ibuki-mio, sakayanagi-arisu, kushida-kikyou, ike-kanji (all ch2). Cross-page Hasebe love line split with ellipsis (footer page-number breaks the stream); Kamuro’s two quote pairs split into two rows. verify y1v7: 47 [says] ALL PASS + 8 non-says ALL PASS; make check OK (R18 0, R19 82/82); gate exit 0; hash `44a56308272f08048317f4c56da39672` twice. New tags: none. Next: ch3 pp.32–97.

### y1v7 ch3 (pp.32–97) — walked
Ch3 “Reunions and Farewells” read in two halves (pp.32–64, pp.65–97). Half 1: Sudou’s Class C tail report and Horikita’s decoy bargain; Farewell, My Lovely loan; Shiina library–cafeteria lunch; Keyaki Mall mastermind board (Kouenji cleared by island retirement, Hirata second candidate, Airi’s shy mastermind ask); Satou declined; Chabashira’s summons; Atsuomi’s drop-out demand and Matsuo leverage (self-immolation). Half 2: free-will refusal; Chairman Sakayanagi blocks expulsion on autonomy and government fees — secret recommendation, fifty-point smokescreen; Chabashira unmasked (no father contact, Class A obsession via Hoshinomiya’s old teasing); dusk second-year girl and red charm; Karuizawa last call and cut-off; Horikita Manabu’s Nagumo warning and bridge offer; Sunday karaoke (Keisei five-in-a-row spicy takoyaki, one in 7776); Ichinose–Sakayanagi Arisu walk-past. New ledgers: ayanokouji-atsuomi, matsuo, matsuo-eiichirou (bare-name pointer). People stamped ch3 → p.97: ayanokouji-kiyotaka, ayanokouji-atsuomi, chabashira-sae, karuizawa-kei, horikita-manabu, ichinose-honami, sakayanagi-arisu, hasebe-haruka, sakura-airi, miyake-akito, yukimura-teruhiko, horikita-suzune, nagumo-miyabi, matsuo, hirata-yousuke, sudou-ken, ike-kanji, hoshinomiya-chie, kushida-kikyou, kouenji-rokusuke, ryuuen-kakeru, manabe-shiho, katsuragi-kouhei, komiya-kyogo, ishizaki-daichi, yamauchi-haruki, shiina-hiyori, satou-maya, matsuo-eiichirou. Quote fixes: Matsuo’s-son line cited p.60–61 with ellipsis across footer; Hasebe Kouenji pair split; Sakura S-see pair split; ishizaki non-says paraphrase unquoted; matsuo-eiichirou note reworded off “ledger” (R18). Volume Coverage-notes bullet: bare Sakayanagi pp.65–73 is the chairman not Arisu; bare Matsuo under matsuo; Hoshinomiya/Katsuragi/Manabe mention-only. verify y1v7: 293 [says] ALL PASS + 20 non-says ALL PASS; make check OK (R18 0, R19 82/82); gate exit 0; hash `98a820dae80bbdfcae620c91c34e90f6` twice. New tags: none. Next: ch4 pp.98–119.

### y1v7 ch4 (pp.98–119) — walked
Ch4 “Insanity”: Ryuuen storms Class D with Ishizaki, Yamada, Komiya and Kondou; Chabashira walks out; Hirata holds the line then is sent back; the path ambush smokes out Ayanokōji, Miyake and Yukimura; rest-area duel with Kouenji (mirror smash, zodiac debt, “moron with a paltry intellect”); Sakayanagi arrives with Kamuro, Hashimoto and Kitou — island contract recited (twenty-thousand private points per person per month, Katsuragi’s signature); Ryuuen’s kick blocked by Hashimoto; Kouenji’s little-girl jab; show ends with the narrowed list “that weird creep lurking behind you.” New ledger: kitou-hayato. People stamped ch4 → p.119: ayanokouji-kiyotaka, ryuuen-kakeru, horikita-suzune, sudou-ken, kouenji-rokusuke, sakayanagi-arisu, hirata-yousuke, ishizaki-daichi, miyake-akito, yukimura-teruhiko, hashimoto-masayoshi, kitou-hayato, kamuro-masumi, katsuragi-kouhei, komiya-kyogo, kondou-reo, yamada-albert, ibuki-mio, ike-kanji, yamauchi-haruki, kushida-kikyou, chabashira-sae. Quote fixes: Kouenji’s “My apologies…” line cited p.109–110 with ellipsis across footer; Sudou’s line corrected to corpus “The heck is with that guy?”. horikita-manabu locator hits were bare-“Horikita” false positives (sort is Horikita). verify y1v7: 473 [says] ALL PASS + 26 non-says ALL PASS; make check OK (R18 0, R19 82/82); gate exit 0; hash `56d212bf5d41b6d17a9087cf7c70df6d` twice. New tags: none. Next: ch5 pp.120–151.

### y1v7 ch5 (pp.120–151) — walked
Ch5 “Time to Settle Things” read in two halves (pp.120–135, pp.136–151). Closing ceremony; Ryuuen’s shortlist down to about ten (Sudou, Miyake, Hirata still standing); Shiina declines the hunt for the library; rooftop trap — camera sprayed black, Albert on standby below, Karuizawa summoned alone under past-exposure threat with X warned in parallel; §5.2 interrogation and Manabe leverage; Ibuki holds her while Ishizaki fetches buckets; first dousing. Half 2: school-rule loopholes and the silent-upperclassman rule (Komiya/Kondou evidence); second bucket; §5.3 Karuizawa POV — four dousings, junior-high hell on loop, cruise-ship setup revealed (X used Hirata to place her, then let Manabe bully her for evidence); lips form “K…t…”, then “K-knock…it…off”; she never gives the name; Ryuuen’s respect; “Goodbye, fake me.” People stamped ch5 → p.151: sakagami, horikita-suzune, miyake-akito, shiina-hiyori, kushida-kikyou, kouenji-rokusuke (half1-only, EOF stamps), hirata-yousuke, sudou-ken, manabe-shiho, yamada-albert, ibuki-mio, ishizaki-daichi, karuizawa-kei, ryuuen-kakeru, komiya-kyogo, kondou-reo, morofuji-rika, ayanokouji-kiyotaka (half2 stamps). Structure: ## y1v7 + start inserted for kondou-reo, kouenji-rokusuke, shiina-hiyori, yamada-albert (orphan sections from ch3/ch4); duplicate ## y1v7 removed from horikita-suzune and miyake-akito after a mis-typed first-block append. Quote fixes: Ibuki’s two camera lines split; Ryuuen’s “have you ever noticed…” cited p.137–138 with ellipsis across footer. Two uncommitted [place:rooftop] rows on ryuuen pushed world/rooftop.html over R12 max_words (3238 > 3000) — removed those place-tag rows (scene evidence kept). bare “Albert” (pp.122, 125–126, 146) is Yamada Albert — volume Coverage-notes bullet. verify y1v7: 679 [says] ALL PASS (21 too short/skipped) + 30 non-says ALL PASS; make check OK (R18 0, R19 82/82); gate exit 0; hash `2eca4fc952f66af0ea617cc42cd3bdd3` twice. New tags: none. Next: ch6 pp.152–196.

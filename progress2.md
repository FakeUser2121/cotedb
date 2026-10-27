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

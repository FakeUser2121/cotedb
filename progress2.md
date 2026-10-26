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

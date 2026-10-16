# COTE Character Knowledge Base — Progress

## ACTIVE TASK
Build an evidence-backed knowledge base over 34 COTE LN volumes — **characters + world/locations + exams/systems** (P8/P9 added by user 2026-10-16). **P3 DONE** (13-stage chain 0-diff) · **P4 DONE** (`dossiers/background.md`, 226 sections) · **P5 DONE** (mid ×20 typed folders + main ×7 deep dossiers; authored analysis 69 arc/35 readings/49 relations via `main_analysis.py`, digest-excluded). **P6 DONE** (verbatim integrity, attribution audit + fixes, consistency gate `p6_consistency.py` all clean; quotes 55,672 / 5,798 attributed / 103 reviewed). **P8 DONE** (28 locations, 40 aliases, 4,076 anchored mentions, 14 location claims, world dossiers ×28 md5-stable, gate `p8_consistency.py` clean). **P9 DONE** (15 exams / 41 exam aliases / 1,262 exam mentions · 5 systems / 7 system aliases / 4,507 system mentions · authored prose 15+5 · 22 instances · 20 exam claims + 18 system claims · dossiers exams ×15 + systems ×5 + indexes + master chronology, md5-stable · gate `p9_consistency.py` clean). **P7 site+PDFs+search DONE, LIVE**: 83-page static site (`share/site`, md5-stable, gate `share_check.py` clean: 8,343 links + 808 search records + print + docs sync) · 6 PDFs (277 pages) in `share/site/pdfs` · deterministic ZIP · repo `FakeUser2121/cote-kb` pushed (corpus/db guarded) · **GitHub Pages live: https://fakeuser2121.github.io/cote-kb/**. **P7-8 (PDFs → Google Drive) handed off — user uploads manually (no Drive credentials on this machine).** Working rule: **small steps, verify each**. Full autonomy granted (P8→P9→P7).

---

## FULL PLAN (locked decisions)

### Principles
1. DB (`cote_kb.db`) is sole source of truth; all files are generated views (never hand-edit dossiers)
2. Evidence ≠ interpretation — structured claim model, never flattened
3. Quotes: **complete verbatim capture** in DB (user requirement), organized in views, citable
4. Roster permanently open — stragglers caught during every later phase (straggler net)
5. Completeness measured (verified) vs estimated — never claimed absolute
6. Event-level modeling; timelines derived from events
7. Resumable batches; no pip (stdlib + installed tools + uvx only); PDFs untouched
8. User said: don't read whole PDFs into cards — dense distilled dossiers, no copy-paste dumps
9. Background characters (low importance): ALL in one file `dossiers/background.md` (user decision — rejected outside suggestion to split)
10. Mid characters: typed folders `dossiers/mid/<type>/` (authority|rivals|allies|peers|family|outside)
11. Main characters: one file each in `dossiers/main/`

### Sharing with people (non-agent readers) — locked 2026-10-16
12. Dual audience: **Markdown views = for agent/LLM work**; **share exports = for people** (no agent needed)
13. Share exports (P7): **PDFs** (primary read artifact — identical layout on every device, read in-browser without download) + **multi-page static HTML site** (GitHub Pages; `index.html` + one page per dossier section + `assets/` css/js; no single-file constraint — hosted). Search index embedded as JS constant so the same folder also works opened from disk (file:// blocks fetch()). ZIP = site + PDFs + readme. DOCX rejected (layout reflows per app/font; no pandoc/LibreOffice on this machine)
14. Delivery = **both** (user decision 2026-10-16): (a) **HTML site → GitHub Pages** free hosting link — the link you click, full no-download experience (searchable, PDFs served by the same site; user accepted public exposure); (b) **PDFs → Google Drive** — easy to move around/pass along, readable in-browser without download. `gh` authenticated (FakeUser2121); **repo `cote-kb` created + Pages live 2026-10-16** (`/docs` source); Drive = user's manual upload of the ready deliverables (P7-8 handoff)
15. Git guard: `gdrive_download/`, `text/`, `cote_kb.db`, `search.db` NEVER enter the repo (raw corpus + DB quotes stay private); repo holds `kb/` scripts, PROGRESS.md, `dossiers/`, `share/`
16. Presentation quality bar (user requirement, final part only): **ease of access** — readers find what they need in seconds (nav sidebar, TOC, cross-links, search, deep anchors per character/exam/location) · **visual consistency** — one stylesheet across all pages (uniform typography, tier/type color coding, same header/footer) · **visually appealing** — clean readable layout, not a data dump. Verify with a walkthrough checklist at P7 before publishing

### Pipeline phases
- **P0 Corpus validation + infra** — DONE (see log)
- **P1 Roster discovery** — multi-extractor union E1–E7, normalization, stoplist, classify, recall audit (~100 stratified pages, verified vs estimated coverage), roster v1 → USER REVIEW CHECKPOINT
- **P2 Roster verification + tiering** — stratified manual audits, FP/FN per extractor, targeted re-audits where errors cluster, assign tiers (1 main / 2 mid / 3 bg / 4 one-off / 9 unidentified), background-first order
- **P3 Evidence & dialogue indexing engine** — events, participants, verbatim quotes (speaker attribution + confidence, ambiguous → review queue), claims with full attribution model, mention_stats; run per tier, background first
- **P4 Background dossiers** → single `background.md` (anchored sections); pilot 5 chars, check with user, then scale
- **P5 Mid + main dossiers** — mid in typed folders; main one file each: deep psychology/arc/quote banks, user priority order; every inference links evidence; competing interpretations distinguishable
- **P6 Cross-volume verification (DONE 2026-10-16)** — alias coverage, unmatched entities, speaker-attribution audit, chronology & relationship consistency, source-anchor spot re-verification, "mentioned but unrecorded" sweep
- **P7 Generation & maintenance / share exports** — **DONE 2026-10-16** (Drive = user manual upload, P7-8 handoff): multi-page HTML site (`share/site`, one page per dossier + nav sidebar + per-page TOC + client-side search over 808 section records), 6 print PDFs (chromium headless, 277 pp) shipped inside `share/site/pdfs`, deterministic ZIP, `docs/` Pages copy, gate `share_check.py`; published to GitHub Pages (see PHASE 7). Incremental new volumes / regeneration machinery live here too
- **P8 World/locations layer** (user-added) — DONE 2026-10-16 (see PHASE 8 section): ANHS + all settings: buildings, facilities, campus zones, dorms, exam venues (islands/cruise/etc.), off-site/city locations. Per location: function, layout facts, narrative importance, changes over time, evidence-cited claims (narrator vs character), link to events/characters. Generated as searchable dossiers. Same entity+occurrence+claim pattern as characters.
- **P9 Exams/systems layer** (user-added) — every exam/special exam/system in FULL detail, nothing skipped: rules, point values, conditions, participants, organizers, each instance's chronology + what happened + outcomes + loopholes exploited. Point system (Private Points, Class Points), student numbers, contracting/expulsion mechanics, clubs, student council, any other school system. Evidence-backed; each exam entity links to characters/locations/volumes. Generated dossiers + master chronology.
- P8/P9 entities get tagged during P3 indexing when mentions are spotted (cheap straggler catch); full dedicated passes happen after P5.

### Data model additions for P8/P9
`locations` (loc_id, name, kind, function, notes) · `location_aliases` · `location_claims` (reuse claims pattern) · `exams` (exam_id, name, kind, rules_summary, points, conditions, organizer) · `exam_instances` (each occurrence: vol, chronology, participants, outcome, evidence) · `systems` (point economy, student council, clubs, etc.) · FTS over all. All reference the same anchor model (vol+page+span).

### Extractor design (P1)
- E1 honorific pairs: `X-kun/san/sensei/senpai/chan/sama`
- E2 mid-sentence capitals (after lowercase/punct — excludes sentence-start noise)
- E3 capital pairs both orders (`Honami Ichinose` + `Ichinose Honami`) → surname↔given tables → bare-form re-sweep
- E4 dialogue tags (`"..." said X`, `"X," said Y`, vocatives)
- E5 intro patterns (`X was a...`, `named/called X`)
- E6 nickname suffixes (`-pon` etc.)
- E7 confirmed-name spelling sweeps (after classification)
- Normalization: macron folding (ō→o, ū→u...), hyphen glue, possessives, honorific-strip → merge key
- Stoplist: common English capitalized words, translator watermark "Goldenagato", "Page" headers

### Data model (cote_kb.db, 20 tables)
volumes · characters · aliases · events · event_participants · quotes · claims · relations · status_timeline · interpretations · unknown_entities · mention_stats · coverage · provenance · roster_candidates · (+ FTS + supporting)

**Source anchors on every evidence row:** vol_id · pdf_page · char_start/end offsets into canonical `text/<stem>.txt` · chapter heading when detectable · provenance run_id

**Claim model:** kind (narrator_fact|character_claim|other_reported|inference) · claimant · perspective · corroboration (none|supported|contradicted + refs) · reliability_note · confidence

**Events:** multi-participant scene-level records; character timelines derive from them

### Acceptance criteria P1→P2 gate
Roster v1 presented to user; recall audit on ~100 stratified pages (every vol × start/mid/end); verified coverage on audited strata; estimated coverage via cross-extractor capture-recapture; target high recall with honest reporting of gaps.

---

## PROGRESS LOG

### P0 Corpus validation — DONE (2026-10-16)
- `kb/corpus_check.py` created; validates PDF↔txt page counts vs pdfinfo, page-marker sequences, empty-page scan, writes volumes registry + provenance to `cote_kb.db`
- Initial path bug (ROOT pointed into kb/) — fixed: ROOT = parent of kb/
- utcnow deprecation — fixed
- Near-empty-page check: initially flagged 15 vols; verified these are **illustration/cover pages** (no text layer) — expected for illustrated LNs; downgraded to informational, not problems
- Result: **all 34 volumes validated** (pdf_pages == txt_pages == marker count, seq ok). Total ~8,386 pages. Empty pages are covers/inserts.
- Volumes registry written with chronological order: y0(0.0), y1v1..y1v11, y1v4.5(4.5), y1v7.5(7.5), y1v11.5(11.5), y1v11.75(11.75), y2v1..y2v12, y2v4.5, y2v9.5, y2v9.75, y2v10.25, y2v12.5, y3v1(24.0)

### P0 Infra — DONE (2026-10-16)
- `kb/init_db.py` created; 20-table schema incl. event/claim/quote model, FTS over quotes, roster_candidates working table
- Schema ready in `cote_kb.db`

### P1 Roster discovery — IN PROGRESS
- `kb/roster_mine.py` created (E1–E6 extractors + normalization + stoplist); normalization hardened (curly-apostrophe fold, ou→o, doubled-vowel collapse, honorific/possessive strip) — canonical key: `normalize()`
- User added scope mid-phase: **P8 world/locations + P9 exams/systems** — schema plan noted above; straggler-tagging to start during P3, dedicated passes after P5

#### P1 classify + seed — DONE (2026-10-16)
- `kb/classify.py`: KNOWN_RAW (71 entries, keys via `normalize()`), `GIVEN_AMBIGUOUS` guard {haruka, satoru, shigeru, kyosuke, hitomi}; wipes+rebuilds `characters`/`aliases` each run; E1 auto-shells. 71/71 matched, E1 auto 172
- `kb/import_seed.py`: external seed cross-check `kb/external_seed_wattpad.txt` (161 entries, 151 in corpus) → 99 new chars, 36 re-pointed, 88 shells dropped; 0 missing
- Deterministic pipeline order (all idempotent): `roster_mine → classify → import_seed → review_pass1 → review_pass2 → review_pass3`

#### P1 band reviews — DONE (2026-10-16)
- `kb/review_pass1.py`: 100+ / 10–99 count bands cleared (NEW/ALIAS/UPGRADE/NOISE/UNKNOWN/LOCATION dicts)
- `kb/review_pass2.py`: 3–9 band cleared (~50 new chars: Ijuin Kou/Wataru, Isoyama+Onuki Nagisa, Hagiwara Chihaya, Yoshimoto Kosetsu, Ayase Natsu, Ikari Momoko, Inoue Toa, Toudou Rin, Todo Chikon, Kamogawa Toshizou, Kaminai Tsushi, Miyako, Mikuru …; ~90 aliases incl. family claims + TL variants; `CID_OVERRIDE` {Tokitou Katsumi, Nishimura Ryuko, Hondou Ryoutaro}; `FAMILY_SKIP` {todo, horikita, ishikura, kamogawa}; ~450 noise keys; `merge_albert()`; `UNKNOWN_NOTES` deliberate ambiguities)
- `kb/review_pass3.py`: 1–2 band full-name pair scan (E3 corpus-wide, 1273 pairs). Precision-gated case A (new char) requires: family row exists with count≥2 + family NOT in en_US dict (allowlist) + given NOT in en_US dict + unique family-given pair — calibrated on a hand-labeled 159-pair sample (keeps 9/9 real, rejects verb-phrase/English/outside-world pairs). Also: `SPECIAL_SWAP` (Yamanaka Ikuko TL reversal), `VARIANT_PAIRS` (Horokita Manabu / Rotsukaku Momoe / Fujirika Morofuji → alias claims), case-B canonical-given guard (blocks `Tachibana Kento`→Akane style wrong-attach), unreviewed-only claims (never clobber deliberate `unknown`s), honorific/possessive canonical stripping, hunspell dictionaries bootstrapped to `/tmp/opencode/hdict/` from GNOME flatpak runtime
- Garbage-kill noise keys added after pass3 audit: Isac/Jeet/Kune/Naona/Shiroi/Koibito/Asimov + Deja/Chitanda/Kuroda/Zhuge/Kodo/Ikusei/Rakkan/Ichiba/Futsatsu/Horoporo (outside-world drops, media names, places, system words)

#### P1 normalize fix + straggler hardening — DONE (2026-10-16)
- `normalize()` bug fixed in `roster_mine.py`: honorific strip now runs BEFORE doubled-vowel collapse and rstrips separators — chained/collapsed forms that produced junk keys now merge correctly:
  - `Miichan`/`Miichan's` → **`mi`** (was key `michan` count14) → routes to Wang Mei-Yu (Y1V8 corpus-verified: "a girl named Wang Mei-Yu… Her nickname was Miichan")
  - `Sae-chan-sensei` → **`sae`** (was key `saechan` count8) → Chabashira Sae (students' pet-name "Sae-chan-sensei", Y1V1)
  - Regression-diff over 2852 raw forms: exactly these 2 key changes, both intended; bare names still safe (`Asama`, `Misama` verified)
- `review_pass3.py` additions: **TITLE_NOISE** {sensei (title; kills bad `Yomawari Sensei` char — TL-glitch, 1 mention), thre/thirten (TL artifacts 'Three-''Thirteen' collapse), agatha (Christie)}; **dict-sweep** — unreviewed count≤3 accepted by hunspell → noise (671 keys; `SWEEP_EXCLUDE={"jute"}` protects hand-verified surname); **shell triage** (SHELL_NOISE 12 junk → deleted; SHELL_PAIRS 3 merges; SHELL_VARIANT 12 redirects; SHELL_PROMOTE 43 incl. Hatsukawa Maho Y2V11, Asama, Sasaki, Kimura, Ninomiya Kuranosuke…)
- Ordering fix: `resolve_shells()` moved **before** the pair scan so promoted families case-B in one pass (was: run1+run2 settle); `repoint()` returns rowcount and all shell stats are effect-gated — **second `review_pass3.py` run is a verified total no-op**
- **Protocol: one full pipeline pass suffices; run pass3 a 2nd time only to verify idempotency**

#### P1 recall audit — DONE (2026-10-16)
- `kb/recall_audit.py`: 102 stratified pages (3/vol at 10/50/90% depth, non-empty fallback); per-page extractor-hit coverage; per-key state resolution; single-token straggler scan (position-filtered: skips dialogue-openers/contractions/interjections/sentence-starts, keeps vocatives); capture-recapture (Chao1)
- Results (final run): 481 hits / 102 pages; **192 distinct keys → 86 mapped + 106 noise + 0 unreviewed + 0 unknown**; **straggler NAME? = 0** (0 tokens after filter); Chao1 estimated unseen non-noise keys ~91 (= expected open tail of 1–2-count keys, covered by 380-row unreviewed pile); 2 benign zero-mapped pages (y1v1 p27 junk hit, y2v9.75 TL afterword)
- Gold annotation (10 hand-checked pages, 25 mentions): **24/24 real-name mentions mapped, 1 shell (Himeno)** — 0 extractor misses; (earlier spot list's "Nakano/Kirimichi" absent from corpus — test-list fabrications, not misses)
- Outputs: `/tmp/opencode/audit_strata.txt`, `/tmp/opencode/audit_stragglers.txt`

#### P1 pipeline state (verified 2026-10-16, single-pass + idempotency re-run)
- roster_candidates: **441 character · 1385 noise · 13 unknown · 380 unreviewed** (all count 1–2); **unreviewed≥3 = 0; orphan candidates = 0; shells = 0**
- characters: **261** (tiers: 1×7, 2×19, 3×41, 4×95, NULL×99 seed-no-tier pending P2); name_order: family-given 179, single 37, unknown 45; status: confirmed 148, seed 99, provisional 14
- pass3-created this run: 56 (10 pair-scan real + 3 shell merges + 43 promotions); top mentions: Horikita Suzune 7669, Ayanokouji Kiyotaka 7352, Ryuuen Kakeru 4195, Ichinose Honami 3909, Kushida Kikyou 3308 …
- 13 deliberate unknowns (unchanged, all with reviewer notes): ryuji(36), kyoto(31→P8), pallet(16→P8), koji(12), so(10), satoru(8), ko(6), shigeru(6), kyosuke(6), nagisa(5), todo(4), goro(3), kiyo(3)
- quotes table: 0 rows — **expected** (P3 scope; schema ready, loader not built yet)
- Review scripts claim only `unreviewed`/`unknown` per pass3 rules; aliases table has no unique constraint (dedupe by SELECT)
- **CHECKPOINT: present roster v1 to user now (counts/tiers, 13 unknowns, 380-row tail sample, audit coverage)**

#### P2 roster verification + tiering — DONE (2026-10-16, roster v1 approved by user)
- **Identity investigations resolved (corpus-verified):** Himeno Yuki = 2nd-Yr Class B / Ichinose class (Y2V4.5 OAA 'Second-Year Class B Himeno Yuki', Y2V6 'Himeno-san from Ichinose-san's class'; Y2V12 first-discussion roster header is SWAPPED — same block files undisputed 2-D Sudou/Miyake/Matsushita/Onodera/Nishimura/Ichihashi under 'Class B'; corroborated by Y2V11 MTL header error) · Matsuo = father/butler (Y1V7; Y2V8 suicide mention) vs son Matsuo Eiichirou (Y2V3, Nanase's childhood friend) — DISTINCT, NO merge · Kijima = V0-only Senator Kijima-sensei (politician; no student same-surname in Y1+) · Horikita Tomiko = Y1V3 joke answer ('Tomiko. Horikita Tomiko.' → 'It's Suzune.') — not a person · Kouejin = TL typo of Kouenji (Y1V1 pool race) · re-splits: seed bare 'Onodera' = Y1V8 3rd-Yr Class B instructor, seed bare 'Ishikura' = 3rd-Yr Class B student (Y1V8 Nagumo card game) — both DISTINCT from Onodera Kayano / Ishikura Kayoko (earlier ad-hoc dup-slug merge was WRONG) · Ikari-sensei = Y2V5 faculty (third Ikari, distinct from student Ikari Momoko) · Kiriyama = one char (student-council VP title succession = P5 claims scope)
- **`kb/review_pass2.py` edits:** removed NEW_CHARS 'Horikita Tomiko' + 'Yashima Mariko'; 'Kiryuuin Fuuka' → 'Kiryuin Fuuka' (canonical matches seed → no dup slug); ALIASES ('Mariko' → Yajima Mariko, note = Y1V4 roster TL typo); ('Tomiko' entry removed); ('Fuuka' retarget); Ishikura given-alias note documents the re-split
- **`kb/review_pass3.py` edits:** 'Kouejin' SHELL_PROMOTE → SHELL_VARIANT (koejin → kouenji-rokusuke); Himeno SHELL_PROMOTE canonical → 'Himeno Yuki' with full class-evidence note
- **`kb/review_tier.py` created — runs LAST in pipeline** (`roster_mine → classify → import_seed → review_pass1 → review_pass2 → review_pass3 → review_tier`), standalone, docstring = full decision log. Persists: 7 identity merges (katsuragi-kohei→katsuragi-kouhei, kushida-kikyo→kushida-kikyou, kiryuuin-fuuka→kiryuin-fuuka, yashima-mariko→yajima-mariko, ikari→ikari-momoko, tokinari-tsukishiro→tsukishiro, yoshimoto-kousetsu→yoshimoto-kosetsu) with loser-note preservation into winner; re-split recreations (onodera / ishikura / ikari-sensei: [P2-instr] notes, family aliases, status→confirmed, name_order→single); removals (horikita-tomiko → candidate noise + purge; kouejin → variant alias on kouenji + purge); Himeno id rename himeno→himeno-yuki + canonical upgrade; instr-guarded note rewrites (Kijima P2 verdict, Kayano/Kayoko re-split corrections, Himeno old-note swap); [P2-distinct] Matsuo cross-notes; [P2-collision] candidate notes (bare keys stay claimed to the STUDENTS — P3 volume disambiguation); alias policy: 12 ambiguous given rows removed {haruka, satoru, shigeru, kyosuke, nagisa, ko}×2 + toshizo-on-student-kamogawa + eichiro-on-father-matsuo; alias dedupe MIN(alias_id) per (char_id, normalized); tiers: kouenji→t2 first (1659), NULL band ≥5→t3 / <5→t4, t4 cnt≥10→t3 (27), force ishikura→t3; provenance method='review_tier_p2'
- **2nd recall strata (25/75/95 depth → /tmp/opencode/audit2/):** 102 pages, 471 hits, 76.9% mapped, **straggler NAME?=0**; 6 open keys resolved → alya/budos/inkpetagon = RoyalMTLs credits staff (Illustrator/Editor/Proofreader, Y2V9.75 p17) → noise (persisted as CREDITS_NOISE); 'Miyaki' (Y2V6 Haruka SS) = TL typo of Miyake → variant claim on miyake-akito (persisted as VARIANT_CLAIMS); 'blueocean' (ship café) + 'kkiyotaka' ('K-Kiyotaka' stammer) correctly ABSENT from roster (mining filters — not recall gaps)
- **FP audit:** 72 classified keys sampled with contexts across E1–E6 (12 each) — **0 FP clusters**; every judgment call = a documented P2 collision case behaving as designed
- **Verification:** `review_tier` idempotent (2nd run = all-zero effects); **two full pipeline re-runs each reproduce the exact structural state — 0 diff lines** on digest {characters: char_id/canonical/name_order/tier/mid_type/status · candidates: key/classification/char_id/count · aliases: char/key/form_type} (notes excluded by design)
- **Final P2 state:** characters **253** (t1×7, t2×20, t3×138, t4×88, null=0); candidates **441 character · 1389 noise · 13 unknown · 376 unreviewed** (all count 1–2); aliases **593**; gates: unreviewed≥3=0 · orphans=0 · shells=0 · null-tier=0; 13 deliberate unknowns unchanged (ryuji/kyoto/pallet/koji/so/satoru/kyosuke/shigeru/ko/nagisa/todo/goro/kiyo)

#### P3 step 1 — quote_mine engine (2026-10-16, verified on y1v1)
- `kb/quote_mine.py` created: per-volume verbatim dialogue extraction + speaker attribution. Patterns: A1 `” said Horikita` (verb+name), A2 `” Horikita said` (name+verb), A3 `” I asked` → POV char (POV_MAP y1v1→ayanokouji-kiyotaka); STOP_FIRST guards block `She said` style; name→`normalize()` (imported from roster_mine — keys match P1/P2 exactly)→ aliases lookup; 1 match=resolve, ≥2=ambiguous (NULL, conf 0.2), 0=unresolved (NULL, conf 0); pronoun/no-tag spans stored unattributed (conf 0) — complete capture, honest gaps. Attribution kind stored in `quotes.context` (A1|A2|A3-pov|pronoun|no-attr) for filtering/stats
- Bug caught by verification: purge ran AFTER insert (deleted the fresh rows — `deleted_prev:2153` on first run); fixed to purge-before-loop; idempotency re-verified: rerun deletes 2153 → reinserts 2153, FTS count matches (2153/2153), `MATCH 'Horikita'` = 119 hits
- y1v1 results: 264 pages, **2153 spans** → A2 133 (94 resolved), A3-pov 110 (all resolved), A1 30 (20 resolved), pronoun 108, no-attr 1772; **224 attributed**, eyeballed sample = 0 wrong speakers
- 15 ambiguous alias keys identified (read-only audit): ALL are known/deliberate P2 collisions (ayanokoji-typo father/son, horikita bro/sis, ijuin twins, ikari student/faculty, ishikura, kamogawa, mako, matsuo, minami, onodera, sonoda, susumu, todo, tokito, yuki) — conservative NULL is correct; scene/volume-aware disambiguation = later P3 step
- no-attr 1772 diagnosed (sampled): mix of (a) untagged back-and-forth dialogue, (b) scare-quoted terms (`“Sleeping Strategy”`), (c) pronoun tags — classification + coreference = P3 step 2 backlog

#### P3 step 2a — quoted-span classification (2026-10-16, y1v1 verified)
- `classify_quoted()` in quote_mine: terminal-punct/end-dash (incl. curly-’ guard) → speech; first-person/contractions → speech; interjection openers → speech; pure alpha-phrase ≤30 chars → term; else other. Wired into attribute()'s fallback: `quotes.context` now holds A1|A2|A3-pov|pronoun|speech|term|other (no-attr gone)
- y1v1 final: speech 1760 · A2 133 · A3-pov 110 · pronoun 108 · A1 30 · term 12 · other 0 (2153 total). Calibrated finding: ~98% of unattributed spans are real untagged dialogue; scare-quoted terms ≈0.6%; edge-sample of all 13 term/other rows hand-checked — correct
- Known miss class logged (not yet fixed): tags like `,” said the instructor` (article after verb) fall through to no-attr — candidate A1 extension

#### P3 step 2b — full-corpus quote run (2026-10-16, all 34 vols)
- POV_MAP extended: y1v1–y1v11 + y2v1–y2v12 + y3v1 → ayanokouji-kiyotaka (A3 `” I asked` → 966 resolved); y0 + 8 SS/specials intentionally unmapped → A3-nopov (482) honest NULL
- **SQLite lock bug**: main() held one uncommitted write txn across volumes → iter_pages()' fresh read connection died with `database is locked` after 5 vols (journal_mode=delete); fixed with `db.commit()` after each volume
- **Typography audit** (3 quote styles across corpus): curly `“...”` (33 vols) + straight `"..."` (y3v1 = 3667 quotes, y2v9.75) + guillemets `«...»` (y1v10, y1v11.5, y1v11.75, y2v1, y2v2) — RE_QUOTE now matches all three (`next(g for g in m.groups() if g is not None)`), inner >4000 chars skipped as pairing-disaster guard; y3v1 went 1 → 1762 spans, y1v11.75 0 → 74
- Final corpus state: **55,672 quotes across all 34 vols**, FTS 55672=55672 · attributed **3881** (A1 1638/2015, A2 1277/1617, A3-pov 966/966) · speech 49,221 · pronoun 931 · A3-nopov 482 · term 270 · other 170 · smallest vols y2v9.75=59 (credits), y1v11.75=74, y2v10.25=55 — plausible
- Backlog for P3 step 3: coreference for pronoun tags (931), article-tags (`said the X`), scene-aware disambiguation of the 15 ambiguous keys (46+y1v1, more corpus-wide), untagged-dialogue speaker inference (49k speech rows via dialogue adjacency/scene context)

#### P3 step 3 — attribution deepening (2026-10-16, `kb/quote_attr.py`)
- Pipeline now: `... → review_tier → quote_mine → quote_attr` (quote_mine purges quotes on re-run → quote_attr MUST re-run after it; both idempotent)
- **GENDER VOTES** (corpus-derived, no config): full/given alias occurrence + gendered pronoun within 60 chars → vote; majority (≥4 votes, ≥0.75 ratio) wins → **106/253 chars gender-known**; recomputed every run
- **PRONOUN rows** (931): re-check 120 chars after span_end — strict tag (`he/she/they` + speech-act verb) → backward same-page scan (≤800 chars, cut at page marker) for nearest alias-name with matching voted gender → char_id conf 0.65 (**605 coreferred**); narration-after-quote false tags → context='speech' (**59 reclassed**); **267 honest NULL** (no gendered name match — sampled: correct to abstain)
- **AMBIGUOUS rows** (586, conf 0.2): given-name window evidence → **40 resolved** (conf 0.7; all-horikita-suzune spot-checked ✓); then **DEFAULT_TAG** {horikita → horikita-suzune 0.8} with Manabu-page guard: corpus test showed only **1/524** ambiguous 'Horikita said' tags sit on a page with Manabu-dialogue → **523 applied, 1 skipped** (y1v7.5), 22 non-horikita keys left honest (ishikura/ayanokoji/kamogawa/onodera/…)
- Result: **attributed 3881 → 5049 (9.1%)**; base 2915 + pov 966 + deepened 1168; unattr 50623; idempotent re-run stable (kept 23 / NULL-tag 267 unchanged)
- Verifications: coref random-12 sample ≈11/12 correct-or-plausible; default-rule sample 5/5 correct; remaining-NULL sample correct abstentions. Article tags (`said the X`) skipped as unresolvable without scene info — logged as review-queue material

#### P3 step 4 — untagged-dialogue inference (2026-10-16, `kb/quote_infer.py`)
- Pipeline: `... → quote_mine → quote_attr → quote_infer` (all idempotent; infer only touches context='speech' rows still NULL)
- Yield measured BEFORE coding: T1 action-narration-before 376/49k · T2 both-side bounded (gap<150) 986 · A2-action-after only 149 · prev-quote gap for unattributed: <50 chars = 25.5k (52%) but anchors inside whitespace-runs are rare
- Implemented: **T1 act-pre** (narration right before quote ends `Name <action>.`, unambiguous name) → conf 0.55, **663 assigned** (samples: Naoe-sensei, Sakayanagi, Tsukishiro, Mika ✓) · **T2 run-alt** (whitespace-adjacent quote runs, interior between two DIFFERENT attributed anchors, strict-alternation parity forced) → conf 0.45, **2 assigned** (parity+distinct-anchor is genuinely rare — correct to stay strict) · term-quotes inside runs excluded from fills
- **Deliberate skip logged**: unanchored runs (the rest of the 49k) — speaker identity not derivable without scene anchors; mass low-confidence fills would poison quote banks. Coverage/known-gap goes into dossiers + P6 audit sample
- Result: **attributed 5049 → 5714 (10.3%)**; rerun = zero-effect idempotent ✓

#### P3 step 5 — scene events (2026-10-16, `kb/event_build.py`)
- Pipeline: `... → quote_infer → event_build`. Quotes clustered into scenes (consecutive attributed quotes, inter-quote gap ≤400 chars; page breaks = layout not scene breaks) per the locked model "events are multi-participant scene records"
- Each scene → events row (`<vol>-p<page>-e<n>`, type='dialogue', summary = speaker roll + opening line), participants role='speaker' with conf = mean of that speaker's quote confidences; provenance='quote_scenes'
- Result: **3,019 scene events, 4,120 participants**; full-rebuild idempotency verified (2nd run identical counts); samples: multi-speaker rolls (y1v4-p93: Manabe 5 / Karuizawa 3 / Ibuki 1) correct
- Other event types (action/revelation/status_change) not derivable at scale yet — dialogue scenes are the P3 base; richer types come with claims (P3-6) + P6 sweeps

#### P3 step 6 — claims + mention_stats + coverage + FULL-CHAIN GATE (2026-10-16)
- `kb/mention_build.py`: mention_stats (2997 rows: alias raw_form × vol word-boundary counts; ~78s run) + coverage grid (1789 rows: 'quotes' 640 / **'occurrences' 1149 = the P4/P6 gap queue** — char present in vol but no attributed quote). Full-rebuild idempotent
- `kb/claim_mine.py`: pattern claims `<Name> is|was a|an|the <pred>` — guards: length-preserving newline flatten (hard-wrap was cutting sentences at line ends), quote-interior exclusion via span lookup, sentence-start boundary (period/quote/page-marker only — killed mid-clause starts), watermark/URL filter (Goldenagato/mp4directs), kind split narrator_fact vs character_claim (first-person → claimant=vol POV). Marker `reliability_note='auto:claim_mine-v1'` → DELETE+rebuild, hand-authored claims untouched. Result: **96 claims** (231→96 after quality guards; samples verified clean), conf 0.6 starter set, P5 authors refine per char
- **Quote/claim id fix**: partial-purge reinserts were escalating autoincrement rowids every run (id churn, not content drift — found via content-keyed re-diff). Now explicit deterministic ids: `quote_id = (vol_chrono_idx+1)*1e6 + n`, same scheme for claim_id → citations stable across runs
- **FULL-CHAIN GATE PASSED**: snapshot (chars/candidates/aliases/quotes+ids/events/participants/mentions/coverage/claims+ids = 70,758 lines) → all **13 stages** re-run (`roster_mine → classify → import_seed → review_pass1 → review_pass2 → review_pass3 → review_tier → quote_mine → quote_attr → quote_infer → event_build → mention_build → claim_mine`) → **diff = 0 lines** (a pre-fix replay also showed 111k-line id churn only; content was already 0-drift)
- **P3 final state**: 55,672 quotes · **5,714 attributed (10.3%)** (A1 1952 / A2 1526 / A3-pov 966 / act-pre 663 / pronoun 605 / run-alt 2) · 3,019 scene events · 4,120 participants · 96 starter claims · 1789 coverage rows · roster gates: unreviewed≥3 = 0
- P3 deliberately NOT claimed: untagged-run speakers (49k, honest NULL), article tags, richer event types, claims beyond the pattern starter — all logged for P6/P5

#### P4 — background dossiers (2026-10-16) DONE
- `kb/build_background.py` → `dossiers/background.md`: **226 sections** (all tier-3 + tier-4), deterministic (byte-identical rerun), 226/226 TOC anchors resolve, regenerated from DB (never hand-edited)
- Section design: stats line (`tier · mentions · quoted lines · scenes`) → aliases → footprint → gap queue / mentions → notes (generic "KNOWN curated" filtered out) → claims (chrono order) → representative quotes (≤6, evenly spread across the char's volume range, each with `vol p.N` anchor)
- **Thin-char handling** (152 sections with no attributed dialogue): top-vols-by-count `Mentions:` footprint + up to 2 verbatim `Mention evidence` windows (`…70 chars left, +130 right…`, `vol p.N`) — one batched corpus pass for all thin chars (37s total run); every one of the 226 sections now carries evidence
- Evidence patterns tolerate all corpus spellings: macron twins (`Onuki`/`Ōnuki`) + ou~ō swaps (`Kouenji`/`Kōenji`) via char-class regex built per alias
- **mention_build fix (data correctness)**: raw-form matching missed macron corpus forms → now counts canon both sides (macron fold + ou→o, deduped); impact: `Koenji` 1,616 mentions surfaced (was ~0), `Ōnuki` found in y2v12; mention_stats 2997→**3278** rows, coverage 1789→**1877** (occurrences 1224 / quotes 653), idempotent (2nd run no-op). Full-chain digest re-baselined implicitly — rerun gate at next pipeline-affecting change

#### P5a — mid dossiers (2026-10-16) DONE
- `kb/assign_mid_type.py`: curated routing table for all 20 tier-2 chars → `characters.mid_type` (authority 4 · rivals 7 · allies 3 · peers 3 · family 2 · outside 1); idempotent (2nd pass 0), asserts table↔tier-2 sync; **new pipeline stage after review_tier — 14-stage chain replay = 0-diff** (protocol line updated)
- `kb/build_mid_dossiers.py` → `dossiers/mid/<type>/<char_id>.md` ×20 + `dossiers/mid/index.md`: Identity (char_id/aliases/notes) · Footprint (spoken-in, gap queue, top mentions, per-vol arc timeline, thin-char evidence) · **Recurring scene partners** (co-participant counts; 16/20 have them — 4 are solo-speaker-only) · Claims (≤8 chrono) · **Quote bank ≤14** spread across volume range; deterministic (20/20 md5-stable rerun)
- Alias→mention totals switched to canonical-token lookup in both builders (raw_form join would have undercounted ou/macron names after the mention_build canon fix)

#### P5b — main dossiers + authored analysis (2026-10-16) DONE
- `kb/build_main_dossiers.py` → `dossiers/main/<char_id>.md` ×7 + `index.md`: Identity · Footprint · **Arc** (status_timeline) · **Psychology & competing readings** (interpretations, confidence-sorted) · **Relationships** (relations w/ span rendering `[from y1v4]`) · scene partners · claims (≤10) · **Quote bank** (≤4/vol, ≤60, grouped); `--pack CHAR` mode dumps authoring evidence packs
- **Authored-content model**: all prose lives in `kb/main_analysis.py` ANALYSIS dict → `apply()` replace-per-char into `status_timeline` / `interpretations` / `relations` — the 3 tables excluded from the structural digest, so authored rows never dirty the 0-diff gate; dossiers stay pure generated views (never hand-edit md)
- Authored coverage (per-char packs read → author → apply → build → review): **69 arc entries · 35 competing readings · 49 relations** across all 7 mains (ayano 11/5/9, horikita 10/5/8, kushida 8/5/6, ryuuen 9/5/8, ichinose 8/5/6, sakayanagi 11/5/6, karuizawa 12/6/6)
- Gates: 8/8 md5-stable rerun · 0 unresolved evidence refs (all `vol p.N` match quotes/claims pdf_page) · 0 evidence-less sections; `rel_type` values kept ASCII hyphenated tokens; all relation char_b ids verified against characters
- **P6 flag list** (carry to verification): (a) y1v5 p.178 "brother admiration" line attributed to ayano but reads Horikita — do not cite until checked; (b) y1v4 p.17 claim char_id=horikita-suzune though claimant is Ayanokouji-narrator; (c) Sakayanagi y3v1 presence vs withdrawal (mentions exist — check she's referenced, not present); (d) class-letter instability across MTL groups in y2v12.5/y3v1 (RoyalMTLs vs LegacyEMTLs) — dossiers avoid class letters for y3 by design

---

## PHASE 6 — cross-volume verification (2026-10-16) — DONE
- **P6-1 all 4 flags resolved**: (a) 7001463 brother-monologue → `horikita-suzune`; (b) y1v4 claim non-bug (Ayanokouji-narrator voicing Horikita's logic — kept, perspectivized); (c) Sakayanagi y3v1 = phone-only reference, not present (0 occurrence rows); (d) class letters by design
- **P6-2 PASS**: 55,672/55,672 quotes verbatim anchor integrity (span→page slice reproduces text after normalize; 0 corruption)
- **P6-3 attribution audit — 4 method classes**: (a) post-anchored narration tags (`…," Name said`, ≤80 chars after span) → 1,142 matched, **0 contradictions**; (b) pre-anchored (`Name said, "…"`, ≤90 before span) → 9 NULL quotes resolvable; (c) pronoun tags (`he/she said` vs `quote_attr.gender_votes` — values **lowercase** `m`/`f`) → 573 checked, **0 mismatches**; (d) self-name/given-name suspects → 15, 6 legitimate in-character self-refs; vocative-start class → fixes. **Residual class: rapid dialogue chains** (no narration anchors within window) — needs scene-level adjudication, quantified in P6-5 backlog
- **P6-4 fixes applied** (persisted in `kb/p6_review.py`, guards on raw-text fragment): `AUDIT_FIXES` 17 manual · `AUDIT_NARRATION` 86 (54 single-tag + multi-candidate adjudications incl. **y2v1 p.94 Ryūen–Hōsen 5-quote scene**: 17000296→housen, 17000297→ryuuen, 17000298→ishizaki (stammer/vocative continuity), 17000300→housen, 17000301→ryuuen; **17000299 left NULL = genuinely ambiguous**) · `AUDIT_CONFIRMED` 8 · 19 stale coverage pairs. Fragment guard requires substring of RAW text — fragments spanning `\n` rejected (3 shortened, e.g. `'but just remember this.'`)
- **P6-5**: `unknown_entities` = **0 rows** (nothing to review); **`mention_build.canon()` bug fixed** — missing `re.sub(r'([aeiou])\1', …)` vowel collapse meant `Ryūen`/`Fūka` macron forms silently dropped coverage in RoyalMTL-style volumes (canon is single source of truth — all 3 dossier builders import it); shared-alias inflation documented (bare `Horikita`/`Ayanokouji` aliases credit father/sibling rows → gap ranking uses char-exclusive tokens); rapid-chain backlog (own_attributed=0, 100s NULL quotes on their mention pages): ryuuen y2v1/y2v10, kouenji y2v4, karuizawa y2v9.5, hirata y1v9
- **P6-6 PASS** — new gate `kb/p6_consistency.py` (read-only, exit 1 on violation): status_timeline unique (char,vol) + per-char chrono non-decreasing + evidence refs resolve to real quote/claim pages · relations chars-exist + ASCII `rel_type` + `valid_from ≤ valid_to` + no evidence predating valid_from + refs resolvable · interpretations char/confidence∈(0,1]/refs · events vol/span/confidence — **span semantics: `span_start` inside own pdf_page, `span_end` on some page ≥ pdf_page of same volume** (event_build clusters volume-wide, GAP_MAX=400, page breaks are layout; first gate version wrongly required whole scene inside start page → 251 false positives, gate fixed not data) · quotes attributed → char exists + confidence set. **All clean, exit 0**
- **Derived-refresh chain**: `p6_review.py` now runs `event_build → mention_build → claim_mine` via subprocess unconditionally after fixes (all full-rebuild idempotent `DELETE+INSERT`); run1 = 14 fixes + refresh, run2 = **0 fixes + identical refresh outputs** — idempotent; script exits 0 so `&&` chains survive (fixed prior `sys.exit(apply())` bug)
- **Post-fix baselines**: quotes 55,672 (**5,798 attributed** / 49,874 NULL, **103 reviewed**) · coverage 1,883 (occurrences 1,210 / quotes 673 — net +2 flipped from new attributions & canon fix, total constant) · events **3,065 scenes / 4,177 participants** · claims 96 (top: kushida 7, hirata 6, ike/karuizawa/ryuuen 5) · unknown_entities 0
- Dossiers rebuilt after all fixes: **30/30 md5-stable** over 2 consecutive rebuilds (`/tmp/opencode/p6c.md5`); mid-bank first-4-per-volume policy unchanged (moved quotes outside banks by design)

---

## PHASE 8 — world/locations layer (2026-10-16) — DONE
- **P8-1 schema** `kb/p8_init.py`: `locations` (loc_id, name, kind, function, notes, first/last_vol) · `location_aliases` · `location_mentions` (vol, pdf_page, span_start/end, provenance) · `location_claims` (claims pattern + loc_id) · `locations_fts` (FTS5 content-storing, DROP+recreate each run; shared `FTS_REBUILD` = DELETE+INSERT); run twice, exit 0
- **P8-2 discovery + import**: `kb/p8_mine.py` (SEED/HEADS/NAMED extractors + shared `form_pattern()` macron-class matcher; report `/tmp/opencode/p8_mine_report.txt`) → corpus context probes → `kb/p8_import.py`: **28 locations / 40 aliases**, gate = every curated form ≥1 corpus hit (all pass), idempotent; kinds: campus-building 14, campus-zone 3, city 3, dorm 1, exam-venue 4, off-site 3; island = "Uninhabited Island" (294) w/ MTL drift alias "deserted island" (73); Keyaki Mall 309 · **exclusion decisions persisted in import docstring**: kyoto/okinawa (ballot-only), hospital/clinic generic, waiting-room y0, maid-cafe concept, main-building context-dependent, dining-hall ambiguous, 0-hit seed guesses, camp generic, generic interiors, sapporo site details
- **P8-3 mentions** `kb/p8_mentions.py`: **4,076 anchored mentions**, combined longest-form-first alternation + per-loc containment overlap dedupe (0 removed), footprint first/last_vol derived from rows, run twice **identical**, 0 orphans; LSP fix (lastgroup None guard)
- **P8-4 authored analysis** `kb/location_analysis.py`: `LOCATIONS` dict **28 entries all authored** (function + notes: layout, narrative importance, changes over time) · `CLAIMS: list[Claim]` **14 entries** · refs gate (every ref a real page; ≥1 ref must carry a mention) · `evidence_for` auto-slices page-local ±80 chars around first mention (fixed absolute/local mix + empty guard) · apply() + FTS refresh; verified 14/14 non-empty verbatim evidence, idempotent; prose rows digest-excluded like main_analysis
- **P8-5 world dossiers** `kb/build_world_dossiers.py` → `dossiers/world/<loc_id>.md` ×28 + `index.md`: Function · Notes · Footprint (by-vol) · scene partners via **page-level co-paged join** to events (span-overlap gave only 9 scenes vs 92/273/75 page-level for island/classroom/keyaki) · claims w/ verbatim evidence · anchors; 2 consecutive rebuilds **md5-identical (0 fails)**
- **P8-6 PASS** — gate `kb/p8_consistency.py` (read-only, exit 1 on violation): locations kind/authored/footprint-vs-mentions · aliases global form uniqueness + orphan/ftype · mention vol/page/**absolute span bounds** + provenance · claims kind/conf/refs real pages + ≥1 mention ref + **evidence verbatim against the claim's own anchor page only**. First run mass-flagged: gate compared absolute spans to page-local `len(text)` and checked evidence against every ref → **gate fixed, not data** (same bug class as p6 events check); all clean, exit 0
- **Run order**: `p8_init → p8_import → p8_mentions → location_analysis → build_world_dossiers` (p8_import clears location_mentions so p8_mentions must re-run after it; location_analysis auto-runs FTS refresh; p8 gates are read-only)

---

## PHASE 9 — exams/systems layer (2026-10-16) — DONE
- **P9-1 discovery** `kb/p9_mine.py` → report `/tmp/opencode/p9_mine_report.txt`: candidate exam/system names harvested from corpora + curated seeds; evidence packs per entity in `/tmp/opencode/p9_packs/` (19 packs read during authoring)
- **P9-2 schema** `kb/p9_init.py`: `exams` (exam_id, name, kind, rules_summary/points/conditions/organizer/notes, first/last_vol) · `exam_aliases` · `exam_mentions` · `exam_instances` (seq, chronology, participants, outcome, refs JSON, evidence, confidence) · `exam_claims` · `systems` (sys_id, name, kind, function, notes) · `system_aliases` · `system_mentions` · `system_claims` · `exams_fts`/`systems_fts` (shared `FTS_REBUILD`); kinds written|special|event|entrance|other · points|governance|activity|discipline|admissions|other; run twice, exit 0
- **P9-3 import** `kb/p9_import.py`: **15 exams / 41 exam aliases / 5 systems / 7 system aliases**, gate = every curated form ≥1 corpus hit (all pass). Form revisions applied this session: cruise-ship-exam += `zodiac test`(4) `zodiac game`(1); mixed-training-camp += `mixed camp`(3); school-festival += `cultural festival`(82); NEW entity **`coop-written-head-to-head`** "Cooperative Comprehensive Written Exam" — resolved the open **y2v9 mystery exam** (official bracket y2v9 p.13: 100 cooperative questions, ≥2/≤5 per student, 10 min turns, OAA-weighted A=1..E=5, time bonuses +10/hr); exclusion/curation decisions persisted in docstring (zodiac not its own entity, provisional Class Vote stays class-poll, etc.)
- **P9-4 mentions** `kb/p9_mentions.py`: **1,262 exam + 4,507 system mentions** (dedup 0), footprint first/last_vol derived, run twice **identical**, 0 orphans; entrance-exam has 29 mentions / 12 vols (0 instances — prose only)
- **P9-5 authored analysis** `kb/p9_analysis.py`: `EXAMS_PROSE` ×15 (rules/points/conditions/organizer/notes) + `SYSTEMS_PROSE` ×5 (function/notes) · `INSTANCES` ×22 (every planned ref pre-verified as a real mention page; ids `(exam_index+1)*100+seq`) · `EXAM_CLAIMS` ×20 (ids `exam_index*100+n`) · `SYSTEM_CLAIMS` ×18 (`sys_index*100+n`); **stricter refs gate than P8 — ALL refs must carry an entity mention** (fail-before-write) + evidence auto-derived as ±80 page-local slice around first mention on refs[0]; verified **60/60 evidence verbatim** against anchor pages, idempotent. Fact corrections made while authoring (probes beat memory): y1v10 p.315 lists three **expulsions** (Totsuka/Yamauchi/Manabe) not "elected students"; y2v8 finals = 1st +50 / 2nd +25 / 3rd −25 / 4th −50, cutoff average 39; y1v6 p.33 "no one has to drop out … this time"; y2v5 p.30 decay rule is Ayanokōji narration (claimant narrator, not Chabashira); 300 CP Kōenji-island (y2v5 p.187/p.114) vs 350 CP unanimous stake (y2v5 p.187)
- **P9-6 dossiers** `kb/build_exam_dossiers.py` → `dossiers/exams/<exam_id>.md` ×15 (Rules · Points · Conditions · Organizer · Notes · Footprint · **Runs** per instance w/ verbatim evidence · Claims w/ evidence+reliability · anchors) + `index.md` + **`chronology.md` master timeline (22 runs, volumes.chrono_order then pdf_page)** · `dossiers/systems/<sys_id>.md` ×5 + `index.md`; 2 consecutive rebuilds **md5-identical**
- **P9-7 PASS** — gate `kb/p9_consistency.py` (read-only): entity kinds/authored fields/footprint-vs-mentions min-max · alias orphan + global form uniqueness + form_type in {full, short, variant, epithet, alias} · mention **page-local span bounds** + provenance · instances/claims: confidence, claimant NULL/'narrator'/existing char, **every ref anchored to the entity**, evidence verbatim at anchor, anchor == first ref · fts row counts · dossier files present. **First run all clean, exit 0**
- **Run order**: `p9_init → p9_import → p9_mentions → p9_analysis → build_exam_dossiers`, then gate `p9_consistency.py` (p9_import clears exam/system mentions so p9_mentions must re-run after it; p9_analysis auto-runs FTS rebuild + DELETE/INSERT instances & claims; gates read-only)

---

## PHASE 7 — share exports (2026-10-16) — DONE
- **P7-1 structure scan**: 82 md files / 440 KB; markdown subset = ATX h1–h3 (890), bullets (3,398; indents 0/2), bold, code, links (302: in-page `#` Contents in background.md + relative `.md` in indexes); no italics/fences/tables/blockquotes; slug rule verified GitHub-style incl. authored anchors (`wang-mei-yu`), no dup h2 slugs
- **P7-2 renderer** `kb/share_render.py` (pure): `slug()` · `inline()` (escape → link → code → bold) · `render()` → (html, headings) · `render_list()` (2-level, sub-`<ul>` inside `<li>` = valid HTML) · `rewrite_links()` (`.md`→`.html`); **lazy continuation**: lines abutting a bullet join it (CommonMark) — fixes multi-line verbatim quotes escaping `<li>` (md stays byte-true)
- **P7-3 site** `kb/build_share_site.py`: 83 pages = 82 dossiers + home, layout preserved (`mid/peers/x.html` etc.), depth-relative roots; nav sidebar from authored `dossiers/*/index.md` link order (details/summary, active section open, type badges), per-page TOC (h2/h3), kicker tags, footer; home = hero stats (253 chars/28 locations/15 exams/5 systems/55,672 quotes/3,065 scenes) + section cards + **Downloads (PDF) card**; `--md5` / `--zip` (deterministic zip → `share/cote-kb-share.zip`, md5-stable) / `--docs` (site → `docs/` for Pages); 2 rebuilds md5-identical
- **P7 search**: `assets/search-index.js` = 808 per-heading records `{u,t,s,x}` as a JS constant (file:// safe) + `assets/search.js` (scored AND terms, ≤12 results, mark-highlighted snippets, `/` focus, ↑↓/Enter, Esc, `#q=` deep links); 12/12 node tests pass (DOM stub); live screenshot verified
- **P7-4 PDFs**: `share/print/*.html` (cover + TOC + page-broken entities, links rebased to `../site/`) → chromium headless `--print-to-pdf`: **background 85 / main 55 / mid 42 / world 42 / exams 40 / systems 13 = 277 pages**, shipped at `share/site/pdfs/`
- **P7-5 gate** `kb/share_check.py` (read-only): 83 pages + 8,343 href/src all resolve · every `#anchor` exists · search-index JSON valid, all 808 record URLs+anchors resolve · print docs 308 links · 6 PDFs readable (pdfinfo) · `docs/` md5 == `share/site` md5 — **all clean, exit 0**. Walkthrough screenshots (chromium headless): home, kouenji, class-poll, background, chronology, exams index, ayanokouji, world index, search dropdown
- **P7-6 publish**: `.gitignore` guards `text/`, `gdrive_download/`, `cote_kb.db`, `search.db`; 229 files committed; **`gh repo create FakeUser2121/cote-kb` (public) + push** (remote switched ssh→https, `gh auth setup-git`); `docs/` committed; **Pages enabled from `/docs`, status `built`**; live-verified: title/stats/search-index/deep page/PDF content-type/anchors — **https://fakeuser2121.github.io/cote-kb/**
- **P7-8 Drive upload — HANDED OFF (user decision 2026-10-16: manual upload)**: this machine has no Google credentials/tooling (checked binaries, env, MCP, python pkgs, sudo); user will drop the deliverables into Drive themselves. Files: `share/site/pdfs/{background,main,mid,world,exams,systems}.pdf` (277 pp) + `share/cote-kb-share.zip` (3,030 KB) — also downloadable from the live site (Downloads card) and the GitHub repo. P7 complete once user uploads.
- **Run order**: `python3 kb/build_share_site.py` (site + print docs) → chromium loop over `share/print/*.html` → `kb/build_share_site.py --zip` + `--docs` → gate `kb/share_check.py` (read-only, exit 0)

---

## FILE MAP
```
cote/
├── gdrive_download/     34 PDFs (untouched)
├── text/                34 .txt with "--- page N ---" markers
├── kb/
│   ├── corpus_check.py       P0 validator (DONE)
│   ├── init_db.py            P0 schema (DONE)
│   ├── roster_mine.py        P1 extractors E1–E6 + normalization (DONE)
│   ├── classify.py           P1 KNOWN_RAW 71 + GIVEN_AMBIGUOUS + E1 shells (DONE)
│   ├── import_seed.py        P1 external seed importer (DONE)
│   ├── check_seed.py         P1 seed cross-check (DONE)
│   ├── review_pass1.py       P1 100+/10–99 band (DONE)
│   ├── review_pass2.py       P1 3–9 band (DONE)
│   ├── review_pass3.py       P1 1–2 band pair scan + sweep + shell triage (DONE)
│   ├── review_tier.py        P2 identity merges/re-splits/alias policy/tier bands (DONE)
│   ├── quote_mine.py         P3 verbatim dialogue + speaker attribution (DONE, all 34 vols)
│   ├── quote_attr.py         P3 pronoun coref + gender votes + ambig defaults (DONE)
│   ├── quote_infer.py        P3 untagged-dialogue T1/T2 inference (DONE)
│   ├── event_build.py        P3 scene-level dialogue events (DONE, 3065 events post-P6)
│   ├── mention_build.py      P3 mention_stats + coverage grid (DONE)
│   ├── claim_mine.py         P3 pattern claims starter set (DONE, 96 claims)
│   ├── build_background.py   P4 background dossier view (DONE, 226 sections)
│   ├── assign_mid_type.py    P5 t2 routing table → characters.mid_type (DONE, 20 chars)
│   ├── build_mid_dossiers.py P5 mid dossiers + --index (DONE, 20 + index)
│   ├── build_main_dossiers.py P5 main dossiers + --pack evidence packs (DONE, 7 + index)
│   ├── main_analysis.py      P5 authored main-char prose → apply() (DONE, 7 chars)
│   ├── p6_review.py          P6 audit fixes + derived refresh chain (DONE, exits 0)
│   ├── p6_consistency.py     P6-6 chronology/relations/refs gate (DONE, exit 0)
│   ├── p8_init.py            P8 locations schema + FTS_REBUILD (DONE)
│   ├── p8_mine.py            P8 discovery extractors + form_pattern() (DONE)
│   ├── p8_import.py          P8 28 locations / 40 aliases + exclusion log (DONE)
│   ├── p8_mentions.py        P8 anchored occurrence rebuild (DONE, 4076)
│   ├── location_analysis.py  P8 authored location prose + 14 claims → apply() (DONE)
│   ├── build_world_dossiers.py P8 world dossiers (DONE, 28 + index)
│   ├── p8_consistency.py     P8 locations/mentions/claims gate (DONE, exit 0)
│   ├── p9_init.py            P9 exams/systems schema + FTS_REBUILD (DONE)
│   ├── p9_mine.py            P9 discovery report (DONE)
│   ├── p9_import.py          P9 15 exams/41 aliases + 5 systems/7 aliases (DONE)
│   ├── p9_mentions.py        P9 anchored mentions rebuild (DONE, 1262 + 4507)
│   ├── p9_analysis.py        P9 prose 15+5 + 22 instances + 38 claims → apply() (DONE)
│   ├── build_exam_dossiers.py P9 exam/system dossiers (DONE, 15 + 5 + index + chronology)
│   ├── p9_consistency.py     P9 exams/systems gate (DONE, exit 0)
│   ├── share_render.py        P7 md→HTML renderer + slugs (DONE)
│   ├── build_share_site.py    P7 site/print/zip/docs builder (DONE, --md5/--zip/--docs)
│   ├── share_check.py         P7 share gate: links/anchors/index/pdf/docs sync (DONE, exit 0)
│   └── recall_audit.py       P1 stratified recall audit + straggler scan (DONE)
├── cote_kb.db           evidence DB (source of truth)
├── search.py            FTS keyword search over text/
├── rebuild_index.sh     rebuilds text/ + search.db
├── search.db            text-search index (separate from KB)
├── dossiers/           generated views (background.md; mid/<type>/ ×20; main/ ×7; world/ ×28; exams/ ×15 + index + chronology; systems/ ×5 + index — all DONE)
├── share/
│   ├── site/             83-page site + assets + pdfs/ ×6 + README (source of truth)
│   ├── print/            6 PDF sources (cover + TOC + page breaks)
│   └── cote-kb-share.zip deterministic site+pdfs bundle (md5-stable)
├── docs/                GitHub Pages copy of share/site (= md5)
├── .gitignore           guards text/ gdrive_download/ *.db
├── PROGRESS.md          this file
```

## KEY REMINDERS FOR RESUMPTION
- **Working style (user rule): small steps — one change/step at a time, verify it, then the next. No batch edits.**
- Corpus facts: 34 vols, ~8386 pages, page markers = PDF page index (no printed page numbers — Calibre ebooks)
- Name variants confirmed: Ayanokouji/Ayanokōji (macrons), Ryuuen/Ryūen, Sudou/Sudō; noise: Goldenagato (TL watermark, ~4096 hits), "Page", "Class", "English", "Japan", "April", I'm/I'll etc.
- Honorific-pair mining already proved: 389 distinct pairs; mid-sentence capitals: 2901 raw tokens; mid-band real names found only by E2: Kinoshita, Kaneda, Hamaguchi, Shiraishi, Sanada, Kijima, Machida, Shiranami, Miyabi, Kitou, Ishigami, Kiyopon (nickname), Yousuke/Honami (given-names-only)
- Straggler net is a USER REQUIREMENT: roster stays open; mention_stats gap detection; unmapped tokens flagged during indexing; dossier-writing discoveries back-filled
- Quote completeness is a USER REQUIREMENT: every dialogue line verbatim into quotes table; attribution confidence; ambiguous → review queue
- **Scope expanded 2026-10-16**: after characters, build P8 (ANHS world/locations map) and P9 (all exams/systems in FULL detail) — see FULL PLAN
- User checkpoint after roster v1 — do NOT proceed to P2/P3 dossiers without user review
- Pipeline protocol: `roster_mine → classify → import_seed → review_pass1 → review_pass2 → review_pass3 → review_tier → assign_mid_type → quote_mine → quote_attr → quote_infer → event_build → mention_build → claim_mine` (all idempotent; one pass settles; 2nd run must be no-op; review_tier = P2 persistence, runs last of P2; assign_mid_type = P5 routing table, tier-2 only; quote_mine purges quotes so EVERYTHING after it must re-run). **Post-protocol**: `kb/main_analysis.py` (apply authored rows — after claim_mine only, since its anchors resolve against quotes/claims; digest-excluded tables) then `kb/p6_review.py` (audit fixes → unconditionally refreshes `event_build → mention_build → claim_mine` via subprocess, exits 0) + `kb/p6_consistency.py` gate. Full-chain replay digest must stay 0-diff on any change (last: 14-stage, 0-diff incl. mid_type). `normalize()` strips honorifics BEFORE vowel collapse (2026-10-16 fix) — never re-introduce collapse-first ordering. **`mention_build.canon()` must keep the doubled-vowel collapse** (P6 fix — mirrors normalize, else macron forms silently drop coverage). **P8 run order**: `p8_init → p8_import → p8_mentions → location_analysis → build_world_dossiers`, then gates `p6_consistency.py` + `p8_consistency.py` (both read-only, exit 0). **P9 run order**: `p9_init → p9_import → p9_mentions → p9_analysis → build_exam_dossiers`, then gate `p9_consistency.py` (read-only, exit 0). **P7 run order**: `kb/build_share_site.py` → chromium `share/print/*.html` → `build_share_site.py --zip --docs` → gate `kb/share_check.py` (read-only, exit 0; docs/ must stay md5-equal to share/site)
- P2 structural-digest method: snapshot chars/candidates/aliases (no notes) → full pipeline re-run → diff must be 0 lines — reuse for any future schema/pipeline change
- Sharing (locked): Drive link-share + GitHub Pages; outputs = PDF (chromium headless) + single-file searchable HTML + ZIP; corpus/text/DB excluded from git forever

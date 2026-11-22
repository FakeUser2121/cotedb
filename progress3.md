# PROGRESS 3 — Site architecture rebuild (reader-facing IA, design system)

Purpose of this file: log **every turn** of the website work. progress2.md stays
the walk/extraction log; this file is only about making the site good-looking,
organized and intuitive. Rule from the user: architecture first — content
volume is worthless inside bad bones. No subagents for this work.

## Why this pass exists
The old site (v2, commit c09b0fb) was organized by what the database knows, not
by what a reader asks. Measured before rebuilding:
- 74 cross-section links spread over 70 pages ≈ one outbound link per page:
  content siloed by *type*, so "what happens in Volume 5" had no home.
- Internal agent taxonomy leaked into public nav: "Main / Mid / Background",
  "dossier", "walk", "checkpoint", char_id lines, `cote_kb.db` notes.
- The locked plan (sec. 6) requires a Story axis, a Topics axis, reader-intent doors
  and an Appendix. None existed — there was a `vol1/` bolt-on instead of a
  Year 1 → Year 3 spine.
- No spoiler control, no citation chips (both locked requirements).
- 226 minor characters rendered as one 225 KB page.

## Target architecture (spec = kb/site_arch.py, single source of truth)
Top-level sections, in nav order, all reader-facing names:
1. **People** — every named character (`people/`)
2. **Story** — chronological spine, year hubs → volume pages (`story/`,
   `story/v/<vol>/`)
3. **Exams & School** — rules, point maths, every exam run (`school/`)
4. **World & Places** (`world/`)
5. **Topics** — answers to the questions people actually ask (`topics/`)
6. **Start here** — three reader doors: writer / number-cruncher / rusty
   (`guides/`)
7. **Appendix** — citations, coverage, downloads (`appendix/`)

Rules the spec enforces: volume ids (`y1v2`, `y0`) are machine tokens only, ever
shown inside a citation chip; tier names become Principal / Recurring / Minor;
group keys become human labels; names get macron-fixed through one table.

## Module map (new build pipeline)
- `kb/site_arch.py` — the IA spec: sections, labels, volume/name/label helpers,
  citation regexes. Renders nothing.
- `kb/site_data.py` — curated records read from cote_kb.db + ledgers (people,
  relations, exam instances, arcs, claims), as plain dicts.
- `kb/site_shell.py` — page template + design system output: masthead, primary
  tabs, section-scoped sidebar, breadcrumbs, citation chips, spoiler toggle,
  search box, footer.
- `kb/site_sections.py` — per-section page builders (people roster + filters,
  A–Z, story/year/volume hubs, exams, systems, places, dominant_vol,
  section_scope).
- `kb/site_topics.py` — topics pages, the three reader doors, appendix, and the
  volume documents (guides + transcripts rendered from drafts/ into
  story/v/<vol>/).
- `kb/share_render.py` — markdown → HTML (extended for the new corpus subset).
- `kb/build_share_site.py` — orchestrator: ctx (stats, vols, char_by_id, lookup,
  pathmap, page factory, scope), then writes pages, search index, PDFs.

## Turn log (append one block per turn)
### 2026-10-26 20:2x — design system + spec + builders written
- Wrote `site_arch.py` (IA spec above), `site_data.py`, `site_shell.py`,
  `site_topics.py`; extended `site_sections.py`, `share_render.py`,
  `build_share_site.py`.
- Screenshots of the OLD site captured in `_sitecheck/` (home.png, ak.png) to
  ground the visual critique before replacing anything.

### 2026-10-26 20:4x — first clean-build attempt crashed
- `build_share_site.py` wiped `share/site/` then died in `TOP.build_vol_docs`.
  Two missing names in `site_topics.py`: `dominant_vol`, `section_scope`
  (both live in `site_sections.py`, were not in the import tuple). Fixed both
  imports. Build not yet green — next turn: full build + link gate.
- Note: uncommitted y1v2 ledger writes exist in `ledgers/` from the walk
  (another session); this pass must not touch ledgers or run git commits.

### 2026-10-26 20:4x–20:5x — build driven to green, link gate rebuilt
- Third crash fixed: `site_topics.py` called `finditer(...)[:4]` (iterator is
  not subscriptable) in three topic builders → wrapped in `list(...)`.
- Build green: **161 pages + 1,223 search records + 6 print bundles + 6 PDFs**.
- Old link gate was a frozen page count (83 pages). Replaced with
  `check_inventory()` in `kb/share_check.py`: every section hub in the spec
  exists, every one of the 36 volumes has a `story/v/<vol>/index.html`, every
  tier-1/2 character has a page, and a BFS from Home finds orphans and depth.
  Result: 161 pages, 161 reachable, **max depth 3**, 0 orphans.
- Broken-link count 1061 → 0. Causes, each fixed at the architecture level:
  1. *page depth*: builders wrote links from the site root while the shell
     wrote `../` links. Now `site_shell.page()` is the single choke point:
     `rebase_site_links()` runs over the finished document (nav, rails and
     body alike), and `site_arch.SITE_ROOTS` is the one list of root-prefixed
     paths. Builders never compute depth again.
  2. *minor characters*: roster/rails linked to `people/<id>.html` for the 226
     minor names, which have no pages of their own. New rule in
     `site_data.person_href(char_id, tier, letter)`: tiers 1–2 get a page,
     everyone else is an anchor on their initial's page
     (`people/minor/t.html#tanishim`). `site_sections.plan_minor()` decides
     placement once, before rendering, and dossier headings are anchored on the
     database id (`<h3 id="<char_id>">`) instead of a re-slugged name, with a
     normalised-name second pass so `Takanashi (Kō)`-style headings still match.
  3. *A–Z strip*: `alpha_nav` emitted all 26 letters, dead-linking the empty
     ones. Now it takes the built letters and renders the rest as disabled.
  4. *print bundles*: `print_links()` was a no-op stub, so `share/print/*.html`
     carried site-relative links that resolved to nothing. Now an in-bundle
     link becomes a same-document anchor and anything else points at
     `../site/<path>`; print also gets its own copy of `style.css`, which is
     why the PDFs roughly doubled in page count — they were rendering
     unstyled before.

### 2026-10-26 21:0x — reader-facing wording, one table
- Internal vocabulary was still reaching the page: `tier 4 · 3 mentions ·
  0 scene(s)`, `**Mentions:** y2v9 ×2`, `Notes: P1 shell promotion`,
  `[P2-band]`, `corpus surname hits 6`, `### y1v2` headings, and the word
  "dossier" — the same leak the old nav had, now in body copy.
- Consolidated into **`site_arch.PROSE_REWORD` / `DOC_REWORD` +
  `public_words()`** (the duplicated table in `site_sections` deleted).
  `site_data.clean()` applies the prose table, `site_sections.reword()` the
  document table, `humanize()` for single curated lines — so a curated record
  and a dossier go through the same wording rules.
  Verified safe: "dossier", "tier" and "corpus" have **zero hits** in
  `text/*.txt`, so no reword can touch a verbatim quote.
- Minor pages now run through `reword()` (they were rendering raw dossier
  markdown — the source of most of the `tier 4` text).
- Volume-code headings render as "Year 1, Volume 2"; `**Mentions:**` →
  **Named in:** with volume names spelled out; pipeline `Notes:` lines dropped.
- Double-escaping bug (`&lt;a href=…` visible on the reader doors and topic
  pages): `S.esc(vol_link(...))` escaped generated markup in four builders —
  fixed to emit the link. Curated record fields (`why`, `situation`,
  `chronology`, `outcome`, `participants`) routed through `D.clean()` so they
  get the same wording pass.
- Duplicate "Home" reported by the user (3 on every page): the tab bar, the
  breadcrumb and the left-rail header all said Home. `crumbs_html()` now drops
  a leading Home crumb and an empty rail gets no header — 1 occurrence.
- Gate state after all of this: `share_check` **all checks passed** (161 pages,
  11,472 links 0 bad, print 2,259 links 0 bad, docs in sync, 6 PDFs).
  Jargon sweep over visible `<main>` text: only remaining "walk"/"ledger"
  hits are inside verbatim quotes; "corpus" removed from the 3 authored strings.
- **Determinism**: two consecutive clean builds → md5
  `a8e36935580a2d3b52d7f1fff69605e1` identical; docs mirror matches.

### 2026-10-26 21:1x — publish
- Pages is already wired on `github.com/FakeUser2121/cote-kb` (public repo,
  legacy Pages from `main:/docs`) — live at
  https://fakeuser2121.github.io/cote-kb/ (HTTP 200 before this push).
- Publishing plan: `docs/` is the served tree, so the commit is the docs
  mirror + the new `kb/` modules. `share/` (the build workspace: `share/site`,
  `share/print`, the zip) is being untracked and gitignored — it duplicated
  `docs/` and only the mirror is served. Local files stay.
- `ledgers/` y1v2 changes from the walk session are deliberately **not** in
  this commit (different concern, and this pass has no authority over them).
- First push was rejected by GitHub ("push declined due to email privacy
  restrictions": commit authored `fakef5858@gmail.com` while the account blocks
  pushes that expose an unverified address). USER CHOICE: use GitHub's noreply
  address. Redid the still-local commit as
  `FakeUser2121 <215920825+FakeUser2121@users.noreply.github.com>` through
  `GIT_*_EMAIL` env vars — no git config touched — then pushed `c09b0fb..14c3750`.
  FOLLOW-UP: the repo's git config still carries the Gmail address, so every
  future commit needs the same env override until the user changes it.
- **LIVE**: Pages rebuilt commit 14c3750 → status `built`. Verified over HTTPS:
  the home page serves the v3 tab bar with exactly one "Home", and
  `story/v/y2v9/index.html`, `people/minor/t.html`, `topics/expulsions.html`
  all return 200. → https://fakeuser2121.github.io/cote-kb/
- `share/` and `_sitecheck/` are gitignored now; `docs/` stays the served copy.

### 2026-10-26 21:2x — visual review handed to the USER
- Image reading is disabled for this session, so the look is the user's call.
  Checklist sent: one Home (not three) top-left; seven-section tab bar on every
  page; left rail scoped to the current section; Story spine within three
  clicks; citation chips expand; the "I've read up to" selector actually hides
  later material; no `tier N` / `dossier` / `corpus` wording anywhere; A–Z strip
  has no dead letters; PDFs download from the Appendix.

### 2026-10-26 21:3x — USER REPORT: empty rail outline remained
- User confirmed the duplicate Home text is gone, but pointed at the markup:
  `<nav class="rail left" id="rail-nav" aria-label="Contents"></nav>` — an
  empty element that still painted its border/panel column.
- Fix in two layers, so no page can ever show a blank rail again:
  - `site_shell.page()` puts `no-left` / `no-right` on `<body>` when that rail
    has nothing to render; `rail_left()` / `rail_right()` now return `""`
    instead of emitting an empty landmark (no stray screen-reader region).
  - `site_assets/style.css`: those body classes collapse the grid column
    (`body.no-left .layout { grid-template-columns: minmax(0,1fr) 244px }` etc.)
    with overrides inside the 1240px and 900px breakpoints — without them the
    higher-specificity base rules would have beaten the media queries and left
    a phantom 244 px strip on phones. The ☰ drawer button is hidden too, since
    it would open nothing.
- Home now renders `class="sec-home no-left"` and has no rail element.

### 2026-10-26 21:4x — cross-link panels (DoD #4) were the real gap
- Measured per section before fixing: people 16/48, story 6/47, school 14/22,
  world 28/29, topics 0/6, guides 0/4, appendix 0/4. The new Story axis was
  still 36 islands — the volume pages had no Related rail at all.
- Added `volume_related(ctx, v, exams, present, docs)` in `site_sections.py`:
  previous/next volume in reading order, the year hub, the exams run here, the
  tier-1/2 characters present, and the guide/transcript documents for the
  volume. Story coverage went 6/47 → **42/47**.
- Coverage after this turn: 11,818 links, 0 bad; 161 pages, all reachable,
  max depth 3; `share_check` all passed (site, print, docs mirror, 6 PDFs);
  build md5 `59ad3edfc078bc1a0066144dfeaf4f36`.
- STILL OPEN: topics (0/6), guides (0/4), appendix (0/4) and 32 people pages
  (mostly minor-character initial pages and hubs) have no Related panel;
  spoiler scoping covers 74/161 pages (248 reveal buttons) — dossier-derived
  pages only, because `section_scope` wraps `<h2>` blocks by their newest
  citation and hub/index pages carry no per-block citations.

## 2026-10-26 22:0x — pushed, Pages rebuilt, live markup verified
- Gate re-run before pushing: `share_check: all checks passed` — 161 pages,
  11,818 links / 0 bad, search index 1,223 records / 0 bad, `docs/` in sync,
  6 print docs / 2,259 links / 0 bad, guides.pdf back to 18 pages.
- Committed as `bfe19f1` ("Site v3.1: collapse empty rails, cross-link the
  volume pages") with the GitHub noreply author via `GIT_*_EMAIL` env vars —
  git config untouched, per standing rule. Staged `kb/` (3 files), `docs/`,
  `progress3.md`; `ledgers/` y1v2 work and `session-ses_ebdd.md` deliberately
  left out of this commit.
- Pushed `14c3750..bfe19f1` to `origin/main`; Pages `builds/latest` reached
  `built` on commit `bfe19f1`.
- Verified the live markup over HTTPS (not screenshots):
  - `index.html` → `class="sec-home no-left"`, 0 `rail left` elements — the
    empty outlined box the user reported is gone.
  - `story/v/y1v1/index.html` → 200, rail present, Related panel present.
  - `people/minor/t.html` → 200; `topics/expulsions.html` → 200 and carries
    `no-right`, so the right column collapses there too.
- Next: remaining Related panels (topics 0/6, guides 0/4, appendix 0/4,
  32 people pages) — DoD #4 is not yet satisfied.

## 2026-10-26 22:3x — evidence-only rebuild + reader wording gate

The user's standing order was to strip everything that pre-dates the y1v1 walk:
those pages were written from whole-series memory and carried invented lines.
Two follow-up decisions from the user: pages whose content came from the retired
layer stay in the nav as labelled stubs, and the y1v1 evidence feeds as many
pages as it can, with unread material falling back to reference links instead of
a wall of bullets.

What changed in the build:
- `build_share_site.py` no longer loads the curated layers at all
  (`status_timeline`, `relations`, `claims` are gone from `build_ctx`); stats are
  derived from the ledgers (`walked`, `scenes`), and `build_pathmap` is
  database-driven, so the pre-walk `dossiers/` tree is not in the path map.
  `render_dossier_meta()`, `site_data_groups()` and the `render` import are
  deleted; 163 → 161 pages after skipping characters whose page is an anchor on
  a minor A–Z page (a `#` in an output path was writing a literal file).
- `dossiers/` moved to `archive/dossiers/` (`git mv`, 101 entries) with a README
  stating it feeds nothing and that its text must not be copied into a ledger,
  draft or page. The generators that still read the old path are listed there.
- Ledger id ↔ page id pairing lives in one table, `site_ledgers.LEDGER_ALIAS`
  (midterm-final-written→midterm-exam, private-points→point-economy,
  library→school-library), with `stem_for/page_id_for/exists_for/load_for`.
  Without it a volume page linked to `school/exam/midterm-final-written.html`,
  which does not exist.
- `site_evidence.vol_chip` takes the page's own directory through `_dir_of()`
  (dirname only for `*.html`), which fixed the off-by-one depth that produced
  `../story/v/y1v11/index.html` on every school/exam page.
- Unread entities render mechanical facts + `coverage_stub`, and the unread
  volumes collapse into one inline line of reference chips plus a link to
  `appendix/coverage.html` — the "graceful fallback, not cluttered dump" rule.
- `entity_page_href` (site_sections) resolves a ledger stem to a real page and
  falls back to the section index; `related_links` gutted to `[]`; `topics` are
  queries over `L.scan()`; `mentioned_volumes` sorts by reading order.

Reader wording pass (this turn):
- Citation chips now say `Vol. 1 p.247`, never `y1v1 p.247`. `chipify` builds the
  label from `volume_short` and skips regions that are already a chip, which also
  killed a real markup bug: chips were being wrapped inside chips
  (`<summary class="cite"><details class="citebox">…`), invalid HTML.
- `site_ledgers.humanize()` turns a volume key used as a word inside a note
  ("her y1v2 arc") into the reader's label, while leaving citations alone.
- Pipeline bookkeeping no longer reaches a page: `<!-- walk: … -->` comments and
  the `## y1v1 WALK COMPLETE` / `coverage: 264/264` stamp were being rendered as
  scene text on the Ayanokōji page. `_entries` now drops headings and
  `BOOKKEEPING_RE` lines.
- `volume_tag` is human ("Year 1 Vol. 5", "Side Stories") in cross-volume lists.
- Home/appendix/topics/school/guides copy rewritten to say "read line by line"
  instead of "the walk / walked / ledger"; footer example matches the chip that
  is actually rendered; `appendix/citations.html` still documents the raw keys —
  that is its job, and it is the only page allowed to.
- Two new gate checks in `share_check.py`: `check_wording` (tag-free visible
  text must not contain ledger/walk/dossier/checkpoint/char_id/cote_kb.db/raw
  volume keys, with "the walk back home" and the citations page exempt) and
  `check_chip_markup` (no `<details>` inside a `<summary>`). The wording check
  found 10 live leaks on its first run; it is now at 0.

Verified this turn: `build_share_site: 161 pages + 761 search records + 6 print
bundles + 6 pdfs`; `share_check: all checks passed` — 15,831 site links 0 bad,
6,653 print links 0 bad, docs/ in sync, wording 0, nested chips 0; HTML tree md5
identical across two full rebuilds (only `pdfs/*.pdf` bytes differ). Spot-checked
rendered text: Ayanokōji scene chips `Vol. 1 p.14-15 …`, no WALK COMPLETE stamp;
`school/exam/entrance-exam.html` stub reads "Nothing about Entrance Exam has been
read line by line yet … Named in 13 volumes — Year 1 Vol. 1 · …".

Note for future turns: `build_share_site.py --docs` is exclusive — it mirrors and
returns. A content change needs the plain build first, then `--docs`, or the gate
silently checks stale HTML (this cost a rebuild cycle here).

The uncommitted y1v2 ledger entries are now part of the published evidence (the
volume page and the affected character/topic pages show them under the "Partway"
status note). Before publishing they were put through the walk's own fidelity
checkers: `kb/verify2.py y1v2` → 172 [says] lines, 4 too short, ALL PASS;
`kb/verify3.py y1v2` → 96 non-says quoted lines, ALL PASS. So the site is
publishing verified text, just not yet a complete volume.

## Known state / risks
- Pushed as `6226d50` (v4) and live on Pages; six sampled URLs return 200 with
  zero internal vocabulary in visible text. Verified content parity between
  `docs/`, `share/site/` and the live pages (Horikita: 23 ledger scenes → 23
  rendered scene blocks).
- DoD #4 is still only partly met: with the curated `relations` table gone, the
  generic "Related" panel returns nothing on the pages listed earlier, and the
  ledger-derived cross-links (`volume_related`, per-section rails) carry what
  connectivity exists. Rebuilding those panels from co-scene evidence is the
  next site task, not a wording task.
- `share_check` counts *lines*, so a scene count must come from `grep -o`, not
  `grep -c`; the pages are single-line HTML by design.
- `share/site/` and `docs/` are both current and in sync (`share_check`
  compares them); PDFs regenerate inside the build.
- Determinism: `*.pdf` excluded from the content md5 (chromium timestamps).
- Ledger fidelity verifiers (progress2.md) stay green independently: 626 [says]
  ALL PASS for y1v1.

## Definition of done for this pass
1. Build runs clean from an empty `share/site/` and is deterministic.
2. Every page reachable from Home in ≤ 3 clicks; no orphan pages.
3. 0 broken links (local crawl gate), 0 jargon terms in public copy.
4. Cross-links: each page carries "who/what else is on this page" panels.
5. Spoiler control + citation chips present on all evidence pages.
6. Screenshots reviewed (home, story hub, volume page, person, topic, door).

## 2026-10-27 — People: allegiance out, page-stated posts in

The user rejected the People grouping on sight, and was right. Diagnosis
before code: `characters.mid_type` (written by `kb/assign_mid_type.py`) held
one unary value per person, but "ally" / "rival" is a relation — it needs a
subject and a moment. The table's own comments ("tracks Ayanokouji", "helped/
protected arc") name volumes (`y1v5`, `y2v6`, `y2v12`) that have never been
read, so the buckets were memory wearing a schema. Three separate faults:

1. No subject. "Allies" to whom was never stored.
2. No time. One immutable value; a Year-2 class reshuffle falsifies every row
   silently. `class: Class 1-D (enrolled April 2015)` in ledger meta made it
   worse by writing the claim in a permanent header.
3. No evidence. 27 people carried a bucket; only 14 had a ledger at all, and
   the per-person ledgers barely contain role statements. Tsubaki Sakurako was
   filed `authority  # teacher` — she is student council — and the label
   merged faculty and council into one bucket, so the entry could be wrong
   and still fit the label.

What replaced it:

- `[role:<key>] (p.NN) note` is now a ledger verb (`MARKERS["role"]`).
  Closed vocabulary in `kb/site_roles.py`: `class-1a…1d`, `student-council`,
  `faculty`. Rendered as "Post", never as the key.
- `kb/site_roles.py` reads **only** those entries, keyed by the volume section
  they sit in, so a transfer is a second row instead of a rewritten first one.
- `kb/site_sections.py`: People index drops the six buckets. New section
  "Where the pages place them" groups by institution under the volume that
  states it, each row carrying the page and the note. Below it, "Role not
  stated on the pages read so far" lists everyone else — for a ledger owner
  it shows the classrooms their scenes are set in; for a name with no ledger
  it says so. 18 of 27 sit there today, which is the honest state of a
  one-volume dissection and exactly the user's point.
- `site_data.py` no longer selects `mid_type`; `GROUP_LABEL` keeps only the
  counted presence bands; `build_pathmap` no longer guesses
  `dossiers/mid/<group>/…` (the link gate proves nothing points there).
- Identity table: "Role in the story" was printing the presence band, so it
  is now "How often they appear"; a new "Where the pages place them" row lists
  the stated posts with volume + page.
- Role citations are **plain page numbers, not chips**: the note beside them
  is a paraphrase, and the page's quote bank may not contain the line that
  carries the claim. A chip that opens unrelated text is worse than a number.

Backfilled (12 lines, 11 people, every one anchored to a page the ledger
already recorded): ayanokouji p.137–140 (PA: "from first-year Class D"),
horikita-suzune p.142–143, kushida p.35, sudou/yamauchi/ike p.102 (Idiot
Trio), karuizawa p.103, ichinose p.224 + p.141, chabashira p.30–32,
hoshinomiya p.140–141, manabu p.66–68. No other line states a post, so
hirata, kouenji and sakura still fall to the unstated list — flagged to the
walk in progress2.md rather than filled by inference.

New gate (`kb/share_check.py`): `check_role_grouping` — every `h4 id="g-…"`
on the People index must be one of the six institutions, and every `[role:…]`
entry must carry `(p.NN)` and a known value; `check_no_curated_typing` —
`site_data.py` may not read `mid_type`, and no people page may show
`mid (allies)`-style strings.

Numbers: build 161 pages + 764 records + 6 bundles + 6 PDFs; gate all green
(15148 site links 0 bad, 6687 print links 0 bad, 0 wording leaks, 0 nested
chips, role grouping 0, curated typing 0); two consecutive builds ->
`md5 6830a4e6618d6c92da54e7143e842a6e` both times.

Operational note: the first rebuild after this change produced four 0-byte
PDFs and a `people.pdf` truncated at exactly 2 MiB — the root disk was at
100% (16 MB free). Reclaimed 165 MB by clearing `~/.cache/chromium-headless`
(the PDF renderer's own cache; it regenerates). /tmp is tmpfs, so clearing
/tmp does **not** help. Disk is still ~99% full overall (Steam alone is 84 GB
in `~/.local/share`); worth watching before the next PDF build.

### Same day — rail hierarchy

User: "theres no indentation here, so i cant tell which options are underneath
or at the same level." Correct: every rail link used the same
`padding: 5px 9px`, so a name inside an expanded group sat flush with the
group itself. Two fixes:

- `.rail details > a.item` is now indented (24px), stepped to 13px, and draws
  a hairline guide at its left edge; the active pill clears the guide. This
  applies to every section's rail, not just People.
- The People rail listed the principals twice — a "Principal characters"
  section link and a "Principal" group holding the same seven names. Merged
  into one `Principal characters` expandable entry; "All people" above it
  still goes to the index top, so no anchor was lost.

### Same day — the rail is a tree, not a list of peers

User: "Its still not right, which ones are supposed to be under which ones?
isnt recurring inside all people, but showed here outside? similar with
others." Right — the indentation fix made nesting *look* possible but the
component still only held one level, so `All people` rendered as a sibling of
its own sections.

- `rail_left` now delegates to a recursive `_rail_node`, and `link_line`
  takes a depth. A `details` may contain `details`; children are wrapped in
  `.sub dN`, which indents behind a hairline per level. Depth is carried in
  the class (`d0`…), so CSS does not guess from DOM position.
- `people_rail` returns one root `<details class="d0" open>`:
  **All people** (summary links to `people/index.html`, count = whole cast)
  → Principal characters / Recurring characters / Minor characters A–Z /
  Roles in Vol. N (→ Class 1-B, Class 1-D, Student council, Faculty) /
  Role not stated (N). Nothing inside is printed as a sibling of the root.
- A `details` may mark its summary as a destination (`summary_href`); the
  arrow still opens, the title still navigates. The existing `href`-on-
  details contract (extra line under the summary) is unchanged, so the Story
  and School rails keep their shape.
- Drive-by fix in `story_rail`: `label.replace('Vol. 1 · ', 'Vol. 1')`
  swallowed the separator and printed `Vol. 1Year 1, Volume 1`. Now built as
  `Vol. N · <volume label>`.

Gate: 161 pages, 16012 links 0 bad, 764 records, 0 wording leaks, 0 nested
chips, role grouping 0, curated typing 0, docs in sync, 6 print docs 6687
links 0 bad, 6 PDFs. Two builds -> md5 `b028a0021240ab73ae840e3ffacec116`
both times.

### 2026-10-27 — The first Ayanokōji scene is now the book's text, not a summary

User, on the opening block of the Ayanokōji page: "That is not all the quotes
he said about that, let alone being word for word." Correct. The ledger had
transcribed the Chapter 1 prologue as eight mixed entries — one quoted
sentence, the rest the walk's paraphrase — and the site printed the
paraphrases under INNER VOICE / BACKSTORY in the same quote styling.

- Re-walked y1v1 p.14–15 against `text/COTE Y1 V1.txt`. The block is now the
  eleven paragraphs of the monologue, each a `[narrates]` entry anchored to
  p.14 or p.15, copied verbatim (verified by normalized diff: 0 mismatches,
  and every source line on those pages is covered except the chapter title).
  The paraphrase entries and the duplicated `[voice]`/`[trivia]` notes are
  gone; one `[trait]` line stays as analysis, not as evidence.
  Scene now reads `13 entries · 11 quoted` instead of `10 · 5`.

### Quote audit triggered by that block

`verify3.py` (the non-`[says]` quote checker) was matching from *any* quote
character to the next one, so a line with two real quotations failed on the
prose between them — two of its three failures were noise. It now pairs
curly quotes directionally and straight quotes alternately, checks every
span over ten characters, and keeps the words inside curly quotes when it
strips the marks (deleting the span cut a hole in the outer quotation). With
the checker honest, it found nine more places where a quotation was not the
book's text:

- `start again` (ayanokouji p.53) — the book cuts off at "start ag—"
- `Horikita trusts you…` (p.93) — actually two sentences on p.94
- `You are defective` (p.126) — book: "You're defective."
- `people learned the truth` (p.192) — book: "people around here learned the truth", p.193
- `how I really feels` (p.216) — "feel"
- `undeniable reality` (horikita p.16) — phrase is nowhere in volume 1
- `Take it slowly` (kushida p.34) — book: "Just take things slowly. Don't rush."
- shogi quote stitched two separate p.151 lines into one; now two quotations
- `girlfriend incentive` / `from a third-year acquaintance` /
  `would've been fine / perfect if serious` (volume ledger) — paraphrases in
  quote marks; replaced with the p.160, p.235 and p.256 lines respectively

`verify2.py y1v1`: 624 says lines, ALL PASS. `verify3.py y1v1`: 246 non-says
quoted lines, ALL PASS. Site gate green; docs mirrored (md5
fbf26d1a0b93d8328f69f8d002f6f560). People PDF rebuilt at 130 pages.

### The page column now uses the width it is given (site, 2026-10-27)

Reported: "not using free real estate", empty space on most pages including
home. Cause was one rule: `site_shell.page()` wrapped every body in
`<div class="measure">` and `.measure { max-width: 74ch }` (~686 px). On home
that 686 px sat inside a 1341 px column (no left rail, 244 px right rail), so
the doors and library cards could only ever form two columns and the right
half of the page was blank.

What changed:

- `.measure` no longer caps width. Running text is capped instead
  (`--prose: 86ch`): paragraphs, top-level lists, blockquotes; boxes at 78ch.
- Structural blocks take the full column: hero, `.stats`, `.doors`, `.cards`,
  `.grid-list`, `.facts`, tables, scene headers.
- Scene blocks and ledgers cap at `92ch` so their rules end under the text
  rather than running past it.
- Hero is a two-column grid at ≥1000 px: title + intro left, the six counts
  right (three columns of stats), instead of a short strip over blank space.
- Home's three "Reading a page" paragraphs sit in `.cols` (two columns above
  1000 px); the six home doors are an explicit 3×2 grid at ≥1000 px.
- Shell width 1520 → 1600 px (`--shell`), applied to masthead, tabs and
  layout together; search box allowed 560 → 680 px.

Measured with headless Chromium+CDP at 1600 px (not a screenshot): home
content 1341, measure 1261 (was ~686), hero 1261 with stats 411 on the right,
doors 1261 in 3 columns, cards 1261 in 4; people index grid 997 wide; prose
797; character ledger 853. At 1366 the text fills the 1027 px column; at 390
everything stacks, no horizontal page overflow (the tab strip scrolls inside
its own `overflow-x`). Print keeps its own 74ch measure inside the page box,
so the PDFs keep their old pagination (people 130 pages, story 153); only
their metadata bytes changed. Rebuild is deterministic (same HTML md5
twice); `share_check --site --print --pdf` all green; docs mirrored (md5
0dc0f7d65fc24632b4a72506c1d8eee9).

### Publishing moved off GitHub Pages (2026-10-27)

`FakeUser2121/cote-kb` is private now, and the free plan cannot serve Pages
from a private repo: `POST /repos/.../pages` returns 422, `has_pages` is
false, and https://fakeuser2121.github.io/cote-kb/ returns 404. User's call:
leave the repo private, Cloudflare is serving the site for now. So `git push`
is the last step from this machine; do not expect the github.io URL to
answer, and do not flip repo visibility or Pages settings unasked.

### Recall rows now lead to the scene (site, 2026-10-27)

Reported on `guides/find-that-moment.html`: "I can't seem to click things
here to see where that part is." The rows were dead text except for the
volume and the entity name; the scene title and the page pin were plain
spans, so nothing led to the block the note came from.

- `site_topics.entity_href()` is now the single resolver for a ledger stem's
  page; `entity_link()` uses it too, so a row and its links cannot drift.
- `scene_anchor()` replicates `site_evidence.scene_block`'s id rule (slug of
  the heading, 48-character cut). `scene_href()` returns
  `entity.html#ev-<anchor>`; for minor characters, whose href already
  carries a letter-page fragment, it keeps only the scene fragment (a URL
  takes one hash).
- The beats list and `entry_row()` (topic pages) link the scene title there;
  the page pin became `a.cite` to the same target instead of a plain span.
- `shell.js` opens a targeted `<details>` on load/hashchange before the
  browser settles, and `:target { scroll-margin-top: head + 14px }` keeps the
  target clear of the sticky masthead.

Validated independently of the gate: 156 scene links across topics and the
recall page, 0 missing pages, 0 missing anchors, 0 duplicate anchors. CDP at
1600 px: `people/...html#ev-y1v1-p-16-18-…` opens the details (top = 120 px
under a 106 px header); `school/system/private-points.html#ev-y1v1-p-30-32-…`
lands a div target at the same offset. Gate green, deterministic
(`892fcf5d2fb2e66a57ff506c5912aae6`), docs mirrored
(`b41b71c74dc578c11ec2921f5ae5323e`); PDFs keep their page counts.

Not changed, but visible from the dump: the beats list is cut at 80 rows
after sorting by volume, and all 80 are Volume 1 Ayanokōji. The cap hides
the rest of the walked evidence instead of sampling it. Left as-is pending
the user's call.

### Ledger rows and the phone masthead (site, 2026-10-27)

Reported as "Page looks half broken and weird", with a dump of the
Ayanokōji page where the speaker and the page pin appeared under the
`Spoken` label. Reproduced with CDP at 1600 px: `entry_html` emitted
`mlabel`, optional `pre`, the `<p>`, optional `post` and the `pin` as five
separate children of a two-column grid. Auto-placement put the quote in
column two and everything after it in column one — the attribution
"Horikita Suzune" measured 104 px wide and 57 px tall, wrapped inside the
gutter, with `p.16` beneath it.

- One `.ebody` cell now holds the paragraph; the role bucket and the
  speaker are inline inside it (the speaker in a `.by` span), and the page
  pin is inline after the text. Column one is `minmax(0, 1fr)`.
- After: label x306 w104, body x424 w733, "— Horikita Suzune" x711 and
  "p.16" x854, both in the text column. 542 rows on the character page with
  0 bodies left of the label and 423 pins with 0 strays; the y1v1 volume page
  has 1711 rows, 0 bad.
- Print uses the same markup, so rows no longer reserve two extra lines:
  people.pdf 130 → 126 pages, story.pdf 153 → 152. Other PDFs unchanged.
- `details.scene.ev > summary > .head` had no grow, so the scene's page chip
  stopped at the title (head right 997 on a 1157-wide row). `flex: 1 1 0;
  min-width: 0` puts the chip at the head's right edge and the entry count at
  the row's; the zero basis also stops the phone wrap that stranded the `+`
  on a line above the title.

Phone masthead, found while measuring: at 390 px the scope picker ran 73 px
past the viewport (`scrollWidth` 448 vs 375). Under 620 px the search now
takes its own row, the tools sit right, and the picker's label is clipped
rather than removed so the select keeps its accessible name. `--head-h` was
stale (152 px at ≤900 where the masthead measures 108): now 112 px at ≤900
and 148 px at ≤620, both measured. On phones the entry count gets its own
line and the separate volume chip is hidden, because the pages chip already
reads "Vol. 1 p.16-18".

Verified: no horizontal overflow on eight sampled pages at 360/390/700/1024;
a folded scene reached by hash at 390 px opens with its top 162 px below a
145 px masthead; the drawer opens at 148 px. Gate green, deterministic
(`c2c7bf95f2c23561521b6621b05e8a7e`), docs mirrored
(`67d1322985046b87050e8cfac2ed0dba`).

Still open from the last report: the "I remember it mattered" list is cut at
80 rows after a sort by volume, so all 80 are Volume 1 Ayanokōji.
### Page numbers stopped pretending to be buttons (site, 2026-10-27)

Reported after the last push: the row page numbers (`p.30-31`) were bright
and showed a pointer but did nothing, and the book is not on the site, so
"where?" had no answer. My previous turn had gone the wrong way — it started
turning every row number into a link to its scene's proof box. That work is
reverted; a site without the book has nothing honest to link a per-row number
to.

The rule now written into the markup: **bright means it does something.**

- `site_evidence.pin()` renders a row number as `<span class="pageref">` —
  muted mono text, `cursor: auto`, no border, no background. It stays exactly
  where it was, because a reader checking a claim needs the printed page.
- `site_shell.chipify()` no longer emits `<span class="cite">` when the page
  has no recorded text; that case is `.pageref` too, with the title "No page
  text recorded from this citation yet". Before, an empty chip looked identical
  to a chip with text behind it.
- The scene chip that does open text gets a caret via CSS
  (`details.citebox > summary.cite::after` → ▾, ▴ when open). Carets and
  arrows are suppressed in print, where nothing opens.
- A number that genuinely navigates — the summary rows on topic and recall
  pages, which quote a scene held on another page — keeps the chip and gains
  an arrow (↗). `site_topics.pin_for()` is now the single builder for those,
  so the three hand-built call sites and `entry_row` cannot drift.
- The Home "Reading a page" section states all three cases, including that the
  book itself is not hosted here.

Counts in the built site: on `people/ayanokouji-kiyotaka.html` 65 scenes, 63
with an expandable page chip, 2 with only a plain page tag, and 425 plain page
numbers; `school/system/private-points.html` 8 chips and 45 plain numbers;
`topics/points.html` 41 arrow chips that navigate.

Verified: clicking a scene chip flips `details.open` false → true and shows
the verbatim lines with the source ("Year 1, Volume 1, page 16"); 1952
fragment links across the site, 0 pointing at a missing page or a missing
anchor; no horizontal overflow on eight sampled pages at 360/390/700/1024.
Gate green, deterministic (`276fa93acf6ed183c10d9aa3e2fbb2f8`), docs mirrored
(`26156c3ee48dc7684620400a7682e554`). PDFs moved again with the changed chips
(topics 123 pages, +271 KB from the arrow chips; people 126).

### One disclosure per scene, then no citation chip at all (site, 2026-10-27)

The reported conflict: "whys there 2 things doing the same thing?" A folded
scene and the chip in its heading both opened the same pages, and the chip's
panel was a two-line sample of the *first* page of a range — a shorter,
truncation-hidden version of the rows underneath it. Governing rule, now stated
in `site_evidence` and enforced by the gate: **one disclosure per region, and a
control may only reveal what is not already visible above it.**

The plan assumed chips would survive outside scenes, in guide and appendix
prose. Both halves of that turned out to be wrong, and both were measured rather
than argued:

- `site_evidence.scene_block()` stopped building a chip in the heading. The
  scene's page range prints as `pages_ref()` — the same grey reference text a
  row uses — so a scene has exactly one expander, its fold. `cite()` is gone;
  `pin()` lost the `ctx`/`vol_id` arguments it no longer needed and now emits a
  link only when the row sits on a *different* page from its scene (topics and
  recall lists), which is what the ↗ arrow has always meant.
- Prose produced no chips to save. All 378 chips in the committed build came
  from scene headings (378 chips, 388 scenes); guide prose writes
  "Vol. 1, p.146" while `chipify` only matched the key form "y1v1 p.247". A
  temporary `default_vol` argument made 95 of them appear — and the DOM then
  showed why the chip had no surface at all: `<details>` is flow content, so the
  parser closes the paragraph around it. 31 inline chips turned 21 paragraphs on
  a guide page into 53 blocks and orphaned the text after each one. The control
  was deleted, not relocated.
- `site_shell.chipify()` is now `reference_cites()`: it wraps a printed-page
  citation in the grey `pageref` span and builds no control. It takes either
  form the sources use — the file key or the human "Vol. 1, p.146" — and prints
  one label for both, so a key can never reach a reader. Tags and existing
  `pageref` spans are opaque, so ids, anchors and already-rendered references
  survive a second pass; a bare "p.25" stays prose because no year can be
  inferred from it. `CHIP_SAMPLE`, the sample/"not shown" panel and the
  `memo_lookup` + `ctx["lookup"]` cache are gone. `site_data.quotes_at()` stays
  as the coverage question the walk asks, with nothing in the site calling it.
- `share_check.py` has `check_disclosures()`/`DisclosureWalker`: a
  `details.citebox` inside `.scene` or `.ledger` fails the build. Negative-tested
  against a folded scene, an open scene div and a bare ledger (1 flag each) and
  against a clean scene and guide prose (0).
- `site_ledgers.VOL_WORD_RE` lost its "keys that belong to a citation are left
  alone" exception: a key inside a note humanises to "Vol. 1 p.247" plain text,
  so a scene cannot acquire a control from its own prose.
- Copy: the Home legend now names two controls, the + fold and the ↗ chip, and
  says grey numbers are never links; the citations appendix explains why a page
  number is never a button here — the scene's own fold already opens those lines,
  and in prose the archive has nothing to open because it holds located lines,
  not the book. The character-page lede and the volume-page evidence note
  stopped promising that a page chip opens text.
- Print: `.citebox[open] { display: none }` was dropping the citation itself from
  paper; with no chips the whole block is deleted, `a.cite` prints as plain text
  with its arrow suppressed, and the citebox/`.citeproof` CSS is gone. Dead
  `#cite-all` handler removed from shell.js (no builder ever rendered it).

Counts, committed build → this build: chips 378 → **0**, plain page references
3477 → 3872, cross-page arrow links unchanged at 668, scenes unchanged at 388.
CDP (`file://` reads, no screenshots): 0 `details.citebox` and 0 `<details>`
inside a `<p>` on seven sampled pages; inside scenes, expanders 0 and buttons 0
(volume page 178 scenes, character page 65); a closed scene is 50px tall and the
same scene open is 1385px, so the fold is doing the whole disclosure job; every
arrow on a page resolves. Gate green: 161 pages, 16830 links, 764 records,
0 bad, 0 disclosure violations, 0 wording leaks; deterministic
(`cb13c2d1132bce4e050ea50ee3256ef7`) and docs mirrored. PDFs: guides 22 / people
123 / school 37 / story 151 / topics 123 (1987 KB, −389 KB now that the panels
stopped printing) / world 34.

Not done: the walk still has y1v2 ch1 unstarted. Stage 5 of the plan — promoting
quote-bank lines a scene does not already carry into verbatim rows — belongs to
the walk itself and starts there.

### y1v2 Chapter 3 reaches the site, and the wording gate earns its keep (site, 2026-10-27)

No engine change this turn — the walk moved and the build followed it.
`check_wording()` is the only interesting part: it blocked the first push of
the Chapter 3 fan-out with 12 problems, and every one of them was a line the
walk had written about itself rather than about the book ("recorded in the
y1v1 section of this ledger", "the ledger only says", "What the ledger can
assert", "chases Horikita down the walk to the entrance"). Five source lines
were rewritten in reader language, one of them twice because the same sentence
is rendered on a person page, the volume page and a topic page. The rule stayed
put; the prose moved. Nothing about the checker was loosened — it was the
ledger text that was wrong.

Counts after the rebuild: 161 pages (unchanged), search records 764 → **776**,
internal links checked 16830 → **17092**, 0 bad; cross-page `a.cite` links 668 →
**735**, plain `.pageref` references 3872 → **4343**, `details.citebox` still 0.
Print bundles: guides 22, **people 131**, **school 39**, **story 154**,
**topics 137**, world 34 pages. Determinism re-measured across two consecutive
builds: `7b912f598b4fed8f5aa0748bdb755744`, and `--docs` mirrored to the same
tree.

Where the new text lands was checked rather than assumed, because Ike and
Yamauchi do not have their own pages: their Chapter 3 blocks render on
`people/minor/i.html`, `people/minor/y.html` and the volume page
`story/v/y1v2/index.html`; `systems/point-economy` renders inside
`school/system/private-points.html` and `exams/midterm-exam` inside
`school/exam/midterm-final-written.html`. Full gate: all checks passed.

### Chapter 4 ships, and the chapter renderer was silently dropping its tail (site, 2026-10-27)

The Chapter 4 evidence went in as one volume section plus fourteen ledgers'
worth of scene rows, and the rebuild surfaced a content bug that had been in the
volume pages from the start: `kb/site_sections.py` rendered a chapter block as
`{extras or beats}` with the two lists capped at `[:8]` and `[:10]`. Every
bold-labelled bullet in a chapter section — which is every beat, plus the page
map, entity, system, thread notes — lands in `extras`, so a chapter with more
than ten labelled bullets had its tail dropped with no warning, and any plain
`beats` list was discarded as soon as one label existed. Chapter 4's section
carries fifteen labelled bullets and published ten.

Fixed at the renderer, not in the copy: both lists are emitted, in document
order, with no cap, and a comment records why the cap cannot come back — a
dropped bullet is a dropped claim, not a layout choice. Effect measured: the
Volume 1 page is unchanged (55 labelled bullets before, 55 after), the Volume 2
page went 15 → 30, and Chapter 4's page map, new-entity, new-system, open-thread
and attribution-gap lines now reach readers.

The wording gate earned its keep again: 14 problems on the first pass, all of
them pipeline vocabulary in prose this session had written — a heading phrased as
"the walk to school", a scene line telling the reader that "the walk should not
over-read", and two older lines using "the ledger records" / "His ledger of".
Five strings rewritten in reader language; the checker was not loosened. The
gate's own regex was left alone, including the `the walk (back|home|there|away)`
exception, because the new phrasings ("walking to school", "the route to school")
are what the prose should have said anyway.

Counts after the rebuild, against the Chapter 3 commit: 161 pages (unchanged),
search records 776 → **778**, site links 17092 → **18094** checked with 0 bad,
cross-page `a.cite` links 735 → **1034**, plain `.pageref` references 4343 →
**5657**, `details.citebox` still 0, ledger rows on the site 5468. Print bundles
grew with the evidence: guides 22, **people 140**, **school 46**, **story 164**,
**topics 199**, world 34 pages. Determinism re-measured across two consecutive
builds: `a6398f038cda4e85e0f920a3c2bbe0d3` (was `7b912f598b4fed8f5aa0748bdb755744`
at Chapter 3), and `--docs` mirrors to the same tree.

Render locations checked rather than assumed: the Ichinose, Sakura, Kushida,
Horikita and Ayanokōji blocks go to their own pages under `people/`; Ike,
Yamauchi and the second-hand Hirata/Karuizawa/Kōenji rows go to
`people/minor/i.html`, `people/minor/y.html` and their named pages;
`systems/point-economy` renders inside `school/system/private-points.html`;
`exams/midterm-exam` inside `school/exam/midterm-final-written.html`; the Chapter
4 narrative section inside `story/v/y1v2/index.html`, where it aggregates into
`topics/points.html`, `topics/results.html`, `topics/relationships.html`,
`topics/who-knew-what.html` and `topics/expulsions.html`. Full gate:
`share_check --site --print --pdf` all checks passed.

### Chapter 5 ships; the missing row was a write, not a render (site, 2026-10-27)

Chapter 5 went in as one volume section plus ten ledgers' worth of scene rows,
and the audit that followed found exactly one row that had been intended but
never written: Chabashira's [limit] on the frog image (p.164). The quote was
already rendering from Sakura's page, which is why the first pass looked
complete — the site was rendering everything it was given; the ledger was the
thing missing a line. The row was added to the faculty-room section and the
rebuild picked it up. No renderer change was needed this time, and none was
made.

A places ledger for the club-activities building was written during the fan-out
and then deleted: world pages enumerate curated location rows, so a new
`ledgers/places` file renders nowhere on the site. Deleting it changed no
output; the building remains in Sakura's 5.5 rows and in the volume setting.

Counts after the rebuild, against the Chapter 4 commit: 161 pages (unchanged),
search records **778**, site links 18094 → **18283** checked with 0 bad,
cross-page `a.cite` links 1034 → **1089**, plain `.pageref` references 5657 →
**6075**, `details.citebox` still 0. Print bundles: guides 22, **people 145**,
school 46, **story 167**, **topics 209**, world 34 pages; print links 8933
checked with 0 bad. Determinism re-measured across two consecutive builds:
`b5fdb0c9711faf8f1e1be265d168f6ef` (the pre-fix build of the same chapter was
`782e8ec3c9b2bb8aafce9d108397cb81`), and `--docs` mirrors to the same tree.

Render locations checked rather than assumed: the Sakura, Kushida, Horikita,
Ayanokōji, Ichinose, Chabashira and Sudō blocks go to their own pages under
`people/`; Ike and Yamauchi to `people/minor/i.html` and `people/minor/y.html`;
the token key and the class board facts to `school/system/private-points.html`;
the Chapter 5 narrative section to `story/v/y1v2/index.html`, where it
aggregates into `topics/points.html`, `topics/who-knew-what.html` and
`topics/relationships.html`. Full gate: `share_check --site --print --pdf` all
checks passed.

### Chapter 6 ships, and a new ledger briefly split a character in two (site, 2026-10-27)

Chapter 6 went in as one volume section plus ten ledgers' worth of scene rows,
and it is the first chapter to add people pages rather than only fill existing
ones. Three ledgers were created: `kanzaki-ryuuji`, `tachibana`, and `sakagami`.
The first renders on `people/minor/k.html` because Class B's second is not a
principal page; Tachibana gets her own `people/tachibana.html`; Sakagami needed
care, because the roster already carried a mention-only `people/sakagami.html`
stub.

The first build exposed that as a duplication: a ledger creates a page by its
file stem, so `ledgers/people/sakagami-sensei.md` produced a second page beside
the roster page and the site briefly held 163 pages with the same teacher on
two of them. The fix was the identifier, not the renderer — the ledger was
renamed to `sakagami.md` with `char_id: sakagami`, the roster name kept the
page, and the stub's "nothing has been read yet" copy was replaced by the
chapter's rows. The rebuild settled at 162 pages.

The wording gate caught the chapter's own phrasing once: "the walk out" appeared
in one scene heading and in the volume's Chapter 6 paragraph, and the checker
read it as pipeline vocabulary in reader copy. Both were rewritten as "leaving
the hearing" / "on the way out"; the checker was not loosened. A second leak
class — quoted lines from other characters sitting in a character's [says] rows —
was caught by review rather than by a gate: Kushida's p.191 send-off had been
recorded under Horikita and Sudō and was converted to [note] in both files
before it could render as their speech.

Counts after the rebuild, against the Chapter 5 commit: 161 → **162** pages,
search records 778 → **793**, site links 18283 → **18870** checked with 0 bad,
cross-page `a.cite` links 1089 → **1209**, plain `.pageref` references 6075 →
**6908**, `details.citebox` still 0. Print bundles: guides 22, **people 153**
(was 145), school 46, **story 172** (was 167), **topics 230** (was 209), world
34 pages; print links 8933 → **9348** checked with 0 bad. Determinism
re-measured across two consecutive builds:
`4d4c5047d6dcf80f90afad6178a91bda`, and `--docs` mirrors to the same tree
(173 files). The hash moved once mid-chapter, from
`1d13757fddce1fb2e377854b95c65fc4`, when the audit found that Ike's and
Yamauchi's p.190 glance at Sakura had been left only in Sakura's own page; two
rows went into each of their ledgers and the site re-measured clean.

Render locations checked rather than assumed: the Sakura, Horikita, Ayanokōji,
Sudō, Ichinose, Chabashira and Manabu blocks go to their own pages under
`people/`; Kushida and Hoshinomiya stay on theirs with small sections;
Kanzaki's rows aggregate into `people/minor/k.html`; Tachibana renders at
`people/tachibana.html`; Sakagami's rows replaced the mention stub at
`people/sakagami.html`; the Chapter 6 narrative section renders at
`story/v/y1v2/index.html` and aggregates into `topics/relationships.html`,
`topics/results.html`, `topics/who-knew-what.html` and `topics/expulsions.html`.
Full gate: `share_check --site --print --pdf` all checks passed.

### Chapter 7 ships, and a principal character stops being an empty page (site, 2026-10-27)

Chapter 7 went in as one volume section plus thirteen ledgers' worth of scene
rows, and it added no pages. `ledgers/people/ryuuen-kakeru.md` used the roster id
that already owned `people/ryuuen-kakeru.html`, so the page count stayed at 162
and the change was a replacement instead of a duplication: the lede that read
"Nothing about Ryūen Kakeru has been read line by line yet. This encyclopedia
only publishes what someone has read and anchored to a page…" gave way to two
anchored sections, "Ch.7 sec. 7.4: named before he is seen" (p.241) and "Ch.7 sec. 7.6:
the boy in the corridor" (pp.254–255). He is grouped as a principal character in
the People rail, not a minor page, because the roster puts him in a top tier — the
same rule that sent Kanzaki to `people/minor/k.html` does not apply to him.

The chapter's evidence spread further than any earlier one, because the retrial is
a cast scene: Chabashira's lecture and her private "defective products" session
land on her page (35 rows), Manabu's secretary offer on his, Sakagami's loss of
his students on his, Tachibana's one open seat on hers, Sudō's first penitent
answer on his, and the camera purchase on `systems/point-economy`, which renders
inside `school/system/private-points.html` rather than as its own page.

Attribution fixes made before the build, all of them found by re-reading the
pages and none by a checker: an untagged p.222 line and an untagged p.220 pair
came out of two characters' `[says]` rows and into `[note]` rows plus the volume's
gap list; Sakura's "That's…" (p.238) moved to Ayanokōji, whose hesitation the
page actually narrates; and "I'm done talking." was re-anchored from p.255 to
p.254. Five spoken lines the chapter gives these characters had no row at all and
were added.

Counts after the rebuild, against the Chapter 6 commit: 162 pages (unchanged), all
reachable, max depth 3, 27 principal characters, 253 people in the index; search
records 793 → **795**; site links 18870 → **19216** checked with 0 bad; print
links 9348 → **9691** checked with 0 bad; cross-page `a.cite` 1209 → **1305**;
plain `.pageref` 6908 → **7671**; `details.citebox` still 0; wording leaks 0.
Print bundles: guides 22, **people 158** (was 153), **school 47** (was 46),
**story 176** (was 172), **topics 247** (was 230), world 34 pages. Determinism
re-measured across two consecutive builds:
`5f140106f5bd2b1527b2f5a11bf071a5`, and `--docs` mirrors to the same tree
(173 files).

Render locations checked rather than assumed: all sixteen labelled bullets of the
volume's Chapter 7 section reach `story/v/y1v2/index.html` (the checker was asked
for every bold label in the section and only "Narrative Beats", the container
heading, is not a rendered label), and its seven beats 7.0–7.6 are present there;
"Only One Solution", "The trap in the corridor" and "declaration of war from some
guy" appear on the volume page, on the Ayanokōji and Ryuuen pages, and in
`topics/results.html` and `topics/who-knew-what.html`; "Get to know the person
called Ayanokouji" appears on `people/chabashira-sae.html` as well as the volume
page. Full gate: `share_check --site --print --pdf` all checks passed.

### The Postscript closes Volume 2 on the site (site, 2026-10-27)

Four pages of author afterword went onto `story/v/y1v2/index.html` as a
Postscript section, and nothing else on the site changed, which is the correct
result: the afterword states no character fact, so it fans out to no person page.
The volume page picked up all eight of its labelled bullets — verified by asking
the built HTML for every bold label in the section, with only the container
heading "Narrative Beats" not rendered as a label — including "disturbance
centered on Sudou", "high-class yakiniku", "PlayStation 4" and the note that
p.261 carries only the publisher's newsletter notice.

Counts after the rebuild, against the Chapter 7 commit: 162 pages (unchanged),
search records 795 (unchanged — afterword bullets are not indexed as records),
site links 19216 and print links 9691, both 0 bad, `a.cite` 1305, `.pageref`
7671, `details.citebox` 0, wording leaks 0. Print bundles: guides 22, people 158,
school 47, **story 178** (was 176), topics 247, world 34 pages. Determinism
re-measured across two consecutive builds:
`858b6761bd5a0a5c7e9f4e847fd39954`, and `--docs` mirrors to the same tree
(173 files). One quote was corrected before the build: the printed biography says
"Primarily responsible for the scenario and PC game planning", and the section had
quietly lower-cased the first letter.

Year 1 Volume 2 is now fully walked on the site: pp.10–261, seven chapters and the
afterword, with the volume page reporting the whole run.

---

### Dark mode made readable, and a finished volume stopped calling itself unfinished (site, 2026-10-28)

Two defects fixed before the next volume opens.

**Dark mode painted light chrome on the dark bar.** The masthead controls
(`#menu`, `#theme`, the `<select>`) are `.icon-btn` with a hardcoded
`background: #f4f6fb` and `color: var(--ink)`; in dark mode `--ink` flips to a
light colour, so every masthead button became light-text-on-near-white and
vanished. They sit on the dark brand bar in both themes, so the fix flips their
own surface with the theme — `[data-theme="dark"] .mast-tools select,
[data-theme="dark"] .icon-btn { background: var(--panel-2) }`, and the same for
`:hover`. Separately, the per-section `--hue-soft` tints are light-mode values
set on `body`, which outranks the dark value on `:root`, so taglines, rail
hovers and table rows kept painting light-on-dark. One rule lets every section
take the root tint back: `[data-theme="dark"] body[data-section] { --hue-soft:
#1d2637 }`. Verified by rendering dark copies of `people/index.html` and
`people/minor/i.html` with the theme forced on: masthead buttons, search box,
tagline and cards all read correctly against the bar now.

**A volume with a Postscript stamp is complete, whatever its chapter count.**
`walk_state` in `kb/site_data.py` was calling a volume evidence-complete on a
hard-coded `len(chapters) >= 8`. y1v2 has seven chapters, so a fully walked,
`→ DONE`-stamped volume was publishing itself as "Partway" in the coverage
table. The rule now keys on the closing boundary stamp the walk actually writes
(`volume_walk_complete`), not on a count: y1v1 and y1v2 report "Transcribed line
by line" and the 34 unwalked volumes stay "Records only".

Counts after the rebuild: 162 pages, 19216 site links and 9691 print links
checked, both 0 bad; search 795 records; `details.citebox` 0; wording leaks 0.
Print bundles unchanged (guides 22, people 158, school 47, story 178, topics
247, world 34 pages; topics.pdf 3753 → 3752 KB). Deterministic tree hash across
two consecutive builds: `8f6caaeef2a776051ce3cdb2b0b3ecf7`, moved from
`858b6761bd5a0a5c7e9f4e847fd39954` by these two fixes; `--docs` mirrors to the
same tree (173 files). No ledger changed, so the quote verifiers were not
re-run.

---

## HANDOFF — site state and the exact next steps (updated 2026-10-28, y1v2 closed)

**Built state right now.** 162 pages, all reachable, max depth 3, 36 volume
pages, 27 principal characters, 253 entries in the People index. Search index 795
records, 0 bad. Site links 19216 checked, 0 bad. Cross-page `a.cite` 1305, plain
`.pageref` 7671, `details.citebox` 0, wording leaks 0, nested chips 0,
disclosure-rule violations 0, role-grouping problems 0, curated-typing leaks 0.
Print bundles: guides 22, people 158, school 47, story 178, topics 247, world 34
pages; print links 9691, 0 bad. Deterministic tree hash across consecutive
builds: `8f6caaeef2a776051ce3cdb2b0b3ecf7`; `docs/` mirrors it exactly (173
files). **y1v2 is fully walked** — its volume page carries Chapters 1–7 and the
Postscript; y1v1 is likewise complete; the other 34 volume pages are stubs and
are the work ahead, one chapter at a time.

**Commands.** Full rebuild: `python3 kb/build_share_site.py` (prints page,
record, bundle and pdf counts). Mirror to the published tree: `python3
kb/build_share_site.py --docs` — this copies `share/site` → `docs/` and rebuilds
nothing, so it must always follow a full build. Gate: `python3 kb/share_check.py
--site --print --pdf`. Determinism: `md5_tree(Path('share/site'))` from
`kb/share_check.py`, twice, on two consecutive builds.

**How a character gets a page, learned the hard way twice.** Page identity comes
from the roster (`cote_kb.db` characters) or, failing that, from the ledger file
stem: `collect_metas` in `kb/build_share_site.py` takes roster ids in tiers 1–2
and then adds every `ledgers/people/<stem>.md` stem. So a new ledger named
`sakagami-sensei.md` sits beside the roster's existing `people/sakagami.html`
and the site holds the same teacher twice (it did, at 163 pages, for one build).
Name new ledgers with the roster id when one exists; rename the ledger instead
of special-casing the renderer. Minor characters without their own page
aggregate into `people/minor/<initial>.html` — Kanzaki, Ike and Yamauchi render
there, and a page count that does not move after a chapter usually means the
evidence landed on an aggregate page, not that it vanished.

**What does not render.** `ledgers/places/*` and `ledgers/systems/*` are keyed to
DB-curated rows (`loc_rows`, `system_rows`); a new file in those directories with
no matching curated row produces no page at all. Do not create one to hold new
facts — put place facts in the people/volume rows and system facts in the
volume section's "New system facts" line, and only add a places/systems ledger
when the curated row is being added too. (`ledgers/places/club-activities-
building.md` was written and deleted for exactly this reason.)

**Renderer rules already fixed, do not reintroduce.** `kb/site_sections.py`
emits chapter blocks without length caps — a dropped bullet is a dropped claim,
and both `extras` and `beats` print in document order. Page numbers stay visible
but are only links when clicking does something; the citation chip surface is
gone and `details.citebox` must stay at 0. One disclosure per region: a scene or
ledger expander may not be duplicated by a chip. The wording gate's regex is
part of the contract: rewrite the copy, not the checker (Chapter 6's "the walk
out" became "leaving the hearing" for this reason).

**Per-chapter site check, in order.** Rebuild → `--docs` → `share_check --site
--print --pdf` → two consecutive `md5_tree` values equal → grep the changed
`docs/**.html` for a distinctive phrase from each new section to prove it
rendered where intended → only then write the progress entries with the measured
numbers, never estimated ones.

**Deploy.** Push `main`; the remote redirects to `FakeUser2121/cotedb` and
Cloudflare serves the site. The repository is deliberately private and the
github.io site is deliberately dead; there is no URL to quote back to the user.

### y1v3 Chapter 1 ships as the volume's first recorded scene (site, 2026-10-29)

Volume 3's ledger and Chabashira's cold-open soliloquy (pp.10–12) reached the
site: 169 pages, 34 assets, search index rebuilt, story/v/y1v3 now a real
volume page rather than a stub. R18 wording fired once on the first build
("ledgers" served on the volume page) and the row was rewritten; the second
build is clean, the ratchet unchanged (R19 warn 82/82). Determinism hash
across consecutive builds: `ffb110dbfa0c9e5b77d50c2a721af34c`. Quotes: 12
non-says spans, 0 [says] lines (the chapter is narration), all corpus-exact.

### y1v3 Chapter 2 reaches the site (site, 2026-10-31)

Island-test chapter (pp.13–99) shipped: nine scene sections on the volume
page, seven new people pages (Mashima, Katsuragi, Totsuka, Ibuki, Shinohara,
Yukimura, Satō), twelve existing people pages extended. 169 pages, 34 assets,
search index rebuilt. Eight non-says quote fixes and one wording rewrite
("ledgers" → "pages") before the clean build. Ratchet unchanged (R19 warn
82/82). Determinism hash across consecutive builds:
`7a491addc20cdacda7c0c1e6579bcda6`. Quotes: 144 non-says spans, 20 [says]
lines, all corpus-exact.

### y1v3 Chapter 3 reaches the site (site, 2026-11-01)

Rivals chapter (pp.100–130) shipped: the volume page carries its third
chapter section, two new people pages (Ibuki Mio, Totsuka Yahiko), four new
directory rows (Kaneda, Ishizaki, Komiya, Kondō) and eight existing people
pages extended. 171 pages, 38 assets, search index rebuilt. No verifier
failures this chapter — the two multi-page quotes were split before the
first verify run. Ratchet unchanged (R19 warn 82/82). Determinism hash
across consecutive builds: `43a2996dce2fd75172d8f0b67ca6eff5`. Quotes: 166
non-says spans, 136 [says] lines, all corpus-exact.

### y1v3 Chapter 4 reaches the site (site, 2026-11-01)

Freedom chapter (pp.131–143) shipped: the volume page carries its fourth
chapter section and seven existing people pages extended (Ayanokōji,
Sakura, Katsuragi, Totsuka, Ike, Yamauchi, Hirata), with one new search
asset (Katsuragi). 171 pages, 39 assets, search index rebuilt. No verifier
failures — the cross-page shirt-bag quote was split before the first
verify run. Ratchet unchanged (R19 warn 82/82). Determinism hash across
consecutive builds: `569fe47fc33f4fbb4c8988bb61b308ef`. Quotes: 169 non-says
spans, 205 [says] lines, all corpus-exact.

### y1v3 Chapter 5 reaches the site (site, 2026-11-01)

Outbreak-of-War chapter (pp.144–158) shipped: the volume page carries its
fifth chapter section and six existing people pages extended (Ayanokōji,
Chabashira, Sudō, Horikita, Ichinose, Kanzaki). 171 pages, 39 assets,
search index rebuilt. One verifier failure fixed before ship — the
cross-page Chabashira verdict was split at the page footer and both
verifiers then passed. Ratchet unchanged (R19 warn 82/82). Determinism
hash across consecutive builds: `bc30cb4a31ca1991466b7947c4abac8a`. Quotes:
175 non-says spans, 283 [says] lines, all corpus-exact.

### y1v3 Chapter 6 reaches the site (site, 2026-11-01)

False-Teamwork chapter (pp.159–239) shipped: the volume page carries its
sixth chapter section and thirteen existing people pages extended
(Ayanokōji, Horikita, Ibuki, Hirata, Ike, Sudō, Yamauchi, Karuizawa,
Kushida, Sakura, Shinohara, Ryūen, Katsuragi) — Ryūen and Katsuragi on
scene only in the handover, an absence section for Shinohara. One new
people page with its search asset: Shinohara Satsuki. 172 pages, 40
assets, search index rebuilt. No verifier failures — both halves passed
on their first verify run. Ratchet unchanged (R19 warn 82/82).
Determinism hash across consecutive builds:
`4e963923c1d97350ce118e4bb3055eb0`. Quotes: 203 non-says spans, 928
[says] lines, all corpus-exact.

### y1v3 Chapter 7 reaches the site (site, 2026-11-02)

The-Curtain-Rises chapter (pp.240–258) shipped: the volume page carries
its seventh chapter section and thirteen existing people pages extended
(Ayanokōji, Horikita, Hirata, Sudō, Ike, Yamauchi, Karuizawa, Ryūen,
Kōenji, Chabashira, Katsuragi, Totsuka/Yahiko, Ibuki) — Mashima and
Kaneda recorded in ledgers only, no new people pages. 172 pages, 40
assets, search index rebuilt. Two cross-page sentences were left
unquoted after the first verify run (pp.253–254, 255–256); one R19
regression caught before ship — the handshake narration carried second
person outside quote marks and was wrapped in them, ratchet restored to
R19 warn 82/82. Determinism hash across consecutive builds:
`5114f99ae30bc4f68a9f15b7810edd09`. Quotes: 233 non-says spans, 1264
[says] lines, all corpus-exact.

### y1v3 Chapter 8 and the volume close reach the site (site, 2026-11-02)

The postscript section (pp.259–262) shipped on the volume page with its
closing stamp — Year 1 Volume 3 now reads as complete (the y1v2
postscript-DONE pattern). No people pages changed for the postscript;
one people page changed overall: Totsuka/Yahiko extended by the p.252
retelling section added at the coverage gate. 172 pages, 40 assets,
search index rebuilt. Quotes: 241 non-says spans, 1264 [says] lines,
all corpus-exact after one first-run fix (the bios quote had imported
the y1v2 wording; the corpus prints "Primarily responsible for
scenario and PC game planning" without "the"). Coverage gate over the
full roster: all real locator hit pages cited, 15 substring-collision
ids discarded with evidence, no content/*.tsv change. R19 ratchet holds
at 82/82. Determinism hash across consecutive builds:
`5ad45779effcb8153e1f603096d13b84`.

### Sakayanagi's page comes alive (site, 2026-11-02)

Owner overrode the wait-at-first-scene convention: her ledger opened
with y1v3's four mention pages, so `docs/people/sakayanagi-arisu.html`
(upgraded in place from the roster stub) now carries four scene cards
(cave-mouth naming, the path correction, the beach absentee read, the
handover argument) and her search/person asset was added — 172 pages,
41 assets. Her cross-volume topic links (relationships, who-knew-what)
re-rendered accordingly. Quotes: 244 non-says spans, 1268 [says] lines,
all corpus-exact. R19 ratchet holds at 82/82. Determinism hash across
consecutive builds: `cad4562da7d06fb9aea02e2ed02ef868`.

### Totsuka's alias reaches the site (site, 2026-11-02)

`yahiko` joined the roster row's aliases cell, so his people page now
shows "Also written: yahiko" and the search index folds the form;
the rebuild is otherwise identical — 172 pages, 41 assets. Quotes:
244 non-says, 1268 [says], all corpus-exact. R19 holds at 82/82.
Determinism hash across consecutive builds:
`7f6fd436a889ba9afdab57a9bc545155`.

### y1v4 Chapter 1 reaches the site (site, 2026-11-03)

The cold-open soliloquy (pp.10–11) shipped as the first section of the
new Year 1 Volume 4 page (`docs/story/v/y1v4/index.html`), with
Karuizawa's people page extended by its first y1v4 section — 172 pages,
42 assets, search index rebuilt. Quotes: 13 non-says spans, 0 [says]
(the chapter has no dialogue), all corpus-exact after one first-run fix
(the class line prints "boys or girls", not "and"). R19 ratchet holds at
82/82. Determinism hash across consecutive builds:
`ee21f656d3ea278b734a18cd864dbf63`.

### y1v4 Chapter 2 reaches the site (site, 2026-11-03)

The Summer Group Test (pp.12-62) shipped as the second section block of
the Year 1 Volume 4 page: 21 people ledgers extended (sotomura-hideo
opened, yukimura-teruhiko and mashima-tomonari among them) — 173 pages,
44 assets, search index rebuilt with the hand-logged `The Professor`
alias. Quotes: 167 [says] spans (1 skipped as too short) and 69 non-says,
all corpus-exact after three cross-page fixes (y1v4 `Page N` footers do
not strip in the verifiers; trim or `…`-split). R19 ratchet holds at
82/82; R18 back to 0 after removing "ledger" from three rows and quoting
the p.13 "little devil" line. Determinism hash across consecutive builds:
`49c55c22ec9ec301ffac9d1b2d5c5e29`.

### y1v4 Chapter 3 reaches the site (site, 2026-11-04)

The café, Rabbit room and night deck (pp.63-124) shipped as the third
section block of the Year 1 Volume 4 page: 21 people ledgers extended,
three opened this chapter (machida-kouji, hamaguchi-tetsuya,
manabe-shiho) — 177 pages, 48 assets, search index rebuilt with the new
Yashima Mariko roster row. Quotes: 479 [says] spans (10 skipped as too
short) and 161 non-says, all corpus-exact after fourteen first-run fixes
(nine cross-page in half one — y1v4 `Page N` footers do not strip in the
verifiers; five in half two plus the volume-file paraphrase-in-quotes).
R18 back to 0 and R19 ratchet holds at 82/82 after removing "dossier"
from three rows and a prose "your" from Ayanokōji’s VIP trait row.
Determinism hash across consecutive builds:
`72491977fbf49c39926376ce9cf0cda4`.

### y1v4 Chapter 4 reaches the site (site, 2026-11-04)

Double Question (pp.125-204) shipped as the fourth section block of the
Year 1 Volume 4 page: 30 people ledgers extended, six opened this
chapter (morishige, takemoto, yamashita, yabu, morofuji, sugimura) —
177 pages, 48 assets, search index rebuilt. Quotes: 844 [says] spans
(26 skipped as too short) and 239 non-says, all corpus-exact after
thirteen first-run fixes (six cross-page … splits, four exact-substring
corrections including “so late” and “didn’t she?”, one note rewrite).
R18/R19 held at 0/82 with no wording churn. Determinism hash across
consecutive builds: `6682b58f7d27f9fb0b6c434dee5845fb`.

### y1v4 Chapter 5 reaches the site (site, 2026-11-04)

Each and Every Difference (pp.205-243) shipped as the fifth section
block of the Year 1 Volume 4 page: 22 people ledgers extended, one
opened this chapter (beppu-ryouta) — 177 pages, 48 assets, search
index rebuilt. The chapter carries the email-show Outcome #1 plan,
Ichinose’s call-and-SIM dismantling of the double swap (real VIP
Karuizawa), and the sec. 5.3 café results (Class C +150 cl / +5.5M pr;
Ryuuen’s Kushida reveal and next-target threat). Quotes: 1074 [says]
spans (31 skipped as too short) and 314 non-says, all corpus-exact
after six first-run fixes (four cross-page … splits, two exact-text
corrections). R18/R19 held at 0/82 with no wording churn. Determinism
hash across consecutive builds: `03811810f8fa172c42a189cf2c5f6c55`.

### y1v4 Chapter 6 reaches the site (site, 2026-11-04)

Postscript (pp.244-248) shipped as the sixth section block of the Year
1 Volume 4 page — author note, Volume 5 tease, engagement trivia and
the Kinugasa/Tomoseshunsaku bios. No roster characters, so no people
ledgers touched; 177 pages, 48 assets unchanged in count. Quotes: 1074
[says] + 316 non-says, all corpus-exact. R18/R19 held at 0/82.
Determinism hash across consecutive builds:
`29604b69da3781b89e6104819458ef95`.

### y1v4 volume-end coverage gate reaches the site (site, 2026-11-05)

The full-roster gate closed: 30 people ledgers gained hand-written
mention rows (605 lines), three characters crossed the scenes
threshold and gained pages (morishige-takurou, morofuji-rika,
takemoto-shigeru) — 180 pages, 51 assets, search index rebuilt. A
mid-gate R19 regression (82 → 142 second-person hits in unquoted
reported speech) was repaired by rewriting twenty rows to third
person; three speaker corrections rode along (p.13 Hirata, pp.171/178
Ayanokōji) plus three speaker identifications (p.65 Horikita, p.188
Manabe, p.198 Karuizawa) and the p.166 scene relabel. characters.tsv
andou-sayo and morofuji-rika alias cells extended. Quotes: 1074
[says] spans (31 skipped as too short) + 316 non-says, all
corpus-exact. R18/R19 held at 0/82 after the repair. Determinism
hash across consecutive builds:
`deae8e046450e1f875866cd52c55febc`.

### search: fuzzy matching and focus preload reaches the site (site, 2026-11-05)

Search Tier 2/3: the index preloads on focus instead of on the first
keystroke, and every exact miss — global query, character scoping,
scene filter, people directory — now falls back to edit-distance-1
variants (4+ letter tokens, one-time word map; a scope resolves only
when exactly one roster id matches, so name isolation holds and
ambiguity falls back to global). Exact queries unchanged. Three typo
assertions added; the browser suite's stale hardcoded counts now derive
from the DOM and the payload file. make browser 25/25 (was 4 FAIL on
missing jsdom plus those counts), make check OK, gate exit 0; build 180
pages, 51 assets. Determinism hash across consecutive builds:
`251c3c38a7b4e2e11d99b2d66116a18c`.

### y1v4.5 Chapter 1 reaches the site (site, 2026-11-07)

The vignette collection opens: its one-page first-person frame (p.10)
becomes a scene on Ayanokōji’s page and the first chapter of the
Year 1 Volume 4.5 page, which turns from stub to partly read — 180
pages, 52 assets (the volume’s first scene payload). Quotes: 2
non-says spans, corpus-exact; R18/R19 held at 0/82. Determinism hash
across consecutive builds:
`31b9bbdd79993ecc0bd1d4b64778800d`.

### y1v4.5 Chapter 2 reaches the site (site, 2026-11-07)

The collection’s first full story (pp.11–48) lands as scene cards
across the roster: the invite chain, the couples-only floor, Ibuki’s
queue talk and the awareness lecture, the reading with Ukon’s fate
tenchuusatsu pronouncement, the trapped elevator, and Katsuragi’s
thanks. Ukon gains a directory presence from the new file; the volume
page turns from one chapter to two. Quotes: 46 [says] + 48 non-says
spans, corpus-exact; R18/R19 held at 0/82. Determinism hash across
consecutive builds:
`ddd34299d8ca9caacfd9a80af72c6aa3`.

### y1v4.5 Chapter 3 reaches the site (site, 2026-11-07)

The birthday-detective chapter (pp.49–107) lands as scene cards across
the roster: the pooled gift and Shinohara blowup, the room birthdays and
February 15, Manabu's crossroads interception and vice-president offer,
the chocolate-shelf cleanup, the bench talk with Horikita, the student
council refusal and the twin-sister reveal, Sudou's 100,000-point run,
and the closing party-popper section from Katsuragi's viewpoint.
Inogashira Kokoro, Nagumo Miyabi and the Student Council Room gain
ledger-backed directory presences from new files. Quotes: 349 [says] +
57 non-says spans, corpus-exact; R18/R19 held at 0/82. Determinism
hash across consecutive builds:
`a4367c75078ad5c359625972ec57080a`.

### y1v4.5 Chapter 4 reaches the site (site, 2026-11-07)

The water-outage chapter (pp.108–131) lands as scene cards across the
roster: the turtle parable, the stuck water bottle, the dry sources,
the Kushida grudge with the ship-exam recap, the corridor run past
Maezono and Kushida, the elevator with Kouenji, Sakura's water, and the
ending where Ayanokōji tests the same bottle on himself. Maezono, the
Cruise Ship Exam, the Cafeteria and the Dormitory gain ledger-backed
directory presences from new files. Quotes: 447 [says] + 58 non-says
spans, corpus-exact; R18/R19 held at 0/82. Determinism hash across
consecutive builds:
`ec89b51796f06012fa6aa88093943f2d`.

### y1v4.5 Chapter 5 reaches the site (site, 2026-11-07)

The love-letter chapter (pp.132–152) lands as scene cards across the
roster: Yamauchi's printed letter and delivery plan, the handover
behind the school building, the midnight call, the rain-soaked
confession and rejection, and the phone loan that closes it. The School
Building gains a ledger-backed directory presence from a new file.
Quotes: 539 [says] + 58 non-says spans, corpus-exact; R18/R19 held at
0/82. Determinism hash across consecutive builds:
`8a0bb5345101c36556e7f772ea5c09f2`.

### y1v4.5 Chapter 6 reaches the site (site, 2026-11-07)

The gathering chapter lands as scene cards across the roster: the
rest-area deal and the clay self-model, the coerced lobby attendance,
Nagumo's first appearance with the student-council history, the
volleyball bet and Sudou's wall, the plastic object and the pool shove,
the ice cream stop, and the sunset walk. Convenience Store and
Swimming Pool gain ledger-backed directory presence; Shibata Sou gets
a first file. Quotes: 718 [says] + 63 non-says spans, corpus-exact;
R18/R19 held at 0/82. Determinism hash across consecutive builds:
`f66222d80c77fc6cf6bdf2f7def67566`.

### y1v4.5 Chapter 7 reaches the site (site, 2026-11-07)

The extra-stories chapter lands as scene cards: Operation Delta's
pitch and the Professor's map, the locker-room execution, the girls'
side of the recording with Karuizawa's card swap, and the empty-folder
payoff. Sonada and Ishikura get first files. Quotes: 776 [says] + 65
non-says spans, corpus-exact; R18/R19 held at 0/82. Determinism hash
across consecutive builds: `cef5f60f91273bd2ffaed86780e83237`.

### y1v4.5 Chapter 8 (Postscript) reaches the site (site, 2026-11-10)

The author’s afterword ships as the volume’s closing section, with
Ayanokōji and Ichino Yuyu passing mentions and the closing DONE stamp
in the volume file. Quotes unchanged at 776 [says] + 65 non-says,
corpus-exact; R18/R19 held at 0/82. Determinism hash across
consecutive builds: `1ba241f64ee5c8a97153336ceb17073b`.

### y1v4.5 volume-end coverage gate reaches the site (site, 2026-11-11)

The volume closes with the coverage-gate fill: passing-mention sections
for 20 characters land on their pages — Manabu's council mentions,
Suzune's queue and outing runs, Katsuragi's gift-hunt margins,
Yamauchi and Sakura's letter plan, and the rest — plus a first file for
Tomose Shunsaku from the postscript credits. Shibata Sō crosses the
scenes threshold and gains a page; Nagumo Miyabi and Shibata Sō gain
search assets. Quotes unchanged at 776 [says] + 65 non-says,
corpus-exact; R18/R19 held at 0/82. Determinism hash across
consecutive builds: `32205736de3595c8d44eca7197f4fe2a`.

### y1v5 Chapter 1 reaches the site (site, 2026-11-11)

The new volume opens on the site with Sudou Ken’s soliloquy as its
cold-open scene card and a new Year 1 Volume 5 story page. Quotes: 8
non-says spans, corpus-exact; R18/R19 held at 0/82. Determinism hash
across consecutive builds: `3799ce92a44fe3385b66dab7a958d50d`.

### y1v5 Chapter 2 reaches the site (site, 2026-11-11)

The sports festival fills the volume page: the rules briefing, the
assembly with Sakayanagi’s introduction and Ryuuen’s walkout, and the
gate warning all appear as scene cards; Fujimaki and the Sports Festival
exam gain their ledgers (both directory-level so far). Quotes: 91
[says] and 18 non-says spans, corpus-exact; R18/R19 held at 0/82.
Determinism hash across consecutive builds:
`211625d520c12d9eb5b3b4697d06103b`.

Chapter 3 fills the homeroom strategy scene (the blackboard vote and the
16–13 split), the entrance betrayal warning, and the grip-strength roster;
five more Class 1-D classmates gain directory-level ledgers (Onodera,
Hondō, Miyamoto, Miyake, Mori). The class point compromise joins the
private-points rules; the four-way tug-of-war and the rock-paper-scissors
staffing join the Sports Festival exam. Quotes: 125 [says] and 78 non-says
spans, corpus-exact; R18/R19 held at 0/82. Determinism hash across
consecutive builds: `bfc0ce9e40792479cf8bbc9187ba29f1`.

Chapter 4 carries the practice arc onto the volume page: the watching classes,
the name bet, Sudou’s leadership week, and Ayanokōji’s three-legged lesson
with the two named problems (Horikita’s partnerships, Kushida’s darkness).
Inogashira gains her first y1v5 rows; Katsuragi and Ryuuen record the
Class A/B/C positioning from the field. Quotes: 131 [says] and 118 non-says
spans, corpus-exact; R18/R19 held at 0/82. Determinism hash across
consecutive builds: `84cb0fa45e1f945543e8a69c9d0083c2`.

Chapter 5 puts the spy outing and the anchor reveal on the volume page: the
cruise-ship theory, Nagumo’s practice-pitch introduction, Kushida’s “It’s
me,” and Horikita’s brother reason. Nagumo and Shibata gain y1v5 sections
(both previously directory-level for this volume). The Sonoda ambiguity on
p.79 stays open in the attribution gaps. Quotes: 141 [says] and 181 non-says
spans, corpus-exact; R18/R19 held at 0/82. Determinism hash across
consecutive builds: `fd05909784782d880bf27cb7bbdc344b`.

Chapter 6 carries the full morning half of the sports festival onto the
volume page: dash through lunch, the Kinoshita fall, Class C’s cavalry crush,
Sudou’s punch and the cover, and Ayanokōji’s weapon speech. Six new people
ledgers open (Hashimoto, Yamada, Nomura, Suzuki, Yajima, Kinoshita); Ishizaki
and Kondō gain first y1v5 sections as cavalry horses. A duplicated Chapter 6
block in the volume ledger was removed before the second-half write-up.
Quotes: 301 [says] and 199 non-says spans, corpus-exact; R18/R19 held at
0/82. Determinism hash across consecutive builds:
`919b2428e7ea373295286796ebc08a4b`.

Chapter 7 puts the sports festival on hold for the false-injury trap:
Chabashira relays Kinoshita’s claim, Ryuuen prices a million points and a
kneel, and Horikita pays for strategy alone before finding her brother at
the entrance. Tachibana gains a first y1v5 section as passing mention with
the president. The append path briefly wrote a second ledger header into
eight people files; those headers were removed before shipping. Quotes:
425 [says] and 204 non-says spans, corpus-exact; R18/R19 held at 0/82.
Determinism hash across consecutive builds:
`a6497eb8051f36898e69ec9702eccd44`.

Chapter 8 is the ally chapter: the scavenger hunt, Sudou’s lobby
confession, Kushida exposed as the leaker who wants Horikita expelled, and
the elevator bargain that gives Horikita her first ally outside basketball
and her brother. Twelve people ledgers grow; the volume Chapter 8 heading
carries a quoted title to keep R19 at baseline. Quotes: 538 [says] and
206 non-says spans, corpus-exact; R18/R19 held at 0/82. Determinism hash
across consecutive builds: `7137b59766f8c38d10f5167421302f36`.

Chapter 9 is the turning point: the 1200-metre relay with Ayanokouji as
anchor and Horikita Manabu’s standing challenge, the first-name bargain
with Sudou, and the hallway where Horikita faces Ryuuen and Kushida —
until a counter-recording of Ryuuen’s own trap plan arrives. Sakayanagi
names the White Room at the special building. Kamuro Masumi’s ledger
opens (roster row pre-existed). Eighteen people ledgers grow; one volume
section. Quote rows converted where lines were under ten characters or
spanned the p.203–204 page break; R18 cleared by rewording one unshipped
volume line. Quotes: 697 [says] (2 too short/skipped) and 212 non-says
spans, corpus-exact; R18/R19 held at 0/82. Determinism hash across
consecutive builds: `860cec3a25ebfa4a6e3aaca3681dd1e3`.

Year 1 Volume 5 closes with the postscript and the volume-end coverage
gate. The locator’s hit pages are compared against every roster cell that
carries y1v5; twenty-seven people ledgers gain grouped passing-mention
sections so each named page has an entry. Ambiguities stay in the volume
notes rather than being guessed: Sonoda-kun on p.79, the two Onodera rows,
Kamuro’s surname-only absence, and Atsuomi’s zero hits. Quotes: 697
[says] (2 too short/skipped) and 251 non-says spans, corpus-exact;
R18/R19 held at 0/82. Determinism hash across consecutive builds:
`76e9e5764687d3400ee0e9c044e103a3`.

Year 1 Volume 6 opens with a four-page interior monologue. The volume
ledger is created with the chapter-1 section; Kushida and Horikita gain
their first y1v6 blocks. Quote hygiene: 6 [says] spans (none too short)
and 7 non-says spans, corpus-exact; R18/R19 held at 0/82. Determinism
hash across consecutive builds: `620b39f6c8f086e584418aa61b1275cf`.

Year 1 Volume 6 chapter 2 runs sixteen pages across ceremony, classroom,
gym passage, corridor and dorm call. Nineteen people ledgers gain their
first or continuing y1v6 blocks with a single shared chapter stamp.
Quote hygiene: 40 [says] spans (none too short) and 19 non-says spans,
corpus-exact; R18/R19 held at 0/82. Determinism hash across consecutive
builds: `c97c59ab5fd290194fcb0b0f5ddb57cc`.

Year 1 Volume 6 chapter 3 is thirty pages across briefing, detour and
café. Nineteen people ledgers gain blocks (four first y1v6 headings).
Quote hygiene: 159 [says] spans (none too short) and 50 non-says spans,
corpus-exact; hyphenated “thank-you” proved the R19 \byou\b trap and was
reworded before ship. Determinism hash across consecutive builds:
`ee9036a4b4578c50d8b966d45e91ec92`.

Year 1 Volume 6 chapter 4 is sixteen pages of Class C’s meeting with no
Class D POV. Nineteen people ledgers gain blocks (ten first y1v6
headings; two new ledgers created for Nishino and Oda). Quote hygiene:
262 [says] spans (none too short) and 50 non-says spans, corpus-exact;
R18/R19 held at 0/82. Determinism hash across consecutive builds:
`012e79edde139ed439624bcf98b43625`.

Year 1 Volume 6 chapter 5 is fifty-six pages across exam teaming,
library sessions and the Kushida wager, written in two halves with
stamps only on the last file batch. Twenty-nine people ledgers gain
blocks (three new ledgers created for Hasebe, Ichihashi and Okiya);
Horikita Manabu named as the mathematics-bet witness pp.120–122.
Quote hygiene: 651 [says] spans (none too short) and 64 non-says spans,
corpus-exact; volume prose that said “ledger” was reworded before
ship and R18 returned to 0. Determinism hash across consecutive
builds: `2f738b9aaacb24c55f04f37f4b9178de`.

Year 1 Volume 6 chapter 6 is forty-five pages across the group’s
formation, the movie, the karaoke juice dump and Ryuuen’s signed fraud
letter, written in two halves with stamps on the last file batch.
Twenty-three people ledgers gain blocks; new ledgers for Shiina Hiyori
and Yoshimoto Kosetsu; first y1v6 headings for Komiya, Kondou,
Katsuragi, Hiyori and Yoshimoto. Quote hygiene: 895 [says] spans (8
too short) and 69 non-says spans, corpus-exact; “ledger” and a bare
“What are you?” outside quotes were reworded before ship. Determinism
hash across consecutive builds: `632cf1772c1ef4ec692d7a46f0462094`.

Year 1 Volume 6 chapter 7 is thirty-three pages across the envelope
counter, the exam days and the rooftop switch confession, written in two
halves with stamps on the last file batch. Eighteen people ledgers gain
blocks; first y1v6 heading for Sakagami. Quote hygiene: 1135 [says]
spans (18 too short) and 69 non-says spans, corpus-exact; three
cross-footer quotes were split at the page break before ship.
Determinism hash across consecutive builds:
`2cac97c2b888d1f4aaf4298a986c15e8`.

Year 1 Volume 6 postscript is two pages of newsletter signup with no story
beats, followed by the volume-end coverage gate: strict word-boundary
locator recheck for all 49 roster names, nineteen passing-mention sections
appended after the last chapter stamp, residual gap fill-ins, and a
Coverage-notes bullet for never-named or surname-only cases. R19 was
briefly at 86 after unquoted paraphrases; both were converted to
corpus-exact quoted lines and the count returned to the 82 baseline.
Missing chapter stamps were added across twelve people ledgers and the
volume closed with `postscript → DONE`. Determinism hash across
consecutive builds: `32cc51b89fef404700801208dbf6b93e`.

Year 1 Volume 7 opens with Ryuuen’s three-page childhood soliloquy and an
eighteen-page winter mall chapter: Ayanokōji’s informal group on class
points and Christmas, Class C’s surveillance, and a solo confrontation
with Kamuro that ends in mutual silence. The volume ledger is new; nineteen
people ledgers gain y1v7 blocks. Two quote defects were fixed before ship —
a cross-page line split on the footer page-number break, and a row that
fused two separate quotation pairs. Determinism hash across consecutive
builds: `44a56308272f08048317f4c56da39672`.

Year 1 Volume 7 chapter 3 spans sixty-six pages in two halves: the
library lunch and mastermind board, the father’s drop-out demand and the
butler’s suicide leverage, Chairman Sakayanagi’s admission revelations,
Chabashira’s unmasking, the final call cutting Karuizawa, Manabu’s
Nagumo warning, and a Sunday karaoke that ends with Ichinose and
Sakayanagi walking past. Three new people ledgers open for Atsuomi, Matsuo
and the full-name roster row. Determinism hash across consecutive builds:
`98a820dae80bbdfcae620c91c34e90f6`.

Year 1 Volume 7 chapter 4 is the rest-area insanity: Ryuuen’s classroom
raid smokes the Class D suspects into the open, Kouenji trades insults
while styling his hair, Sakayanagi recites the island contract and eats a
kick Hashimoto blocks, and the Dragon Boy leaves with his list narrowed to
the creep behind Horikita. Kitō Hayato opens a ledger for the white-glove
bodyguard. Determinism hash across consecutive builds:
`56d212bf5d41b6d17a9087cf7c70df6d`.

Year 1 Volume 7 chapter 5 is the winter-vacation rooftop trap: Ryuuen
sprays the single camera, summons Karuizawa under threat of her past,
and works her with buckets while Ibuki holds and Ishizaki fetches water;
her POV breaks under four dousings and the cruise-ship setup, then
refuses to say the name — “K-knock…it…off.” Determinism hash across
consecutive builds: `2eca4fc952f66af0ea617cc42cd3bdd3`.

Year 1 Volume 7 chapter 6 is intersecting thoughts on the winter-break
eve: Chabashira’s private-point test closes one system mystery, the mall
group walks while the rooftop trap runs, Ayanokōji proves X with Ibuki’s
camera story, then wins the brawl he planned and keeps Ryuuen alive as a
Class D tool after the tyrant transfers his points. Determinism hash
across consecutive builds: `13bd47a168a32c287a29f03204acc5f7`.

Year 1 Volume 7 chapter 7 is Ryuuen’s morning-after loss: Ibuki’s
800-million counter-check, the withdrawal forms he refuses to sign, and
Ayanokōji’s mirror of his own first week; the postscript teases the
third semester. Determinism hash across consecutive builds:
`154a3e9549268cedc52cf9a363f629dc`.

Year 1 Volume 7.5 is a three-day Christmas supplement: Karuizawa’s date
plan and Satō’s ask, Ayanokōji’s pharmacy bag and the Sakayanagi–Ichinose
pitch, Ibuki’s disastrous day, the double date and Nagumo’s arm-grab,
Satō’s honest rejection, the Manabu sibling reveal, Kiriyama’s burner-email
pact, and the cold-medicine gift that names Karuizawa “Kei.” Coverage gate
closed with passing-mention notes and volume-end FP list; postscript is
author note only. Determinism hash across consecutive builds:
`da14d05ffec87700cf7950cdfe2782ef`.

Year 1 Volume 8 chapter 1 is a single-page Horikita Manabu soliloquy at
graduation: he joined without ambition, played the role model, faced
Nagumo’s direct pressure until he stopped responding, and regrets never
making a friend he could trust — “this was just the beginning.”
Determinism hash across consecutive builds:
`ff885e45386a6bf8e77713e65226060b`.

Year 1 Volume 8 chapter 2 opens the Mixed Training Camp: the bus rules
briefing (multipliers, representative expulsion, solidarity, revocation),
Class C’s failed even-split, Matoba’s five-minute Class A pitch, four-class
group forming under Nagumo’s early draft, Fujimaki’s rebuke and the
Horikita–Nagumo average-score duel, Kōenji’s exposed twenty-million-point
Class A plan and refusal of the rep role, Yukimura’s reluctant nomination,
the dorm bed scramble, and the first shared cafeteria hour with Ichinose.
Determinism hash across consecutive builds:
`5997e7c2d301e09b4a0d3c0d87876371`.

Year 1 Volume 8 chapter 3 is the first full camp morning and evening: group
six’s dorm fight and Kōenji’s non-cooperation, the cleaning roster and zazen
dojo, breakfast rotation politics, PE, Sakayanagi’s bump and Ichinose-treasurer
rumor, and Nagumo’s marked-deck Old Maid. New entities onodera-sensei and
tsunoda. Determinism hash across consecutive builds:
`e38ba9d561822dbab7c36b032e959eb2`.

Year 1 Volume 8 chapter 4 runs from cook-duty fracture and Kiriyama’s
classroom confrontation through the bathhouse size contest (Sudou, Katsuragi,
Albert, Kōenji, Ryuuen’s chant trap) to Ayanokōji’s 1 a.m. “25” note and the
corridor meeting with Horikita Manabu on Nagumo and student-council exam
power. New entity wang-mei-yu. Determinism hash across consecutive builds:
`291c22d788b9db7ba36fc49470f0098e`.

Year 1 Volume 8 chapter 5 runs from Ichinose’s eleven-girl group roster and
Shiina’s volunteer representative turn through the girls’ night romance talk
to Ichinose’s soft-lie rule (“delaying the pain ’til later”). New entities
nishi-haruka, motodoi-chikako, rokkaku-momoe. Determinism hash across
consecutive builds: `fa8622c988de69a0d7746449928f62c6`.

Year 1 Volume 8 chapter 6 runs from the 18 km relay course walk and Kōenji’s
wild-boar detour through the Asahina Nazuna charm bargain on Nagumo to the
pitch-dark group talk that becomes the first real group night. New entity
asahina-nazuna. Determinism hash across consecutive builds:
`1dcb68fe8aded93c733229f0b33f43a7`.

Year 1 Volume 8 chapter 7 runs from the day-seven relay plan and Kōenji’s
bare-minimum bargain through Ichinose’s dinner tell and Tachibana’s courtyard
checkmate to Nagumo’s abstain demand and the Ayanokōji-name play in the
corridor. Determinism hash across consecutive builds:
`9803e29ef20bda01ea79f32a0d571e09`.

Year 1 Volume 8 chapter 8 runs from the dorm-room Suzune–Kushida
surveillance and oath argument through the knife metaphor to Kushida’s “last
time” exit and Suzune’s powerless choice of her over Ayanokōji. Determinism
hash across consecutive builds: `bc252f2a2f6455e6d268d431c6c720c4`.

Year 1 Volume 8 chapter 9 runs from the final-day briefing and random zazen
through the relay and Nagumo’s girls’ trap to the double lifeline and the
corridor debrief. Determinism hash across consecutive builds:
`d5387bc5902dc9a66455bd51db84f928`.

Year 1 Volume 8 chapter 10 is the author’s postscript; the volume closes
with a Postscript → DONE stamp. Determinism hash across consecutive builds:
`fc1ad251594d13137b2f5ed5c4a27fe6`.

Year 1 Volume 8 volume-end coverage gate closed: passing-mention sections
on 33 people pages plus volume Coverage notes; Rule 12 sample logged.
Determinism hash across consecutive builds:
`f752960a7db85214b9047146be63bf47`.

Year 1 Volume 9 walk opens with the prologue (Ichinose Honami’s
monologue and the Nagumo interview) plus chapter 1 (Sakayanagi’s
student-council audience; Kōenji’s private-point loophole; Kushida
outside the door). Determinism hash across consecutive builds:
`821788a175bd26046e4df316336227f4`.

Year 1 Volume 9 chapter 2 is the changing relationships chapter —
breakup, slander note, Yamauchi summons, and the Hashimoto–Kanzaki
gymnasium standoff. Determinism hash across consecutive builds:
`a871f9e0724a630d02f867b7afb1d312`.

Year 1 Volume 9 chapter 3 keeps the intention unchanged — Mii-chan’s
Hirata consultation, Hiyori’s offer, and the Ichinose–Horikita–
Ayanokōji meeting that ends in advice to do nothing. Determinism hash
across consecutive builds: `56c4e12bc682b46950105485effec166`.

Year 1 Volume 9 chapter 4 is the two secrets chapter — the criminal
letter in the mailboxes and Kamuro’s shoplifter confession with the
beer proof, closing on Manabu’s call about Kushida and Nagumo.
Determinism hash across consecutive builds: `f6ebafbfe3d02ea457fefaa960e9e8e6`.

Year 1 Volume 9 chapter 5 is the spreading-rumors chapter — the
provisional-test rules, Sudō’s study ask, Ichinose’s empty room and
Hashimoto’s shadowing tail ending at the elevator to Ichinose’s floor.
Determinism hash across consecutive builds: `27d39f3c798d24af40639d6f9733cb1d`.

Year 1 Volume 9 chapter 6 is the something-vague chapter — the tail turns
into a three-way confrontation, Ichinose answers her door sick, four
full-name forum rumors hit the provisional-exam morning, and the rumor
about Ayanokōji and Karuizawa becomes the cover both of them have to live
with.

Correction pass across the y1v4, y1v8 and y1v9 records — the class-letter
defects line now matches the corpus (Class C from the third semester,
Ryūen’s class now Class D), paste artifacts are gone, and the missed
promotion announcement at y1v8 p.13 is on both bus-briefing scenes and the
volume beats. Determinism hash across consecutive builds:
`3f6938d86bee3398f84ebb9f0f1f6231`.

Year 1 Volume 9 chapter 7 is the how-it-all-works chapter — the standoff’s
fallout, Hashimoto’s failed test, the mock-exam numbers, Sakayanagi’s
exam-eve timing, and Ichinose’s shoplifter confession to her whole class.
Determinism hash across consecutive builds:
`2e1d8cdb9fdba31f8b60985244261f7a`.
Year 1 Volume 9 chapters 8–10 (Epilogue + Short Stories) and volume-end
coverage gate. Epilogue: The Return (pp.176–225): Ichinose's confession,
Sakayanagi's attack, school rumor ban, ranking competition, Kushida
negotiation, rumor operation via Kiriyama, door conversations, exam day,
Valentine chocolate. Short Stories (pp.226–238): Kamuro's Intention,
Reliable Classmates (Satō), Sakayanagi's Preparations. Coverage gate:
all 51 roster characters checked, passing mentions recorded, closing
stamp added. Determinism hash across consecutive builds:
`8703cdda39e154c3aaf10f8287cf8199`.
Year 1 Volume 10 walk started: Prologue (pp.6–10), Chapter 1 (pp.11–29),
Chapter 2 (pp.30–84). Volume ledger created. Supplementary exam "The
Class Vote" announced (March 2, exam March 8). Determinism hash across
consecutive builds: `1a8afb9b6b224ad5ea2f225cf210ee72`.

Year 1 Volume 10 Chapter 3 (pp.85–147) walked. Class Poll politics:
Ichinose/Nagumo deal revealed, Sakayanagi targets Katsuragi. Determinism
hash: `5927541cbc7102484dbdcc91f173cf23`.

Year 1 Volume 10 Chapter 4 (pp.148–181) walked. Ayanokōji targeted in
Class Poll; Yamauchi/Sakayanagi identified as masterminds. Determinism
hash: `be8ab39d1e86f26dbe3599d47cc1e77b`.

Year 1 Volume 10 Chapter 5 (pp.182–237) walked. Horikita nominates
Yamauchi after Manabu meeting; class confrontation and Hirata collapse.
Determinism hash: `aaa0b75f5ebaa1f61be711b06f172d64`.

Year 1 Volume 10 Chapter 6 (pp.238–285) walked. Other classes’ strategies:
Ryūen accepts expulsion, Ichinose borrows from Nagumo, Sakayanagi targets
Ayanokōji via Yamauchi. Determinism hash: `7aa085ff7ff7095818de72975c7ca518`.

Year 1 Volume 10 completed (Prologue through Short Stories, pp.6–376).
Epilogue covers Class Poll expulsions and outcomes; volume closed with
coverage notes and DONE stamp. Determinism hash: `07c6b4817cdb3b08f1faf8f2ec1baee8`.

Year 1 Volume 11 walk started: Prologue (pp.7–12). Sakayanagi’s White
Room memory and Ayanokōji. Determinism hash: `6616223090c987c7e9262af9f554cf44`.

Year 1 Volume 11 Chapter 1 "The Teachers’ Battle" (pp.13–26) walked.
Tsukishiro imposes first-year exam changes; teacher conflict. Determinism
hash: `b4c834dcff42ea32623ae022084291ce`.

Year 1 Volume 11 Chapter 2 "The First Years’ Final Battle" (pp.27–54)
walked. Event Selection Exam rules and Ayanokōji named commander.
Determinism hash: `66e5f9106099b1fdbf430914a61305a7`.

Year 1 Volume 11 Chapter 3 "Opponents" (pp.55–92) walked. Class C vs
Class A matchup set; commander system explained; Kei meets Ayanokōji.
Determinism hash: `28193ff9b8eb1a3fdab81680d2764421`.

Year 1 Volume 11 Chapter 4 "What the Class Lacks" (pp.93–169) walked.
Class C struggles to prepare; Hirata isolates himself and Mii-chan keeps
reaching out. Determinism hash: `b425ad0e8e7356d8b96786004ee421d4`.

Year 1 Volume 11 Chapter 5 "A Trap, a Home-Cooked Meal, and a Favor"
(pp.170–280) walked. Class A events revealed; Horikita plans and
Ayanokōji/Keisei get predictions from Katsuragi. Determinism hash:
`d39733ac0f9d63dafc97764f8a00158c`.

Year 1 Volume 11 Chapter 6 "A Man’s Tears" (pp.281–317) walked.
Hirata confronts his past and returns to support Class C. Determinism
hash: `c4881954e6794ba9bd94fd940bc3153b`.

Year 1 Volume 11 Chapter 7 "Ayanokōji vs. Sakayanagi" (pp.318–367)
walked. First five exam events: Class C down 2–3 to Class A. Determinism
hash: `0daddbc64cd4f58f4327f68505e3dce0`.

Year 1 Volume 11 Chapter 8 "Class B vs. Class D" (pp.368–399) walked.
Ryūen leads Class D to a 4–2 victory over Class B. Determinism hash:
`95de910a6fb1594b45627d29a76c7bb9`.

Year 1 Volume 11 Epilogue "The Line Between the Winner and the Loser"
(pp.400–476) walked. Class A defeats Class C 4–3; Tsukishiro’s
interference revealed; Ayanokōji wins library rematch vs Sakayanagi.
Volume y1v11 completed with coverage notes and DONE stamp. Determinism
hash: `6bea783884c7cb8573db97157f0b718a`.

| y1v11.5 Prologue (pp.8-12) | 5 | 0 | 342aba6642427bb7cfbe092356ab20b9 |
| y1v11.5 Ch.1 (pp.13-120) | 108 | 0 | e5b41a99926b0436ec5c0f0ac722c58d |
| y1v11.5 Ch.2 (pp.121-143) | 23 | 0 | 46ca9d3997bf8a1c5f991590fea07c2f |
| y1v11.5 Ch.3 (pp.144-236) | 93 | 0 | 868ed83c02b68ae5db926b854d8de3ea |
| y1v11.5 Ch.4 (pp.237-295) | 59 | 0 | 28e7a1f600026c6322c783cf4b17b2aa |
| y1v11.5 Ch.5 (pp.296-351) | 56 | 0 | 76339b4b1acd8c2b015aa453bbfbd6ae |
| y1v11.5 Ch.7 Epilogue (pp.352-423) | 72 | 0 | ccae3b82136b217ee9e22dedb831af88 |
| y1v11.5 DONE | 423 | 0 | ccae3b82136b217ee9e22dedb831af88 |
| y1v11.75 Section (pp.1-18) | 18 | 0 | c94d311b46e7064be17d0bbb329e2f51 |
| y1v11.75 DONE | 18 | 0 | c94d311b46e7064be17d0bbb329e2f51 |
| y1v10 redo enrichment (Ch.4/Ch.6/Epilogue voice) | 473 | 0 | ac71ffe4c4cdd2f1ea2e2131a2abc5ef |
| y1v11 redo enrichment (Ch.2-Epilogue voice) | 234 | 0 | b62d2d58e58653f19323a801512a8084 |
| y2v1 Prologue+Ch.1+Ch.2 (pp.7-65) | 59 | 0 | 872eb01573a38ff441915291d1033211 |
| y2v12.5 (pp.8-216) | 216 | 0 | 5b6dc03f68a30257921993d2f04237bf |
| y3v1 (pp.10-287) | 287 | 0 | db6948f25f64cc3204eed2143f7a7156 |
| y3v2 (pp.10-263) | 263 | 0 | 73ad0bafe656a36a390cf0b4846ec97f |
| y3v3 (pp.12-256) | 256 | 0 | ae48217efe34306afdce69374fd25464 |
| y0 (pp.10-265) | 265 | 0 | 2ffa83b04525aafb7607bcb3bb843048 |
| y2v2 (pp.6-354) | 354 | 0 | 7aae5f31087696d44e35d66bc7c793c2 |
| y2v3 (pp.7-368) | 368 | 0 | 62bfe007829db085350d3ca16a496571 |
| y2v4 (pp.5-284) | 284 | 0 | d2acb6217fa83ffd61612c62b2f8872f |
| y2v4.5 (pp.10-290) | 290 | 0 | 31962a8ef8042eaa275a781e825250e3 |
| y2v5 (pp.7-243) | 243 | 0 | c15213576899fc8e8f2179e2afeb4c02 |
| y2v6 (pp.11-346) | 346 | 0 | 42ca7779490d72057b8c63f051a2eea1 |
| y2v7 (pp.7-207) | 207 | 0 | 75b28b9fd394816fa7b08d4036a6a2e4 |
| y2v8 (pp.11-208) | 208 | 0 | da33a4eca56f5f4e87201de29ce71701 |
| y2v9 (pp.8-225) | 225 | 0 | bdf77052e6f4a786e185e4690b42f063 |
| y2v9.5 (pp.10-219) | 219 | 0 | 6375c6765bd30c3818d91e9ea573b4ad |
| y2v9.75 (pp.4-8) | 17 | 0 | 5d5ac4a00ff7cbf080545264a203e959 |
| y2v10 (pp.9-235) | 235 | 0 | 5f397e582c47d59cdc47c1a578e9b29f |
| y2v10.25 (pp.1-10) | 10 | 0 | edd9335c73121a3699ded619bfdf69f3 |
| y2v11 (pp.11-223) | 223 | 0 | dc7c7824c249172c296c5e251febbfc8 |
| y2v12 (pp.12-228) | 228 | 0 | c36336d4930122ca663b6d8f825a1c88 |
| y3v3 depth pass | 256 | 28 | e5dcb795239b7ac22dab2165f02cae48 |
| y1v11.5 depth pass | 423 | 207 | 07d2540f276ab5918afa28b49e02b9e2 |
| y1v11.75 depth pass | 18 | 21 | a33dc3ec85f7fe022e246f2b65654f92 |
| y3v1 depth pass | 287 | 246 | 8ab9fd1c057e2735619f58a8f8235eb9 |
| y3v2 depth pass | 263 | 233 | 0adbcd0fd10a63a5965b7e604216805b |
| y3v3 depth redo | 256 | 223 | 3a1de15fcba81419f7cb00a5bd55ba0c |
| y0 depth pass (foundational) | 265 | 322 quotes / 64 scenes | 105a6f1d0edffa5982c5a3895229f8d1 |
| y3v2 depth redo | 263 | 613 quotes / 113 scenes | 52997afde409a6b0b362b9657a2a92e9 |
| y3v1 depth redo | 287 | 548 quotes / 126 scenes | 2e4ce48bde64e5c31502cc7c01a46f2d |
| y2v1 depth pass | 369 | 361 quotes / 191 scenes | 70c7b7a350102aec54f12d5502b18b25 |
| y2v2 depth pass | 354 | 280 quotes / 121 scenes | f99a61071e4dd6333ba5a988adb7a0a4 |
| y2v3 depth pass | 368 | 337 quotes / 126 scenes | 71e5b86a1e8aee3349245e1d976f3b06 |
| y2v4 depth pass | 284 | 196 quotes / 84 scenes | 27960e48e1881cb4d8043427d72a9ceb |
| y2v4.5 depth pass | 290 | 226 quotes / 127 scenes | 5ef343c03d2c04bef55dd0f4015a0e17 |
| y2v5 depth pass | 243 | 185 quotes / 106 scenes | 4e2e577f79382fa5ca418203b8cec1b3 |
| y2v6 depth pass | 346 | 185 quotes / 112 scenes | c7180b9c2bdefd24ba37dd92d6494d88 |
| y2v7 depth pass | 207 | 87 quotes / 100 scenes | 6a108d9815b9bfb31f48219c2d6813fe |
| y2v8 depth pass | 208 | 33 quotes / 88 scenes | 05096153fabf6ed7ce07f595739189ce |
| y2v9 depth pass | 225 | 34 quotes / 70 scenes | 6164911dab665ab8c29b8849a259be7f |
| y2v9 full scene pass + stub removal | 225 | 63 scenes / all quotes verified | a587279814e83182f63990f9e30ee8e1 |
| y2v4–y2v8 stub removal + passing-mention fill; gen with= id fix (R04) | 208 | verify/gate/hash green; make check green after gen fix | 9273b35457ea54b1fe16f23dfcaae73b |
| Year 2 stub repair — final batch (y2v9.75, y2v10.25, y2v10, y2v11, y2v12, y2v12.5) | — | verify/gate/make check green; hash deterministic | 44d72953fa0e3416f1370ed6e0af29f0 |
| y2v9.5 depth pass complete (full line-by-line read, coverage gate run) | 219 | verify/make check/hash green | 54d483abc37ef9538400990eaf037046 |
| rebuild-from-origin push | — | filter-branch normalize identity; verify/hash green | 384bb8285992b890decd34b623f501b5 |

| y2v12 depth pass | 228 | 432 quotes / 282 sections | 24af8babd74feccf7ee4d480a3557dd6 |
| y2v11 depth pass complete | 223 | 324 sections (142 evidence / 182 mention) | 93c577b0961f22e536945cb796b91858 (x2 deterministic) |
| y2v11 coverage gate + repair | 223 | locator for all 85 roster characters; genuine mentions added; stubs (75) removed | 93c577b0961f22e536945cb796b91858 |
| y2v11 + y2v12 depth passes merged to rebuild-from-origin | — | merged chain green: verify both ALL PASS; gate/build/check OK; hash docs de8d0590b53035111f4835f2fc2d0b01 (deterministic x2); docs rebuilt in merge | de8d0590b53035111f4835f2fc2d0b01 |
| y2v4.5 depth pass | 290 | 199 sections; coverage gate run (81 locator rows; d610f50... fresh-build hash) | docs/ restored to committed state; parent rebuilds at merge |
| y2v4.5 depth pass (verifier close-out) | 290 | verify y2v4.5 ALL PASS (513 says + 267 non-says); fresh-build hash c86a4219093d2ca33750a5fa02ad988a | docs/ restored |
| y2v4.5 depth pass final | 290 | 215 sections | docs/ restored to committed; parent rebuilds at merge |
| y2v10 Prologue+Ch.1 (pp.4-30) | 30 | verify ALL PASS (replica) | pending |
| y2v10 Ch.6–Epilogue batch (this session) | 226 (Ch.6 66pp + Ch.7 28pp + Epilogue+SS 19pp) | 273 person sections; volume ledger rewritten (Ch.6/Ch.7/Epilogue + 4 SSs); make check/gate OK; R19 80≤baseline; R18 0; docs restored | 1592 | ba6f1ebcb64b8a61f1c3d2b0d2d9dca6 |
| y2v10 coverage gate + DONE | 235 | 84 roster characters gated; ~116 mention anchors added; verify replica ALL PASS (1612); gate/check OK; R19 80≤baseline; DONE stamp | 1612 | 9cf06c99d80350f98b770751cd7b6efd |
| y2v5 depth pass end to end | 243 | 188 person sections; all chapters walked (Ch.1→Afterword); coverage gate run for 64/64 roster rows (0 uncited hits after mechanical recount); verify replica ALL PASS (534 says / 503 non-says); R18 0; R19 188 vs baseline 82 (disclosed, not reworded); make check red only on test_committed_docs_match_a_fresh_build (parent rebuilds) | docs/ restored to committed state; parent rebuilds at merge | b028b177 + finalize |
| y2v7 depth pass complete (inc. vol. ledger restore) | 207 | 322 paginated person sections; coverage gate 71 ids (64 clean, 7 matcher-noise ids triaged); volume ledger reconstructed from 6b2984ea^ after 6b2984ea/1929c765 truncation | docs not rebuilt in worktree; parent rebuilds at merge |
| y2v4 depth pass (full re-walk; supersedes the 84-scene 196-quote entry — that pass was below the y1v1 bar) | 284 | 224 paginated person sections (Prologue 7 / Ch.1 42 / Ch.2 18 / Ch.3 24 / Ch.4 36 / Ch.5 40 / Ch.6 42 / Epilogue 15); §5 coverage gate run for all 94 roster rows; quote replica ALL PASS (2,474 spans); make check green on fresh build; R18 0; R19 81 vs baseline 82; docs/ restored; parent rebuilds at merge | 991c5f8c6465c9f9d3c088a44a518441 (x2 deterministic) |
| y2v6 depth pass + repair close-out (this session) | 346 | 202 person sections; verify replica ALL PASS (2282 says / 572 non-says); R19 103→81 (< baseline); R18 2→0; strict validator clean; make check red only on test_committed_docs_match_a_fresh_build (parent rebuilds docs/ at merge); DONE stamp deferred to merge | docs/ not rebuilt in worktree; parent rebuilds at merge; no commit pushed | fb936b… (fresh build, temporarily inspected, docs/ then restored to committed state) | 1cd3b60b |
| y2v2 Ch.5→SS depth pass + coverage-gate repair (this session) | 354 | 192 person sections; quote replica ALL PASS (2,762 spans; 0 pm5-window / 0 whole-volume-only); §5 gate run for 66 roster rows, 0 uncited whole-word hit pages after 3 closing rows + recount; heading self-check empty; DONE stamp kept | docs not rebuilt in this worktree; parent rebuilds at merge | pending (this commit) |
| y2v3 depth pass complete (full line-by-line read; coverage gate run; DONE stamp kept) | 368 | 342 paginated person sections; §5 coverage gate run for all 65 roster rows (genuine hits anchored or coverage-noise catalogued; final word-boundary sweep: zero genuine gaps); heading self-check empty; verify replica ALL PASS (2919 says / 577 non-says); hasebe-haruka y2v3 cell reverted (zero genuine prints); Matsuo son/father disambiguation | docs/ not rebuilt in worktree; parent rebuilds at merge; verify --vol y2v3 pending re-check at parent | eef42b53 + this commit |
| y2v3 depth pass INTEGRATED at parent | 368 | 342 paginated person sections; parent verify y2v3 ALL PASS (2919 says / 577 non-says); y2v2 re-verified ALL PASS; merge-time R18 10→0, R19 84→81 (< baseline 82); gate OK; make check OK; heading self-check empty | docs rebuilt at parent | 85a8e96df0c3906f8ba9a2cf6697e8a5 (x2) |
| y2v9.75 depth pass (five-page short story, pp.4–8; whole volume read in page order) | 17 | 23 person sections (Ayanokōji 5 / Horikita 5 / Kushida 5 / Ibuki 4 + 4 honest mention/zero-hit sections); 116 says + 28 non-says quotes ALL PASS; §5 gate run for 8 roster rows (3 zero-genuine-print rows recorded); docs/ not rebuilt in worktree | docs/ untouched; parent rebuilds at merge | 5d2f5c2da3d6142247fd5f88cf5373ae (x2, temp-out build) |
| y2v9.75 depth pass INTEGRATED at parent | 17 | 23 person sections; parent verify ALL PASS (116 says / 28 non-says); gate OK; make check OK; heading self-check empty | docs rebuilt at parent | 5d2f5c2da3d6142247fd5f88cf5373ae (x2) |
| y2v10.25 depth pass (10-page short story, pp.1–9) | 10 | 23 person sections + 2 gymnasium place sections; verify replica ALL PASS (69 says / 19 non-says); §5 gate run for all 9 roster rows (3 zero-print rows noted); docs/ not rebuilt in worktree | docs/ untouched; parent rebuilds at merge | e20d0d60 (temp-out build) |
| y2v10.25 depth pass INTEGRATED at parent | 10 | 23 person sections + 2 place sections; parent verify ALL PASS (69 says / 19 non-says); gate OK; make check OK; heading self-check empty | docs rebuilt at parent | 6d6d64b46b0e54d43901123c9aca46b0 (x2) |
| y2v12.5 partial agent work salvaged | 216 | one section split into three scenes in Ayanokōji's ledger; replica verify ALL PASS (808 says / 33 non-says); walk still incomplete | docs untouched | n/a |

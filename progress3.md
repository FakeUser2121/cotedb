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
- The locked plan (§6) requires a Story axis, a Topics axis, reader-intent doors
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

## Known state / risks
- `share/site/` is currently half-orphaned (assets dir only) until the build
  completes; PDFs regenerate inside the build.
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

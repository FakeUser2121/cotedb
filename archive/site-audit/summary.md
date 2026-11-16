# COTE Knowledge Base — site map (read-only audit, 2026-10-28)

Audited object: the built site at [share/site/](/home/user3/Documents/unsafe/cote/share/site) —
**162 HTML pages**, mirrored byte-for-byte into `docs/` (`diff -rq share/site docs` → identical,
173 files including assets, PDFs and README).

**The live site could not be crawled.** `https://fakeuser2121.github.io/cote-kb/`,
`/sitemap.xml`, `/robots.txt` and the GitHub Pages API all returned **HTTP 404** (repo is private,
Pages is off; deployment is expected to come from Cloudflare). Every number below was measured from
the built tree, so it describes what *would* be served, not what *is* served. **unverified: live
responses, redirects, CDN behaviour, browser rendering, dark mode.**

There is no `sitemap.xml` and no `robots.txt` in the build, so discovery was done by crawling
`/index.html` and following every `href` (8 BFS rounds, no new pages after the first pass — all 162
pages were reached).

---

## 1. Shape of the site

| | measured |
|---|---|
| HTML pages | 162 |
| Sections (tab bar) | 7 + Home |
| Internal link edges (every `href`) | 18,568 |
| Distinct page→page pairs | 8,963 (8,813 across pages, 150 same-page jumps) |
| External links | **0** (no `http`/`mailto` href anywhere) |
| Unreachable / orphan / dead-end pages | **0 / 0 / 0** |
| Broken link targets / broken anchors | **0 / 0** |
| Visible page citations (`p.NN`) | 10,228 |
| Words (visible text) | 376,213 |
| Scene blocks rendered | 2,153 |
| Search index records | 795 |
| Print bundles / PDFs | 6 / 6 |

## 2. Page types, and what each type contains

Every type has exactly one layout signature (no per-type drift was found), except the `<h1>` rule in
sec. 5.1. Counts are of pages; "in" = incoming internal links, "out" = distinct pages linked.

| page type | pages | URL pattern | words | in | out | sections (h2) |
|---|---|---|---|---|---|---|
| home | 1 | `/index.html` | 862 | 483 | 10 | Where do you want to start? / The library / Reading a page |
| section index | 7 | `/<section>/index.html` | 7,147 | 2,167 | 215 | per section |
| volume page | 36 | `/story/v/<vol>/index.html` | 134,476 | 6,289 | 2,695 | At a glance / Who is named in it / Exams named in this volume / What was read |
| character page | 28 | `/people/<id>.html` | 96,647 | 4,413 | 1,828 | Who this is / <volume> … |
| place page | 28 | `/world/<id>.html` | 14,158 | 843 | 1,287 | What the records say it is |
| minor A–Z index | 20 | `/people/minor/<letter>.html` | 21,925 | 1,843 | 1,117 | <letter> entries |
| exam page | 15 | `/school/exam/<id>.html` | 8,336 | 527 | 576 | What the records say it is |
| system page | 5 | `/school/system/<id>.html` | 6,703 | 344 | 213 | What the records say it is |
| topic page | 5 | `/topics/<id>.html` | 57,347 | 57 | 168 | per question |
| year hub | 4 | `/story/y<0-3>.html` | 2,603 | 245 | 200 | (none — card list only) |
| appendix page | 3 | `/appendix/<id>.html` | 1,935 | 538 | 102 | citation key / evidence by volume / downloads |
| guide page (Start here) | 3 | `/guides/<id>.html` | 4,344 | **12** | 167 | per door |
| volume guide | 3 | `/story/v/y1v1/<char>.guide.html` | 6,059 | **14** | 84 | Infobox / Personality & voice / Abilities & feats / Trivia |
| volume transcript | 3 | `/story/v/y1v1/<char>.transcript.html` | 12,963 | **16** | 84 | one h2 per scene |
| chronology page | 1 | `/school/chronology.html` | 708 | 23 | 67 | Volumes in reading order |

**Depth from the homepage (BFS over links):** depth 1 = 10 pages (the 7 section indexes + 3 appendix
pages), depth 2 = 144 pages, depth 3 = 7 pages (the 6 y1v1 guide/transcript pages and
`people/tachibana.html`). Nothing is deeper.

## 3. Navigation elements, and where each appears

| element | pages it appears on | edges |
|---|---|---|
| masthead (brand + search + theme) | 162 / 162 | 162 |
| tab bar (Home + 7 sections) | 162 / 162 | 1,296 |
| left rail "Contents" | 161 / 162 (not on `index.html`) | 5,255 |
| breadcrumb | 154 / 162 (not on Home or the 7 section indexes) | 222 |
| right rail "Page context" | 144 / 162 | 1,369 |
| body links | 158 / 162 | 9,616 |
| footer | 162 / 162 | 648 |

Modules used by the right rail: `On this page` (auto table of contents), `Evidence footprint`,
`Related`. A page may carry one, two or all three: character pages run 28/28 Evidence footprint,
15 On-this-page, 14 Related; volume pages always carry all three.

## 4. How pages are generated (Step 1, from source)

One builder, one output dir, no templates on disk — every page is Python-composed.

```
ledgers/<kind>/<stem>.md  ─┐
cote_kb.db (51 tables)     ├─ kb/build_share_site.py  →  share/site/**/*.html  →  docs/  →  share/print/*.html  →  share/site/pdfs/*.pdf
drafts/<char>.<vol>.*.md  ─┘        │
                              kb/site_shell.py  page()          ← shell: masthead, tabs, crumbs, rails, footer
                              kb/site_sections.py               ← home, indexes, person, minor A–Z, volume, year, chronology
                              kb/site_topics.py                 ← 5 topic pages, 3 guide doors, 3 appendix pages, volume docs
                              kb/site_evidence.py               ← scene_block(), volume_sections() (the transcript rows)
                              kb/site_roles.py                  ← [role:…] buckets behind "Where the pages place them"
                              kb/site_ledgers.py                ← ledger grammar + MARKERS label table
                              kb/site_arch.py                   ← SECTIONS, volume ids/labels, TIER_LABEL
                              kb/site_bands.py (UNTRACKED)      ← evidence bands; NOT in the audited build
```

Content sources actually read by the build: **23 ledgers** (people ×18, exams ×1, systems ×1,
places ×3, volumes ×2 — 359 scene blocks, 3,624 entries) + the database for mechanical facts
(253 characters, 36 volumes, 15 exams, 5 systems, 28 locations, 58,609 quotes) + 6 markdown docs in
`drafts/`. The `dossiers/` tree is not read.

Citation grammar on every evidence row: `[marker] (p.NN)` → rendered as
`<span class="pageref">Vol. 1 p.137–140</span>`, with the volume word generated from the ledger's
`## <vol>` section, never typed by hand.

## 5. Clusters and hubs

Intra-section links 6,752 vs inter-section links 11,062 — the graph is a cross-reference web, not
seven silos. The three biggest flows: `people → story` 2,386, `story → people` 1,365,
`topics → people` 2,264.

Top hubs (incoming): `people/ayanokouji-kiyotaka.html` 1,194 · `story/v/y1v2/index.html` 1,066 ·
`story/v/y1v1/index.html` 972 · `people/index.html` 711 · `people/horikita-suzune.html` 627 ·
`index.html` 483.
Largest outgoing: `topics/results.html` 1,786 · `topics/who-knew-what.html` 1,201 ·
`topics/relationships.html` 589 · `people/index.html` 388 · `story/v/y1v1/index.html` 382.
Weakest connected (still reachable): the three `guides/*.html` doors (4 incoming each), the six
`story/v/y1v1/*.{guide,transcript}.html` (4–6 each).

Full per-page detail: [pages.csv](/home/user3/Documents/unsafe/cote/site-audit/pages.csv) (162 rows)
· [links.csv](/home/user3/Documents/unsafe/cote/site-audit/links.csv) (18,568 rows)
· [neighbors.csv](/home/user3/Documents/unsafe/cote/site-audit/neighbors.csv) (top-5 per page)
· [graph.json](/home/user3/Documents/unsafe/cote/site-audit/graph.json) ·
[sitemap.mermaid](/home/user3/Documents/unsafe/cote/site-audit/sitemap.mermaid) ·
[graph.html](/home/user3/Documents/unsafe/cote/site-audit/graph.html) (interactive, vis-network from
unpkg, needs a network to render) · [problems.md](/home/user3/Documents/unsafe/cote/site-audit/problems.md)

## 6. Top 10 problems (detail and evidence in problems.md)

1. **The published source does not build.** `kb/site_evidence.py:172` closes a dict comprehension with
   `]` — `SyntaxError`, so no page can be regenerated today. (`python3 -m py_compile kb/*.py`)
2. **155 of 162 pages have no `<h1>`.** Only `index.html` and the 6 y1v1 docs have one; every entity
   page carries the name as `<div class="kicker">` and a `<span class="here">` crumb.
3. **Two pages emit duplicate `id`s** — `people/index.html#g-faculty` twice, and
   `story/v/y1v2/index.html#ev-y1v2-p-248-251-ch-7-7-5-the-private-lesson-about` twice — so volume-2
   rail links land in volume-1's box.
4. **The People rail advertises a section the body does not contain** (`Roles in Vol. 2 · Student
   council`, count 2) because its only member, `tachibana`, is a ledger stem with no roster row — the
   body drops it, the rail keeps it.
5. **28 character pages, only 15 with transcribed scenes.** The other 13 (Sakayanagi, Nagumo,
   Yagami, Tsukishiro …) render `Who this is` and then nothing.
6. **34 of 36 volume pages say "Not read line by line yet"**; the Story spine's bulk is mechanical
   counts. Evidence exists for `y1v1` and `y1v2` only.
7. **The same name is spelled two ways in reader copy**: URL/title `Chabashira Sae` vs 111 visible
   occurrences of `Chiyabashira`.
8. **Ledger markers with no reader label leak pipeline vocabulary** into `mlabel`: Limit ×98,
   Fact ×38, Trade ×6, Impact ×4, Tactic/Scope/Inference/Goal ×2 each.
9. **Nine pages are near-dead-ends of the menu** (3 guide doors, 6 volume docs) — reachable only from
   the tab bar / rails, 4–6 incoming links each; the 6 volume docs are also the only dossier-style
   layout (Infobox / Trivia) on a site that retired dossiers.
10. **No `sitemap.xml`, no `robots.txt`, no `<link rel="canonical">`, zero external links, and no
    live deployment** (404) — nothing outside the tree tells a crawler or a reader where the site
    comes from; only `Vol. N p.NN` book citations, with no bibliography URL.

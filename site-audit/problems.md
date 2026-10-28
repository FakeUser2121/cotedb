# Problems found, ordered by severity

Everything below was measured on the built tree (`share/site`, 162 pages, mirror of `docs/`) and the
source in `kb/`. No file was edited during the audit. "How found" names the check, so it can be
re-run.

---

## S1 — The source tree does not build, so the shipped site cannot be regenerated
**Where:** [kb/site_evidence.py](/home/user3/Documents/unsafe/cote/kb/site_evidence.py) line 172
**What I saw:**
```
File "kb/site_evidence.py", line 172
    order = {v["id"]: v["order"] for v in ctx["vol_list"]]
                                                         ^
SyntaxError: closing parenthesis ']' does not match opening parenthesis '{'
```
`python3 -m py_compile kb/*.py` fails on this file, and `python3 kb/build_share_site.py` stops at the
`import site_bands` → `import site_evidence` chain. A dict comprehension is closed with `]`.
**Effect:** every page below is a snapshot; nothing in the tree can currently be rebuilt.
**How found:** py_compile + a failed build, then bracket tracking with `tokenize`.

## S2 — The People rail advertises a group the page does not contain
**Where:** [/people/index.html](/home/user3/Documents/unsafe/cote/share/site/people/index.html) and the same rail on all 28 character pages
**What I saw:** the left rail prints
`Roles in Vol. 2 · 2 → [Student council] [Faculty]`, but the body section
`<h3 id="r-y1v2">Recorded in Year 1, Volume 2</h3>` contains **one** box: Faculty (Sakagami).
"Student council" has no box, so the link lands on Year 1 Volume 1's Student council box.
**Cause:** the only y1v2 student-council fact is `tachibana` (p.193). `site_roles.collect()` returns
it, `site_roles.index()` counts it for the rail, but `site_sections._role_sections()` drops the row
because `ctx["char_by_id"]` has no `tachibana` (the roster id is `tachibana-akane`;
`ledgers/people/tachibana.md` keeps the walk's own stem). Rail = ledger truth, body = roster truth.
**How found:** `detail.json` cross-page anchor check flagged `#g-student-council` / `#g-faculty`
targets whose heading sits under a different volume; then `site_roles.index()` was run directly and
compared against the built body (`('tachibana', False)` — id not in `characters`).

## S3 — Duplicate element ids: anchor links land in the wrong volume's box
**Where:**
- [/people/index.html](/home/user3/Documents/unsafe/cote/share/site/people/index.html):
  `<h4 id="g-faculty">` appears **twice** (Vol. 1 box and Vol. 2 box). The rail's Vol. 2 "Faculty"
  therefore scrolls to Vol. 1's Faculty.
- [/story/v/y1v2/index.html](/home/user3/Documents/unsafe/cote/share/site/story/v/y1v2/index.html):
  `id="ev-y1v2-p-248-251-ch-7-7-5-the-private-lesson-about"` appears twice — two different scene
  blocks share one anchor because the slug is truncated at 48 characters.
**How found:** per-page `<id>` frequency count over all 162 files (`scan.json → dup_ids`), confirmed
by extracting the id list of that page.

## S4 — 155 of 162 pages have no `<h1>` at all
**Where:** every page except `/index.html` and the six
[/story/v/y1v1/&lt;char&gt;.guide|transcript.html](/home/user3/Documents/unsafe/cote/share/site/story/v/y1v1/) documents.
**What I saw:** entity pages put the name in `<div class="kicker">` and in a
`<span class="here">` breadcrumb; the first real heading is an `<h2>`. `grep -c "<h1"` → 0 on 155
files, and `pages.csv` shows the H1 column as "(no &lt;h1&gt; element on this page)" for those rows.
**Effect:** no document heading for assistive tech, for search-result titles, or for the
"top-of-page" anchor; also why the intended hierarchy is only legible from breadcrumbs.
**How found:** tag count per file.

## S5 — Most of the Story axis is a counter, not content
**Where:** 34 of the 36 [/story/v/*/index.html](/home/user3/Documents/unsafe/cote/share/site/story/v/) pages.
**What I saw:** their Evidence-state row reads "Not read line by line yet, so this page carries only
what can be counted" (verbatim on
[/story/v/y2v7/index.html](/home/user3/Documents/unsafe/cote/share/site/story/v/y2v7/index.html)).
Only `y1v1` and `y1v2` carry transcribed scenes. Same shape on people: **13 of 28 character pages
have zero scene blocks** — `ayanokouji-atsuomi`, `hashimoto-masayoshi`, `housen-kazuomi`,
`ishizaki-daichi`, `katsuragi-kouhei`, `mashima-tomonari`, `nagumo-miyabi`, `nanase-tsubasa`,
`sakayanagi-arisu`, `shiina-hiyori`, `tsubaki-sakurako`, `tsukishiro`, `yagami-takuya` — they render
`Who this is` + a volume-mention list and stop.
**Ledger side of the same fact:** 25 ledgers exist (people ×18, exams ×1, systems ×1, places ×3,
volumes ×2), covering exactly 2 of 36 volumes.
**How found:** per-page scene-block count (`scan.json → scenes`) and `site_ledgers.volume_index()`.

## S6 — PDF bundles are in the tree, linked from nowhere, and the page that should link them says there are none
**Where:** [share/site/pdfs/](/home/user3/Documents/unsafe/cote/share/site/pdfs) (6 files, 13.9 MB:
people 4.8 MB, story 3.0 MB, topics 3.8 MB, school 1.4 MB, world 0.6 MB, guides 0.5 MB) vs
[/appendix/downloads.html](/home/user3/Documents/unsafe/cote/share/site/appendix/downloads.html)
**What I saw:** the Downloads page reads "PDF bundles — Print-ready bundles of the reference sections,
generated from the same build as this site. **No bundles in this build.**" while six PDFs sit in the
served folder; `grep -o 'pdfs/[^"]*\.pdf'` across all 162 pages returns **0 links**. `people.pdf`
itself is fine (16,561 extracted text lines, 164 "Spoken" rows), so the defect is the missing link and
the contradicting sentence, not the file.
**How found:** file listing vs href scan, then `pdftotext` extraction.

## S7 — The same volume is labelled identically in one list, and the labels repeat across years
**Where:** [/people/sakayanagi-arisu.html](/home/user3/Documents/unsafe/cote/share/site/people/sakayanagi-arisu.html)
"Where the name appears" block (same component on all 28 character pages and the indexes).
**What I saw:** 31 items in one unbroken `<p class="mentions">`, whose visible labels repeat:
`Vol. 3` appears **3 times** (y1v3, y2v3, y3v3), and `Vol. 1`, `Vol. 2`, `Vol. 4`…`Vol. 11` twice
each — the year is dropped from the label while the href keeps it. There is no separator or grouping
either, so it reads as a duplicated list.
**How found:** parsed the block's `href / label / status` triples and counted labels.

## S8 — Naming drift between URL, title and body text
**Where:** site-wide; worst cases:
- `Chabashira Sae` — page title and file
  [people/chabashira-sae.html](/home/user3/Documents/unsafe/cote/share/site/people/chabashira-sae.html)
  vs **111** occurrences of `Chiyabashira` in body text, transcripts and citations
  (`story/v/y1v1/*.transcript.html` heading "Chiyabashira + school rules", her own page included).
  `aliases` lists all five forms (`Chiyabashira`, `Chabishira`, `Chibashira`, `Chabasira`,
  `Chabashira`), and the build renders the alias it found rather than the canonical name.
- `Ryūen` 169 vs `Ryuuen` 43; `Kikyō` 562 vs `Kikyo` 11.
- file stem vs display name disagree in romanisation on person pages (`sudou-ken` ↔ "Sudō Ken",
  `ryuuen-kakeru` ↔ "Ryūen Kakeru"), and the walk's ledger stems (`tachibana`, `ike-kanji`) are not
  the roster ids (`tachibana-akane`) — the S2 bug's root.
**How found:** accent-folded comparison of link text against target title, plus raw grep counts.

## S9 — Band vs evidence: a character with 20 transcribed scenes has no page
**Where:** Ike Kanji — [people/minor/i.html#ike-kanji](/home/user3/Documents/unsafe/cote/share/site/people/minor/i.html#ike-kanji)
**What I saw:** `ledgers/people/ike-kanji.md` holds **20 scene blocks and 109 quoted lines** across
y1v1 + y1v2, and the People rail labels him "Minor character"; there is no `people/ike-kanji.html`.
The shipped rule is `OWN_PAGE_TIERS = (1, 2)` on the curated `characters.tier` column (Ike is tier 3,
Ayanokōji tier 1 …), so transcription volume cannot earn a page. The fix is in the tree
([kb/site_bands.py](/home/user3/Documents/unsafe/cote/kb/site_bands.py), untracked, thresholds
scenes ≥ 3 / lines ≥ 10) but nothing is built with it yet — see S1.
**How found:** `site_ledgers.load("people","ike-kanji")` counts vs `characters.tier` vs file listing.

## S10 — Navigation regions overlap in purpose
**Where:** shell, all 162 pages.
**What I saw:**
- On 161 of 162 pages the left rail's first link goes to the same destination as a tab-bar link
  (`All people` → `people/index.html`, which the "People" tab already marks as current).
- Three doors into the same reading aids: `Home → "Where do you want to start?"` cards,
  the **Start here** tab ([/guides/index.html](/home/user3/Documents/unsafe/cote/share/site/guides/index.html)),
  and [/topics/index.html](/home/user3/Documents/unsafe/cote/share/site/topics/index.html)). The three guide
  pages get **4 incoming links each**, all from rails — no body page links to them.
- `Topics` holds "Points, prices and payouts" and "Winners, placements", which duplicate the purpose
  of `Exams & School` system pages (`point-economy`, exam pages).
- Breadcrumbs are absent on the home page and the 7 section indexes (by design: the leading Home crumb
  is dropped), so the only hierarchy hint on an index is the tab bar.
**How found:** region classification of every href (`diag.json → region_coverage`,
`pages_without_*`) plus destination-set comparison of rail links against tab links.

## S11 — The same evidence rows are reprinted across the site
**What I saw:** of **3,958** distinct ledger rows rendered, **3,282** appear on two or more pages
(7,273 occurrences in total). One row is shown on the character page, the volume page, the exam / place
page and the topic page that touch it. Scene blocks themselves are not duplicated (681 distinct, only
4 repeated), so this is the row-level fan-out — by design, but it is the reason `people.pdf` is 4.8 MB
and 155 pages of one site are mostly the same sentences.
**How found:** text fingerprinting of every `<li class="e-*">` row per page (`detail.json → ledger_rows`).

## S12 — Six pages still use the retired dossier layout
**Where:** [story/v/y1v1/](/home/user3/Documents/unsafe/cote/share/site/story/v/y1v1/) — three
`.guide.html` and three `.transcript.html` files, generated from `drafts/*.md`.
**What I saw:** their `<h2>`s are `Infobox`, `Personality & voice`, `Abilities & feats (Year 1, Vol. 1)`,
`Story summary`, `Relationships (Vol. 1)`, `Voice samples`, `Trivia` — vocabulary no other page type
uses — and they are the only entity pages on the site with an `<h1>` (see S4) and the only ones with a
year-3 BFS depth. Everything else on the site is ledger-rendered.
**How found:** per-type heading inventory (`anatomy.json`) and component signatures.

## S13 — Nothing outside the site documents it
**What I saw:** no `sitemap.xml`, no `robots.txt` (checked on disk and over HTTP), no
`<link rel="canonical">` on any page, **0 external hrefs site-wide**, and one `meta description`
per page. The only provenance statement is inside `README.txt` and the citation key page, which cites
"the English ebook and the physical book" without a publisher, ISBN or URL. The live origin
`https://fakeuser2121.github.io/cote-kb/` returns **404**, as do its `/sitemap.xml` and `/robots.txt`,
and the GitHub Pages API returns 404 (repo private) — so no online copy was auditable.
**How found:** HTTP probes (`curl -o /dev/null -w "%{http_code}"`), file listing, href scan.

## S14 — Pipeline vocabulary reaches reader copy
**Where:** `mlabel` row labels site-wide.
**What I saw:** eight ledger markers have no entry in `site_ledgers.MARKERS` and fall through to the
default label, printing raw-ish words on reader pages: **Limit ×98**, **Fact ×38**, **Trade ×6**,
**Impact ×4**, **Tactic ×2**, **Scope ×2**, **Inference ×2**, **Goal ×2**. (`limit`, `fact`, `trade`,
`impact`, `tactic`, `scope`, `inference`, `goal` are written by the walk but not in the table.)
**How found:** frequency count of `<span class="mlabel">` values vs the MARKERS key list.

## S15 — Truncated rail labels vs full section headings (cosmetic)
**What I saw:** 29 rail links read "Role not stated (17)" and point at `people/index.html#g-unstated`,
whose heading reads "Role not stated on the pages read so far (17)". Same for every character page's
rail. Not a broken link — a label/destination wording mismatch found by the anchor-text comparison.

---

## What could not be checked (unverified)
- **The live deployment.** All HTTP probes returned 404; the site exists only as built files here.
- **Browser rendering** (CSS geometry, dark mode, the search box, the details/summary interaction) — no
  page was opened in a browser during this audit; all findings are from parsing the HTML.
- **Whether `share_check.py` would pass today** — it needs the build, which fails (S1).
- **PDF layout quality** — only the text layer was extracted, not page count or visual breaks.
- **The 6 `drafts/*.md` sources' accuracy** — they are pre-walk authored prose; the audit records that
  they are rendered, not whether their claims hold.

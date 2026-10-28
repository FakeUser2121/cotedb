# The COTE encyclopedia schema

This is the fixed contract every page is built from. It is the human-readable
form of `kb/schema.json`; where the two disagree, the JSON is what the build
reads.

The point of the contract is a single promise:

> **Adding information means adding data.** A new character is a row in
> `cote_kb.db` plus (once the walk reads their pages) a file in
> `ledgers/people/`. A new volume is a row in `volumes`. A new exam, system or
> place is a row in its table. None of those additions requires touching a
> builder, a template, a navigation list or a CSS file.

## What the build reads

| input | what it is | who may edit |
|---|---|---|
| `cote_kb.db` | one row per named thing, plus coverage and the mention tables | add rows/tables; never change a fact or a quote |
| `ledgers/<kind>/<stem>.md` | the walk's page-anchored notes; the only prose source | append only |
| `drafts/people/*.md` | the six authored documents (3 guides, 3 transcripts) | authored text |
| `kb/schema.json` | this contract, machine-readable | the schema owner |
| `kb/redirects.json` | retired URLs and where they went | anyone changing a URL |
| `kb/entity_names` (table) | the one display spelling per entity | the schema owner |

Everything else in `kb/` is a builder. The pipeline is:

```
cote_kb.db + ledgers/ + drafts/ + schema.json
        │
        ├─ kb/registry.py      one record per entity (id, name, aliases, sort key, status)
        ├─ kb/site_data.py     rows for the builders
        ├─ kb/site_ledgers.py  the ledger grammar
        ├─ kb/site_evidence.py scene blocks and citation rendering
        ├─ kb/site_roles.py    `[role:…]` facts, grouped by volume
        ├─ kb/site_bands.py    which characters get a page
        ├─ kb/site_sections.py page builders (home, people, story, school, world)
        ├─ kb/site_topics.py   topics, guides, appendix
        ├─ kb/site_shell.py    masthead, tabs, rails, breadcrumbs, footer
        └─ kb/build_share_site.py  orchestration → share/site → docs/ → print → pdf
```

## Sections

One ordered list, defined once (`schema.json` → `sections`), used by the tab
bar, the home page, the footer and every index:

1. Start here — `guides/index.html`
2. People — `people/index.html`
3. Story — `story/index.html`
4. Exams & School — `school/index.html`
5. World & Places — `world/index.html`
6. Topics — `topics/index.html`
7. Appendix — `appendix/index.html`

Home is not a section: it is the front door to the seven.

## Entity types

| type | id | URL | index | sort key |
|---|---|---|---|---|
| character | `characters.char_id` | `people/{id}.html` (bands 1–2) or `people/minor/{letter}.html#{id}` (band 3) | People, A–Z | family name, folded |
| volume | `volumes.vol_id` | `story/v/{id}/index.html` | Story → year | `chrono_order` |
| exam | `exams.exam_id` | `school/exam/{id}.html` | Exams & School | first volume's `chrono_order` |
| system | `systems.sys_id` | `school/system/{id}.html` | Exams & School | name, alphabetical |
| place | `locations.loc_id` | `world/{id}.html` | World & Places | name, alphabetical |
| topic | `topics/{id}.html` | `topics/{id}.html` | Topics | title, alphabetical |
| year | `y0`…`y3` | `story/y{year}.html` | Story | year number |
| scene | `ev-{vol}-p{first}-{last}-{order}` | anchored inside a page | — | page order |
| source | `volumes.vol_id` | `story/v/{id}/index.html` | — | `chrono_order` |

`source` is the citation-facing record of a volume. Every label a reader sees
("Year 1, Volume 3", "Vol. 3", "Year 1 Vol. 3") is generated from it; no
builder types a volume name.

### Page templates (ordered sections)

A page of a type always shows its sections in this order. A section with no
data renders one standard line — "Not covered yet." — so the layout never
shifts between pages of the same type.

**character** — lead · At a glance · Who this is · Names & aliases · Story
(by volume) · Relationships · Appearances · Evidence · Related

**volume** — lead · At a glance · What happens, chapter by chapter · Who is
named in it · Exams in this volume · Scenes read from it · Full documents for
this volume · Related

**exam** — lead · At a glance · The rules · When it was run · Evidence · Related

**system** — lead · At a glance · How it works · Where the pages state it ·
Evidence · Related

**place** — lead · At a glance · What it is · When it appears · Evidence · Related

**topic** — lead · The answer · Evidence · Related

**year** — lead · Volumes in order · Related

The "Names & aliases" section is why a reader can see every spelling in use:
the display name, the database canonical name (when different), the family and
given forms, nicknames, honorifics, and the misspellings the text actually
prints. Each is labelled with where it comes from. No spelling is deleted
because it is wrong — it is shown *as* a variant, and only the display name is
used in titles and links.

## Fields every entity has

| field | meaning |
|---|---|
| `id` | permanent slug; never changes |
| `display_name` | the one spelling used in the title, H1, breadcrumb, link text and body |
| `aliases` | every other spelling; search and redirects only |
| `sort_key` | what every generated list sorts by |
| `type` | one of the table above |
| `status` | `stub` / `partial` / `complete`, computed |
| `tier` | characters only: 1 principal, 2 medium, 3 minor |
| `parents` | year / class / section |

## Status

Computed on every build from the data, never typed by hand:

- **character** — `stub` no scene blocks; `partial` scenes exist but a volume
  the name appears in has not been read through; `complete` scenes exist and
  every volume the name appears in carries its DONE stamp.
- **volume** — `complete` when its own ledger carries `→ DONE`; `partial` when
  it has chapters or scenes; `stub` otherwise.
- **exam / system / place** — `stub` no ledger; `partial` ledger scenes exist;
  `complete` every volume the ledger cites is DONE.
- **topic** — `complete` when every volume with evidence is DONE.

## Bands: who gets a page

A character gets a page of their own when either the curated tier already
qualifies, or their transcribed evidence crosses a threshold:

- **Principal** — 40+ scenes and 300+ quoted lines, or curated tier 1
- **Medium** — 3+ scenes or 10+ quoted lines, or curated tier 2
- **Minor** — everyone else: an entry on the page for their initial

Evidence can promote, never demote. The thresholds live in `schema.json` →
`bands`.

## Names and identity

- Display spellings live in the `entity_names` table, seeded once by
  `kb/init_entity_names.py`. Changing a canonical spelling is an `UPDATE`.
- Other spellings live in `aliases`, `exam_aliases`, `location_aliases`,
  `system_aliases` and the ledger's `aliases used for anchors:` line.
- An alias owned by more than one entity is **ambiguous**: it stays searchable
  but is not used as an alias or a redirect. `kb/registry.py --report` lists
  them.
- A ledger filename is not necessarily a page id. `site_ledgers.LEDGER_ALIAS`
  is the only pairing table (`tachibana` → `tachibana-akane`,
  `midterm-exam` → `midterm-final-written`, `point-economy` → `private-points`,
  `school-library` → `library`). Every builder resolves through it.

## Scenes and anchors

A scene lives inside the page that renders its ledger, never on a page of its
own. Its id is `ev-` + the block's heading slug, cut at 48 characters, with a
namespace prefix when several ledgers share one page (the A–Z pages). The same
function that writes the id also builds every link to it, so a link and its
target cannot drift apart.

## URLs and redirects

Existing URLs are permanent. When an id changes, the old path gets a row in
`kb/redirects.json`; the build writes a small meta-refresh page there with a
visible link and `rel=canonical`.

## Validation

The build fails on any of:

1. a page without exactly one H1, or with a duplicate id
2. an internal link or anchor that does not resolve
3. an entity without a display name, a sort key or a unique id
4. two entities sharing an alias
5. entity link text that is not the target's display name
6. a different section order in tab bar, home, footer or indexes
7. a left-rail link that duplicates a tab-bar link
8. a rail count that differs from the items the body renders
9. a list not sorted by its declared key
10. a ledger marker without a reader label
11. two layouts for one page type
12. a page without a breadcrumb
13. a changed URL without a redirect

## Decisions still open

See `NAMING.md` — spellings that need a human choice, each with the evidence
and the current default.

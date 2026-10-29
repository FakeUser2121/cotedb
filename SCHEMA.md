# Content model

The site is built from plain files. No database, no corpus.

```
content/            the roster and settings (tab-separated, one header line)
  volumes.tsv         id, year, number, label
  characters.tsv      id, name, sort, aliases (;), volumes (;)   volumes = where the name appears
  exams.tsv  systems.tsv  places.tsv    id, name, kind, volumes (;)
  topics.tsv          id, title, lede, kind (rows|pairs), markers, pattern, owners
  config.json         tier thresholds, own-page rule, page sizes
  old_urls.txt        every URL the previous site served (each redirects)
ledgers/<kind>/<id>.md   the evidence: page-anchored notes, one file per entity
ledgers/volumes/<vol>.md chapters and beats for a volume
gen/                the generator (model.py, render.py, build.py, markers.json, assets/)
docs/               the built site. Generated. Never edited by hand.
```

A ledger's file name **is** the entity id: `ledgers/people/sudou-ken.md` belongs to
`sudou-ken` in `characters.tsv`.

## Adding things (data only)

| To add | Do this | Touches code? |
|---|---|---|
| a character | one row in `characters.tsv` | no |
| a volume | one row in `volumes.tsv` | no |
| an exam, system or place | one row in its `.tsv` | no |
| a topic | one row in `topics.tsv` (markers and/or a regex, optional owner kind) | no |
| evidence | append blocks to the entity's ledger | no |
| a new row label | one entry in `gen/markers.json` | no |

The build fails if a ledger uses a marker that has no reader label, or a ledger
file has no matching row.

## Evidence shape (what a page can show)

A block is one scene: `### y1v1 p.46–51 — Title`, then rows `[marker] (p.NN) text`.

| Row | Becomes |
|---|---|
| `[scene]` | the one-line setup under the title (write it first) |
| `[says:<id>]` `[ask]` | a spoken line, with its speaker |
| `[thinks]` `[narrates]` | inner voice, narration |
| `[action]` | what happens |
| `[rel:<id>]` | a relationship note, and the "with" list |
| `[place:<id>]` `[exam:<id>]` | tags that put the scene on that place or exam page |
| anything else in `gen/markers.json` | a labelled note under "more notes" |

## Pages and URLs

| Page | URL | Exists when |
|---|---|---|
| Home | `index.html` | always |
| People directory | `people/index.html` | always; one row per character |
| Character | `people/<id>.html` | scenes >= 3 or quoted lines >= 10 (`config.json`) |
| Story, year, volume | `story/index.html`, `story/y<n>.html`, `story/v/<vol>/index.html` | always, one per volume |
| Exams, systems | `school/index.html`, `school/exam/<id>.html`, `school/system/<id>.html` | always |
| Places | `world/index.html`, `world/<id>.html` | always |
| Topics | `topics/index.html`, `topics/<id>.html` | one per row in `topics.tsv` |
| About | `about/how-to-read.html`, `about/coverage.html` | always |
| Search | `search/index.html` | always |
| Old URLs | listed in `content/old_urls.txt` | become redirects |

Menu: **People · Story · Exams & School · World & Places · Topics**. Footer: How to
read this site, Coverage, Contribute. Nothing else is a section.

## Tiers

Computed, never typed. A character is **Main** when named in at least `main_share`
of the volumes in scope, **Supporting** at `supporting_share`, otherwise **Minor**.
Scope is all volumes, or one year when a year is chosen. Tier decides grouping in
the directory; it does not decide whether a page exists. Evidence does.

## One scene card, everywhere

Title, volume and pages, one setup line, places and exams, who is with them, up to
three key lines (long lines are cut and shown whole under "more notes"), the other
rows folded under "more notes", and before/after buttons. A scene is never shown as
a bare quote. Long pages hold only the first few cards in HTML; the rest load from
`assets/s/<page>.js` and are filtered in the browser, so a page stays small however
much evidence exists.

## Reading order

Year 1, Year 2, Year 3, then side stories. "Read up to" (top right) hides anything
after the chosen volume, using this order.

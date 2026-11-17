# AGENTS.md — COTE Knowledge Base

Read this file first, then the last entries of `progress2.md` and `progress3.md`.
It is the only instruction file. If your memory, a progress note or an older
habit disagrees with it, this file wins. All output (ledgers, notes, commit
messages, replies) is in English.

## 1. What this is

A static, searchable knowledge base of the *Classroom of the Elite* light novels,
built from 37 local translated volumes. Every claim carries a volume and a page;
every quotation is verbatim. Readers are fanfic writers (voice, exact lines,
scene context), powerscalers (feats, numbers, exam outcomes) and people trying to
find "where was that moment?". The goal is a complete answer in ten seconds
without going back to the novels. Verbatim accuracy and correct attribution are
non-negotiable.

Priority while walking: **capture everything, polish nothing.** Organisation is
generated later from complete, consistently anchored ledgers.

## 2. Repo map

| Path | What | Who edits |
|---|---|---|
| `ledgers/<kind>/<id>.md` | the evidence: page-anchored notes, one file per entity | you, append only |
| `ledgers/volumes/<vol>.md` | chapters, beats and gaps for a volume | you, append only |
| `content/*.tsv`, `content/config.json` | the roster and settings | you, rows only |
| `gen/` | the generator (`model.py`, `render.py`, `build.py`, `markers.json`, `assets/`) | owner only |
| `docs/` | the built site | **nobody**: it is generated |
| `kb/` | walk tools (`cote.py`, `cote_mcp.py`, `walk_locate.py`, `verify2.py`, `verify3.py`) and the validator (`validate_site.py`, `schema/`) | owner only |
| `progress2.md`, `progress3.md` | walk log; what shipped | you |
| `PROGRESS.md` | history of the earlier phases | read only |
| `archive/` | retired work | nobody; never run, import or copy from it |
| `text/`, `gdrive_download/` | local only; **never enter git** | — |

The site is built only from `content/` and `ledgers/`. The page locator is
`python3 kb/walk_locate.py locate --vol <vol> --char <id>`: it searches a
volume's pages in `text/` for a roster character's published name forms
(`name`, `sort` and `aliases` from `content/characters.tsv`, matched
case- and diacritic-insensitively). It is a walk aid; it never feeds the site
and is never served.

Retired for good, do not recreate: the database-driven site build, a `share/`
mirror, PDF bundles, dossier / guide / article pages, a Start-here or Appendix
section, and the local-LLM extraction experiment (rejected by the owner).

## 3. Hard rules

1. **Never edit `docs/`.** It is generated: `python3 kb/cote.py build`.
2. **Ledgers are append-only.** Never reword, reorder or delete an existing row.
   **Exception (owner, 2026-11-18): editing and deletion are permitted when you
   are fixing a mistake** — e.g. removing placeholder stubs, malformed
   chapter-sized sections, or wrong rows you or a prior pass introduced. This is
   repair, not polishing: the row being removed must be an error, not genuine
   walk evidence. State in `progress2.md` exactly what was removed and why.
3. **Never edit `gen/`, `kb/validate_site.py`, `kb/schema/`** unless
   the owner's task says so. This file may be edited when the owner's task
   or a standing instruction says so. If a check fails, fix the content. If
   you think a check is wrong, stop and explain; never loosen it.
4. **Never fill a field from memory, wikis, the anime or the web.** Only what the
   corpus pages say. If it is not on a recorded page, leave it empty.
5. **The baseline only goes down.** `kb/schema/validate_baseline.json` counts
   violations per rule; a change may lower a count, never raise it.
6. **One name, one spelling.** Names live in `content/*.tsv`; never type a name
   into code. Do not decide spelling questions (macrons, shared nicknames): list
   the options with evidence and ask.
7. **No new section, tab, page type, link style, marker or file type** without
   the owner's approval.
8. **Stdlib only, no pip.** `node` is needed only for `make browser`. Code has
   module docstrings and no inline comments. Never guess an API or schema:
   inspect first.
9. **Work only inside this repo.** Never modify `git config`; commit as the
   noreply identity through environment variables. Never commit `session-*.md`.
10. **If anything fails or is unclear, stop.** Paste the command and its full
    output. No workaround, no retry loop, no hiding the problem by editing output.
11. **Code never fills data.** Scripts (`walk_locate.py`, `cote.py read`, any
    ad-hoc python) only locate and verify text. Ledgers, TSV rows and progress
    entries are written by hand from pages you have read. Do not script
    discovery or generate content.
12. **Nothing surfaces without an explicit destination.** Every ledger row is
    written for a named place on the site (entity page, volume page, and/or a
    named topic). Before shipping, confirm each new row appears only where
    intended: sample any topic or other query list that would republish it and
    confirm membership against that list's title and lede. Pattern and query
    code may propose candidates; a human accepts or rejects each member.
    Unreviewed auto-collection into a curated list is forbidden. Changing a
    topic pattern or membership list is editorial: show before/after samples
    and get the owner's OK. Prefer hand-curated membership over regex when
    either would do.

## 4. Commands

Use the `cote_walk` MCP tools if loaded; otherwise `python3 kb/cote.py <command>`
(tell the owner the server needs a reload; do not switch permanently). Do not use
ad-hoc sed, cat, grep or python one-liners for these steps. `cmd | tail` reports
tail's status, not cmd's: check the real exit code.

| Command | Does |
|---|---|
| `status` | git state, every ledger's last boundary marker, progress tails |
| `next [--vol y1v3]` | chapter map: walked / remaining, next range |
| `chapters [--vol y1v3]` | a volume's section page ranges |
| `read --vol y1v3 --pages 10-12 [--blank]` | verbatim pages; `--blank` flags blank or two-line pages |
| `append --file ledgers/people/<id>.md --from <tmpfile> [--under <vol>] [--stamp "<vol> ch<N> → p.<X>"] [--at-end]` | insert a section, one boundary stamp per chapter |
| `ledger-new people/<id> --header "char_id: <id> · class: Class 1-D · ..."` | create a ledger |
| `verify [--vol y1v3]` | check every quote against the volume text |
| `build` | regenerate `docs/` and print its hash |
| `gate` | strict site validator and generator tests |
| `hash [docs]` | determinism hash; run twice, the values must match |
| `ship --from <msgfile> --check --vol <vol> [--push]` | stage, gate, commit, optionally push |

Also: `make check` (tests, validation, compile), `make strict` (every violation),
`make build`, `make browser`.

## 5. The walk

**Unit: one chapter of one volume, read once, every ledger touched at once.**
Order: y1v1 → y1v11.75 → y2v1 → y2v12.5 → y3v1 → y3v2 → y3v3 → y0 (side
stories, last). `next` tells you where you are; do not trust a remembered list.
Read in page order and never skip pages. Rhythm: **small steps. One change,
verify, next.** Write ledger entries right after each read, before reading on.

**"One chapter" is the work unit, NOT the ledger-section unit.** A chapter is
read once, but it produces MANY ledger sections — one per scene, typically 2–4
pages each. Never write one section per chapter, and never compress a 30-page
chapter into a single section. §6 defines the section shape; check your headings
against it before moving on.

**Re-read this file at every chapter boundary and again before every ship.** In
a long session these rules decay from context; the harness injecting them once
is not enough. Record any standing reminder in `progress2.md`, which you read
at the start of every task.

Per chapter:
1. `next`, then `read` the range with `--blank`. A chapter over about 30 pages is
   read in two halves with entries written between them.
2. Append to **every** ledger the chapter touches: people, exams, places, systems
   (`ledgers/<kind>/<id>.md`). Use the heading dialect the file already uses and
   pass the **same `--stamp`** to every file touched. A character who is absent
   gets no stamp.
3. Every present roster character gets at least one entry per chapter. Sweep each
   main character present for voice, feats and traits. The viewpoint character
   narrates, so his sweep is a full linear read; non-viewpoint characters are
   mention-anchored.
4. Append the chapter to `ledgers/volumes/<vol>.md`: setting, narrative beats,
   page-map note, new named entities, new system facts, open threads, attribution
   gaps.
5. `verify --vol <vol>` until both verifiers pass (section 7).
6. `build`, `gate`, `hash` twice. Section 10 is the full checklist.
7. Log in `progress2.md` (walked, left open, defects kept as printed) and
   `progress3.md` (page counts, determinism hash).
8. `ship --from <msgfile> --check --vol <vol>`.

Per volume: a coverage gate. Run the page locator (`kb/walk_locate.py locate`)
for each roster character the volume names and compare its hit pages against
the pages cited in the ledgers; every hit page gets an entry or an explicit
`passing mention`. The locator only knows published spellings, so a page where
the text misspells a name may not surface. **You must actually run the locator
for every roster character with this volume in their `volumes` cell and record
the result in `progress2.md` before you may write a "Coverage notes" claim,
a `→ DONE` stamp, or a completion entry. Writing "hits cross-checked" or
"topic membership spot-checked" without having run the check is a false claim,
not a shortcut.** Note that the locator matches name forms as substrings, so
short aliases produce false positives (e.g. `ike` matches "like", and both
Horikitas match the shared `Horikita`); read the hit pages to triage them, do
not assume every hit needs a new entry. Also check every topic whose
pattern or membership list could match rows written this volume: hand-check
each new hit against that topic's title and lede (rule 12); list noise for an
owner-approved pattern or list change rather than shipping it silently. Then
end the volume with a closing stamp `<!-- walk: <vol> <last section> → DONE -->`
in `ledgers/volumes/<vol>.md` (the site reads it to mark the volume complete) and
add a `progress2.md` row. If the walk finds a named character in a volume that is
missing from that character's `volumes` cell in `content/characters.tsv`, add the
volume id (add only; never remove).

## 6. Ledger format

```
# Sakura Airi — walk ledger

char_id: sakura-airi · class: Class 1-D · status: mid (allies)
aliases used for anchors: sakura, airi, sakura-san

## y1v2

<!-- walk: y1v2 → start -->

### y1v2 p.152–158 — Ch.5 sec. 5.1: <what the scene does>
[scene] (p.152) Place, time, who is present, what the page states outright.
[says:ike-kanji] (p.153) “One quoted line.”
[rel:horikita-suzune] (p.155) Relation, scoped to this volume.

<!-- walk: y1v2 ch5 → p.189 -->
```

- One `## <vol>` block per volume, oldest first. One `### <vol> p.RANGE — <label>`
  section per scene, in page order. **The first row of every section is `[scene]`:
  one setup sentence.** That sentence is the card's setup line on the site.
- **`p.RANGE` in the heading is mandatory and is not optional decoration.** The
  site parser (`gen/model.py`, `SHEAD`) reads the page range from the heading
  itself; a row's `(p.NN)` does NOT fill it in. A heading like
  `### y3v3 Ch.1 — depth read: ...` missing `p.RANGE` produces a card with a
  *blank* page range. Always write `### y3v3 p.14–45 — <label>`. `pp.X–Y` is fine
  for a multi-page scene; a chapter number is never a substitute.
- **Section = scene, not chapter, not volume.** Target 2–4 pages per section and
  one section per distinct scene/beat. A single section spanning a whole chapter
  (20+ pages) or a whole volume (`pp.14–251`) is wrong, even if every row inside
  it carries a page. Compare your section count to the volume's scene density:
  a 250-page volume should yield on the order of 150–200 sections, not ~50.

**Self-check before shipping (do not skip):** for each volume you touched, run
`grep -rh '^### <vol> ' ledgers/people/ | grep -vE '^### <vol> pp?\.'` — the
output must be empty. Then check the count with
`grep -rh '^### <vol> ' ledgers/people/ | wc -l` against the density above. Paste
both results into `progress2.md`. A green build/gate/check does NOT prove the
headings are well-formed; this grep does.
- **Every row starts with its page, `(p.NN)`.** A row without a page does not go in.
- Exactly one `<!-- walk: … chN → p.X -->` boundary stamp per chapter per file, at
  the end of that chapter's last section. `append --stamp` enforces it.
- The header line keeps the file's own form (`char_id:`, `place_id:`, `system_id:`,
  `exam_id:`, `vol_id:`). The `class:` value feeds the people directory.
- **A ledger's file name equals its entity id**, which equals the row id in
  `content/`. A mismatch fails the build.

Tags. The complete list the site can show is `gen/markers.json`. A row with any
other tag stops the build and names the file; new tags need the owner's approval
and a reader label.

| Tag | Use |
|---|---|
| `[scene]` | setup (first row of a section) |
| `[action]` | what a character does |
| `[says]` | one quoted line. In a person's own ledger it is that person's line; any other speaker is `[says:<char_id>]` |
| `[thinks]` | interior monologue, quoted |
| `[voice]` `[trait]` `[feat]` `[limit]` `[status]` | how the character speaks; characterisation with its evidence; demonstrated competence; what they cannot do or the page withholds; where they stand now |
| `[back]` | backward reference to an earlier volume's fact |
| `[rule]` `[status:points]` | rules, numbers, point moves |
| `[rel:<id>]` | relation to another entity, scoped to this volume. Write it on **each** participant's ledger, mirrored from the same scene |
| `[place:<id>]` `[exam:<id>]` `[class:<id>]` | tags that put the scene on that place, exam or class; the id must exist in `content/` |
| `[note]` | reasoning about the record itself: inference, absence, ambiguity |
| `[trivia]` `[role:<key>]` | detail; a post held (student council, faculty) |
| `[fact]` `[trade]` `[impact]` `[tactic]` `[scope]` `[inference]` `[goal]` `[number]` `[result]` `[flag]` `[narrates]` `[ask]` `[say]` `[think]` | already present in ledgers; use only the way a nearby existing block uses them |

A new kind of fact needs the owner's approval **before** first use. No junk drawer.

## 7. Quotes, attribution, inference

A past fill pass produced about 55 invented `[says]` quotes (memory of a
translation and the anime, not the corpus). That is the failure this section
exists to prevent.

- **Every quoted string is corpus-exact.** Copy the printed words; only quote-mark
  and dash style may differ. A `[says]` row holds **one** quotation pair (the first
  `“…”`); a second sentence inside the pair fails. A line split by `…` is checked
  fragment by fragment. If a line cannot be quoted exactly, describe it in a
  `[note]`. Never paraphrase inside quotation marks. Ellipses inside a corpus line
  are literal.
- `verify --vol` normalises (NFKC, curly quotes and dashes folded,
  non-alphanumerics stripped) and searches the cited pages ±5, then the whole
  volume. Run it after **every** writing batch. Never close a chapter on a failing
  quote. Fix the row, never the verifier; replace with corpus-exact text, do not
  delete the insight.
- Speaker named in the text: write the name. Speaker untagged: record the line under
  the responding character with a `[note]` saying the translation leaves it
  untagged, or leave it out and list the gap in the volume's attribution list.
  **Never assign a speaker from context alone.**
- **Never present an inference as fact.** Label it `[inference]` or `[note]`.
- Record what a chapter's pages know, not what later volumes reveal.
- Translation defects are kept as printed and flagged at the page; do not
  correct them silently.
- Corpus quirks: strip "Goldenagato" and "RoyalMTLs" watermark lines in tools;
  quote glyphs vary by volume (curly, straight, guillemets); page markers are
  `--- page N ---`; `walk_locate.py chapters` finds chapters (the four tiny
  marker-less volumes use fixed sections); `Y3V2`, `Y3V3` and the new `V0-dark`
  superseded older rows.
- Standing corrections: the bus-challenger lines (y1v1 pp.19–20) are the office
  lady; the uniformed girl (p.21) being Kushida is an inference, noted as one; the
  red-haired delinquent is Sudō, not Ryūen; Horikita's "club betrayal" is pp.59–62.

## 8. Adding entities (data only)

| To add | Row in | Columns |
|---|---|---|
| character | `content/characters.tsv` | `id, name, sort, aliases (;), volumes (;)` |
| volume | `content/volumes.tsv` | `id, year, number, label` |
| exam / system / place | `content/exams.tsv`, `systems.tsv`, `places.tsv` | `id, name, kind, volumes (;)` |
| topic | `content/topics.tsv` | `id, title, lede, kind (rows or pairs), markers, pattern, owners` |

Add the row first, then `ledger-new` with the same id. Ids are lowercase,
hyphenated, family name first (`sudou-ken`). The display `name` follows the
spelling already used in the file; if unsure, ask. Separate list cells with `;`.

## 9. What the site shows (the validator enforces it)

- Menu: **People · Story · Exams & School · World & Places · Topics**; footer: How
  to read this site, Coverage, Contribute. Nothing else is a section.
- A character gets a page when scenes ≥ 3 or quoted lines ≥ 10 (`content/config.json`);
  otherwise a directory row. Tiers (Main, Supporting, Minor) are computed from how
  many volumes name the character; they never decide whether a page exists.
- One scene card everywhere: title, volume and pages, `[scene]` setup, tags, who is
  with them, up to three key lines (long ones cut, whole under "more notes"),
  before/after buttons. A quote is never shown without its scene.
- **Link grammar:** a name links as a whole; a citation `p.47` is never a link; a
  before/after pointer is one button for the whole line; controls are buttons; no
  link inside a quotation; a link labelled with a section name goes to that section.
- **Wording on served pages:** no pipeline vocabulary (ledger, dossier, scene
  block, database, raw ids such as `y1v2`); no second person in published prose
  (quoted speech is exempt). If the validator flags a row, rewrite the row.
- **Public voice:** macron names (Ayanokōji, Kōenji), neutral encyclopedic prose.

## 10. Before every commit

1. `python3 kb/cote.py build`
2. `python3 kb/cote.py gate` (exit 0)
3. `make check` (OK)
4. `python3 kb/cote.py hash` twice; the two values must match.
5. `git status`: only `ledgers/`, `content/`, `docs/`, `progress*.md` changed
   (anything else needs the owner's approval).
6. One change per commit; put the `make check` output in the message.
7. Do not push if any step failed.

**Steps 1–7 are not sufficient on their own.** They validate the built site
(quotes, markers, links, wording, baseline) but do NOT check ledger heading
shape, scene granularity, or whether the §5 coverage gate was run. Before every
commit of walk work you must ALSO:

8. Run the §6 heading self-check grep for every volume touched (output empty)
   and the section-count sanity check; paste both into `progress2.md`.
9. Run the §5 coverage gate for every roster character with the volume in their
   `volumes` cell; record the uncovered hits and how each was resolved in the
   volume's Coverage notes and in `progress2.md`.
10. Only then write the `→ DONE` stamp and the completion entry. If 8 or 9 was
    not actually performed, do not write a claim that it was.

## 11. Stop and ask when

A check fails and you cannot fix it by editing content; the build names an unknown
marker; a quote will not verify; a spelling, alias or id is ambiguous; a field would
need outside knowledge; the task seems to need a change in `gen/`, `kb/` or this
file; a baseline count would rise; anything here contradicts the task.

## 12. Report at the end of each task

Files changed (exact paths); the `make check` result; new entities and any new tag
requested; every place you were unsure and what you left empty; what is open next.

## 13. Working with the owner

Short, direct verdicts ("GO"): fold implications into the plan without
re-litigating what is locked here. Be honest about tradeoffs. Show a sample and get
approval before scaling. Plain language. Durable progress files over conversation
memory. Present checkpoints as files with exact paths.

## 14. Common mistakes to avoid (added after y1v9 walk)

These are mistakes made during the y1v9 walk. Do not repeat them.

1. **Match the heading dialect of the file you are editing.** The volume ledger
   uses `### Chapter N: Title (pp. X–Y)` or `### Prologue: Title (pp. X–Y)`.
   Person ledgers use `### y1v9 p.RANGE — label`. Never invent a new heading
   format like `### y1v9 p.X–Y — Epilogue: ...`. Check the existing headings
   in the file before writing new ones.

2. **`[says]` is only for quoted lines.** A row tagged `[says]` must contain
   a corpus-exact quotation in quotation marks. If the content is a description,
   an observation, or paraphrase, use `[note]`, `[scene]`, or another
   appropriate tag. Never use `[says]` for non-quoted text.

3. **Coverage notes must list every passing mention.** After writing entries,
   run the page locator for every roster character with the volume in their
   volumes cell. Compare hit pages against cited pages. Every hit page that
   is not a scene presence must be listed as a passing mention in the volume's
   Coverage notes section. Do not skip this step or assume "it's just a mention."

4. **Verify before shipping, not after.** Run `verify`, `build`, `gate`,
   `make check`, and `hash` twice BEFORE committing. If any check fails, fix
   the content first. Do not commit and then discover errors.

5. **Read every page yourself.** Do not rely on the page locator to discover
   content. The locator only knows published spellings and will miss misspelled
   names. Read the pages, write entries from what you read, then use the
   locator only for the coverage gate cross-check.

6. **Check the file's existing format before appending.** Look at the last
   3-5 sections of the file to understand the heading style, row format, and
   stamp placement. Match it exactly.

7. **Do not turn "one chapter" into "one section."** This mistake shipped three
   bad volumes (y3v1–v3). §5's "unit: one chapter" describes the work rhythm
   (read once, touch all ledgers), NOT the ledger-section shape. Each chapter
   must be broken into many scene sections with `### <vol> p.RANGE — label`
   headings. A chapter-sized section with 3 quotes is a summary, not a scene,
   and a bare `### y3v3 Ch.1 — depth read` heading produces a card with no page
   range. Compare against y1v1's headings before you write.

8. **Do not claim a check you did not run.** "Coverage notes: hits cross-checked"
   and "topic membership spot-checked" are claims about work done. Writing them
   without running the locator is the same failure as inventing a quote: the
   record asserts something false. Run the §5 gate and paste its result into
   `progress2.md` before you write the claim, the DONE stamp, or COMPLETE.

9. **Repair is not polishing.** §3.2's exception lets you delete an erroneous
   row (a stub, a malformed chapter-sized section, a quote from the wrong
   volume), but not to "improve" genuine walk evidence. When you remove rows,
   log in `progress2.md` exactly which sections you deleted and why they were
   errors. A wrong row you catch before shipping is a fix; genuine history is
   never rewritten to look tidier.

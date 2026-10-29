---
name: cote-walk
description: Continue the page-anchored COTE encyclopedia walk — read the next chapter of a volume, fan its evidence into the per-entity ledgers, verify every quote, rebuild and publish the static site. Use whenever asked to walk, continue, or finish a chapter of the Classroom of the Elite volumes, to add or correct ledger rows, or to ship the site after chapters land. All steps run through one command, `python3 kb/cote.py`, instead of ad-hoc sed/cat/grep/python invocations.
metadata:
  version: "1"
---

# COTE walk

The encyclopedia is built from walk ledgers: page-anchored rows extracted from
the translated volumes, rendered into a static site. One chapter at a time, in
order, with every claim tied to a page and every quotation verbatim.

## Tools

The loop is exposed as MCP tools by the `cote_walk` server
(`kb/cote_mcp.py`, registered as a custom stdio server). Call them directly;
do not reach for sed, cat, grep, git or a shell for any of these steps.

| Tool | Does |
| --- | --- |
| `status` | git state, every ledger's last boundary marker, progress tails |
| `next` | chapter map with walked/remaining, next range and read commands |
| `chapters` | a volume's section page ranges |
| `read_pages` | verbatim page extraction; `blank` flags illustration pages |
| `append` | insert a section into a ledger, one boundary marker per chapter |
| `ledger_new` | create a per-entity ledger |
| `verify` | check every quote against the volume text |
| `build` | rebuild `docs/` from `content/` and the ledgers (`docs` flag ignored) |
| `gate` | strict site validator and generator tests |
| `hash` | determinism hash; run twice, the values must match |
| `ship` | stage, commit as the noreply identity, optionally push |

`Read`, `Grep`, `Glob` and `Edit` remain the right tools for inspecting and
writing prose; the tools above cover the pipeline around them.

If the `cote_walk` tools are not available in the session (server not loaded
yet), the same operations exist as `python3 kb/cote.py <command>`; run that, and
tell the user the server needs a reload rather than falling back permanently.

## The chapter loop

Read in page order; never skip pages. Extract a range, read all of it, then the
next range. Keep a chapter's pages in one pass so cross-references stay straight.

1. `next` to get the range; `read` the first half, then the second with `--blank`
   so blank and two-line pages are identified rather than guessed.
2. Fan the evidence into every ledger the chapter touches. One ledger file per
   entity, appended with `append`. Reuse the section heading the file's own
   dialect uses (`### y1v2 p.152–158 — Ch.5 §5.1: <claim>`), and pass the same
   `--stamp` to every file touched by the chapter so each ledger carries exactly
   one boundary marker per chapter.
3. Write the chapter's section in `ledgers/volumes/<vol>.md` (append at end, no
   `--under`): setting, narrative beats, page-map note, new named entities, new
   system facts, open threads, attribution gaps.
4. `verify --vol` until both verifiers pass. A failure is a misquoted line or a
   quote stitched across two corpus sentences — fix the row, never the verifier.
5. `build`; then `gate`; then `hash` twice and confirm the two runs match.
6. Close the chapter in `progress2.md` (what was walked, what stayed open, what
   defects were kept as printed) and `progress3.md` (what shipped: page counts,
   link and citation counts, determinism hash, render locations checked).
7. `ship --from <msg file> --check --vol <vol> --push`.

## Non-negotiables

- Verbatim quotation only. Ellipses inside a corpus line are literal; do not
  join two sentences inside one quotation pair.
- Attribution gaps are recorded as gaps. If the translation leaves a speaker
  untagged, say so in the row; never assign the line.
- Forward-only knowledge stays out. A chapter records what its pages know, not
  what later volumes reveal.
- Translation defects are preserved and flagged at the page, not silently
  corrected.
- Page numbers stay in the copy but must never look clickable when nothing
  happens on click.
- Commits use the noreply identity through environment variables only; `git
  config` is never modified. Never commit `session-*.md`.
- The generated `docs/` tree is what gets published; never edit it by hand.
  `RULES.md` and `SCHEMA.md` define what the site may contain.

## Resources

- `references/ledger-grammar.md` — row tags, section shapes, stamp placement,
  and the wording rules the validator enforces.
- `kb/cote.py` — the wrapper itself; `cote.py <cmd> -h` for every flag.

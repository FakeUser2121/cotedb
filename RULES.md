# Rules for anyone (or any model) editing this repository

Run `make check` before every commit. If it fails, the change is wrong, not the check.

## What the site is
A static knowledge base of a novel series. Every claim carries a volume and page.
Readers want one answer, with its context, on one page, without losing their place.

## Hard rules
1. **Never edit `docs/` by hand.** It is generated: `make build`.
2. **Never weaken `kb/validate_site.py` or `kb/schema/rules.json` to make a check
   pass.** Change a rule only on the owner's decision, and say so in the commit.
3. **The baseline only goes down.** `kb/schema/validate_baseline.json` holds the
   violation count per rule. A change may lower a count, never raise it.
4. **Never rewrite a fact or a quote.** `ledgers/` is append-only. Do not fill a
   field from memory or from a wiki: if the book page is not recorded, leave it empty.
5. **One name, one spelling.** Display names live in `content/*.tsv`; do not type a
   name into generator code.
6. **No new section, tab, page type or link style** unless it is in
   `kb/schema/rules.json` first, with a rule that checks it.
7. **Ambiguous? Stop and ask.** List the options; do not pick.
8. **One change per commit**, with the output of `make check` in the message.

## Link grammar (enforced)
| Kind | Clickable part |
|---|---|
| Name (character, place, exam) | the whole name as written, never a fragment |
| Citation `p.47` | nothing; it is never a link |
| Scene pointer (before / after) | the whole line, arrow included (a button) |
| Control (filter, load more) | a visible bordered button |
| Navigation (tabs, breadcrumb) | the whole item |

Also: no link inside a quotation; a link labelled with a section name goes to that
section; each target linked once per paragraph; every page has one `<h1>` and a
breadcrumb; the tab bar is the same on every page; no pipeline words on a page.

## Commands
| Command | Does |
|---|---|
| `make build` | rebuild `docs/` from `content/` and `ledgers/`, then validate |
| `make check` | tests, strict-ratchet validation, byte-compile |
| `make strict` | print every violation, ignoring the baseline |
| `make baseline` | accept today's counts (only after they went down) |
| `make browser` | drive the built pages in jsdom (needs `npm install jsdom`) |

The walk tools `kb/cote.py build | gate | hash` call the same things.

## Open decisions (owner)
- Long-vowel policy for names (display keeps marks; search ignores them).
- Whether some very high-traffic characters get a page before their scenes are read.
- Caps in `kb/schema/rules.json` (`max_words`) are tuned to today's data.
- R19 (second person) is a warning: some ledger rows quote speech without quotation marks.

# Ledger grammar

The shape every walk row takes, and the rules the site validator enforces on the
prose that reaches readers.

## File shape

```
# Sakura Airi — walk ledger

char_id: sakura-airi · class: Class 1-D · status: mid (allies)
aliases used for anchors: sakura, airi, sakura-san

## y1v2

<!-- walk: y1v2 → start -->

### y1v2 p.152–158 — Ch.5 §5.1: <what the scene does>
[row] (p.152) …

<!-- walk: y1v2 ch5 → p.189 -->
```

- One `## <vol>` block per volume, oldest first.
- One `### <vol> p.RANGE — <label>` section per scene, in page order.
- Exactly one `<!-- walk: … chN → p.X -->` boundary marker per chapter in each
  file, at the end of that chapter's last section. `append --stamp` enforces it:
  it de-duplicates repeats and writes the marker after the new section.
- The header line stays in the file's own form (`char_id:` for people,
  `place_id:` / `system_id:` / `exam_id:` / `vol_id:` for the rest).

## Row tags

| Tag | Use |
| --- | --- |
| `[scene]` | place, time, who is present, what the page states outright |
| `[action]` | what a character does, with the page |
| `[says]` | one quoted line of dialogue — first `“…”` pair only |
| `[thinks]` | interior monologue, quoted |
| `[feat]` | demonstrated competence or habit |
| `[trait]` | characterisation the page supports, with the evidence |
| `[status]` | where the character stands at this point |
| `[limit]` | what the character cannot do, or what the page withholds |
| `[note]` | reasoning about the record itself (inference, absence, ambiguity) |
| `[rel:<id>]` | a relation to another entity, scoped to this volume |
| `[place:<id>]` | a location established or reused |
| `[back]` | backward reference to an earlier volume's fact |

Every row starts with its page or page range in parentheses. A row without a
page does not go in.

## Quotation rules

The verifiers (`cote.py verify --vol`) normalise both sides: NFKC, curly quotes
and dashes folded, non-alphanumerics stripped. What that means in practice:

- Copy the printed words exactly; only quote marks and dash style may differ.
- A `[says]` row holds a single quotation pair. The checker reads the first
  `“…”` pair and compares it against the source; a second sentence inside the
  same pair is treated as part of the quote and fails.
- A quotation split by `…` is checked fragment by fragment; each fragment must
  appear in the volume.
- Cross-page quotations are fine — the fallback search covers the whole volume.
- If a line cannot be quoted exactly, describe it in a `[note]` instead. Never
  paraphrase inside quotation marks.

## Attribution

- Speaker named in the text: write the name.
- Speaker untagged: record the line under the responding character with a
  `[note]` saying the translation leaves it untagged, or leave it out and record
  the gap in the volume page's attribution list.
- Never infer a speaker from context alone and present it as printed.

## Prose the site publishes

Rows are rendered into reader-facing pages, so they pass the validator's wording rules (R18 is an error, R19 a warning):

- No pipeline vocabulary: ledger, dossier, scene block, raw volume ids, database
  names. Say "the record", "this page", "the chapter".
- No second person, no instructions to the reader.
- Page references stay, but never styled as controls when nothing happens on
  click.
- A dropped bullet is a dropped claim: the chapter renderer emits every labelled
  line, uncapped and in document order.

When the gate flags a line, rewrite the line. Loosening the checker is not a fix.

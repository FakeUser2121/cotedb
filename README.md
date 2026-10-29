# COTE Knowledge Base

A static, searchable, page-cited knowledge base for *Classroom of the Elite*.
Notes and evidence live in plain files; `docs/` is the generated site.

```
content/   roster and settings (tsv)     gen/    the generator
ledgers/   page-anchored evidence        docs/   the built site (generated)
kb/        walk tools and the validator
```

- Build: `make build`   Check: `make check`
- Add a character, volume, exam, place or topic: add one row in `content/`.
  Add evidence: append to its ledger. See [SCHEMA.md](SCHEMA.md).
- Rules for contributors and models: [RULES.md](RULES.md).

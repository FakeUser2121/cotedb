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
  Add evidence: append to its ledger.
- Search telemetry (Cloudflare Pages): logs what visitors type, while they
  type, to a first-party D1 database. Setup and the stats page:
  [functions/README.md](functions/README.md).
- Everything a contributor or a model needs: [AGENTS.md](AGENTS.md).

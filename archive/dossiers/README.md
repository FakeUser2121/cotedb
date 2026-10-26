# Retired layer — dossiers/

Nothing in here feeds the website. It was the pre-walk analysis pass: prose
written from memory of the series and from database rows whose speaker
attribution was already known to be unreliable.

The user's ruling (2026-10-26): only output produced by the chapter-unit walk
is correct. Public prose now comes from `ledgers/**` (page-anchored entries)
and `drafts/people/*.md` (the guides and scene transcripts the walk wrote),
and the build reads no other content source. This tree is kept only so the
old wording stays searchable and the retired generators still run.

* Build inputs: none. `kb/build_share_site.py` never opens this directory.
* Generators that still write here: `kb/build_main_dossiers.py`,
  `kb/build_mid_dossiers.py`, `kb/build_background.py`,
  `kb/build_exam_dossiers.py`, `kb/build_world_dossiers.py`.
* Checkers that still read here: `kb/p8_consistency.py`, `kb/p9_consistency.py`.
* Do not copy text from these files into a ledger, a draft, or a page.

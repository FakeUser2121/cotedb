COTE Knowledge Base — share site
===============================

Static HTML site over the evidence-backed knowledge base for the
Classroom of the Elite light novels.

  index.html            start here (stats + sections + PDF downloads)
  background.html       background characters
  main/ mid/            character profiles (section-preserving)
  world/                world / location profiles
  exams/                exam profiles + master chronology
  systems/              school systems (points, council, clubs, expulsion)
  vol1/                 Year 1, Volume 1 — guides + scene transcripts
  pdfs/                 6 per-category PDFs (print editions of the site)
  assets/               stylesheet + client-side search index

Search: press / (or click the box in the header). Works opened from
disk (file://) — the index is a JS constant, no server needed.

Developer notes: generated — never hand-edit. Regenerate:
  python3 kb/build_share_site.py
Built from the repository knowledge base. Verbatim quotes are cited
with volume + page anchors (e.g. y1v1 p.247).

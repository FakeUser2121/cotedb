#!/usr/bin/env python3
"""One-time migration: cote_kb.db is gone, so recover what it fed into the
site from the site itself (docs/ as built at commit f5fced0) and write it as
plain files under content/. Run once, before the first rebuild:

    python3 tools/migrate_roster_once.py

Writes content/{volumes,characters,exams,systems,places}.tsv and
content/old_urls.txt, and renames four ledgers so a ledger's file name equals
the entity id it belongs to. After the rebuild this script has nothing left
to read and can be deleted.
"""
import html
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "content"

RENAMES = [("ledgers/people/tachibana.md", "ledgers/people/tachibana-akane.md"),
           ("ledgers/exams/midterm-exam.md", "ledgers/exams/midterm-final-written.md"),
           ("ledgers/systems/point-economy.md", "ledgers/systems/private-points.md"),
           ("ledgers/places/school-library.md", "ledgers/places/library.md")]

# Spellings the walk itself wrote (kb/schema/NAMING.md section 3).
WALK_FORMS = {
    "ayanokouji-kiyotaka": ["kiyopon"], "chabashira-sae": ["Chiyabashira"],
    "hirata-yousuke": ["Yousuke"], "hondou-ryoutaro": ["Hondou"],
    "kondou-reo": ["Kondou"], "kushida-kikyou": ["Kikyou"],
    "kouenji-rokusuke": ["Kouenji"], "ryuuen-kakeru": ["Ryuuen"],
    "satou-maya": ["Satou"], "sudou-ken": ["Sudou"],
}
# Defect flagged in NAMING.md D5: the macroniser turned "Inoue" into "Inōe".
NAME_FIXES = {"inoue-toa": "Inoue Toa"}


def main_html(path):
    s = path.read_text(encoding="utf-8")
    a, b = s.find("<main"), s.find("</main>")
    return s[a:b]


def vols_in(markup):
    out = []
    for v in re.findall(r"story/v/([^/]+)/index\.html", markup):
        if v not in out:
            out.append(v)
    return out


def romanizations(name):
    plain = "".join(c for c in unicodedata.normalize("NFD", name)
                    if not unicodedata.combining(c))
    doubled = name.replace("ō", "ou").replace("Ō", "Ou").replace("ū", "uu").replace("Ū", "Uu")
    return [x for x in dict.fromkeys([doubled, plain]) if x != name]


def tsv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(header)] + ["\t".join(str(c) for c in r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: {len(rows)} rows")


def main():
    names = {}
    for line in (ROOT / "kb/entity_names.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        t, i, n, sk, *_ = line.split("\t") + [""] * 4
        names.setdefault(t, {})[i] = (NAME_FIXES.get(i, n), sk)

    # volumes
    rows = []
    for vid, (label, _) in names["volume"].items():
        m = re.match(r"y(\d)v([\d.]+)$", vid)
        year, num = (int(m.group(1)), m.group(2)) if m else (0, "0")
        rows.append((vid, year, num, label))
    rows.sort(key=lambda r: (int(r[1]), float(r[2])))
    tsv(OUT / "volumes.tsv", ["id", "year", "number", "label"], rows)

    # which volumes name each character: minor entries + own-page mentions
    named = {}
    for f in sorted((DOCS / "people" / "minor").glob("*.html")):
        body = main_html(f)
        for m in re.finditer(r'<h3 id="([^"]+)">.*?</h3>(.*?)(?=<h3 id=|\Z)', body, re.S):
            named.setdefault(m.group(1), [])
            for v in vols_in(m.group(2)):
                if v not in named[m.group(1)]:
                    named[m.group(1)].append(v)
    for f in sorted((DOCS / "people").glob("*.html")):
        cid = f.stem
        if cid == "index" or cid not in names["character"]:
            continue
        body = main_html(f)
        mm = re.search(r'<p class="mentions">(.*?)</p>', body, re.S)
        if mm:
            named.setdefault(cid, [])
            for v in vols_in(mm.group(1)):
                if v not in named[cid]:
                    named[cid].append(v)
    order = {r[0]: i for i, r in enumerate(rows)}
    rows_c = []
    for cid, (name, sk) in names["character"].items():
        al = romanizations(name) + WALK_FORMS.get(cid, [])
        ledger = ROOT / "ledgers" / "people" / f"{cid}.md"
        if cid == "tachibana-akane":
            ledger = ROOT / "ledgers/people/tachibana.md"
        if ledger.exists():
            m = re.search(r"aliases used for anchors:\s*([^\n]+)", ledger.read_text(encoding="utf-8"))
            if m:
                al += [a.strip() for a in m.group(1).split(",") if a.strip() and "-" not in a]
        al = [a for a in dict.fromkeys(al) if a.lower() != name.lower() and "/" not in a]
        vols = sorted(named.get(cid, []), key=lambda v: order.get(v, 999))
        rows_c.append((cid, name, "Inoue" if cid == "inoue-toa" else (sk or name.split()[0]), ";".join(al), ";".join(vols)))
    rows_c.sort(key=lambda r: (r[2].lower(), r[1].lower()))
    tsv(OUT / "characters.tsv", ["id", "name", "sort", "aliases", "volumes"], rows_c)

    # exams, systems, places
    def facts(body):
        return {html.unescape(k): html.unescape(re.sub("<[^>]+>", "", v)).strip()
                for k, v in re.findall(r'<div class="k">(.*?)</div><div class="v">(.*?)</div>', body, re.S)}
    for kind, sub, table in (("exam", "school/exam", "exams"), ("system", "school/system", "systems"),
                             ("place", "world", "places")):
        out = []
        for eid, (name, _) in names[kind].items():
            f = DOCS / sub / f"{eid}.html"
            body = main_html(f) if f.exists() else ""
            fa = facts(body)
            k = fa.get("Type") or fa.get("Kind") or ""
            out.append((eid, name, k, ";".join(vols_in(body))))
        out.sort(key=lambda r: r[1].lower())
        tsv(OUT / f"{table}.tsv", ["id", "name", "kind", "volumes"], out)

    # every URL the old site served, so removed pages can redirect
    old = sorted(p.relative_to(DOCS).as_posix() for p in DOCS.rglob("*.html"))
    (OUT / "old_urls.txt").write_text("\n".join(old) + "\n", encoding="utf-8")
    print(f"content/old_urls.txt: {len(old)} urls")

    for a, b in RENAMES:
        if (ROOT / a).exists():
            subprocess.run(["git", "mv", a, b], cwd=ROOT, check=True)
            print("renamed", a, "->", b)


if __name__ == "__main__":
    main()

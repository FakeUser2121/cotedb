#!/usr/bin/env python3
"""Write kb/schema/NAMING.md: every entity whose spelling is not settled.

The brief's rule is that spelling is data, not a guess: a name gets one
display row in `entity_names`, and anything the data disagrees about is
printed here with its evidence, so the owner of the archive can decide it
once. Nothing in this file chooses. It measures:

  * characters the build macronises (display row vs. roster spelling),
  * spellings the walk actually wrote in the ledgers, per character,
  * ledger stems whose id differs from the roster's,
  * aliases claimed by more than one entity,
  * names the mechanical macroniser gets wrong.

Run: python3 kb/gen_naming.py [--print]
"""

import argparse
import collections
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry  # noqa: E402
import site_arch  # noqa: E402
import site_data as D  # noqa: E402
import site_ledgers as L  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "cote_kb.db"
OUT = Path(__file__).with_name("schema") / "NAMING.md"


LONG = {"ā": "aa", "ī": "ii", "ū": "uu", "ē": "ee", "ō": "ou"}


def strip_macrons(text):
    s = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in s if not unicodedata.combining(c))


def vowel_key(text):
    """The letters behind the macrons: 'Kikyō' and 'Kikyou' agree, so a row
    differing only by a macron is one name written two ways."""
    s = text or ""
    for long, short in LONG.items():
        s = s.replace(long, short)
    return re.sub(r"[^a-z0-9]+", "", strip_macrons(s).lower())


def corpus():
    """Every ledger file's text, the only prose the site is allowed to quote."""
    out = {}
    for p in sorted((ROOT / "ledgers").rglob("*.md")):
        out[p.relative_to(ROOT).as_posix()] = p.read_text(encoding="utf-8")
    return out


def spelling_re(name):
    """A regex that finds any spelling of `name` whose vowels are the same as
    the display form but written long or short. 'Kikyō' finds 'Kikyou';
    'Sudō' finds 'Sudou'; plain letters stay literal."""
    out = []
    for ch in name:
        if ch == "ō":
            out.append("(?:ō|ou|o)")
        elif ch == "ū":
            out.append("(?:ū|uu|u)")
        elif ch in "āīē":
            out.append("(?:%s|%s%s)" % (ch, strip_macrons(ch), strip_macrons(ch)))
        else:
            out.append(re.escape(ch))
    return re.compile(r"(?<![\w-])" + "".join(out) + r"(?![\w-])")


def counts(corpus, regex):
    c = collections.Counter()
    for text in corpus.values():
        c.update(m.group(0) for m in regex.finditer(text))
    return c


def macron_pairs(con, corpus):
    """Every character whose display row differs from the roster spelling by
    macrons alone."""
    rows = con.execute(
        "SELECT entity_id, display_name FROM entity_names "
        "WHERE entity_type = 'character' ORDER BY display_name").fetchall()
    canon = dict(con.execute("SELECT char_id, canonical_name FROM characters"))
    out = []
    for cid, shown in rows:
        raw = (canon.get(cid) or "").strip()
        if not raw or raw == shown or vowel_key(raw) != vowel_key(shown):
            continue
        c = counts(corpus, spelling_re(shown))
        out.append({"id": cid, "roster": raw, "shown": shown,
                    "forms": c})
    return out


def attestation(con, corpus):
    """Spellings the walk actually wrote that are not just one word of the
    title (a surname or given name is not a misspelling). These are already
    aliases, so no decision is needed; the page lists them under the title."""
    out = []
    for cid, shown in con.execute(
            "SELECT entity_id, display_name FROM entity_names "
            "WHERE entity_type = 'character' ORDER BY display_name"):
        title_words = {w.lower() for w in shown.replace("-", " ").split()}
        forms = []
        for raw, form in con.execute(
                "SELECT raw_form, form_type FROM aliases WHERE char_id = ? "
                "AND COALESCE(is_noise, 0) = 0", (cid,)):
            if not raw or vowel_key(raw) == vowel_key(shown):
                continue
            words = {w.lower().strip(".,") for w in raw.replace("-", " ").split()}
            if words <= title_words:
                continue  # a component of the name, not a variant of it
            n = sum(len(re.findall(
                r"(?<![\w-])" + re.escape(raw) + r"(?![\w-])", t))
                for t in corpus.values())
            if n:
                forms.append((raw, n, form or ""))
        if forms:
            forms.sort(key=lambda f: (-f[1], f[0]))
            out.append({"id": cid, "shown": shown, "forms": forms})
    return out


def variant_rows(con, corpus):
    """Characters whose ledgers write more than one surface spelling."""
    rows = con.execute(
        "SELECT entity_id, display_name FROM entity_names "
        "WHERE entity_type = 'character' ORDER BY display_name").fetchall()
    out = []
    for cid, shown in rows:
        c = counts(corpus, spelling_re(shown))
        if len(c) > 1:
            out.append({"id": cid, "shown": shown, "forms": c})
    return out


def macroniser_defects(con, corpus):
    """Names where macronize() groups the vowels wrongly.

    Two failures are checkable without guessing at a reading:
      * the macron does not stand where 'ou'/'uu' were (positional), and
      * the name ends in 'oue', where the 'u' is its own syllable (Ino-ue),
        so no long vowel exists to mark.
    """
    rows = con.execute(
        "SELECT char_id, canonical_name FROM characters "
        "WHERE merged_into IS NULL").fetchall()
    out = []
    for cid, raw in rows:
        raw = (raw or "").strip()
        got = site_arch.macronize(raw) if raw else raw
        if not raw or got == raw:
            continue
        if re.search(r"oue\b", raw, re.I) and "\u014de" in got:
            out.append((cid, raw, got))
            continue
        i = j = 0
        while i < len(got) and j < len(raw):
            g = got[i]
            if g in "\u014d\u016b":
                want = "ou" if g == "\u014d" else "uu"
                if raw[j:j + 2].lower() != want:
                    out.append((cid, raw, got))
                    break
                i, j = i + 1, j + 2
            else:
                if g.lower() != raw[j].lower():
                    out.append((cid, raw, got))
                    break
                i, j = i + 1, j + 1
    return out


def id_map(con):
    out = []
    for kind, pairs in L.LEDGER_ALIAS.items():
        for stem, pid in pairs.items():
            out.append((kind, stem, pid))
    return out


def ambiguous(reg):
    return sorted(reg["ambiguous"].items())


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def fmt_forms(c):
    return ", ".join(f"`{k}` ×{v}" for k, v in c.most_common())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="prn", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB_PATH)
    site_arch.load_names(con)
    reg = registry.load(con)
    text = corpus()

    pairs = macron_pairs(con, text)
    variants = variant_rows(con, text)
    misspelt = attestation(con, text)
    defects = macroniser_defects(con, text)
    ids = id_map(con)
    amb = ambiguous(reg)

    lines = []
    add = lines.append
    add("# Naming decisions")
    add("")
    add("Generated by `kb/gen_naming.py` from `cote_kb.db`, `ledgers/` and the")
    add("`entity_names` table. Every spelling on the site is a row in that table;")
    add("this page lists the rows the data does not settle, with the evidence for")
    add("each, so each one can be decided once and then only be data.")
    add("")
    add("To apply a decision, edit `entity_names` (one row per entity), then")
    add("rebuild. No builder change is needed, and no other page has to be")
    add("touched: indexes, search, crumbs, citations and cross-links all read the")
    add("same row.")
    add("")
    add("## 1. Long-vowel mark (macron) policy")
    add("")
    add(f"{len(pairs)} characters are drawn with a macron on the site while the")
    add("roster and most of the walk spell them without one. The counts are")
    add("occurrences in `ledgers/`, across all spellings of the same name.")
    add("")
    add(md_table(["Id", "Roster spelling", "Shown on site", "Spellings in the ledgers"],
                 [[f"`{p['id']}`", p["roster"], p["shown"],
                   fmt_forms(p["forms"]) or "*no scene read yet*"]
                  for p in pairs]))
    add("")
    add("Decision D1: one policy for all of them.")
    add("")
    add("- (a) keep the macron everywhere (current build),")
    add("- (b) drop it everywhere and print the roster spelling,")
    add("- (c) keep it only where the ledgers mostly use it, or")
    add("- (d) per name — tick individual rows above.")
    add("")
    add("Status: **pending**.")
    add("")
    add("## 2. Names written two ways in the ledgers")
    add("")
    add("These are not only macron differences: the walk itself uses more than")
    add("one spelling. A reader who types either one should land on the same")
    add("page, which the search index and the alias table already handle; the")
    add("question is which one the page is *titled* with.")
    add("")
    add(md_table(["Id", "Title today", "Spellings in the ledgers"],
                 [[f"`{v['id']}`", v["shown"], fmt_forms(v["forms"])]
                  for v in variants]))
    add("")
    add("Decision D2: for each row, which spelling is the title? The others")
    add("become aliases. Status: **pending**.")
    add("")
    add("## 3. Other spellings the walk wrote")
    add("")
    add("Everything a reader might type that is not the title: shortened,")
    add("macron-free and plain wrong forms, with how often the ledgers use")
    add("them. They are already aliases, so search resolves them and the")
    add("entity page lists them under the title. Nothing to decide here;")
    add("this is the evidence that the 'also written as' line is complete.")
    add("")
    add(md_table(["Id", "Title", "Forms attested in `ledgers/`"],
                 [[f"`{m['id']}`", m["shown"],
                   ", ".join(f"`{f}` ×{n}" for f, n, _t in m["forms"])]
                  for m in misspelt]))
    add("")
    add("## 4. Ids that differ between the walk and the roster")
    add("")
    add("A ledger is filed under the id the walk wrote into it; the roster and")
    add("the pages use the imported id. `kb/site_ledgers.py: LEDGER_ALIAS` is")
    add("the only table that pairs them, so this list is the whole exception")
    add("set.")
    add("")
    add(md_table(["Kind", "Ledger stem", "Page id"],
                 [[k, f"`{s}`", f"`{p}`"] for k, s, p in ids]))
    add("")
    add("Decision D3: keep pairing them this way, or rename the ledger / the")
    add("roster row so the ids agree. Status: **pending** (current pairing")
    add("works and every link resolves).")
    add("")
    add("## 5. Aliases claimed by more than one entity")
    add("")
    add("A shared alias still resolves in search but is stripped from the")
    add("entity's alias list, because one name cannot belong to two pages.")
    add("These need a qualifier or a decision to drop the alias.")
    add("")
    add(md_table(["Alias", "Claimed by"],
                 [[f"`{k}`", "; ".join(f"{t}:`{i}` ({a})" for t, i, a in v)]
                  for k, v in amb]))
    add("")
    add("Decision D4: for each, keep the alias on the likelier owner and")
    add("qualify the other (e.g. `Horikita Suzune (student)`). Status:")
    add("**pending**.")
    add("")
    add("## 6. Mechanical macroniser errors")
    add("")
    add("`site_arch.macronize()` is the fallback for any name without an")
    add("`entity_names` row. It changes these names wrongly:")
    add("")
    if defects:
        add(md_table(["Id", "Roster spelling", "Macronised"],
                     [[f"`{c}`", r, m] for c, r, m in defects]))
    else:
        add("None found.")
    add("")
    add("`inoue-toa` already has a display row seeded from the wrong rule, so")
    add("fixing the rule alone would not change the page: correct the row.")
    add("")
    add("Decision D5: correct the row(s) by hand, or fix `macronize()` so the")
    add("`oue` ending stays unmarked, then reseed. Status: **pending**.")
    add("")
    add("## 7. What is already settled")
    add("")
    add("- Page titles, search, indexes, citations and scene links all read")
    add("  `entity_names`; there is no second spelling table.")
    add("- Ledger text is never rewritten: a quote keeps the spelling the")
    add("  walk transcribed, whatever the title says.")
    add("- Search is accent- and case-insensitive, so `Kikyou` and `Kikyō`")
    add("  reach the same page regardless of the decision above.")
    add("")

    body = "\n".join(lines)
    if args.prn:
        print(body)
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    print(f"naming: {len(pairs)} macron rows, {len(variants)} variant rows, "
          f"{len(ids)} id pairs, {len(amb)} ambiguous aliases, "
          f"{len(defects)} macroniser defects → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

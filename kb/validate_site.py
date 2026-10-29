#!/usr/bin/env python3
"""Validate a BUILT site (default: docs/) against kb/schema/rules.json.

No database, no corpus, no third-party packages: it reads only the HTML that
the build produced, so it can run anywhere (laptop, CI, another model's
sandbox).

    python3 kb/validate_site.py                    # check docs/ vs baseline
    python3 kb/validate_site.py --strict           # ignore baseline, show all
    python3 kb/validate_site.py --update-baseline  # accept today's counts
    python3 kb/validate_site.py --site share/site  # another build dir
    python3 kb/validate_site.py --rule R08 --all   # every hit for one rule

Exit code 0: no rule got worse than the baseline (and no error rule is above
zero in --strict mode). Exit code 1: at least one rule got worse.

The baseline is a ratchet. It records how many violations each rule had when
it was last accepted; a build may lower a count but never raise it. When a
count reaches zero, run --update-baseline and the rule is locked at zero.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import html
import json
import posixpath
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "kb" / "schema" / "rules.json"
BASELINE_PATH = ROOT / "kb" / "schema" / "validate_baseline.json"
MARKERS_JSON = ROOT / "gen" / "markers.json"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


# ----------------------------------------------------------------- parsing
class Page(HTMLParser):
    """Collects what the rules need, in one pass over one HTML file."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[dict] = []
        self.h1 = 0
        self.ids: list[str] = []
        self.title = ""
        self.refresh = None
        self.links: list[dict] = []
        self.mlabels: list[str] = []
        self.has_crumbs = False
        self.tabs: list[str] = []
        self.words = 0
        self.scene_blocks = 0
        self.ledger_rows = 0
        self.text: list[str] = []
        self.raw = ""
        self._in_title = False
        self._cur_a: dict | None = None
        self._in_mlabel = False
        self._mlabel_buf: list[str] = []
        self._skip = 0
        self._serial = 0

    # helpers
    def _anc(self, pred):
        return any(pred(n) for n in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        node = {"tag": tag, "cls": cls, "id": a.get("id")}
        if tag in ("p", "li"):
            self._serial += 1
            node["serial"] = self._serial
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "title":
            self._in_title = True
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            m = re.search(r"url=(.+)$", a.get("content") or "", re.I)
            self.refresh = m.group(1).strip() if m else ""
        if tag == "nav" and "crumbs" in cls:
            self.has_crumbs = True
        if (tag == "details" and "scene" in cls) or (tag == "article" and "card" in cls):
            self.scene_blocks += 1
        if tag == "li" and any(c.startswith("e-") for c in cls):
            self.ledger_rows += 1
        if tag == "span" and "mlabel" in cls:
            self._in_mlabel = True
            self._mlabel_buf = []

        if tag == "a" and a.get("href") is not None:
            in_tabs = self._anc(lambda n: n["tag"] == "nav" and "tabs" in n["cls"])
            in_left = self._anc(lambda n: n["tag"] == "nav" and "rail" in n["cls"]
                                and "left" in n["cls"])
            in_main = self._anc(lambda n: n["tag"] == "main")
            in_quote = self._anc(lambda n: "verb" in n["cls"]) and not self._anc(
                lambda n: "by" in n["cls"] or "pin" in n["cls"])
            block = next((self.stack[i]["serial"]
                          for i in range(len(self.stack) - 1, -1, -1)
                          if self.stack[i]["tag"] in ("p", "li")), None)
            self._cur_a = {"href": a["href"], "cls": cls, "text": [],
                           "tabs": in_tabs, "left": in_left, "main": in_main,
                           "quote": in_quote, "block": block,
                           "has_pageref": False}
            if in_tabs:
                self.tabs.append(a["href"])
        if self._cur_a is not None and tag != "a" and self._cur_a["text"]:
            self._cur_a["text"].append(" ")
        if tag == "span" and "pageref" in cls and self._cur_a is not None:
            self._cur_a["has_pageref"] = True

        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        if tag == "span" and self._in_mlabel:
            self._in_mlabel = False
            self.mlabels.append("".join(self._mlabel_buf).strip())
        if tag == "a" and self._cur_a is not None:
            self._cur_a["text"] = re.sub(r"\s+", " ", "".join(self._cur_a["text"])).strip()
            self.links.append(self._cur_a)
            self._cur_a = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._skip:
            return
        if self._cur_a is not None:
            self._cur_a["text"].append(data)
        if self._in_mlabel:
            self._mlabel_buf.append(data)
        if self._anc(lambda n: n["tag"] == "main"):
            self.words += len(data.split())
            self.text.append(data)


# ----------------------------------------------------------------- helpers
def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()


def page_type(rel: str, rules: dict) -> str:
    for pat, t in rules["page_types"]:
        if fnmatch.fnmatch(rel, pat):
            return t
    return "other"


def matches_any(rel: str, pats: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, p) for p in pats)


def resolve(from_rel: str, href: str) -> tuple[str | None, str]:
    """-> (target path relative to site root or None if external, fragment)."""
    if re.match(r"^(https?:|mailto:|tel:|javascript:|data:)", href):
        return None, ""
    path, _, frag = href.partition("#")
    path = path.split("?")[0]
    if not path:
        return from_rel, frag
    base = posixpath.dirname(from_rel)
    target = posixpath.normpath(posixpath.join(base, path))
    if target.endswith("/") or target in (".", ""):
        target = posixpath.join(target, "index.html")
    return target, frag


def known_marker_labels() -> set[str]:
    """Reader labels a row may carry: the values of gen/markers.json."""
    try:
        return set(json.loads(MARKERS_JSON.read_text(encoding="utf-8")).values())
    except (OSError, ValueError):
        return set()


BLOCKS = re.compile(r'<article class="card".*?</article>|<details class="chap".*?</details>|<ol class="rules">.*?</ol>', re.S)
QUOTE_LI = re.compile(r'<li class="q [^"]*">.*?</li>|<li><span class="mlabel">(?:Spoken|Asked|Inner voice|Narration|Voice)</span>.*?</li>', re.S)


def prose(markup: str) -> str:
    """Published prose of evidence blocks, minus quoted lines (speech may say 'you')."""
    blocks = BLOCKS.findall(markup)
    text = html.unescape(re.sub(r"<[^>]+>", " ", " ".join(QUOTE_LI.sub(" ", b) for b in blocks)))
    return re.sub(r"“[^”]*”|\"[^\"]*\"", " ", text)


def payload_prose(site: Path) -> dict[str, str]:
    out = {}
    d = site / "assets" / "s"
    if d.is_dir():
        for f in d.glob("*.js"):
            m = re.search(r"CARDS\[[^\]]*\]=(.*);\s*$", f.read_text(encoding="utf-8"), re.S)
            if m:
                out[f.stem] = prose(" ".join(it["h"] for it in json.loads(m.group(1))))
    return out


def payload_ids(site: Path) -> dict[str, set[str]]:
    """Scene ids inside the lazy payload files, by page key."""
    out = {}
    d = site / "assets" / "s"
    if d.is_dir():
        for f in d.glob("*.js"):
            out[f.stem] = set(re.findall(r'"i":"([^"]+)"', f.read_text(encoding="utf-8")))
    return out


# ------------------------------------------------------------------ checks
def run(site: Path, rules: dict):
    pages: dict[str, Page] = {}
    for f in sorted(site.rglob("*.html")):
        rel = f.relative_to(site).as_posix()
        p = Page()
        try:
            p.raw = f.read_text(encoding="utf-8", errors="replace")
            p.feed(p.raw)
        except Exception as e:  # malformed HTML should be reported, not crash
            p.title = f"<parse error: {e}>"
        pages[rel] = p

    hits: dict[str, list[str]] = defaultdict(list)
    add = lambda rule, msg: hits[rule].append(msg)

    titles = {rel: re.sub(r"\s*·\s*COTE Knowledge Base\s*$", "", p.title).strip()
              for rel, p in pages.items()}
    labels = known_marker_labels()
    tab_order = rules["tabs"]["order"]
    payload = payload_ids(site)
    vocab = re.compile(rules["wording"]["banned_vocabulary"], re.I)
    second = re.compile(rules["wording"]["second_person"], re.I)
    for key, txt in payload_prose(site).items():
        for m_ in vocab.finditer(txt):
            add("R18_wording", f"assets/s/{key}.js: pipeline word '{m_.group(0)}'")
        for m_ in second.finditer(txt):
            add("R19_second_person", f"assets/s/{key}.js: second person '{m_.group(0)}'")
    cite_re = re.compile(rules["citation_pattern"])
    tab_labels = {fold(lbl): tgt for tgt, lbl in rules["tabs"]["labels"].items()}
    ent_targets = rules["entity_link_targets"]
    ent_skip = rules["entity_link_skip_targets"]

    for rel, p in pages.items():
        ptype = page_type(rel, rules)

        # R16: redirect pages are checked only for their target
        if p.refresh is not None:
            tgt, _ = resolve(rel, p.refresh)
            if tgt is None or tgt not in pages:
                add("R16_redirect_target", f"{rel} -> {p.refresh}")
            continue

        if p.h1 != 1:
            add("R01_one_h1", f"{rel}: {p.h1} <h1>")
        dups = [k for k, n in Counter(p.ids).items() if n > 1]
        for d in dups:
            add("R02_duplicate_ids", f"{rel}: id={d}")
        if ptype not in rules["breadcrumb_exempt"] and not p.has_crumbs:
            add("R05_no_breadcrumb", rel)

        tab_targets = [resolve(rel, h)[0] for h in p.tabs]
        tab_targets = [t for t in tab_targets if t and t != rules["home"]]
        if tab_targets != tab_order:
            add("R06_tab_order", f"{rel}: {tab_targets}")
        tabset = set(tab_targets) | {rules["home"]}

        body_text = " ".join(p.text)
        for m_ in vocab.finditer(body_text):
            add("R18_wording", f"{rel}: pipeline word '{m_.group(0)}'")
        for m_ in second.finditer(prose(p.raw)):
            add("R19_second_person", f"{rel}: second person '{m_.group(0)}' in published prose")
        if p.words > rules["max_words"].get(ptype, 10 ** 9):
            add("R12_page_too_big", f"{rel} ({ptype}): {p.words} words > "
                f"{rules['max_words'][ptype]}")
        if ptype in rules["no_evidence_on"] and (p.scene_blocks or p.ledger_rows):
            add("R13_evidence_on_index",
                f"{rel} ({ptype}): {p.scene_blocks} scenes, {p.ledger_rows} rows")
        if labels:
            for lab in sorted(set(p.mlabels)):
                if lab and lab not in labels:
                    add("R14_unlabelled_marker", f"{rel}: '{lab}'")

        seen_in_block: dict[int, Counter] = defaultdict(Counter)
        for ln in p.links:
            tgt, frag = resolve(rel, ln["href"])
            if tgt is None:
                continue
            text = ln["text"]
            # R03 / R04
            if tgt not in pages:
                if not (site / tgt).exists():
                    add("R03_broken_link", f"{rel} -> {ln['href']}")
                continue
            if frag and frag not in pages[tgt].ids and frag != "top":
                key = tgt[:-5].replace("/", "-")
                if frag not in payload.get(key, ()):
                    add("R04_broken_anchor", f"{rel} -> {ln['href']}")
            # R07
            if ln["left"] and tgt in tabset and tgt != rel:
                add("R07_rail_repeats_tab", f"{rel}: '{text}' -> {tgt}")
            # R08
            if ln["has_pageref"] or cite_re.match(text):
                add("R08_citation_linked", f"{rel}: '{text[:40]}' -> {ln['href']}")
            # R09
            if ln["quote"]:
                add("R09_link_in_quote", f"{rel}: '{text[:40]}'")
            # R17
            lab = fold(text)
            if lab in tab_labels and tab_labels[lab] != tgt and not ln["quote"]:
                add("R17_label_mismatch",
                    f"{rel}: '{text}' goes to {tgt}, expected {tab_labels[lab]}")
            # R10
            if not re.search(r"[A-Za-z0-9\u00C0-\u024F\u3040-\u30FF\u4E00-\u9FFF]", text):
                add("R10_empty_link_text", f"{rel} -> {ln['href']} text='{text}'")
            # R11
            if ln["block"] is not None and not ln["tabs"] and not ln["left"]:
                seen_in_block[ln["block"]][ln["href"]] += 1
            # R15
            if (ln["main"] or not ln["left"]) and not ln["tabs"] and not frag \
                    and matches_any(tgt, ent_targets) and not matches_any(tgt, ent_skip) \
                    and "vlink" not in ln["cls"] and not ln["quote"]:
                title_words = set(fold(titles.get(tgt, "")).split())
                words = fold(text).split()
                if words and title_words and not set(words) <= title_words:
                    add("R15_entity_link_text", f"{rel}: '{text}' -> {tgt} ({titles[tgt]})")
        for blk, c in seen_in_block.items():
            for href, n in c.items():
                if n > 1 and not href.startswith("#"):
                    add("R11_duplicate_link", f"{rel}: {href} x{n}")
    return pages, hits


# ------------------------------------------------------------------ report
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", default="docs", help="built site directory")
    ap.add_argument("--strict", action="store_true", help="ignore the baseline")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--rule", help="only this rule (prefix ok, e.g. R08)")
    ap.add_argument("--all", action="store_true", help="print every hit")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--examples", type=int, default=4)
    args = ap.parse_args(argv)

    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    site = (ROOT / args.site) if not Path(args.site).is_absolute() else Path(args.site)
    if not site.is_dir():
        print(f"site directory not found: {site}", file=sys.stderr)
        return 2

    pages, hits = run(site, rules)
    counts = {r: len(hits.get(r, [])) for r in rules["rules"]}

    if args.update_baseline:
        BASELINE_PATH.write_text(json.dumps(counts, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
        print(f"baseline written: {BASELINE_PATH.relative_to(ROOT)}")
        return 0

    baseline = {}
    if BASELINE_PATH.exists() and not args.strict:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    worse, better, fail_strict = [], [], []
    for r, spec in rules["rules"].items():
        n = counts[r]
        if args.strict:
            if n and spec["level"] == "error":
                fail_strict.append(r)
        else:
            b = baseline.get(r)
            if b is not None and n > b:
                worse.append(r)
            elif b is not None and n < b:
                better.append(r)
            elif b is None and n and spec["level"] == "error":
                worse.append(r)

    if args.json:
        print(json.dumps({"pages": len(pages), "counts": counts,
                          "baseline": baseline, "worse": worse}, indent=2))
    else:
        print(f"site: {site.relative_to(ROOT) if site.is_relative_to(ROOT) else site}"
              f"   pages: {len(pages)}   mode: {'strict' if args.strict else 'ratchet'}")
        print()
        print(f"{'rule':26} {'level':6} {'now':>6} {'base':>6}   what")
        for r, spec in rules["rules"].items():
            if args.rule and not r.startswith(args.rule):
                continue
            b = baseline.get(r, "-")
            flag = " <-- WORSE" if r in worse else (" (better)" if r in better else "")
            print(f"{r:26} {spec['level']:6} {counts[r]:>6} {str(b):>6}   "
                  f"{spec['what']}{flag}")
            show = hits.get(r, []) if args.all else hits.get(r, [])[:args.examples]
            if (args.all or args.rule or r in worse) and show:
                for line in show:
                    print(f"      {line}")
                if not args.all and counts[r] > len(show):
                    print(f"      ... and {counts[r] - len(show)} more (use --all)")
        print()
        if worse or fail_strict:
            bad = worse or fail_strict
            print("FAIL:", ", ".join(bad))
        else:
            print("OK: nothing got worse than the baseline."
                  if not args.strict else "OK: no error-level violations.")
            if better:
                print("Improved:", ", ".join(better),
                      "- run --update-baseline to lock the gain in.")
    return 1 if (worse or fail_strict) else 0


if __name__ == "__main__":
    sys.exit(main())

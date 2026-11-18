"""Load content/ and ledgers/ into one plain model. No database, no corpus.

content/*.tsv      the roster: volumes, characters, exams, systems, places, topics
content/config.json thresholds (tiers, own-page rule, page sizes)
ledgers/<kind>/<id>.md  the evidence: page-anchored scenes, one file per entity
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
LEDGERS = ROOT / "ledgers"
CFG = json.loads((CONTENT / "config.json").read_text(encoding="utf-8"))
MARKERS = json.loads((Path(__file__).parent / "markers.json").read_text(encoding="utf-8"))

KIND_OF = {"says": "spoken", "say": "spoken", "ask": "spoken",
           "thinks": "inner", "think": "inner", "narrates": "narration"}
VOLRE = r"y0|y\d+v\d+(?:\.\d+)?"
VOLH = re.compile(rf"^##\s+({VOLRE})\s*$")
HEAD = re.compile(r"^###\s+(.*?)\s*$")
SHEAD = re.compile(rf"^({VOLRE})\s+(pp?\.[^—]*?)\s*—\s*(.+)$")
ENTRY = re.compile(r"^\[([a-z]+)(?::([A-Za-z0-9._-]+))?\]\s*(.*)$")
PGPFX = re.compile(r"^\((pp?\.[^)]*)\)\s*")
BOOK = re.compile(r"^(walk|coverage|chunks?|progress)\s*:", re.I)
DONE = re.compile(r"<!--[^>]*→\s*DONE")


def tsv(name):
    with open(CONTENT / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def fold(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()


def pnum(label):
    m = re.search(r"\d+", label or "")
    return int(m.group()) if m else 0


class Model:
    def __init__(self):
        self.cfg = CFG
        self.vols = []
        for r in tsv("volumes.tsv"):
            y, n = int(r["year"]), float(r["number"])
            short = "Side stories" if r["id"] == "y0" else f"Y{y}V{r['number']}"
            self.vols.append({"id": r["id"], "year": y, "num": n, "label": r["label"],
                              "short": short, "ord": 0})
        self.vols.sort(key=lambda v: (v["year"] or 9, v["num"]))
        for i, v in enumerate(self.vols, 1):
            v["ord"] = i
        self.vol = {v["id"]: v for v in self.vols}

        self.chars = {r["id"]: {**r, "aliases": [a for a in r["aliases"].split(";") if a],
                                "volumes": [v for v in r["volumes"].split(";") if v in self.vol]}
                      for r in tsv("characters.tsv")}
        self.exams = self._ents("exams.tsv")
        self.systems = self._ents("systems.tsv")
        self.places = self._ents("places.tsv")
        self.topics = tsv("topics.tsv")
        self.threads = tsv("threads.tsv")
        self.kinds = {"people": self.chars, "exams": self.exams,
                      "systems": self.systems, "places": self.places}

        self.ledger = {}
        self.vol_ledger = {}
        self.scenes = []
        self._load_ledgers()
        self._check_markers()
        self._link_scenes()
        self._tiers()

    # ---------------------------------------------------------------- roster
    def _ents(self, fn):
        return {r["id"]: {**r, "volumes": [v for v in r["volumes"].split(";") if v in self.vol]}
                for r in tsv(fn)}

    def name(self, kind, eid):
        e = self.kinds.get(kind, {}).get(eid)
        return e["name"] if e else eid

    def human(self, text):
        text = text.replace("$\\rightarrow$", "→").replace('\\"', '"')
        return re.sub(rf"\b({VOLRE})\b",
                      lambda m: self.vol[m.group(1)]["label"].replace("Volume", "Vol.")
                      if m.group(1) in self.vol else m.group(1), text)

    # --------------------------------------------------------------- ledgers
    def _load_ledgers(self):
        for kind in ("people", "exams", "systems", "places"):
            d = LEDGERS / kind
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.md")):
                text = f.read_text(encoding="utf-8")
                meta = {}
                for line in text.split("\n## ", 1)[0].splitlines():
                    for part in re.split(r"\s+·\s+", line.strip()):
                        k, _, v = part.partition(":")
                        if v and re.match(r"^[a-z_ ]+$", k.strip()):
                            meta.setdefault(k.strip().replace(" ", "_"), v.strip())
                self.ledger[(kind, f.stem)] = {"meta": meta,
                                               "blocks": self._blocks(text)}
        for f in sorted((LEDGERS / "volumes").glob("*.md")):
            self.vol_ledger[f.stem] = {"done": bool(DONE.search(f.read_text(encoding="utf-8"))),
                                       "chapters": self._chapters(f.read_text(encoding="utf-8"))}

    def _check_markers(self):
        bad = {}
        for (kind, eid), led in self.ledger.items():
            for b in led["blocks"]:
                for r in b["rows"]:
                    if r["m"] not in MARKERS:
                        bad.setdefault(r["m"], f"ledgers/{kind}/{eid}.md")
        if bad:
            raise SystemExit("unknown ledger marker: " + "; ".join(
                f"[{m}] first seen in {f}" for m, f in sorted(bad.items()))
                + ". Add a reader label to gen/markers.json (the owner approves new labels).")

    def _blocks(self, text):
        out, vol, cur = [], None, None
        for line in text.splitlines():
            m = VOLH.match(line)
            if m:
                vol, cur = m.group(1), None
                continue
            h = HEAD.match(line)
            if h:
                sh = SHEAD.match(h.group(1))
                if sh:
                    cur = {"vol": sh.group(1), "pages": sh.group(2).replace("pp.", "p.").strip(),
                           "title": self.human(sh.group(3)), "rows": []}
                else:
                    cur = {"vol": vol, "pages": "", "title": self.human(h.group(1)), "rows": []}
                if cur["vol"] in self.vol:
                    out.append(cur)
                else:
                    cur = None
                continue
            s = line.strip()
            if cur is None or not s or s.startswith(("<!--", "#")) or BOOK.match(s):
                continue
            m = ENTRY.match(s)
            if m:
                rest, pg = m.group(3), ""
                pm = PGPFX.match(rest)
                if pm:
                    pg, rest = pm.group(1).replace("pp.", "p."), rest[pm.end():]
                cur["rows"].append({"m": m.group(1), "t": m.group(2) or "", "pg": pg,
                                    "text": self.human(rest.strip())})
            elif cur["rows"]:
                cur["rows"][-1]["text"] += " " + self.human(re.sub(r"^[-*]\s+", "", s))
        return out

    def _chapters(self, text):
        chapters, cur, sec = [], None, None
        for line in text.splitlines():
            h = HEAD.match(line)
            if h:
                t = h.group(1)
                pm = re.search(r"\((pp?\.?\s*[\d–\-]+)\)\s*$", t)
                pages = ("p." + re.sub(r"^pp?\.?\s*", "", pm.group(1)).replace("-", "–")) if pm else ""
                cur = {"title": self.human(re.sub(r"\s*\(pp?\.?[^)]*\)\s*$", "", t)),
                       "pages": pages, "secs": []}
                chapters.append(cur)
                sec = None
                continue
            if cur is None:
                continue
            top = re.match(r"^- \*\*(.+?):?\*\*:?\s*(.*)$", line)
            sub = re.match(r"^\s+[-*]\s+(.*)$", line)
            if top:
                sec = {"key": top.group(1).strip(": "), "text": self.human(re.sub(r"\*(.+?)\*", r"\1", top.group(2))), "items": []}
                cur["secs"].append(sec)
            elif sub and sec is not None:
                sec["items"].append(self.human(re.sub(r"\*+(.+?)\*+", r"\1", sub.group(1))))
        return chapters

    # ---------------------------------------------------------------- scenes
    def _link_scenes(self):
        seen = Counter()
        for (kind, eid), led in sorted(self.ledger.items()):
            for b in led["blocks"]:
                p0 = pnum(b["pages"]) or next((pnum(r["pg"]) for r in b["rows"] if r["pg"]), 0)
                seen[(kind, eid, b["vol"], p0)] += 1
                sid = f"sc-{eid}-{b['vol'].replace('.', '_')}-p{p0}-{seen[(kind, eid, b['vol'], p0)]}"
                quotes = []
                for r in b["rows"]:
                    if r["m"] in KIND_OF:
                        who = r["t"] if r["t"] else (eid if kind == "people" else "")
                        quotes.append({"kind": KIND_OF[r["m"]], "who": who, "pg": r["pg"],
                                       "text": r["text"], "row": r})
                with_ = []
                for r in b["rows"]:
                    for t in ([r["t"]] if r["m"] == "rel" else []) + ([r["t"]] if r["m"] in KIND_OF else []):
                        if t and t != eid and t not in with_:
                            with_.append(t)
                s = {"id": sid, "owner": (kind, eid), "vol": b["vol"], "year": self.vol[b["vol"]]["year"],
                     "ord": self.vol[b["vol"]]["ord"], "pages": b["pages"], "p0": p0,
                     "title": b["title"], "rows": b["rows"], "quotes": quotes, "with": with_,
                     "setup": " ".join(r["text"] for r in b["rows"] if r["m"] == "scene"),
                     "mentioned": any(r["m"] == "mentioned" for r in b["rows"]),
                     "places": [r["t"] for r in b["rows"] if r["m"] == "place" and r["t"] in self.places],
                     "exams": [r["t"] for r in b["rows"] if r["m"] == "exam" and r["t"] in self.exams],
                     "prev": None, "next": None}
                self.scenes.append(s)
        self.scenes.sort(key=lambda s: (s["ord"], s["p0"], s["owner"], s["id"]))
        by = defaultdict(list)
        for s in self.scenes:
            by[(s["owner"], s["vol"])].append(s)
        for lst in by.values():
            for a, b in zip(lst, lst[1:]):
                a["next"], b["prev"] = b, a
        self.by_id = {s["id"]: s for s in self.scenes}

    def scenes_of(self, kind, eid):
        return [s for s in self.scenes if s["owner"] == (kind, eid)]

    def scenes_in(self, vol):
        return [s for s in self.scenes if s["vol"] == vol]

    def scenes_tagged(self, field, eid):
        return [s for s in self.scenes if eid in s[field]]

    # ------------------------------------------------------------ tiers etc.
    def _tiers(self):
        scopes = {"all": self.vols, **{str(y): [v for v in self.vols if v["year"] == y]
                                       for y in (1, 2, 3)}}
        for c in self.chars.values():
            c["tier"] = {}
            for key, vs in scopes.items():
                ids = {v["id"] for v in vs}
                n = sum(1 for v in c["volumes"] if v in ids)
                share = n / len(vs) if vs else 0
                c["tier"][key] = ("main" if share >= CFG["main_share"] else
                                  "supporting" if share >= CFG["supporting_share"] else
                                  "minor") if (n or key == "all") else ""
            sc = self.scenes_of("people", c["id"])
            real_sc = [s for s in sc if not s.get("mentioned")]
            mentions = [s for s in sc if s.get("mentioned")]
            lines = sum(len(s["quotes"]) for s in real_sc)
            c["scenes"], c["lines"] = len(real_sc), lines
            c["mentions"] = len(mentions)
            c["read_vols"] = sorted({s["vol"] for s in real_sc}, key=lambda v: self.vol[v]["ord"])
            c["has_page"] = (len(real_sc) >= CFG["page_min_scenes"] or lines >= CFG["page_min_lines"])
            led = self.ledger.get(("people", c["id"]), {"meta": {}, "blocks": []})
            m = re.search(r"Class\s+([0-9]-[A-D])", led["meta"].get("class", ""))
            roles = sorted({r["t"] for b in led["blocks"] for r in b["rows"] if r["m"] == "role" and r["t"]})
            c["roles"] = roles
            c["class"] = m.group(1) if m else next(
                (re.sub(r"class-(\d)([a-d])", lambda x: f"{x.group(1)}-{x.group(2).upper()}", r) for r in roles
                 if re.fullmatch(r"class-\d[a-d]", r)), "")

    def vol_state(self, vid):
        n = len(self.scenes_in(vid))
        led = self.vol_ledger.get(vid)
        if led and led["done"]:
            return "complete"
        return "partial" if (n or led) else "stub"

    def relations(self, cid):
        cnt = Counter()
        for s in self.scenes_of("people", cid):
            for r in s["rows"]:
                if r["m"] == "rel" and r["t"] in self.chars and r["t"] != cid:
                    cnt[r["t"]] += 1
        return cnt.most_common()

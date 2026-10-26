#!/usr/bin/env python3
"""Render a per-volume scene transcript from a walk ledger.

Reads ledgers/people/<char_id>.md (tag grammar: [says], [says:<id>], [thinks],
[back], [back:<id>], scene headers), emits chronological transcript markdown
with speaker display names and page anchors. Source of truth stays the ledger;
this is a view.

Usage: python3 kb/ledger_transcript.py <char_id> --vol y1v1 [-o out.md]
"""
import argparse
import re
import sys
from pathlib import Path

DISPLAY = {
    "ayanokouji-kiyotaka": "Ayanokōji Kiyotaka",
    "horikita-suzune": "Horikita Suzune",
    "horikita-manabu": "Horikita Manabu",
    "kushida-kikyou": "Kushida Kikyō",
    "hirata-yousuke": "Hirata Yōsuke",
    "ike-kanji": "Ike Kanji",
    "yamauchi": "Yamauchi",
    "sudou": "Sudō",
    "koenji-souta": "Koenji Sōta",
    "chiyabashira-sae": "Chiyabashira Sae",
    "hoshinomiya-chie": "Hoshinomiya Chie",
    "karuizawa-kei": "Karuizawa Kei",
    "ichinose-honami": "Ichinose Honami",
    "ryuuen-kakeru": "Ryūen Kakeru",
    "sakayanagi-arisu": "Sakayanagi Arisu",
}

VOL_LABEL = {
    "y1v1": "Year 1, Volume 1",
}

TAG_RE = re.compile(r"^\[(says|thinks|back)(?::([a-z0-9-]+))?\]\s*(\(p\.\d+(?:-\d+)?\))\s*(.*)$")
HDR_RE = re.compile(r"^### (y1v\d+(?:\.\d+)?) p\.(\d+)(?:-(\d+))? — (.+)$")


def curly(s: str) -> str:
    s = s.replace("**", "")  # ledger emphasis markers don't belong in the transcript view
    # normalize straight quotes to typographic pair, keep elipses/inner quotes simple
    out, open_q = [], True
    for i, ch in enumerate(s):
        if ch == '"':
            out.append("“" if open_q else "”")
            open_q = not open_q
        else:
            out.append(ch)
    return "".join(out)


def speaker_line(tag: str, char_id: str, kind: str) -> str:
    who = tag or char_id
    name = DISPLAY.get(who, who)
    if not tag and who == char_id and kind in ("thinks",):
        return "Ayanokōji (inner)"
    if not tag and who == char_id and kind == "back":
        return "Ayanokōji (narrated)"
    return name


def build(ledger: Path, vol: str, char_id: str) -> str:
    lines = ledger.read_text(encoding="utf-8").splitlines()
    in_vol = False
    rows = []  # (page, kind_order, heading, speaker, text)
    heading = "(opening)"
    for ln in lines:
        if ln.startswith("## "):
            in_vol = ln.strip() == f"## {vol}"
            continue
        if not in_vol:
            continue
        if ln.startswith("### "):
            m = HDR_RE.match(ln)
            if m and m.group(1).startswith(vol):
                hi = m.group(3) or m.group(2)
                heading = f"{VOL_LABEL.get(vol, vol)}, p.{m.group(2)}–{hi} — {m.group(4)}"
            continue
        m = TAG_RE.match(ln.strip())
        if not m:
            continue
        kind, tag, anchor, rest = m.groups()
        if kind not in ("says", "thinks", "back"):
            continue
        page = int(anchor.strip("()p. ").split("-")[0])
        speaker = speaker_line(tag or "", char_id, kind)
        kind_order = {"says": 0, "back": 1, "thinks": 2}[kind]
        rows.append((page, kind_order, heading, speaker, curly(rest.strip()), kind))

    label = VOL_LABEL.get(vol, vol)
    out = [f"# {DISPLAY.get(char_id, char_id)} — {label} scene transcript", ""]
    out.append(
        f"Scene by scene: the speech lines, narration beats, and inner monologue of {label}, "
        f"quoted verbatim with page numbers (e.g. p.247)."
    )
    out.append("")
    last_h = None
    for page, _ko, heading, speaker, text, kind in rows:
        if heading != last_h:
            if last_h is not None:
                out.append("")
            out.append(f"## {heading}")
            out.append("")
            last_h = heading
        verb = {"says": "said", "thinks": "mused", "back": "narrated"}[kind]
        out.append(f"- **[p.{page}]** {speaker} {verb}: {text}")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("char_id")
    ap.add_argument("--vol", required=True)
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()
    ledger = Path("ledgers/people") / f"{args.char_id}.md"
    if not ledger.exists():
        print(f"missing ledger: {ledger}", file=sys.stderr)
        return 1
    md = build(ledger, args.vol, args.char_id)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"wrote {args.out} ({len(md)} bytes)")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())

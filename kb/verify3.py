"""Verify every non-[says] quoted ledger string against its volume's corpus text.

Usage: python3 kb/verify_ledgers_nonsays.py <volkey>   (default y1v1)

Volume context per line: file name ledgers/volumes/<volkey>.md, or the most
recent ##/### heading carrying a volume token.  Checks lines with (p.N)/(pp. N)
anchors and a >=10-char quoted span, excluding [says] lines: NFKC
alphanumeric-stream containment in the +-5 page window, then full-volume
fallback.  Watermark/header lines stripped.
"""
import re
import sys
import glob
import os
import unicodedata

os.chdir("/home/user3/Documents/unsafe/cote")

VOL_TOKEN_RE = re.compile(r"\b((?:y\d+v|v)\d+(?:\.\d+)?|v0)\b")
SKIP_LINE_RE = re.compile(r"(?i)^(goldenagato|royalmtls?|legacyemtls|page\|\d+)")


def fold_vol(stem):
    s = unicodedata.normalize("NFKD", stem.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("cote", "").replace(" ", "").replace(".", "")


def vol_files():
    out = {}
    for fn in sorted(os.listdir("text")):
        if fn.endswith(".txt"):
            out[fold_vol(fn[:-4])] = os.path.join("text", fn)
    return out


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    for k, v in {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                 "\u2014": "-", "\u2013": "-", "\u2026": "..."}.items():
        s = s.replace(k, v)
    return re.sub(r"[^0-9a-z\u3040-\u30ff\u4e00-\u9fff]+", "", s.lower())


def load_pages(volfile):
    raw = open(volfile, encoding="utf-8").read()
    pages = {}
    cur = 0
    buf = []
    for l in raw.splitlines():
        m = re.match(r"^--- page (\d+) ---$", l.strip())
        if m:
            if cur:
                pages[cur] = "\n".join(buf)
            cur = int(m.group(1))
            buf = []
            continue
        if SKIP_LINE_RE.match(l.strip()):
            continue
        buf.append(l)
    if cur:
        pages[cur] = "\n".join(buf)
    full = norm("\n".join(pages[p] for p in sorted(pages)))
    return pages, full


def line_vol(line, ctx):
    if not re.match(r"^#{2,3}\s", line):
        return ctx
    t = VOL_TOKEN_RE.search(line)
    return t.group(1) if t else ctx


def quoted_spans(line):
    """Every quoted span on a line, >10 chars.

    Pairing matters: the old single regex let a closing quote open the next
    span, so `notes "girly" type ... type: "kinder, more ladylike girl"`
    checked the prose *between* two real quotations and failed a line whose
    quotes were both verbatim. Curly quotes are directional, so pair them
    first and remove them; the remaining straight quotes then alternate
    open/close.
    """
    spans = [m.group(1) for m in re.finditer(r"\u201c([^\u201c\u201d]+)\u201d", line)]
    # Drop only the curly quote *characters*: deleting the span they wrap
    # would cut a hole in a straight-quoted passage and make the joined text
    # miss the source.
    rest = re.sub(r"[\u201c\u201d]", "", line)
    parts = rest.split('"')
    spans.extend(parts[i] for i in range(1, len(parts) - 1, 2))
    return [s for s in spans if len(s.strip()) >= 10]


def main():
    volkey = sys.argv[1] if len(sys.argv) > 1 else "y1v1"
    vf = vol_files()
    if volkey not in vf:
        sys.exit(f"unknown volume {volkey}: {sorted(vf)}")
    pages, full = load_pages(vf[volkey])
    fails = []
    total = 0
    for lf in sorted(glob.glob("ledgers/*/*.md")):
        stem = os.path.basename(lf)[:-3]
        ctx = stem if re.fullmatch(r"y\d+v[\d.]+|v0", stem) else None
        for i, line in enumerate(open(lf, encoding="utf-8"), 1):
            ctx = line_vol(line, ctx)
            if ctx != volkey:
                continue
            s = line.lstrip()
            if not (s.startswith("[") or s.startswith("-") or s.startswith("  ")):
                continue
            if re.match(r"\[says(:[\w-]+)?\]\s*\(p", s):
                continue
            pm = re.search(r"\((?:p|pp)\.\s*(\d+)", line)
            if not pm:
                continue
            first = int(pm.group(1))
            spans = quoted_spans(line)
            if not spans:
                continue
            total += 1
            local = norm("".join(pages.get(p, "") for p in range(max(1, first - 5), first + 6)))
            for span in spans:
                frags = [f for f in re.split(r"\s*\.\.\.\s*|\s*…\s*", span)
                         if len(f.strip()) >= 10]
                for f in frags:
                    nf = norm(f)
                    if not nf:
                        continue
                    if nf in local or nf in full:
                        continue
                    fails.append((lf, i, first, f[:90]))
                    break
                else:
                    continue
                break
    print(f"volume {volkey}: checked {total} non-says quoted lines")
    if not fails:
        print("ALL PASS")
    for f in fails:
        print("  FAIL", f[0], "L" + str(f[1]), "p." + str(f[2]), repr(f[3]))
    if fails:
        sys.exit(1)


main()

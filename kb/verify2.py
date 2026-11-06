"""Verify every [says] ledger quote against its volume's corpus text.

Usage: python3 kb/verify_ledgers_says.py <volkey>   (e.g. y1v2; default y1v1)

Volume context for each ledger line comes from the file name
(ledgers/volumes/<volkey>.md) or the most recent heading carrying a volume
token (## y1v2 / ### y1v2 p.12-39).  Lines are checked only against their own
volume: NFKC-normalized alphanumeric-stream containment in the cited +-5 page
window, then full-volume fallback.  Header/footer watermark lines are stripped.
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
    table = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2014": "-", "\u2013": "-", "\u2026": "...",
    }
    for k, v in table.items():
        s = s.replace(k, v)
    s = s.lower()
    return re.sub(r"[^0-9a-z\u3040-\u30ff\u4e00-\u9fff]+", "", s)


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
    m = re.match(r"^#{2,3}\s", line)
    if not m:
        return ctx
    t = VOL_TOKEN_RE.search(line)
    return t.group(1) if t else ctx


def extract_quote(line):
    m = re.search(r"\[says(?::[\w-]+)?\]\s*\(p\.[^)]*\)\s*[“\"](.+?)[”\"]", line)
    return m.group(1) if m else None


def main():
    volkey = sys.argv[1] if len(sys.argv) > 1 else "y1v1"
    vf = vol_files()
    key = fold_vol(volkey)
    if key not in vf:
        sys.exit(f"unknown volume {volkey}: {sorted(vf)}")
    pages, full = load_pages(vf[key])
    fails = []
    total = 0
    short = 0
    for lf in sorted(glob.glob("ledgers/*/*.md")):
        stem = os.path.basename(lf)[:-3]
        ctx = stem if re.fullmatch(r"y\d+v[\d.]+|v0", stem) else None
        for i, line in enumerate(open(lf, encoding="utf-8"), 1):
            ctx = line_vol(line, ctx)
            if not ctx or fold_vol(ctx) != key:
                continue
            if not re.match(r"\s*\[says(:[\w-]+)?\]\s*\(p\.", line):
                continue
            pm = re.search(r"\(p\.(\d+)", line)
            first_pg = int(pm.group(1))
            q = extract_quote(line)
            if q is None:
                continue
            total += 1
            frags = [f for f in re.split(r"\s*\.\.\.\s*|\s*…\s*", q) if len(f.strip()) >= 10]
            if not frags:
                short += 1
                continue
            local = norm("".join(pages.get(p, "") for p in range(max(1, first_pg - 5), first_pg + 6)))
            for f in frags:
                nf = norm(f)
                if not nf:
                    continue
                if nf in local or nf in full:
                    continue
                fails.append((lf, i, first_pg, f[:80]))
                break
    print(f"volume {volkey}: checked {total} [says] lines ({short} too short/skipped)")
    if not fails:
        print("ALL PASS")
    for f in fails:
        print(f"  FAIL {f[0]} L{f[1]} p.{f[2]}: {f[3]!r}")
    if fails:
        sys.exit(1)


main()

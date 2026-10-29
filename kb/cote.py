#!/usr/bin/env python3
"""cote.py — one entry point for the whole walk loop.

Every step of the COTE encyclopedia walk (read pages, append ledger rows, verify
quotes, rebuild the site, run the gate, update progress, commit, push) goes
through this file, so no ad-hoc sed/cat/grep/python one-liners are needed.

Usage:
  cote.py status
  cote.py next      [--vol y1v3]     (default: first unfinished volume)
  cote.py chapters  [--vol y1v3]     (default: first unfinished volume)
  cote.py read      --vol y1v2 --pages 158-163
  cote.py append    --file ledgers/people/sakura-airi.md --from drafts/ch5.md \
                    [--under y1v2] [--stamp "y1v2 ch5 -> p.189"] [--at-end]
  cote.py verify    [--vol y1v2]
  cote.py build
  cote.py gate
  cote.py hash      [docs]
  cote.py ship      --message-from drafts/msg.txt [--check] [--push]
  cote.py ledger-new people/kanzaki-ryuuji --header "char_id: kanzaki-ryuuji ..."

Paths are relative to the repo root; run from anywhere.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRESS = ["progress2.md", "progress3.md"]
SHIP_PATHS = ["AGENTS.md", "README.md", "Makefile", ".github", "content", "docs", "gen", "kb", "ledgers", "progress2.md", "progress3.md"]
NEVER_SHIP = re.compile(r"(^|/)(session-[^/]+|share|_sitecheck|cote_kb\.db|search\.db|text|gdrive_download)(/|$)")
STAMP_RE = re.compile(r"^<!--\s*walk:\s*(?P<inner>.*?)\s*-->\s*$")
HEAD_RE = re.compile(r"^##\s+(?P<vol>[A-Za-z0-9._-]+)\s*$")

AUTHOR_ENV = {
    "GIT_AUTHOR_NAME": "FakeAn",
    "GIT_AUTHOR_EMAIL": "FakeAn@users.noreply.github.com",
    "GIT_COMMITTER_NAME": "FakeAn",
    "GIT_COMMITTER_EMAIL": "FakeAn@users.noreply.github.com",
}


def die(msg: str, code: int = 2) -> "NoReturn":
    print(f"cote: {msg}", file=sys.stderr)
    raise SystemExit(code)


def git(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and proc.returncode != 0:
        die(f"git {' '.join(args)} failed:\n{proc.stdout}{proc.stderr}")
    return (proc.stdout + proc.stderr).strip()


def run(cmd: list[str], blurb: str) -> int:
    """Run a kb/ script, echoing its output, and return the exit code."""
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).rstrip()
    if out:
        print(out)
    return proc.returncode


def read(path: pathlib.Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        die(f"no such file: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    return path.read_text(encoding="utf-8")


def text_arg(inline: str | None, from_file: str | None, what: str) -> str:
    if bool(inline) == bool(from_file):
        die(f"give {what} either inline or with --from FILE (not both, not neither)")
    return inline if inline else read(pathlib.Path(from_file))


# ---------------------------------------------------------------- read / map


def cmd_read(a) -> int:
    cmd = [sys.executable, "kb/walk_locate.py", "extract", "--vol", a.vol]
    if a.pages:
        cmd += ["--pages", a.pages]
    code = run(cmd, "read")
    if a.blank:
        print("\n(blank-page scan)")
        report_blank_pages(a.vol, a.pages)
    return code


def parse_page_range(spec: str) -> range:
    if "-" in spec:
        lo, hi = spec.split("-", 1)
        return range(int(lo), int(hi) + 1)
    return range(int(spec), int(spec) + 1)


def volume_pages(vol: str, pages: str) -> dict[int, list[str]]:
    """Return {page: [prose lines]} for a range, watermarks already dropped."""
    proc = subprocess.run(
        [sys.executable, "kb/walk_locate.py", "extract", "--vol", vol, "--pages", pages],
        cwd=ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        die("extraction failed: " + proc.stderr.strip())
    out: dict[int, list[str]] = {}
    cur = None
    skip = re.compile(r"^(?:goldenagato\|.*|Page\|\d+|--- page \d+ ---)$", re.I)
    for line in proc.stdout.splitlines():
        m = re.match(r"^--- page (\d+) ---$", line.strip())
        if m:
            cur = int(m.group(1))
            out[cur] = []
            continue
        if cur is None or skip.match(line.strip()):
            continue
        if line.strip():
            out[cur].append(line.rstrip())
    return out


def report_blank_pages(vol: str, pages: str) -> None:
    got = volume_pages(vol, pages)
    for page in sorted(got):
        n = len(got[page])
        if n == 0:
            print(f"  p.{page}: BLANK (no prose)")
        elif n <= 3:
            print(f"  p.{page}: short ({n} lines)")


def cmd_chapters(a) -> int:
    vol = a.vol or first_unfinished_volume()
    return run([sys.executable, "kb/walk_locate.py", "chapters", "--vol", vol], "chapters")


def chapter_map(vol: str) -> list[tuple[int, int, int, str]]:
    """[(index, first_page, last_page, title)] for a volume, in book order."""
    proc = subprocess.run(
        [sys.executable, "kb/walk_locate.py", "chapters", "--vol", vol],
        cwd=ROOT, capture_output=True, text=True,
    )
    out = []
    for line in proc.stdout.splitlines():
        m = re.match(r"^\s*p\.\s*(\d+)\s*[-–]\s*(\d+)\s*\(\s*\d+ pp\)\s+(.*)$", line)
        if m:
            out.append((0, int(m.group(1)), int(m.group(2)), m.group(3).strip()))
    numbered = []
    for i, (_n, lo, hi, title) in enumerate(out, start=1):
        c = re.search(r"\bChapter\s+(\d+)", title, re.I)
        numbered.append((int(c.group(1)) if c else i, lo, hi, title))
    return numbered


# --------------------------------------------------------------- append


def stamp_index(lines: list[str], under: str | None) -> int:
    """Index at which a new section should be inserted inside a volume block."""
    if not under:
        return len(lines)
    anchor = None
    for i, line in enumerate(lines):
        m = HEAD_RE.match(line)
        if m and m.group("vol").strip().lower() == under.lower():
            anchor = i + 1
            break
    if anchor is None:
        heads = [HEAD_RE.match(l).group("vol") for l in lines if HEAD_RE.match(l)]
        die(f"no '## {under}' heading in file; headings found: {', '.join(heads) or 'none'}")
    for i in range(anchor, len(lines)):
        if HEAD_RE.match(lines[i]):
            return i
    return len(lines)


def cmd_append(a) -> int:
    body = text_arg(a.section, a.from_file, "the section text").rstrip("\n")
    if not body.strip():
        die("section text is empty")
    path = pathlib.Path(a.file)
    if not path.is_absolute():
        path = ROOT / path
    rel = path.relative_to(ROOT)
    text = read(path)
    trailing_nl = text.endswith("\n")
    lines = text.split("\n")
    if trailing_nl:
        lines = lines[:-1]

    stamp = None
    if a.stamp:
        stamp = f"<!-- walk: {a.stamp} -->"
        kept = [l for l in lines if l.strip() != stamp]  # one boundary marker per stamp
        if len(kept) != len(lines):
            print(f"cote: de-duplicated {len(lines) - len(kept)} old copy of this stamp")
        lines = kept

    at = len(lines) if a.at_end else stamp_index(lines, a.under)
    # drop a blank run at the tail so we control spacing
    while at > 0 and not lines[at - 1].strip():
        lines.pop(at - 1)
        at -= 1

    block = ["", body.rstrip()]
    if stamp:
        block += ["", stamp]
    lines[at:at] = block
    new = "\n".join(lines).rstrip("\n") + "\n"
    path.write_text(new, encoding="utf-8")
    added = len(body.split("\n"))
    print(f"cote: +{added} lines -> {rel} ({len(new.splitlines())} lines total)")
    return 0


def cmd_ledger_new(a) -> int:
    path = ROOT / "ledgers" / a.kind / f"{a.stem}.md"
    if path.exists() and not a.force:
        die(f"{path.relative_to(ROOT)} already exists (use --force to overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)
    title = a.title or a.stem.replace("-", " ").title()
    start = a.start_vol or first_unfinished_volume()
    body = (
        f"# {title} — walk ledger\n\n"
        f"{a.header}\n\n"
        f"## {start}\n\n"
        f"<!-- walk: {start} → start -->\n"
    )
    path.write_text(body, encoding="utf-8")
    print(f"cote: created {path.relative_to(ROOT)}")
    return 0


# --------------------------------------------------------------- checks


def cmd_verify(a) -> int:
    codes = []
    if a.vol:
        codes.append(run([sys.executable, "kb/verify2.py", a.vol], "verify2"))
        codes.append(run([sys.executable, "kb/verify3.py", a.vol], "verify3"))
    else:
        codes.append(run([sys.executable, "kb/verify2.py"], "verify2"))
        codes.append(run([sys.executable, "kb/verify3.py"], "verify3"))
    return 0 if all(c == 0 for c in codes) else 1


def cmd_build(a) -> int:
    """Rebuild docs/ from content/ and ledgers/. --docs is accepted and ignored."""
    code = run([sys.executable, "gen/build.py"], "build")
    if code != 0:
        return code
    print("cote: site hash " + tree_hash("docs"))
    return 0


def cmd_gate(a) -> int:
    """Publishing gate: the strict site validator and the generator tests."""
    codes = [run([sys.executable, "kb/validate_site.py", "--site", "docs", "--strict"], "validate"),
             run([sys.executable, "-m", "unittest", "discover", "-s", "gen/tests"], "gen tests"),
             run([sys.executable, "-m", "unittest", "discover", "-s", "kb/tests"], "kb tests")]
    return 0 if all(c == 0 for c in codes) else 1


def tree_hash(rel: str) -> str:
    import hashlib  # noqa: PLC0415

    root = ROOT / rel
    h = hashlib.md5()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def cmd_hash(a) -> int:
    print(tree_hash(a.path))
    return 0


# --------------------------------------------------------------- status


def volume_order() -> list[str]:
    """Volume ids in reading order, from the source texts; side stories last."""
    vols = []
    for fn in sorted((ROOT / "text").glob("*.txt")):
        m = re.match(r"COTE Y(\d) V(\d+(?:\.\d+)?)\.txt$", fn.name)
        if m:
            vols.append((int(m.group(1)), float(m.group(2)),
                         f"y{m.group(1)}v{m.group(2)}"))
    vols.sort()
    out = [v for _y, _n, v in vols]
    if (ROOT / "text" / "COTE V0.txt").exists():
        out.append("y0")
    return out


def volume_done(vol: str) -> bool:
    """A volume is closed when its ledger carries a `→ DONE` boundary stamp."""
    led = ROOT / "ledgers" / "volumes" / f"{vol}.md"
    if not led.exists():
        return False
    return any(re.search(r"→\s*DONE\b", m.group("inner"))
               for line in led.read_text(encoding="utf-8").splitlines()
               if (m := STAMP_RE.match(line)))


def first_unfinished_volume() -> str:
    """The first volume in reading order without a `→ DONE` stamp."""
    for v in volume_order():
        if not volume_done(v):
            return v
    return volume_order()[-1]


def cmd_next(a) -> int:
    vol = a.vol or first_unfinished_volume()
    led = ROOT / "ledgers" / "volumes" / f"{vol}.md"
    stamps = []
    if led.exists():
        stamps = [STAMP_RE.match(l).group("inner")
                  for l in led.read_text(encoding="utf-8").splitlines() if STAMP_RE.match(l)]
    walked = max((int(n) for s in stamps for n in re.findall(r"→ p\.?(\d+)", s)), default=0)
    cmap = chapter_map(vol)
    if cmap and (volume_done(vol) or all(hi <= walked for _n, _lo, hi, _t in cmap)):
        walked = max([walked] + [hi for _n, _lo, hi, _t in cmap])
    print(f"== {vol}: {len(cmap)} sections, last page recorded p.{walked} ==")
    nxt = None
    for num, lo, hi, title in cmap:
        if lo > walked:
            mark, status = "TODO", " "
        elif hi > walked:
            mark, status = "PART", " "
        else:
            mark, status = "done", " "
        if nxt is None and lo > walked:
            nxt = (num, lo, hi, title)
        print(f"  [{mark}] ch{num} p.{lo}-{hi}  {title}")
    if nxt:
        mid = nxt[1] + (nxt[2] - nxt[1]) // 2
        print(f"\nnext: chapter {nxt[0]} — pages {nxt[1]}-{nxt[2]}")
        print(f"  cote.py read --vol {vol} --pages {nxt[1]}-{mid}")
        print(f"  cote.py read --vol {vol} --pages {mid + 1}-{nxt[2]} --blank")
    else:
        print("\nthis volume is fully recorded")
    return 0


def cmd_status(a) -> int:
    print("== git ==")
    print("  " + git("status", "-sb").splitlines()[0])
    print(f"  HEAD: {git('log', '-1', '--format=%h %s')}")
    dirty = [l for l in git("status", "--porcelain").splitlines() if l.strip()]
    real = [l for l in dirty if not NEVER_SHIP.search(l[3:])]
    print(f"  changes to ship: {len(real)} (ignored/local: {len(dirty) - len(real)})")
    for l in real[:12]:
        print("   ", l)
    print("\n== walk position ==")
    for p in sorted((ROOT / "ledgers").rglob("*.md")):
        stamps = [STAMP_RE.match(l).group("inner") for l in p.read_text(encoding="utf-8").splitlines()
                  if STAMP_RE.match(l)]
        last = stamps[-1] if stamps else "no stamps"
        print(f"  {p.relative_to(ROOT)}: {last}  ({len(stamps)} stamps)")
    print("\n== progress files ==")
    for p in PROGRESS:
        f = ROOT / p
        heads = re.findall(r"^###\s+(.+)$", f.read_text(encoding="utf-8"), re.M) if f.exists() else []
        print(f"  {p}: {len(heads)} entries, last: {heads[-1] if heads else '-'}")
    return 0


# --------------------------------------------------------------- ship


def cmd_ship(a) -> int:
    msg = text_arg(a.message, a.message_from, "the commit message")
    if a.check:
        print("== gate ==")
        if cmd_gate(argparse.Namespace(full=True)) != 0:
            die("gate failed; nothing committed", 1)
        print("== verifiers ==")
        if a.vol and cmd_verify(argparse.Namespace(vol=a.vol)) != 0:
            die("quote verification failed; nothing committed", 1)
    paths = [p for p in (a.add or SHIP_PATHS) if (ROOT / p).exists()]
    blocked = [p for p in paths if NEVER_SHIP.search(p)]
    if blocked:
        die(f"refusing to stage local-only paths: {', '.join(blocked)}")
    staged = git("add", "--", *paths) or ""
    diff = git("diff", "--cached", "--name-only")
    if not diff.strip():
        print("cote: nothing staged; working tree matches HEAD for " + ", ".join(paths))
        return 0
    names = diff.splitlines()
    print(f"== staging {len(names)} files ==")
    for n in names[:15]:
        print("   ", n)
    if len(names) > 15:
        print(f"    … {len(names) - 15} more")
    env = os.environ | AUTHOR_ENV
    proc = subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, env=env,
                          capture_output=True, text=True)
    print(proc.stdout.strip() or proc.stderr.strip())
    if proc.returncode != 0:
        die("commit failed", 1)
    if a.push:
        print("== push ==")
        print(git("push", "origin", a.branch))
    print("== after ==")
    print(git("status", "-sb").splitlines()[0])
    return 0


# --------------------------------------------------------------- wiring


def main() -> int:
    ap = argparse.ArgumentParser(prog="cote.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(fn=cmd_status)

    p = sub.add_parser("next")
    p.add_argument("--vol", help="volume id; default: the first unfinished volume")
    p.set_defaults(fn=cmd_next)
    p = sub.add_parser("chapters")
    p.add_argument("--vol", help="volume id; default: the first unfinished volume")
    p.set_defaults(fn=cmd_chapters)

    p = sub.add_parser("read", help="print a page range with watermarks kept as extracted")
    p.add_argument("--vol", required=True)
    p.add_argument("--pages", required=True)
    p.add_argument("--blank", action="store_true", help="also flag blank/short pages in the range")
    p.set_defaults(fn=cmd_read)

    p = sub.add_parser("append", help="insert a section into a ledger, keeping one stamp per boundary")
    p.add_argument("--file", required=True)
    p.add_argument("--section")
    p.add_argument("--from", dest="from_file")
    p.add_argument("--under", help="volume heading to insert inside, e.g. y1v2")
    p.add_argument("--stamp", help='boundary marker text, e.g. "y1v2 ch5 → p.189"')
    p.add_argument("--at-end", action="store_true")
    p.set_defaults(fn=cmd_append)

    p = sub.add_parser("ledger-new")
    p.add_argument("kind")
    p.add_argument("stem")
    p.add_argument("--header", required=True)
    p.add_argument("--title")
    p.add_argument("--start-vol", dest="start_vol",
                   help="volume to open; default: the first unfinished volume")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_ledger_new)

    p = sub.add_parser("verify"); p.add_argument("--vol")
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("build"); p.add_argument("--docs", action="store_true"); p.set_defaults(fn=cmd_build)

    p = sub.add_parser("gate"); p.add_argument("--full", action="store_true"); p.set_defaults(fn=cmd_gate)

    p = sub.add_parser("hash"); p.add_argument("path", nargs="?", default="docs"); p.set_defaults(fn=cmd_hash)

    p = sub.add_parser("ship", help="stage the shipped paths, commit as the noreply identity, optionally push")
    p.add_argument("--message")
    p.add_argument("--from", dest="message_from")
    p.add_argument("--check", action="store_true", help="run the gate (and --vol verifiers) before committing")
    p.add_argument("--vol", help="volume to verify when --check is set")
    p.add_argument("--push", action="store_true")
    p.add_argument("--branch", default="main")
    p.add_argument("--add", nargs="*", help="override the staged paths")
    p.set_defaults(fn=cmd_ship)

    a = ap.parse_args()
    os.chdir(ROOT)
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())

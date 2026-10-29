#!/usr/bin/env python3
"""P1 recall audit: stratified page sample + straggler/mapping coverage report.

For every volume takes 3 pages (10% / 50% / 90% depth; empty pages fall back
to the nearest non-empty neighbour), then reports per page:

- extractor hits (E1-E6) and how many resolve to a real character
- open candidates (unreviewed/unknown) touching the audited page
- straggler tokens: NAME_TOK-like capitalized words on the page that are in
  NO extractor output, NO roster candidate and NO alias (potential missed
  names / gold-only mentions)

Writes:
  /tmp/opencode/audit_strata.txt     sampled vol/page list
  /tmp/opencode/audit_stragglers.txt straggler token review list (freq-sorted,
                                     with contexts, hunspell English flag)

Read-only — never writes to cote_kb.db.
"""
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_mine import (  # noqa: E402
    E1_RE, E2_RE, E3_RE, E4a_RE, E4b_RE, E4c_RE, E5_RE, E6_RE, NAME_TOK,
    STOP_LOWER, context_snippet, is_noise_token, iter_pages, normalize,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "cote_kb.db")
OUT = "/tmp/opencode"

EXTRACTORS = {
    "E1": E1_RE, "E2": E2_RE, "E3": E3_RE,
    "E4a": E4a_RE, "E4b": E4b_RE, "E4c": E4c_RE,
    "E5": E5_RE, "E6": E6_RE,
}
TOK_RE = re.compile(rf"\b({NAME_TOK})\b")

INTERJECTIONS = {
    "ah", "ahh", "aight", "anyways", "aye", "bam", "bingo", "boom", "bye",
    "cool", "damn", "dang", "duh", "eh", "gee", "goddamn", "ha", "haha",
    "hey", "hm", "hmm", "hmph", "ho", "huh", "hum", "jeez", "kay", "look",
    "no", "nope", "oh", "okay", "oops", "ouch", "ow", "oy", "please",
    "poi", "right", "sheesh", "so", "sorry", "stop", "sure", "tch", "uh",
    "ugh", "wait", "want", "watch", "well", "what", "whew", "whoa", "whew",
    "whoops", "why", "wow", "yay", "yeah", "yep", "yes", "yo", "yuck",
}


def straggler_keep(text, m):
    """Position/content filter: drop dialogue-openers, contractions,
    stammers, sentence-initial English — keep mid-sentence and paired caps."""
    tok = m.group(1)
    i = m.start() - 1
    while i >= 0 and text[i] in " \n\t":
        i -= 1
    prev = text[i] if i >= 0 else " "
    nxt = text[m.end():m.end() + 1]
    if re.match(r"^[A-Z][-\'’]", tok):          # stammer: Y-yeah, R-really
        return False
    if "\'" in tok or "’" in tok:               # We've, It'd, They'll
        return False
    if tok.lower() in INTERJECTIONS:
        return False
    if prev in "“\"«(":                         # dialogue opener: “Ugh...
        return False
    if prev in ".?!":
        # sentence start: keep only if a capitalized word follows (pair)
        rest = text[m.end():m.end() + 40]
        if not re.match(r"\s+[A-Z]", rest):
            return False
    if prev in "”’":                            # after closing quote(s)
        j = i - 1
        if j >= 0 and text[j] in ".?!":         # new sentence: pair-rule only
            rest = text[m.end():m.end() + 40]
            if not re.match(r"\s+[A-Z]", rest):
                return False
        return True
    if prev.islower():                          # mid-sentence cap (E2 zone)
        return True
    if re.match(r"\s+[A-Z]", nxt):              # forms a cap pair
        return True
    return prev in ",;:'’)"


def load_db_views():
    db = sqlite3.connect(DB)
    cand = {r[0]: (r[1], r[2]) for r in db.execute(
        "SELECT normalized, classification, char_id FROM roster_candidates")}
    alias = {}
    for r in db.execute(
            "SELECT a.normalized, a.char_id FROM aliases a "
            "JOIN characters c ON c.char_id=a.char_id "
            "WHERE c.char_id NOT LIKE 'provisional-%'"):
        alias.setdefault(r[0], r[1])
    chars = {r[0]: r[1] for r in db.execute(
        "SELECT char_id, canonical_name FROM characters "
        "WHERE char_id NOT LIKE 'provisional-%'")}
    db.close()
    return cand, alias, chars


def stratified_pages():
    """(vol_id, stem, page, text) at 10/50/90 depth per volume; non-empty."""
    by_vol = defaultdict(list)
    for vol_id, stem, page, _s, text in iter_pages():
        by_vol[vol_id].append((vol_id, stem, page, text))
    out = []
    for vol_id in sorted(by_vol):
        pages = by_vol[vol_id]
        n = len(pages)
        for frac in (0.1, 0.5, 0.9):
            idx = min(n - 1, int(n * frac))
            # nearest non-empty around idx
            for off in range(n):
                for j in (idx + off, idx - off):
                    if 0 <= j < n and len(pages[j][3].strip()) > 150:
                        chosen = pages[j]
                        break
                else:
                    continue
                break
            else:
                continue
            out.append(chosen)
    return out


def english_flags(tokens):
    """tokens accepted by en_US hunspell (name-like if NOT accepted)."""
    if not tokens:
        return set()
    hd = "/tmp/opencode/hdict"
    if not os.path.exists(os.path.join(hd, "en_US.dic")):
        os.makedirs(hd, exist_ok=True)
        hits = glob_en_us()
        if not hits:
            return set()
        shutil.copy(hits[0], os.path.join(hd, "en_US.dic"))
        shutil.copy(hits[0][:-4] + ".aff", os.path.join(hd, "en_US.aff"))
    p = subprocess.run(
        ["hunspell", "-d", "en_US", "-l"],
        input="\n".join(sorted(tokens)), capture_output=True, text=True, cwd=hd)
    misspelled = {w.lower() for w in p.stdout.split()}
    return {t for t in tokens if t.lower() not in misspelled}


def glob_en_us():
    import glob
    return glob.glob(
        "/home/user3/.local/share/flatpak/runtime/**/hunspell/en_US.dic",
        recursive=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    cand, alias, chars = load_db_views()

    def resolve(key):
        """-> (state, char_id|None): mapped|noise|unknown|unreviewed|absent"""
        c = cand.get(key)
        if c and c[0] == "character" and c[1] and \
                not c[1].startswith("provisional-"):
            return "mapped", c[1]
        if key in alias:
            return "mapped", alias[key]
        if c:
            return c[0], None
        return "absent", None

    pages = stratified_pages()
    with open(os.path.join(OUT, "audit_strata.txt"), "w") as f:
        for vol, stem, page, _t in pages:
            f.write(f"{vol}\t{stem}\tpage {page}\n")

    ext_key_pages = defaultdict(set)      # key -> pages seen
    ext_bits = defaultdict(set)           # key -> extractors
    state_pages = defaultdict(set)        # key -> pages (for open candidates)
    stragglers = defaultdict(list)        # token -> [(vol,page,tok,ctx)] (max 3)
    stragg_n = Counter()                  # token -> total occurrences
    page_stats = []

    for vol, stem, page, text in pages:
        keys = set()
        for ename, rx in EXTRACTORS.items():
            for m in rx.finditer(text):
                for g in m.groups():
                    if not g or not g[0].isupper():
                        continue
                    k = normalize(g)
                    if not k or is_noise_token(g) or g.lower() in STOP_LOWER:
                        continue
                    keys.add(k)
                    ext_key_pages[k].add((vol, page))
                    ext_bits[k].add(ename)
                    st, _ = resolve(k)
                    state_pages[k].add(st)

        mapped = sum(1 for k in keys if resolve(k)[0] == "mapped")
        page_stats.append((vol, page, len(keys), mapped))

        for m in TOK_RE.finditer(text):
            tok = m.group(1)
            if is_noise_token(tok) or tok.lower() in STOP_LOWER:
                continue
            if not straggler_keep(text, m):
                continue
            k = normalize(tok)
            if k in cand or k in alias or k in keys:
                continue
            ctx = context_snippet(text, m.start(), m.end())
            stragg_n[k] += 1
            if len(stragglers[k]) < 3:
                stragglers[k].append((vol, page, tok, ctx))

    # hunspell flags for stragglers
    eng = english_flags({v[0][2] for v in stragglers.values()})

    with open(os.path.join(OUT, "audit_stragglers.txt"), "w") as f:
        f.write(f"{len(pages)} strata pages; {len(stragglers)} straggler tokens\n")
        f.write("=== NAME-LIKE (NOT english dict) — review these for missed names ===\n")
        n_name = n_eng = 0
        for tok, occ in sorted(stragglers.items(),
                               key=lambda x: -len(x[1])):
            raw = occ[0][2]
            flag = "ENG" if raw.lower() in eng else "NAME?"
            if flag == "NAME?":
                n_name += 1
            else:
                n_eng += 1
            f.write(f"\n[{flag}] {raw}  x{stragg_n[tok]}\n")
            for vol, page, _raw, ctx in occ:
                f.write(f"    {vol} p{page}: {ctx}\n")

    # summary
    total_keys = len(ext_key_pages)
    mapped = sum(1 for k in ext_key_pages if resolve(k)[0] == "mapped")
    unmapped = total_keys - mapped
    open_states = Counter()
    for k in ext_key_pages:
        st, _ = resolve(k)
        open_states[st] += 1
    # extractor overlap (capture-recapture view): non-noise keys only
    real_keys = [k for k in ext_bits if resolve(k)[0] != "noise"]
    enc = Counter(len(ext_bits[k]) for k in real_keys)
    n1 = enc.get(1, 0)
    n2 = max(enc.get(2, 0), 1)
    chao1 = mapped + (n1 * n1) / (2 * n2)
    real_n = len(real_keys)

    total_mapped = sum(t for _v, _p, _k, t in page_stats)
    total_hits = sum(k for _v, _p, k, _t in page_stats)
    print(f"strata pages: {len(pages)} (3 per volume)")
    print(f"page coverage: {total_hits} extractor-hits, "
          f"{total_mapped} mapped "
          f"({100.0 * total_mapped / max(1, total_hits):.1f}%)")
    print(f"distinct keys on strata: {total_keys}  states: {dict(open_states)}")
    print(f"extractor-hit distribution per key (capture-recapture): "
          f"{dict(sorted(enc.items()))}")
    print(f"non-noise keys on strata: {real_n} (singletons {n1}, doubletons {n2})")
    print(f"Chao1 estimated unseen non-noise keys: ~{chao1:.0f} (mapped base {mapped})")
    print(f"straggler tokens: {len(stragglers)} "
          f"(NAME? {n_name} / ENG {n_eng}) -> {OUT}/audit_stragglers.txt")

    # per-volume one-liner for volumes with zero mapped hits (alarm bell)
    bad = [(v, p, t, m) for v, p, t, m in page_stats if t and m == 0]
    if bad:
        print("pages with extractor hits but 0 mapped:", len(bad))
        for v, p, t, m in bad[:10]:
            print(f"   {v} p{p}: {t} hits, {m} mapped")


if __name__ == "__main__":
    main()

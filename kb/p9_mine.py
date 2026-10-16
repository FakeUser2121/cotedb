"""P9 discovery: mine exam and system terms across the corpus.

Three extractors, printed as one report:
  S1 seed-term counts (exam names + system vocabulary)
  S2 phrases immediately before "exam"/"test" (corpus-grounded names)
  S3 explicit naming patterns ("exam is called", quoted X Exam, overview boxes)
"""
import collections
import re
import sys

sys.path.insert(0, "kb")
from roster_mine import iter_pages

SEED_TERMS = [
    "paper shuffle", "island exam", "uninhabited island exam",
    "deserted island exam", "cruise ship", "ship exam", "special exam",
    "midterm", "final exam", "entrance exam", "zodiac", "class poll",
    "event selection", "mixed training camp", "unanimous",
    "survival and elimination", "end-of-year", "comprehensive academic",
    "sports festival", "school festival", "field trip", "volleyball",
    "private points", "class points", "student council", "club",
    "expulsion", "contract", "coin", "white room", "grid", "task",
    "withdrawal", "leader", "vote", "voting",
]

GENERIC_BEFORE = {
    "this", "the", "a", "an", "that", "these", "those", "my", "his",
    "her", "their", "our", "next", "last", "big", "final", "midterm",
    "finals", "entrance", "special", "first", "second", "third",
    "written", "oral", "practical", "on", "during", "before", "after",
    "about", "for", "in", "of", "to", "at", "with", "from", "by",
    "but", "and", "or", "when", "while", "once", "after", "day",
    "exam", "test", "school", "math", "english", "japanese", "science",
}

NAME_BEFORE = re.compile(
    r"\b([A-Za-z][A-Za-z'’\-]*(?: [A-Za-z][A-Za-z'’\-]*){0,4})"
    r" +(exam|test)\b", re.I)

NAMING = re.compile(
    r"(?:exam|test)\s+(?:is|was|will be)\s+(?:called|named)|"
    r"name of the (?:special )?(?:exam|test) is|"
    r"‘[A-Z][A-Za-z ]+(?:Exam|Test|Poll|Vote)’|"
    r"'[A-Z][A-Za-z ]+(?:Exam|Test|Poll|Vote)'|"
    r"Special Exam Overview|Exam Overview")


def main():
    counts = collections.Counter()
    vols = collections.defaultdict(set)
    examples = {}
    before = collections.Counter()
    before_vols = collections.defaultdict(set)
    before_ex = {}
    naming = {}
    for vol, _stem, page, _pstart, text in iter_pages():
        low = text.lower()
        for t in SEED_TERMS:
            n = low.count(t)
            if n:
                counts[t] += n
                vols[t].add(vol)
                examples.setdefault(t, []).append(f"{vol} p.{page}")
        for m in NAME_BEFORE.finditer(text):
            key = m.group(1).lower().strip()
            if key in GENERIC_BEFORE or key in {"on the day of the",
                                                "during the",
                                                "in this special"}:
                continue
            if len(key) < 4 or key == m.group(2).lower():
                continue
            before[(key, m.group(2).lower())] += 1
            before_vols[key].add(vol)
            before_ex.setdefault(key,
                                 f"{vol} p.{page}: …"
                                 f"{text[max(0, m.start()-50):m.end()+30]}"
                                 f"…".replace("\n", " "))
        for m in NAMING.finditer(text):
            snippet = text[max(0, m.start() - 60):m.end() + 80]
            snippet = snippet.replace("\n", " ")
            key = snippet[:90]
            if key not in naming:
                naming[key] = f"{vol} p.{page}: …{snippet}…"

    print("=== S1 seed-term counts ===")
    for t in SEED_TERMS:
        print(f"{t!r:32} hits={counts[t]:5}  vols={len(vols[t]):2}  "
              f"ex={examples.get(t, [])[:3]}")

    print("\n=== S2 phrases before exam/test (count>=3, 2+ vols) ===")
    for (key, w), n in before.most_common():
        if n < 3 or len(before_vols[key]) < 2:
            continue
        print(f"{n:4} vols={len(before_vols[key]):2} [{w}] {key!r}")
        print(f"      {before_ex[key][:150]}")

    print(f"\n=== S3 explicit naming patterns ({len(naming)} unique) ===")
    for v in naming.values():
        print(" ", v[:175])
    return 0


if __name__ == "__main__":
    sys.exit(main())

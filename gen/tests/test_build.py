"""Generator invariants. Run: python3 -m unittest discover -s gen/tests"""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "gen"))
import model as M  # noqa: E402

MODEL = M.Model()


def tree(root):
    h = hashlib.md5()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


class Content(unittest.TestCase):
    def test_every_ledger_marker_has_a_reader_label(self):
        used = {r["m"] for led in MODEL.ledger.values() for b in led["blocks"] for r in b["rows"]}
        self.assertEqual(used - set(M.MARKERS), set(), "add a label to gen/markers.json")

    def test_ledger_file_names_are_entity_ids(self):
        for (kind, eid) in MODEL.ledger:
            self.assertIn(eid, MODEL.kinds[kind], f"ledgers/{kind}/{eid}.md has no row in content/")

    def test_scene_ids_are_unique(self):
        ids = [s["id"] for s in MODEL.scenes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_scene_cites_a_known_volume(self):
        for s in MODEL.scenes:
            self.assertIn(s["vol"], MODEL.vol)

    def test_reading_order_is_year_one_to_three_then_side_stories(self):
        self.assertEqual(MODEL.vols[0]["id"], "y1v1")
        self.assertEqual(MODEL.vols[-1]["id"], "y0")

    def test_own_page_rule(self):
        cfg = MODEL.cfg
        for c in MODEL.chars.values():
            earned = c["scenes"] >= cfg["page_min_scenes"] or c["lines"] >= cfg["page_min_lines"]
            self.assertEqual(c["has_page"], earned, c["id"])

    def test_every_character_has_a_tier(self):
        for c in MODEL.chars.values():
            self.assertIn(c["tier"]["all"], ("main", "supporting", "minor"), c["id"])

    def test_volume_ids_in_rosters_exist(self):
        for kind in ("exams", "systems", "places"):
            for e in MODEL.kinds[kind].values():
                for v in e["volumes"]:
                    self.assertIn(v, MODEL.vol)


class Build(unittest.TestCase):
    def test_two_builds_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for out in (a, b):
                subprocess.run([sys.executable, str(ROOT / "gen/build.py"), "--out", out],
                               check=True, capture_output=True)
            self.assertEqual(tree(a), tree(b))

    def test_committed_docs_match_a_fresh_build(self):
        docs = ROOT / "docs"
        if not docs.exists():
            self.skipTest("docs/ not built yet")
        with tempfile.TemporaryDirectory() as a:
            subprocess.run([sys.executable, str(ROOT / "gen/build.py"), "--out", a],
                           check=True, capture_output=True)
            self.assertEqual(tree(a), tree(docs), "docs/ is stale: run make build")

    def test_every_character_page_has_a_markdown_card(self):
        docs = ROOT / "docs"
        if not docs.exists():
            self.skipTest("docs/ not built yet")
        for c in MODEL.chars.values():
            if not c["has_page"]:
                continue
            f = docs / "people" / f"{c['id']}.md"
            self.assertTrue(f.exists(), f"missing {f.relative_to(docs)}")
            text = f.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(f"# {c['name']}\n"), f.relative_to(docs))
            self.assertIn("## Scenes\n", text, f.relative_to(docs))

    def test_download_page_lists_every_character_with_a_card(self):
        docs = ROOT / "docs"
        if not docs.exists():
            self.skipTest("docs/ not built yet")
        page = (docs / "download/index.html").read_text(encoding="utf-8")
        self.assertIn("assets/dl/people.js", page)
        self.assertIn("assets/download.js", page)
        data = (docs / "assets/dl/people.js").read_text(encoding="utf-8")
        for c in MODEL.chars.values():
            if c["has_page"]:
                self.assertIn(f'["{c["id"]}"', data)


if __name__ == "__main__":
    unittest.main()

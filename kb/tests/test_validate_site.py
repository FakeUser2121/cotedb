"""Self-test: a clean mini-site passes; each injected fault trips its own rule.
Run:  python3 -m unittest discover -s kb/tests -v
"""
import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kb"))
import validate_site as vs  # noqa: E402

RULES = json.loads((ROOT / "kb/schema/rules.json").read_text(encoding="utf-8"))
TABS = ["people", "story", "school", "world", "topics"]


def tabs(prefix):
    return ('<nav class="tabs"><a href="%sindex.html">Home</a>' % prefix + "".join(
        '<a href="%s%s/index.html">%s</a>' % (prefix, t, RULES["tabs"]["labels"][t + "/index.html"])
        for t in TABS) + "</nav>")


def page(title, body, prefix="../", crumbs=True, h1=True, extra_head=""):
    c = '<nav class="crumbs"><a href="%sindex.html">Home</a></nav>' % prefix if crumbs else ""
    h = "<h1>%s</h1>" % title if h1 else ""
    return ("<html><head><title>%s · COTE Knowledge Base</title>%s</head><body>%s"
            "<main>%s%s%s</main></body></html>" % (title, extra_head, tabs(prefix), c, h, body))


def build(tmp, overrides=None):
    files = {"index.html": page("Home", "<p>hi</p>", prefix="", crumbs=False)}
    for t in TABS:
        files[f"{t}/index.html"] = page(t.title(), "<p>x</p>")
    files["people/horikita-suzune.html"] = page(
        "Horikita Suzune",
        '<p class="verb">“Hello.” <span class="by">— <a href="ayanokouji-kiyotaka.html">'
        'Ayanokouji Kiyotaka</a></span> <span class="pin"><span class="pageref">p.1</span></span></p>')
    files["people/ayanokouji-kiyotaka.html"] = page("Ayanokouji Kiyotaka", "<p>ok</p>")
    files.update(overrides or {})
    for rel, html in files.items():
        f = Path(tmp) / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
    return Path(tmp)


def hits_for(overrides=None):
    with tempfile.TemporaryDirectory() as tmp:
        site = build(tmp, overrides)
        _, hits = vs.run(site, RULES)
        return {k: len(v) for k, v in hits.items() if v}


class T(unittest.TestCase):
    def test_clean_site_has_no_hits(self):
        self.assertEqual(hits_for(), {})

    def test_two_h1(self):
        h = hits_for({"people/horikita-suzune.html": page("A", "<h1>B</h1>")})
        self.assertIn("R01_one_h1", h)

    def test_duplicate_id(self):
        h = hits_for({"people/horikita-suzune.html": page("A", '<p id="x"></p><p id="x"></p>')})
        self.assertIn("R02_duplicate_ids", h)

    def test_broken_link_and_anchor(self):
        h = hits_for({"people/horikita-suzune.html": page(
            "A", '<a href="nope.html">n</a> <a href="ayanokouji-kiyotaka.html#zzz">m</a>')})
        self.assertIn("R03_broken_link", h)
        self.assertIn("R04_broken_anchor", h)

    def test_no_breadcrumb(self):
        h = hits_for({"people/horikita-suzune.html": page("A", "<p>x</p>", crumbs=False)})
        self.assertIn("R05_no_breadcrumb", h)

    def test_extra_tab(self):
        bad = page("A", "<p>x</p>").replace("</nav><main>", "<a href=\"../guides/index.html\">Start here</a></nav><main>", 1)
        self.assertIn("R06_tab_order", hits_for({"people/horikita-suzune.html": bad}))

    def test_citation_linked(self):
        h = hits_for({"people/horikita-suzune.html": page(
            "A", '<a href="ayanokouji-kiyotaka.html">p.21</a>')})
        self.assertIn("R08_citation_linked", h)

    def test_link_inside_quote_but_not_in_attribution(self):
        h = hits_for({"people/horikita-suzune.html": page(
            "A", '<p class="verb">“See <a href="ayanokouji-kiyotaka.html">Ayanokouji</a> now.”</p>')})
        self.assertIn("R09_link_in_quote", h)

    def test_empty_link_text(self):
        h = hits_for({"people/horikita-suzune.html": page(
            "A", '<a href="ayanokouji-kiyotaka.html">→</a>')})
        self.assertIn("R10_empty_link_text", h)

    def test_label_mismatch(self):
        h = hits_for({"people/horikita-suzune.html": page(
            "A", '<a href="../index.html">People</a>')})
        self.assertIn("R17_label_mismatch", h)

    def test_evidence_on_directory(self):
        h = hits_for({"people/index.html": page(
            "People", '<details class="scene"><summary>s</summary></details>')})
        self.assertIn("R13_evidence_on_index", h)

    def test_duplicate_link_in_one_paragraph(self):
        h = hits_for({"people/horikita-suzune.html": page(
            "A", '<p><a href="ayanokouji-kiyotaka.html">Ayanokouji</a> and '
                 '<a href="ayanokouji-kiyotaka.html">Ayanokouji</a></p>')})
        self.assertIn("R11_duplicate_link", h)

    def test_entity_link_text_must_be_a_name_of_target(self):
        h = hits_for({"people/horikita-suzune.html": page(
            "A", '<a href="ayanokouji-kiyotaka.html">click here</a>')})
        self.assertIn("R15_entity_link_text", h)

    def test_page_too_big(self):
        h = hits_for({"people/horikita-suzune.html": page("A", "<p>" + "word " * 7000 + "</p>")})
        self.assertIn("R12_page_too_big", h)

    def test_redirect_to_missing_file(self):
        h = hits_for({"people/old.html":
                      '<html><head><meta http-equiv="refresh" content="0; url=gone.html"></head></html>'})
        self.assertIn("R16_redirect_target", h)


if __name__ == "__main__":
    unittest.main()

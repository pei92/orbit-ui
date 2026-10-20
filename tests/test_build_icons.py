import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_icons as bi  # noqa: E402

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke="currentColor"><path d="M1 1h2"/></svg>'


class BuildIconsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        for n in ("star", "orbit"):
            (self.dir / f"{n}.svg").write_text(SVG, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_rule_per_icon_sorted(self):
        block = bi.build(self.dir)
        self.assertTrue(block.startswith(bi.START) and block.endswith(bi.END))
        self.assertLess(block.index(".o-icon--orbit"), block.index(".o-icon--star"))
        self.assertEqual(block.count(".o-icon--"), 2)

    def test_uri_is_css_safe(self):
        uri = bi.data_uri(SVG)
        self.assertNotIn("#", uri)
        self.assertNotIn("<", uri)
        self.assertIn("%23000", uri)  # currentColor 换成黑色作 mask

    def test_repo_css_is_up_to_date(self):
        css = (ROOT / "assets" / "orbit.css").read_text(encoding="utf-8")
        self.assertIn(bi.build(ROOT / "assets" / "icons"), css)


if __name__ == "__main__":
    unittest.main()

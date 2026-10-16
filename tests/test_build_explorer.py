import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_explorer as be  # noqa: E402


def candidate(**over):
    c = {
        "id": "mission", "name": "任务控制台", "concept": "盯着唯一的数字",
        "typography": "JetBrains Mono", "palette": ["#07090c", "#ffb547"],
        "traits": ["密集网格"], "source": "a.html",
    }
    c.update(over)
    return c


class BuildExplorerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "a.css").write_text("body{background:url(bg.png)}", encoding="utf-8")
        (self.dir / "bg.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (self.dir / "a.html").write_text(
            '<link rel="stylesheet" href="a.css"><img src="bg.png"><script>var x="</div>"</script>',
            encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, manifest):
        p = self.dir / "manifest.json"
        p.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        return p

    def base(self, cands):
        return {"schemaVersion": 1, "project": "测试", "brief": "简述", "round": "02", "candidates": cands}

    def test_builds_and_inlines_assets(self):
        out = be.build(self.write(self.base([candidate()])))
        html = out.read_text(encoding="utf-8")
        self.assertIn("data:image/png;base64", html)
        self.assertNotIn('href=\\"a.css\\"', html)
        self.assertNotIn("/*__ORBIT_DATA__*/null", html)
        # 候选里的 </script>、</div> 要被转义，不能提前结束对比页的 <script>
        payload = html.split("const DATA = ")[1].split(";\nconst MOBILE")[0]
        self.assertNotIn("</", payload)
        json.loads(payload)

    def test_reports_all_problems_at_once(self):
        bad = candidate(id="Bad ID", palette=["red"], source="missing.html")
        with self.assertRaises(be.ManifestError) as cm:
            be.load_manifest(self.write({"schemaVersion": 2, "project": "", "brief": "x", "candidates": [bad]}))
        text = "\n".join(cm.exception.problems)
        for needle in ("schemaVersion", "project", ".id", ".palette", "missing.html"):
            self.assertIn(needle, text)

    def test_refuses_overwrite_without_force(self):
        m = self.write(self.base([candidate()]))
        be.build(m)
        with self.assertRaises(be.ManifestError):
            be.build(m)
        be.build(m, force=True)

    def test_baseline_sorted_first_and_unique(self):
        data = be.load_manifest(self.write(self.base([candidate(), candidate(id="now", baseline=True)])))
        self.assertEqual(data["candidates"][0]["id"], "now")
        with self.assertRaises(be.ManifestError):
            be.load_manifest(self.write(self.base([candidate(baseline=True), candidate(id="b", baseline=True)])))

    def test_viewport_formats(self):
        data = be.load_manifest(self.write({**self.base([candidate(nativeViewport={"width": 800, "height": 600})]),
                                            "nativeViewport": "1920×1080"}))
        self.assertEqual(data["candidates"][0]["viewport"], {"width": 800, "height": 600})
        data = be.load_manifest(self.write({**self.base([candidate()]), "nativeViewport": "1920x1080"}))
        self.assertEqual(data["candidates"][0]["viewport"], {"width": 1920, "height": 1080})

    def test_source_cannot_escape_manifest_dir(self):
        with self.assertRaises(be.ManifestError):
            be.load_manifest(self.write(self.base([candidate(source="../outside.html")])))

    def test_example_manifest_builds(self):
        manifest = ROOT / "examples" / "launch-page" / "manifest.json"
        out = self.dir / "explorer.html"
        be.build(manifest, out)
        self.assertGreater(out.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()

# plugins/rad-okf/tests/test_index.py
import sys, os, unittest, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_model as om
import okf_index as oi

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# B\n")
        write(self.root, "product/faunero.md",
              "---\ntype: Product\ntitle: Faunero\ndescription: The app.\n---\nx\n")
        write(self.root, "concepts/flow.md",
              "---\ntype: Concept\ntitle: Flow\n---\ny\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_generate_groups_and_bullets(self):
        m = om.build_model(self.root)
        out = oi.generate_index_text(m, "My Bundle")
        self.assertTrue(out.startswith("# My Bundle\n"))
        self.assertIn("## Concepts", out)
        self.assertIn("## Product", out)
        self.assertIn("* [Faunero](product/faunero.md) — The app.", out)
        self.assertIn("* [Flow](concepts/flow.md)", out)   # no description -> no em dash
        self.assertNotIn("flow.md) —", out)

    def test_drift_detects_missing(self):
        m = om.build_model(self.root)               # index.md ("# B") lists nothing
        codes = {(f["code"], f["id"]) for f in oi.validate_index(m)}
        self.assertIn(("index-drift", "product/faunero"), codes)
        self.assertIn(("index-drift", "concepts/flow"), codes)

    def test_regenerate_writes_canonical_index(self):
        oi.regenerate(self.root, "My Bundle")
        text = (self.root / "index.md").read_text(encoding="utf-8")
        self.assertIn("## Product", text)
        self.assertIn("[Faunero](product/faunero.md)", text)
        m2 = om.build_model(self.root)
        self.assertEqual(oi.validate_index(m2), [])   # no drift after regen

    def test_no_title_falls_back_to_humanized_filename(self):
        write(self.root, "notes/raw-note.md", "---\ntype: Note\n---\nz\n")
        m = om.build_model(self.root)
        out = oi.generate_index_text(m, "B")
        self.assertIn("* [Raw Note](notes/raw-note.md)", out)

    def test_description_internal_whitespace_collapses(self):
        write(self.root, "x.md", "---\ntype: T\ntitle: X\ndescription: a   b\n---\nq\n")
        m = om.build_model(self.root)
        out = oi.generate_index_text(m, "B")
        self.assertIn("* [X](x.md) — a b", out)   # runs collapsed to a single space

    def test_empty_bundle_just_title(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "index.md").write_text("# B\n", encoding="utf-8")
            m = om.build_model(root)
            self.assertEqual(oi.generate_index_text(m, "B"), "# B\n")
            self.assertEqual(oi.validate_index(m), [])

if __name__ == "__main__":
    unittest.main()

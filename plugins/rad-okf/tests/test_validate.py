# plugins/rad-okf/tests/test_validate.py
import sys, os, unittest, tempfile, pathlib
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_validate as ov

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# root\n* [A](/a.md)\n")
        write(self.root, "a.md", "---\ntype: Thing\n---\n[gone](/missing.md)\n")
        write(self.root, "notype.md", "---\ntitle: no type here\n---\nx\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_codes(self):
        res = ov.validate(self.root, max_age_days=180,
                          now=datetime(2026, 6, 14, tzinfo=timezone.utc))
        codes = {f["code"] for f in res["findings"]}
        self.assertIn("missing-type", codes)     # notype.md
        self.assertIn("broken-link", codes)       # a.md -> /missing.md

    def test_missing_type_is_error(self):
        res = ov.validate(self.root)
        sev = [f["severity"] for f in res["findings"] if f["code"] == "missing-type"]
        self.assertEqual(sev, ["error"])

if __name__ == "__main__":
    unittest.main()

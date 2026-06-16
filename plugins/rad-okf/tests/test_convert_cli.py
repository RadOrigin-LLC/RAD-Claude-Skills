# plugins/rad-okf/tests/test_convert_cli.py
import sys, os, unittest, tempfile, pathlib, json, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

def run(*args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "okf_convert.py"), *args],
                          capture_output=True, text=True)

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "index.md").write_text("# B\n", encoding="utf-8")
        (self.root / "okf.json").write_text('{"name": "B"}', encoding="utf-8")
        self.src = self.root / "data.csv"
        self.src.write_text("name,role\nRyan,dev\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_writes_nothing(self):
        proc = run(str(self.src), "concepts/data.md", "--bundle", str(self.root),
                   "--type", "Dataset", "--title", "Data", "--dry-run", "--json")
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["format"], ".csv")
        self.assertFalse((self.root / "concepts" / "data.md").exists())

    def test_convert_writes_concept_table_and_indexes(self):
        proc = run(str(self.src), "concepts/data.md", "--bundle", str(self.root),
                   "--type", "Dataset", "--title", "Data", "--description", "rows")
        self.assertEqual(proc.returncode, 0)
        out = (self.root / "concepts" / "data.md").read_text(encoding="utf-8")
        self.assertIn("type: Dataset", out)
        self.assertIn("| name | role |", out)              # converted body
        idx = (self.root / "index.md").read_text(encoding="utf-8")
        self.assertIn("[Data](concepts/data.md)", idx)      # wired into index
        log = (self.root / "log.md").read_text(encoding="utf-8")
        self.assertIn("**Convert**", log)

    def test_markdown_routed_to_add(self):
        md = self.root / "note.md"
        md.write_text("# hi\n", encoding="utf-8")
        proc = run(str(md), "concepts/note.md", "--bundle", str(self.root),
                   "--type", "Note", "--title", "N", "--json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("add", json.loads(proc.stdout)["error"])

    def test_unsupported_type_rejected(self):
        binf = self.root / "doc.pdf"
        binf.write_text("x", encoding="utf-8")
        proc = run(str(binf), "concepts/doc.md", "--bundle", str(self.root),
                   "--type", "Doc", "--title", "D", "--json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("new --body", json.loads(proc.stdout)["error"])

if __name__ == "__main__":
    unittest.main()

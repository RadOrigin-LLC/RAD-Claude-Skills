# plugins/rad-okf/tests/test_check_cli.py
import sys, os, unittest, tempfile, pathlib, json, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# root\n")
        write(self.root, "notype.md", "---\ntitle: x\n---\ny\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_json_output_and_exit_code(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "okf_check.py"), str(self.root), "--json"],
            capture_output=True, text=True)
        data = json.loads(proc.stdout)
        codes = {f["code"] for f in data["findings"]}
        self.assertIn("missing-type", codes)
        self.assertEqual(proc.returncode, 1)  # errors present

if __name__ == "__main__":
    unittest.main()

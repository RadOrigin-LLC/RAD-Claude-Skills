# plugins/rad-okf/tests/test_viz.py
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_viz as ov

MODEL = {
    "root": "/x",
    "files": {"a": {"id": "a", "type": "Thing", "reserved": False, "errors": []},
              "index": {"id": "index", "type": "", "reserved": True, "errors": []}},
    "links": [{"src": "a", "dst": "index", "resolved": True}],
}

class T(unittest.TestCase):
    def test_self_contained_html(self):
        out = ov.render_html(MODEL, name="My Bundle")
        self.assertTrue(out.lstrip().lower().startswith("<!doctype html"))
        self.assertIn("My Bundle", out)
        self.assertIn('"id": "a"', out)            # node data inlined
        self.assertNotIn("http://", out)            # no external resources
        self.assertNotIn("https://", out)

if __name__ == "__main__":
    unittest.main()

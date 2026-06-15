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
        # Self-contained means no external resource FETCHES. The SVG namespace URI
        # (http://www.w3.org/2000/svg) is a local identifier, never loaded over the
        # network, so a blanket http:// ban would be wrong — target real fetches.
        self.assertNotIn('src="http', out)
        self.assertNotIn('href="http', out)
        self.assertNotIn("<link", out)
        self.assertNotIn("<script src", out)
        self.assertNotIn("//cdn", out)

    def test_script_breakout_is_escaped(self):
        # A concept id/type containing </script> must not terminate the inline
        # <script> block in the output.
        model = {
            "root": "/x",
            "files": {"evil": {"id": "evil</script><img src=x onerror=alert(1)>",
                               "type": "T</script>", "reserved": False, "errors": []}},
            "links": [],
        }
        out = ov.render_html(model)
        self.assertNotIn("</script><img", out)   # raw breakout absent
        self.assertIn("<\\/script>", out)         # escaped form present

if __name__ == "__main__":
    unittest.main()

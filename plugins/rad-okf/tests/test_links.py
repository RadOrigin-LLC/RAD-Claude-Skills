# plugins/rad-okf/tests/test_links.py
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_links as ol

class T(unittest.TestCase):
    def test_find_links(self):
        links = ol.find_links("see [A](/tables/a.md) and [B](../b.md) and [ext](http://x.com)")
        targets = [l["target"] for l in links]
        self.assertEqual(targets, ["/tables/a.md", "../b.md", "http://x.com"])

    def test_external(self):
        self.assertTrue(ol.is_external("http://x.com"))
        self.assertFalse(ol.is_external("/tables/a.md"))

    def test_resolve_absolute(self):
        self.assertEqual(ol.resolve_target("/tables/a.md", "x/y"), "tables/a")

    def test_resolve_relative(self):
        self.assertEqual(ol.resolve_target("../b.md", "tables/users"), "b")
        self.assertEqual(ol.resolve_target("c.md", "tables/users"), "tables/c")

if __name__ == "__main__":
    unittest.main()

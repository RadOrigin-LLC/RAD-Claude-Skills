# plugins/rad-okf/scripts/okf_convert.py
"""Convert a non-markdown text source into a markdown concept body, then wrap it
in OKF frontmatter via okf_new.build_concept and write it through the same path
as `new` (dry-run, index regen, log append, bundle-containment guard).

Pure converters (to_markdown_body) handle .txt/.html/.htm/.csv/.json with the
stdlib only. Markdown (.md) is routed to the `add` command; binary formats
(PDF/docx) are extracted by the agent and written via `new --body`."""
import argparse, csv, io, json, sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
import okf_bundle as ob
import okf_config as cfg
import okf_io as oio
import okf_index as oi
import okf_log as olog
import okf_new as onew

SUPPORTED = (".txt", ".html", ".htm", ".csv", ".json")

class _HTMLToText(HTMLParser):
    """Minimal HTML -> markdown: headings, paragraphs/divs, list items, links.
    script/style content is dropped. Good enough for v2 (quality varies — §13)."""
    BLOCK = {"p", "div", "section", "article", "header", "footer",
             "ul", "ol", "tr", "blockquote"}
    HEAD = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__()
        self.parts = []        # finished block strings
        self.buf = []          # inline text for the current block
        self.skip = 0          # >0 while inside script/style
        self.heading = None    # current heading level, or None
        self.bullet = False    # current block is a list item
        self.href = None       # current <a> target

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in self.HEAD:
            self._flush(); self.heading = int(tag[1])
        elif tag == "li":
            self._flush(); self.bullet = True
        elif tag in self.BLOCK:
            self._flush()
        elif tag == "a":
            self.href = dict(attrs).get("href")

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            self._flush()

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.HEAD or tag in self.BLOCK or tag == "li":
            self._flush()
        elif tag == "a":
            self.href = None

    def handle_data(self, data):
        if self.skip:
            return
        if self.href:
            text = data.strip()
            if text:
                self.buf.append("[%s](%s)" % (text, self.href))
        else:
            self.buf.append(data)

    def _flush(self):
        text = " ".join("".join(self.buf).split())
        self.buf = []
        if text:
            if self.heading:
                self.parts.append("#" * self.heading + " " + text)
            elif self.bullet:
                self.parts.append("- " + text)
            else:
                self.parts.append(text)
        self.heading = None
        self.bullet = False

    def result(self):
        self._flush()
        return ("\n\n".join(self.parts) + "\n") if self.parts else ""

def _csv_to_table(text):
    rows = [r for r in csv.reader(io.StringIO(text)) if r]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    norm = [r + [""] * (width - len(r)) for r in rows]
    def line(cells):
        return "| " + " | ".join(c.replace("|", r"\|").strip() for c in cells) + " |"
    out = [line(norm[0]), "| " + " | ".join(["---"] * width) + " |"]
    out += [line(r) for r in norm[1:]]
    return "\n".join(out) + "\n"

def _json_to_block(text):
    try:
        data = json.loads(text)
    except ValueError:
        return "```json\n%s\n```\n" % text.strip()
    return "```json\n%s\n```\n" % json.dumps(data, indent=2, ensure_ascii=False)

def _html_to_md(text):
    p = _HTMLToText()
    p.feed(text)
    return p.result()

def _txt_to_md(text):
    return text.strip() + "\n" if text.strip() else ""

def to_markdown_body(text, ext):
    """Convert raw source text of the given extension to a markdown body.
    Raises ValueError for unsupported extensions."""
    ext = ext.lower()
    if ext == ".csv":
        return _csv_to_table(text)
    if ext == ".json":
        return _json_to_block(text)
    if ext in (".html", ".htm"):
        return _html_to_md(text)
    if ext == ".txt":
        return _txt_to_md(text)
    raise ValueError("unsupported extension for convert: %s" % ext)

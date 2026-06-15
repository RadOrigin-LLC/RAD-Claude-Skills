# plugins/rad-okf/scripts/okf_links.py
"""Markdown link parsing and resolution to OKF concept ids."""
import re, posixpath
from pathlib import PurePosixPath

LINK_RE = re.compile(r"\[(?P<text>[^\]]*)\]\((?P<target>[^)]+)\)")

def find_links(body):
    out = []
    for m in LINK_RE.finditer(body):
        out.append({
            "text": m.group("text"),
            "target": m.group("target").strip(),
            "start": m.start(),
            "end": m.end(),
        })
    return out

def is_external(target):
    return "://" in target or target.startswith("mailto:")

def resolve_target(target, source_id):
    """Resolve a link target to a concept id (path minus .md), or None for
    external/empty links. source_id is the concept id of the linking file."""
    if is_external(target):
        return None
    path_part = target.split("#", 1)[0].strip()
    if not path_part:
        return None
    if path_part.startswith("/"):
        cid = path_part.lstrip("/")
    else:
        base = PurePosixPath(source_id).parent
        cid = posixpath.normpath(str(base / path_part))
    return cid[:-3] if cid.endswith(".md") else cid

# plugins/rad-okf/scripts/okf_index.py
"""Generate, parse, validate, and regenerate the bundle's root index.md.
The engine owns the index: sections are grouped by top-level directory and
bullets come from each concept's frontmatter (title + description), so
regeneration is lossless when frontmatter is filled in."""
from pathlib import Path
import okf_links as ol
import okf_io as oio
import okf_model as om

def humanize(name):
    return name.replace("-", " ").replace("_", " ").strip().title()

def _bullet(model, cid):
    meta = model["files"][cid].get("meta", {})
    title = meta.get("title") or humanize(cid.split("/")[-1])
    line = "* [%s](%s.md)" % (title, cid)
    desc = meta.get("description")
    if isinstance(desc, str) and desc.strip():
        line += " — %s" % " ".join(desc.split())   # collapse newlines so the bullet stays one line
    return line

def generate_index_text(model, name):
    concepts = sorted(cid for cid, f in model["files"].items() if not f["reserved"])
    root_level = [c for c in concepts if "/" not in c]
    by_top = {}
    for c in concepts:
        if "/" in c:
            by_top.setdefault(c.split("/", 1)[0], []).append(c)
    lines = ["# %s" % name, ""]
    for c in root_level:
        lines.append(_bullet(model, c))
    if root_level:
        lines.append("")
    for top in sorted(by_top):
        lines.append("## %s" % humanize(top))
        for c in by_top[top]:
            lines.append(_bullet(model, c))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

def index_entries(index_text):
    """Set of concept ids the index links to (resolved from the root)."""
    out = set()
    for lk in ol.find_links(index_text):
        if ol.is_external(lk["target"]):
            continue
        cid = ol.resolve_target(lk["target"], "index")
        if cid:
            out.add(cid)
    return out

def validate_index(model):
    """Findings for concepts missing from the index and index links pointing at
    concepts that no longer exist. Pure (does not write).
    Note: a concept absent from the index will often also trip okf_model's
    'orphan' check; the two findings are intentionally distinct (index-drift is
    fixable by `check --fix`, orphan is advisory) and may co-fire."""
    findings = []
    expected = {cid for cid, f in model["files"].items() if not f["reserved"]}
    idx = model["files"].get("index")
    if idx is None:
        for cid in sorted(expected):
            findings.append({"severity": "info", "code": "index-drift", "id": cid,
                             "message": "no index.md; concept is unlisted"})
        return findings
    listed = index_entries(idx.get("body", ""))
    for cid in sorted(expected - listed):
        findings.append({"severity": "info", "code": "index-drift", "id": cid,
                         "message": "not listed in index.md"})
    for cid in sorted(listed - set(model["files"])):
        findings.append({"severity": "warning", "code": "index-drift", "id": cid,
                         "message": "index.md links to a missing concept"})
    return findings

def regenerate(root, name):
    """Rebuild root/index.md from the current bundle, preserving newline style."""
    p = Path(root) / "index.md"
    nl = "\n"
    if p.exists():
        _, nl = oio.read(p)
    model = om.build_model(root)
    oio.write(p, generate_index_text(model, name), nl)

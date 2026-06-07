#!/usr/bin/env python3
"""
doc-redundancy.py — Cross-doc duplicate detection for the active core.

Compares bullet items and headings across the active-core docs and flags
near-duplicates. A near-duplicate is content that appears in two different docs
that should reference each other rather than both carry the same content — the
duplication that confuses coding agents (a fact stated two ways drifts apart).

Active docs scanned:
  - AGENTS.md
  - docs/prd.md
  - docs/plan.md
  - docs/handoff.md
  - docs/reference/decision-log.md

Approach: tokenize bullet text and headings from each doc (lowercase, stopwords
removed), compute Jaccard similarity between cross-doc items, flag pairs above
the threshold. Intra-file repetition is ignored — that's plan-lint's job.

Modes: (no modes — single pass)

Usage:
  python3 doc-redundancy.py /path/to/project
  python3 doc-redundancy.py /path/to/project --threshold 0.6
  python3 doc-redundancy.py /path/to/project --json

Output:
  Default — human-readable text. Exit 1 if any MEDIUM duplicate found, else 0.
  --json   — single JSON object on stdout.
  Exit 2  — script errors (project dir not found).

Severity:
  MEDIUM — similarity >= 0.85 (likely duplicate content)
  LOW    — similarity in [threshold, 0.85) (related content; user judgment)

No third-party dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

DEFAULT_THRESHOLD = 0.7
TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
BULLET = re.compile(r"^\s*-\s+(?P<text>.+?)\s*$")
HEADING = re.compile(r"^#{1,6}\s+(?P<text>.+?)\s*$")

# Common English stopwords + low-signal tokens
STOPWORDS = frozenset({
    "a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "with",
    "and", "or", "but", "if", "then", "else", "when", "where", "what",
    "who", "how", "why", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "such", "do", "does",
    "did", "have", "has", "had", "will", "would", "could", "should", "can",
    "may", "might", "must", "shall", "we", "i", "you", "he", "she", "they",
    "our", "your", "their", "us", "them", "from", "into", "than", "more",
    "less", "most", "least", "all", "any", "some", "none", "each", "every",
    "no", "not", "yes", "out", "over", "via",
})

ACTIVE_DOCS = (
    "AGENTS.md",
    "docs/prd.md",
    "docs/plan.md",
    "docs/handoff.md",
    "docs/reference/decision-log.md",
)


@dataclass
class Item:
    file: str         # relative path
    line: int
    kind: str         # "bullet" | "heading"
    raw_text: str
    tokens: frozenset[str]


@dataclass
class Duplicate:
    severity: str     # MEDIUM | LOW
    file_a: str
    line_a: int
    text_a: str
    file_b: str
    line_b: int
    text_b: str
    similarity: float

    def to_dict(self) -> dict:
        return asdict(self)


# ---------- parsing ----------


def tokenize(text: str) -> frozenset[str]:
    """Normalize text into a frozenset of meaningful tokens for Jaccard."""
    tokens = TOKEN_RE.findall(text.lower())
    return frozenset(t for t in tokens if t not in STOPWORDS and len(t) > 1)


def extract_items(file_path: Path, rel_path: str) -> list[Item]:
    """Extract bullets and headings from a markdown file. Skip very short items."""
    items: list[Item] = []
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return items
    for lineno, raw in enumerate(text.splitlines(), start=1):
        m = BULLET.match(raw)
        if m:
            txt = m.group("text").strip()
            # Strip leading "**bold**:" labels (e.g., "- **Risk:** description")
            txt_norm = re.sub(r"^\*\*[^*]+\*\*:?\s*", "", txt)
            if len(txt_norm) >= 10:
                items.append(Item(
                    file=rel_path,
                    line=lineno,
                    kind="bullet",
                    raw_text=txt,
                    tokens=tokenize(txt_norm),
                ))
            continue
        h = HEADING.match(raw)
        if h:
            txt = h.group("text").strip()
            if len(txt) >= 10:
                items.append(Item(
                    file=rel_path,
                    line=lineno,
                    kind="heading",
                    raw_text=txt,
                    tokens=tokenize(txt),
                ))
    return items


# ---------- similarity ----------


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_duplicates(items: list[Item], threshold: float) -> list[Duplicate]:
    """For each cross-file pair, check Jaccard similarity. Flag above threshold."""
    duplicates: list[Duplicate] = []
    by_file: dict[str, list[Item]] = {}
    for item in items:
        by_file.setdefault(item.file, []).append(item)

    files = sorted(by_file.keys())
    for i, file_a in enumerate(files):
        for file_b in files[i + 1:]:
            for item_a in by_file[file_a]:
                if len(item_a.tokens) < 3:
                    continue
                for item_b in by_file[file_b]:
                    if len(item_b.tokens) < 3:
                        continue
                    sim = jaccard(item_a.tokens, item_b.tokens)
                    if sim >= threshold:
                        severity = "MEDIUM" if sim >= 0.85 else "LOW"
                        duplicates.append(Duplicate(
                            severity=severity,
                            file_a=item_a.file,
                            line_a=item_a.line,
                            text_a=item_a.raw_text,
                            file_b=item_b.file,
                            line_b=item_b.line,
                            text_b=item_b.raw_text,
                            similarity=round(sim, 3),
                        ))
    # Sort: MEDIUM first, then by similarity descending within severity
    duplicates.sort(key=lambda d: (0 if d.severity == "MEDIUM" else 1, -d.similarity))
    return duplicates


# ---------- doc discovery ----------


def collect_docs(project_dir: Path) -> list[tuple[Path, str]]:
    """Find the active-core docs under project_dir. Returns (abs_path, rel_path)."""
    found: list[tuple[Path, str]] = []
    for rel in ACTIVE_DOCS:
        abs_path = project_dir / rel
        if abs_path.exists() and abs_path.is_file():
            found.append((abs_path, rel))
    return found


# ---------- output ----------


def render_text(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"doc-redundancy: project={report['project_dir']}")
    docs_str = ", ".join(report["docs_scanned"]) if report["docs_scanned"] else "(none found)"
    lines.append(f"docs scanned: {report['doc_count']} ({docs_str})")
    lines.append(f"items extracted: {report['item_count']}")
    lines.append(f"threshold: {report['threshold']}")
    duplicates = report["duplicates"]
    if not duplicates:
        lines.append("")
        lines.append("OK — no cross-doc duplicates found above threshold.")
        return "\n".join(lines)

    by_sev: dict[str, list[dict]] = {}
    for d in duplicates:
        by_sev.setdefault(d["severity"], []).append(d)

    lines.append("")
    summary = ", ".join(f"{sev}: {len(by_sev[sev])}" for sev in ("MEDIUM", "LOW") if sev in by_sev)
    lines.append(f"Duplicates: {len(duplicates)} total — {summary}")
    for sev in ("MEDIUM", "LOW"):
        for d in by_sev.get(sev, []):
            lines.append(f"  {sev} (similarity={d['similarity']})")
            lines.append(f"    {d['file_a']}:{d['line_a']}  →  {d['text_a'][:80]}")
            lines.append(f"    {d['file_b']}:{d['line_b']}  →  {d['text_b'][:80]}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("project_dir", help="Path to project root (containing docs/)")
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Jaccard similarity threshold for flagging (default {DEFAULT_THRESHOLD})",
    )
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        print(f"error: project dir not found: {project_dir}", file=sys.stderr)
        return 2

    docs = collect_docs(project_dir)
    items: list[Item] = []
    for abs_path, rel_path in docs:
        items.extend(extract_items(abs_path, rel_path))

    duplicates = find_duplicates(items, args.threshold)

    report = {
        "project_dir": str(project_dir),
        "docs_scanned": [rel for _, rel in docs],
        "doc_count": len(docs),
        "item_count": len(items),
        "threshold": args.threshold,
        "duplicates": [d.to_dict() for d in duplicates],
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))

    fail = any(d["severity"] == "MEDIUM" for d in report["duplicates"])
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""
doc-contradiction.py — Cross-doc disagreement detection for the 4-doc active core.

Flags potential contradictions between docs that should agree. Mechanical token-
overlap detection — surfaces candidates for user review, not definitive errors.
Semantic contradiction needs natural-language reasoning beyond stdlib Python.

Check:
- docs/prd.md non-goals vs docs/plan.md commitments (task Objectives + In-scope)
  ("is the plan building something the PRD says is a non-goal?")

Severity is always MEDIUM or LOW — never CRITICAL or HIGH. The validator surfaces
signals; the user judges whether each is a real contradiction.

Usage:
  python3 doc-contradiction.py /path/to/project
  python3 doc-contradiction.py /path/to/project --threshold 0.4
  python3 doc-contradiction.py /path/to/project --json

Output:
  Default — human-readable text. Exit 0 always (findings are advisory).
  --json   — single JSON object on stdout.
  Exit 2  — script errors (project dir not found).

No third-party dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

DEFAULT_THRESHOLD = 0.4
TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
BULLET = re.compile(r"^\s*-\s+(?P<text>.+?)\s*$")
CHECKBOX = re.compile(r"^\s*-\s*\[(?P<box>[ x])\]\s*(?P<text>.+?)\s*$")
SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$")

# Negation words stripped from non-goal text before comparison, so the substantive
# content tokens can be matched against ACs that propose the opposite.
NEGATION_WORDS = frozenset({
    "not", "no", "never", "won't", "wont", "without",
    "neither", "nor", "none", "noone", "nobody",
    "skip", "skipping", "skipped", "avoid", "avoiding",
    "exclude", "excluded", "excluding",
})

STOPWORDS = frozenset({
    "a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "with",
    "and", "or", "but", "if", "then", "else", "when", "where", "what",
    "who", "how", "why", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "such", "do", "does",
    "did", "have", "has", "had", "will", "would", "could", "should", "can",
    "may", "might", "must", "shall", "we", "i", "you", "he", "she", "they",
    "our", "your", "their", "us", "them", "from", "into", "than", "more",
    "less", "most", "least", "all", "any", "some", "each", "every", "out",
    "over", "via", "yes",
})


@dataclass
class Item:
    section: str
    line: int
    raw_text: str
    tokens: frozenset[str]
    tokens_no_negation: frozenset[str]


@dataclass
class Finding:
    severity: str     # MEDIUM | LOW
    category: str     # non_goal_vs_ac | (future: pattern_vs_adr, milestone_vs_status)
    file_a: str
    line_a: int
    text_a: str
    file_b: str
    line_b: int
    text_b: str
    overlap: float
    note: str

    def to_dict(self) -> dict:
        return asdict(self)


def _stem(tok: str) -> str:
    """Very simple stemmer — strips common English plurals. v1 only.

    Catches `apps`→`app`, `users`→`user`, `flies`→`fly`. Not a real stemmer;
    intentionally conservative to avoid false collapses. Improves recall for
    contradiction detection where plural/singular mismatch is common.
    """
    if len(tok) > 3:
        if tok.endswith("ies"):
            return tok[:-3] + "y"
        if tok.endswith("es") and not tok.endswith("ses") and not tok.endswith("ues"):
            return tok[:-2]
        if tok.endswith("s") and not tok.endswith("ss") and not tok.endswith("us"):
            return tok[:-1]
    return tok


def tokenize(text: str) -> tuple[frozenset[str], frozenset[str]]:
    """Return (tokens_with_negation_intact, tokens_with_negation_stripped).

    Tokens are stemmed for plural/singular collapse so "apps" matches "app".
    """
    raw_tokens = TOKEN_RE.findall(text.lower())
    filtered = [t for t in raw_tokens if t not in STOPWORDS and len(t) > 1]
    stemmed = [_stem(t) for t in filtered]
    with_neg = frozenset(stemmed)
    no_neg = frozenset(t for t in with_neg if t not in NEGATION_WORDS)
    return with_neg, no_neg


def parse_section_items(file_path: Path, section_name: str) -> list[Item]:
    """Extract bullet/checkbox items from a named ## section of a markdown file."""
    items: list[Item] = []
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return items

    in_section = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        m = SECTION_HEADING.match(raw)
        if m:
            in_section = m.group(1).strip() == section_name
            continue
        if not in_section:
            continue

        cm = CHECKBOX.match(raw)
        bm = BULLET.match(raw)
        text_content = None
        if cm:
            text_content = cm.group("text").strip()
        elif bm:
            text_content = bm.group("text").strip()
        if text_content and len(text_content) >= 8:
            # Strip leading "**Label:** " prefix common in template-style docs
            text_norm = re.sub(r"^\*\*[^*]+\*\*:?\s*", "", text_content)
            with_neg, no_neg = tokenize(text_norm)
            items.append(Item(
                section=section_name,
                line=lineno,
                raw_text=text_content,
                tokens=with_neg,
                tokens_no_negation=no_neg,
            ))
    return items


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------- checks ----------


def parse_plan_commitments(plan_path: Path) -> list[Item]:
    """Extract what the plan commits to BUILDING: each task's Objective field plus
    the 'In scope' bullets. These are what a PRD non-goal would contradict."""
    items: list[Item] = []
    try:
        text = plan_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return items

    obj_re = re.compile(r"^\s*-\s*\*\*Objective:\*\*\s*(?P<text>.+?)\s*$")
    in_scope_label = re.compile(r"^\s*\*\*In scope", re.IGNORECASE)
    out_scope_label = re.compile(r"^\s*\*\*(Out of scope|Non-goals)", re.IGNORECASE)

    in_scope_section = False
    in_scope = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        sm = SECTION_HEADING.match(raw)
        if sm:
            in_scope_section = sm.group(1).strip().lower() == "scope"
            in_scope = False
        om = obj_re.match(raw)
        if om:
            t = om.group("text").strip()
            if len(t) >= 8:
                with_neg, no_neg = tokenize(t)
                items.append(Item("Objective", lineno, t, with_neg, no_neg))
            continue
        if in_scope_section:
            if in_scope_label.match(raw):
                in_scope = True
                continue
            if out_scope_label.match(raw):
                in_scope = False
                continue
            if in_scope:
                bm = BULLET.match(raw)
                if bm:
                    t = bm.group("text").strip()
                    if len(t) >= 8:
                        with_neg, no_neg = tokenize(t)
                        items.append(Item("In scope", lineno, t, with_neg, no_neg))
    return items


def check_nongoals_vs_plan(project_dir: Path, threshold: float) -> list[Finding]:
    """For each prd.md non-goal, check whether the plan commits to building it."""
    findings: list[Finding] = []
    prd_path = project_dir / "docs" / "prd.md"
    plan_path = project_dir / "docs" / "plan.md"
    if not prd_path.exists() or not plan_path.exists():
        return findings

    non_goals = parse_section_items(prd_path, "Non-goals")
    commitments = parse_plan_commitments(plan_path)

    for ng in non_goals:
        if len(ng.tokens_no_negation) < 2:
            continue
        for c in commitments:
            if len(c.tokens_no_negation) < 2:
                continue
            sim = jaccard(ng.tokens_no_negation, c.tokens_no_negation)
            if sim >= threshold:
                severity = "MEDIUM" if sim >= 0.6 else "LOW"
                findings.append(Finding(
                    severity=severity,
                    category="nongoal_vs_plan",
                    file_a="docs/prd.md",
                    line_a=ng.line,
                    text_a=ng.raw_text,
                    file_b="docs/plan.md",
                    line_b=c.line,
                    text_b=c.raw_text,
                    overlap=round(sim, 3),
                    note=f"Plan {c.section.lower()} overlaps a PRD non-goal — confirm intent",
                ))
    findings.sort(key=lambda f: (0 if f.severity == "MEDIUM" else 1, -f.overlap))
    return findings


# ---------- output ----------


def render_text(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"doc-contradiction: project={report['project_dir']}")
    lines.append(f"checks run: {', '.join(report['checks_run'])}")
    lines.append(f"threshold: {report['threshold']}")

    findings = report["findings"]
    if not findings:
        lines.append("")
        lines.append("OK — no cross-doc contradictions found.")
        return "\n".join(lines)

    by_sev: dict[str, list[dict]] = {}
    for f in findings:
        by_sev.setdefault(f["severity"], []).append(f)

    lines.append("")
    summary = ", ".join(f"{sev}: {len(by_sev[sev])}" for sev in ("MEDIUM", "LOW") if sev in by_sev)
    lines.append(f"Findings: {len(findings)} total — {summary}")
    lines.append("(Mechanical detection — surface for user review, not definitive errors.)")
    for sev in ("MEDIUM", "LOW"):
        for f in by_sev.get(sev, []):
            lines.append(f"  {sev} ({f['category']}, overlap={f['overlap']})")
            lines.append(f"    {f['note']}")
            lines.append(f"    {f['file_a']}:{f['line_a']}  →  {f['text_a'][:80]}")
            lines.append(f"    {f['file_b']}:{f['line_b']}  →  {f['text_b'][:80]}")
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
        help=f"Jaccard overlap threshold for flagging (default {DEFAULT_THRESHOLD})",
    )
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        print(f"error: project dir not found: {project_dir}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    checks_run: list[str] = ["nongoal_vs_plan"]
    findings.extend(check_nongoals_vs_plan(project_dir, args.threshold))

    report = {
        "project_dir": str(project_dir),
        "checks_run": checks_run,
        "threshold": args.threshold,
        "findings": [f.to_dict() for f in findings],
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))

    # Always exit 0 — findings are advisory, not errors
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

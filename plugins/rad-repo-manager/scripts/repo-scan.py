#!/usr/bin/env python3
"""
repo-scan.py — mechanical drift signals consumed by rad-repo-manager's repo-align.

High-precision, mechanical signals only — so the loose-ends count is trustworthy and
never cries wolf. Fuzzy checks (contradiction, redundancy) have their own scripts.

Signals (each a "loose end"):
  1. Active-set growth — AGENTS.md's declared cold-start read path lists more than the
     4 core docs.
  2. Floating docs — a .md at the repo root or directly under docs/ that isn't a known
     core/allowed file. (Scoped narrowly on purpose: .md inside source trees, packages,
     etc. is NOT considered — component READMEs must never false-flag.)
  3. Legacy inbox items — docs/inbox/*.md (a retired tier; flagged so contents get filed out).
  4. AGENTS.md bloat — past a soft line cap.

Severity: 0 -> green, 1-4 -> yellow, >=5 -> red.

Nudge cooldown: the optional "run repo-align" suggestion (red only, standalone runs
only) is rate-limited via a small state file (.rad/repo-manager-state.json) so it
can't nag. repo-align itself calls with --no-record, so it never writes state.

Usage:
  python3 repo-scan.py <project-dir>
  python3 repo-scan.py <project-dir> --json
  python3 repo-scan.py <project-dir> --json --no-record   # don't update nudge state

Output: human text by default; --json emits a single object. Exit 0 always (advisory).
No third-party dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CORE_DOCS = ("docs/prd.md", "docs/plan.md", "docs/handoff.md")

# Root-level .md files that are normal project furniture — never "floating".
ALLOWED_ROOT = {
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md", "LICENSE.md",
    "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "CHANGELOG.md",
}

AGENTS_SOFT_LINE_CAP = 250
SEVERITY_YELLOW = 1
SEVERITY_RED = 5
NUDGE_COOLDOWN_SCANS = 3

READ_PATH_HEADING = re.compile(r"cold-start read path", re.IGNORECASE)
NUMBERED_ITEM = re.compile(r"^\s*\d+\.\s+")


def find_floating(root: Path) -> list[str]:
    """Floating = a .md at repo root (not in ALLOWED_ROOT) or directly under docs/
    (not a core doc). Deliberately shallow — code-adjacent .md is ignored."""
    floating: list[str] = []

    for p in sorted(root.glob("*.md")):
        if p.name not in ALLOWED_ROOT:
            floating.append(p.name)

    docs = root / "docs"
    if docs.is_dir():
        core_names = {Path(c).name for c in CORE_DOCS}
        for p in sorted(docs.glob("*.md")):
            if p.name not in core_names:
                floating.append(f"docs/{p.name}")

    return floating


def count_inbox(root: Path) -> list[str]:
    inbox = root / "docs" / "inbox"
    if not inbox.is_dir():
        return []
    return [f"docs/inbox/{p.name}" for p in sorted(inbox.glob("*.md"))
            if p.name.lower() != "readme.md"]


def declared_active_count(root: Path) -> int | None:
    """Count the numbered entries under AGENTS.md's 'cold-start read path' heading.
    Returns None if AGENTS.md or the section is absent."""
    agents = root / "AGENTS.md"
    if not agents.is_file():
        return None
    lines = agents.read_text(encoding="utf-8", errors="replace").splitlines()
    in_section = False
    count = 0
    for ln in lines:
        if READ_PATH_HEADING.search(ln):
            in_section = True
            continue
        if in_section:
            if NUMBERED_ITEM.match(ln):
                count += 1
            elif ln.strip().startswith("#"):
                break  # next heading ends the section
            elif count > 0 and not ln.strip():
                # blank after the list ends it
                if count >= 1:
                    break
    return count if count else None


def agents_line_count(root: Path) -> int | None:
    agents = root / "AGENTS.md"
    if not agents.is_file():
        return None
    return len(agents.read_text(encoding="utf-8", errors="replace").splitlines())


def load_state(root: Path) -> dict:
    state_file = root / ".rad" / "repo-manager-state.json"
    if state_file.is_file():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(root: Path, state: dict) -> None:
    rad = root / ".rad"
    try:
        rad.mkdir(exist_ok=True)
        (rad / "repo-manager-state.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )
    except OSError:
        pass  # state is best-effort; never fail the scan over it


def scan(root: Path, record: bool) -> dict:
    floating = find_floating(root)
    inbox = count_inbox(root)
    active = declared_active_count(root)
    agents_lines = agents_line_count(root)

    breakdown: dict[str, object] = {}
    loose = 0

    if active is not None and active > 4:
        breakdown["active_set_overflow"] = active - 4
        loose += active - 4
    if floating:
        breakdown["floating"] = floating
        loose += len(floating)
    if inbox:
        breakdown["inbox"] = inbox
        loose += len(inbox)
    if agents_lines is not None and agents_lines > AGENTS_SOFT_LINE_CAP:
        breakdown["agents_bloat"] = {"lines": agents_lines, "cap": AGENTS_SOFT_LINE_CAP}
        loose += 1

    if loose == 0:
        severity = "green"
    elif loose < SEVERITY_RED:
        severity = "yellow"
    else:
        severity = "red"

    # Nudge cooldown — only the red repo-align tail is rate-limited.
    state = load_state(root)
    scan_count = int(state.get("scan_count", 0)) + 1
    last_nudge = int(state.get("last_red_nudge_scan", -NUDGE_COOLDOWN_SCANS))
    show_nudge = severity == "red" and (scan_count - last_nudge) >= NUDGE_COOLDOWN_SCANS
    if record:
        state["scan_count"] = scan_count
        if show_nudge:
            state["last_red_nudge_scan"] = scan_count
        save_state(root, state)

    return {
        "loose_ends": loose,
        "severity": severity,
        "show_nudge": show_nudge,
        "breakdown": breakdown,
        "agents_present": agents_lines is not None,
    }


def render_text(report: dict) -> str:
    n = report["loose_ends"]
    sev = report["severity"]
    if sev == "green":
        return "Repo's tidy — nothing loose."
    if sev == "yellow":
        return f"A few loose ends ({n}) — fine for now."
    tail = " — worth a /rad-repo-manager:repo-align to sort it." if report["show_nudge"] else "."
    return f"Getting cluttered ({n}){tail}"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("path", help="Project directory to scan")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    p.add_argument("--no-record", action="store_true", help="Don't update nudge state")
    args = p.parse_args(argv)

    root = Path(args.path)
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    report = scan(root, record=not args.no_record)
    print(json.dumps(report, indent=2) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

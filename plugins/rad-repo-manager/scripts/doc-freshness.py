#!/usr/bin/env python3
"""
doc-freshness.py — staleness signals for the active core docs.

Implements the "active doc unchanged while code churned" drift signal: for each core
doc, when was it last committed, and how much non-doc code has changed since? Plus a
handoff-specific check: the handoff should be refreshed every working session, so any
code commit newer than the handoff (with no uncommitted handoff edit in flight) means
the resume snapshot is stale.

Pure git + stdlib, advisory only, fast (a handful of git calls). Run by:
  - /rad-repo-manager:startup  (every session — feeds the "Doc freshness" line)
  - /rad-repo-manager:repo-align (the deep pass)
  - hooks/session-start.py (ambient one-liner at session start)

Severity model (advisory candidates, not verdicts):
  HIGH    handoff very stale (>= 5 code commits or >= 7 days behind HEAD)
  MEDIUM  handoff behind HEAD at all; prd/plan past their MEDIUM commit threshold
  LOW     prd/plan past their LOW commit threshold
  INFO    doc missing, untracked, or no git history — reported, never counted stale

Thresholds (code-touching commits since the doc last changed):
  docs/plan.md  LOW >= 10, MEDIUM >= 20
  docs/prd.md   LOW >= 15, MEDIUM >= 30
  AGENTS.md     informational only (staying unchanged is normal)

Usage:
  python3 doc-freshness.py <project-dir>
  python3 doc-freshness.py <project-dir> --json

Output: human text by default; --json emits a single object. Exit 0 always (advisory).
No third-party dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CORE_DOCS = ("AGENTS.md", "docs/prd.md", "docs/plan.md", "docs/handoff.md")

THRESHOLDS = {
    "docs/prd.md": {"low": 15, "medium": 30},
    "docs/plan.md": {"low": 10, "medium": 20},
}

HANDOFF = "docs/handoff.md"
HANDOFF_HIGH_COMMITS = 5
HANDOFF_HIGH_DAYS = 7

UPDATED_STAMP = re.compile(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})")


def git(root: Path, *args: str) -> str | None:
    """Run a git command; return stripped stdout, or None on any failure."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def doc_state(root: Path, doc: str) -> dict:
    """Gather the git facts for one doc."""
    path = root / doc
    state: dict = {"path": doc, "exists": path.is_file()}
    if not state["exists"]:
        return state

    last_hash = git(root, "log", "-1", "--format=%H", "--", doc)
    if not last_hash:
        state["tracked"] = False  # never committed (or no git history)
        return state
    state["tracked"] = True
    state["last_commit_date"] = git(root, "log", "-1", "--format=%cI", "--", doc)

    # Code-touching commits since this doc last changed (excludes all .md churn).
    count = git(root, "rev-list", "--count", f"{last_hash}..HEAD",
                "--", ".", ":(exclude)*.md")
    state["code_commits_since"] = int(count) if count and count.isdigit() else 0

    # Uncommitted edit in flight counts as "being kept fresh right now".
    porcelain = git(root, "status", "--porcelain", "--", doc)
    state["dirty"] = bool(porcelain)

    stamp = UPDATED_STAMP.search(path.read_text(encoding="utf-8", errors="replace"))
    if stamp:
        state["updated_stamp"] = stamp.group(1)
    return state


def days_behind_head(root: Path, doc_date: str | None) -> int | None:
    head_date = parse_iso(git(root, "log", "-1", "--format=%cI"))
    doc_dt = parse_iso(doc_date)
    if not head_date or not doc_dt:
        return None
    return max(0, (head_date - doc_dt).days)


def judge(root: Path, states: dict[str, dict]) -> list[dict]:
    findings: list[dict] = []

    for doc, st in states.items():
        if not st["exists"]:
            findings.append({"path": doc, "severity": "INFO",
                             "summary": f"{doc} is missing."})
            continue
        if not st.get("tracked"):
            findings.append({"path": doc, "severity": "INFO",
                             "summary": f"{doc} exists but has never been committed."})
            continue

    # Handoff: should be refreshed every working session.
    ho = states.get(HANDOFF, {})
    if ho.get("tracked"):
        behind = ho.get("code_commits_since", 0)
        if behind > 0 and not ho.get("dirty"):
            days = days_behind_head(root, ho.get("last_commit_date"))
            sev = "HIGH" if (behind >= HANDOFF_HIGH_COMMITS
                             or (days is not None and days >= HANDOFF_HIGH_DAYS)) else "MEDIUM"
            bits = [f"{behind} code commit{'s' if behind != 1 else ''} since it was last updated"]
            if days:
                bits.append(f"~{days} day{'s' if days != 1 else ''} behind the latest commit")
            stamp = ho.get("updated_stamp")
            stamped = f" (stamped {stamp})" if stamp else ""
            findings.append({
                "path": HANDOFF, "severity": sev,
                "summary": f"docs/handoff.md is stale{stamped}: " + ", ".join(bits) +
                           ". The resume snapshot no longer reflects the repo.",
            })

    # prd / plan: unchanged while code churned.
    for doc, th in THRESHOLDS.items():
        st = states.get(doc, {})
        if not st.get("tracked") or st.get("dirty"):
            continue
        n = st.get("code_commits_since", 0)
        if n >= th["medium"]:
            sev = "MEDIUM"
        elif n >= th["low"]:
            sev = "LOW"
        else:
            continue
        findings.append({
            "path": doc, "severity": sev,
            "summary": f"{doc} unchanged across {n} code-touching commits — "
                       f"worth checking it still matches reality.",
        })

    return findings


def overall(findings: list[dict]) -> str:
    sevs = {f["severity"] for f in findings}
    for level in ("HIGH", "MEDIUM", "LOW"):
        if level in sevs:
            return level.lower()
    return "fresh"


def render_text(report: dict) -> str:
    if not report["git_history"]:
        return "No git history yet — freshness can't be measured."
    findings = report["findings"]
    real = [f for f in findings if f["severity"] != "INFO"]
    info = [f for f in findings if f["severity"] == "INFO"]
    lines = []
    if not real:
        lines.append("Core docs look fresh.")
    for f in real:
        lines.append(f"[{f['severity']}] {f['summary']}")
    for f in info:
        lines.append(f"[info] {f['summary']}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("path", help="Project directory to scan")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    root = Path(args.path)
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    has_history = git(root, "rev-parse", "HEAD") is not None
    states = {doc: doc_state(root, doc) for doc in CORE_DOCS}
    findings = judge(root, states) if has_history else []

    report = {
        "git_history": has_history,
        "severity": overall(findings) if has_history else "unknown",
        "findings": findings,
        "docs": states,
    }
    print(json.dumps(report, indent=2) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

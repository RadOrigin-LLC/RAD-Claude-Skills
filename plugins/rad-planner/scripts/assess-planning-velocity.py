#!/usr/bin/env python3
"""
assess-planning-velocity.py — overplanning-signal validator.

Measures four planning-velocity signals over a project's git history to surface
the planning-as-avoidance pattern (rewriting plans instead of shipping code):

  1. current_md_edits_since_last_code_commit
     Count of commits touching docs/planning/current.md since the last commit
     that touched non-docs files on the active branch.
     Threshold (default): 5. Above threshold flagged.

  2. ac_rewrite_count_per_ac
     For each acceptance-criterion checkbox line currently in
     docs/planning/current.md, count how many times the line was rewritten
     across git history (via blame-style diff scan).
     Threshold (default): 3 rewrites per AC. Above threshold flagged per-AC.

  3. planning_doc_growth_ratio
     Size delta (in bytes) of docs/ over the last N days vs size delta of
     tracked source files. Above ratio (default 2.0) flagged.

  4. time_since_last_code_commit
     Days since the last commit that touched non-docs source files.
     Threshold (default): 14 days with current.md mtime fresh (<7 days).
     Both conditions → flagged.

This is a heuristic, not a verdict. It surfaces signals the user evaluates.

Usage:
  python3 assess-planning-velocity.py <project-dir>
  python3 assess-planning-velocity.py <project-dir> --json
  python3 assess-planning-velocity.py <project-dir> \
    --threshold-edits 8 --threshold-rewrites 5 \
    --threshold-growth 3.0 --threshold-stale-days 21 \
    --window-days 30

Exit codes:
  0 — no signals flagged OR git not initialized (graceful skip)
  1 — at least one signal flagged
  2 — script error

Pure stdlib, Python 3.8+. Shells out to system `git` binary.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

DOCS_PATH = "docs/"
PLANNING_CURRENT = "docs/planning/current.md"

# Default thresholds — exposed as CLI flags for per-project override
DEFAULT_THRESHOLD_EDITS = 5
DEFAULT_THRESHOLD_REWRITES = 3
DEFAULT_THRESHOLD_GROWTH = 2.0
DEFAULT_THRESHOLD_STALE_DAYS = 14
DEFAULT_FRESH_PLAN_DAYS = 7
DEFAULT_WINDOW_DAYS = 30

# Files counted as "docs" for the docs-vs-source split
DOCS_PREFIXES = ("docs/", "README", "CHANGELOG", ".claude/", "AGENTS.md", "CLAUDE.md")


@dataclass
class Signal:
    name: str
    value: float | int | str
    threshold: float | int | None
    flagged: bool
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Report:
    project_dir: str
    git_available: bool
    signals: list[Signal] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_dir": self.project_dir,
            "git_available": self.git_available,
            "signals": [s.to_dict() for s in self.signals],
            "notes": self.notes,
        }


def _git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=20,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "git binary not found on PATH"
    except subprocess.TimeoutExpired:
        return 124, "", "git command timed out"


def _is_docs_path(path: str) -> bool:
    return any(path.startswith(p) for p in DOCS_PREFIXES)


def _signal_edits_since_last_code_commit(cwd: Path, threshold: int) -> Signal:
    """Count of commits touching planning/current.md after the last commit
    that touched non-docs files."""
    # Get the SHA of the most recent commit touching a non-docs source file.
    # Strategy: walk commits newest-first; for each, list changed files; stop
    # at the first commit with any non-docs file.
    code, out, err = _git(
        ["log", "--pretty=format:%H", "--name-only", "-z", "--no-merges", "--", "."],
        cwd,
    )
    if code != 0:
        return Signal(
            name="current_md_edits_since_last_code_commit",
            value="error",
            threshold=threshold,
            flagged=False,
            message=f"git log failed: {err}",
        )

    # Parse: each commit is "SHA\n<file1>\n<file2>\n...\0" with -z separator.
    commits: list[tuple[str, list[str]]] = []
    raw = out.replace("\x00", "\n").splitlines()
    current_sha: str | None = None
    current_files: list[str] = []
    for line in raw:
        line = line.strip()
        if not line:
            if current_sha:
                commits.append((current_sha, current_files))
                current_sha = None
                current_files = []
            continue
        if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
            if current_sha:
                commits.append((current_sha, current_files))
            current_sha = line
            current_files = []
        else:
            current_files.append(line)
    if current_sha:
        commits.append((current_sha, current_files))

    edits = 0
    for _sha, files in commits:
        has_code = any(f and not _is_docs_path(f) for f in files)
        if has_code:
            break
        if PLANNING_CURRENT in files:
            edits += 1

    flagged = edits > threshold
    msg = (
        f"{edits} edit(s) to docs/planning/current.md since last code commit "
        f"(threshold: {threshold})"
    )
    if flagged:
        msg += " — planning-as-avoidance signal"
    return Signal(
        name="current_md_edits_since_last_code_commit",
        value=edits,
        threshold=threshold,
        flagged=flagged,
        message=msg,
    )


def _signal_ac_rewrite_count(cwd: Path, threshold: int) -> Signal:
    """For each AC checkbox line in current.md, count rewrites in git history.

    Heuristic: parse current ACs from the current.md, then run `git log -L`
    on the Acceptance criteria section. Count number of commits that modified
    each AC line.
    """
    plan_path = cwd / PLANNING_CURRENT
    if not plan_path.exists():
        return Signal(
            name="ac_rewrite_count_per_ac",
            value="no current.md",
            threshold=threshold,
            flagged=False,
            message="docs/planning/current.md not present — signal skipped",
        )

    # Find the line range of "## Acceptance criteria"
    lines = plan_path.read_text(encoding="utf-8", errors="replace").splitlines()
    ac_start: int | None = None
    ac_end: int | None = None
    for i, ln in enumerate(lines, start=1):
        if ln.strip().lower() == "## acceptance criteria":
            ac_start = i
            continue
        if ac_start and ln.startswith("## "):
            ac_end = i - 1
            break
    if ac_start and not ac_end:
        ac_end = len(lines)
    if not ac_start or not ac_end:
        return Signal(
            name="ac_rewrite_count_per_ac",
            value="no AC section",
            threshold=threshold,
            flagged=False,
            message="No '## Acceptance criteria' section in current.md",
        )

    # git log -L <start>,<end>:<file>  returns commits that touched that range.
    # Count commits = rewrite count for that section.
    code, out, err = _git(
        ["log", "--pretty=format:%H", "-L", f"{ac_start},{ac_end}:{PLANNING_CURRENT}"],
        cwd,
    )
    if code != 0:
        return Signal(
            name="ac_rewrite_count_per_ac",
            value="error",
            threshold=threshold,
            flagged=False,
            message=f"git log -L failed: {err}",
        )
    # Lines in output that look like SHAs (40 hex chars) count as commits
    rewrite_count = sum(
        1 for ln in out.splitlines()
        if len(ln.strip()) == 40 and all(c in "0123456789abcdef" for c in ln.strip())
    )

    flagged = rewrite_count > threshold
    msg = (
        f"Acceptance-criteria section rewritten {rewrite_count} time(s) "
        f"(threshold: {threshold})"
    )
    if flagged:
        msg += " — ACs are churning; consider whether you're refining the plan or refining the product"
    return Signal(
        name="ac_rewrite_count_per_ac",
        value=rewrite_count,
        threshold=threshold,
        flagged=flagged,
        message=msg,
    )


def _signal_planning_doc_growth(cwd: Path, threshold: float, window_days: int) -> Signal:
    """Ratio of docs/ byte-growth to source byte-growth over the last N days."""
    since = f"--since={window_days}.days"
    # Get diff stats for the window
    code, out, err = _git(
        ["log", since, "--no-merges", "--numstat", "--pretty=format:"],
        cwd,
    )
    if code != 0:
        return Signal(
            name="planning_doc_growth_ratio",
            value="error",
            threshold=threshold,
            flagged=False,
            message=f"git log --numstat failed: {err}",
        )
    docs_delta = 0
    source_delta = 0
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_str, removed_str, path = parts
        if added_str == "-" or removed_str == "-":
            # Binary file — skip
            continue
        try:
            added = int(added_str)
            removed = int(removed_str)
        except ValueError:
            continue
        delta = added + removed  # total change magnitude in lines
        if _is_docs_path(path):
            docs_delta += delta
        else:
            source_delta += delta

    if source_delta == 0:
        if docs_delta == 0:
            return Signal(
                name="planning_doc_growth_ratio",
                value=0.0,
                threshold=threshold,
                flagged=False,
                message=f"No activity in last {window_days} days",
            )
        # Pure docs activity — flag heavily
        ratio = float("inf")
        flagged = True
        msg = (
            f"{docs_delta} doc-line changes vs 0 source-line changes "
            f"in last {window_days} days — entirely planning, no shipping"
        )
        return Signal(
            name="planning_doc_growth_ratio",
            value="docs-only",
            threshold=threshold,
            flagged=flagged,
            message=msg,
        )

    ratio = docs_delta / source_delta
    flagged = ratio > threshold
    msg = (
        f"docs:source line-change ratio = {ratio:.2f} "
        f"({docs_delta} docs / {source_delta} source) over last {window_days} days "
        f"(threshold: {threshold})"
    )
    if flagged:
        msg += " — planning is outpacing shipping"
    return Signal(
        name="planning_doc_growth_ratio",
        value=round(ratio, 2),
        threshold=threshold,
        flagged=flagged,
        message=msg,
    )


def _signal_time_since_last_code_commit(
    cwd: Path,
    threshold_days: int,
    fresh_plan_days: int,
) -> Signal:
    """Days since last non-docs commit, flagged when current.md is fresh."""
    code, out, err = _git(
        ["log", "--pretty=format:%H %ct", "--name-only", "-z", "--no-merges"],
        cwd,
    )
    if code != 0:
        return Signal(
            name="time_since_last_code_commit",
            value="error",
            threshold=threshold_days,
            flagged=False,
            message=f"git log failed: {err}",
        )

    # Parse commits — each "SHA <unix-ts>\nfile1\nfile2\n...\0"
    raw = out.replace("\x00", "\n").splitlines()
    last_code_ts: int | None = None
    current_ts: int | None = None
    current_files: list[str] = []

    for line in raw:
        line = line.strip()
        if not line:
            if current_ts and current_files:
                if any(f and not _is_docs_path(f) for f in current_files):
                    last_code_ts = current_ts
                    break
            current_ts = None
            current_files = []
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2 and len(parts[0]) == 40:
            try:
                if current_ts and current_files:
                    if any(f and not _is_docs_path(f) for f in current_files):
                        last_code_ts = current_ts
                        break
                current_ts = int(parts[1])
                current_files = []
            except ValueError:
                pass
        else:
            current_files.append(line)

    # Tail flush
    if last_code_ts is None and current_ts and current_files:
        if any(f and not _is_docs_path(f) for f in current_files):
            last_code_ts = current_ts

    if last_code_ts is None:
        return Signal(
            name="time_since_last_code_commit",
            value="never",
            threshold=threshold_days,
            flagged=False,
            message="No non-docs commits found in history",
        )

    now = int(time.time())
    days = (now - last_code_ts) / 86400

    # Check planning freshness
    plan_path = cwd / PLANNING_CURRENT
    plan_fresh = False
    plan_mtime_days: float | None = None
    if plan_path.exists():
        plan_mtime_days = (now - plan_path.stat().st_mtime) / 86400
        plan_fresh = plan_mtime_days < fresh_plan_days

    flagged = days > threshold_days and plan_fresh
    msg = f"Last code commit was {days:.1f} days ago (threshold: {threshold_days})"
    if plan_mtime_days is not None:
        msg += f"; current.md was last touched {plan_mtime_days:.1f} days ago"
    if flagged:
        msg += " — planning is fresh but code is stale; consider executing the plan"
    return Signal(
        name="time_since_last_code_commit",
        value=round(days, 1),
        threshold=threshold_days,
        flagged=flagged,
        message=msg,
    )


def assess(project_dir: Path, thresholds: dict) -> Report:
    report = Report(project_dir=str(project_dir), git_available=False)

    if not project_dir.exists():
        report.notes.append(f"Project directory not found: {project_dir}")
        return report

    code, _out, _err = _git(["rev-parse", "--is-inside-work-tree"], project_dir)
    if code != 0:
        report.notes.append("Not a git repository — planning-velocity signals unavailable")
        return report
    report.git_available = True

    report.signals.append(_signal_edits_since_last_code_commit(
        project_dir, thresholds["edits"]
    ))
    report.signals.append(_signal_ac_rewrite_count(
        project_dir, thresholds["rewrites"]
    ))
    report.signals.append(_signal_planning_doc_growth(
        project_dir, thresholds["growth"], thresholds["window"]
    ))
    report.signals.append(_signal_time_since_last_code_commit(
        project_dir, thresholds["stale_days"], thresholds["fresh_plan_days"]
    ))

    return report


def render_text(report: Report) -> str:
    lines = [f"Planning velocity assessment — {report.project_dir}"]
    if not report.git_available:
        for n in report.notes:
            lines.append(f"  note: {n}")
        return "\n".join(lines)

    any_flagged = any(s.flagged for s in report.signals)
    for s in report.signals:
        marker = "⚠ " if s.flagged else "  "
        lines.append(f"{marker}{s.name}: {s.message}")
    lines.append("")
    if any_flagged:
        lines.append(
            "One or more signals flagged. Consider whether you're refining the "
            "plan instead of shipping the code. Override thresholds per-project "
            "via --threshold-* flags if these defaults don't fit."
        )
    else:
        lines.append("No overplanning signals flagged.")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("project_dir", help="Project root directory")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument("--threshold-edits", type=int, default=DEFAULT_THRESHOLD_EDITS)
    p.add_argument("--threshold-rewrites", type=int, default=DEFAULT_THRESHOLD_REWRITES)
    p.add_argument("--threshold-growth", type=float, default=DEFAULT_THRESHOLD_GROWTH)
    p.add_argument("--threshold-stale-days", type=int, default=DEFAULT_THRESHOLD_STALE_DAYS)
    p.add_argument("--fresh-plan-days", type=int, default=DEFAULT_FRESH_PLAN_DAYS)
    p.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS)
    args = p.parse_args(argv)

    project_dir = Path(args.project_dir).resolve()

    thresholds = {
        "edits": args.threshold_edits,
        "rewrites": args.threshold_rewrites,
        "growth": args.threshold_growth,
        "stale_days": args.threshold_stale_days,
        "fresh_plan_days": args.fresh_plan_days,
        "window": args.window_days,
    }

    report = assess(project_dir, thresholds)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render_text(report))

    if not report.git_available:
        return 0
    return 1 if any(s.flagged for s in report.signals) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

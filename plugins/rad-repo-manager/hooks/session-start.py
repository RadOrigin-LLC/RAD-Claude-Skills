#!/usr/bin/env python3
"""
SessionStart hook — ambient doc-health one-liner.

Runs the two cheap scans (repo-scan.py mechanical signals + doc-freshness.py staleness)
and, only when something is off, emits a short status line into session context. Silent
when the repo is clean or doesn't use the doc model — zero noise on green.

Exit 0 always; a broken hook must never block a session.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def run_scan(script: str, root: str, *extra: str) -> dict | None:
    try:
        out = subprocess.run(
            [sys.executable, str(SCRIPTS / script), root, "--json", *extra],
            capture_output=True, text=True, timeout=20,
        )
        return json.loads(out.stdout) if out.returncode == 0 else None
    except Exception:
        return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    root = Path(payload.get("cwd") or ".")

    # Only speak in repos that use the doc model — AGENTS.md alone isn't enough
    # (it's a broad convention); require a core doc beside it.
    if not (root / "AGENTS.md").is_file() or not (
        (root / "docs" / "handoff.md").is_file() or (root / "docs" / "prd.md").is_file()
    ):
        return 0

    scan = run_scan("repo-scan.py", str(root), "--no-record")
    fresh = run_scan("doc-freshness.py", str(root))

    bits: list[str] = []
    if fresh and fresh.get("severity") in ("high", "medium", "low"):
        worst = next(
            (f["summary"] for sev in ("HIGH", "MEDIUM", "LOW")
             for f in fresh["findings"] if f["severity"] == sev),
            None,
        )
        if worst:
            bits.append(worst)
    if scan and scan.get("severity") in ("yellow", "red"):
        n = scan.get("loose_ends", 0)
        bits.append(f"{n} loose doc end{'s' if n != 1 else ''}")

    if not bits:
        return 0  # green — say nothing

    print(
        "[rad-repo-manager] Doc health: "
        + " | ".join(bits)
        + " — /rad-repo-manager:startup for a briefing, /rad-repo-manager:repo-align to clean up."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

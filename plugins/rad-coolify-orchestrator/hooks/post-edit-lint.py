#!/usr/bin/env python3
"""
PostToolUse hook — auto-lint Dockerfiles and compose files after Claude edits them.

Reads the PostToolUse payload from stdin, and if the edited file is a Dockerfile
or docker-compose file, runs the matching deterministic linter from scripts/
(--json) and surfaces CRITICAL/WARNING findings back to Claude as additional
context. SUGGESTION-level findings are skipped to keep the signal high.

Silent on non-Docker files, silent on clean files, silent on any internal error.
Never blocks: always exits 0.
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

MAX_FINDINGS = 8

COMPOSE_PATTERNS = ("docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml")


def pick_linter(file_path: str) -> str | None:
    name = Path(file_path).name
    if name.startswith("Dockerfile") or name.endswith(".Dockerfile"):
        return "lint-dockerfile.py"
    if any(fnmatch.fnmatch(name, pat) for pat in COMPOSE_PATTERNS):
        return "lint-compose.py"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path", "")
    if not file_path or not Path(file_path).is_file():
        return 0

    linter = pick_linter(file_path)
    if linter is None:
        return 0

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    script = Path(plugin_root) / "scripts" / linter
    if not script.is_file():
        return 0

    try:
        out = subprocess.run(
            [sys.executable, str(script), file_path, "--json"],
            capture_output=True, text=True, timeout=15,
        )
        report = json.loads(out.stdout)
    except Exception:
        return 0

    findings = []
    for rep in report.get("reports", []):
        for f in rep.get("findings", []):
            if f.get("severity") in ("CRITICAL", "WARNING"):
                findings.append(f)

    if not findings:
        return 0

    findings.sort(key=lambda f: 0 if f.get("severity") == "CRITICAL" else 1)
    shown = findings[:MAX_FINDINGS]
    lines = [
        f"[rad-coolify-orchestrator] {linter} found "
        f"{len(findings)} issue(s) in the file just edited ({Path(file_path).name}):"
    ]
    for f in shown:
        loc = f" L{f['line']}" if f.get("line") else ""
        lines.append(f"- {f.get('severity')}{loc} ({f.get('category')}): {f.get('message')}")
        if f.get("fix"):
            lines.append(f"  fix: {f['fix']}")
    if len(findings) > MAX_FINDINGS:
        lines.append(f"...and {len(findings) - MAX_FINDINGS} more. Run the coolify-reviewer agent for the full report.")
    lines.append("Address CRITICAL findings now if they were introduced by this edit; otherwise mention them to the user.")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n".join(lines),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())

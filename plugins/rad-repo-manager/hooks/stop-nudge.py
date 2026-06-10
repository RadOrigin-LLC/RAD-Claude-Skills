#!/usr/bin/env python3
"""
Stop hook — one quiet wrapup reminder per session, only when it's earned.

Fires at most once per session, and only when ALL of these hold:
  - the repo uses the doc model (AGENTS.md + docs/ exist)
  - the working tree is dirty beyond docs/handoff.md itself (real work in flight)
  - docs/handoff.md is NOT being kept fresh (no uncommitted handoff edit, and its
    last commit is over 2 hours old or it was never committed)

Never blocks, never repeats within a session (tracked in .rad/repo-manager-state.json,
the same best-effort state file repo-scan.py uses). Exit 0 always.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HANDOFF = "docs/handoff.md"
RECENT_COMMIT_HOURS = 2

NUDGE = (
    "[rad-repo-manager] Uncommitted work in the tree and docs/handoff.md hasn't been "
    "refreshed — when you're done for the session, /rad-repo-manager:wrapup leaves a "
    "clean resume point. (This reminder shows once per session.)"
)


def git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def already_nudged(root: Path, session_id: str) -> bool:
    state_file = root / ".rad" / "repo-manager-state.json"
    if not state_file.is_file():
        return False
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return False
    return state.get("stop_nudge_last_session") == session_id


def record_nudge(root: Path, session_id: str) -> None:
    state_file = root / ".rad" / "repo-manager-state.json"
    state: dict = {}
    if state_file.is_file():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    state["stop_nudge_last_session"] = session_id
    try:
        state_file.parent.mkdir(exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass  # best-effort; never fail the hook over state


def handoff_recently_committed(root: Path) -> bool:
    iso = git(root, "log", "-1", "--format=%cI", "--", HANDOFF)
    if not iso:
        return False
    try:
        committed = datetime.fromisoformat(iso)
    except ValueError:
        return False
    age = datetime.now(timezone.utc) - committed.astimezone(timezone.utc)
    return age.total_seconds() < RECENT_COMMIT_HOURS * 3600


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    root = Path(payload.get("cwd") or ".")
    session_id = str(payload.get("session_id") or "")

    # Same doc-model guard as the other hooks: AGENTS.md plus a core doc.
    if not (root / "AGENTS.md").is_file() or not (
        (root / "docs" / "handoff.md").is_file() or (root / "docs" / "prd.md").is_file()
    ):
        return 0
    if not session_id or already_nudged(root, session_id):
        return 0

    porcelain = git(root, "status", "--porcelain")
    if porcelain is None:
        return 0
    lines = [ln for ln in porcelain.splitlines() if ln.strip()]
    dirty_beyond_handoff = [ln for ln in lines if HANDOFF not in ln]
    handoff_dirty = len(dirty_beyond_handoff) != len(lines)

    if not dirty_beyond_handoff:
        return 0  # nothing real in flight
    if handoff_dirty or handoff_recently_committed(root):
        return 0  # handoff is being kept fresh

    record_nudge(root, session_id)
    print(NUDGE)
    return 0


if __name__ == "__main__":
    sys.exit(main())

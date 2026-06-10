#!/usr/bin/env python3
"""
PreCompact hook — preserve what the handoff needs through compaction.

Compaction is where wrapup's raw material dies: validation commands and their results,
what was actually changed, and the resume point live only in conversation context. This
hook injects preservation instructions so the compaction summary keeps the facts
docs/handoff.md is built from.

Only speaks in repos that use the doc model. Exit 0 always.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

INSTRUCTIONS = (
    "[rad-repo-manager] This repo keeps a resume snapshot in docs/handoff.md, "
    "rebuilt at /rad-repo-manager:wrapup from session evidence. Preserve verbatim "
    "through compaction: (1) every validation command run this session (tests, "
    "build, lint) and its actual result; (2) the list of files changed and why; "
    "(3) the current task and the single next action; (4) any gotchas discovered. "
    "These cannot be reconstructed after compaction."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    root = Path(payload.get("cwd") or ".")
    # Same doc-model guard as the other hooks: AGENTS.md plus a core doc.
    if not (root / "AGENTS.md").is_file() or not (
        (root / "docs" / "handoff.md").is_file() or (root / "docs" / "prd.md").is_file()
    ):
        return 0
    print(INSTRUCTIONS)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env bash
# rad-session PreCompact hook
#
# Fires just before Claude Code compacts the conversation context.
# Emits a systemMessage telling Claude to run /wrapup so session state
# (HANDOFF.md, session-log.md, CLAUDE.md) reflects the pre-compaction
# state before it's lost.
#
# The payload enumerates the specific capture targets so that even if
# post-compaction context is thin, Claude has a concrete checklist to
# reconstruct from. This is more robust on smaller models (Haiku) where
# latent reflection can't be relied on.
#
# Input (stdin JSON): standard hook payload — we ignore it; the action
# is always the same regardless of compaction trigger or matcher.
#
# Output (stdout JSON): a systemMessage shown to Claude in the
# post-compaction context. Exit 0 = non-blocking success.

set -euo pipefail

# Drain stdin so the hook runner doesn't block on pipe buffering.
cat >/dev/null 2>&1 || true

cat <<'JSON'
{
  "systemMessage": "⚠ rad-session PreCompact hook fired. Context compaction is imminent — pre-compaction state must be captured before it's lost.\n\nBEFORE doing any other work, run the /wrapup skill. When you run it, make sure the synthesis pass captures these targets explicitly (they are the most commonly lost categories after compaction):\n\n  1. DECISIONS made this session — architecture, tool choices, naming rules — with the WHY preserved.\n  2. FAILED APPROACHES — anything tried that didn't work. Use the canonical format: TRIED: X — FAILED BECAUSE: Y — CORRECT APPROACH: Z (omit the last field if unknown).\n  3. USER CORRECTIONS — any feedback that redirected your approach. These are high-value for future sessions.\n  4. MODIFIED FILES — paths with a one-line description of what changed.\n  5. OPEN WORK — tasks in flight, described as current state (not as instructions to the next session).\n  6. KEY INSIGHTS — non-obvious API quirks, environment gotchas, architectural constraints not already in CLAUDE.md.\n\nIf the conversation is already partially compacted and you can't see some of this, note that explicitly in HANDOFF.md's Last Session Summary: 'Context was compacted during this session — synthesis based on remaining visible turns only.' A partial handoff beats no handoff.\n\nAfter /wrapup completes, resume whatever the user was working on. The /startup skill will read the fresh HANDOFF.md at the start of the next session."
}
JSON

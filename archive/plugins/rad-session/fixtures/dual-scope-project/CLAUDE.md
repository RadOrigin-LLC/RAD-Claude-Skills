@AGENTS.md

## Claude-specific behavior

- Use `/plan` for ambiguous, multi-file, or architectural work.
- Use subagents for broad codebase investigation, log triage, and post-change review so the main session stays focused.
- If the session drifts after repeated corrections, stop, update `docs/status.md`, and restart with a fresh session.

## Compact Instructions

When using compact:
- preserve the current objective
- preserve non-goals and hard boundaries
- preserve acceptance criteria
- preserve the current list of changed files
- preserve latest validation commands and results
- preserve blockers, open questions, and next step
- drop superseded exploration paths and abandoned ideas

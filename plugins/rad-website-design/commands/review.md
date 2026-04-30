---
description: Run the web-design-reviewer agent over a path (or current dir) for a 2026 design review pass.
argument-hint: "[path]"
allowed-tools: Read, Glob, Grep, Bash, Agent
---

The user wants a web design review of `$ARGUMENTS` (defaults to current working directory if empty).

Invoke the `web-design-reviewer` agent on the target. The agent will:

1. Detect the stack (React/Astro/Tailwind/etc.)
2. Run three pure-stdlib Python validators in parallel
3. Execute static-analysis phases (layout, typography, motion, stack-specific)
4. Surface heuristic findings with rationale
5. List NEEDS-MANUAL follow-ups

Pass the target path to the agent. Surface its report verbatim — do not re-summarize, do not add a verdict, do not editorialize.

If the target is unclear, ask the user once for the path. Do not guess.

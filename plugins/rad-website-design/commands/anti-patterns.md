---
description: Surface the severity-tiered 2026 web design anti-pattern catalog, optionally scoped to a target path.
argument-hint: "[path or topic]"
allowed-tools: Read, Glob, Grep, Skill, Agent
---

The user wants the 2026 web design anti-pattern catalog (or wants to scan `$ARGUMENTS` for anti-patterns).

**Two modes:**

1. **No path / topic only:** Load the `web-design-anti-patterns` skill via the Skill tool and surface the relevant tier(s) for `$ARGUMENTS`. If `$ARGUMENTS` is empty, surface the full catalog (Tier 1 AVOID-AT-ALL-COSTS first, then Tier 2 SHOULD-AVOID).

2. **Path provided:** Invoke the `web-design-reviewer` agent on the path. The agent will scan source for anti-pattern matches and produce a severity-ranked report.

Heuristic to choose: if `$ARGUMENTS` looks like a file/dir path (contains `/`, `.tsx`, `.html`, `.css`, etc.) → Mode 2. Otherwise → Mode 1.

Always cite damage with the source data (FTC fines, conversion drops, INP fail rates) — don't soften it. The whole point of this command is to surface real consequences.

Never issue Pass/Fail. Tag findings `[STATIC]` / `[HEURISTIC]` / `[NEEDS-MANUAL]`.

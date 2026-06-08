---
name: startup
description: >
  This skill should be used when the user says "startup", "start session",
  "orient me", "where did we leave off", "catch me up", "what's the state",
  "session briefing", or "what was I working on". Fast, read-only session
  orientation — read the four active docs + git state and surface where you are,
  what's next, and whether the repo looks aligned. Recommends
  /rad-repo-manager:repo-init on a fresh repo and /rad-repo-manager:repo-align when
  docs look drifted. It does not scaffold, audit, clean, write, or change anything.
argument-hint: ""
user-invocable: true
allowed-tools: Read Glob Grep Bash
---

# Startup — orient, fast and read-only

Get oriented at the top of a session. **Read-only and lean** — read the active docs
and git state, surface where things stand, and point at the right next skill. This is
not onboarding (that's `/rad-repo-manager:repo-init`) and not an audit (that's
`/rad-repo-manager:repo-align`).

## What this skill does NOT do

- No scaffolding or onboarding — a fresh repo gets pointed at `repo-init`.
- No deep audit, contradiction/redundancy check, or doc filing — that's `repo-align`.
- No reading of `docs/archive/`.
- No cleanup, no writes of any kind, no commits.
- No product or implementation changes.

## Procedure

1. **Gather git evidence** (read-only), in one batch:
   ```bash
   git status --short
   git branch --show-current
   ```
2. **Glob** for `AGENTS.md` and the `docs/` core to see what exists. Decide the path:
   - **Fresh repo** — no `AGENTS.md` and no real `docs/prd.md`/`docs/plan.md`. Stop
     and recommend `/rad-repo-manager:repo-init`. Do **not** scaffold here.
   - **Established repo** — `AGENTS.md` exists. Orient (below).
3. **Read the active core** that exists, in one parallel batch: `AGENTS.md`,
   `docs/prd.md`, `docs/plan.md`, `docs/handoff.md`. Read nothing else by default —
   not reference docs, not `docs/design.md`, not `docs/archive/`.
4. **Note alignment** by glob only (no deep scan): does the repo match the active
   model (the four core docs declared in `AGENTS.md`), or are there loose `.md` files
   at the root / under `docs/`, missing core docs, off-model `status`/`roadmap` docs,
   or a stale handoff? If it looks drifted, recommend `/rad-repo-manager:repo-align` —
   don't fix anything here.
5. **Surface the briefing** (format below). Ground every line in what you actually
   read; if a doc is missing or stale, say so plainly rather than inventing.

## Output format

```text
Startup:
Branch:           <current branch>
Working tree:     <clean / dirty summary from git status>
Active docs:      <which of the 4 exist; name any missing>
Current focus:    <current milestone / active task from docs/plan.md, one line>
Resume point:     <next action from docs/handoff.md>
Stop conditions:  <from docs/plan.md, if declared>
Repo hygiene:     <looks aligned | looks drifted → recommend repo-align | fresh repo → recommend repo-init>
Notes:            <anything material, or "None">
```

## References

- `${CLAUDE_PLUGIN_ROOT}/references/doc-model.md` — the active core, the conditional
  tiers, and what "aligned" means

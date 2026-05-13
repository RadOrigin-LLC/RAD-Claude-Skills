---
name: status
description: >
  This skill should be used when the user says "plan status", "where am I in the plan",
  "what's next", "what tasks are left", "show plan progress", "which tasks are blocked",
  "next eligible task", "plan progress", "how far along", "what can I work on next",
  or wants a quick read on an in-flight implementation plan without re-running the full
  review skill.
argument-hint: "[path to tasks.md or plan file]"
user-invocable: true
allowed-tools: Read Glob Bash
---

# Status — Plan Progress Report

Read a tasks file (or `PLAN.md` / `implementation_plan.md` with inline tasks) and report what's done, what's blocked, and what's eligible to work on next. Calls `scripts/plan-lint.py --mode status` for a deterministic state report — no LLM judgment required.

## When to use

- Picking up an in-flight plan and you want to know where to start.
- Mid-execution sanity check ("am I actually making progress, or just churning?").
- After a session break — "remind me which task was next."
- Before invoking `/rad-planner:checkpoint` — quick check of what's actually done vs. just claimed done.

For a deeper quality audit, use `/rad-planner:review-plan` instead. This skill is the cheap read.

## Workflow

### 1. Locate the tasks file

If a path was provided, use it. Otherwise Glob in parallel for:
- `tasks.md`
- `PLAN.md` (RAD 3.0+ standard)
- `implementation_plan.md` (v2.x legacy)
- `plan.md`
- Any `.md` in `docs/plans/` or `plans/`

If multiple match, ask the user which one (or use the most recently modified).

### 2. Run the status validator

```bash
python3 ${plugin_root}/scripts/plan-lint.py --mode status <path> --json
```

Where `${plugin_root}` is the rad-planner plugin install directory. If `python3` isn't available, fall back to manual parsing — read the tasks file, count states by their `[STATE]` markers, and identify next-eligible by checking dependency arrays against task IDs whose state is `[DONE]` or `[VERIFIED]`.

### 3. Present the report

```markdown
# Plan Status — [filename]

**Progress:** [completed]/[total] tasks ([percent]%)
**State breakdown:** [PENDING: N, IN PROGRESS: N, BLOCKED: N, DONE: N, VERIFIED: N, DEFERRED: N]

## Next eligible (deps satisfied)
- [task ID]: [title] — complexity [N], priority [high/medium/low]

## Currently in progress
- [task ID]: [title]

## Blocked
- [task ID] ← waiting on [list of unmet deps]

## Recommendation
[One sentence: which task to pick up next, or "all remaining work is blocked — investigate why" if next_eligible is empty.]
```

### 4. Optional next-step offer

If next_eligible is non-empty, offer:
- "Want me to read the full task spec for [next-eligible-id] so you can start?"
- "Want me to run `/rad-planner:review-plan` for a deeper quality check?"

If next_eligible is empty AND there are blocked tasks AND no tasks are in-progress, that signals a stuck plan — surface this directly: "All remaining tasks are blocked and nothing is in progress. Either a task was completed but not marked [DONE]/[VERIFIED], or the dependency graph has an issue. Run `/rad-planner:review-plan` to diagnose."

## What this skill does NOT do

- Does not modify the tasks file (read-only).
- Does not re-validate the DAG or check for missing fields — use `/rad-planner:review-plan` for that.
- Does not estimate time-to-complete (no historical data; complexity scores are not durations).
- Does not detect that work *was actually done* if the user forgot to update task states. State accuracy depends on the user / executing agent marking tasks honestly.

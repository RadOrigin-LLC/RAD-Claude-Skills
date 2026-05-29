---
name: status
description: >
  This skill should be used when the user says "plan status", "where am I in the plan",
  "what's next", "what tasks are left", "show plan progress", "which acceptance criteria
  are left", "how far along", "what can I work on next",
  or wants a quick read on an in-flight plan without re-running the full review skill.
argument-hint: "[path to docs/planning/current.md]"
user-invocable: true
allowed-tools: Read Glob Bash
---

# Status — Plan Progress Report

Read the active plan (`docs/planning/current.md`) and report acceptance-criteria progress for the current milestone, what's left, and the recommended next step. Calls `scripts/plan-lint.py --mode status` for a deterministic progress read — no LLM judgment required.

## When to use

- Picking up an in-flight plan and you want to know where to start.
- Mid-execution sanity check ("am I actually making progress, or just churning?").
- After a session break — "remind me what's left in this milestone."
- Before invoking `/rad-planner:checkpoint` — quick check of what's actually done vs. just claimed done.

For a deeper quality audit (anti-patterns, risk assessment), use `/rad-planner:review-plan` instead. This skill is the cheap read.

## Workflow

### 1. Locate the plan

If a path was provided, use it. Otherwise the canonical plan is `docs/planning/current.md`. If it's missing, Glob in parallel for a legacy or non-canonical fallback (`PLAN.md`, `plan.md`, any `.md` in `docs/plans/` or `plans/`) and note that the project isn't on the canonical structure — recommend `/rad-planner:plan` to migrate.

### 2. Run the status validator

```bash
python3 ${plugin_root}/scripts/plan-lint.py --mode status <path> --json
```

Where `${plugin_root}` is the rad-planner plugin install directory. The script reports acceptance-criteria checkbox progress: `completed` and `total` counts, percent complete, and the `pending` (unchecked) criteria text. It does **not** return the text of completed criteria or the milestone name — read those from `current.md` directly (allowed-tools includes Read); the script's counts are authoritative. If `python3` isn't available, fall back to manual parsing — read the plan file and count `- [x]` vs `- [ ]` entries in the **Acceptance criteria** section.

### 3. Present the report

```markdown
# Plan Status — [milestone name from current.md]

**Acceptance criteria:** [completed]/[total] complete ([percent]%)

## Done
- [x] [criterion text]

## Remaining
- [ ] [criterion text]

## Next recommended step
[From current.md "Notes for the next session" — the most likely next action + first file to touch, verbatim where possible. If absent, say "current.md has no Notes for the next session — consider adding one at next /wrapup."]
```

If the **Acceptance criteria** section is missing or uses bullets instead of checkboxes, surface that directly: "current.md's acceptance criteria aren't in checkbox form, so progress can't be tracked — run `/rad-planner:plan --validate` and fix the plan-lint finding."

### 4. Optional next-step offer

If criteria remain, offer:
- "Want me to read the relevant section of `current.md` so you can start the next criterion?"
- "Want me to run `/rad-planner:review-plan` for a deeper quality check?"

If all acceptance criteria are `[x]` checked, the milestone has shipped — surface this directly: "All acceptance criteria are complete. Run `/rad-session:wrapup` to archive this milestone and `/rad-planner:plan --improve` to set up the next one."

## What this skill does NOT do

- Does not modify the plan (read-only).
- Does not re-validate required sections or check for vague language — use `/rad-planner:review-plan` (or `/rad-planner:plan --validate`) for that.
- Does not estimate time-to-complete (no historical data).
- Does not detect that work *was actually done* if the user forgot to check the acceptance-criteria boxes. Progress accuracy depends on the executing agent / user checking boxes honestly as criteria are met.

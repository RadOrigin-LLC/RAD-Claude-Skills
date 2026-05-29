---
name: checkpoint
description: >
  This skill should be used when the user says "checkpoint", "save progress",
  "document and clear", "dump context", "save state", "prepare to clear", "session
  handoff", "wrap up this session", "context is getting long", "I need to clear",
  "save my work", "handoff", "I need to switch tasks", "before I close",
  or when the conversation is approaching context limits and work needs to be
  preserved before clearing the session. Also trigger proactively when detecting
  signs of context degradation (repeated suggestions, vague responses, hallucinated
  file paths).
argument-hint: "[--plan path/to/current.md] [--phase current-phase-name] [--run-id <id>]"
user-invocable: true
allowed-tools: Read Glob Grep Write Bash
---

# Checkpoint — Document & Clear Context Management

Preserve the current session state so work can be resumed in a fresh session without loss. This implements the "Document & Clear" pattern, which mitigates context rot — the observed degradation of AI reasoning quality as context windows fill. The skill saves planner run state and reflects completed acceptance criteria in the plan; the user runs `/clear` and starts the new session themselves. Nothing here is automatic.

**`docs/status.md` is owned by rad-session `/wrapup`** per the single-writer rule (see `docs/cross-plugin-contracts.md`). `/checkpoint` does **not** write `docs/status.md`. If you want a full session-level handoff written from evidence, run `/rad-session:wrapup` either before or after `/checkpoint`. The two are complementary:

- `/checkpoint` saves **planner-skill run state** — the bookkeeping for resuming `/plan`, `/review-plan`, or `/evaluate-stack` mid-flight (`.planner/state/<run-id>.json`).
- `/rad-session:wrapup` saves **session state** — writes `docs/status.md` from evidence (git diff, test output, plan-task state), surfaces candidate ADRs, prunes the operating manual's Operational sections.

Checkpoint at milestone boundaries, after 2 consecutive failures, or when context degradation signs appear (vague responses, hallucinated paths, correction loops). See `references/context-management.md` for the full trigger matrix and the shared checkpoint schema.

For a quick read of *where you are* in an in-flight plan without writing a checkpoint, use `/rad-planner:status` instead.

## Cross-model note

This skill is model-agnostic. The git state capture and run-state file generation are deterministic; parallel Reads of the plan file plus `git status` / `git log` are independent and should be batched.

## Execution: parallel-first

Step 1's reads — `docs/planning/current.md`, `git status`, `git log --oneline -5`, `git rev-parse --abbrev-ref HEAD` — are all independent. Batch into a single parallel burst. Only serialize when Step 3's plan update requires the prior read's contents.

## Checkpoint Workflow

### Step 1: Assess Current State (parallel batch)

Read the active plan (`docs/planning/current.md` if it exists) and run git commands in parallel. Capture:
- What milestone are we in (from current.md "Current milestone")?
- Which acceptance criteria are met, in progress, or blocked?
- What files were modified in this session?
- Are there any uncommitted changes?
- Current branch, recent commits, ahead/behind vs. remote

### Step 2: Write Planner State File (if run-id is available)

If `--run-id <id>` is provided, or if a prior `plan` / `review-plan` / `evaluate-stack` run is in progress, write/update the planner state file at `.planner/state/<run-id>.json` per the shared schema in `references/context-management.md`. This lets the next session resume the specific skill that was in flight via `--resume <run-id>`.

The shared schema allows the `plan`, `review-plan`, and `evaluate-stack` skills to all use the same state file format — different `skill` values, same structure.

If no run-id is in flight, skip this step and proceed to Step 3.

### Step 3: Reflect Completed Acceptance Criteria

If `docs/planning/current.md` exists, update its **Acceptance criteria** checkboxes to match reality — mark criteria that are actually met as `- [x]`. This is execution state (which boxes are checked), not a structural rewrite; do not touch the milestone's Objective, Guardrails, or other rad-planner-owned structure. Leave criteria you can't confirm as `- [ ]`. The next `/rad-session:wrapup` reads these checkbox states as evidence.

### Step 4: Recommend Next Steps

Tell the user:

```
Checkpoint complete. Planner state saved to .planner/state/<run-id>.json[ and current.md acceptance criteria updated].

To continue in a fresh session:
1. (Recommended) Run /rad-session:wrapup first to write docs/status.md from evidence
2. Start a new Claude Code session (or run /clear)
3. Run /rad-session:startup — it reads docs/status.md + docs/planning/current.md and orients you
   OR if a run-id was saved: "/rad-planner:plan --resume <run-id>"
4. The fresh session will have a clean context window

If you skipped step 1 (no /wrapup), the next /startup will only have docs/planning/current.md
plus the planner state file and git history to work from — usually enough for plan-level
resumption but missing the evidence-based session reality that docs/status.md captures.

If you want to continue in this session instead, that's fine —
but be aware that context quality may degrade as the session gets longer.
```

## What Gets Preserved

| What | Where | Why |
|------|-------|-----|
| Active skill run state | `.planner/state/<run-id>.json` | Resume specific skill via `--resume` |
| Acceptance-criteria progress | `docs/planning/current.md` checkboxes | Track completion as evidence for /wrapup |
| Git state | Captured at checkpoint time, surfaced in output | Know what's committed vs. uncommitted at the moment of /checkpoint |

## What `/checkpoint` does NOT preserve

- **`docs/status.md`** — that's rad-session `/wrapup`'s job, written from evidence (single-writer rule).
- The full conversation history (that's the point — we're clearing it).
- Intermediate reasoning or exploration results (externalize important findings to `docs/decisions/` or `docs/planning/current.md`).
- Temporary debugging context (capture only the solution, not the journey).

## Key Reference

Load `references/context-management.md` for the full Document & Clear protocol, trigger conditions, context budget rules, and the shared checkpoint schema used by `plan`, `review-plan`, and `evaluate-stack`.

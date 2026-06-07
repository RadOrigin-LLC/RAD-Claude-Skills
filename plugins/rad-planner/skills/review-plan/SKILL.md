---
name: review-plan
description: >
  This skill should be used when the user says "review my plan", "audit this plan",
  "check my implementation plan", "is this plan complete", "what's missing from my
  plan", "validate my plan", "plan review", "check plan quality", "risk review",
  "check dependencies", "are there any risks in my plan", or has an existing plan
  (`docs/plan.md`) that needs a quality audit before execution begins.
argument-hint: "[path to plan file]"
user-invocable: true
allowed-tools: Read Glob Grep Agent Write Bash
---

# Review Plan — implementation plan quality audit

Audit an existing `plan.md` in two layers:

1. **Mechanical** via `scripts/plan-lint.py` — required sections, per-task field
   presence, dependency resolution, no vague language. Deterministic; no LLM judgment.
2. **Judgment** via the `risk-assessor` agent — anti-pattern scanning, architecture
   concerns, rollback quality, checkpoint placement, TDD strategy.

This is the quality gate between planning and execution. It does not write durable docs
and does not modify the plan unless explicitly authorized (Step 5).

## Workflow

### 1. Locate the plan

If a path was provided, read it. Otherwise detect the plan in order:
`docs/plan.md`, `docs/planning/current-execution.md`,
`docs/planning/current.md`, root `PLAN.md`. Read it completely.

If none exists, report that there's no plan to review and recommend `/rad-planner:plan`.

### 2. Mechanical lint

```bash
python3 ${plugin_root}/scripts/plan-lint.py <plan-path> --json
```

Parse the JSON. It reports missing required sections, tasks missing any of the six
fields (Objective, Files, Depends on, Done when, Validate, Rollback), unresolved or
cyclic dependencies, and vague language. Exit 1 = issues, 0 = clean. These findings are
deterministic and **bypass the risk-assessor** — they feed straight into the report.

### 3. Delegate to risk-assessor

Use the Agent tool with the substituted template from
`references/subagent-prompts/risk-assessment.md`. Pass the plan content,
`iteration_number: 1`, `max_iterations: 1` (review-plan is a single pass; the iterative
loop belongs to `/rad-planner:plan`), and a note that the mechanical layer already ran —
focus judgment on what scripts can't check (anti-patterns, architecture, rollback
quality, checkpoint placement, TDD strategy).

If durable context docs exist and are relevant (e.g. a `docs/prd.md`,
`docs/architecture.md`, a decision log), read them read-only and pass them as supporting
context so the assessor judges the plan against stated product/architecture intent. Do
not require them — many projects won't have them.

Validate the agent's JSON:

```bash
echo "$AGENT_OUTPUT" | python3 ${plugin_root}/scripts/validate-json.py \
  ${plugin_root}/references/subagent-prompts/risk-assessment.schema.json - --extract-from-markdown
```

Re-prompt once on schema failure, then fall back to markdown parsing per
`agents/risk-assessor.md`. Key fields: `verdict` (`APPROVE` | `REVISE` | `RETHINK`),
`blocking_issues[]`, `advisory_issues[]`, `escalation_required`.

### 4. Present results

```markdown
# Plan Review Report

**Plan:** [path]
**Mechanical lint:** [PASS | N issues]
**Risk-assessor verdict:** APPROVE | REVISE | RETHINK
**Overall recommendation:** [actionable next step]

## Mechanical issues (from plan-lint.py)
- [deterministic — no judgment debate]

## Critical issues (block execution until fixed)
- [issue with specific fix]

## Improvements (recommended before execution)
- [issue with fix]

## Optional enhancements
- [nice-to-have]

## Escalation
[only when verdict=RETHINK — recommend /rad-brainstormer:design-sprint]
```

Apply production-grade standards by default: every task needs both Validate and
Rollback; auth/payment/data tasks need a security checkpoint; external integrations need
error handling in the task spec. Treat gaps in these as blocking.

### 5. Offer fixes (only when authorized)

If `verdict` is `REVISE`, offer to fix issues directly in the plan file. For each fix,
explain the change, show before/after, and modify **only** `plan.md` — never create
implementation files, never write durable docs. Mechanical issues (missing field, vague
phrase) usually have unambiguous fixes; offer to apply those directly.

If `verdict` is `RETHINK`, do not offer fixes — the architecture has fundamental issues
task-level edits won't resolve. Recommend `/rad-brainstormer:design-sprint`, then
re-review.

## What this skill does NOT do

- Does not modify the plan unless authorized in Step 5.
- Does not write durable docs (PRD, architecture, decision log) — if the review surfaces
  a durable change, name it in the report for the user to apply.
- Does not test that the plan works — that's the executor's job.
- Does not re-run the iterative risk loop — that belongs to `/rad-planner:plan`.

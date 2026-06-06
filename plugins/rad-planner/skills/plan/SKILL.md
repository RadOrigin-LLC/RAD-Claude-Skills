---
name: plan
description: >
  This skill should be used when the user says "plan my project", "create an
  implementation plan", "help me architect this", "I need a plan before coding",
  "let's plan before we build", "plan this feature", "break this down into
  tasks", "map out the work", "create a project plan", "plan this app", or wants
  a structured, risk-first implementation plan before writing any code. Also
  trigger proactively when a user describes a non-trivial project or feature and
  appears ready to start coding without a plan. Produces a single plan file
  (`docs/planning/plan.md`); does not write product, architecture, or decision
  docs — it surfaces those as a separate update-prompt for the user to apply.
argument-hint: "[project description or path to existing codebase]"
user-invocable: true
allowed-tools: Read Glob Grep WebSearch WebFetch Agent Write Bash
---

# Plan — risk-first implementation planning

Orchestrate a planning conversation that produces one thing: a plan a fresh agent
can execute. The method is **risk-first, adversarially-reviewed, and mechanically-
validated** — more rigorous than single-pass planning, without document sprawl.

**CRITICAL: This is PLANNING MODE. Do NOT write implementation code. Do NOT create
source files. Produce the plan only.**

**CRITICAL: The planner writes exactly two files, both under `docs/planning/`:**
- `plan.md` — always (the plan).
- `[date]-update-prompt.md` — only when the conversation surfaces a change that
  belongs in a durable doc the planner does not own (PRD / product contract,
  decision log, architecture).

**The planner never writes durable docs itself** (no `prd.md`, no decision log, no
architecture file, no operating manual, no status doc). When planning surfaces
durable content, it goes into the update-prompt with a pointer in `plan.md`, and
the user applies it. See "Surfacing" below.

## What this skill does — honestly

- Runs a six-phase conversation: Discovery → Stack → Build → Validate & Risk →
  Review → Export.
- Surfaces non-obvious assumptions, evaluates stack for codegen accuracy, decomposes
  goal-backward, sequences risk-first with size discipline, specs every task to
  execution-readiness, then mechanically validates and adversarially reviews the plan.
- Dispatches two subagents — `stack-advisor` and `risk-assessor` — with JSON output
  contracts validated by `scripts/validate-json.py`.
- Runs `scripts/plan-lint.py` against `plan.md`: required sections, per-task field
  presence, dependency resolution, no vague language. **Real validation, not a model
  self-check.**

## What this skill does NOT do

- Does not execute the plan.
- Does not write product, architecture, decision, status, or operating-manual docs —
  those surface into the update-prompt for the user to apply.
- Does not write outside `docs/planning/`.
- Does not detect every anti-pattern; mechanical checks cover field presence,
  dependency integrity, and vague language. `risk-assessor` handles judgment calls.

## Phase 1: Discovery

Understand the project before planning anything.

**Pre-discovery scope check.** If the project idea is still fuzzy — the user is
debating *what* to build or whether the problem is the right one — stop and recommend
`/rad-brainstormer:brainstorm-session` or `/rad-brainstormer:design-sprint`. Planning
assumes the *what* is decided; it plans the *how* and *order*.

**Detect greenfield vs. existing codebase.** Glob the working directory.

- **Existing codebase:** issue a parallel batch of Reads — `CLAUDE.md` / `AGENTS.md`,
  `README.md`, `package.json` (or language-equivalent manifest), top-level config —
  plus a Glob of the directory structure. Identify stack, conventions, integration
  points, and existing test infrastructure. Plan anchored to what's actually there.
- **Greenfield:** no repo to read; plan from the description.

**Ask 3–5 high-information strategic questions** (not implementation details). Examples:
- "What's the most important thing this system must get right?"
- "What's the biggest technical risk you see?"
- "Who are the users and what's their primary workflow?"
- "What existing systems must this integrate with?"
- "What are the hard constraints — timeline, team, infrastructure?"

**Capture assumptions.** Ask explicitly: *"What's true about this project's reality
that wouldn't be obvious from the code? For example: 'no users yet so we can break
compat freely', 'single-tenant only', 'team has no Rust experience', 'the DB can be
rebuilt anytime this month'."* Capture at least three. These land in `plan.md`'s
**Key assumptions** section.

Wait for answers before proceeding.

## Phase 2: Stack Evaluation

Evaluate the technology stack **when a stack decision is in play** — a new project, or
existing work adopting new frameworks/services. If the project has a settled stack and
the work introduces nothing new, note that and skip to Phase 3.

Delegate to the `stack-advisor` agent using `references/subagent-prompts/stack-eval.md`.
Pass `mode` (`new_project` | `evaluate_existing` | `compare_frameworks`) and project
context. The agent evaluates against the AI-native Golden Path matrix
(`references/golden-path-matrix.md`) — stack chosen for how accurately an LLM can
implement it, not just general fit.

Validate the returned JSON before consuming:

```bash
echo "$AGENT_OUTPUT" | python3 ${plugin_root}/scripts/validate-json.py \
  ${plugin_root}/references/subagent-prompts/stack-eval.schema.json - --extract-from-markdown
```

Re-prompt once on schema failure, then fall back to markdown parsing. Read the result:
- `confidence: high|medium` → present the recommendation.
- `confidence: low` → surface the risks before proceeding.
- `escalation_required: true` → stop; recommend rethinking scope via the brainstormer.

A stack choice is durable. Record a brief summary in `plan.md`'s **Stack** section; if
the rationale is worth keeping, **surface it** into the update-prompt (Phase 6).

## Phase 3: Build the Plan

Load `references/plan-template.md` for the output structure, in a parallel batch with
`references/failure-state-template.md`, `references/tdd-constraints.md`,
`references/context-management.md`, and `references/anti-patterns.md`.

**Decompose goal-backward.** Work back from the goal: what must be TRUE, what must
EXIST, what is CRITICAL vs. nice-to-have, what is explicitly a non-goal. Critical items
become milestones; non-goals land in `plan.md`'s **Scope**.

**Sequence risk-first, with size discipline.**
- The hardest unknown is solved first — a spike or decision milestone — before
  committing effort to dependent work.
- Aim for **2–3 tasks per milestone**. A milestone over 5 tasks is a split candidate
  (warn, don't force — respect user agency).
- Map dependencies explicitly; note what can parallelize.

**Spec every task to execution-readiness.** Each task carries all six fields:
Objective, Files, Depends on, Done when, Validate, Rollback. Apply the failure-state
triple (Action / Validation / Rollback) and insert a checkpoint after every milestone.
Note where to checkpoint-and-clear context per `references/context-management.md`.

**Write the draft.** Compose the plan into `docs/planning/plan.md` with
`**Status:** DRAFT`, following `references/plan-template.md`. (Path resolution and
existing-plan detection: see "Plan location" below.)

## Phase 4: Validate & Risk

**Mechanical validation first** — run on the draft:

```bash
python3 ${plugin_root}/scripts/plan-lint.py docs/planning/plan.md --json
```

It flags missing sections, tasks missing any of the six fields, unresolved or cyclic
dependencies, and vague language. **Fix every CRITICAL or HIGH issue before risk
assessment** — `risk-assessor` should spend its judgment on what scripts can't check.

**Then adversarial review.** Delegate to the `risk-assessor` agent using
`references/subagent-prompts/risk-assessment.md`. It checks against the documented
anti-patterns (`references/anti-patterns.md`), architecture concerns, rollback quality,
and checkpoint placement. Validate its JSON (`validate-json.py` against
`risk-assessment.schema.json`), re-prompt once on failure, then fall back to markdown.

Read the verdict:
- `APPROVE` → proceed to Phase 5.
- `REVISE` (iteration < 3) → fix `blocking_issues`, re-lint, re-dispatch.
- `REVISE` (iteration ≥ 3, issues remain) → stop looping; surface unresolved issues and
  ask the user to accept as known gaps, restructure, or re-enter via the brainstormer.
- `RETHINK` → stop immediately. The architecture has fundamental issues task-level
  edits won't fix. Recommend `/rad-brainstormer:design-sprint`.

## Phase 5: Review & Approval

Present: the plan summary (milestones, task count, risk level, plan-lint result), the
full task list, the risk report, and the assumptions captured. The draft `plan.md` is
readable on disk during review.

**Ask explicitly: "Does this plan look right? Anything to adjust before I lock it in?"**
The plan is not approved until the user says so. Incorporate feedback and re-lint if
tasks change.

## Phase 6: Export

On approval:

1. Flip `plan.md`'s `**Status:** DRAFT` to `APPROVED` and stamp `**Updated:**`.
2. **Surfacing** — if Discovery, Stack, or Risk turned up anything durable (a
   product-behavior change, a decision worth recording, an architecture implication),
   write `docs/planning/[date]-update-prompt.md` per the update-prompt template in
   `references/plan-template.md`, and add the `**Pending durable-doc updates:**`
   pointer line to `plan.md`. If nothing durable surfaced, write no second file.
3. Run `plan-lint.py` once more on the final `plan.md`; report clean or surface
   remaining issues for the user to accept or fix.

## Surfacing

The planner owns `plan.md` and nothing else. When the conversation produces content
that belongs in a durable doc — the PRD / product contract (current product behavior),
the decision log (an active decision), the architecture reference (a structural
implication) — it does **not** write that doc. It records the needed change in the
update-prompt as a plain-language, paste-ready instruction naming the target file, and
points `plan.md` at it. The user (or a coding agent they run) applies it. This keeps
the planner strictly a planner and the durable docs under the user's control.

## Plan location

Default: `docs/planning/plan.md`. Before creating, detect an existing plan to update in
place rather than spawning a competitor — check, in order: `docs/planning/plan.md`,
`docs/planning/current-execution.md`, `docs/planning/current.md`, root `PLAN.md`. If one
exists, update it (preserving the user's structure where it diverges). Greenfield →
create `docs/planning/plan.md`. Never write outside `docs/planning/`.

## Execution: parallel-first

Batch independent reads — Phase 1 codebase exploration and Phase 3 reference loading
each have no inter-file dependencies. Serialize only user-approval gates and the phase
order itself.

## Key references

- `references/plan-template.md` — `plan.md` + update-prompt structure, enforced rules
- `references/failure-state-template.md` — Action / Validation / Rollback triples
- `references/tdd-constraints.md` — per-task test strategy
- `references/context-management.md` — checkpoint-and-clear protocol
- `references/anti-patterns.md` — documented planning anti-patterns (risk-assessor)
- `references/golden-path-matrix.md` — AI-native stack evaluation criteria
- `references/subagent-prompts/stack-eval.md` — `stack-advisor` dispatch template
- `references/subagent-prompts/risk-assessment.md` — `risk-assessor` dispatch template
- `scripts/plan-lint.py` — mechanical `plan.md` validator
- `scripts/validate-json.py` — subagent JSON-contract validator
- `examples/plan.md` — a real, lint-clean plan

---
name: plan
description: >
  This skill should be used when the user says "plan my project", "create an
  implementation plan", "help me architect this", "I need a plan before coding",
  "let's plan before we build", "plan this feature", "break this down into
  tasks", "map out the work", "create a project plan", "plan this app", or wants
  a structured, risk-first implementation plan before writing any code. Also
  trigger proactively when a user describes a non-trivial project or feature and
  appears ready to start coding without a plan. Runs a structured discovery
  interview, builds a release map (MVP/Beta now, V1 next, end goal later), and
  produces a single plan file (`docs/plan.md`). Can draft `docs/prd.md` from the
  interview answers with per-section confirmation when none exists; other durable
  docs surface as an update-prompt for the user to apply.
argument-hint: "[project description or path to existing codebase]"
user-invocable: true
allowed-tools: Read Glob Grep WebSearch WebFetch Agent Write Bash AskUserQuestion
---

# Plan — risk-first implementation planning

Orchestrate a planning conversation that produces one thing: a plan a fresh agent can
execute *and a moderately experienced non-developer can read*. The method is
**interview-driven, risk-first, adversarially-reviewed, and mechanically-validated**
— more rigorous than single-pass planning, without document sprawl.

**CRITICAL: This is PLANNING MODE. Do NOT write implementation code. Do NOT create
source files. Produce the plan only.**

**CRITICAL: The planner writes at most three files, all under `docs/`:**
- `plan.md` — always (the plan).
- `prd.md` — **only** when it's missing or skeletal, **only** drafted from the user's
  own interview answers, and **only** with per-section confirmation (Phase 1's PRD
  gap check). Never edited when a real PRD already exists — changes to an existing
  PRD go in the update-prompt.
- `[date]-update-prompt.md` — only when the conversation surfaces a change that
  belongs in a durable doc the planner does not own (an existing PRD, decision log,
  architecture).

## What this skill does — honestly

- Runs a six-phase conversation: Discovery (structured interview) → Stack → Build →
  Validate & Risk → Review → Export.
- Grills before planning: drives the eight coverage areas in
  `references/discovery-interview.md` to settled-or-explicitly-unknown, mirrors the
  project back for correction, and proposes assumptions for confirm/deny.
- Anchors every plan to the user's end goal via a release map — **Now** (MVP/Beta,
  fully specced), **Next** (V1 outline), **Later** (end goal themes). Detail decays
  with distance by design.
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
- Does not edit an existing real PRD, and does not write architecture, decision,
  status, or operating-manual docs — those surface into the update-prompt.
- Does not write outside `docs/`.
- Does not spec future versions in task detail — "Next" and "Later" stay coarse until
  `/rad-planner:replan` pulls them in.
- Does not detect every anti-pattern; mechanical checks cover field presence,
  dependency integrity, and vague language. `risk-assessor` handles judgment calls.

## Phase 1: Discovery — the interview

Understand the project before planning anything. Full protocol:
`references/discovery-interview.md` — load it first.

**Pre-discovery scope check.** If the project idea is still fuzzy — the user is
debating *what* to build or whether the problem is the right one — stop and recommend
`/rad-brainstormer:brainstorm-session` or `/rad-brainstormer:design-sprint`. Planning
assumes the *what* is decided; it plans the *how* and *order*. (A messy existing
project with unclear state is different — that's `/rad-planner:rescue`.)

**Pre-fill from evidence.** Glob the working directory.

- **Existing codebase:** issue one parallel batch of Reads — `docs/prd.md`,
  `docs/handoff.md`, any existing `docs/plan.md`, `CLAUDE.md` / `AGENTS.md`,
  `README.md`, the manifest (`package.json` or language equivalent), top-level config
  — plus a Glob of the directory structure. The PRD is product authority: plan
  *against* it, and surface any contradiction as a question, never a silent override.
  Never ask what the repo already answers — confirm instead.
- **Greenfield:** no repo to read; the interview carries everything.

**Run the interview** per the protocol: round 1 questions across the eight coverage
areas (end goal, users & workflow, MVP, success criteria, constraints, assets,
exclusions, danger zones) → mirror the project back for correction → follow-up rounds
on unsettled areas only, capped at 3 → propose 3–6 assumptions for confirm/deny.
Plain language throughout; AskUserQuestion for choice-shaped questions.

**Close with the two gates** (both in `references/discovery-interview.md`):

1. **Speed fork** — ask: quick plan (skip Phase 2, single risk pass in Phase 4) or
   full plan? The user chooses; recommend full for greenfield, quick for a feature in
   an established codebase.
2. **PRD gap check** — if `docs/prd.md` is missing or skeletal, offer to draft it
   from the interview answers, confirming each section (apply / reword / skip) before
   writing. The PRD content is the user's answers reorganized — never invented. After
   writing, stamp its `**Updated:**` date. If the user declines, note the gap in Key
   assumptions and continue.

## Phase 2: Stack Evaluation

*(Skipped on the quick path, or when the stack is settled and the work introduces
nothing new — note that and move on.)*

Evaluate the technology stack **when a stack decision is in play** — a new project, or
existing work adopting new frameworks/services.

Delegate to the `stack-advisor` agent using `references/subagent-prompts/stack-eval.md`.
Pass `mode` (`new_project` | `evaluate_existing` | `compare_frameworks`) and project
context. The agent evaluates against the AI-native Golden Path matrix
(`references/golden-path-matrix.md`) — stack chosen for how accurately an LLM can
implement it, not just general fit.

Validate the returned JSON before consuming (use `python3`, or `python` on Windows):

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

**Build the release map first.** Three horizons, anchored to the interview:
- **Now** — the MVP/Beta the user defined. This is what the plan's milestones and
  tasks cover, in full six-field detail.
- **Next** — V1: a milestone-level outline (3–6 bullets), no task specs.
- **Later** — the end goal: theme bullets.
Detail decays with distance **by design** — speccing distant versions in task detail
is fake precision. Pulling "Next" into detail is a `/rad-planner:replan` event.

**Decompose goal-backward** *within the Now horizon*: what must be TRUE, what must
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

**Write for both readers.** The task fields serve the coding agent — keep them
precise. The human layer serves the vibe coder: the "How to read this plan" note, the
release map, and an *After this ships:* line under each milestone heading saying in
plain English what the user can do once it lands. Both are in the template.

**Write the draft.** Compose the plan into `docs/plan.md` with
`**Status:** DRAFT`, following `references/plan-template.md`. (Path resolution and
existing-plan detection: see "Plan location" below.)

## Phase 4: Validate & Risk

**Mechanical validation first** — run on the draft (use `python3`, or `python` on
Windows):

```bash
python3 ${plugin_root}/scripts/plan-lint.py docs/plan.md --json
```

It flags missing sections (including the release map), tasks missing any of the six
fields, unresolved or cyclic dependencies, and vague language. **Fix every CRITICAL or
HIGH issue before risk assessment** — `risk-assessor` should spend its judgment on
what scripts can't check.

**Then adversarial review.** Delegate to the `risk-assessor` agent using
`references/subagent-prompts/risk-assessment.md`. It checks against the documented
anti-patterns (`references/anti-patterns.md`), architecture concerns, rollback quality,
and checkpoint placement. Validate its JSON (`validate-json.py` against
`risk-assessment.schema.json`), re-prompt once on failure, then fall back to markdown.

On the **quick path**: a single risk pass (`max_iterations: 1`) — fix blocking issues
once, present anything unresolved to the user, no loop.

On the **full path**, read the verdict:
- `APPROVE` → proceed to Phase 5.
- `REVISE` (iteration < 3) → fix `blocking_issues`, re-lint, re-dispatch.
- `REVISE` (iteration ≥ 3, issues remain) → stop looping; surface unresolved issues and
  ask the user to accept as known gaps, restructure, or re-enter via the brainstormer.
- `RETHINK` → stop immediately. The architecture has fundamental issues task-level
  edits won't fix. Recommend `/rad-brainstormer:design-sprint`.

## Phase 5: Review & Approval — for a human, not an engineer

Present, in this order:

1. **The plain-English summary** — 4–6 sentences: what's being built, what the MVP
   delivers, what comes after, and the one biggest risk.
2. **The release map** — Now / Next / Later, verbatim.
3. **The decisions baked into this plan** — 3–5 bullets naming each judgment call the
   plan embeds (stack choice, ordering choice, deliberate exclusion, risk mitigation)
   so the user signs off on *decisions*, not a wall of tasks.
4. The milestone list with the *After this ships* lines, then the full task detail,
   risk report, and plan-lint result — available, after the parts a human reviews.

**Ask explicitly: "Does this match what you're trying to build? Anything to adjust
before I lock it in?"** The plan is not approved until the user says so. Incorporate
feedback and re-lint if tasks change.

## Phase 6: Export

On approval:

1. Flip `plan.md`'s `**Status:** DRAFT` to `APPROVED` and stamp `**Updated:**`.
2. **Surfacing** — if Discovery, Stack, or Risk turned up anything durable that the
   planner doesn't own (a change to an *existing* PRD, a decision worth recording, an
   architecture implication), write `docs/[date]-update-prompt.md` per the
   update-prompt template in `references/plan-template.md`, and add the
   `**Pending durable-doc updates:**` pointer line to `plan.md`. If nothing durable
   surfaced, write no second file.
3. Run `plan-lint.py` once more on the final `plan.md`; report clean or surface
   remaining issues for the user to accept or fix.

## Surfacing

The planner owns `plan.md`, and may *birth* `docs/prd.md` from the interview (Phase 1,
per-section confirmation) when none exists. Everything else durable — changes to an
existing PRD, the decision log, the architecture reference — it does **not** write.
It records the needed change in the update-prompt as a plain-language, paste-ready
instruction naming the target file, and points `plan.md` at it. The user (or a coding
agent they run) applies it. After birth, the PRD is maintained by the user and
rad-repo-manager's wrapup — the planner doesn't touch it again outside the
update-prompt.

## Plan location

Default: `docs/plan.md`. Before creating, detect an existing plan — check, in order:
`docs/plan.md`, `docs/planning/current-execution.md`, `docs/planning/current.md`, root
`PLAN.md`. **If a real plan exists and work has happened since it was written, that's
a re-plan, not a fresh plan — hand off to `/rad-planner:replan`**, which marks shipped
work from git evidence before restructuring. Only update in place when the existing
plan is a stub or no execution has started. Greenfield → create `docs/plan.md`. Never
write outside `docs/`.

## Execution: parallel-first

Batch independent reads — Phase 1 codebase exploration and Phase 3 reference loading
each have no inter-file dependencies. Serialize only user-approval gates and the phase
order itself.

## Key references

- `references/discovery-interview.md` — the interview protocol: coverage areas, mirror, rounds, both closing gates
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

---
name: plan
description: >
  This skill should be used when the user says "plan my project", "create an implementation
  plan", "plan-project" (legacy 2.x trigger), "plan this app", "I need a plan before coding",
  "help me architect this", "let's plan before we build", "create a project plan",
  "implementation plan", "plan this feature", "map out the work", "break this down into
  tasks", "create a roadmap", "project breakdown", "reboot my plan", "regenerate the plan
  after a pivot", "validate my plan files", "gap-check my plan docs", or wants to create
  a structured, dependency-aware implementation plan before writing any code. Also trigger
  proactively when a user describes a non-trivial project idea and appears ready to start
  coding without a plan.
argument-hint: "[project description or existing codebase path] [--lite] [--reboot] [--validate] [--non-interactive] [--resume <run-id>] [--output-dir <path>]"
user-invocable: true
allowed-tools: Read Glob Grep WebSearch WebFetch Agent Write Bash
---

# Plan — Structured Implementation Planning

You are orchestrating a project planning workflow. The goal is a set of planning artifacts a fresh AI session can pick up and execute without the original conversation context. Whether the plan actually achieves that depends on the quality of the planning session — this skill provides scaffolding and mechanical checks, not guarantees.

**CRITICAL: You are in PLANNING MODE. Do NOT write implementation code. Do NOT create source files. Produce planning artifacts ONLY.**

## What this skill does — honestly

- Walks you through a 6-phase workflow (Discovery → Stack → Plan → Risk → Review → Export). `--reboot` adds a Phase 0.5 repo audit; `--validate` runs a cheap gap-check without the full workflow.
- Dispatches subagents for stack evaluation and risk assessment with JSON output contracts.
- Runs `scripts/plan-lint.py` to mechanically check the generated `tasks.md` for cycles, phantom dependencies, missing required fields, vague validation language, and complexity-7+ tasks without subtasks. **This is real validation, not a model self-check.**
- Runs `scripts/validate-json.py` against the subagent JSON contracts before consuming them; re-prompts the agent once on schema failure.
- Saves run state to `.planner/state/<run-id>.json` so a long planning session can be resumed.
- Emits the **RAD 8-doc standard** (see `references/file-conventions.md` → canonical at `docs/file-conventions.md`): PRD, ARCHITECTURE, ASSUMPTIONS, DECISIONS, PLAN, plus `tasks.md` and `CLAUDE-FRAGMENT.md` (the `@-import` block consumed by rad-session `/init`).

## What this skill does NOT do

- Does not execute the resulting plan.
- Does not write CLAUDE.md, HANDOFF.md, or `.claude/session-log.md` — those belong to rad-session per the single-writer rule.
- Does not test that the plan is actually "zero-context ready" — that label is the goal of the templates, not a verified property.
- Does not detect every anti-pattern; the mechanical checks cover field presence, DAG integrity, and vague language. The risk-assessor agent handles judgment-required anti-patterns and architectural concerns.
- Does not stop you skipping phases. The phase order is enforced by instructions to the model, not by code.

## Cross-model note

This skill works across Opus 4.7, Sonnet 4.6, and Haiku 4.5. Opus/Sonnet handle parallel batching reliably; Haiku may follow phase order sequentially. The plan output, JSON contracts, and validator scripts are identical regardless of model.

## Execution: parallel-first

- **Phase 0.5 repo audit (`--reboot` only)** issues parallel Reads for existing strategic docs (`PRD.md`, `ARCHITECTURE.md`, `ASSUMPTIONS.md`, `DECISIONS.md`, `PLAN.md`, `tasks.md`) and any v2.x legacy file (`implementation_plan.md`, `docs/ARCHITECTURE.md`). No inter-file dependencies — one parallel burst.
- **Phase 1 codebase exploration** has no inter-file dependencies when the project exists. Issue parallel Reads for `CLAUDE.md`, `README.md`, `package.json`, `tsconfig.json` (or language-equivalent config), plus a Glob of the top-level directory structure.
- **Phase 3 reference loading** (`plan-template.md`, `task-format.md`, `anti-patterns.md`, `failure-state-template.md`, `tdd-constraints.md`, `context-management.md`) has no inter-file dependencies — single parallel batch.
- **Phase 2 and Phase 4 subagent dispatches** are independent of each other only when Phase 2 is complete before Phase 3 begins.
- **Always serialize:** user-approval gates and the discovery → stack → plan → risk → review phase order.

## Mode Flags

- `--lite` — Skip Phase 2 (stack eval) and the iterative risk-assessor loop. For small, single-milestone work (bug fixes, single-feature additions touching ≤3 files). Produces a 5-10 task plan with the same per-task fields, but no architecture diagram or full risk audit. Auto-detected if the project description is short and clearly bounded; explicit flag overrides.
- `--reboot` — Project has existed before (with or without rad-planner 3.x docs); regenerate the strategic docs anchored to current code reality. Adds Phase 0.5 (repo audit + archive originals to `*.pre-reboot`). DECISIONS.md is appended-to, not overwritten, with prior entries marked superseded. See **Reboot Mode Workflow** below.
- `--validate` — Cheap gap-check: does the 8-doc set exist? Does `tasks.md` lint clean? No agents dispatched, no writes. See **Validate Mode Workflow** below. For a deeper quality audit, use `/rad-planner:review-plan` instead.
- `--non-interactive` — Skip all user-approval gates. Best-effort plan, commit artifacts, emit a trailing JSON block listing `awaiting_user_review` items. Auto-proceed thresholds: stack-advisor `verification_verified: true` with `confidence: high|medium` → proceed; risk-assessor `verdict: APPROVE` → proceed; any `RETHINK` verdict → halt regardless of mode and escalate.
- `--resume <run-id>` — Load checkpoint state from `.planner/state/<run-id>.json` and continue from the last saved phase.
- `--output-dir <path>` — Write the five strategic/operational docs plus `tasks.md` and `CLAUDE-FRAGMENT.md` under `<path>` instead of project root. FRAGMENT `@-import` paths are adjusted accordingly. Default is project root, matching the RAD 8-doc convention.

## Checkpoint & Resume

Long planning runs are compaction-prone. Save state to `.planner/state/<run-id>.json` at these transitions:

0.5. After Phase 0.5 (`--reboot` only — audit complete, originals archived)
1. After Phase 1 (discovery complete, codebase explored if applicable)
2. After Phase 2 (stack recommendation received and accepted)
3. End of Phase 3 (plan DAG drafted)
4. After each Phase 4 risk-assessor iteration
5. After Phase 5 (user approval)
6. After Phase 6 (artifacts written)

Checkpoint schema (shared with `review-plan` and `evaluate-stack`):
```json
{
  "run_id": "string",
  "skill": "plan | review-plan | evaluate-stack",
  "phase": "0.5 | 1 | 2 | 3 | 4-iter-N | 5 | 6",
  "mode": "full | lite | reboot | validate",
  "started_at": "ISO-8601",
  "last_saved": "ISO-8601",
  "model": "opus | sonnet | haiku",
  "project_summary": "string",
  "codebase_context": {
    "root": "string",
    "claude_md_present": false,
    "stack_detected": ["string"],
    "existing_strategic_docs": ["PRD.md", "ARCHITECTURE.md"]
  },
  "stack_recommendation": "JSON from stack-advisor or null",
  "plan_path": "string or null",
  "tasks_path": "string or null",
  "risk_history": [{"iteration": 1, "verdict": "REVISE", "issue_count": 0}],
  "escalation": {"required": false, "reason": "", "route_to": ""},
  "awaiting_user_review": ["string"]
}
```

The model has to remember to write the checkpoint at each transition — there is no hook that does it automatically. On `--resume <run-id>`, load the file, announce the phase you're resuming from, and continue.

## Workflow

### Phase 0.5: Repo Audit (`--reboot` only)

When `--reboot` is passed, the project has already lived. The goal of Phase 0.5 is to anchor the regenerated plan to **current code reality**, not the original PRD's aspirations.

1. **Parallel-Read existing strategic docs.** Look for `PRD.md`, `ARCHITECTURE.md`, `ASSUMPTIONS.md`, `DECISIONS.md`, `PLAN.md`, `tasks.md` at project root. Also look for v2.x legacy paths: `implementation_plan.md`, `docs/ARCHITECTURE.md`. Report which exist.
2. **Audit the codebase against the prior PRD.** Glob the source tree. Identify:
   - Major divergences between prior PRD scope and what's been built
   - Components that exist in code but aren't in ARCHITECTURE.md
   - Components in ARCHITECTURE.md that were never built
   - Stack drift (package.json deps vs. what was originally chosen)
3. **Archive originals.** For each existing strategic doc, rename `<name>.md` → `<name>.md.pre-reboot`. Append a header line on each archive: `> Archived YYYY-MM-DD by /plan --reboot. Superseded by regenerated <name>.md.`
4. **Read DECISIONS.md** (now `.pre-reboot`). Parse the sequence-numbered entries. The reboot will append new entries; prior entries will be marked superseded individually based on Phase 1–5 outcomes.
5. **Surface the audit findings to the user** (skip detailed report in `--non-interactive`):
   - What we found in code vs. docs
   - What's about to be archived
   - What the planning session should focus on
6. Save Phase 0.5 checkpoint with `mode: reboot` and the `existing_strategic_docs` array.

Phase 1 then proceeds anchored to **detected current state** rather than greenfield assumptions.

### Phase 1: Strategic Discovery

**Pre-discovery scope check.** If the user's project idea is clearly fuzzy (still debating what to build, which approach, or whether the problem is the right one), recommend `/rad-brainstormer:brainstorm-session` or `/rad-brainstormer:design-sprint` and return here once the direction is locked. `plan` plans the *how/order*; it assumes the *what* is decided.

**Lite-mode auto-detect.** If the project description fits all of:
- Single feature or bug fix, ≤3 files affected
- No new dependencies / framework choices
- One milestone of work, estimated <1 day

…suggest `--lite` mode unless the user explicitly wants the full workflow.

**If the user provided a project description (or `--reboot` Phase 0.5 produced an audit):**
1. Summarize your understanding. In `--reboot`, summarize against the audit findings, not the prior PRD.
2. Ask 3-5 high-information strategic questions (NOT implementation details):
   - "What's the most important thing this system must get right?"
   - "What's the biggest technical risk you see?"
   - "Who are the target users and what's their primary workflow?"
   - "What existing systems does this need to integrate with?"
   - "What are the hard constraints? (timeline, team, infrastructure)"
3. **Assumption capture (new in 3.0, feeds ASSUMPTIONS.md):** Ask explicitly: *"What's true about this project's reality that wouldn't be obvious from the code? Examples: 'no users yet so we can break compat freely', 'single-tenant only', 'we can rebuild the DB anytime in the next 30 days', 'sensitive data — no real values ever live in the repo', 'team has no Rust experience'."* Capture at least 3 entries. In `--reboot`, also ask which prior assumptions have flipped.
4. Wait for answers (skip in `--non-interactive` — record unanswered questions in `awaiting_user_review`).

**If in an existing codebase (and not already done in Phase 0.5):**
1. Issue parallel Reads for `CLAUDE.md`, `README.md`, `package.json`, `tsconfig.json` (or language equivalents), plus a Glob of the top-level structure.
2. Identify patterns, conventions, integration points.
3. Present findings and ask clarifying questions (skip in `--non-interactive`).

Save Phase 1 checkpoint.

### Phase 2: Stack Evaluation (skip in `--lite`)

Use the Agent tool to delegate to the `stack-advisor` agent using the substituted template from `references/subagent-prompts/stack-eval.md`. Pass `mode` (`new_project` | `evaluate_existing` | `compare_frameworks`) and `project_context`.

**After receiving the agent's output, validate the JSON contract:**

```bash
# Pipe the agent's output through the schema validator
echo "$AGENT_OUTPUT" | python3 ${plugin_root}/scripts/validate-json.py \
  ${plugin_root}/references/subagent-prompts/stack-eval.schema.json - --extract-from-markdown
```

If validation fails, re-prompt the agent once with: "Your last output failed JSON Schema validation: [errors]. Re-emit the JSON block matching `references/subagent-prompts/stack-eval.schema.json`." If the second attempt also fails, fall back to markdown parsing per the legacy structure in `agents/stack-advisor.md`.

Parse the validated JSON per the schema:
- `evaluation_complete: true` + `confidence: high|medium` → present recommendation to user (or auto-proceed in `--non-interactive`)
- `confidence: low` → surface risks to user before proceeding
- `escalation_required: true` → stop. Surface `escalation_reason` and recommend rethinking scope via brainstormer

Save Phase 2 checkpoint. The stack rationale will become one of the initial DECISIONS.md entries in Phase 6.

### Phase 3: Build the Plan

Load references in a single parallel batch: `plan-template.md`, `task-format.md`, `anti-patterns.md`, `failure-state-template.md`, `tdd-constraints.md`, `context-management.md`.

1. **Define milestones** — logical phases of work (3-6 milestones typical; 1-2 in `--lite`).
2. **Break into tasks** — each milestone becomes 3-8 specific tasks (lite: 5-10 tasks total, no milestone hierarchy required).
3. **Map dependencies** — explicit `Dependencies: [S1, S2]` for every task.
4. **Score complexity** — 1-10 per task; expand any task > 7 into subtasks.
5. **Define validation** — every task gets a runnable validation check.
6. **Define rollbacks** — every task gets a revert procedure.
7. **Set test strategy** — per `references/tdd-constraints.md`.
8. **Insert checkpoints** — after every milestone, per `references/failure-state-template.md`.
9. **Plan context management** — identify where to checkpoint/clear sessions per `references/context-management.md`.

**Mechanical validation (this is the part that's actually enforced):**

```bash
python3 ${plugin_root}/scripts/plan-lint.py --mode all <path-to-tasks.md> --json
```

The script returns issues for: cycles, phantom dependencies, complexity > 7 without subtasks, missing required fields (Validation, Rollback, Dependencies, Complexity), and vague validation language ("verify it works", "looks right", "tbd", etc.).

**If `plan-lint` reports CRITICAL or HIGH issues, fix them before proceeding to Phase 4.** Re-run until clean. The risk-assessor agent should not have to re-do work the script already covered.

Save Phase 3 checkpoint.

### Phase 4: Risk Assessment (skip in `--lite`)

Use the Agent tool to delegate to the `risk-assessor` agent using the substituted template from `references/subagent-prompts/risk-assessment.md`. The agent will also run `plan-lint.py` itself but should focus its judgment on the passes scripts can't cover (anti-patterns 1, 11, 13; architectural concerns; TDD strategy quality).

Pass the draft plan, current `iteration_number`, and `max_iterations` (default 3).

**Validate the agent's JSON output before consuming:**

```bash
echo "$AGENT_OUTPUT" | python3 ${plugin_root}/scripts/validate-json.py \
  ${plugin_root}/references/subagent-prompts/risk-assessment.schema.json - --extract-from-markdown
```

Re-prompt once on validation failure, then fall back to markdown parsing.

Parse the validated JSON per the schema:
- `verdict: APPROVE` → proceed to Phase 5. Record verdict in the risk history (will become a DECISIONS.md entry in Phase 6).
- `verdict: REVISE` and `iteration < max_iterations` → fix `blocking_issues`, increment iteration, re-dispatch. Save per-iteration checkpoint.
- `verdict: REVISE` and `iteration >= max_iterations` with issues remaining → stop looping. Surface `unresolved_issues` to user: "Risk assessment hit iteration cap. Decide: (a) accept these as known gaps, (b) drop back to Phase 3 and restructure the affected tasks yourself, or (c) re-enter via `/rad-brainstormer:design-sprint` if the architecture itself is the problem." In `--non-interactive`, add unresolved issues to `awaiting_user_review`.
- `verdict: RETHINK` → stop immediately regardless of iteration. Surface to user: "Risk assessment returned RETHINK. The architecture has fundamental issues that task-level patches won't fix. Re-enter via `/rad-brainstormer:design-sprint`." Set `escalation.required: true` and `escalation.route_to: "/rad-brainstormer:design-sprint"` in the checkpoint.

### Phase 5: Plan Review & Approval

Present to the user:
1. **Executive summary** — milestones, task count, complexity distribution, plan-lint result, estimated risk level.
2. **Architecture overview** — component diagram, key decisions (omitted in `--lite`).
3. **Full task list** — with dependencies, validation, and rollback for each.
4. **Risk report** — any remaining concerns and mitigations (omitted in `--lite`).
5. **Context management plan** — when to checkpoint and clear.
6. **Assumption set** — the 3+ entries captured in Phase 1 (will land in ASSUMPTIONS.md).

**Ask explicitly: "Does this plan look correct? Should I adjust anything before we lock it in?"**

The plan is NOT approved until the user says so. (In `--non-interactive`, skip approval and add "plan not reviewed by user" to `awaiting_user_review`.)

Save Phase 5 checkpoint.

### Phase 6: Plan Export — Split into 5 Strategic + Operational Files

Once approved, emit the **RAD 8-doc standard** outputs to the project root (or `--output-dir <path>`). Each file has a single canonical purpose; see `references/file-conventions.md` (pointer to `docs/file-conventions.md`) for the spec.

**Files written (or archived-then-overwritten in `--reboot`):**

1. **`PRD.md`** — from Phase 1 Discovery output: project summary, goal, scope (in/out), success criteria, tech-stack summary (from Phase 2), constraints. Target 50–150 lines. Replaces section 1 of the v2.x mega-doc.
2. **`ARCHITECTURE.md`** — from Phase 2 stack-advisor + Phase 5 architecture decisions: Mermaid component diagram, system boundaries, data flow, key design decisions table with rationale. Target 100–300 lines. Replaces section 2 of the v2.x mega-doc.
3. **`ASSUMPTIONS.md`** — from Phase 1 assumption-capture interview: 3+ tight one-line entries describing what's true about the project's reality that wouldn't be obvious from code. Target 20–80 lines. **New file type in 3.0.**
4. **`DECISIONS.md`** — initial entries from Phase 2 stack rationale + Phase 4 risk-assessor verdict history. Sequence-numbered (`0001`, `0002`, …). Target 50–500 lines (above threshold, prompt to convert to ADR layout under `decisions/NNNN-slug.md`). In `--reboot`, append new entries to the existing file and mark prior entries `**Status:** Superseded by <new-entry-number> (reboot YYYY-MM-DD)` where applicable.
5. **`PLAN.md`** — milestones, refined implementation steps, checkpoints, target files, risks/considerations. Target 100–400 lines. Replaces sections 3–7 of the v2.x mega-doc. **This is the renamed `implementation_plan.md`.**
6. **`tasks.md`** — machine-readable task list per `references/task-format.md`. Unchanged shape from 2.x. Validated by `plan-lint.py` after write.
7. **`CLAUDE-FRAGMENT.md`** — transient handoff artifact. Contains an `@-import` block listing the 5 strategic/operational paths above:
   ```markdown
   # CLAUDE-FRAGMENT — Strategic docs for this project
   <!-- Emitted by /rad-planner:plan. Consumed-and-deleted by rad-session /init. -->

   @PRD.md
   @ARCHITECTURE.md
   @ASSUMPTIONS.md
   @DECISIONS.md
   @PLAN.md
   ```
   rad-session `/init` merges this into CLAUDE.md and deletes the FRAGMENT. If FRAGMENT is missing at `/init` time, the import block is auto-generated from detected strategic docs. Safe to delete by hand if you've already merged manually.

**Files NOT written by /plan (single-writer rule):**
- `CLAUDE.md` — owned by rad-session `/init`, `/wrapup`, `/add-resource`
- `HANDOFF.md` — owned by rad-session `/wrapup`
- `.claude/session-log.md` — owned by rad-session `/wrapup`

**Files dropped from v2.x:**
- `implementation_plan.md` — renamed to `PLAN.md`
- `EXECUTION-PROMPT.md` — rad-session `/startup` briefing covers the same role

**After all writes:**

8. **Run `plan-lint.py --mode all`** one final time on the exported `tasks.md`. If clean, report it. If issues, surface them — the user has the choice to fix or accept.
9. **`--reboot` only:** print the supersession summary — which DECISIONS entries were marked superseded, which originals were archived to `*.pre-reboot`. If `DECISIONS.md` is now over ~500 lines, surface the ADR-layout conversion prompt (decoupled from reboot; user decides independently).
10. Recommend the user run `/rad-session:init` (or restart their session) to pick up the new FRAGMENT.
11. Save Phase 6 checkpoint (terminal).

In `--non-interactive` mode, emit a trailing JSON block:
```json
{
  "plan_complete": true,
  "run_id": "string",
  "mode": "full | lite | reboot",
  "files_written": ["PRD.md", "ARCHITECTURE.md", "ASSUMPTIONS.md", "DECISIONS.md", "PLAN.md", "tasks.md", "CLAUDE-FRAGMENT.md"],
  "files_archived": [],
  "decisions_superseded": [],
  "milestones": 0,
  "task_count": 0,
  "plan_lint_clean": true,
  "risk_verdict": "APPROVE | REVISE | not-run-in-lite",
  "escalation_required": false,
  "awaiting_user_review": ["string"]
}
```

## Validate Mode Workflow (`--validate`)

Cheap gap-check. **No agents dispatched, no writes, no user-approval gates.** For a deeper quality audit, use `/rad-planner:review-plan` (dispatches the risk-assessor).

1. **Read the project root.** Issue parallel Reads for `PRD.md`, `ARCHITECTURE.md`, `ASSUMPTIONS.md`, `DECISIONS.md`, `PLAN.md`, `tasks.md`, plus a Glob for `CLAUDE-FRAGMENT.md` and `CLAUDE.md` (to check whether FRAGMENT was already merged).
2. **Run plan-lint on tasks.md (if present):**
   ```bash
   python3 ${plugin_root}/scripts/plan-lint.py --mode all tasks.md --json
   ```
3. **Emit a checklist:**
   ```markdown
   # Plan Validation — <project>

   ## 8-doc gap-check
   - [x] PRD.md (52 lines)
   - [x] ARCHITECTURE.md (148 lines)
   - [ ] ASSUMPTIONS.md ← MISSING (run /plan to create)
   - [x] DECISIONS.md (12 entries, 87 lines)
   - [x] PLAN.md (231 lines)
   - [x] tasks.md (24 tasks, plan-lint clean)
   - [ ] CLAUDE-FRAGMENT.md ← already merged (CLAUDE.md @-imports present)

   ## plan-lint result
   [output verbatim, or "skipped — tasks.md not present"]

   ## Strategic-doc staleness
   [Best-effort: compare git mtime of strategic docs against most-recent commit
    that touched files outside docs. If strategic docs haven't been touched in
    N commits while code has churned, surface as "potentially stale".]

   ## Recommendation
   [One-liner: "Plan is execution-ready" / "Create missing docs first" / etc.]
   ```
4. **Exit clean.** No writes. In `--non-interactive`, emit a trailing JSON:
   ```json
   {
     "validate_complete": true,
     "docs_present": ["PRD.md"],
     "docs_missing": ["ASSUMPTIONS.md"],
     "plan_lint_clean": true,
     "stale_warnings": [],
     "recommendation": "Create missing docs first"
   }
   ```

## Lite Mode Workflow (`--lite`)

For small, single-milestone work, the workflow collapses:

1. **Discovery** — 1-2 questions, not 5. Still ask for 1-2 ASSUMPTIONS entries.
2. **Skip Phase 2** (stack eval) — assume the existing stack
3. **Phase 3 plan** — 5-10 tasks, single milestone, no architecture diagram needed
4. **Skip Phase 4** (risk assessor) — but still run `plan-lint.py` for the mechanical checks
5. **Phase 5 review** — present and approve
6. **Phase 6 export** — same 5 strategic/operational files + tasks.md + FRAGMENT, but PRD/ARCHITECTURE/ASSUMPTIONS sections will be brief (often single-paragraph)

Lite mode trades the architectural review for speed. Use it when you'd otherwise be tempted to skip planning entirely. Don't use it when the work is novel, cross-cutting, or touches anything security/auth/payment.

## Reboot Mode Workflow (`--reboot`)

Project has been built, and now you're regenerating the plan after a pivot, scope change, or significant architectural restructuring. Key differences from a fresh run:

1. **Phase 0.5 fires first** — audit existing code, archive prior strategic docs to `*.pre-reboot`.
2. **Phase 1 anchors to current code reality**, not the prior PRD's aspirations. Interview includes "which prior assumptions have flipped?"
3. **Phase 6 DECISIONS.md is appended-to, not overwritten.** Prior entries get marked `**Status:** Superseded by <new-entry-number> (reboot YYYY-MM-DD)` where the reboot caused them to no longer apply. The new entry's sequence number is the cross-reference.
4. **~500-line threshold prompt.** If DECISIONS.md crosses the index-style cutoff during reboot, surface independently: *"DECISIONS.md is over the index-style threshold. Convert to /decisions/ ADR layout? (y/N)"*. This conversion is a decoupled decision — it's not automatic in 4.0.
5. **All other strategic docs (PRD, ARCHITECTURE, ASSUMPTIONS, PLAN, tasks)** are overwritten after archiving. The `.pre-reboot` archives stay in git history; remove them when you're confident the reboot landed.

Don't use `--reboot` for small course corrections — for those, just edit DECISIONS.md by hand or run `/rad-planner:plan --lite` for a fresh small plan. Reboot is for "we're rethinking the whole shape of this."

## Key References

These contain the detailed templates and contracts. Load them as needed:
- `references/plan-template.md` — Master plan structure (PRD / ARCHITECTURE / ASSUMPTIONS / DECISIONS / PLAN sections, with shared rules)
- `references/file-conventions.md` — Pointer to canonical `docs/file-conventions.md` (8-doc standard, single-writer rule, ownership matrix)
- `references/task-format.md` — Task states, dependency rules, complexity scoring
- `references/golden-path-matrix.md` — Tech stack evaluation criteria
- `references/anti-patterns.md` — 14 documented anti-patterns
- `references/failure-state-template.md` — Triple-component validation
- `references/tdd-constraints.md` — Testing requirements per task
- `references/context-management.md` — Document & Clear protocol + checkpoint schema
- `references/subagent-prompts/stack-eval.md` — Stack-advisor dispatch template
- `references/subagent-prompts/risk-assessment.md` — Risk-assessor dispatch template
- `examples/example-plan.md` + `examples/example-tasks.md` — A real, validator-clean output
- `scripts/README.md` — Validator script documentation

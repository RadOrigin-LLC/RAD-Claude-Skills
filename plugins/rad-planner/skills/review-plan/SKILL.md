---
name: review-plan
description: >
  This skill should be used when the user says "review my plan", "audit this plan",
  "check my implementation plan", "is this plan complete", "what's missing from my plan",
  "validate my plan", "plan review", "check plan quality", "risk review", "check
  dependencies", "are there any risks in my plan", or has an existing implementation
  plan (`docs/planning/current.md`) that needs quality
  assessment before execution begins.
argument-hint: "[path to plan file] [--strict] [--non-interactive] [--resume <run-id>]"
user-invocable: true
allowed-tools: Read Glob Grep Agent Write Bash
---

# Review Plan — Implementation Plan Quality Audit

Audit an existing implementation plan. The audit has two layers:

1. **Mechanical checks** via `scripts/plan-lint.py` — DAG integrity, field presence, vague language. Deterministic; no LLM judgment.
2. **Judgment checks** via the `risk-assessor` agent — anti-pattern scanning, architectural concerns, TDD strategy quality.

This is the quality gate between planning and execution.

## Cross-model note

Model-agnostic. Batch the plan-file reads and risk-assessor reference loads in parallel. The risk-assessor JSON contract is identical regardless of which model tier the session runs in.

## Execution: parallel-first

- **Step 1 plan location** — if multiple candidate paths exist, Glob and Read them in a single parallel batch.
- **Step 2 mechanical lint** — runs in parallel with Step 3 risk-assessor dispatch (independent inputs, both read the same plan).
- **Step 4 additional checks** can run concurrently with interpreting the risk-assessor's JSON output.

## Mode Flags

- `--strict` — Apply production-grade standards (see "Strict Mode" below). The mechanical lint already runs at full strictness; `--strict` raises the risk-assessor's threshold for what counts as blocking.
- `--non-interactive` — Skip Step 6 fix-offer interaction. Emit verdict + unresolved issues as trailing JSON. Auto-proceed thresholds: `verdict: APPROVE` → exit clean; `verdict: REVISE` → emit issues without applying fixes; `verdict: RETHINK` → emit escalation routing.
- `--resume <run-id>` — Load `.planner/state/<run-id>.json` and continue from last saved step.

## Workflow

### 1. Locate the Plan

If a path was provided, read it directly. Otherwise the canonical plan is `docs/planning/current.md`. Read it plus the supporting canonical docs in a single parallel batch — `docs/vision.md` (goal + non-goals), `docs/architecture.md` (invariants, stack), `docs/roadmap.md` (sequencing) — so the risk-assessor has full strategic context.

If `docs/planning/current.md` doesn't exist, fall back to Glob for a legacy or non-canonical plan file (`PLAN.md`, `plan.md`, `implementation_plan.md`, any `.md` in `docs/plans/` or `plans/`) and note in the report that the project isn't on the canonical structure — recommend `/rad-planner:plan` to migrate. (For the cheap "do the canonical docs exist + does lint pass" gap-check without dispatching the risk-assessor, use `/rad-planner:plan --validate` instead.)

Read the plan file(s) completely in a single parallel batch.

Save Step 1 checkpoint to `.planner/state/<run-id>.json`.

### 2. Mechanical Lint (parallel with Step 3)

```bash
python3 ${plugin_root}/scripts/plan-lint.py --mode all docs/planning/current.md --json
python3 ${plugin_root}/scripts/coverage-validator.py docs/planning/current.md --json
python3 ${plugin_root}/scripts/dependency-cycle-detector.py docs/planning/ --json --include-archive   # scans current.md + archive/*.md; no-ops cleanly if no milestone dependencies are declared
```

Capture the output. The scripts report:
- **plan-lint:** missing required sections, acceptance-criteria checkbox format, vague language ("verify it works", etc.)
- **coverage-validator:** acceptance criteria with no verification path in the validation commands
- **dependency-cycle-detector:** cycles in the milestone dependency graph

Exit code 1 = issues found, 0 = clean. Either way, parse the JSON for the issue list — these feed directly into Step 5's report and **bypass the risk-assessor entirely** (deterministic results don't need LLM judgment).

### 3. Delegate to Risk Assessor (parallel with Step 2)

Use the Agent tool to delegate to the `risk-assessor` agent with the substituted template from `references/subagent-prompts/risk-assessment.md`. Pass:
- The plan content
- The supporting canonical docs read in Step 1 (vision / architecture / roadmap) as `{supporting_docs_or_none}`
- `iteration_number: 1`, `max_iterations: 1` (review-plan runs a single pass; the iterative loop is owned by `/rad-planner:plan`)
- A note that the mechanical layer has already run, so the agent should focus on judgment-required passes (anti-patterns 1, 9, 13; architecture; TDD strategy quality) rather than re-doing the field-presence, coverage, and dependency-cycle checks the scripts already cover

**Validate the agent's JSON output:**

```bash
echo "$AGENT_OUTPUT" | python3 ${plugin_root}/scripts/validate-json.py \
  ${plugin_root}/references/subagent-prompts/risk-assessment.schema.json - --extract-from-markdown
```

Re-prompt once on schema failure, then fall back to markdown parsing per the legacy structure in `agents/risk-assessor.md`.

Parse the validated JSON. Key fields:
- `verdict`: `APPROVE` | `REVISE` | `RETHINK`
- `blocking_issues[]`: CRITICAL/HIGH issues with fix suggestions
- `advisory_issues[]`: MEDIUM/LOW issues
- `escalation_required`: surfaced when the audit cannot produce a clean verdict

Save Step 3 checkpoint with the parsed JSON + lint output.

### 4. Additional Checks (Beyond Lint and Risk Assessment)

After parsing the risk assessor's report, also verify:

**Zero-Context Readiness (judgment, not enforced):**
- Could a fresh AI session execute this plan with no prior conversation?
- Are all file paths explicit (not "the auth file" but `src/middleware/auth.ts`)?
- Are all commands runnable as-is (not "run the tests" but `npm test -- --grep auth`)?
- Are all external dependencies documented (env vars, API keys, services)?

**Completeness:**
- Does every milestone have a checkpoint?
- Does every task have a Definition of Done?
- Are success criteria defined at the project level?
- Is the architecture documented (not just implied)?
- Are edge cases called out specifically?

**Formatting (lint covers most of this; this is for things lint can't see):**
- Are stop-and-checkpoint boundaries present per milestone?
- Is the plan structured per the `docs/planning/current.md` 8-section schema?

### 5. Present Results

Output a structured review, merging the lint output, the risk-assessor JSON, and the additional checks:

```markdown
# Plan Review Report

**Plan:** [filename]
**Review mode:** [standard | strict]
**Mechanical lint:** [PASS | N issues]
**Risk-assessor verdict:** APPROVE | REVISE | RETHINK
**Overall recommendation:** [actionable next step]

## Mechanical Issues (from plan-lint.py)
- [LIST — these are deterministic, no judgment debate]

## Critical Issues (block execution until fixed)
- [Issue with specific fix recommendation]

## Improvements (recommended before execution)
- [Issue with fix]

## Optional Enhancements
- [Nice-to-have]

## Completeness Checklist
- [x] Project summary and success criteria
- [x] Architecture documented
- [ ] Target files listed ← MISSING
- [x] Dependencies mapped
[...]

## Escalation
[Only present if verdict=RETHINK — recommend /rad-brainstormer:design-sprint]
```

### 6. Offer Fixes (interactive only)

If `verdict` is `REVISE` and not `--non-interactive`, offer to fix the identified issues directly in the plan file. For each fix:
- Explain what you're changing and why.
- Show the before/after.
- Only modify the plan document — never create implementation files.

Mechanical issues from plan-lint generally have unambiguous fixes (add the missing field, replace the vague phrase). Offer to apply those automatically.

If `verdict` is `RETHINK`, do NOT offer fixes. Instead surface: "This plan has fundamental architectural issues that task-level fixes won't resolve. Re-enter via `/rad-brainstormer:design-sprint` to rework the architecture, then return here for re-review."

In `--non-interactive` mode, emit a trailing JSON block and exit:

```json
{
  "review_complete": true,
  "run_id": "string",
  "plan_path": "string",
  "lint_issues": 0,
  "verdict": "APPROVE | REVISE | RETHINK",
  "blocking_issue_count": 0,
  "advisory_issue_count": 0,
  "escalation_required": false,
  "escalation_route": "",
  "awaiting_user_review": ["string"]
}
```

## Strict Mode (`--strict`)

When `--strict` is specified, apply production-grade standards on top of the lint:
- Every task MUST have validation AND rollback (lint already enforces; strict makes any missing field a CRITICAL not HIGH).
- Coverage targets MUST be specified per task (judgment).
- Security review checkpoints MUST exist for auth/payment/data tasks (judgment).
- Context management plan MUST include specific clear points (judgment).
- All external API integrations MUST have error handling in the task spec (judgment).

In strict mode, the risk-assessor treats any MEDIUM issue in these categories as HIGH.

## What this skill does NOT do

- Does not modify the plan unless explicitly authorized in Step 6.
- Does not test that the plan actually works — that's the executor's job.
- Does not check anti-patterns the script can't see (judgment-required ones); the risk-assessor agent handles those.
- Does not re-validate the schema of the plan file itself; it parses by best-effort markdown matching.

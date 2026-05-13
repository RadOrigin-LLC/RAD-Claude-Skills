# rad-planner

Structured implementation-planning scaffolding for Claude Code, with **mechanical validators** (Python scripts) backing the parts that templates alone can't enforce.

## What this actually is

A 6-skill plugin that walks you through Discovery → Stack Eval → Plan → Risk → Review → Export, dispatches subagents for stack and risk work, and runs Python validators on the generated artifacts. The plan output is markdown intended for a fresh AI session to pick up cold.

The skills are mostly structured prompts that ask the model to behave like a planner. The **scripts** in `scripts/` are real validators — they parse the generated tasks file, build the DAG, check for cycles and phantom dependencies, verify required fields are present, flag vague language, and validate subagent JSON against schemas. Where the README says "enforced," the script does the work.

## File conventions

rad-planner produces project-level planning artifacts per the [RAD 8-doc standard](../../docs/file-conventions.md) at the repository root. The standard is the canonical convention shared with rad-session: it defines target lengths, update triggers, pruning rules, and the single-writer rule that prevents collision between plugins.

## What it does NOT do

- **Does not execute the resulting plan.** It produces planning artifacts. You (or another tool) run the work.
- **Does not test that a plan is "zero-context ready."** That's the *intent* of the templates, not a verified property.
- **Does not detect every anti-pattern.** Mechanical checks cover field presence, DAG integrity, and vague language. Anti-patterns 1, 9, 11, 13 (judgment-required) are still checked by the risk-assessor agent — and several of those are opinions with thresholds, not laws.
- **Does not stop you from skipping phases.** Phase order is enforced by instructions to the model, not by code.
- **Does not auto-checkpoint or auto-clear context.** The checkpoint skill writes a handoff file; you run `/clear` and rehydrate yourself.
- **Does not track planning quality over time.** No metrics, no learning from prior plans.
- **Does not replace Claude Code's built-in Plan Mode** — it adds artifacts on top of it. See "Relationship to built-in Plan Mode" below.

## Skills

| Skill | Trigger | What it produces |
|---|---|---|
| `/rad-planner:plan` | "plan my project", "create implementation plan" | Full 6-phase workflow → 5-file split (PRD / ARCHITECTURE / ASSUMPTIONS / DECISIONS / PLAN) + `tasks.md` + transient `CLAUDE-FRAGMENT.md`. Supports `--lite`, `--reboot`, `--validate`. Legacy 2.x trigger `plan-project` still works. |
| `/rad-planner:evaluate-stack` | "what stack should I use", "recommend a stack" | Stack recommendation table with live version verification. Standalone or as Phase 2 of `/plan`. |
| `/rad-planner:review-plan` | "review my plan", "audit this plan" | Deep quality audit combining mechanical lint + risk-assessor judgment. For a cheap "do the docs exist + does lint pass" gap-check, use `/plan --validate` instead. |
| `/rad-planner:status` | "plan status", "what's next", "where am I in the plan" | Quick read of an in-flight plan: % complete, blocked tasks, next eligible. |
| `/rad-planner:checkpoint` | "checkpoint", "save progress", "document and clear" | Writes `.planner/state/<run-id>.json` and updates plan task states. **Does NOT write HANDOFF.md in 3.0+** — that's rad-session `/wrapup`'s job (single-writer rule). |

Honest note: `evaluate-stack` and `review-plan` are also exposed as standalone skills, but they re-use the same agents (`stack-advisor`, `risk-assessor`) that `/plan` invokes during its phases. Treat them as direct entry points for those phases, not separate functionality.

**Removed in 3.0:** `generate-project-config` is gone. Its v2.x role (derive `CLAUDE.md` + `ARCHITECTURE.md` from an approved plan) is fully absorbed by `/plan`'s Phase 6, which now emits `ARCHITECTURE.md` directly and produces `CLAUDE-FRAGMENT.md` for rad-session `/init` to merge into `CLAUDE.md`. Run `/plan` for greenfield, `/plan --reboot` for projects without a plan.

## Agents

| Agent | Role | Model |
|---|---|---|
| **plan-architect** | Lead orchestrator — read-only exploration, strategic questions, plan drafting | Opus 4.7 default, Sonnet 4.6 fallback |
| **stack-advisor** | Tech stack evaluation, live version checks via Context7/WebSearch | Opus 4.7 default, Sonnet 4.6 fallback |
| **risk-assessor** | Anti-pattern judgment, architecture concerns, TDD strategy quality. Calls `plan-lint.py` first to skip mechanical checks. | Opus 4.7 default, Sonnet 4.6 fallback |

## Mechanical validators (scripts/)

The validators are what convert "we enforce DAG integrity" from aspiration to fact.

### `scripts/plan-lint.py`

Pure-Python (3.8+ stdlib only). Modes:

| Mode | Catches |
|---|---|
| `dag` | Multi-hop cycles, phantom dependencies (`Dependencies: [S99]` where S99 doesn't exist), complexity > 7 without subtasks |
| `checklist` | Missing required fields (Validation, Rollback, Dependencies, Complexity), vague language ("verify it works", "looks right", "tbd") |
| `status` | Task state report — % complete, state breakdown, blocked tasks, next-eligible by dependency |
| `all` | dag + checklist |

Output: human-readable text or `--json` for machine consumption. Exit `0` clean, `1` issues found, `2` script error.

### `scripts/validate-json.py`

Validates JSON output (from subagents) against JSON Schema files at `references/subagent-prompts/*.schema.json`. Pure stdlib; uses the `jsonschema` package if installed for fuller draft-07 coverage.

Used by skills to validate subagent contracts before consuming them — re-prompts the agent once on schema failure rather than silently parsing whatever came back.

### `scripts/README.md`

Full invocation docs and the table of which skill / agent calls which script when.

## Relationship to built-in Plan Mode

Claude Code ships with [Plan Mode](https://docs.claude.com/en/docs/claude-code/) (Shift+Tab toggle, `--permission-mode plan`) which restricts to read-only tools. rad-planner does not replace it; the two compose:

- **Plan Mode** handles read-only enforcement at the runtime level (no Edit/Write/Bash).
- **rad-planner** adds structured artifacts on top: a 7-section plan template, a DAG, a risk audit, an executor handoff manifest, and a checkpoint schema.

You can run `/rad-planner:plan` inside Plan Mode for runtime-level read-only guarantees — the skill will still produce all its planning artifacts via the Write tool (which is required to save the plan).

## Pipeline with rad-brainstormer

`rad-planner` and [`rad-brainstormer`](../rad-brainstormer/) chain. They own different phases:

| Phase | Plugin | Owns | Output |
|---|---|---|---|
| **Ideation** (divergent) | `rad-brainstormer` | Exploring the problem, generating options, stress-testing assumptions | A decided idea + rough direction |
| **Design** (post-ideation) | `rad-brainstormer:design-sprint` | Architecture, components, data flow, API design, error handling, testing strategy | A reviewable design spec |
| **Planning** (pre-code) | `rad-planner:plan` | Dependency-aware task graph, complexity scoring, risk audit, failure states | An ordered implementation plan |
| **Code** | your tools of choice | Implementation | Working software |

If you come in with a clear idea, start with `/rad-planner:plan`. If the idea is fuzzy, start with `/rad-brainstormer:brainstorm-session` first.

## Reference Files

The `references/` directory contains the knowledge base agents and skills load on demand:

| Reference | Content |
|---|---|
| `golden-path-matrix.md` | AI-native proficiency tiers + project-type stack recommendations (date-stamped, opinionated) |
| `anti-patterns.md` | 14 documented "Do Not Do" constraints (some are opinions with thresholds — clearly marked) |
| `plan-template.md` | Template structure for the 5-file split (PRD / ARCHITECTURE / ASSUMPTIONS / DECISIONS / PLAN) with shared rules and a "what enforces what" table |
| `file-conventions.md` | Pointer to canonical `docs/file-conventions.md` (RAD 8-doc standard, single-writer rule) |
| `task-format.md` | DAG-based task syntax, states, dependency rules, complexity scoring |
| `failure-state-template.md` | Triple-component validation (Action → Validation → Rollback) |
| `tdd-constraints.md` | Red-Green-Refactor + mutation testing requirements |
| `context-management.md` | Document & Clear triggers, handoff protocol, shared checkpoint schema |
| `subagent-prompts/stack-eval.md` + `.schema.json` | Stack-advisor dispatch template + JSON Schema |
| `subagent-prompts/risk-assessment.md` + `.schema.json` | Risk-assessor dispatch template + JSON Schema |

## Examples

`examples/example-plan.md` and `examples/example-tasks.md` are a complete (small) plan that passes the validators. Use them to:
- See what `/plan` actually produces (not just templates) — `example-plan.md` shows all five strategic/operational docs concatenated for readability.
- Run the validators against a real artifact: `python3 scripts/plan-lint.py --mode all examples/example-tasks.md`.
- Test the validator failure modes by introducing a cycle or stripping a field.

## Upgrading from 2.x

If you have a project that was set up with rad-planner 2.x, run the migration helper bundled with rad-session **before** installing rad-planner 3.0:

```bash
# Preview the changes (writes nothing)
python3 ${rad-claude-skills}/plugins/rad-session/scripts/migrate-to-v4.py /path/to/your/project --dry-run

# Apply (interactive — confirms each transformation)
python3 ${rad-claude-skills}/plugins/rad-session/scripts/migrate-to-v4.py /path/to/your/project

# Or apply non-interactively (safe transforms only; ambiguous items skipped for manual review)
python3 ${rad-claude-skills}/plugins/rad-session/scripts/migrate-to-v4.py /path/to/your/project --non-interactive
```

**What gets transformed:**

| v2.x artifact | 3.0 outcome |
|---|---|
| `implementation_plan.md` (mega-doc) | Split into `PRD.md` / `ARCHITECTURE.md` / `ASSUMPTIONS.md` / `DECISIONS.md` / `PLAN.md` at project root. Section-heading heuristics map the old 7-section template. The "Key Design Decisions" table seeds DECISIONS.md as sequence-numbered entries. ASSUMPTIONS.md is a placeholder (no v2.x source). |
| `EXECUTION-PROMPT.md` | Archived. The rad-session 4.0 `/startup` briefing covers the same kickoff role. |
| `docs/ARCHITECTURE.md` | Moved to `ARCHITECTURE.md` at project root (3.0 puts all strategic docs at root). When `implementation_plan.md` is also being split, the duplicate at `docs/` is archived to avoid two sources of truth. |
| `HANDOFF.md` from `/checkpoint` | Archived. rad-planner 3.0's `/checkpoint` no longer writes HANDOFF.md (single-writer rule) — that file is owned by rad-session `/wrapup`. The next `/rad-session:wrapup` regenerates it. |
| `CLAUDE.md` from `/rad-planner:generate-project-config` | Preserved as-is. The `generate-project-config` skill is removed in 3.0; `CLAUDE-FRAGMENT.md` is emitted alongside so the next `/rad-session:init` can merge strategic `@-imports`. |

All originals archive to `.rad-archive/<UTC-timestamp>/` (gitignored by default). The archive's `manifest.json` records every action for audit and rollback. See `plugins/rad-session/scripts/README.md` for the script's full contract.

**After migration, verify:**

```bash
python3 scripts/plan-lint.py --mode all tasks.md   # mechanical task-graph lint
/rad-planner:plan --validate                       # cheap 8-doc gap-check
/rad-session:init                                  # merges CLAUDE-FRAGMENT.md
```

**Rollback:** copy files back from `.rad-archive/<timestamp>/` (originals carry `.orig` suffix, path separators flattened to `-`), then delete the new v4 files. **Re-run safety:** the migration script is a no-op on projects already on the 8-doc standard.

## What's New in 3.0

- **Document standardization — the RAD 8-doc standard.** `/plan` now emits five strategic/operational files (PRD.md, ARCHITECTURE.md, ASSUMPTIONS.md, DECISIONS.md, PLAN.md) at project root instead of a single 7-section `implementation_plan.md`. Each file has a single canonical purpose and one plugin owner. Canonical spec at `docs/file-conventions.md` (shared with rad-session 4.0).
- **`plan-project` renamed to `plan`.** Same skill, shorter name. Legacy trigger phrases (`plan-project`, "plan my project") still work.
- **`CLAUDE-FRAGMENT.md` handoff to rad-session.** `/plan` Phase 6 emits a transient `@-import` block listing the 5 strategic paths. rad-session `/init` merges it into CLAUDE.md and deletes the FRAGMENT. Single-writer rule: `/plan` never touches CLAUDE.md directly.
- **`/plan --reboot` mode.** For projects past their original plan: audits existing code (Phase 0.5), archives prior strategic docs to `*.pre-reboot`, regenerates anchored to current reality, marks superseded DECISIONS entries with sequence-number references (`Superseded by 0042 (reboot YYYY-MM-DD)`). ADR-layout conversion at the ~500-line threshold is prompted independently, not automatic.
- **`/plan --validate` mode.** Cheap 8-doc gap-check: do the files exist? Does `tasks.md` lint clean? No agents dispatched, no writes. Cheaper than `/review-plan` (which dispatches the risk-assessor for deep judgment audits).
- **`/checkpoint` no longer writes HANDOFF.md.** That file is owned exclusively by rad-session `/wrapup` in the 4.0/3.0 era. `/checkpoint` now writes only `.planner/state/<run-id>.json` and updates plan task states. Run `/rad-session:wrapup` before clearing if you want a session-level handoff.
- **`generate-project-config` removed.** Its v2.x role is fully absorbed by `/plan`'s Phase 6 (ARCHITECTURE.md) and `/init`'s FRAGMENT merge (CLAUDE.md). One source of truth, not two.
- **`EXECUTION-PROMPT.md` dropped.** rad-session `/startup` briefing covers the same role: it reads HANDOFF.md + session-log + CLAUDE.md and orients you for the next chunk of work. A separate kickoff artifact was redundant.
- **`ASSUMPTIONS.md` is a new file type.** Phase 1 Discovery explicitly captures non-obvious truths about the project's reality ("no users yet", "single-tenant only", "sensitive data — no real values in repo"). Invalidated assumptions use strikethrough, not deletion — audit trail matters.
- **`DECISIONS.md` is sequence-numbered and append-only.** Stack rationale + risk-assessor verdicts seed the initial entries. `/wrapup` Phase 3.5 (rad-session 4.0) prompts to append tagged decisions from a work session.

## What's New in 2.1

- **`scripts/plan-lint.py`** — Mechanical DAG + checklist + status validator. Converts "we enforce DAG integrity" from claim to mechanism.
- **`scripts/validate-json.py`** — JSON Schema validator for subagent output contracts. Skills now re-prompt on schema failure instead of silently falling back to markdown parsing.
- **JSON Schema files** at `references/subagent-prompts/{stack-eval,risk-assessment}.schema.json` — Concrete contract, not just documentation.
- **`/rad-planner:status` skill** — Quick read of in-flight plan progress, blocked tasks, next eligible.
- **`--lite` flag on `plan-project`** — Single-milestone workflow for small/bug-fix work, skips stack eval + risk-assessor loop, still runs `plan-lint.py`.
- **`EXECUTION-PROMPT.md` artifact** — Phase 6 now generates a copy-pasteable kickoff prompt for the next session, not just "start a fresh session and load the plan."
- **Risk-assessor calls `plan-lint.py` first** — Mechanical checks are deterministic; the agent's judgment is reserved for anti-pattern, architecture, and TDD-quality passes scripts can't do.
- **Honesty pass across the README and references** — "Enforces" softened to "guides" or "validates" depending on actual mechanism. "Zero-context ready" now framed as the intent, not a verified property. Anti-pattern #1 (Vector Sidecar) reframed from dogmatic ban to threshold-based default.
- **Date-stamped Golden Path matrix** with explicit "trust live verification over the matrix when they disagree" guidance.
- **`examples/`** — A real, validator-clean plan + tasks file ships with the plugin.

## What's New in 2.0 (prior release)

Platform-level optimization pass for Opus 4.7 (Sonnet 4.6 and Haiku 4.5 fully supported):

- **Opus-default on all three agents.** Sonnet 4.6 is a first-class fallback; Haiku 4.5 for narrow scope.
- **JSON-first subagent output contracts** with markdown fallback for model variance. (2.1 made these enforced via `validate-json.py`.)
- **Externalized subagent prompt templates** at plugin-level `references/subagent-prompts/`.
- **`--non-interactive` mode** on `plan-project`, `review-plan`, `evaluate-stack`, `generate-project-config`.
- **`--resume <run-id>` + shared checkpoint schema** at `.planner/state/<run-id>.json`.
- **Parallel-first execution guidance** in every multi-phase skill.
- **Escalation path to brainstormer** on `RETHINK` verdict.
- **Flattened agent layout** to `agents/<name>.md`.
- **Honest claims audit** across references — first pass; 2.1 extends this throughout.

## Quick Start

1. Start a new Claude Code session.
2. Run `/rad-planner:plan` with your project description (add `--lite` for small work, `--reboot` for an existing project that needs replanning).
3. Answer the strategic discovery questions (including the assumption-capture interview new in 3.0).
4. Review the generated plan and approve.
5. Run `/rad-session:init` (or restart your session) so rad-session merges `CLAUDE-FRAGMENT.md` into `CLAUDE.md`. Then start a fresh execution session — `/rad-session:startup` briefs you for the first task.

For an existing plan: `/rad-planner:plan --validate path/to/project` for a cheap 8-doc gap-check, `/rad-planner:review-plan path/to/plan.md` for a deep quality audit, or `/rad-planner:status path/to/tasks.md` for a quick progress read.

## The Planning Workflow

```
┌───────────┐  ┌────────────┐  ┌─────────┐  ┌─────────┐  ┌────────────┐
│ Discovery │→ │ Stack Eval │→ │  Plan   │→ │  Risk   │→ │   Review   │
└───────────┘  └────────────┘  └─────────┘  └─────────┘  └────────────┘
                                                              ↓
                                              ┌──────────────────────────────────┐
                                              │ Export: PRD + ARCHITECTURE +     │
                                              │ ASSUMPTIONS + DECISIONS + PLAN + │
                                              │ tasks + CLAUDE-FRAGMENT (with    │
                                              │ plan-lint validation)            │
                                              └──────────────────────────────────┘
```

`--lite` collapses Stack Eval and Risk into a single Plan→Lint→Review pass. `--reboot` adds a Phase 0.5 audit before Discovery. `--validate` short-circuits the workflow to a cheap gap-check + lint pass.

## What Gets Generated

After the planning workflow completes, at project root (or `--output-dir`):

**Strategic tier (set at project genesis, rarely change):**
- `PRD.md` — project summary, scope, success criteria, tech-stack summary, constraints
- `ARCHITECTURE.md` — component diagram, system boundaries, data flow, design decisions
- `ASSUMPTIONS.md` — non-obvious truths about the project's reality

**Operational tier (evolve with the work):**
- `DECISIONS.md` — sequence-numbered append-only architecture decisions (stack rationale + risk-assessor verdicts seed it)
- `PLAN.md` — milestones, implementation steps, target files, checkpoints, risks/considerations

**Machine-readable:**
- `tasks.md` — task list with dependency graph, validated by `plan-lint.py`
- `.planner/state/<run-id>.json` — resumable run state (via `--resume`)

**Transient handoff:**
- `CLAUDE-FRAGMENT.md` — `@-import` block consumed and deleted by `/rad-session:init`

**Not written by `/plan` (single-writer rule):**
- `CLAUDE.md` — owned by rad-session `/init`, `/wrapup`, `/add-resource`
- `HANDOFF.md` — owned by rad-session `/wrapup`
- `.claude/session-log.md` — owned by rad-session `/wrapup`

See `docs/file-conventions.md` (canonical) for the full ownership matrix and update/pruning rules.

## Requirements

- **Python 3.8+** for the validator scripts. If unavailable, the skills surface a fallback: manual review using the documented checklists. The honest framing is that without Python, the "validators" reduce to "templates the model is asked to follow."
- Optional: `pip install jsonschema` for fuller JSON Schema draft-07 coverage in `validate-json.py`. Pure-stdlib subset is used when not installed.

## License

Apache-2.0

# rad-planner

Plan-first project planning for Claude Code — **conversational by design**, with mechanical validators (pure-stdlib Python) backing the parts templates alone can't enforce.

> **v4.11 — v3.0 debt retirement.** The legacy v3.0 agents, sibling skills, and reference files are realigned to the v4.x canonical doc structure. `plan-architect` is retired (the `/plan` skill is the orchestrator); `risk-assessor` now reviews `docs/planning/current.md`'s milestone structure instead of a v3.0 `tasks.md` DAG; `status` reports acceptance-criteria progress; `checkpoint` points at `docs/status.md` (HANDOFF.md / session-log retired in rad-session 5.0). Point-version model references removed plugin-wide; agents/skills are model-agnostic.
>
> **v4.10 — user-owned content visibility audit.** New `audit-user-content.py` validator surfaces stale user-owned operating-manual sections — orphan terminology (Title-Case phrases that appear nowhere else in the repo) and dead paths (links to files that don't exist) — without modifying them. Invoked by rad-session 5.6+ at `/wrapup` and `/startup`. Pairs with the sectioned-writer rule: refusal to modify ≠ refusal to flag staleness.
>
> **v4.9 — depth-of-planning heuristic at M0.5.** The scope gate recommends a planning depth (shallow / standard / deep) from the inferred decision class — architecture / cost / UX / trust / identity changes warrant deep; cosmetic fixes warrant shallow. `--depth` overrides. Shallow skips M1–M5; deep adds a mandatory `risk-assessor` pass at M4. The M0.5 hard gate fires regardless.
>
> **v4.8 — compact milestone contract in `current.md`.** M6 writes a `### Session contract` sub-section (the 7-field build-readiness block: current milestone / goal / in scope / out of scope / files likely touched / acceptance criteria / stop-and-ask-if) derived from the canonical sections. `plan-lint.py` validates all 7 fields; rad-session 5.5+ surfaces it at `/startup` before the first tool call.
>
> **v4.7 — Lanes section in the operating manual.** M6 writes a verbatim role-separation contract — what the human decides, what the agent may do during planning vs during coding, what it must never do. Agent-agnostic; owned by rad-planner per the sectioned-writer rule; rad-session 5.4+ treats it as never-prunable.
>
> **v4.6 — build-readiness gate alignment.** `docs/planning/current.md` gains required **Guardrails** and **User-visible behavior** sections (enforced by `plan-lint.py`); `docs/planning/parked.md` becomes a first-class third option for ambiguous ideas; `--assessment` surfaces planning-velocity signals to catch planning-as-avoidance.
>
> **v4.5 — `--assessment` flag exposed.** A read-only state-of-project diagnostic. Runs the internal assessor over whatever evidence exists (git, docs, source, validator results) and emits a structured report: project facts, canonical-doc coverage + staleness + validator pass/fail, detected drift signals, and an inferred next-step suggestion (full / improve / drift / pivot / "no planner action needed") with one-sentence rationale. Distinct from `--drift` (which requires an existing plan): `--assessment` works on any project state, produces no writes, skips M0.5 and M1–M5.
>
> **v4.4 — project-story synthesis skills.** Two new skills derive plain-language narrative views from the canonical doc set: `/project-story` generates a state-of-the-project narrative (one-line product test, who it's for in build order, what it's explicitly NOT, where we are, what's pending, bottom line) for non-developer stakeholders, new collaborators, future-self after time away, or funders. `/refresh-story` updates an existing story file in place via inline drift detection.
>
> **v4.3 — M0.5 briefing reshape + conversational-continuation triggers.** The M0.5 scope-confirmation gate renders as a prose-first briefing (Where we left off + Last accomplishment + Next logical step + Or you could start with + a single Mechanical state line) instead of identifier-heavy recap. Trigger phrases expanded to catch free-form planning-continuation utterances at session open.
>
> **v4.2 — M0.5 scope-confirmation hard gate.** Fires after M0 discovery and BEFORE any substantive work on ALL entry points and ALL modes including `--auto`. Autonomy applies to the work, not to the scope decision.
>
> **v4.1 — conversational by design.** `/plan` is multi-phase dialogue. M1–M5 each require explicit user input. Harness-level autonomy hints (permission-mode Auto/Bypass, `<system-reminder>` "don't ask clarifying questions") apply to *tool-use approvals*, NOT to the planning conversation. New opt-in `--auto` flag is the only way to suppress M1–M5 — it produces DRAFT-labeled strawmen and does NOT write ADRs (candidates land in `docs/planning/proposed-decisions.md` for user review).

## What this actually is

A 7-skill plugin built around a five-phase **planning conversation** that produces the plan, then an M6 milestone that writes the approved doc set per the [canonical structure](../../docs/doc-conventions.md). The plan is the deliverable; the docs follow the plan, not the other way around.

The skills are structured prompts that drive the conversation. The **scripts** in `scripts/` are real validators — they parse the generated `current.md`, check required sections, validate AC checkbox format, scan for vague language, detect cross-doc duplicates, find vision/plan contradictions, lint dependency cycles, and validate subagent JSON against schemas. Where the README says "validates," the script does the work.

## What it does NOT do

- **Does not execute the resulting plan.** It produces planning artifacts. You (or another tool) run the work.
- **Does not silently auto-write under `--auto`.** Every `--auto` output file carries a `> **DRAFT — review and revise**` banner; ADRs are deferred to `docs/planning/proposed-decisions.md` so the user explicitly promotes them.
- **Does not bypass the M0.5 scope-confirmation gate.** Not even under `--auto`. Autonomy applies to the work; the scope decision is always confirmed.
- **Does not detect every anti-pattern.** Mechanical checks cover section presence, AC format, vague language, cross-doc duplication, and vision/plan contradiction. Judgment-required anti-patterns are surfaced by the `risk-assessor` agent.
- **Does not track planning quality over time.** No metrics, no learning from prior plans.
- **Does not migrate from 3.x to 4.x automatically.** Neither prior version had public traffic; migration tooling was intentionally not built.

## Skills

| Skill | Trigger | What it produces |
|---|---|---|
| `/rad-planner:plan` | "plan my project", "create implementation plan", "improve my plan", "continue planning" | Five-phase conversation → approved doc set written at M6 per the [canonical structure](../../docs/doc-conventions.md). Six mode flags: `--full`, `--improve`, `--drift`, `--pivot`, `--validate`, `--assessment`. Plus opt-in `--auto` for DRAFT strawmen. |
| `/rad-planner:project-story` | "tell me what this project is", "explain the state of the project", "summarize for a stakeholder" | State-of-project narrative read from the canonical doc set (vision + decisions + planning/current + status + roadmap). Plain English, no marketing language, every claim traceable. |
| `/rad-planner:refresh-story` | "refresh the story", "update PROJECT-STORY.md" | In-place refresh of an existing story file. Inline drift detection — regenerates only sections whose canonical source has changed; preserves the user's edits in fresh sections. |
| `/rad-planner:evaluate-stack` | "what stack should I use", "recommend a stack" | Stack recommendation table with live version verification. Standalone, or invoked as part of `/plan`'s M2/M3 conversation. |
| `/rad-planner:review-plan` | "review my plan", "audit this plan" | Deep quality audit combining mechanical lint + risk-assessor judgment. For a cheap "do the docs exist + does lint pass" gap-check, use `/plan --validate` instead. |
| `/rad-planner:status` | "plan status", "what's next", "where am I in the plan" | Quick read of an in-flight plan: acceptance-criteria progress (% complete, what's done, what's remaining). |
| `/rad-planner:checkpoint` | "checkpoint", "save progress" | Writes `.planner/state/<run-id>.json` and reflects completed acceptance criteria in `current.md`. Does NOT write `docs/status.md` — that's owned by rad-session `/wrapup` (single-writer rule). |

## Agents

| Agent | Role | Model |
|---|---|---|
| **stack-advisor** | Tech stack evaluation, live version checks via Context7/WebSearch | Opus default, Sonnet fallback |
| **risk-assessor** | Anti-pattern judgment, architecture concerns, TDD strategy quality. Calls `plan-lint.py` first to skip mechanical checks. | Opus default, Sonnet fallback |

## Mechanical validators (scripts/)

The validators are what convert "we enforce structure" from aspiration to fact. All pure-stdlib Python 3.8+. All emit human-readable text by default and structured `--json` on request. Exit 0 clean, 1 issues found, 2 script error.

| Script | What it checks |
|---|---|
| `plan-lint.py` | `docs/planning/current.md` — required sections, AC checkbox format, vague-language detection |
| `status-validator.py` | `docs/status.md` — freshness vs git mtime, 8-section presence, evidence-based validation results |
| `doc-redundancy.py` | Cross-doc bullet duplicate detection via Jaccard similarity (catches "same thing said in two docs") |
| `doc-contradiction.py` | `vision.md` non-goals vs `current.md` acceptance criteria via stemmed token overlap (catches "we said NOT to do X but plan-task #3 does X") |
| `estimate-validator.py` | Flags plans with no effort/size signal |
| `dependency-cycle-detector.py` | DFS cycle detection across milestone dependencies |
| `coverage-validator.py` | Flags ACs with no apparent validation command |
| `scope-creep-detector.py` | Vision non-goals dropped from current.md AND present elsewhere in plan content |
| `validate-json.py` | JSON Schema validator for subagent output contracts; re-prompts the agent once on schema failure |

Each validator is also exposed as a standalone slash command (`/plan-lint`, `/status-validate`, `/doc-redundancy`, `/doc-contradiction`, `/plan-estimates`, `/plan-cycles`, `/plan-coverage`, `/plan-scope-creep`) usable on any plan-shaped markdown outside the `/plan` workflow. Validator documentation lives in `scripts/README.md`.

## The planning conversation (M0 → M6)

```
M0  Pre-flight discovery — project dir, agent scope, existing state, entry point  (mechanical, silent)
M0.5  Scope-confirmation hard gate — prose-first briefing, user confirms / redirects / expands  ◀── ALL entry points & modes, including --auto
M1  Constitution & Frame — operating-manual content
M2  Goal-Backward Scope — must-be-TRUE / must-EXIST / CRITICAL vs nice-to-have, hardest unknown, derailment risks, non-goals
M3  Sequence with Size Discipline — milestones with 2-3 tasks each, ~50% context bar, dependencies mapped, risk-first ordering
M4  Quality Gates — per-milestone ACs, validation commands, stop conditions, Definition of Done
M5  Doc-Set Recommendation — complexity routing (lite / standard / full), per-doc rationale, user_approval hard gate
M6  Execute the plan's first milestone — write the approved doc set per the canonical structure
```

Without `--auto`, all M1–M5 phases require explicit user response before the conversation advances. A `<system-reminder>` saying "don't ask clarifying questions" does not suppress M1–M5 prompts — it only suppresses trivial in-execution confirmations.

`--auto` is the only mode that bypasses M1–M5 dialogue. **It does NOT bypass M0.5.** Even in `--auto`, the scope confirmation fires once.

`--assessment` and `--validate` short-circuit early: after M0 mechanical discovery, route directly to the assessor (for `--assessment`) or the validator suite (for `--validate`). M0.5 does not fire and M1–M5 do not run.

## What gets written at M6

Per the [canonical doc structure](../../docs/doc-conventions.md):

- **Operating manual** — `CLAUDE.md` and/or `AGENTS.md` per agent scope (Claude-only / Codex-only / both)
- `docs/vision.md` — what success looks like, audience, non-goals
- `docs/architecture.md` — system shape, key components, integration points
- `docs/planning/current.md` — current milestone, tasks with acceptance criteria, validation commands
- `docs/status.md` — scaffold only (rad-session populates from evidence)
- `docs/decisions/NNNN-*.md` — sequence-numbered ADRs (default mode only; `--auto` writes `docs/planning/proposed-decisions.md` instead)
- `docs/roadmap.md` — optional, depending on doc-set complexity
- `.rad/profile` — project-scoped mentor vs dev mode preference

**Not written by `/plan` (single-writer rule):**
- `docs/status.md` — owned by rad-session `/wrapup` (populates from evidence)

## Pipeline with rad-brainstormer

`rad-planner` and [`rad-brainstormer`](../rad-brainstormer/) chain. They own different phases:

| Phase | Plugin | Owns | Output |
|---|---|---|---|
| **Ideation** (divergent) | `rad-brainstormer` | Exploring the problem, generating options, stress-testing assumptions | A decided idea + rough direction |
| **Design** (post-ideation) | `rad-brainstormer:design-sprint` | Architecture, components, data flow, API design, error handling, testing strategy | A reviewable design spec |
| **Planning** (pre-code) | `rad-planner:plan` | Five-phase plan-first conversation, doc-set recommendation, mechanical validation | An approved plan + the canonical doc set |
| **Code** | your tools of choice | Implementation | Working software |

If you come in with a clear idea, start with `/rad-planner:plan`. If the idea is fuzzy, start with `/rad-brainstormer:brainstorm-session` first.

## Relationship to built-in Plan Mode

Claude Code ships with [Plan Mode](https://docs.claude.com/en/docs/claude-code/) (Shift+Tab toggle, `--permission-mode plan`) which restricts to read-only tools. rad-planner does not replace it; the two compose:

- **Plan Mode** handles read-only enforcement at the runtime level (no Edit/Write/Bash).
- **rad-planner** adds the conversation + the doc-set artifact + the mechanical validators.

`/plan --assessment` and `/plan --validate` are safe to run inside Plan Mode (no writes). The full `/plan` workflow needs Write at M6 to emit the doc set.

## Reference files

The `references/` directory contains the knowledge base agents and skills load on demand:

| Reference | Content |
|---|---|
| `golden-path-matrix.md` | AI-native proficiency tiers + project-type stack recommendations (date-stamped, opinionated) |
| `anti-patterns.md` | Documented "Do Not Do" constraints (some are opinions with thresholds — clearly marked) |
| `failure-state-template.md` | Triple-component validation (Action → Validation → Rollback) |
| `tdd-constraints.md` | Red-Green-Refactor + mutation testing requirements |
| `context-management.md` | Document & Clear triggers, handoff protocol, shared checkpoint schema |
| `subagent-prompts/stack-eval.md` + `.schema.json` | Stack-advisor dispatch template + JSON Schema |
| `subagent-prompts/risk-assessment.md` + `.schema.json` | Risk-assessor dispatch template + JSON Schema |

## Fixtures

Two test fixtures under `fixtures/` exercise the validators end-to-end. Use them to see what passing artifacts look like, or to test validator failure modes by introducing a contradiction or stripping a section.

## Pair with rad-session

`rad-planner` owns the plan and the strategic docs; [`rad-session`](../rad-session/) owns each session's lifecycle and `docs/status.md` (the evidence of what's actually been built). They share the [canonical doc structure](../../docs/doc-conventions.md) and the sectioned-writer rule that keeps the operating manual coherent across both. Use them together for the full lifecycle; each one works standalone.

## Requirements

- **Python 3.8+** for the validator scripts. If unavailable, the skills surface a fallback: manual review using the documented checklists. Honest framing: without Python, the "validators" reduce to "templates the model is asked to follow."
- Optional: `pip install jsonschema` for fuller JSON Schema draft-07 coverage in `validate-json.py`. Pure-stdlib subset is used when not installed.

## License

Apache-2.0

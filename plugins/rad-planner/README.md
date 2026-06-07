# rad-planner

Plan a project before you write code. rad-planner runs a rigorous planning conversation and produces one thing: a plan a fresh agent can execute. It is **strictly a planner** — it writes the plan and nothing else.

> **v5.0 — reboot.** Stripped the v4.x canonical doc tree, scope gates, depth heuristics, and doc-org validators that had buried the planning method under document machinery. Restored the v3.0 conversation's rigor, kept the genuinely-good ideas (goal-backward decomposition, size discipline), and reshaped the output to a single lean plan. Decoupled from rad-session: no operating-manual or status-doc writes, no cross-plugin handoff file.

## What makes it more than a generic planner

Claude can already write a plan. rad-planner's method is **risk-first, adversarially-reviewed, and mechanically-validated** — passes a single-shot plan doesn't get:

- **Assumption surfacing** — makes the invisible project truths explicit before sequencing anything.
- **Codegen-aware stack evaluation** — `stack-advisor` picks tech for how accurately an LLM can implement it (the AI-native Golden Path matrix), not just general fit.
- **Goal-backward decomposition + risk-first sequencing** — solve the hardest unknown first; small shippable milestones (size discipline).
- **Mechanical validation** — `plan-lint.py` is a real pass/fail check on the plan (required sections, per-task fields, dependency resolution + cycles, vague language), not the model grading its own homework.
- **Adversarial review** — the `risk-assessor` agent checks the plan against 14 documented anti-patterns and architecture concerns, returns APPROVE / REVISE / RETHINK, iterates, and escalates to brainstorming when the architecture itself is broken.
- **Failure-state rigor** — every task carries a rollback, not just a happy path.

## Output — one file

The planner writes a single plan at `docs/plan.md` (created fresh, or an existing plan updated in place). Everything folds into it — objective, scope, assumptions, stack, milestones, tasks, checkpoints, risks, validation, stop conditions. No strategic-doc tree.

When the conversation surfaces something that belongs in a **durable doc the planner does not own** (a PRD / product contract, a decision log, an architecture reference), it does *not* write that doc. It writes a paste-ready `docs/[date]-update-prompt.md` you run in Claude or Codex to apply the change, and points `plan.md` at it. Durable docs stay under your control.

## Skills

| Skill | Trigger | What it does |
|---|---|---|
| `/rad-planner:plan` | "plan my project", "create an implementation plan", "help me architect this", "break this into tasks" | The six-phase planning conversation → `docs/plan.md` (+ a conditional update-prompt). |
| `/rad-planner:review-plan` | "review my plan", "audit this plan", "is this plan complete" | Two-layer quality audit of an existing plan: mechanical lint + adversarial risk review. |

## Agents

| Agent | Role |
|---|---|
| **stack-advisor** | Tech-stack evaluation for codegen accuracy; live version checks via Context7 / WebSearch. |
| **risk-assessor** | Adversarial plan review — anti-patterns, architecture, rollback quality, checkpoint placement, TDD. Runs `plan-lint.py` first to skip mechanical checks. |

## The planning conversation

```
1  Discovery        — greenfield vs existing-codebase detection, strategic questions, assumption capture
2  Stack Evaluation — stack-advisor + Golden Path matrix (when a stack decision is in play)
3  Build the Plan   — goal-backward decomposition, risk-first sequencing + size discipline,
                      every task specced to execution-readiness (six fields)
4  Validate & Risk  — plan-lint.py (mechanical) then risk-assessor (adversarial, iterative)
5  Review           — human approves; never self-approves
6  Export           — write plan.md; surface durable changes into the update-prompt
```

If the idea is still fuzzy, the planner stops and routes you to [`rad-brainstormer`](../rad-brainstormer/) — planning assumes the *what* is decided and plans the *how* and *order*.

## Mechanical validators (scripts/)

Pure-stdlib Python 3.8+. Human-readable text by default, `--json` on request. Exit 0 clean, 1 issues found, 2 script error.

| Script | What it checks |
|---|---|
| `plan-lint.py` | `plan.md` — required sections, per-task field presence (Objective, Files, Depends on, Done when, Validate, Rollback), dependency resolution + cycles, vague-language detection. |
| `validate-json.py` | JSON Schema validator for the `stack-advisor` / `risk-assessor` output contracts; re-prompts the agent once on schema failure. |

## Pipeline with rad-brainstormer

`rad-planner` and [`rad-brainstormer`](../rad-brainstormer/) own different phases:

| Phase | Plugin | Output |
|---|---|---|
| **Ideation** (divergent) | `rad-brainstormer` | A decided idea + rough direction |
| **Design** (post-ideation) | `rad-brainstormer:design-sprint` | A reviewable design spec |
| **Planning** (pre-code) | `rad-planner:plan` | An approved `plan.md` |
| **Code** | your tools of choice | Working software |

Clear idea → start with `/rad-planner:plan`. Fuzzy idea → start with `/rad-brainstormer:brainstorm-session`.

## Relationship to built-in Plan Mode

Claude Code ships with [Plan Mode](https://docs.claude.com/en/docs/claude-code/) (read-only enforcement). rad-planner composes with it: Plan Mode handles read-only enforcement at the runtime level; rad-planner adds the conversation, the method, and the mechanical validation. The full `/plan` workflow needs Write to emit `plan.md`.

## Reference files

Loaded on demand by the skills and agents:

| Reference | Content |
|---|---|
| `plan-template.md` | The `plan.md` structure + update-prompt template + enforced rules |
| `golden-path-matrix.md` | AI-native proficiency tiers + project-type stack recommendations |
| `anti-patterns.md` | Documented planning anti-patterns (some are opinions with thresholds — marked) |
| `failure-state-template.md` | Triple-component validation (Action → Validation → Rollback) |
| `tdd-constraints.md` | Per-task test-strategy requirements |
| `context-management.md` | Document & Clear triggers and milestone-boundary discipline |
| `subagent-prompts/stack-eval.md` + `.schema.json` | `stack-advisor` dispatch template + JSON Schema |
| `subagent-prompts/risk-assessment.md` + `.schema.json` | `risk-assessor` dispatch template + JSON Schema |

A real, lint-clean example plan lives in `examples/plan.md` (with a companion `examples/2026-06-06-update-prompt.md`).

## Requirements

- **Python 3.8+** for the validator scripts. Without it, the skills fall back to manual review against the documented checklists — honestly, "validators" reduce to "templates the model is asked to follow."
- Optional: `pip install jsonschema` for fuller draft-07 coverage in `validate-json.py`. A pure-stdlib subset is used otherwise.

## License

Apache-2.0

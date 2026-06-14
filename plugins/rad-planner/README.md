# rad-planner

Plan a project before you write code — and re-plan it as reality unfolds. rad-planner is built for solo developers who aren't formally trained engineers: it interrogates you until it actually understands what you're building, then produces a plan that a moderately experienced vibe coder can read **and** a coding agent can execute. It is **strictly a planner** — it never writes implementation code.

## What makes it more than a generic planner

Claude can already write a plan. rad-planner's method is **interview-driven, risk-first, adversarially-reviewed, and mechanically-validated** — passes a single-shot plan doesn't get:

- **The grilling** — a structured discovery interview: eight coverage areas (end goal, users, MVP, success criteria, constraints, assets, exclusions, danger zones), each driven to *settled* or *explicitly unknown*; the project mirrored back for correction; assumptions proposed for confirm/deny instead of asking you to invent them. Capped at 3 rounds so it stays fast.
- **The release ladder** — every plan anchors to your end goal via a Now / Next / Later release map. Detail decays with distance by design: only "Now" gets task specs; speccing distant versions is fake precision.
- **Written for two readers** — a plain-language layer (how-to-read note, release map, *After this ships* lines per milestone) for you; six-field task blocks for the coding agent.
- **Codegen-aware stack evaluation** — `stack-advisor` picks tech for how accurately an LLM can implement it (the AI-native Golden Path matrix), not just general fit.
- **Goal-backward decomposition + risk-first sequencing** — solve the hardest unknown first; small shippable milestones (size discipline).
- **Mechanical validation** — `plan-lint.py` is a real pass/fail check on the plan (required sections, per-task fields, dependency resolution + cycles, vague language), not the model grading its own homework.
- **Adversarial review** — the `risk-assessor` agent checks the plan against 14 documented anti-patterns and architecture concerns, returns APPROVE / REVISE / RETHINK, iterates, and escalates to brainstorming when the architecture itself is broken.
- **Failure-state rigor** — every task carries a rollback, not just a happy path.

## Output

The plan lives in a single file, `docs/plan.md` — objective + end goal, release map, scope, assumptions, stack, milestones, tasks, checkpoints, risks, validation, stop conditions. No strategic-doc tree. At re-plan, shipped work moves to a `## Shipped` section — history is preserved, never deleted.

**The PRD exception:** when `docs/prd.md` is missing or a skeleton, the planner offers to draft it — each section written from *your own interview answers* and applied only on your per-section confirmation. After that birth, the PRD is yours (and rad-repo-manager keeps it fresh); the planner never edits an existing PRD. Changes to other durable docs (decision log, architecture) are never written directly — they go into a paste-ready `docs/[date]-update-prompt.md` you run in Claude or Codex, with a pointer in `plan.md`.

## Skills — two doors in, one maintained plan

| Skill | Trigger | What it does |
|---|---|---|
| `/rad-planner:plan` | "plan my project", "create an implementation plan", "break this into tasks" | **Door 1 — greenfield or clear next effort.** The six-phase conversation: interview → stack → build → validate & risk → review → export. Offers a quick path (single feature: skip the stack agent, single risk pass) or full path — your choice, asked once. |
| `/rad-planner:rescue` | "this repo is a mess", "help me out of this", "I don't know where this stands" | **Door 2 — project in an unclear state.** Read-only archaeology (code + git evidence) → evidence-led interview (keep/cut/unknown per piece) → PRD from your answers → a fresh release-map plan starting from where the project actually is. Assesses and plans; never fixes, runs, or deletes code. |
| `/rad-planner:replan` | "update the plan", "we shipped the MVP — what's next", "the plan is out of date" | Evidence-based plan update: marks shipped work from git + handoff (moved to `## Shipped`, never deleted), re-baselines the rest, pulls the next horizon into detail when "Now" ships. Single risk pass; your approval gates everything. |
| `/rad-planner:review-plan` | "review my plan", "audit this plan", "is this plan complete" | Two-layer quality audit of an existing plan: mechanical lint + adversarial risk review. |

## Agents

| Agent | Role |
|---|---|
| **stack-advisor** | Tech-stack evaluation for codegen accuracy; live version checks via Context7 / WebSearch. |
| **risk-assessor** | Adversarial plan review — anti-patterns, architecture, rollback quality, checkpoint placement, TDD. Runs `plan-lint.py` first to skip mechanical checks. |

## The planning conversation

```
1  Discovery        — evidence pre-fill (PRD/handoff/repo), then the structured interview:
                      eight coverage areas, mirror-back, ≤3 rounds, proposed assumptions.
                      Closes with the speed fork (quick vs full — you choose) and the
                      PRD gap check (draft it from your answers, per-section confirmed)
2  Stack Evaluation — stack-advisor + Golden Path matrix (full path, when a stack decision is in play)
3  Build the Plan   — release map (Now/Next/Later), goal-backward decomposition within "Now",
                      risk-first sequencing + size discipline, every task specced to
                      execution-readiness (six fields), plain-language layer for the human
4  Validate & Risk  — plan-lint.py (mechanical) then risk-assessor (adversarial; iterative
                      on the full path, single-pass on the quick path)
5  Review           — plain summary + release map + the embedded decisions first, detail after;
                      human approves; never self-approves
6  Export           — write plan.md; surface durable changes into the update-prompt
```

If the idea is still fuzzy, the planner stops and routes you to [`rad-brainstormer`](../rad-brainstormer/) — planning assumes the *what* is decided and plans the *how* and *order*. If the *project* exists but its state is the mystery, that's `/rad-planner:rescue`.

## Boundary with rad-repo-manager

[`rad-repo-manager`](../rad-repo-manager/) maintains what the planner produces: its `wrapup` makes one-line status touches to `plan.md` ("M2 shipped") and keeps the PRD fresh after the planner births it. When the divergence is structural — milestones obsolete, scope shifted, the next version due — that's `/rad-planner:replan`. The repo-manager maintains; the planner restructures.

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
| `discovery-interview.md` | The grilling protocol — eight coverage areas, mirror step, round caps, the speed fork and PRD gap check |
| `plan-template.md` | The `plan.md` structure (incl. release map + Shipped rules) + update-prompt template + enforced rules |
| `golden-path-matrix.md` | AI-native proficiency tiers + project-type stack recommendations |
| `anti-patterns.md` | Documented planning anti-patterns (some are opinions with thresholds — marked) |
| `failure-state-template.md` | Triple-component validation (Action → Validation → Rollback) |
| `tdd-constraints.md` | Per-task test-strategy requirements |
| `context-management.md` | Document & Clear triggers and milestone-boundary discipline |
| `subagent-prompts/stack-eval.md` + `.schema.json` | `stack-advisor` dispatch template + JSON Schema |
| `subagent-prompts/risk-assessment.md` + `.schema.json` | `risk-assessor` dispatch template + JSON Schema |

A real, lint-clean example plan lives in `examples/plan.md` (with a companion `examples/2026-06-06-update-prompt.md`).

## Requirements

- **Python 3.8+** for the validator scripts (`python3`, or `python` on Windows). Without it, the skills fall back to manual review against the documented checklists — honestly, "validators" reduce to "templates the model is asked to follow."
- Optional: `pip install jsonschema` for fuller draft-07 coverage in `validate-json.py`. A pure-stdlib subset is used otherwise.

## License

Apache-2.0

# AGENTS.md

**Status:** Active operating entrypoint. Keep this file short.

This file tells coding and review agents how to work in this repository. It is
not the product specification, plan, status log, or historical record.

Remote repository: <REMOTE_URL_OR_TBD>

## Active source of truth

Default cold-start read path:

1. `AGENTS.md`
2. `docs/prd.md`
3. `docs/plan.md`
4. `docs/handoff.md`

Conditional references (read only when the task touches the area):

- Decision conflict or active-rule lookup: `docs/reference/decision-log.md`.
- Architecture task: `docs/reference/architecture.md`, if present.
- Design task: `docs/reference/design.md`, if present.
- API/AI route task: `docs/reference/api-contracts.md`, if present.
- Build/release/deployment task: `docs/reference/commands.md`, if present.
- Known trap/task pattern: `docs/reference/lessons-learned.md`, if present.
- Test strategy task: `docs/reference/testing.md`, if present.

Newly generated docs that aren't one of the above (a side brainstorm, a smoke-test
report, an AI-produced analysis) go in `docs/inbox/` to be filed later — never
scattered elsewhere.

Archive rule: do **not** read `docs/archive/` during normal work. Archive files
are historical context only and are not current authority unless the user
explicitly asks for historical context.

## Agent work modes

Pick the mode before working. If the user did not specify a mode, infer the
least risky mode from the request.

| Mode | Use when | Code changes? |
| --- | --- | ---: |
| `product_strategy` | The user asks whether the product approach or user flow is right. | No |
| `architecture_review` | The user asks about source-of-truth conflicts, repo structure, system risks, stale docs, or contradictory implementation. | No |
| `documentation` | The user asks to consolidate, archive, rewrite, or simplify docs. | Docs only |
| `implementation` | The user asks for scoped application changes. | Yes, within scope |
| `review` | The user asks to assess a branch, PR, agent output, or recent commits. | No by default |
| `wrapup` | The user asks for final status, handoff, or validation summary. | Handoff doc only |

Do not default to implementation when the user is asking whether the approach is
wrong. Do not patch one symptom when the failure indicates a product-contract or
source-of-truth problem.

## Protected changes

Stop and ask before touching:

- Auth, billing, schema migrations, or access-control rules.
- New dependencies.
- API/provider activation or external-contract changes.
- Deployment behavior, environment variables, health checks, or release routing.
- Any rename/move that could break scripts, tests, imports, docs, or external systems.
- <PROJECT_SPECIFIC_PROTECTED_AREAS>

## Engineering baseline

- <PROJECT_CONVENTIONS — e.g. language/strictness, naming, commit style, test colocation>

## Documentation rules

- Do not duplicate durable facts across active docs. Put each durable fact in one home and link to it elsewhere.
- `AGENTS.md` contains operating rules only.
- Product behavior belongs in `docs/prd.md`.
- The plan (scope, milestones, tasks) belongs in `docs/plan.md` (owned by `/rad-planner:plan`).
- Current task / status / resume point belongs in `docs/handoff.md`.
- Active decisions belong in `docs/reference/decision-log.md`.
- Newly generated docs awaiting filing go in `docs/inbox/`.
- Historical summaries, old plans, smoke notes, superseded decisions, and audit handoffs belong in `docs/archive/` with an archive banner.
- Do not edit archived files except to add an archive/supersession banner or move them.

## Validation commands

For application changes, run the project's standard validation before push:

```
<PROJECT_VALIDATION_COMMANDS — e.g. lint, type-check, test, build>
```

For documentation-only changes, run at minimum:

```
git diff --check
git status --short
```

If documentation changes alter repo policy, read-order, commands, or references
used by scripts/tests, run enough validation to prove references were not broken.

## Definition of done

A task is done only when:

- The selected work mode was appropriate.
- The change follows the current product contract (`docs/prd.md`) and the plan (`docs/plan.md`).
- The diff stays within the requested scope.
- Protected changes were not made without approval.
- Relevant validation was run and summarized.
- Remaining risks, unknowns, and follow-up tasks are stated plainly.

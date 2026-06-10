# Plan Output Template — single-file `plan.md`

rad-planner emits **one** plan file: `docs/plan.md` (created if absent; updated in place if a plan already exists there or at a detected legacy path). Everything the planning conversation produces — objective, end goal, release map, scope, assumptions, stack, milestones, tasks, checkpoints, risks — folds into this one file as sections. No separate `tasks.md`, no strategic-doc tree. It is written for two readers at once: the plain-language layer (How-to-read note, Release map, *After this ships* lines) for the human; the six-field task blocks for the coding agent.

A second file, `docs/[date]-update-prompt.md`, is written **only when** the conversation surfaces a change that belongs in a durable doc the planner does not own (PRD / product contract, decision log, architecture). See "Update-prompt template" below.

`plan.md` is validated mechanically by `scripts/plan-lint.py` after every write.

---

## `plan.md` template

```markdown
# Plan: [Project Name]

**Status:** [DRAFT | APPROVED | IN PROGRESS | COMPLETED]
**Updated:** [YYYY-MM-DD]
<!-- Add the next line ONLY when an update-prompt was written this session: -->
**Pending durable-doc updates:** see `[YYYY-MM-DD]-update-prompt.md`

> **How to read this plan:** the Release map says where this effort fits on the road
> to the end goal. Milestones are the chunks of work, each with an *After this ships*
> line saying what you can do once it lands. The task blocks underneath are precise
> instructions for the coding agent — you don't need to parse every field. Stop
> conditions are where the agent must halt and ask you instead of guessing.

## Objective

[1–2 sentences: what this builds and why now. The "why now" separates a real
project from a someday-maybe.]

**End goal:** [One sentence — the truly-done state from Discovery, beyond this
plan's MVP. Anchors the Release map's "Later".]

## Release map

[Detail decays with distance — by design. Only "Now" gets milestones and tasks
below; speccing distant versions in task detail is fake precision. Pulling "Next"
into detail is a /rad-planner:replan event when "Now" ships.]

- **Now — [MVP/Beta name] (this plan):** [one sentence — what ships and for whom]
- **Next — V1:** [milestone-level outline, 3–6 bullets; no task specs]
  - [outline bullet]
- **Later — the end goal:** [theme bullets anchored to the End goal line]
  - [theme bullet]

## Scope

**In scope:**
- [Capability the plan commits to]

**Out of scope / non-goals:**
- [Deliberate exclusion — not just unattended, explicitly NOT building this]

## Key assumptions

[Non-obvious truths about the project's reality that wouldn't be evident from the
code. One-line entries. When an assumption invalidates, strike it through rather
than deleting — the audit trail matters.]

- [YYYY-MM-DD] [e.g. "No real users yet — backward-compat can break until M3."]

## Stack

[Only when a stack evaluation ran this session. Brief — language, framework, data
store, key libraries. The full rationale is durable; if it warrants recording,
surface it into the update-prompt, do not expand it here.]

## Milestones

| # | Milestone | Goal (what it ships) | Key artifacts |
|---|---|---|---|
| M1 | [theme] | [coherent shippable outcome] | [files / components] |

[Risk-first ordering: the hardest unknown is solved first. Size discipline:
aim for 2–3 tasks per milestone; a milestone over 5 tasks is a split candidate.]

## Tasks

### M1 — [theme]

*After this ships: [plain English — what the user can do or see once M1 lands.]*

- **T1 — [title]**
  - **Objective:** [1–2 sentences]
  - **Files:** [files likely created / modified]
  - **Depends on:** [none | T-x, T-y]
  - **Done when:** [specific, measurable — not "works"]
  - **Validate:** `[runnable command or verifiable condition]`
  - **Rollback:** `[how to revert to last known-good]`

[Repeat per task. Every task carries all six fields — plan-lint enforces it.]

## Checkpoints

### After M1

- **Gate:** T1–Tn complete and validated
- **Validate:** `[command that proves the milestone]`
- **Rollback:** `[reset to pre-M1 known-good]`

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| [risk] | [Low/Med/High] | [Low/Med/High] | [specific mitigation] |

## Validation

[The commands that prove the whole plan is done. Concrete, pass/fail.]

## Stop conditions

[When the executing agent must halt and ask rather than guess — e.g. requirement
conflict, change touches auth/billing/data model, validation fails and the fix
needs scope expansion.]
```

---

## Shared rules (enforced)

Every task in `## Tasks` MUST carry all six fields: **Objective, Files, Depends on, Done when, Validate, Rollback**. `plan-lint.py` flags any task missing one.

1. **Dependencies reference task IDs** (`T1`, `T2`) and must resolve to a task that exists in the file — no phantom dependencies, no cycles. Checked by `plan-lint.py`.
2. **`Validate` and `Done when` must be runnable or verifiable** — vague language ("verify it works", "looks right", "tbd", "etc.") is flagged.
3. **`Rollback` must restore a known-good state.** Judgment — `risk-assessor` checks quality.
4. **A checkpoint follows every milestone**, with its own gate / validate / rollback (the failure-state triple from `references/failure-state-template.md`). Placement judged by `risk-assessor`.
5. **Assumption invalidations use strikethrough**, never deletion.
6. **Task-level detail exists only for the "Now" horizon.** "Next" stays a milestone outline; "Later" stays themes. `/rad-planner:replan` pulls the next horizon into detail when "Now" ships.
7. **Shipped work is preserved, never deleted.** At re-plan, shipped task blocks move to a `## Shipped` section (outside `## Tasks`, so the linter doesn't re-validate history). Remaining tasks that depended on a shipped task get `Depends on: none — predecessor shipped` (do not keep the old task ID in the field; the linter would read it as a phantom dependency).

| Rule | Enforced by |
|---|---|
| Required sections present (incl. Release map) | `plan-lint.py` |
| Per-task field presence | `plan-lint.py` |
| Dependency resolution + no cycles | `plan-lint.py` |
| Vague-language detection | `plan-lint.py` |
| Rollback correctness, checkpoint placement, anti-pattern coverage | `risk-assessor` agent (judgment) |
| Horizon detail-decay, shipped-history preservation | skill procedure (`plan` / `replan`) |

---

## Update-prompt template

Written to `docs/[date]-update-prompt.md` **only** when the conversation surfaced a durable-doc change. `plan.md` gets a one-line `**Pending durable-doc updates:**` pointer (above). One source of truth: the surfaced items live here, not duplicated into `plan.md`.

```markdown
# [YYYY-MM-DD] — Doc update prompt

Generated by rad-planner. Paste into Claude or Codex to reconcile durable docs
with decisions made during this planning session. Delete once the updates land.

---

During planning on [YYYY-MM-DD] we made changes that affect durable docs the
planner does not own. Please:

1. **[path, e.g. docs/prd.md]** — [what to record, and why; mark any superseded
   wording].
2. **[path, e.g. docs/reference/decision-log.md]** — [active decision to add;
   note whether a detailed ADR is warranted].
3. **[path, e.g. docs/architecture.md]** — [implication to capture].

After updating, confirm each file changed and delete this prompt.
```

**Agent-agnostic.** The prompt names files and changes in plain language — it runs in Claude, Codex, or any agent. The planner never writes these durable docs itself; it only writes this prompt and the `plan.md` pointer.

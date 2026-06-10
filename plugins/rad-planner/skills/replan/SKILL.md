---
name: replan
description: >
  This skill should be used when the user says "replan", "update the plan",
  "re-baseline the plan", "the plan is out of date", "we shipped the MVP — what's
  next", "mark this milestone done", "the plan doesn't match reality anymore",
  "pull the next version into the plan", "adjust the plan", or when an existing
  `docs/plan.md` has diverged from what actually got built. Evidence-based plan
  update: reads git history + docs/handoff.md to mark shipped work (history
  preserved, never deleted), re-baselines remaining tasks, and pulls the next
  release-map horizon into detailed milestones when the current one is done.
  Re-lints and runs a single risk pass; nothing is final until the user approves.
argument-hint: "[optional: what changed, e.g. 'M2 shipped' or 'we dropped the API idea']"
user-invocable: true
allowed-tools: Read Glob Grep Agent Write Bash AskUserQuestion
---

# Replan — evidence-based plan update

Bring `docs/plan.md` back in line with reality without losing history or re-running
the whole planning conversation. Real projects diverge from the plan by milestone 2 —
this is the sanctioned way to absorb that, instead of hand-editing the plan or
starting over.

**Boundary with rad-repo-manager:** its `wrapup` makes one-line status touches ("M2
shipped", stamp the date) scoped to a session. `replan` is the *structural* event —
re-sequencing, re-scoping, pulling the next horizon into detail. Wrapup maintains;
replan restructures.

**CRITICAL: No implementation code, no source files. The only files written are
`docs/plan.md` and (conditionally) `docs/[date]-update-prompt.md`.** An existing PRD
is never edited — contradictions surface into the update-prompt.

## 1. Gather evidence — not memory

Read in one parallel batch: `docs/plan.md`, `docs/handoff.md`, `docs/prd.md` (if
present). Then git, scoped by the plan's `**Updated:**` date:

```bash
git log --oneline --since="<plan Updated date>"
git diff --stat $(git rev-list -1 --before="<plan Updated date>" HEAD)..HEAD
git status --short
```

If no plan exists, stop and recommend `/rad-planner:plan` (fresh) or
`/rad-planner:rescue` (project in an unclear state).

## 2. Classify, against evidence

For each milestone and task in the plan, classify from the diff, commit messages,
file existence, and the handoff's validation record:

- **Shipped** — the artifacts exist and validation evidence supports it.
- **Partially done** — some artifacts exist; name what's missing.
- **Not started** — no evidence.
- **Obsolete** — the work no longer makes sense given what actually happened.

Where the evidence is ambiguous, ask — one batched set of questions
(AskUserQuestion), not a drip. Never silently guess a milestone's fate.

## 3. Present the assessment — plain language first

Before touching the file:

```text
Plan vs reality:
Shipped:        <milestones/tasks, with the evidence in one clause each>
Partially done: <what's missing, in user terms>
Not started:    <...>
Looks obsolete: <what and why — needs your confirmation>
Drifted:        <anything built that the plan never mentioned>
```

Confirm the obsolete calls and any surprises with the user before restructuring.

## 4. Restructure — history preserved, never deleted

On the user's go-ahead, update `docs/plan.md`:

1. **Shipped milestones** — mark ✅ in the Milestones table; **move** their task
   blocks to a `## Shipped` section at the end of the file (create it if absent,
   newest first). Never delete them. `## Shipped` lives outside `## Tasks`, so the
   linter doesn't re-validate history.
2. **Dependency rewrite** — remaining tasks that depended on a moved task get
   `Depends on: none — predecessor shipped`. Do **not** leave the old task ID in the
   field: the linter reads any `T<n>` in `Depends on` as a live reference and will
   flag a phantom dependency.
3. **Partially done** — split: the done part moves to `## Shipped` as a note; the
   remainder becomes a properly specced task (all six fields) with a fresh ID.
4. **Obsolete** — strike through in the Milestones table with a one-line reason;
   move its task blocks to `## Shipped` under an "Obsolete —" note. Same dependency
   rewrite.
5. **Horizon pull** — if the "Now" horizon is substantially shipped, promote "Next"
   from the Release map into detailed milestones and six-field tasks (goal-backward,
   risk-first, 2–3 tasks per milestone — same discipline as `plan`), and refresh the
   Release map: the new work becomes "Now", "Later" themes feed the new "Next".
   Confirm the promoted scope with the user — this is the moment the V1 outline
   becomes real commitments.
6. **Assumptions** — strike through any the evidence invalidated (never delete);
   propose new ones from what was learned, confirm/deny.
7. Set `**Status:** DRAFT`, stamp `**Updated:**` with today's date.

## 5. Validate, review, approve

Run the linter (use `python3`, or `python` on Windows):

```bash
python3 ${plugin_root}/scripts/plan-lint.py docs/plan.md --json
```

Fix CRITICAL/HIGH. Then a **single** risk pass — dispatch `risk-assessor`
(`references/subagent-prompts/risk-assessment.md`, `max_iterations: 1`), focused on
the restructured and newly promoted work; note in the dispatch that `## Shipped` is
history and out of scope. Fix blocking issues once; surface the rest.

Present per `plan`'s Phase 5 shape (plain summary → release map → decisions → detail).
On approval: flip to `APPROVED`, re-stamp, write the update-prompt if anything durable
surfaced (e.g. the PRD now describes behavior that shipped differently).

## What this skill does NOT do

- Does not write or edit source files, run tests, or fix anything in the code.
- Does not delete history — shipped/obsolete work moves to `## Shipped` or is struck
  through, always recoverable.
- Does not edit an existing `docs/prd.md` or other durable docs — surfaces changes
  via the update-prompt.
- Does not re-run full Discovery — that's `plan` (fresh) or `rescue` (unclear state).
- Does not auto-approve — the restructured plan is DRAFT until the user says lock it.

## Key references

- `references/plan-template.md` — structure, the `## Shipped` rule, dependency-rewrite rule
- `references/subagent-prompts/risk-assessment.md` — single-pass dispatch
- `scripts/plan-lint.py` — re-run after every restructure

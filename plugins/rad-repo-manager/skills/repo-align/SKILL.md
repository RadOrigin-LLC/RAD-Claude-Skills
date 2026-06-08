---
name: repo-align
description: >
  This skill should be used when the user says "repo-align", "align the repo",
  "clean up the repo", "check for drift", "is the repo in good shape", "find
  contradictions", "what's gotten messy", "doc cleanup", "are my docs consistent",
  "tidy up the docs", or when startup flagged drift. The deep, opt-in alignment
  pass: finds documentation drift (duplicate authorities, stale docs,
  contradictions, scope-creep, loose/misplaced docs, broken read paths) and proposes
  fixes interactively. Proposes before acting on every judgment call; preserves
  history with git mv; never silently merges, deletes, or archives.
argument-hint: "[--report-only]"
user-invocable: true
allowed-tools: Read Glob Grep Bash Write Edit AskUserQuestion
---

# Repo Align — bring an existing repo back to the compact model

The deep, opt-in pass. Go deep enough to find documentation drift, surface it in plain
English, and **propose one disposition per judgment call — always confirmed before
acting. Never silently merge, delete, archive, or rewrite.**

This can take a minute. The fast everyday skills are `startup`/`wrapup`; this is the
periodic alignment. With `--report-only`, do steps 1–3 (find and present) and stop —
propose no changes.

## The model you're aligning to

Active read path (the four core docs, declared in `AGENTS.md`):

1. `AGENTS.md` — operating manual / how we work
2. `docs/prd.md` — durable product authority
3. `docs/plan.md` — the plan (owned by `/rad-planner:plan`)
4. `docs/handoff.md` — the short resume snapshot

Conditional (read only when the task touches them): `docs/design.md`,
`docs/reference/*` (closed catalog), `docs/README.md`. `docs/archive/*` is history, not
read by default. READMEs explain the repo to humans — they are **not** agent
instruction authority.

## 1. Run the mechanical scans

These are the drift signals — pure-stdlib, advisory. Capture each JSON; they surface
**candidates**, not verdicts. Your judgment decides which are real.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/repo-scan.py . --json --no-record      # floating/misplaced docs, active-set growth, AGENTS.md bloat
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doc-contradiction.py . --json          # plan builds something the PRD lists as a non-goal (scope-creep)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doc-redundancy.py . --json             # the same fact stated in two active docs
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit-user-content.py . --json         # AGENTS.md orphan terms + dead paths
```

(If Python 3 is unavailable, do the same checks by reading the docs directly and say
the mechanical pass was skipped.)

## 2. Read the active core and judge

Read `AGENTS.md`, `docs/prd.md`, `docs/plan.md`, `docs/handoff.md`. Then search for
repo-management and doc files that may be drifting:

- `CLAUDE.md`, `GEMINI.md`, `README.md`
- `docs/status.md`, `docs/roadmap.md`, `docs/implementation-plan.md` (off-model — should not exist)
- `docs/design.md`, `docs/reference/*`, `docs/archive/*`
- loose `*.md` outside the expected locations; `docs/inbox/*` (a retired tier — file its contents out)
- folder-specific `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` (likely confuse agents)

Identify: duplicate authorities, stale docs, pointer chains, missing core docs,
contradictory read paths, docs that belong in archive or the reference catalog,
root-README content that has become stale status, and off-model status/roadmap docs.

The question that matters for fuzzy findings: **does this mean a decision is needed?**
A prd↔plan contradiction usually does — frame it as a decision for the user, not an
error to silently patch.

## 3. Present findings — plain language, grouped

```markdown
# Repo alignment

## Needs a decision
- The plan builds offline mode, but the PRD lists offline as a non-goal. Which wins?

## Active-doc conflicts / redundancy
- `docs/prd.md` and `AGENTS.md` both define the validation steps — pick one home.

## Off-model docs
- `docs/status.md` exists — this model has no status doc; fold its live bits into docs/handoff.md, archive the rest.

## Loose / misplaced docs
- `smoke-2026-05-30.md` (repo root) — a smoke-test report sitting loose.
- `docs/inbox/brainstorm-routing.md` — inbox is retired; file this out.

## Pointer / read-path problems
- `AGENTS.md` links `docs/old-architecture.md` — file doesn't exist.

## Missing core docs
- `docs/handoff.md` is absent.

## Suggested actions
[per-item dispositions below]
```

No jargon, no validator names in the user-facing report — describe the problem and the
fix in words a non-coder follows.

## 4. Offer fixes — closed disposition set, confirmed per item

For each drifting or misplaced doc, propose ONE disposition and ask before acting
(AskUserQuestion, or a clear yes/no per item):

1. **Fold** — merge durable content into a core/reference doc, then archive the original.
2. **Extract** — pull action items into `docs/plan.md` or `docs/reference/lessons-learned.md`, then archive the original.
3. **Promote** — it's a real reference doc → move to a `docs/reference/` catalog slot (decision-log, architecture, api-contracts, commands, lessons-learned, testing) or to top-level `docs/design.md`.
4. **Archive** — historical / done → `git mv` into `docs/archive/`, add the archive banner.
5. **Relocate** — a misplaced core doc → move to its proper home.

Rules:

- **Propose, never auto-act.** Every fold/extract/move/delete waits for the user's yes.
- **Preserve history:** move tracked files with `git mv`, never delete-and-recreate.
- **No doc-type classifier.** Suggest a disposition with a one-line reason; the user picks.
- **Keep `CLAUDE.md`/`GEMINI.md` as thin `@AGENTS.md` pointers** — if one has grown its own content, propose folding that content into `AGENTS.md` and restoring the shim.
- After approved moves, **update the active pointers** so the default read path is still the four core docs.

## 5. Surface durable changes — don't write them

When a finding implies a change to a durable doc the manager doesn't own — `docs/prd.md`
(product behavior) or `docs/reference/decision-log.md` (a decision) — do **not** edit
those files. Describe the change in plain language and name the target file for the
user to apply (in Claude or Codex). The manager files and flags; the user owns product
and decisions.

## What this skill does NOT do

- Does not auto-apply judgment calls — every move/merge/delete/archive is user-confirmed.
- Does not write `docs/prd.md` or the decision log — surfaces the change instead.
- Does not create `docs/status.md`, `docs/roadmap.md`, `docs/implementation-plan.md`,
  loose root status/handoff/audit docs, or folder-specific agent files.
- Does not run on every session — it's the opt-in deep pass.

## References

- `${CLAUDE_PLUGIN_ROOT}/references/doc-model.md` — tiers, active core, reference catalog, filing
- `${CLAUDE_PLUGIN_ROOT}/scripts/` — the four drift-signal scans

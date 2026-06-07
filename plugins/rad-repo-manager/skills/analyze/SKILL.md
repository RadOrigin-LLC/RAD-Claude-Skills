---
name: analyze
description: >
  This skill should be used when the user says "analyze", "clean up the repo",
  "check for drift", "is the repo in good shape", "find contradictions", "what's
  gotten messy", "doc cleanup", "file these docs", "are my docs consistent", "tidy
  up", or when the health line from startup/wrapup went red. The deep, opt-in
  hygiene pass: scans for contradictions, redundancy, orphaned/stale content,
  scope-creep, operating-manual bloat, and loose/unfiled docs; then proposes fixes
  interactively in plain language. Proposes — never auto-acts.
argument-hint: "[--report-only]"
user-invocable: true
allowed-tools: Read Glob Grep Bash Write Edit AskUserQuestion
---

# Analyze — the deep clean, done with you

This is where the manager rolls up its sleeves. Run the full hygiene scan, surface
what's drifting in plain English, and offer to fix it — **one disposition per item,
always confirmed by the user. Never silently extract, fold, or file.**

This pass is opt-in and can take a minute. The fast everyday commands are
`startup`/`wrapup`; this is the periodic review.

## 1. Run the mechanical scans

Batch the validators (pure-stdlib, repointed at the 4-doc model). Capture each JSON:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/repo-scan.py . --json            # loose ends, inbox, floating docs, active-set size, AGENTS bloat
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doc-contradiction.py . --json    # prd non-goals vs what the plan builds (catches scope-creep)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doc-redundancy.py . --json       # same fact in two active docs
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit-user-content.py . --json   # AGENTS.md orphan terms + dead paths
```

These are deterministic signals. Token-overlap checks surface *candidates*, not
verdicts — your judgment decides which are real.

## 2. Judgment layer — decisions needed

Read the active core (`AGENTS.md`, `docs/prd.md`, `docs/plan.md`, `docs/handoff.md`)
and interpret the signals. The question that matters: **does a finding mean a
decision is needed?** A prd↔plan contradiction usually does — "the plan builds X, the
prd lists X as a non-goal; which is right?" Frame these as decisions for the user, not
as errors to silently patch.

## 3. Present findings — plain language, grouped

```markdown
# Repo analysis

**Health:** 🟢/🟡/🔴 — N loose ends

## Needs a decision
- The plan builds offline mode, but the PRD lists offline as a non-goal. Which wins?

## Contradictions / redundancy
- `docs/prd.md` and `AGENTS.md` both define the validation steps — pick one home.

## Loose & unfiled docs (M in inbox, K floating)
- `docs/inbox/brainstorm-routing.md` — looks like a side-brainstorm.
- `smoke-2026-05-30.md` (repo root) — a smoke-test report sitting loose.

## Operating-manual drift
- `AGENTS.md` mentions "Grounded Naturalist" — appears nowhere else; renamed/retired?
- `AGENTS.md` links `docs/old-architecture.md` — file doesn't exist.

## Suggested actions
[the per-item dispositions below]
```

No jargon, no validator names in the user-facing report — describe the problem and the
fix in words a non-coder follows.

## 4. Offer fixes — closed disposition set, confirmed per item

For each unfiled or drifting doc, propose ONE disposition and ask before acting
(AskUserQuestion, or a clear yes/no per item):

1. **Fold** — merge its durable content into a core/reference doc, then archive the original. (*side-plan → `docs/plan.md`*)
2. **Extract** — pull the action items into the plan or `lessons-learned`, then archive the original. (*smoke test, audit report*)
3. **Promote** — it's a real reference doc → move to a `docs/reference/` slot (catalog: decision-log, architecture, design, api-contracts, commands, lessons-learned, testing).
4. **Archive** — historical/done as-is → `git mv` into `docs/archive/`, add the archive banner.
5. **Relocate** — a misplaced core doc → move to its proper home.

Rules:
- **Propose, never auto-act.** Every fold/extract/move waits for the user's yes.
- **No doc-type classifier.** Suggest a disposition with a one-line reason; the user picks. Don't pretend to know "this is a smoke test" with certainty.
- **Off-catalog reference docs** (a `docs/reference/<x>.md` not in the catalog) are themselves a loose end — ask whether it's a standard slot or belongs in archive.
- Moves use `git mv` so history is preserved.

## 5. Surface durable changes — don't write them

When a finding implies a change to a durable doc the manager doesn't own — `docs/prd.md`
(product behavior) or `docs/reference/decision-log.md` (a decision) — do **not** edit
those files. Write a paste-ready `docs/inbox/[date]-update-prompt.md` describing the
change in plain language and naming the target file, for the user to apply (in Claude
or Codex). The manager files and flags; the user owns product and decisions.

## What this skill does NOT do

- Does not auto-apply anything — every change is user-confirmed.
- Does not write `docs/prd.md` or the decision log — surfaces an update-prompt instead.
- Does not classify doc types definitively — suggests, user decides.
- Does not run on every session — it's the opt-in deep pass.

## References

- `${CLAUDE_PLUGIN_ROOT}/references/doc-model.md` — tiers, active set, reference catalog, filing
- `${CLAUDE_PLUGIN_ROOT}/scripts/` — the four scans (repo-scan + three deep validators)

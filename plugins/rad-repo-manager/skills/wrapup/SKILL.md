---
name: wrapup
description: >
  This skill should be used when the user says "wrapup", "wrap up", "end of
  session", "save state", "handoff", "leave a clean stopping point", "I'm done for
  now", or "before I close". Writes a short, evidence-grounded docs/handoff.md
  (overwrite, not append) from git evidence — not chat memory — then reconciles
  the active core docs with this session's changes: applies scoped updates to the
  docs it owns (docs/plan.md, AGENTS.md operational sections) on a single OK, and
  for stale user-owned docs (prd/design/decision-log) drafts the exact edit and
  applies it only on explicit per-edit confirmation. Scoped to recent changes, not
  a deep audit. No status/roadmap/implementation-plan files, no auto-commit or
  push.
argument-hint: ""
user-invocable: true
allowed-tools: Read Glob Grep Bash Write Edit AskUserQuestion
---

# Wrapup — leave a clean handoff

End the session at a spot a fresh chat (or a post-compaction continuation) can resume
from cold. **Lean and evidence-grounded** — gather what actually changed, overwrite
the handoff snapshot, and stop. The deep pass is `/rad-repo-manager:repo-align`.

**Two hard rules:**

- **The one required output is an overwritten `docs/handoff.md`.** Always write it —
  even if nothing changed this session (then it just snapshots the current resting
  state). Never finish `wrapup` without having written it.
- **Do not run tests, builds, linters, or any command beyond the read-only git
  inspection in step 1.** `wrapup` only *records* validation that already ran this
  session; it never runs validation itself.

## Ownership boundary (read this first)

- `docs/plan.md` owns the durable roadmap, milestone scope, allowed/forbidden work,
  validation gates, and stop conditions.
- `docs/handoff.md` owns only the short resume snapshot for the next chat.
- **If a statement must stay true after the next session, it does not belong only in
  `docs/handoff.md`** — it belongs in `docs/plan.md`, `docs/prd.md`, `docs/design.md`,
  or a reference doc.
- Overwrite `docs/handoff.md` as a snapshot. Never append a log.

## 1. Gather evidence (not memory)

In one batch:

```bash
git status --short
git diff --stat
git log --oneline -10
```

Determine what changed from the working tree, staged files, and recent commits — not
from a chat summary. For the Validation line, report only what *already* ran this
session (do **not** re-run): take it from the conversation, or — after compaction —
from what the compaction summary preserved (the plugin's PreCompact hook instructs
the summary to keep validation commands and results verbatim). If neither source has
it, write "Not recorded this session" — never invent or assume a result. If nothing
changed at all this session, still write the handoff — it snapshots the current
resting state.

## 2. Overwrite the handoff snapshot

Overwrite `docs/handoff.md` from `${CLAUDE_PLUGIN_ROOT}/templates/handoff.md` (create
the `docs/` folder first if it doesn't exist). This is the deliverable — write it; do
not let the Validation line or anything else crowd it out. Keep it ~10–25 lines. Stamp
`**Updated:**` with today's date (it's in your context; failing that, use the latest
commit date from `git log -1 --format=%cs` — don't ask the user). The shape:

- **Last completed** — 1–3 bullets grounded in the diff / commits / test output.
- **Current focus** — the current milestone or active task from `docs/plan.md`.
- **Next action** — the single next step to pick up.
- **Validation** — commands run this session and their result, or "Not run this session."
- **Watchouts** — only material gotchas; omit if none.

## 3. Reconcile the core docs with this session

Check whether *this session's changes* left any active core doc stale — scoped to what
actually changed (the diff/commits above), **not** a whole-repo audit (that's
`/rad-repo-manager:repo-align`). Read `AGENTS.md`, `docs/prd.md`, and `docs/plan.md` and
compare each against what the session did. Then split by ownership:

- **Docs the plugin owns — `docs/plan.md` and `AGENTS.md`'s operational sections.**
  Offer the specific, scoped update (one line each: what's stale → what it should say)
  and apply it on the user's OK. Typical `plan.md` updates: a milestone shipped or
  changed status, the current milestone advanced, allowed/forbidden scope shifted, or a
  validation gate / stop condition changed. Keep every edit minimal and within the
  session's scope — never rewrite beyond what changed. **If the divergence is
  structural** — milestones obsolete, scope materially shifted, the plan's "Now"
  horizon essentially shipped — don't restructure here: make the one-line status
  touches and recommend `/rad-planner:replan` for the rebuild.

- **Docs the user owns — `docs/prd.md`, `docs/design.md`,
  `docs/reference/decision-log.md`.** The user owns the *decision*, not the typing.
  Don't just describe the staleness — **draft the exact edit** (the precise wording,
  shown as old → new) and ask per doc via AskUserQuestion: **apply / skip / let me
  reword**. Apply only on an explicit "apply" for that specific edit — never bundle
  user-owned edits into a blanket OK, and never touch these docs without that
  per-edit confirmation. A skipped edit is restated in one line at the end so it
  isn't silently lost.

When you edit any core doc that carries an `**Updated:**` stamp (or when `plan.md`
changes), refresh the stamp to today — the freshness scans key off it.

If nothing the session touched made a core doc stale, say so and change nothing here.

## 4. Hygiene pulse — one line, no audit

Run the cheap mechanical scan (use `python3`, or `python` on Windows):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/repo-scan.py . --json --no-record
```

If it's green, say nothing. If loose ends exist, add **one line** to your closing
summary naming them and pointing at `/rad-repo-manager:repo-align` — do not file,
move, or fix anything here. (Skip silently if Python is unavailable.)

## 5. Commit

Do **not** auto-commit or push. Tell the user the handoff is written and they can
commit via their normal flow (e.g. GitHub Desktop). If they explicitly ask, commit on
the current branch with a short message — otherwise leave it.

## What this skill does NOT do

- No whole-repo audit, contradiction/redundancy scan, or doc filing — that's `repo-align`. The core-doc reconcile in step 3 is scoped to this session's changes only.
- Does not run tests, builds, linters, or validators — it only records validation that already ran.
- Does not edit `docs/prd.md`, `docs/design.md`, or `docs/reference/decision-log.md` without an explicit per-edit "apply" from the user — it drafts the exact edit, asks, and a "skip" means hands off.
- Does not create `docs/status.md`, `docs/roadmap.md`, `docs/implementation-plan.md`,
  loose root-level handoff/status/audit docs, or folder-specific agent files.
- No writing of product content; no appending to the handoff; no auto-commit or push.

## References

- `${CLAUDE_PLUGIN_ROOT}/templates/handoff.md` — the snapshot shape
- `${CLAUDE_PLUGIN_ROOT}/references/doc-model.md` — the active core and the plan ↔ handoff boundary

---
name: wrapup
description: >
  This skill should be used when the user says "wrapup", "wrap up", "end of
  session", "save state", "handoff", "leave a clean stopping point", "I'm done for
  now", or "before I close". Writes a short, evidence-grounded docs/handoff.md
  (overwrite, not append) from git evidence — not chat memory — and updates
  docs/plan.md only if durable execution state changed. No deep audit, no
  status/roadmap/implementation-plan files, no auto-commit or push.
argument-hint: ""
user-invocable: true
allowed-tools: Read Glob Grep Bash Write Edit
---

# Wrapup — leave a clean handoff

End the session at a spot a fresh chat (or a post-compaction continuation) can resume
from cold. **Lean and evidence-grounded** — gather what actually changed, overwrite
the handoff snapshot, and stop. The deep pass is `/rad-repo-manager:repo-align`.

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
from a chat summary. If validation (tests/build/lint) ran this session, capture the
command and its result; if not, record "Not run this session." If nothing happened,
say so — don't manufacture a narrative.

## 2. Overwrite the handoff snapshot

Overwrite `docs/handoff.md` from `${CLAUDE_PLUGIN_ROOT}/templates/handoff.md`. Keep it
~10–25 lines. Stamp `**Updated:**` with today's date (ask the user for the date if you
don't have it — do not call a clock). The shape:

- **Last completed** — 1–3 bullets grounded in the diff / commits / test output.
- **Current focus** — the current milestone or active task from `docs/plan.md`.
- **Next action** — the single next step to pick up.
- **Validation** — commands run this session and their result, or "Not run this session."
- **Watchouts** — only material gotchas; omit if none.

## 3. Update the plan only if durable state changed

Touch `docs/plan.md` **only** if durable execution state actually changed this session
— a milestone shipped or changed status, the current milestone advanced,
allowed/forbidden scope shifted, or a validation gate / stop condition changed. Make
the minimal edit. If nothing durable changed, leave `docs/plan.md` untouched.

Do **not** edit `docs/prd.md` (product) or `docs/design.md` unless the user explicitly
asks and a product/design decision actually changed.

## 4. Commit

Do **not** auto-commit or push. Tell the user the handoff is written and they can
commit via their normal flow (e.g. GitHub Desktop). If they explicitly ask, commit on
the current branch with a short message — otherwise leave it.

## What this skill does NOT do

- No deep audit, contradiction check, or doc filing — that's `repo-align`.
- Does not create `docs/status.md`, `docs/roadmap.md`, `docs/implementation-plan.md`,
  loose root-level handoff/status/audit docs, or folder-specific agent files.
- No writing of product content; no appending to the handoff; no auto-commit or push.

## References

- `${CLAUDE_PLUGIN_ROOT}/templates/handoff.md` — the snapshot shape
- `${CLAUDE_PLUGIN_ROOT}/references/doc-model.md` — the active core and the plan ↔ handoff boundary

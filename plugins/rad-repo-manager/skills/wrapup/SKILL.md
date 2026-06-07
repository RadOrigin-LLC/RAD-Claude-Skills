---
name: wrapup
description: >
  This skill should be used when the user says "wrapup", "wrap up", "end of
  session", "save state", "handoff", "leave a clean stopping point", "I'm done for
  now", "before I close", or wants a clean handoff for a new chat or for continuing
  after compaction. Overwrites docs/handoff.md from git evidence (not chat memory),
  then prints the one-line health verdict. Intentionally lean — no deep audit, no
  auto-commit. The deep hygiene pass is /rad-repo-manager:analyze.
argument-hint: ""
user-invocable: true
allowed-tools: Read Glob Grep Bash Write
---

# Wrapup — leave a clean handoff

End the session at a spot a new chat (or a post-compaction continuation) can resume
from cold. **Keep it lean** — gather evidence, write the handoff snapshot, show the
health line. No audit. The deep pass is `/rad-repo-manager:analyze`.

## 1. Gather evidence (not memory)

The handoff is grounded in what actually happened, not a chat summary. In one batch:

```bash
git status --short
git diff --stat
git log --oneline -10
```

If tests/build were run this session, capture their last result. If the working tree
is clean and nothing happened, say so — don't manufacture a narrative.

## 2. Write the handoff snapshot

Overwrite `docs/handoff.md` from `${CLAUDE_PLUGIN_ROOT}/templates/handoff.md`. It is a
**snapshot, not a log** — replace the contents, do not append. Keep it ~15 lines:

- **What changed this session** — 1–3 bullets from the actual diff / test output.
- **Current working state** — what works, what's mid-flight, what's broken now.
- **Resume point** — the single next action to pick up.
- **Gotchas** — anything that will bite the next session (omit if none).

Stamp `**Updated:**` with today's date (ask the user for the date if not available;
do not call a clock). Write only `docs/handoff.md` — nothing else.

## 3. Health line

Run the cheap tripwire scan and print the one-line verdict as the last line:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/repo-scan.py . --json
```

Render exactly one line per the thresholds:

- 🟢 `Repo's tidy — nothing loose.` (0)
- 🟡 `A few loose ends (N) — fine for now.` (1–4)
- 🔴 `Getting cluttered (N) — worth a /rad-repo-manager:analyze to sort it.` (≥5)

Apply the same 3-session cooldown on the 🔴 `/analyze` tail as startup. The count
always shows; the explicit nudge is rate-limited so it never becomes noise.

## 4. Commit

Do **not** auto-commit. Tell the user the handoff is written and they can commit via
their normal flow (e.g. GitHub Desktop). If they explicitly ask you to commit, do so
on the current branch with a short message; otherwise leave it.

## What this skill does NOT do

- No deep audit, contradiction check, or doc filing — that's `analyze`.
- No writing of product or plan content.
- No auto-commit, no push.
- No appending to handoff — it's overwritten each time.

## References

- `${CLAUDE_PLUGIN_ROOT}/templates/handoff.md` — the snapshot shape
- `${CLAUDE_PLUGIN_ROOT}/scripts/repo-scan.py` — the cheap tripwire scan
- `${CLAUDE_PLUGIN_ROOT}/references/doc-model.md` — the tiers and filing rules

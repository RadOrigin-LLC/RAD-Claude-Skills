# session-log.md format (retired in v5.0)

`.claude/session-log.md` is retired as of rad-session 5.0. Its journal role is replaced by `docs/planning/archive/YYYY-MM-DD-MN-slug.md` — one file per shipped milestone, written by `/wrapup` Phase 6 when all acceptance criteria in `docs/planning/current.md` are checked.

The canonical convention lives at:

→ **[`docs/doc-conventions.md`](../../../docs/doc-conventions.md)** — section on `docs/planning/archive/` (canonical source)

## Why the change

v4.0's session-log.md was a flat append-only file capped at 20 entries. Two structural problems:

1. **Per-session granularity was too fine.** Sessions don't map cleanly to milestones — one milestone often spans 5–20 sessions; one session sometimes spans multiple milestones. Per-session entries fragmented the timeline.
2. **20-entry hard cap forced premature trim.** Real projects have more than 20 milestones; the cap was a workaround for fixed-size flat files, not a meaningful boundary.

`planning/archive/` solves both: one file per **shipped milestone** (the right granularity), unlimited count (one file per archive entry), and the filename's date+milestone-number prefix sorts chronologically without scanning content.

## If your project still has .claude/session-log.md

It's no longer read or written by rad-session. You can archive or delete it. Per-session granularity didn't map cleanly to milestones; the v5.0 `docs/planning/archive/` structure (one file per shipped milestone) replaces it for retrospective signal.

# Briefing Examples (v5.0)

Canonical output formats for `/startup` Phase 3. The startup skill picks one of these five shapes based on what it detected. Follow the structure verbatim — the formatting is load-bearing for scanability.

**Target:** under 35 lines, under 5 seconds wall-clock (doorman model).

---

## Full Briefing (status.md + current.md both present, coding project)

```
[If sync warnings from Phase 0, place them above everything else:]
⚠ Reading stale local state — origin has N unpulled commits. Re-run /startup without --no-pull to sync.
[or]
⚠ Couldn't sync — <dirty working tree | local diverged from origin>. Resolve with: <git stash | git pull --rebase>.

[If cross-machine handoff detected:]
Continuing from <other-host> — last status committed there.

Project: [name]
Type: Coding ([stack from architecture.md or detect-stack.py])
Branch: [name] ([N ahead, M behind] or [up to date])
Mode: [mentor | dev]    Scope: [claude_only | codex_only | claude_and_codex]

Current milestone: [from current.md current_milestone]
Status: [from status.md current state — one line]

Where we left off (status.md):
  - [last-completed item 1]
  - [last-completed item 2]

Open acceptance criteria (current.md):
  - [ ] [AC 1]
  - [ ] [AC 2]

Latest validation:
  - [command] → [result from status.md]

[If status.md has "Known issues or blockers":]
Blockers:
  - [item]

Next recommended step:
  [from status.md next-recommended-step]

[If gap-check found any missing strategic docs:]
⚠ Missing strategic docs: <list> — run /rad-planner:plan --improve to populate.

Ready to continue. What would you like to work on?
```

### Concrete example (Wayfinder mid-flight)

```
Project: wayfinder
Type: Coding (Next.js + Supabase + Drizzle)
Branch: main (up to date)
Mode: mentor    Scope: claude_only

Current milestone: M2 — Activity-constraint engine
Status: on track

Where we left off (status.md):
  - Constraint evaluator implemented at lib/constraints/evaluator.ts (24/24 tests passing)
  - Constraint type definitions locked at lib/constraints/types.ts

Open acceptance criteria (current.md):
  - [ ] Failure reasons surfaced (which constraint failed, by how much)
  - [ ] UI handles 1+ constraint sets per user
  - [ ] Visual Crossing rate-limit handling

Latest validation:
  - bun test lib/constraints/ → pass (24/24)
  - bun run typecheck → pass

Next recommended step:
  Start the Drizzle CRUD layer in lib/constraints/queries.ts. First decide: per-user vs per-account scope.

Ready to continue. What would you like to work on?
```

---

## Status-only briefing (status.md present, current.md missing)

When `docs/planning/current.md` is absent (project hasn't run `/rad-planner:plan` yet) but `docs/status.md` exists:

```
Project: [name]
Type: [Coding (stack) | Non-coding]
Branch: [name] ([ahead/behind])
Mode: [mentor | dev]    Scope: [claude_only | codex_only | claude_and_codex]

Status: [from status.md current state]

Where we left off (status.md):
  - [items]

[If "Decisions made during execution" non-trivial:]
Recent decisions:
  - [items]

Next recommended step:
  [from status.md]

⚠ No planning/current.md found — run /rad-planner:plan to define the current milestone.

Ready to continue.
```

---

## Minimal briefing (no status.md, no current.md)

```
Project: [name from directory or operating manual]
Type: [Coding (stack) | Non-coding]
[Branch: [name] — if git project]
Mode: [mentor | dev]    Scope: [claude_only | codex_only | claude_and_codex]

No status.md or current.md yet — this looks like a fresh project, or one that hasn't run /startup (which bootstraps on first run) / /plan / /wrapup.

[If operating manual exists:]
From [CLAUDE.md | AGENTS.md | <non-canonical name>]: [brief summary — Project section, one line]

[If git history exists:]
Recent activity:
  - [last 3-5 commits]

Recommendations:
  - Run /rad-session:init if rad-session hasn't been set up
  - Run /rad-planner:plan to define the current milestone

What would you like to work on?
```

---

## First-time briefing (after /startup bootstrap, before first /plan or /wrapup)

```
Project: [name]
Type: Coding ([stack])
Branch: [name] ([up to date])
Mode: mentor    Scope: [from .rad/profile]

Operating manual: [CLAUDE.md | AGENTS.md | both] — Operational sections scaffolded.
docs/status.md: scaffolded, awaiting first /wrapup.

⚠ Strategic docs not present — run /rad-planner:plan to define vision, architecture, and the current milestone.

Detected resources:
  MCPs: [list]
  Stack CLIs: [list]
  Scripts ([pm]): [list]

Ready to plan. What's the project about?
```

---

## Non-coding briefing

```
Project: [name]
Type: Non-coding
Mode: [mentor | dev]

Status: [from status.md]

Where we left off (status.md):
  - [items]

Recently modified files:
  - [file list]

Next recommended step:
  [from status.md]

Ready to continue.
```

---

## What changed from v4.0

| v4.0 briefing source | v5.0 briefing source |
|---|---|
| `HANDOFF.md` | `docs/status.md` (project-scoped, evidence-based) |
| Strategic docs at project root (PRD / ARCH / ASSUMPTIONS / DECISIONS / PLAN) | `docs/` canonical structure (vision / architecture / planning/current / decisions) |
| `CLAUDE.md` (always) | Operating manual per agent_scope (CLAUDE.md / AGENTS.md / both) |
| Resource discovery as a separate Phase 2.5 section | Resources only surfaced if drift detected (otherwise silent) |
| `## Resources` section in CLAUDE.md | Strategic resources documented in `docs/architecture.md`; transient session resources via `/add-resource` |

The briefing length target tightened from "no fixed target" to **under 35 lines** to honor the doorman model.

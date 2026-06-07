# The doc model rad-repo-manager enforces

A deliberately tiny, declared, defended set of "truth" docs, with everything else
demoted to on-demand reference or cold archive. This is the spine of the plugin.

## Tiers

| Tier | Where | Read policy |
|---|---|---|
| **Active** | the 4 core docs (below) | every session |
| **Reference** | `docs/reference/*` — a closed, named catalog | only when the task touches that area |
| **Inbox** | `docs/inbox/*` | not read for work; flagged by wrapup, filed by analyze |
| **Archive** | `docs/archive/*` | never by default; only on explicit request |

## The active core — hard ceiling of 4 (+ shims)

```
AGENTS.md         · operating manual: how we work, boundaries, the declared read path
docs/prd.md       · durable product authority: what we're building / current behavior
docs/plan.md      · the plan: scope, milestones, tasks (owned by /rad-planner:plan)
docs/handoff.md   · live session state: where we are, what's next, gotchas
```

Plus thin `CLAUDE.md` / `GEMINI.md` that are *only* an `@AGENTS.md` import, created per
the agents the user actually uses. (Codex reads `AGENTS.md` natively — no shim.)

The active set is **declared in `AGENTS.md`** and **capped at four**. "On track" =
reality matches the declared set, nothing floating, nothing bloated.

## Who writes what

- **rad-repo-manager writes:** `AGENTS.md` operational sections (never user-authored content), the shims, `docs/handoff.md`. Scaffolds `prd.md`/`plan.md` skeletons once at onboarding.
- **rad-planner writes:** `docs/plan.md` content (scope/milestones/tasks).
- **the user owns:** `docs/prd.md`, `docs/reference/decision-log.md`, reference docs.
- **surfaced, never written by the manager:** changes to `prd.md` / `decision-log.md` → a paste-ready update-prompt in `docs/inbox/`.

"What's next" lives only in `docs/handoff.md`. One source.

## Reference catalog (closed)

A fixed, named set of slots — not a free-for-all folder. A doc that matches a slot is
filed; anything off-catalog is itself a loose end.

| Slot | What goes in it |
|---|---|
| `decision-log.md` | active decisions, compact |
| `architecture.md` | system shape, data model, stack rationale |
| `design.md` | visual / UI design direction |
| `api-contracts.md` | API routes, provider / AI integration contracts |
| `commands.md` | build / release / deployment commands (don't duplicate AGENTS.md's short pre-push list) |
| `lessons-learned.md` | known traps and their fixes |
| `testing.md` | test strategy / coverage |

Reference docs are **scaffolded by none** — each appears only when a project needs it.
The catalog is the menu, not the starter set.

## Document intake & filing

New docs are expected (side brainstorms, smoke tests, AI reports). There's a process,
not a ban.

- **Intended path:** agents write any new, un-homed `.md` into `docs/inbox/`.
- **Backstop:** any `.md` outside core / reference / inbox / archive is *floating* —
  flagged harder (an agent or a manual save dropped it loose).
- **Filing (analyze, user-confirmed):** Fold · Extract · Promote · Archive · Relocate.

## Loose ends (the health-line signals)

Cheap, high-precision, mechanical — so the count is trustworthy and never cries wolf:

1. active set grew beyond the declared four
2. a `.md` is floating (outside any tier) or sitting in the inbox
3. `AGENTS.md` past a soft size cap (bloating)
4. an active doc unchanged while code churned N+ commits (possibly stale)

Fuzzy checks (semantic contradiction, redundancy) never feed the health line — they
live in `analyze`, which the user opts into.

## Non-goals

No status/roadmap/per-feature docs. No writing durable content (surfaced only). No deep
audit in startup/wrapup. No auto-action on judgment calls. No doc-type classifier. Not
a correctness guarantee — a drift early-warning, honestly scoped.

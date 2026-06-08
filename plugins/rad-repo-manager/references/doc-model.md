# The doc model rad-repo-manager enforces

A deliberately tiny, declared, defended set of "truth" docs, with everything else
demoted to on-demand reference or cold archive. This is the spine of the plugin.

## Tiers

| Tier | Where | Read policy |
|---|---|---|
| **Active** | the 4 core docs (below) | every session |
| **Conditional** | `docs/design.md` · `docs/reference/*` (closed catalog) · `docs/README.md` | only when the task touches that area |
| **Archive** | `docs/archive/*` | never by default; only on explicit request |

## The active core — hard ceiling of 4 (+ shims)

```
AGENTS.md         · operating manual: how we work, boundaries, the declared read path
docs/prd.md       · durable product authority: what we're building / current behavior
docs/plan.md      · the plan: roadmap, milestones, scope, gates, stop conditions (owned by /rad-planner:plan)
docs/handoff.md   · the short resume snapshot: where we are, what's next, gotchas
```

Plus thin `CLAUDE.md` / `GEMINI.md` that are *only* an `@AGENTS.md` import, created per
the agents the user actually uses. (Codex reads `AGENTS.md` natively — no shim.)

The active set is **declared in `AGENTS.md`** and **capped at four**. "Aligned" =
reality matches the declared set: nothing floating, nothing bloated, no off-model
status/roadmap docs.

## The plan ↔ handoff boundary (the one that matters most)

- `docs/plan.md` owns everything **durable**: roadmap, milestones, allowed scope,
  forbidden scope, validation gates, stop conditions.
- `docs/handoff.md` owns only the **short resume snapshot** for the next chat.
- **If a statement must remain true after the next session, it does not belong only in
  `docs/handoff.md`.** Put it in `docs/plan.md` (or `prd.md` / `design.md` / a
  reference doc) and let the handoff point at it.

"What's next" lives in `docs/handoff.md`. One source.

## Who writes what

- **rad-repo-manager writes:** `AGENTS.md` operational sections (never user-authored content), the shims, `docs/handoff.md`. Scaffolds `prd.md`/`plan.md` skeletons once at `repo-init`. At `wrapup`, offers scoped updates to `docs/plan.md` and `AGENTS.md` operational sections when the session made them stale.
- **rad-planner writes:** `docs/plan.md` content (roadmap / milestones / scope / gates).
- **the user owns:** `docs/prd.md`, `docs/design.md`, `docs/reference/decision-log.md`, reference docs.
- **surfaced, never written by the manager:** a change to `prd.md` / `design.md` / `decision-log.md` is described for the user to apply — including at `wrapup` when the session made one stale. The manager flags; the user owns product and decisions.

## Reference catalog (closed)

A fixed, named set of slots — not a free-for-all folder. A doc that matches a slot is
filed; anything off-catalog is itself a loose end.

| Slot | What goes in it |
|---|---|
| `decision-log.md` | active decisions, compact |
| `architecture.md` | system shape, data model, stack rationale |
| `api-contracts.md` | API routes, provider / AI integration contracts |
| `commands.md` | build / release / deployment commands |
| `lessons-learned.md` | known traps and their fixes |
| `testing.md` | test strategy / coverage |

Visual / UI design direction lives at top-level `docs/design.md` (conditional), not in
the catalog. Reference docs are **scaffolded by none** — each appears only when a
project needs it. The catalog is the menu, not the starter set.

## Drift signals (mechanical, for repo-align)

Cheap, high-precision, mechanical checks — `scripts/repo-scan.py` plus three deeper
validators — surface **candidates** for `/rad-repo-manager:repo-align`:

1. active set grew beyond the declared four
2. a `.md` is floating (outside any tier) or sitting loose at the root / under `docs/`
3. `AGENTS.md` past a soft size cap (bloating)
4. an active doc unchanged while code churned (possibly stale)
5. plan ↔ PRD contradiction (scope-creep), cross-doc redundancy, AGENTS.md orphan terms / dead paths

These feed **judgment**, not auto-action — `startup` stays read-only; `wrapup` only
reconciles the core docs against the current session (offering owned-doc edits,
surfacing user-owned ones). These whole-repo mechanical signals are read and
dispositioned in `repo-align`, always with your confirmation.

## Non-goals

No status/roadmap/implementation-plan/per-feature docs. No `docs/inbox/` staging tier.
No writing durable content (surfaced only). No whole-repo audit in startup/wrapup (wrapup's core reconcile is session-scoped). No
auto-action on judgment calls. No doc-type classifier. No folder-specific agent files.
Not a correctness guarantee — a drift early-warning, honestly scoped.

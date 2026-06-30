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
- **rad-planner writes:** `docs/plan.md` content (release map / roadmap / milestones / scope / gates). It may also **birth** `docs/prd.md` — drafted from the user's own discovery-interview answers, applied per-section on explicit confirmation — when none exists or only the skeleton does. After birth, the PRD is the user's; the planner never edits an existing PRD.
- **the user owns:** `docs/prd.md` (once it exists), `docs/design.md`, `docs/reference/decision-log.md`, reference docs.
- **drafted, applied only on explicit per-edit confirmation:** a change to `prd.md` / `design.md` / `decision-log.md` is drafted as the exact edit (old → new) and applied only when the user says "apply" for that specific edit — at `wrapup` (session-scoped) and `repo-align` (whole-repo). The user owns the decision; the manager does the typing. A skip means hands off.
- **freshness stamps:** `docs/prd.md`, `docs/plan.md`, and `docs/handoff.md` carry an `**Updated:**` date (templates include it; `AGENTS.md` deliberately doesn't — staying unchanged is normal for it). Whoever edits a stamped doc refreshes the stamp — the freshness scan keys off it.

## Authority order — resolving contradictions

When two active docs disagree on an accepted decision, the conflict is resolved by
authority, highest wins:

1. The owner's instruction in the current session
2. `docs/prd.md` — product behavior and rules
3. `docs/reference/decision-log.md` — recorded active decisions
4. `docs/plan.md` — execution, scope, milestones
5. `docs/design.md` — brand / UI / visual direction
6. `docs/reference/*` — the rest of the catalog
7. `docs/handoff.md` — the resume snapshot
8. `docs/archive/*` — history (never current authority)

The higher doc wins; the lower is brought into line as a **drafted** edit under the
per-edit confirmation rule — never silently. Two rules bound this:

- **Decisions live in their authority doc.** An accepted decision belongs in `docs/prd.md`
  or `docs/reference/decision-log.md`, not stranded only in a brainstorm, the handoff, or
  `AGENTS.md`. A stranded decision is promoted to its authority doc.
- **Stop, don't merge.** If authority can't decide which version is right — two same-tier
  docs disagree, or the conflict is a genuine product decision the owner hasn't made —
  **STOP and surface it as a decision.** Never silently merge two conflicting decisions.

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

Brand / UI/UX / visual design direction lives at top-level `docs/design.md`
(conditional), not in the catalog — technical/system design belongs in
`architecture.md` above, never in `design.md`. Reference docs are **scaffolded by none** — each appears only when a
project needs it. The catalog is the menu, not the starter set.

## Superseded content & retired terminology

Two lightweight conventions keep "what's current" honest without moving everything to
archive:

- **Superseded banner.** When an active doc's content has been overtaken but is worth
  keeping in place for context (not yet ready to move to archive), add a banner at the
  top: `> **Superseded YYYY-MM-DD:** replaced by <doc/section> — kept for context.` This
  is distinct from the archive banner, which marks a file *moved* into `docs/archive/`. No
  active doc should carry obsolete product direction without one of the two.
- **Retired terminology (optional config).** A project may maintain a `## Retired
  terminology` table in `AGENTS.md` mapping each dead term to its replacement.
  `repo-align` reads it and greps the active docs for every retired term, flagging stray
  uses. The list is project-supplied — no terms are hardcoded. Format:

  ```
  ## Retired terminology

  | Retired | Use instead |
  |---|---|
  | Trip Kit | Fieldbook |
  | Phase 1 / Phase 2 | named milestones in docs/plan.md |
  ```

  The section is exempt from the orphan-terminology audit (retired terms are *meant* to be
  absent from active docs).

## Drift signals (mechanical)

Cheap, high-precision, mechanical checks — `scripts/repo-scan.py` and
`scripts/doc-freshness.py` plus three deeper validators — surface **candidates**:

1. active set grew beyond the declared four (`repo-scan`)
2. a `.md` is floating (outside any tier) or sitting loose at the root / under `docs/` (`repo-scan`)
3. `AGENTS.md` past a soft size cap (bloating) (`repo-scan`)
4. an active doc unchanged while code churned — stale handoff, untouched prd/plan (`doc-freshness`)
5. plan ↔ PRD contradiction (scope-creep), cross-doc redundancy, AGENTS.md orphan terms / dead paths (`doc-contradiction`, `doc-redundancy`, `audit-user-content`)

These feed **judgment**, not auto-action. The two cheap scans (1–4) run every session:
`startup` reads them for the briefing (still read-only), `wrapup` runs the hygiene
pulse, and the SessionStart hook surfaces a one-liner ambiently. The deeper validators
(5) and all dispositions live in `repo-align`, always with your confirmation.

## The ambient layer (hooks)

Skills only run when invoked — the hooks catch what habit misses, and all three are
silent in repos that don't use this model:

- **SessionStart** — runs the two cheap scans; injects a one-line doc-health note
  *only* when something is stale or loose. Says nothing on green.
- **PreCompact** — instructs the compaction summary to preserve the handoff's raw
  material verbatim (validation commands + results, files changed, current task, next
  action) so a post-compaction `wrapup` isn't writing from amnesia.
- **Stop** — at most one reminder per session, only when real work is uncommitted and
  the handoff isn't being kept fresh: a nudge that `wrapup` exists. Never blocks.

## Non-goals

No status/roadmap/implementation-plan/per-feature docs. No `docs/inbox/` staging tier.
No writing durable content without an explicit per-edit confirmation. No whole-repo
audit in startup/wrapup (the cheap scans are signals, not an audit; wrapup's core
reconcile is session-scoped). No auto-action on judgment calls. No blocking hooks and
no hook noise on green. No doc-type classifier. No folder-specific agent files. Not a
correctness guarantee — a drift early-warning, honestly scoped.

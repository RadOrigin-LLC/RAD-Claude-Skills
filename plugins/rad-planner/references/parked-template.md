# `docs/planning/parked.md` — template

This is the canonical format for `docs/planning/parked.md` entries. rad-planner appends to this file during `/plan` M2 when the user opts to park an idea instead of putting it in scope or marking it a non-goal.

## File header (created once on first park)

```markdown
# Parked

Ideas captured during planning but not committed to. Distinct from `vision.md` non-goals (foreclosure — "we are NOT building this") and from `roadmap.md` Later/Parked (which implies sequencing). This file is the open-ended holding pen.

Entries are appended in reverse chronological order (newest first). No automated pruning. Promotion to a milestone or to non-goals is user-initiated.
```

## Entry format

```markdown
## YYYY-MM-DD — Short title

**Why parked:** one-line reason (e.g., "interesting but post-v1", "needs user research first", "depends on retired feature returning")
**Source:** which M2 conversation / which milestone surfaced it / who raised it
**Promote when:** condition under which this should be revisited (optional)

Brief description of the idea, no more than a paragraph. Specific enough that future-you remembers what it was without re-deriving the context.
```

## When `/plan` M2 offers parking

During M2 (Goal-Backward Scope), the user can answer "park" instead of "in scope" or "non-goal" when an idea surfaces that:

- Doesn't fit must-be-TRUE / must-EXIST / CRITICAL for the current milestone
- Isn't a clean non-goal (foreclosing it feels too strong)
- Has enough substance to want to remember

rad-planner appends the entry with the date, a one-line title, and the captured reasoning. The full conversation context is condensed; only what future-you needs to evaluate the idea later is preserved.

## What does NOT belong in `parked.md`

- Decisions already made — those go in `docs/decisions/`
- Active milestone work — that's `docs/planning/current.md`
- Foreclosed ideas — those go in `vision.md` non-goals
- Sequenced future work — that's `roadmap.md`
- Bug reports — those go in your issue tracker
- TODOs in code — those stay in code

## Manual promotion

When the user wants to bring a parked idea forward, they:

1. Move the entry from `parked.md` into the appropriate destination (a new milestone in `roadmap.md`, an active task in `current.md`, or an ADR in `docs/decisions/` if the parking decision itself was the choice to defer)
2. Optionally leave a stub entry behind referencing the promotion target
3. No tooling enforces this — promotion is judgment, not automation

## Manual cleanup

When a parked idea becomes irrelevant (project pivoted, technology changed, intent shifted), the user can:

- Delete the entry entirely (low-cost; this is not a historical record)
- Or replace the body with a one-line "Closed: <reason>" note if the parking history is worth keeping

Neither plugin auto-prunes parked entries. The file can grow unboundedly without breaking anything — that's intentional, because the cost of forgetting a good idea is higher than the cost of carrying a stale one.

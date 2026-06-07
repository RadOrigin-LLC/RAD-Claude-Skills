# Current Plan

## Objective

Ship M3: hierarchical layout via the Sugiyama framework — layer assignment, crossing minimization, coordinate assignment — producing a stable left-to-right DAG rendering.

## Why this matters

Force-directed layout (M1) handles general graphs but produces unreadable results for DAGs. Hierarchical layout is the gold standard for DAG visualization and unlocks a major user segment (dependency graphs, build graphs).

## Non-goals

- Not adding orthogonal edge routing — that's M5 (with crossings reduced from M3)
- Not building a layout UI — library-level only

## Current milestone

M3: Sugiyama hierarchical layout

## Acceptance criteria

- [x] Layer assignment via longest-path produces correct layers for acyclic + DAG-with-back-edge graphs
- [ ] Crossing minimization via median heuristic converges in <500ms for graphs up to 100 nodes
- [ ] Coordinate assignment produces stable x/y output deterministic across runs
- [ ] Public `layoutSugiyama(graph)` function returns layout-ready node positions
- [ ] No runtime dependency added; output matches existing `Layout` type

## Validation commands

- `bun test src/layout/sugiyama/` — Sugiyama unit tests
- `bun test tests/integration/sugiyama-end-to-end.test.ts` — end-to-end layout integration
- `bun run typecheck` — strict TS passes
- `bun run lint` — biome lint passes

## Planned changes

- [x] `src/layout/sugiyama/layer.ts` — layer assignment
- [ ] `src/layout/sugiyama/crossing.ts` — median crossing minimization
- [ ] `src/layout/sugiyama/coord.ts` — coordinate assignment
- [ ] `src/layout/sugiyama/index.ts` — public entry point

## Open questions

- Median heuristic gives ~80% optimality; should we add a brute-force pass for <20-node graphs?
- Coordinate assignment: prioritize symmetry or minimal edge length?

## Risks

- Risk: median heuristic doesn't converge for highly-connected graphs
  - Mitigation: cap iterations at 24 and fall back to last best result
- Risk: API surface drift from force-directed layout
  - Mitigation: both algorithms return the same `Layout` type — locked in `src/layout/types.ts`

## Stop conditions

Stop and ask for approval if:

- The public `Layout` type must change
- A runtime dependency must be added
- M1 force-directed layout regresses

## Notes for the next session

- Most likely next step: implement crossing minimization
- Files likely to change: `src/layout/sugiyama/crossing.ts`, tests
- What must remain true: M1 force-directed layout unchanged and zero runtime dependencies

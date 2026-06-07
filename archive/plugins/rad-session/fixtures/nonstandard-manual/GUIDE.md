# Agent Operating Manual

## Project

Graphkit is a developer-facing TS library for declarative graph layout. Existing project that adopted rad-session after initial repo conventions had already settled on `GUIDE.md` rather than `CLAUDE.md`.

## Read order

- Before implementation, read `docs/status.md` and `docs/planning/current.md`.
- Read `docs/architecture.md` for layout-algorithm boundaries.
- Read `docs/decisions/` before revisiting choices already made.

## Hard boundaries

- Do not break the public API exported from `src/index.ts` without a major-version ADR.
- Do not add runtime dependencies — the library stays zero-dep at runtime.
- Do not expand scope beyond `docs/planning/current.md`.

## Commands

- Install: `bun install`
- Unit tests: `bun test`
- Lint: `bun run lint`
- Typecheck: `bun run typecheck`
- Build: `bun run build`

## Engineering rules

- Prefer the smallest change that satisfies the acceptance criteria.
- Reuse existing patterns before introducing new abstractions.
- When behavior changes, update tests in the same change set.
- When behavior or workflow changes, update the relevant docs in the same change set.

## Definition of done

- The acceptance criteria in `docs/planning/current.md` are satisfied.
- Relevant validation commands have been run and results are recorded in `docs/status.md`.

## Escalate instead of guessing

- A change to the public API surface
- Performance regression in the force-directed layout
- Validation fails and the fix requires scope expansion

## Claude-specific behavior

- Use `/plan` for ambiguous, multi-file, or architectural work.
- Use subagents for broad investigation; keep the main session focused.

## Compact Instructions

When using compact:
- preserve the current objective
- preserve non-goals and hard boundaries
- preserve acceptance criteria
- preserve the current list of changed files
- preserve latest validation commands and results
- preserve blockers, open questions, and next step
- drop superseded exploration paths and abandoned ideas

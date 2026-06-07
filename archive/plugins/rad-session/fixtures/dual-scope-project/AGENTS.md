# Agent Operating Manual

## Project

Ledgerline is a TypeScript web app for small-team accounting — double-entry ledger, invoices, monthly reports. Single-tenant per workspace.

## Read order

- Before implementation, read `docs/status.md` and `docs/planning/current.md`.
- Read `docs/architecture.md` before any structural, cross-cutting, or multi-file change.
- Read `docs/vision.md` before changing user-facing behavior or product scope.
- Read `docs/decisions/` before revisiting choices already made.

## Hard boundaries

- Do not expand scope beyond `docs/planning/current.md`.
- Do not change the chart-of-accounts schema or the journal-entry contract.
- Do not add a new dependency without explicit approval — record the proposal as a candidate ADR first.
- Do not introduce a new state-management library — Zustand stays as-is.

## Commands

- Install: `pnpm install`
- Dev server: `pnpm dev`
- Unit tests: `pnpm test`
- Lint: `pnpm lint`
- Typecheck: `pnpm typecheck`
- Build: `pnpm build`

## Engineering rules

- Prefer the smallest change that satisfies the acceptance criteria.
- Reuse existing patterns before introducing new abstractions.
- When behavior changes, update tests in the same change set.
- When behavior or workflow changes, update the relevant docs in the same change set.
- If a decision becomes durable, record it in `docs/decisions/`.

## Definition of done

- The acceptance criteria in `docs/planning/current.md` are satisfied.
- Relevant validation commands have been run and results are recorded in `docs/status.md`.
- The diff stays within the stated scope and non-goals.

## Escalate instead of guessing

- Missing requirement or conflicting requirement
- Change would affect billing, auth, or the journal-entry contract
- Validation fails and the fix requires scope expansion

# Agent Operating Manual

## Project

Routebadge is a TS service that issues signed JWT route-permission badges for a microservice mesh. Single-purpose, dev-mode tester profile (faster /wrapup with less prompting).

## Read order

- Before implementation, read `docs/status.md` and `docs/planning/current.md`.
- Read `docs/architecture.md` for signing/key-rotation invariants.
- Read `docs/decisions/` before revisiting choices already made.

## Hard boundaries

- Do not change the JWT claim shape without an ADR.
- Do not add a key-management dependency — KMS-as-given.
- Do not expand scope beyond `docs/planning/current.md`.

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

## Definition of done

- The acceptance criteria in `docs/planning/current.md` are satisfied.
- Relevant validation commands have been run and results are recorded in `docs/status.md`.

## Escalate instead of guessing

- A change to the JWT claim shape
- A new dependency beyond what's in package.json
- Validation fails and the fix requires scope expansion

## Claude-specific behavior

- Use `/plan` for ambiguous, multi-file, or architectural work.

## Compact Instructions

When using compact:
- preserve the current objective, non-goals, acceptance criteria
- preserve changed files and validation results
- drop superseded exploration

# Current Plan

## Objective

Ship M2: zero-downtime JWT signing key rotation with a 24-hour rolling acceptance window for the previous key.

## Why this matters

M1 (single-key signing) works but any rotation breaks all in-flight tokens. M2 makes key rotation a non-event for downstream services.

## Non-goals

- Not adding key generation automation — operator-driven rotation only this milestone
- Not building a UI — CLI-only operator surface

## Current milestone

M2: Dual-key rotation with 24h overlap

## Acceptance criteria

- [x] Signer always uses the current key
- [x] Verifier accepts both current and previous key for 24h after rotation
- [x] After 24h, previous key is rejected; only current key is accepted
- [x] Operator CLI command `routebadge rotate` triggers rotation atomically
- [x] No in-flight token invalidation during rotation

## Validation commands

- `pnpm test src/jwt/` — JWT module unit tests
- `pnpm test tests/integration/rotation-flow.spec.ts` — end-to-end rotation test
- `pnpm typecheck` — strict TS passes
- `pnpm lint` — biome lint passes

## Planned changes

- [x] `src/jwt/signer.ts` — current-key signing
- [x] `src/jwt/verifier.ts` — rolling-window verification
- [x] `src/jwt/rotation.ts` — rotation scheduler
- [x] `src/cli/rotate.ts` — operator CLI
- [x] `tests/integration/rotation-flow.spec.ts` — E2E

## Open questions

(none — all resolved during M2)

## Risks

(none — addressed during M2 via the rolling window design)

## Stop conditions

- Milestone is shipped; no active stop conditions. (This plan is awaiting archive — see Notes for the next session.)

## Notes for the next session

- This milestone is shipped — all acceptance criteria checked.
- /wrapup should detect this and propose archiving `current.md` to `planning/archive/`.
- Next milestone (M3) will plan a new `current.md` after archive.

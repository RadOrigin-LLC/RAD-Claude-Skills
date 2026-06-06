# Plan: URL Shortener Service

**Status:** APPROVED
**Updated:** 2026-06-06
**Pending durable-doc updates:** see `2026-06-06-update-prompt.md`

## Objective

Ship a single-tenant URL shortener with idempotent shortening and an atomic click
counter, deployable as one container. Worth doing now because an internal tool needs
short links this sprint and no shared service exists yet.

## Scope

**In scope:**
- Shorten a long URL to a stable short code (idempotent: same URL → same code).
- Redirect a short code to its target and increment a click counter atomically.

**Out of scope / non-goals:**
- Custom/vanity codes — deliberately deferred; not building this for v1.
- Multi-tenant isolation — single-tenant only until a second consumer appears.
- Analytics dashboard — click counts are stored, not visualized, in v1.

## Key assumptions

- [2026-06-06] No real users yet — backward-compat can break freely until M3 ships.
- [2026-06-06] Single-tenant only; multi-tenant would require a schema rework.
- [2026-06-06] The database can be rebuilt from migrations anytime this month — no backfill required.

## Stack

PostgreSQL 16 + Drizzle ORM (atomic `UPDATE ... RETURNING` for the counter, `ON CONFLICT`
for idempotency); Fastify on Node 20 (native TS types, schema-validated routes).

## Milestones

| # | Milestone | Goal (what it ships) | Key artifacts |
|---|---|---|---|
| M1 | Idempotency spike | Prove same-URL-same-code under concurrency | `schema.ts`, spike test |
| M2 | Core service | Shorten + redirect with atomic counter | `shortener.ts`, route handlers |
| M3 | Deploy | One container + smoke CI | `Dockerfile`, `ci.yml` |

Risk-first ordering: the hardest unknown (idempotency under concurrent writes) is M1, a
spike, before the dependent core service in M2.

## Tasks

### M1 — Idempotency spike

- **T1 — Validate idempotent insert under concurrency**
  - **Objective:** Prove `ON CONFLICT (url_hash) DO NOTHING ... RETURNING` returns a stable code under parallel inserts of the same URL.
  - **Files:** `src/db/schema.ts`, `test/spike/idempotency.test.ts`
  - **Depends on:** none
  - **Done when:** 100 concurrent inserts of one URL yield exactly one row and one code.
  - **Validate:** `npm run test -- test/spike/idempotency.test.ts`
  - **Rollback:** `git restore src/db/schema.ts test/spike/`

### M2 — Core service

- **T2 — Shorten endpoint**
  - **Objective:** `POST /shorten` returns a short code, idempotent per the M1 approach.
  - **Files:** `src/shortener.ts`, `src/routes/shorten.ts`
  - **Depends on:** T1
  - **Done when:** `POST /shorten` with a repeated URL returns the same code and HTTP 200.
  - **Validate:** `npm run test -- test/shorten.test.ts`
  - **Rollback:** `git restore src/shortener.ts src/routes/shorten.ts`
- **T3 — Redirect with atomic counter**
  - **Objective:** `GET /:code` 302-redirects and increments clicks in one statement.
  - **Files:** `src/routes/redirect.ts`
  - **Depends on:** T2
  - **Done when:** `GET /:code` returns 302 to the target and the click count increases by exactly one per request under load.
  - **Validate:** `npm run test -- test/redirect.test.ts`
  - **Rollback:** `git restore src/routes/redirect.ts`

### M3 — Deploy

- **T4 — Container + smoke CI**
  - **Objective:** Build a runnable image and a CI job that boots it and hits `/health`.
  - **Files:** `Dockerfile`, `.github/workflows/ci.yml`
  - **Depends on:** T3
  - **Done when:** CI builds the image, starts it, and `curl -fsS localhost:3000/health` exits 0.
  - **Validate:** `docker build -t shortener . && docker run -d -p 3000:3000 shortener && sleep 2 && curl -fsS localhost:3000/health`
  - **Rollback:** `git restore Dockerfile .github/workflows/ci.yml`

## Checkpoints

### After M1
- **Gate:** T1 complete and validated
- **Validate:** `npm run test -- test/spike/idempotency.test.ts`
- **Rollback:** `git reset --hard <pre-M1 commit>`

### After M2
- **Gate:** T2, T3 complete and validated
- **Validate:** `npm run test`
- **Rollback:** `git reset --hard <pre-M2 commit>`

### After M3
- **Gate:** T4 complete; smoke CI green
- **Validate:** `npm run test && docker build -t shortener .`
- **Rollback:** `git reset --hard <pre-M3 commit>`

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Counter race under concurrent redirects | Medium | High | Single-statement `UPDATE ... RETURNING`; load-tested in T3 |
| Hash collision on url_hash | Low | High | Unique constraint + `ON CONFLICT`; collision surfaces as a constraint error, not silent overwrite |

## Validation

- `npm run test` — full suite green
- `npm run lint && npx tsc --noEmit` — lint and types clean
- `docker build -t shortener .` — image builds

## Stop conditions

- The redirect or shorten path needs to touch auth — out of scope; stop and ask.
- A schema change beyond the `urls` table is required — stop and ask before migrating.
- Validation fails and the fix needs new dependencies — stop and ask.

## Next step

Implement T1 — write the concurrency spike test against `ON CONFLICT ... RETURNING` and confirm one row per URL.

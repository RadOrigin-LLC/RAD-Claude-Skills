# Plan: URL Shortener Service

**Status:** APPROVED
**Updated:** 2026-06-06
**Pending durable-doc updates:** see `2026-06-06-update-prompt.md`

> **How to read this plan:** the Release map says where this effort fits on the road
> to the end goal. Milestones are the chunks of work, each with an *After this ships*
> line saying what you can do once it lands. The task blocks underneath are precise
> instructions for the coding agent — you don't need to parse every field. Stop
> conditions are where the agent must halt and ask instead of guessing.

## Objective

Ship a single-tenant URL shortener with idempotent shortening and an atomic click
counter, deployable as one container. Worth doing now because an internal tool needs
short links this sprint and no shared service exists yet.

**End goal:** The team's default link service — short links with click analytics that
internal tools call via API instead of each building their own.

## Release map

- **Now — MVP (this plan):** shorten + redirect with a click counter, in one
  container, for a single internal consumer.
- **Next — V1:** milestone outline only
  - Vanity/custom short codes
  - A minimal click-stats endpoint (counts per code, no dashboard)
  - Auth token so a second team can consume the API safely
- **Later — the end goal:**
  - Analytics dashboard
  - Multi-tenant isolation when a second heavy consumer appears

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

*After this ships: nothing user-visible yet — we've proven the trickiest part (the
same URL always gets the same code, even under load) before building on it.*

- **T1 — Validate idempotent insert under concurrency**
  - **Objective:** Prove `ON CONFLICT (url_hash) DO NOTHING ... RETURNING` returns a stable code under parallel inserts of the same URL.
  - **Files:** `src/db/schema.ts`, `test/spike/idempotency.test.ts`
  - **Depends on:** none
  - **Done when:** 100 concurrent inserts of one URL yield exactly one row and one code.
  - **Validate:** `npm run test -- test/spike/idempotency.test.ts`
  - **Rollback:** `git restore src/db/schema.ts test/spike/`

### M2 — Core service

*After this ships: you can shorten a URL and the short link redirects — the product
works on your machine.*

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

*After this ships: the shortener runs as a real service others can use, and CI proves
every change still boots.*

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

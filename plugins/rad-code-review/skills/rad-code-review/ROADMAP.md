# RAD Code Review — Roadmap

## v5.1 (current)

**Backend-as-a-Service data-exposure coverage + security-deep launch-readiness mode.** Closes the biggest gap for BaaS-backed apps, where the database (RLS / Security Rules) is the authorization layer rather than server middleware — the realistic customer-data-leak path that the framework-IDOR heuristics (§2.4) don't cover.

- **Security checklist §2.5 "Backend-as-a-Service: the database is your authorization layer"** — Supabase/PostgREST RLS, Firebase (Firestore/RTDB/Storage rules + Admin SDK), and Appwrite/PocketBase/Nhost/Amplify. Covers missing/permissive RLS, the `user_metadata` untrusted-claim escalation, anonymous-sign-in `authenticated`≠authorized, RLS-not-traversing-joins, `service_role`/Admin keys in client/public-env, `security definer` bypass, Storage/Realtime/edge-function leaks, and a **reachability gate** (exposed schema + grant + no policy) so RLS-off-but-unreachable tables don't false-positive. Includes a "do NOT flag" list (the anon/publishable key in client code is correct by design).
- **`severity-model.md`** — BaaS data-exposure rows in the Critical/Major tables, a reachability gate, and a never-downgrade rule for anon-reachable tables.
- **Stack detection (Step 3b)** — Supabase/Firebase/Appwrite/PocketBase/Nhost/Amplify markers, plus a public-env-prefix scan for leaked `service_role`/Admin keys.
- **`--security-deep` mode / `launch` strictness** (realizes the v3.1-planned threat-model + security-only ideas) — a focused launch-readiness pass (trust boundaries → data-exposure surface → authorization model → secrets) with a threat-model-lite report section and a **no-false-assurance contract**: never emits a "safe to launch" verdict, reports verified-vs-could-not-verify, and recommends an independent human pen-test. See `references/security-deep-mode.md`.
- Grounded in current advisories (the CVE-2025-48757 missing-RLS class, Supabase publishable/secret key model, OWASP API Security Top 10 BOLA/BOPLA/BFLA) and adversarially reviewed for missing vectors and false positives before shipping.

## v5.0

**Shorter IDs, honest flags, wired validator.** Finding IDs `CR-NNN` (config/state paths unchanged); `check-hallucinated-imports.py` wired into automated checks (Step 5g, offline); fingerprint-based history comparison (per-run IDs never compared across runs); `--engine claude|codex|both` removed — it implied Codex execution that was never implemented; `--adversarial-model` provides the real cross-model pass; reports save to `.radcr/history/` only; model references de-versioned.

## v3.0

**Optimized for Claude Opus** — major platform-level upgrade, no new review dimensions. Retains full compatibility with Sonnet and (for narrow scopes) Haiku.

- **Opus as default primary-review model** — agent and skill both default to Opus; `--model sonnet|haiku` overrides per-run; `.radcrconfig.yml` `review_model` sets a project default.
- **Parallel tool-call pipeline** — agent Phase 1 issues Glob/Grep/Read as a single parallel batch. Orchestrator Steps 3a–3e run in parallel. Step 5 automated checks (npm audit, pip-audit, gitleaks, tsc, eslint, etc.) run concurrently via `run_in_background` instead of one after another.
- **JSON-first subagent output** — primary and adversarial subagents emit structured JSON per the schema in `references/subagent-prompts/*.md`. Orchestrator parses JSON as authoritative. Markdown fallback retained for legacy resilience.
- **Compaction-safe checkpointing** — state written to `.radcr/state/<run-id>.json` after Steps 5, 7, 9. `--resume <run-id>` rehydrates mid-review and continues from the last checkpoint. Long reviews of 500+ file repos no longer lose progress when context compacts.
- **`--non-interactive` mode** — Step 10 menu is skipped; findings, verdict, and report path return as structured data. Used by the `code-reviewer` agent, `/loop` sessions, and CI integrations.
- **Externalized subagent prompts** — moved from inline in `orchestrate-review.md` Step 6/8 to `references/subagent-prompts/{primary,adversarial,self-adversarial}-review.md`. Cleaner orchestrator, easier to audit and version.
- **`.radcrconfig.yml` accepted-risk expiry enforcement** — entries with `expires < today` are surfaced as stale and re-evaluated rather than silently suppressed. Prevents permanent suppression via never-reviewed acceptances.
- **Structured JSON blame context** — Step 3f now emits a single JSON document with per-file changed ranges, blame metadata (scoped to changed lines only via `git blame -L`), and dependency edges. Replaces the prose "annotated diff context document" — smaller, more reliable, faster to produce on large diffs.
- **History filename unified** — `{YYYY-MM-DD}-{HHmmss}-{scope}-{strictness}.md` across both orchestrator and report-generation. Multiple same-day reviews no longer overwrite.
- **Cleanup** — removed vestigial `install.sh`/`install.ps1` (handled by plugin manifest) and unused `scripts/*.sh` that no workflow referenced.

## v2.1

Interactive findings menu — accept specific findings or all minor findings as intentional, persisted to `.radcrconfig.yml` with 1-year expiry and optional justification. Show-new-only mode filters the current report against `.radcr/history/` to surface only findings introduced since the last review. First-run `.radcrconfig.yml` creation with optional `.gitignore` integration.

## v2.0

Diff-aware scoping, actionable detection heuristics, and practical PR workflow support.

- Blame-aware diff scoping — `diff` and `commit` scopes only flag issues on changed lines by default, with dependency chain detection for pre-existing issues that new code depends on
- Incremental review (`--since <commit>`) — review all changes since a specific commit, with blame-aware filtering
- `--full-scan` override — opt out of blame-aware filtering to get v1.0-style full review on any scope
- Framework-specific IDOR detection — concrete grep-able mutation ownership patterns for Next.js Server Actions, Next.js API Routes, Express/Fastify, Django/DRF, Rails, and Go (Gin/Echo/Chi/net/http), plus multi-tenant isolation checks
- Performance profiling heuristics — 8 detection patterns: N+1 queries in loops, unnecessary React re-renders, unbounded list rendering, synchronous blocking in handlers, missing pagination, bundle bloat indicators, missing caching, missing database indexes
- Dynamic ARIA state detection — catches hardcoded `aria-expanded`, `aria-selected`, `aria-checked`, `aria-pressed`, and frozen `aria-hidden` as string literals instead of dynamic values
- Finding attribution — every finding tagged as `introduced`, `pre-existing-dependency`, or `pre-existing-secret` for clear signal in PR review workflows
- Adversarial blame validation — adversarial pass verifies blame-scoping decisions to catch issues that were incorrectly filtered or incorrectly included

## v1.0

The foundation. A complete code review skill.

- Full 10-category review (functional, security, AI slop, architecture, tests, performance, UX, accessibility, release readiness, documentation)
- 8 project-type modules (web app, API, Chrome extension, CLI, library, Electron, mobile, SaaS)
- Sequential adversarial review (the v1.0 docs described a "dual-engine Claude+Codex" mode; the Codex half was never actually implemented and the flag was removed in v5.0)
- Review-of-review calibration pass
- Fix application with build/test validation
- Structured JSON report with severity-ranked findings
- Report history and comparison between runs
- `.radcrconfig.yml` project-level configuration
- Local-only mode (no network dependencies)
- Dependency vulnerability audit (npm, pip, cargo, go — when the matching tool is installed)
- License compliance checking with copyleft detection
- Secrets scanning (gitleaks + pattern fallback, never exposes values)
- Cross-platform install (bash + PowerShell)

## v3.1 (planned — deferred from v2.1 roadmap)

Deeper domain-specific review capabilities. *(Threat-model mode and the `security-only`-style focused pass shipped in v5.1 as `--security-deep` / `launch`; the remaining items below are still planned.)*

- **Threat model mode** — ✅ shipped in v5.1 as the security-deep threat-model-lite output (attack surfaces, trust boundaries, data-flow risks).
- **API contract review** — Validate that implementation matches OpenAPI/Swagger schema. Detect undocumented endpoints, missing error responses, request/response type mismatches, and breaking changes between schema versions.
- **Schema/migration review** — Analyze database migrations for: data loss risk, missing rollback, index performance, constraint correctness, and compatibility with ORM models. Support for SQL migrations, Prisma, Alembic, ActiveRecord, and Flyway.
- **Infra/deploy config deep review** — Extended analysis of Dockerfiles, Kubernetes manifests, Terraform/Pulumi configs, CI/CD pipelines, and cloud IAM policies.
- **`security-only` strictness level** — ✅ effectively shipped in v5.1: `--security-deep` concentrates the review on data-exposure/authorization/secrets and de-prioritizes architecture/UX/a11y/perf.

## v4.0 (planned)

Interactive and visual review capabilities, plus extensibility.

- **Accessibility deep-dive mode** — Interactive accessibility audit using Playwright to render pages, run axe-core, check keyboard navigation, verify ARIA attributes, test screen reader compatibility, and validate color contrast.
- **UI/UX teardown mode** — Visual analysis via screenshots. Review layout consistency, spacing, typography hierarchy, interactive element sizing, loading states, error states, empty states, and responsive breakpoints.
- **Performance-focused mode** — Integrate with profiling data (Lighthouse, webpack-bundle-analyzer, py-spy, Go pprof) to correlate code patterns with measured performance characteristics.
- **Custom project-type module support** — User-defined project-type modules in `.radcr/project-types/` that extend or override built-in modules.
- **Plugin system for custom checks** — Define custom review rules as small scripts or prompt fragments.

## v5.0 (future)

Cross-service intelligence and continuous operation.

- **Multi-repo/monorepo cross-service analysis** — Review changes in context of the full service graph.
- **Runtime behavior verification integration** — Correlate code review findings with runtime data from APM tools.
- **Production incident correlation** — Given a post-mortem, trace root cause back to specific code patterns.
- **Continuous review mode** — Watch for code changes and run incremental reviews automatically.

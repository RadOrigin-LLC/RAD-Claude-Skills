# Changelog

All notable changes to `rad-coolify-orchestrator` will be documented in this file.

## [2.1.0] - 2026-06-10

### Fixed
- **coolify-reviewer Step 0 was unwired**: validator commands referenced `${plugin_root}`, which is not a real variable (`${CLAUDE_PLUGIN_ROOT}` is) — the four Python validators silently never ran and the agent fell back to LLM-only review. Also made the invocation cross-platform: interpreter resolved via `command -v python3 || command -v python` (python3 doesn't exist on most Windows installs), stdout captured directly instead of writing to `/tmp/`.
- **MCP env var endpoints didn't match the OpenAPI spec**: `coolify_list_env_vars`/`coolify_create_env_var` called `/applications/{uuid}/environment-variables`; the spec path is `/applications/{uuid}/envs`. Healthcheck now tries `/health` (spec) with `/healthcheck` fallback for older instances.
- **Env var guidance corrected** in coolify-actions: changes take effect on the next *deploy* (`coolify_deploy`), not on restart — a restart reuses the existing container with old values. Workflow 6 previously said "redeploy" but showed `coolify_restart_application`.
- **Workflow 10 backup wording corrected**: `POST /databases/{uuid}/backups` creates a *scheduled backup config*, not a one-off manual backup run (no trigger-now endpoint exists in the API).
- **De-versioned model references** (Opus 4.7/Sonnet 4.6/Haiku 4.5 → Opus/Sonnet/Haiku) in agent prose, README, and plugin.json per suite policy.

### Added
- **MCP server v1.1.0 — 9 new tools (27 → 36)**: `coolify_update_env_var`, `coolify_delete_env_var`, `coolify_cancel_deployment`, `coolify_list_running_deployments`, `coolify_start_service`, `coolify_stop_service`, `coolify_restart_service`, `coolify_list_database_backups`, `coolify_list_backup_executions`. All endpoints verified against Coolify's OpenAPI spec (`main`, June 2026). Closes the gaps where coolify-actions promised intents (update env var, service lifecycle, backup history) the MCP couldn't perform.
- **`coolify-status` skill** — one-shot read-only "is everything up" dashboard: healthcheck → version → servers → resources → in-flight deployments, leads with problems, grounds version-specific advice on `coolify_version` instead of doc snapshots.
- **PostToolUse hook (`hooks/post-edit-lint.py`)** — after Claude edits a `Dockerfile*` or compose file, the matching linter runs automatically (`--json`) and CRITICAL/WARNING findings surface as context. Silent on clean/non-Docker files, never blocks, always exits 0. Tested against dirty/clean Dockerfile and compose fixtures.
- coolify-actions workflows extended: env var update/delete, service lifecycle, cancel-in-progress deploy, scheduled-backup configs + execution history; tool quick-reference table updated.

### Changed
- README freshness pattern: "latest is beta.474" claim replaced with "last verified against beta.474 (April 2026)" + live grounding via `coolify_version` — rolling-beta version claims rot too fast to hardcode.
- `coolify_create_env_var`: `is_build_time` now optional and only sent when explicitly set (current Coolify unified build/runtime envs and dropped the flag from the spec; older instances still accept it).

## [2.0.0] - 2026-04-27

### Added (mechanism)
- `scripts/lint-dockerfile.py` — Coolify-specific Dockerfile linter (unpinned base, missing USER/EXPOSE/HEALTHCHECK, secret-shaped ARGs/ENVs, single-stage warning, COPY . reminder)
- `scripts/lint-compose.py` — Coolify-specific docker-compose validator (missing healthchecks/restart, hardcoded secrets, privileged mode, port conflicts with Coolify reserved ports 80/443/8000, stateful services without volumes)
- `scripts/check-coolify-env.py` — env handling validator (.env in git, .gitignore gaps, hardcoded secrets across files, Nixpacks version-pin gap)
- `scripts/audit-cicd.py` — CI/CD validator (curl without --fail, hardcoded webhook URLs/tokens, :latest image tags, missing test gate, missing post-deploy status check)
- `scripts/README.md` — full script docs + when-the-agent-runs-which table
- All scripts pure stdlib Python 3.8+, end-to-end tested against deliberately broken fixtures

### Updated (current Coolify state, April 2026)
- **Build packs:** Nixpacks flagged as in maintenance mode (Railway moved focus to Railpack in 2025); Railpack reframed from "available with opt-in" to "NOT yet a Coolify build pack option" (active community discussion #5282/#5519/#7983 but no merged PR)
- **Reverse proxy:** Caddy added as experimental alternative to Traefik (added at beta.237) — coolify-deploy SKILL covers both
- **Shared variables:** expanded to 4 scopes (server/team/project/environment) with `{{scope.VAR}}` interpolation syntax (beta.471, April 2026) — coolify-security SKILL updated
- **API token expiration:** new in beta.474 — coolify-cicd/api-reference.md updated
- **PostgreSQL 18 + pgvector 18:** added in beta.463 (Feb 2026) — coolify-databases SKILL updated
- **Webhook canonical method is GET** per Coolify's own docs (POST also works) — coolify-cicd SKILL updated to show both
- **HMAC webhook signing strengthened** in beta.474 — noted in coolify-cicd
- **Old container accumulation in Swarm rolling updates** (Issue #8299, Feb 2026) — bug noted in swarm-guide.md

### Honest framing pass
- **"Zero-downtime"** reframed in coolify-deploy SKILL with explicit conditions (single-container only, no host port bindings, working healthcheck, attachable volumes; recreate strategy fallback when conditions fail)
- **Sentinel** explicitly framed as "lightweight metrics side-car, not full observability" in coolify-observability SKILL — clarifies CPU/RAM/disk/network only, no log aggregation, no tracing, no APM
- **API stability caveats** added to coolify-cicd/api-reference.md (Issues #7702, #8782 — spec-vs-behavior gaps documented)
- **Coolify v4 is rolling beta** explicitly stated in coolify-deploy SKILL (latest is `v4.0.0-beta.474`, ~474 betas over 2 years, v4.0.0 stable milestone not closed)
- **Coolify Cloud disambiguation** in plugin description (managed product, $5/month + $3/server, out of scope for this plugin)
- **Coolify v5 in early development** noted (April 2025 announcement, full PHP rewrite, no release date)
- **Docker Swarm itself supported through 2030** (Mirantis) — clarifies that the "experimental" label is about Coolify integration, not Swarm viability

### Updated (agent — Opus 4.7 platform pass)
- `coolify-reviewer` agent: **Opus 4.7 default** (with Sonnet 4.6 fallback note)
- New "Step 0: Run the deterministic validators" — agent invokes the four scripts before LLM judgment passes
- Steps 2-5 reframed as "judgment-only — script already covered structure"
- New JSON output mode (`--json`) for skill consumption alongside markdown for human reading
- Mechanism-first architecture documented at top of agent file

### Verified
- Bundled `@radoriginllc/coolify-mcp` confirmed published on npm at v1.0.0; 27 tools verified in source vs README
- All major technical claims (Sentinel, Swarm, UFW+Docker, API endpoints, database engines) re-verified against current Coolify docs and GitHub issues

## [1.0.0] - 2026-04-03

### Added
- Initial release with 7 skills: deploy, databases, security, cicd, troubleshoot, observability, infrastructure
- coolify-reviewer agent for autonomous Coolify config/Dockerfile auditing
- Decision trees for build pack selection, database provisioning, troubleshooting flows
- Anti-pattern documentation for all domains
- Runnable commands and worked examples throughout
- Coverage report documenting research sources and confidence levels

### Notes
- All content verified against Coolify v4.x self-hosted
- Swarm and Railpack content marked as experimental
- Multi-server content sourced from official docs + community patterns

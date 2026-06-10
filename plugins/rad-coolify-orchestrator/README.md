# rad-coolify-orchestrator — Deploy, manage, and troubleshoot self-hosted apps on Coolify — from Claude Code.

Coolify is a self-hosted Heroku/Netlify alternative with its own patterns for Dockerfiles, environment variables, Traefik (or Caddy) routing, and rolling deployments. rad-coolify-orchestrator teaches Claude those patterns so you're not guessing at configuration or debugging 502s without a clear mental model. Plus it ships **four Python validators** that catch the patterns the LLM reviewer can miss when eyeballing files.

## Read this first: scope and honest framing

- **Self-hosted only.** All content assumes self-hosted Coolify v4.x. **Coolify Cloud** (managed control plane, $5/month + $3/month per server, launched 2025) is a different product — many things differ.
- **Coolify v4 is a rolling beta.** This plugin's content was last verified against `v4.0.0-beta.474` (April 2026); Coolify ships new betas constantly, so don't treat that as "latest" — when version-specific behavior matters, the plugin checks your actual instance via the MCP `coolify_version` tool instead of assuming. Pin to a specific Coolify version for production automation.
- **No Kubernetes support.** Plugin covers Coolify's actual orchestration: single-server (default) and Docker Swarm (experimental in Coolify, but Swarm itself is supported by Mirantis through 2030).
- **Sentinel is a metrics side-car, not full observability.** CPU/RAM/disk/network only. No log aggregation, no tracing, no APM. Add Grafana+Prometheus or external APM for real observability.
- **"Zero-downtime" deploys have conditions** — single-container only (not docker-compose), no host port bindings, working healthcheck, volumes attachable to multiple containers. When conditions fail, Coolify falls back to recreate strategy (brief downtime).

## What you can do with this

- Deploy an application to Coolify with the right build pack and health check configuration
- Diagnose 502/504 errors, failed deployments, and Traefik routing issues with a structured approach
- Set up environment variables and secrets without exposing them in Dockerfiles or build logs (with mechanism — `check-coolify-env.py` actually scans for hardcoded secrets)
- Configure CI/CD pipelines that trigger Coolify deployments from GitHub Actions (with mechanism — `audit-cicd.py` catches missing `--fail`, exposed tokens)
- Have Claude run live operational queries against your Coolify instance (via the bundled MCP server)

## How it works

| Skill | Purpose |
|---|---|
| `coolify-deploy` | Build packs (Nixpacks/Static/Dockerfile/Compose), Caddy alternative proxy, deployment configuration, rolling updates with honest conditions |
| `coolify-databases` | One-click engines (PostgreSQL 13-18, MySQL, MariaDB, MongoDB, Redis, KeyDB, Dragonfly, ClickHouse), backups, restore, connection patterns |
| `coolify-security` | Secrets management, BuildKit secrets, RBAC, **shared variables (server/team/project/environment scopes — new in beta.471)** |
| `coolify-cicd` | GitHub Actions, GitLab CI, REST API (with stability caveats), webhooks (GET canonical), token expiration, HMAC signing |
| `coolify-infrastructure` | Multi-server, Docker Swarm (experimental, with bug notes), build servers |
| `coolify-observability` | Sentinel (honest scope: metrics side-car only), notification channels, log drains (Axiom, Loki, New Relic, FluentBit), Uptime Kuma |
| `coolify-troubleshoot` | 502/504 diagnosis, Traefik routing, container failures, deployment errors, SSL issues |
| `coolify-actions` | MCP-based operational actions against a live Coolify instance — uses the bundled `@radoriginllc/coolify-mcp` (36 tools) |
| `coolify-status` | One-shot read-only "is everything up" dashboard — health, version, servers, resources, in-flight deployments |

| Agent | Purpose |
|---|---|
| `coolify-reviewer` | Reviews Coolify configs, Dockerfiles, compose, env, and CI/CD. **2.0: runs 4 Python validators first (mechanism), then applies LLM judgment to what scripts can't see.** Opus default. |

| Hook | Purpose |
|---|---|
| `post-edit-lint` (PostToolUse) | After Claude edits a Dockerfile or compose file, the matching linter runs automatically and surfaces CRITICAL/WARNING findings immediately — guardrails without invoking the reviewer. Silent on clean/non-Docker files, never blocks. |

| Script | Purpose |
|---|---|
| `scripts/lint-dockerfile.py` | Coolify-specific Dockerfile linter — unpinned base images, missing USER/EXPOSE/HEALTHCHECK, secret-shaped ARGs/ENVs, single-stage warning |
| `scripts/lint-compose.py` | Coolify-specific compose validator — missing healthchecks/restart, hardcoded secrets, privileged mode, port conflicts with Coolify reserved ports (80/443/8000), stateful services without volumes |
| `scripts/check-coolify-env.py` | Env handling — `.env` in git, `.gitignore` gaps, hardcoded secrets across files, Nixpacks version-pin gap |
| `scripts/audit-cicd.py` | CI/CD validator — curl without `--fail`, hardcoded webhook URLs/tokens, `:latest` tags, missing test gate, missing post-deploy status check |

All scripts are pure Python 3.8+ stdlib. No `pip install` required.

## What's NEW in 2.1

- **MCP server expanded to 36 tools** (was 27): update/delete env vars, cancel deployment, list running deployments, service start/stop/restart, scheduled-backup configs + execution history. Closes the gaps where `coolify-actions` workflows promised intents the MCP couldn't perform.
- **Two endpoint fixes in the MCP**: env vars now use the spec path `/applications/{uuid}/envs` (was `/environment-variables`, not in the OpenAPI spec); healthcheck tries `/health` with `/healthcheck` fallback for older instances.
- **New `coolify-status` skill** — one-shot read-only dashboard (health → version → servers → resources → in-flight deploys), grounding version-specific advice on `coolify_version` instead of doc snapshots.
- **New PostToolUse hook** — editing a Dockerfile/compose file auto-runs the matching linter and surfaces findings immediately.
- **coolify-reviewer fixed and cross-platform**: validator invocation now uses `${CLAUDE_PLUGIN_ROOT}` (the previous `${plugin_root}` variable didn't exist, so Step 0 silently never ran), resolves `python3`/`python` portably, and no longer depends on `/tmp`.
- **Env var guidance corrected**: changes take effect on the next *deploy* — a restart reuses the old container env.

## What's NEW in 2.0

### Mechanism (4 Python validators)
The `coolify-reviewer` agent now runs four scripts as Step 0 before LLM judgment. Same pattern as rad-planner's `risk-assessor` + `plan-lint.py`. Converts "I'll check your Dockerfile" from LLM eyeballing to deterministic Python — saves tokens, gives reproducible results, and lets the LLM focus on what scripts can't see (semantic healthcheck quality, cross-file consistency, intent).

### Honest framing updates
- **Nixpacks is in maintenance mode** (Railway moved focus to Railpack in 2025) — flagged in `build-packs.md`. Practical impact: very recent runtime versions (Node 24+) may not be available; use Dockerfile as the escape hatch.
- **Railpack is NOT yet a Coolify build pack option** — earlier docs implied it was available with opt-in. Reality: active community discussion (#5282, #5519, #7983), no merged PR. Plugin now states this clearly.
- **Caddy added as experimental alternative proxy** (beta.237) — `coolify-deploy` SKILL now mentions both options with caveats.
- **"Zero-downtime"** reframed with explicit conditions in `coolify-deploy` SKILL.
- **Sentinel** explicitly framed as metrics side-car (not observability solution) in `coolify-observability` SKILL.
- **API stability** caveats added to `coolify-cicd` reference (Issues #7702, #8782 — spec-vs-behavior gaps).
- **Coolify v4 is rolling beta** — explicit in deploy SKILL; pin Coolify version for production automation.

### Updates for new Coolify features (2025-2026)
- Shared variables expanded to **four scopes** (server/team/project/environment) with `{{scope.VAR}}` interpolation syntax (beta.471, April 2026) — documented in `coolify-security`.
- **API token expiration** (beta.474) — documented in `coolify-cicd/api-reference.md`.
- **PostgreSQL 18 + pgvector 18** (beta.463, Feb 2026) — added to `coolify-databases`.
- **Webhook canonical method is GET** (per Coolify's own docs); POST also works. Both forms documented in `coolify-cicd`.
- **HMAC webhook signing strengthened** (beta.474) — noted in `coolify-cicd`.
- **Old container accumulation in Swarm rolling updates** (Issue #8299, Feb 2026) — bug noted in `swarm-guide.md`.

### Platform pass
- `coolify-reviewer` agent: **Opus default** with Sonnet fallback note
- Mechanism-first execution model documented
- JSON output mode for skill consumption alongside markdown for human reading

## What this plugin does NOT do

- **Does not cover Coolify Cloud** — managed product is out of scope
- **Does not provide Kubernetes support** — Coolify itself doesn't support K8s; plugin covers actual options (single-server, Swarm-experimental)
- **Does not promise zero-downtime** — surfaces the conditions, you assess if your setup meets them
- **Does not validate deployment will succeed** — catches *patterns* that lead to failures; the actual deploy still has to work
- **Does not connect to your live Coolify** by itself — the bundled MCP server (`coolify-actions` skill) does that with your `COOLIFY_URL` + `COOLIFY_API_TOKEN`
- **Does not auto-fix issues** — reviews and reports; you decide what to change

## Quick Start

```bash
claude plugins add ./RAD-Claude-Skills/plugins/rad-coolify-orchestrator
```

### Bundled MCP server (36 tools)

This plugin bundles [`@radoriginllc/coolify-mcp`](https://www.npmjs.com/package/@radoriginllc/coolify-mcp) — v1.1.0, 36 tools across health/version, servers, projects, applications, deployments (incl. cancel + running list), env vars (full CRUD), databases (incl. backup configs + execution history), services (incl. lifecycle), and resources. All endpoints verified against Coolify's OpenAPI spec. Set two environment variables and the MCP auto-configures when you install the plugin:

```bash
export COOLIFY_URL=https://your-coolify-instance.example.com
export COOLIFY_API_TOKEN=your-api-token
```

### Example prompts

```
Review my Coolify deployment config         # → coolify-reviewer agent (runs scripts + LLM judgment)
Is everything up on Coolify?                # → coolify-status (read-only dashboard)
Why is my deployment failing?               # → coolify-troubleshoot
Set up CI/CD for Coolify                    # → coolify-cicd
Is my Dockerfile ready for Coolify?         # → coolify-reviewer (lint-dockerfile.py + judgment)
Deploy my app to Coolify                    # → coolify-actions (MCP)
Check what's running on my server           # → coolify-actions (MCP)
```

## Sources

The plugin's claims are grounded in:

- [Coolify Docs](https://coolify.io/docs/)
- [Coolify GitHub Releases](https://github.com/coollabsio/coolify/releases)
- [Coolify Build Packs Overview](https://coolify.io/docs/applications/build-packs/overview)
- [Coolify Sentinel docs](https://coolify.io/docs/knowledge-base/server/sentinel)
- [Coolify Swarm docs](https://coolify.io/docs/knowledge-base/docker/swarm)
- [Coolify API Authorization](https://coolify.io/docs/api-reference/authorization)
- [coollabsio/sentinel repo](https://github.com/coollabsio/sentinel)
- [Railpack project](https://railpack.com/) (upstream Beta, NOT yet a Coolify build pack)
- [chaifeng/ufw-docker](https://github.com/chaifeng/ufw-docker) (latest release Nov 2025; Docker UFW bypass still not natively fixed)
- [Mirantis Long-Term Support for Swarm through 2030](https://www.mirantis.com/blog/mirantis-guarantees-long-term-support-for-swarm/)
- [@radoriginllc/coolify-mcp on npm](https://www.npmjs.com/package/@radoriginllc/coolify-mcp)

When the plugin makes a factual claim, it cites the source. When something is opinionated or experimental, it says so.

## License
Apache-2.0

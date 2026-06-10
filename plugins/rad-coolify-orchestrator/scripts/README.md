# rad-coolify-orchestrator scripts

Mechanical validators that turn the coolify-reviewer agent's checklist from "I'll look at your Dockerfile" into "Python ran four scanners and found these specific issues." Same pattern as rad-planner's `plan-lint.py`.

All scripts are pure Python 3.8+ stdlib. No `pip install` required (`lint-compose.py` will use PyYAML if it's installed for fuller YAML coverage, but the built-in fallback parser handles the subset docker-compose actually uses).

## lint-dockerfile.py

Catches Coolify-specific Dockerfile patterns:

```bash
python3 scripts/lint-dockerfile.py <Dockerfile>
python3 scripts/lint-dockerfile.py <project-root>      # finds Dockerfile* recursively
python3 scripts/lint-dockerfile.py <path> --json
python3 scripts/lint-dockerfile.py <path> --strict     # promote SUGGESTION to WARNING
```

**Catches:**
- Unpinned base images (`:latest` or no tag) — breaks reproducibility
- Missing USER directive (container runs as root) — security issue
- Missing EXPOSE directive — Coolify needs this for port auto-detection
- Missing HEALTHCHECK — Coolify rolling updates require it for zero-downtime
- ARG with secret-shaped name — build args bake into image layers
- ENV with hardcoded secret-looking value
- Single-stage builds where multi-stage would dramatically reduce image size
- COPY . with reminder about .dockerignore

**Exit codes:** `0` clean, `1` issues found, `2` script error.

## lint-compose.py

Catches Coolify-specific docker-compose patterns:

```bash
python3 scripts/lint-compose.py <compose.yml>
python3 scripts/lint-compose.py <project-root>          # finds compose files recursively
python3 scripts/lint-compose.py <path> --json
python3 scripts/lint-compose.py <path> --strict
```

**Catches:**
- Missing healthchecks — Coolify rolling updates require them
- Missing `restart: unless-stopped` — services don't auto-recover
- Hardcoded secrets in `environment:` blocks
- `--privileged: true` — disables container isolation
- Sensitive `cap_add` (ALL, SYS_ADMIN, NET_ADMIN, DAC_OVERRIDE)
- Stateful services (postgres, mysql, mongo, redis, etc.) without volume mounts → **data loss risk**
- Port conflicts with Coolify's reserved ports (80, 443, 8000, 6001, 6002)
- Privileged port bindings (<1024)
- Services missing `coolify` network attachment when project uses it

**Exit codes:** `0` clean, `1` issues found, `2` script error.

## check-coolify-env.py

Validates env handling across the project:

```bash
python3 scripts/check-coolify-env.py <project-root>
python3 scripts/check-coolify-env.py <project-root> --json
python3 scripts/check-coolify-env.py <project-root> --strict
```

**Catches:**
- `.env` file present at project root (verify it's not committed)
- `.gitignore` missing `.env` / `.env.*` patterns
- Hardcoded secrets across `.env`, `Dockerfile`, `docker-compose.yml` (regex against secret-shaped names + secret-shaped values)
- Missing `.env.example` for contributor onboarding
- Nixpacks-detected stack without `NIXPACKS_*` version pins → reproducibility risk now that Nixpacks is in maintenance mode (Railway moved focus to Railpack in 2025)

**Exit codes:** `0` clean, `1` issues found, `2` script error.

## audit-cicd.py

Validates GitHub Actions / GitLab CI workflows that deploy to Coolify:

```bash
python3 scripts/audit-cicd.py <project-root>
python3 scripts/audit-cicd.py <path-to-workflow.yml>
python3 scripts/audit-cicd.py <path> --json
```

**Catches:**
- `curl` to Coolify deploy endpoint without `--fail` (silent failures — CI passes even when deploy trigger errors)
- Webhook URL with embedded uuid/token hardcoded in workflow file
- Bearer token literal in `Authorization` header (vs secret reference)
- `:latest` image tags (non-reproducible deploys)
- Deploy job with no detectable test step (broken code ships)
- Deploy step with no post-deploy status polling (CI passes before actual deploy completes)

**Exit codes:** `0` clean, `1` issues found, `2` script error.

## When the hook runs these (new in 2.1)

The `post-edit-lint` PostToolUse hook (`hooks/post-edit-lint.py`) runs `lint-dockerfile.py` or `lint-compose.py` automatically whenever Claude edits a `Dockerfile*` or `*compose*.yml/.yaml` file in any project, and surfaces CRITICAL/WARNING findings as context immediately. SUGGESTION-level findings are excluded from hook output to keep the signal high — run the agent for the full report. The hook is silent on clean files and non-Docker files, and never blocks.

## When the agent runs these

The `coolify-reviewer` agent is updated in 2.0 to invoke these scripts as Step 0 (before LLM-based passes), then apply LLM judgment only to what scripts can't see (e.g., is the healthcheck endpoint actually checking dependencies, is the Traefik routing semantically correct, etc.). Same pattern as rad-planner's risk-assessor:

| Reviewer pass | Was (1.x) | Is (2.0) |
|---|---|---|
| Dockerfile review | LLM eyeballs each line | `lint-dockerfile.py` runs first; LLM focuses on judgment-required (Dockerfile *intent*, custom RUN commands) |
| Compose review | LLM eyeballs each service | `lint-compose.py` runs first; LLM focuses on cross-service patterns |
| Env review | LLM scans for secrets visually | `check-coolify-env.py` runs first; LLM focuses on whether the env split (build vs runtime) makes sense for the app |
| CI/CD review | LLM eyeballs workflows | `audit-cicd.py` runs first; LLM focuses on workflow structure beyond hardcoded patterns |

## What these scripts deliberately do NOT do

- **Don't validate the deployment will actually succeed** — they catch *patterns* that lead to failures, not the failures themselves
- **Don't run `docker build` or `docker compose config`** — file-text analysis only
- **Don't make network calls** — no Coolify API checks (use `coolify_healthcheck` MCP tool for that)
- **Don't claim to catch all secrets** — heuristics (secret-shaped names + token patterns); high-entropy random-looking strings inside legitimate config will sometimes false-positive, and well-disguised secrets will be missed
- **Don't replace the LLM reviewer** — they handle the mechanical checks so the LLM can focus on judgment-required ones

## Honest scope statement

These scripts encode the patterns that experienced Coolify operators check. They're not an authoritative validator (Coolify itself doesn't ship one), and they reflect 2026 conventions that may evolve. When Coolify changes (new build packs, new proxy options, new env-var scopes), these scripts may lag — re-run the agent's full LLM judgment pass alongside the scripts for completeness.

# Archived Plugins

These plugins are paused — they remain in the repository for reference and potential revival, but are **not** listed in the marketplace and will not be installed by anyone browsing `RadOrigin-LLC/RAD-Claude-Skills`.

## Why archived

Two waves of archival:

**Single-framework reviewers (April 2026).** Modern frontier coding models (Opus 4.7+) have strong baseline knowledge of these frameworks and languages. The skills here mostly duplicated that baseline knowledge without adding meaningful uplift, and contributed noise to skill selection. Generic "best practices" and "anti-pattern" skills for popular frameworks were the lowest-leverage portion of the toolkit. Reviewer agents in these plugins were partially redundant with [`rad-code-review`](../plugins/rad-code-review), which orchestrates ship-readiness reviews using a stack-aware approach.

**Wide-surface productivity wrappers (April 2026).** `rad-google-workspace` exposed 93 skills (44 services + 41 workflow recipes + 10 personas) — too wide a surface for routine use, and the workflow/persona skills duplicated what Opus 4.7 can compose on its own from the underlying service skills. Superseded by [`rad-gws-core`](../plugins/rad-gws-core), the focused 14-skill subset covering everyday productivity (Gmail send/read/reply/triage, Docs write, Sheets read/append, Slides, Drive, Calendar). Both depend on the same `gws` CLI binary, so anyone who needs the broader surface can still install from the archive.

**Lifecycle consolidation (April 2026).** `rad-stack-guide` had two jobs: stack detection (one-time per project) and review orchestration (specialist-reviewer dispatch). Its stack-detection value duplicated rad-session's `/startup` Phase 2.5 Resource Discovery, and its review-orchestration value collapsed when the framework reviewers above were archived — there were no specialists left to orchestrate. Superseded by [`rad-session`](../plugins/rad-session) 3.0, which absorbed the per-project setup phase as `/init` so one plugin owns the whole lifecycle (`/init` → `/startup` → `/wrapup`). Existing CLAUDE.md content from the old `/detect-stack` skill stays valid; running `/rad-session:init` once re-establishes the `## Resources` section in the new format.

## Archived plugins

| Plugin | Notes |
| --- | --- |
| `rad-astro` | Astro 5/6 standards, a11y, perf, security |
| `rad-fastify` | Fastify encapsulation, hooks, schemas, testing |
| `rad-google-workspace` | Full Google Workspace — 44 service skills + 41 workflow recipes + 10 role personas. Superseded by [`rad-gws-core`](../plugins/rad-gws-core) (14 essential skills). |
| `rad-nextjs` | App Router, RSC, security, testing |
| `rad-react` | React 19 patterns, hooks, security, perf |
| `rad-stack-guide` | Stack detection + specialist reviewer orchestration. Superseded by [`rad-session`](../plugins/rad-session) 3.0 — stack detection moved into `/init`; review orchestration deprecated when framework reviewers were archived. |
| `rad-stripe-fastify-webhooks` | Stripe webhook handling, idempotency, Zod contracts |
| `rad-typescript` | Strict mode, type narrowing, API safety |
| `rad-zod` | Zod v4 schemas, error handling, integrations |

## How to restore one

```bash
# 1. Move it back
git mv archive/plugins/rad-zod plugins/rad-zod

# 2. Re-add its entry to .claude-plugin/marketplace.json
#    (copy the shape of an existing entry — name, source, description, category, homepage, license)

# 3. Bump marketplace version, commit, push.
```

If reviving multiple, consider whether the underlying premise — that frontier models cover this baseline — has changed. If a specific skill turned out to provide unique uplift (e.g., a version-specific migration guide), prefer extracting that single skill rather than reviving the whole plugin.

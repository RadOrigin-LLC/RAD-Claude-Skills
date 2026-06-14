# Archived Plugins

These plugins are paused — they remain in the repository for reference and potential revival, but are **not** listed in the marketplace and will not be installed by anyone browsing `RadOrigin-LLC/RAD-Claude-Skills`.

## Why archived

Plugins land here for a few recurring reasons:

- **Superseded by a successor.** `rad-session` was rebuilt as [`rad-repo-manager`](../plugins/rad-repo-manager) around a minimal four-doc core (`AGENTS.md`, `docs/prd.md`, `docs/plan.md`, `docs/handoff.md`). Its older canonical doc tree (`docs/status.md`, `docs/planning/current.md`, plus vision / architecture / decisions) had grown redundant and confused coding agents. The old skills don't carry forward — the doc model changed underneath them.
- **Baseline now covered by the model.** The single-framework reviewer plugins (React, Next.js, Astro, Fastify, TypeScript, Zod, Stripe webhooks) mostly restated knowledge current frontier models already have, and added noise to skill selection. Ship-readiness review lives in [`rad-code-review`](../plugins/rad-code-review), which is stack-aware.
- **Surface too wide for routine use.** `rad-google-workspace` exposed the full Google Workspace API surface — more than most projects need day to day, and its workflow/persona skills duplicated what the model can compose from the underlying service skills.
- **Job absorbed elsewhere.** `rad-stack-guide` did stack detection and reviewer orchestration; stack detection folded into the session lifecycle, and reviewer orchestration had nothing left to orchestrate once the framework reviewers were archived.

## Archived plugins

| Plugin | Notes |
| --- | --- |
| `rad-astro` | Astro 5/6 standards, a11y, perf, security |
| `rad-fastify` | Fastify encapsulation, hooks, schemas, testing |
| `rad-google-workspace` | Full Google Workspace integration — service skills, workflow recipes, and role personas. Requires the `gws` CLI. |
| `rad-nextjs` | App Router, RSC, security, testing |
| `rad-react` | React 19 patterns, hooks, security, perf |
| `rad-session` | Session lifecycle (`/startup`, `/wrapup`, `/add-resource`) built on the older canonical doc tree. Superseded by [`rad-repo-manager`](../plugins/rad-repo-manager) — minimal four-doc model. |
| `rad-stack-guide` | Stack detection + specialist reviewer orchestration. Stack detection folded into the session lifecycle; review orchestration retired when the framework reviewers were archived. |
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

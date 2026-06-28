# rad-code-review — Catch what AI wrote wrong before it ships.

When you build with Claude, you move fast. Fast enough that subtle bugs, fake error handling, and hardcoded accessibility states slip through — and they look fine at a glance. rad-code-review is the adversarial reviewer that knows exactly which mistakes AI code generators make. It only flags what *you* changed, not the whole codebase. And it understands your framework well enough to catch the security holes that generic linters miss.

## What You Can Do With This

- Review your current diff for bugs and security issues before committing — only the code you wrote gets flagged
- Check a new API endpoint for IDOR vulnerabilities across 6 supported frameworks (Next.js, Express, Fastify, Django, Rails, Go)
- Run a pre-ship audit across the full repo with a clear ship/no-ship verdict
- Detect AI-generated code anti-patterns: hallucinated imports, fake error handling, placeholder stubs, silent failures
- Audit a Backend-as-a-Service app where the database is the auth layer — missing/permissive Supabase RLS or Firebase Security Rules, the `user_metadata` escalation, and `service_role`/Admin keys leaked into the client bundle
- Run a launch-readiness security pass before handling real customer data with `--security-deep` (or `--strictness launch`)

## How It Works

rad-code-review runs three review roles in sequence — bug finder, architecture reviewer, release gate — then produces severity-ranked findings with optional fix application.

| Skill | Purpose |
|-------|---------|
| `rad-code-review` | Full orchestrated review — blame-aware scoping, 3 review roles, 12 dimensions, adversarial pass, fix application, report generation |

| Agent | Purpose |
|-------|---------|
| `code-reviewer` | Autonomous reviewer — scans codebase for bugs, security vulnerabilities, AI slop, performance anti-patterns, accessibility violations, and release blockers |

## Key Capabilities

- **Opus default, Sonnet/Haiku compatible** — set `--model` per run or pin via `.radcrconfig.yml`'s `review_model`
- **Parallel tool-call pipeline** — Steps 1–5 batch reads, greps, and shell checks; `run_in_background` for automated scans
- **JSON-first subagent output** — authoritative findings schema; markdown fallback only on parse failure
- **Checkpoint + `--resume`** — state written after Steps 5/7/9 so compaction mid-review is recoverable
- **`--non-interactive`** — structured return path for `code-reviewer` agent, `/loop`, CI
- **Blame-aware diff scoping** — only flag issues you introduced, not pre-existing noise
- **14-pattern AI slop detection** — hallucinated imports, fake error handling, placeholder stubs, silent failures, and 10 more
- **Mechanical hallucinated-imports validator** — `check-hallucinated-imports.py` runs in the automated-checks phase (offline, pure stdlib): every external import verified against your lockfiles, every relative import against disk
- **Fingerprint-based history comparison** — findings match across runs by category+file+title fingerprint (per-run IDs are never compared), so "show new findings only" means it
- **Framework-specific IDOR detection** — Next.js, Express, Fastify, Django, Rails, Go
- **Backend-as-a-Service data-exposure lane** — for apps where the database (RLS / Security Rules) *is* the authorization layer: Supabase/PostgREST RLS, Firebase (Firestore/RTDB/Storage rules + Admin SDK), Appwrite/PocketBase/Nhost/Amplify. Includes a reachability gate (exposed schema + grant + no policy) so deny-all/un-granted tables don't false-positive, the `user_metadata` untrusted-claim escalation, RLS-not-traversing-joins, `service_role`/Admin keys in client/public-env, and a "do NOT flag" list (the anon/publishable key in client code is correct by design)
- **`--security-deep` / `--strictness launch` launch-readiness pass** — 4 phases (trust boundaries → data-exposure surface → authorization model → secrets) with a no-false-assurance contract: never emits a "safe to launch" verdict, reports verified-vs-could-not-verify, recommends an independent human pen-test
- **Dynamic ARIA state detection** — catches hardcoded `aria-expanded`, `aria-selected`, `aria-checked`, `aria-pressed`
- **Performance heuristics** — N+1 queries, unbounded lists, sync blocking, bundle bloat, re-renders
- **8 project-type modules** — web app, API, Chrome extension, CLI, library, Electron, mobile, SaaS
- **Fix application with validation** — applies fixes, runs tests, verifies
- **Accepted-risk expiry enforcement** — stale `.radcrconfig.yml` entries are re-evaluated, not silently suppressed

## Quick Start

```bash
claude plugins add ./RAD-Claude-Skills/plugins/rad-code-review
```

Then just ask naturally:

```
Review my code
Is this ready to ship?
Check what I changed for security issues
Review changes since last release
```

Or use slash commands:

```bash
/rad-code-review diff                               # Review current diff (blame-aware, Opus)
/rad-code-review --since abc123                     # Review since a specific commit
/rad-code-review repo --strictness public           # Full repo, public release standard
/rad-code-review repo --strictness launch           # Launch-readiness: security-deep pass, no-false-assurance verdict
/rad-code-review diff --security-deep               # Add the launch-readiness security pass to any review
/rad-code-review diff --model sonnet                # Cost-sensitive scan on Sonnet
/rad-code-review diff --non-interactive             # Agent/CI mode (no findings menu)
/rad-code-review --resume 2026-04-16-143022         # Resume an interrupted review
```

## Agent vs. Skill

- **Skill (`/rad-code-review`)** — full orchestrated workflow with interactive findings menu, fix application, `.radcrconfig.yml` acceptance flow. Default mode when a human triggers a review.
- **`code-reviewer` agent** — autonomous reviewer invoked by another Claude (or automatically after significant feature work). Returns findings directly without menu prompts. Use `subagent_type: "code-reviewer"` when spawning from other agents; use the skill when a human is driving.

The agent always runs in non-interactive mode. The skill supports `--non-interactive` to match that behavior for CI/loop contexts.

## Naming

Finding IDs are **`CR-NNN`** — short to type, reference in conversation ("fix CR-7"), and fit in commit messages (`fix(review): … [CR-001]`). The config file (`.radcrconfig.yml`) and the state/history directories (`.radcr/state/`, `.radcr/history/`) keep the longer `radcr` prefix: renaming them would break existing per-repo state and configs for zero readability gain — you type finding IDs, not paths.

**If you have an existing `.ucrconfig.yml`** from the oldest versions of this plugin: rename it to `.radcrconfig.yml`, and rename `.ucr/` (if present) to `.radcr/`. Existing history files remain readable after the rename. Reports written before v5.0 use `RADCR-NNN` IDs — the fingerprint-based history comparison handles them via title+file matching.

## Version

**5.1.0** — Backend-as-a-Service data-exposure lane (security-checklist §2.5): Supabase/PostgREST RLS, Firebase rules + Admin SDK, and Appwrite/PocketBase/Nhost/Amplify, with a reachability gate (exposed schema + grant + no policy), the `user_metadata` untrusted-claim escalation, RLS-not-traversing-joins, `service_role`/Admin-key leak detection, and a do-NOT-flag list — wired into stack detection (Step 3b), the primary-review prompt, the severity model, and the SaaS/web-app/API project-type modules. New `--security-deep` mode and `--strictness launch`: a 4-phase launch-readiness pass (trust boundaries → data-exposure surface → authorization model → secrets) with a no-false-assurance contract. Grounded in current advisories (CVE-2025-48757, Supabase publishable/secret key model, OWASP API Top 10).

**History:** v5.0 — shorter `CR-NNN` finding IDs (config/state paths keep the `radcr` prefix); `check-hallucinated-imports.py` wired into the review (Step 5g, offline, lockfile-verified); fingerprint-based history matching (category+file+title) replacing per-run IDs; `--engine` removed in favor of `--adversarial-model <name>`; reports save to `.radcr/history/` only; model references de-versioned. v4.x — `UCR-` → `RADCR-` naming changeover. v3.0 — Opus default, parallel tool calls, JSON-first subagent output, checkpoint/`--resume`, `--non-interactive`, externalized prompts, accepted-risk expiry, unified history filenames. v2.0 — blame-aware scoping, framework IDOR, performance heuristics, dynamic ARIA detection. Full detail in git log.

## License
Apache-2.0

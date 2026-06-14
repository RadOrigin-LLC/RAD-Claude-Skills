# RAD Code Review

**3-role adversarial review with diff-aware scoping and AI slop detection — built specifically to catch what AI wrote badly, and to flag only what you changed.**

## Diff-Aware by Default

For diff and commit scopes, the review is **blame-aware** — it only flags issues on lines you changed, tags each finding `introduced` vs `pre-existing-dependency`, and supports `--since <commit>` for multi-commit deltas. On top of that: framework-specific IDOR heuristics (Next.js, Express, Fastify, Django, Rails, Go), concrete performance patterns (N+1 inside loops, re-render triggers, unbounded lists, sync blocking, bundle bloat), and dynamic ARIA state detection. The adversarial pass also validates the blame-scoping decisions so nothing real gets filtered out. Use `--full-scan` to flag everything in scope instead.

## Why This Exists

AI-generated code compiles, passes basic tests, and looks correct at a glance. But it has measurable quality issues: hallucinated APIs, shallow error handling, missing edge cases, copy-paste patterns that diverge, IDOR vulnerabilities that pass code review, and N+1 queries that work in dev but crash in production.

RAD Code Review is the harsh reviewer that runs AFTER the build phase. It is intentionally adversarial — it assumes the code is wrong and looks for proof. When it finds nothing, that is a meaningful signal.

**Diff-awareness** makes it work naturally in PR workflows. You don't want 50 findings about pre-existing tech debt when you're reviewing a 3-file PR. You want to know: "Did I introduce any problems?"

## Quick Start

### Installation

```bash
git clone https://github.com/RadOrigin-LLC/RAD-Claude-Skills.git
cd RAD-Claude-Skills

# Install as a plugin
claude plugins add ./plugins/rad-code-review
```

### Usage

```bash
# Review your current diff (blame-aware — only flags your changes)
/rad-code-review diff

# Review changes since a specific commit
/rad-code-review --since abc123

# Review last commit before merging
/rad-code-review commit

# Full repository audit (no blame filtering)
/rad-code-review repo

# Override blame-aware default — flag everything in the diff
/rad-code-review diff --full-scan

# Strict mode for public release
/rad-code-review repo --strictness public

# Cross-model adversarial review (a different model challenges the findings)
/rad-code-review diff --adversarial-model sonnet
```

Or just say it naturally:

```
Review my PR
Is this ready to ship?
Check what I changed for security issues
Review changes since last release
```

### Review Scopes

| Scope | What It Reviews | Blame-Aware | When To Use |
|-------|----------------|-------------|-------------|
| `diff` | Staged/unstaged changes | Yes (default) | PR review, quick check |
| `commit` | HEAD commit | Yes (default) | Post-merge verification |
| `--since <commit>` | All changes since commit | Yes (default) | Sprint review, release delta |
| `tree` | Working tree changes | No (full scan) | Before committing |
| `repo` | Entire repository | No (full scan) | Initial audit, periodic deep review |

### Blame-Aware Mode

When reviewing a diff or commit, it only flags issues on lines you changed. This means:

- **Introduced issues**: Problems in your changed code. Always flagged.
- **Pre-existing dependencies**: If your new code calls an existing function that has a vulnerability, it's flagged with `[PRE-EXISTING]` tag and explains the dependency chain.
- **Suppressed**: Pre-existing code quality issues unrelated to your changes. Not flagged.
- **Override**: Use `--full-scan` to see everything.

### Strictness Levels

| Level | Behavior |
|-------|----------|
| `mvp` | Focus on blockers and critical bugs. Skip style, docs, minor issues. Fast. |
| `production` | Full review across all 12 dimensions. Default. |
| `public` | Everything in production plus: public API surface, docs completeness, license compliance, security hardening. |

### Adversarial Pass Options

| Mode | How | Behavior |
|------|-----|----------|
| Self-adversarial | default | The same model re-attacks its own findings — challenges, validates blame-scoping, hunts for misses. |
| Cross-model | `--adversarial-model <name>` | A different model family runs the challenge pass — catches blind spots self-review can't. |

(The old `--engine claude|codex|both` flag was removed — it implied Codex execution that was never implemented. `--adversarial-model` is the honest cross-model equivalent.)

## What It Reviews

### Three Roles, Every Run

1. **Bug Finder** — Functional defects, logic errors, race conditions, edge cases, unhandled errors, and 14 AI slop patterns (hallucinated imports, fake error handling, placeholder stubs, silent failures, cargo-cult patterns, and more).

2. **Architecture Reviewer** — Structure, coupling, naming, abstraction quality, test coverage gaps, performance anti-patterns (N+1 queries, unbounded lists, sync blocking, bundle bloat), and maintainability.

3. **Release Gate** — Security (OWASP + framework-specific IDOR for 6 frameworks), accessibility (WCAG 2.2 + dynamic ARIA state detection), license compliance, dependency vulnerabilities, secret exposure, and documentation completeness.

### 12 Review Dimensions

Functional correctness, security, AI slop detection, architecture, tests, performance, UI/UX, accessibility, release readiness, documentation, dependencies, privacy/secrets handling.

### 8 Project-Type Modules

Web app, API/backend, Chrome extension, CLI tool, library/package, Electron app, mobile (React Native/Flutter), SaaS platform.

## Features

- **Blame-aware diff scoping** — only flag issues you introduced, with dependency chain detection
- **Incremental `--since` review** — review changes across multiple commits
- **Framework-specific IDOR detection** — Next.js Server Actions, Express, Fastify, Django, Rails, Go
- **Performance profiling heuristics** — N+1, re-renders, unbounded lists, sync blocking, bundle bloat
- **Dynamic ARIA state detection** — hardcoded `aria-expanded`, `aria-selected`, `aria-checked`, `aria-pressed`
- **14-pattern AI slop detection** — hallucinated imports, fake error handling, placeholder stubs, silent failures, cargo-cult patterns, fabricated comments, fake completeness
- **3-role adversarial review** — bug finder, architecture reviewer, release gate
- **Review-of-review calibration** — de-duplication, severity calibration, false positive removal
- **Fix application with validation** — apply fixes, run tests, verify
- **Report history and comparison** — track findings over time, diff between runs
- **8 project-type modules** — type-specific checklists loaded automatically
- **Local-only mode** — all analysis works offline
- **Configurable via `.radcrconfig.yml`** — project-level settings

## Configuration

Create a `.radcrconfig.yml` in your project root to customize behavior:

```yaml
# .radcrconfig.yml
version: 1

defaults:
  scope: diff
  strictness: production
  review_model: opus

project_type: web-app

exclude_paths:
  - "vendor/**"
  - "dist/**"
  - "*.min.js"
  - "**/*.generated.*"

min_severity: info

licenses:
  allowed: [MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC]
  denied: [GPL-3.0, AGPL-3.0]

history:
  enabled: false
  directory: .radcr/history
```

## Architecture

```
User triggers review
        |
        v
   Orchestrator (SKILL.md)
        |
        +-- Parses scope + flags (--since, --full-scan)
        +-- Detects project type + stack
        +-- Computes blame-aware diff context (if applicable)
        |
        v
   Automated checks (parallel)
        +-- npm audit / pip-audit / cargo audit -> dependency vulnerabilities
        +-- license-checker / pip-licenses      -> license compliance
        +-- gitleaks                            -> secret detection
        +-- tsc / eslint / project tests        -> existing project tools
        +-- check-hallucinated-imports.py       -> mechanical AI-slop Pattern #1 (offline)
        |
        v
   Primary review (Opus subagent by default)
        +-- Receives annotated diff + blame context
        +-- 12-dimension analysis scoped to changed lines
        +-- Framework-specific IDOR heuristics
        +-- Performance profiling patterns
        +-- Dynamic ARIA state detection
        +-- AI slop detection (14 patterns)
        |
        v
   Adversarial pass (self-adversarial, or cross-model via --adversarial-model)
        +-- Challenges findings
        +-- Validates blame-scoping decisions
        +-- Hunts for missed issues
        +-- Removes false positives
        |
        v
   Calibration pass
        +-- Deduplicate + severity calibration
        +-- Tag findings: introduced vs pre-existing
        |
        v
   Report generation
        +-- Finding summary with attribution breakdown
        +-- History comparison
        +-- Fix suggestions
```

## Project Structure

```
rad-code-review/
  SKILL.md                         # Orchestrator with blame-aware scoping rules
  README.md                        # This file
  ROADMAP.md                       # Version roadmap
  LICENSE                          # Apache-2.0 License
  references/
    ai-slop-patterns.md            # 14 AI slop detection patterns
    security-checklist.md           # Security checklist + IDOR framework heuristics
    ux-accessibility-checklist.md   # UX/a11y checklist + dynamic ARIA states
    performance-heuristics.md       # Performance detection patterns
    severity-model.md               # Severity classification
    trust-model.md                  # Trust boundaries
    adversarial-protocol.md         # Adversarial review protocol
    release-readiness.md            # Release readiness checklist
  workflows/
    orchestrate-review.md           # Main workflow with blame-aware scoping
    report-generation.md            # Report generation
    offer-fixes.md                  # Fix application
  project-types/
    web-app.md | api.md | chrome-extension.md | cli-tool.md
    library.md | electron-app.md | mobile-app.md | saas.md
  templates/
    findings-schema.md              # Finding format template
    report-template.md              # Full report template
    triage-report-template.md       # Triage report template
    radcrconfig-template.yml          # Default config template
  scripts/
    dep-audit.sh                    # Dependency vulnerability audit
    license-check.sh                # License compliance check
    secrets-scan.sh                 # Secrets detection
```

## License

Apache-2.0. See [LICENSE](LICENSE).

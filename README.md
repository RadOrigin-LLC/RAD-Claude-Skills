# RAD Claude Skills

A curated marketplace of plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — Anthropic's agentic coding tool. The lineup focuses on capabilities that add value beyond Opus's baseline competence: workflow lifecycle, MCP-backed live operations, structured planning, honest AI-pattern auditing, and domain-specific tools where they earn their place.

Install everything at once or cherry-pick individual plugins.

> **June 2026 — marketplace v1.25.0 (12 plugins).** **rad-gws-core** and **rad-supabase** removed from the lineup. The planner/repo-manager pair rebuilt for solo vibe coders. **[rad-planner](plugins/rad-planner/) 6.0** added the grilling and the ladder: a structured discovery interview (eight coverage areas driven to settled-or-explicitly-unknown, mirror-back, proposed assumptions), a release map in every plan — **Now** (MVP/Beta, fully specced) → **Next** (V1 outline) → **Later** (end goal) — plus two new skills: `/replan` (evidence-based plan updates, history never deleted) and `/rescue` (read-only project archaeology + a fresh plan for a repo that got away from you). It can now draft `docs/prd.md` from your own interview answers, per-section confirmed. **rad-session → [rad-repo-manager](plugins/rad-repo-manager/) 1.4.0** is the rebuilt minimal-document repo manager that maintains what the planner produces: `/startup` (read-only orientation grounded in two mechanical drift scans), `/wrapup` (handoff from git evidence + session-scoped doc reconcile, exact edits applied only on per-edit confirmation), `/repo-init`, `/repo-align`, git-evidence staleness detection, and three non-blocking hooks that stay silent until something is actually stale or loose. Both pair around a four-doc active core — `AGENTS.md` · `docs/prd.md` · `docs/plan.md` · `docs/handoff.md`. rad-session is retired to [`archive/`](archive/).
>
> **Earlier — April 2026.** Single-framework reviewer plugins (rad-react, rad-zod, rad-typescript, rad-nextjs, rad-fastify, rad-astro, rad-stripe-fastify-webhooks) archived — Opus 4.7 handles those well enough on its own. **rad-stack-guide** archived — stack-detection value absorbed into rad-session 5.1's `/startup` Phase 0.5 (originally `/init`, folded after a name conflict with Claude Code's built-in). **rad-google-workspace** (93 skills) archived — superseded by rad-gws-core (14 essential skills; itself removed from the lineup in June 2026). All archived plugins preserved under [`archive/`](archive/). The remaining 12 plugins are the ones that demonstrably add value Opus doesn't already provide.

---

## What's Here

```
RAD-Claude-Skills/
├── packages/                          # Standalone npm packages
│   └── coolify-mcp/                   # @radoriginllc/coolify-mcp — MCP server for Coolify API
├── plugins/                           # Claude Code CLI & Desktop plugins (multi-skill bundles)
│   ├── rad-1password/                 # 1Password CLI workflows — secret rotation, env injection, vault ops
│   ├── rad-a11y/                      # WCAG 2.2 AA accessibility toolkit
│   ├── rad-brainstormer/              # Anti-anchoring brainstorming — any topic, not just code
│   ├── rad-chrome-extension/          # MV3 Chrome extension development
│   ├── rad-code-review/               # Diff-aware adversarial code review
│   ├── rad-context-prompter/          # Prompt engineering for 30+ AI platforms
│   ├── rad-coolify-orchestrator/      # Coolify self-hosted PaaS management (MCP-backed)
│   ├── rad-explain/                   # Honest project explanation — 5 skills + 2 grounding/overpromise validators
│   ├── rad-para-second-brain/         # PARA second brain — organize, review, distill
│   ├── rad-planner/                   # Strictly-planning — risk-first, adversarial, mechanically-validated → docs/plan.md
│   ├── rad-seo-optimizer/             # Complete SEO & AEO toolkit
│   └── rad-repo-manager/              # Repo manager for vibe coders — startup/wrapup/repo-init/repo-align + drift hooks
└── skills/                            # Claude.ai skills (ZIP upload / Project Knowledge)
    ├── rad-brainstormer/              # Ideation — Claude.ai adaptation of rad-brainstormer
    ├── rad-seo-aeo-reviewer/          # SEO/AEO — Claude.ai adaptation of rad-seo-optimizer
    └── rad-writer/                    # Writing — Claude.ai-only distribution (no longer a plugin)
```

---

## Plugins vs Skills — Two Formats, Two Environments

You'll notice some names appear in both `plugins/` and `skills/` (`rad-brainstormer`, plus `rad-seo-optimizer` ↔ `rad-seo-aeo-reviewer`), and that `rad-writer` lives only under `skills/`. They cover the same knowledge but are built for different environments:

**`plugins/` — Claude Code CLI & Claude Desktop**
Full plugin bundles with multiple skills, autonomous agents, reference files, and automatic routing. They activate when you're working in a Claude Code session — they can read your filesystem, spawn subagents, and chain tools together. Install with `claude plugins add`.

**`skills/` — Claude.ai (the web app)**
Single-file skills designed for [claude.ai](https://claude.ai). They work as uploadable ZIP files via **Settings > Customize > Skills**, as Project Knowledge, or as conversation attachments. They consolidate plugin knowledge into one skill, use web search and URL fetching instead of filesystem tools, and output deliverables as artifacts. No CLI needed.

Two plugins have Claude.ai counterparts: `rad-brainstormer` and `rad-seo-optimizer` (as `rad-seo-aeo-reviewer`). A third Claude.ai skill, `rad-writer`, is distributed standalone — the matching plugin was retired in v1.11.0 (its project-narrative role moved to `rad-explain`). The table column **Works with** shows which environments each plugin supports.

---

## Why These Plugins?

Claude Code is powerful out of the box — but it doesn't know which MCP servers your project has wired up, which review patterns catch AI-generated mistakes in your specific framework, or how to deterministically validate the implementation plan it just generated. These plugins add value Opus doesn't provide on its own: deterministic validators (Python scripts), MCP-backed live operations, structured workflow lifecycle, and domain-specific tools.

Each one installs in a single command and activates automatically when you ask Claude about relevant topics. No configuration, no manual invocation. Use any plugin on its own, or run **`/rad-repo-manager:startup`** in a new project — it's a quick read-only orientation (the four active docs + git state + two mechanical drift scans); on a fresh repo it points you at `/rad-repo-manager:repo-init`, which scaffolds a lean AGENTS.md + agent shims + the four-doc core and hands off to `/rad-planner:plan`.

---

## Quick Install

### Option 1: Add as a Marketplace (recommended)

Add the entire marketplace to Claude Code or Claude Desktop — browse and install any plugin, with automatic updates on sync.

```bash
# Add the marketplace
claude plugin marketplace add https://github.com/RadOrigin-LLC/RAD-Claude-Skills

# Install any plugin from the marketplace
claude plugin install rad-repo-manager@rad-claude-skills
claude plugin install rad-code-review@rad-claude-skills
claude plugin install rad-planner@rad-claude-skills
# ... any plugin from the list below

# Update all installed plugins
claude plugin marketplace update
```

### Option 2: Install Directly from Git

```bash
# Clone the repo
git clone https://github.com/RadOrigin-LLC/RAD-Claude-Skills.git

# Install any plugin
claude plugins add ./RAD-Claude-Skills/plugins/rad-repo-manager
claude plugins add ./RAD-Claude-Skills/plugins/rad-code-review
claude plugins add ./RAD-Claude-Skills/plugins/rad-planner
# ... any plugin from the list below
```

### Verify Installation

Start a new Claude Code session and run:
```
/skills
```

---

## Where to Start

Not sure which plugins to install first? These four deliver the most value across the widest range of projects:

| Plugin | Why install it | Works with |
|--------|---------------|-----------|
| [rad-repo-manager](plugins/rad-repo-manager/) | **1.4.0** — A minimal-document repo manager for vibe coders that keeps your docs consistent *and fresh* so coding agents don't get confused by contradictory or stale information. Lean `/startup` (read-only orientation: the four active docs + git state + two mechanical drift scans) and `/wrapup` (handoff written from git evidence, not chat memory, then a session-scoped doc reconcile — exact edits drafted, applied only on your per-edit OK), `/repo-init` (greenfield scaffold), and an opt-in `/repo-align` deep clean (contradictions, redundancy, loose docs — proposed, never auto-applied). Three quiet hooks catch what habit misses: a doc-health line at session start, handoff evidence preserved through compaction, at most one wrapup reminder per session. Replaces rad-session. | CLI, Desktop |
| [rad-code-review](plugins/rad-code-review/) | **5.0** — Catches bugs, AI anti-patterns, and security issues in your current diff. Blame-aware scoping, framework-specific IDOR (6 frameworks), AI slop detection (14 patterns, incl. a mechanical lockfile-verified hallucinated-imports validator), performance heuristics, 3 review roles, short `CR-NNN` finding IDs, fingerprint-based history comparison. Language- and framework-agnostic. | CLI, Desktop |
| [rad-planner](plugins/rad-planner/) | **6.0** — A planner built for solo devs who aren't formally trained engineers. It grills you first (a structured discovery interview — eight coverage areas driven to settled-or-explicitly-unknown, your project mirrored back for correction, assumptions proposed for confirm/deny), then writes a plan with a release ladder — **Now** (MVP/Beta, fully specced tasks) → **Next** (V1 outline) → **Later** (your end goal) — readable by you, executable by your coding agent. Four skills: `/plan` (greenfield), `/rescue` (project archaeology + a fresh plan for a repo that got away from you — assesses, never fixes), `/replan` (evidence-based updates that never delete history), `/review-plan` (quality audit). Can draft your PRD from your own interview answers, per-section confirmed. Mechanically lint-validated + adversarially risk-reviewed. | CLI, Desktop |
| [rad-explain](plugins/rad-explain/) | **0.1.0** — Honest project explanation for any repo. Five skills (`narrate-project`, `elevator-pitch`, `draft-pitch`, `explain-document`, `ground-readme`) generate audience-targeted external communications from internal artifacts. Two pure-stdlib Python validators (`check-grounding`, `check-overpromise`) run on every output — claims must trace to repo source; superlatives, vague-quantity, marketing fluff, and production-readiness assertions get flagged. No rad-planner dependency; works on any repo. | CLI, Desktop |

After installing rad-repo-manager, run `/rad-repo-manager:startup` in your project — it reads the four active docs + git state, runs the two drift scans, and briefs you on where you are, what's next, and whether the docs are trustworthy. On a fresh repo it points you at `/rad-repo-manager:repo-init` to scaffold the four-doc core, then `/rad-planner:plan`.

---

## Plugin Pipelines

Some plugins are designed to chain. The most common pipeline for a new project:

1. **[rad-brainstormer](plugins/rad-brainstormer/)** — explore the problem space without being anchored by AI suggestions, converge on an idea, produce a design spec (`/rad-brainstormer:brainstorm-session` → `/rad-brainstormer:design-sprint`)
2. **[rad-planner](plugins/rad-planner/)** — turn the spec into an ordered implementation plan via the interview-driven, risk-first planning conversation. Writes one file, `docs/plan.md` (release map Now/Next/Later, milestones, tasks, validation, risks); mechanically validated by `plan-lint.py` and adversarially reviewed by the `risk-assessor` agent. Later, `/rad-planner:replan` absorbs reality into the plan, and `/rad-planner:rescue` is the entry point when a project's state got away from you.
3. **[rad-repo-manager](plugins/rad-repo-manager/)** — `/startup` orients each session; `/repo-init` scaffolds a fresh repo; `/wrapup` writes a clean handoff from git evidence and reconciles the core docs with the session; `/repo-align` is the opt-in deep clean that catches drift. Owns `AGENTS.md` operational sections and `docs/handoff.md`; reads the `docs/plan.md` that rad-planner writes.
4. **[rad-code-review](plugins/rad-code-review/)** — review the code you generate from the plan (`/rad-code-review`)

Each plugin stands alone — the pipeline is a suggestion, not a requirement. The boundary between `design-sprint` and `plan` is: design-sprint produces a *spec* (architecture, components, APIs), plan produces an *ordered implementation plan* — sequenced milestones with acceptance criteria, validation commands, guardrails, and risks — written as a single `docs/plan.md`.

---

## Plugins

### Workflow & Code Quality

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-repo-manager](plugins/rad-repo-manager/) | 4 | 0 | **1.4.0** — A minimal-document repo manager for vibe coders. Four skills: `/startup` (read-only session orientation — the four active docs + git state + two mechanical drift scans, ending in a grounded freshness/hygiene briefing), `/wrapup` (overwrite `docs/handoff.md` from git evidence, then a session-scoped reconcile — owned docs updated on your OK, user-owned docs get the exact edit drafted and applied only on per-edit confirmation; no auto-commit, never runs tests), `/repo-init` (greenfield scaffold of the doc model — never invents product content), `/repo-align` (opt-in deep clean — contradictions, redundancy, stale/loose docs, broken read paths; proposes, never auto-acts, moves with `git mv`). Three non-blocking hooks, silent unless something is wrong: a session-start doc-health line, compaction-survival instructions for handoff evidence, and a once-per-session wrapup nudge. Doc model is a tiny declared core (`AGENTS.md` · `docs/prd.md` · `docs/plan.md` · `docs/handoff.md`; prd/plan/handoff carry an `Updated:` freshness stamp) plus a closed reference catalog and `docs/archive/`. Five pure-stdlib validators — the cheap two run at every session start, so a stale handoff or an untouched PRD is caught the next time you open the project, not months later. Replaces rad-session. | CLI, Desktop |
| [rad-code-review](plugins/rad-code-review/) | 1 | 1 | **5.0** — Diff-aware adversarial code review. Blame-aware scoping, framework-specific IDOR (6 frameworks), AI slop detection (14 patterns + a mechanical hallucinated-imports validator wired into the automated-checks phase), performance heuristics, 3 review roles, `CR-NNN` finding IDs, fingerprint-based cross-run history comparison, cross-model adversarial pass via `--adversarial-model`. Language- and framework-agnostic. | CLI, Desktop |
| [rad-planner](plugins/rad-planner/) | 4 | 2 | **6.0** — A planner for solo devs who aren't formally trained engineers; strictly a planner (never writes implementation code). Method: a structured discovery interview (eight coverage areas — end goal, users, MVP, success criteria, constraints, assets, exclusions, danger zones — driven to settled-or-explicitly-unknown, mirror-back, proposed assumptions, ≤3 rounds), codegen-aware stack evaluation (`stack-advisor` + AI-native Golden Path matrix), goal-backward decomposition with size discipline, mechanical validation (`plan-lint.py`), then an adversarial `risk-assessor` pass against 14 documented anti-patterns (APPROVE/REVISE/RETHINK). Output: one `docs/plan.md` with a release map — Now (MVP/Beta, six-field task specs) / Next (V1 outline) / Later (end goal) — plus a plain-language layer for the human reader. Four skills: `/plan`, `/rescue` (read-only project archaeology + evidence-led interview + fresh plan for a messy repo), `/replan` (evidence-based update; shipped work moves to `## Shipped`, never deleted), `/review-plan`. Births `docs/prd.md` from your interview answers (per-section confirmed) when none exists; other durable changes surface as a paste-ready update-prompt. Quick path (skip stack agent, single risk pass) or full path — your choice at discovery. | CLI, Desktop |
| [rad-a11y](plugins/rad-a11y/) | 6 | 1 | WCAG 2.2 AA accessibility — 4 reference skills (semantic HTML, ARIA, keyboard/focus, forms), 1 setup skill (a11y-testing wires up real axe via jest-axe + Playwright), 1 static-analysis skill (a11y-review) + autonomous reviewer agent. **2.0 honesty pass:** every finding tagged `[STATIC]` / `[HEURISTIC]` / `[NEEDS-MANUAL]`; no Pass/Fail compliance verdict. **2.1 mechanical validators:** 4 pure-stdlib Python scripts (scan-jsx-patterns, check-tailwind-contrast with real WCAG sRGB math, check-target-size for WCAG 2.5.8, lint-aria wrapping eslint-plugin-jsx-a11y) run in Phase 0 before LLM judgment. **2.2 cross-model + stack-aware:** Phase 0 + Phase 1 issued as a single parallel tool-call burst on Opus 4.7/Sonnet 4.6 (Haiku falls back gracefully); Phase 8 stack slices only execute when detected stack matches (React/Next/Astro/Tailwind/Radix/Headless UI), plain HTML projects skip Phase 8 entirely. | CLI, Desktop |
| [rad-chrome-extension](plugins/rad-chrome-extension/) | 9 | 1 | Chrome MV3 extensions — WXT, React, security, messaging, storage, service workers, CWS compliance | CLI, Desktop |

### Productivity & Content

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-seo-optimizer](plugins/rad-seo-optimizer/) | 12 | 3 | Full SEO toolkit — site audits, AEO/AI visibility, keyword research, competitor analysis, link building, schema, technical SEO | CLI, Desktop, Claude.ai |
| [rad-brainstormer](plugins/rad-brainstormer/) | 4 | 3 | **3.0** — The brainstormer that doesn't anchor you: it draws out *your* thinking before offering any ideas (research-backed anti-anchoring protocol), under enforced divergent/convergent discipline. Brainstorms anything — software, business, content, travel, creative. Four skills (consolidated from ten): `brainstorm-session` (techniques as modes — SCAMPER, six hats, reverse, HMW, starburst, unblock), `idea-evaluation`, `five-whys`, `design-sprint` (spec → hands off to `/rad-planner:plan`, which pre-fills from it). Three agents: live domain research, pre-mortem idea-challenger, iterative spec-reviewer. Output is one file, delivered where you choose — personal folder, project (as an explicitly transient doc), or chat only. | CLI, Desktop, Claude.ai |
| [rad-explain](plugins/rad-explain/) | 5 | 0 | **0.1.0** — Honest project explanation. Five skills (`narrate-project`, `elevator-pitch`, `draft-pitch`, `explain-document`, `ground-readme`) generate audience-targeted external communications from a project's internal artifacts. Two pure-stdlib Python validators (`check-grounding`, `check-overpromise`) gate every output — claims must trace to repo source, superlatives + vague-quantity + marketing fluff + unsupported production-readiness get flagged. Works on any repo; reads canonical `docs/` if present, falls back to README + manifest + source structure. | CLI, Desktop |
| [rad-para-second-brain](plugins/rad-para-second-brain/) | 5 | 2 | PARA second brain — organize notes, run weekly reviews, progressive summarization, session handoffs, 12 favorite problems | CLI, Desktop |
| [rad-context-prompter](plugins/rad-context-prompter/) | 2 | 1 | Prompt engineering — write, debug, and optimize prompts for 30+ AI platforms. Includes decompiler for reverse-engineering existing prompts | CLI, Desktop |

### Backend & Infrastructure

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-coolify-orchestrator](plugins/rad-coolify-orchestrator/) | 9 | 1 | Coolify self-hosted PaaS — deployments, databases, security, CI/CD, troubleshooting, observability, infrastructure, live actions, status dashboard. **4 Python validators** (lint-dockerfile, lint-compose, check-coolify-env, audit-cicd) run via the coolify-reviewer agent *and* auto-fire on Dockerfile/compose edits via a PostToolUse hook (new in 2.1). Honest about what's experimental (Sentinel scope, Swarm, Caddy proxy, Railpack-NOT-yet-shipped). Bundles [`@radoriginllc/coolify-mcp`](packages/coolify-mcp/) (36 tools, OpenAPI-spec-verified). | CLI, Desktop |
| [rad-1password](plugins/rad-1password/) | 11 | 0 | End-to-end coverage of the 1Password CLI (`op`) — so Claude can use your secrets without you ever pasting plaintext into chat. Seven auto-triggered routers (`1password-cli`, `op-secrets-injection`, `op-item-management`, `op-provisioning`, `op-ssh-keys`, `op-shell-plugins`, `op-service-accounts`) plus four utility slash commands (`/op-signin`, `/op-status`, `/op-find`, `/op-secret-template`). All 8 commands and 11 management commands documented at the 1Password CLI reference are covered; flags cross-checked against `op --help` on v2.34.0. Honest about beta scope (`op environment` is beta-only and directed to in-app management). Requires 1Password CLI v2.x; biometric unlock or service-account token. | CLI, Desktop |

---

## Claude.ai Skills

Three standalone skills packaged for [claude.ai](https://claude.ai). Import as a ZIP via **Settings > Customize > Skills**, add to a Project, or attach to any conversation. Two are Claude.ai counterparts of marketplace plugins (`rad-brainstormer`, `rad-seo-optimizer` → `rad-seo-aeo-reviewer`); one is Claude.ai-only after the matching plugin was retired (`rad-writer` — see the v1.11.0 retirement note above).

| Skill | Source | ZIP | What It Does |
|-------|--------|-----|-------------|
| [rad-writer](skills/rad-writer/) | Claude.ai-only (plugin retired v1.11.0) | `rad-writer.zip` | Domain-aware writing and editorial review across 9 content types, AI pattern avoidance, voice profiling |
| [rad-brainstormer](skills/rad-brainstormer/) | Counterpart of rad-brainstormer plugin | `rad-brainstormer.zip` | Facilitated ideation, SCAMPER/Six Hats/Five Whys, pre-mortem analysis, design sprint |
| [rad-seo-aeo-reviewer](skills/rad-seo-aeo-reviewer/) | Counterpart of rad-seo-optimizer plugin | `rad-seo-aeo-reviewer.zip` | SEO audit (URL or GitHub mode), competitor research, content strategy, AI search visibility |

See [`skills/README.md`](skills/README.md) for import instructions and how these differ from the plugin versions.

---

## How It Works

Once installed, skills activate automatically when you ask Claude about relevant topics. Each skill has specific **trigger phrases** — natural language patterns that tell Claude when to use that skill.

For example, with `rad-a11y` installed:
```
You: "Is this component accessible?"
Claude: [activates a11y-review skill, runs WCAG 2.2 AA review]

You: "Set up axe-core testing for my project"
Claude: [activates a11y-testing skill, scaffolds CI integration]
```

With `rad-seo-optimizer` installed:
```
You: /seo-audit https://mysite.com
Claude: [runs 6-phase SEO audit with scored report]

You: "How do I get recommended by ChatGPT?"
Claude: [activates aeo-optimizer skill, analyzes AI search visibility]
```

See each plugin's README for its full list of trigger phrases.

---

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed and authenticated
- Internet access (for skills that fetch web content)
- Some plugins have additional requirements noted in their READMEs

---

## Contributing

Found a bug? Have an idea for a new skill? See:

- [Contributing Guide](CONTRIBUTING.md) — how to submit changes
- [Code of Conduct](CODE_OF_CONDUCT.md) — community standards
- [Security Policy](SECURITY.md) — reporting vulnerabilities
- [Discussions](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/discussions) — questions & ideas

---

## License

[Apache License 2.0](LICENSE) — free to use, modify, and distribute. Includes patent protection and requires noting modifications.

---

Built with Claude Code by [RAD](https://github.com/RadOrigin-LLC)

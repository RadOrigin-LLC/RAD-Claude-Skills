# RAD Claude Skills

A curated marketplace of plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — Anthropic's agentic coding tool. The lineup focuses on capabilities that add value beyond Opus's baseline competence: workflow lifecycle, MCP-backed live operations, structured planning, honest AI-pattern auditing, and domain-specific tools where they earn their place.

Install everything at once or cherry-pick individual plugins.

> **June 2026 — marketplace v1.19.0 (14 plugins).** Two ground-up reboots in this window. **rad-planner 5.0 → 5.1** stripped back to *strictly planning*: it runs a risk-first, adversarially-reviewed, mechanically-validated planning conversation and writes one file — `docs/plan.md` — surfacing durable changes (PRD, decisions, architecture) for you to apply rather than generating a doc tree. The v4.x canonical-doc machinery, scope gates, and depth heuristics were removed. **rad-session → [rad-repo-manager](plugins/rad-repo-manager/) 1.0** is a rebuilt minimal-document repo manager for vibe coders: a lean `/startup` (orient, or onboard a fresh repo) and `/wrapup` (clean handoff written from git evidence), a deep opt-in `/analyze` (find contradictions, redundancy, loose docs — fixes proposed, never auto-applied), and a one-line health verdict that makes doc drift visible early. Both pair around a four-doc active core — `AGENTS.md` · `docs/prd.md` · `docs/plan.md` · `docs/handoff.md`. rad-session is retired to [`archive/`](archive/).
>
> **Earlier — April 2026.** Single-framework reviewer plugins (rad-react, rad-zod, rad-typescript, rad-nextjs, rad-fastify, rad-astro, rad-stripe-fastify-webhooks) archived — Opus 4.7 handles those well enough on its own. **rad-stack-guide** archived — stack-detection value absorbed into rad-session 5.1's `/startup` Phase 0.5 (originally `/init`, folded after a name conflict with Claude Code's built-in). **rad-google-workspace** (93 skills) archived — superseded by [`rad-gws-core`](plugins/rad-gws-core/) (14 essential skills). All archived plugins preserved under [`archive/`](archive/). The remaining 14 plugins are the ones that demonstrably add value Opus doesn't already provide.

---

## What's Here

```
RAD-Claude-Skills/
├── packages/                          # Standalone npm packages
│   └── coolify-mcp/                   # @radoriginllc/coolify-mcp — MCP server for Coolify API
├── plugins/                           # Claude Code CLI & Desktop plugins (multi-skill bundles)
│   ├── rad-1password/                 # 1Password CLI workflows — secret rotation, env injection, vault ops
│   ├── rad-a11y/                      # WCAG 2.2 AA accessibility toolkit
│   ├── rad-brainstormer/              # Ideation methodologies & creative tools
│   ├── rad-chrome-extension/          # MV3 Chrome extension development
│   ├── rad-code-review/               # Diff-aware adversarial code review
│   ├── rad-context-prompter/          # Prompt engineering for 30+ AI platforms
│   ├── rad-coolify-orchestrator/      # Coolify self-hosted PaaS management (MCP-backed)
│   ├── rad-explain/                   # Honest project explanation — 5 skills + 2 grounding/overpromise validators
│   ├── rad-gws-core/                  # Google Workspace core (14 essential skills)
│   ├── rad-para-second-brain/         # PARA second brain — organize, review, distill
│   ├── rad-planner/                   # Strictly-planning — risk-first, adversarial, mechanically-validated → docs/plan.md
│   ├── rad-seo-optimizer/             # Complete SEO & AEO toolkit
│   ├── rad-repo-manager/              # Repo manager for vibe coders — /startup, /wrapup, /analyze; minimal-doc hygiene
│   └── rad-supabase/                  # Full-stack Supabase development (MCP-backed)
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

Each one installs in a single command and activates automatically when you ask Claude about relevant topics. No configuration, no manual invocation. Use any plugin on its own, or run **`/rad-repo-manager:startup`** in a new project — on first run it onboards the project (asks once which agents are in scope, scaffolds a lean AGENTS.md + agent shims + the four-doc core) and points you at `/rad-planner:plan`; subsequent runs are a quick read-only orientation.

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
| [rad-repo-manager](plugins/rad-repo-manager/) | **1.0** — A minimal-document repo manager for vibe coders that keeps your docs consistent so coding agents don't get confused by contradictory information. Lean `/startup` (orient, or onboard a fresh repo — scaffold a four-doc core + agent shims) and `/wrapup` (clean handoff written from git evidence, not chat memory), plus an opt-in `/analyze` deep-clean that finds contradictions, redundancy, and loose/unfiled docs and proposes fixes (never auto-applies). A one-line health verdict (🟢/🟡/🔴 + loose-ends count) makes drift visible early. Replaces rad-session. | CLI, Desktop |
| [rad-code-review](plugins/rad-code-review/) | **4.1** — Catches bugs, AI anti-patterns, and security issues in your current diff. Blame-aware scoping, framework-specific IDOR (6 frameworks), AI slop detection (14 patterns), performance heuristics, 3 review roles. Language- and framework-agnostic. | CLI, Desktop |
| [rad-planner](plugins/rad-planner/) | **5.1** — Strictly a planner. Runs a risk-first, adversarially-reviewed, mechanically-validated planning conversation (discovery + assumption capture → codegen-aware stack eval → goal-backward decomposition with size discipline → mechanical lint → adversarial risk pass) and writes one file: `docs/plan.md`. Durable changes (PRD, decisions, architecture) are surfaced as a paste-ready update-prompt for you to apply — it never writes them itself. Two skills (`/plan`, `/review-plan`), two agents, two pure-stdlib validators. | CLI, Desktop |
| [rad-explain](plugins/rad-explain/) | **0.1.0** — Honest project explanation for any repo. Five skills (`narrate-project`, `elevator-pitch`, `draft-pitch`, `explain-document`, `ground-readme`) generate audience-targeted external communications from internal artifacts. Two pure-stdlib Python validators (`check-grounding`, `check-overpromise`) run on every output — claims must trace to repo source; superlatives, vague-quantity, marketing fluff, and production-readiness assertions get flagged. No rad-planner dependency; works on any repo. | CLI, Desktop |

After installing rad-repo-manager, run `/rad-repo-manager:startup` in your project — on first run it onboards the project (agent scope, a lean AGENTS.md, agent shims, the four-doc core) and points you at `/rad-planner:plan`. Subsequent runs are a quick orientation that ends with a one-line health verdict.

---

## Plugin Pipelines

Some plugins are designed to chain. The most common pipeline for a new project:

1. **[rad-brainstormer](plugins/rad-brainstormer/)** — explore the problem space, converge on an idea, produce a design spec (`/rad-brainstormer:brainstorm-session` → `/rad-brainstormer:design-sprint`)
2. **[rad-planner](plugins/rad-planner/)** — turn the spec into an ordered implementation plan via the risk-first planning conversation. Writes one file, `docs/plan.md` (milestones, tasks, validation, risks); mechanically validated by `plan-lint.py` and adversarially reviewed by the `risk-assessor` agent.
3. **[rad-repo-manager](plugins/rad-repo-manager/)** — `/startup` orients each session (or onboards a fresh repo); `/wrapup` writes a clean handoff from git evidence; `/analyze` keeps the docs consistent and catches drift. Owns `AGENTS.md` and `docs/handoff.md`; reads the `docs/plan.md` that rad-planner writes.
4. **[rad-code-review](plugins/rad-code-review/)** — review the code you generate from the plan (`/rad-code-review`)

Each plugin stands alone — the pipeline is a suggestion, not a requirement. The boundary between `design-sprint` and `plan` is: design-sprint produces a *spec* (architecture, components, APIs), plan produces an *ordered implementation plan* — sequenced milestones with acceptance criteria, validation commands, guardrails, and risks — written as a single `docs/plan.md`.

---

## Plugins

### Workflow & Code Quality

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-repo-manager](plugins/rad-repo-manager/) | 3 | 0 | **1.0** — A minimal-document repo manager for vibe coders. Three commands: `/startup` (orient at session start, or onboard a fresh repo — scaffold a lean AGENTS.md, agent shims, and the four-doc core, then point at `/rad-planner:plan`), `/wrapup` (overwrite `docs/handoff.md` from git evidence for a clean handoff; no auto-commit), and `/analyze` (opt-in deep clean — contradictions, redundancy, orphaned content, loose/unfiled docs — fixes proposed interactively, never auto-applied). startup/wrapup are intentionally lean and end with a one-line health verdict (🟢/🟡/🔴 + loose-ends count) you watch climb across sessions so drift is visible early; the `/analyze` nudge is rate-limited so it never nags. Doc model is a tiny declared core (`AGENTS.md` · `docs/prd.md` · `docs/plan.md` · `docs/handoff.md`) plus a closed reference catalog, a `docs/inbox/` for new docs awaiting filing, and `docs/archive/`. Authors only AGENTS.md operational sections, the shims, and `docs/handoff.md`; surfaces durable changes via update-prompt. Four pure-stdlib validators. Replaces rad-session. | CLI, Desktop |
| [rad-code-review](plugins/rad-code-review/) | 1 | 1 | **4.1** — Diff-aware adversarial code review. Blame-aware scoping, framework-specific IDOR (6 frameworks), AI slop detection (14 patterns), performance heuristics, 3 review roles. Language- and framework-agnostic. | CLI, Desktop |
| [rad-planner](plugins/rad-planner/) | 2 | 2 | **5.1** — Strictly a planner: a risk-first, adversarially-reviewed, mechanically-validated planning conversation that produces one file, `docs/plan.md`. Method: strategic discovery + assumption capture, codegen-aware stack evaluation (`stack-advisor` + AI-native Golden Path matrix), goal-backward decomposition with size discipline, mechanical validation (`plan-lint.py` — required sections, per-task fields, dependency resolution + cycles, vague language), then an adversarial `risk-assessor` pass against 14 documented anti-patterns (APPROVE/REVISE/RETHINK, escalates to brainstorming). Durable changes are surfaced as a paste-ready `docs/[date]-update-prompt.md` for you to apply — never written by the planner. Two skills (`/plan`, `/review-plan`), two agents (`stack-advisor`, `risk-assessor`), two validators (`plan-lint`, `validate-json`). v5.0 reboot stripped the v4.x canonical-doc machinery. | CLI, Desktop |
| [rad-a11y](plugins/rad-a11y/) | 6 | 1 | WCAG 2.2 AA accessibility — 4 reference skills (semantic HTML, ARIA, keyboard/focus, forms), 1 setup skill (a11y-testing wires up real axe via jest-axe + Playwright), 1 static-analysis skill (a11y-review) + autonomous reviewer agent. **2.0 honesty pass:** every finding tagged `[STATIC]` / `[HEURISTIC]` / `[NEEDS-MANUAL]`; no Pass/Fail compliance verdict. **2.1 mechanical validators:** 4 pure-stdlib Python scripts (scan-jsx-patterns, check-tailwind-contrast with real WCAG sRGB math, check-target-size for WCAG 2.5.8, lint-aria wrapping eslint-plugin-jsx-a11y) run in Phase 0 before LLM judgment. **2.2 cross-model + stack-aware:** Phase 0 + Phase 1 issued as a single parallel tool-call burst on Opus 4.7/Sonnet 4.6 (Haiku falls back gracefully); Phase 8 stack slices only execute when detected stack matches (React/Next/Astro/Tailwind/Radix/Headless UI), plain HTML projects skip Phase 8 entirely. | CLI, Desktop |
| [rad-chrome-extension](plugins/rad-chrome-extension/) | 9 | 1 | Chrome MV3 extensions — WXT, React, security, messaging, storage, service workers, CWS compliance | CLI, Desktop |

### Productivity & Content

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-seo-optimizer](plugins/rad-seo-optimizer/) | 12 | 3 | Full SEO toolkit — site audits, AEO/AI visibility, keyword research, competitor analysis, link building, schema, technical SEO | CLI, Desktop, Claude.ai |
| [rad-brainstormer](plugins/rad-brainstormer/) | 10 | 3 | Structured ideation — SCAMPER, Six Hats, Five Whys, reverse brainstorming, design sprints, pre-mortem analysis | CLI, Desktop, Claude.ai |
| [rad-explain](plugins/rad-explain/) | 5 | 0 | **0.1.0** — Honest project explanation. Five skills (`narrate-project`, `elevator-pitch`, `draft-pitch`, `explain-document`, `ground-readme`) generate audience-targeted external communications from a project's internal artifacts. Two pure-stdlib Python validators (`check-grounding`, `check-overpromise`) gate every output — claims must trace to repo source, superlatives + vague-quantity + marketing fluff + unsupported production-readiness get flagged. Works on any repo; reads canonical `docs/` if present, falls back to README + manifest + source structure. | CLI, Desktop |
| [rad-para-second-brain](plugins/rad-para-second-brain/) | 5 | 2 | PARA second brain — organize notes, run weekly reviews, progressive summarization, session handoffs, 12 favorite problems | CLI, Desktop |
| [rad-context-prompter](plugins/rad-context-prompter/) | 2 | 1 | Prompt engineering — write, debug, and optimize prompts for 30+ AI platforms. Includes decompiler for reverse-engineering existing prompts | CLI, Desktop |

### Backend & Infrastructure

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-supabase](plugins/rad-supabase/) | 11 | 1 | Full-stack Supabase — local CLI workflows, MCP remote operations, RLS, migrations, auth, storage, edge functions, branching | CLI, Desktop |
| [rad-coolify-orchestrator](plugins/rad-coolify-orchestrator/) | 8 | 1 | Coolify self-hosted PaaS — deployments, databases, security, CI/CD, troubleshooting, observability, infrastructure. **2.0 ships 4 Python validators** (lint-dockerfile, lint-compose, check-coolify-env, audit-cicd) the coolify-reviewer agent runs before LLM judgment. Honest about what's experimental (Sentinel scope, Swarm, Caddy proxy, Railpack-NOT-yet-shipped). Bundles [`@radoriginllc/coolify-mcp`](packages/coolify-mcp/) (27 verified tools). | CLI, Desktop |
| [rad-1password](plugins/rad-1password/) | 11 | 0 | End-to-end coverage of the 1Password CLI (`op`) — so Claude can use your secrets without you ever pasting plaintext into chat. Seven auto-triggered routers (`1password-cli`, `op-secrets-injection`, `op-item-management`, `op-provisioning`, `op-ssh-keys`, `op-shell-plugins`, `op-service-accounts`) plus four utility slash commands (`/op-signin`, `/op-status`, `/op-find`, `/op-secret-template`). All 8 commands and 11 management commands documented at the 1Password CLI reference are covered; flags cross-checked against `op --help` on v2.34.0. Honest about beta scope (`op environment` is beta-only and directed to in-app management). Requires 1Password CLI v2.x; biometric unlock or service-account token. | CLI, Desktop |

### Google Workspace

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-gws-core](plugins/rad-gws-core/) | 14 | 0 | Google Workspace essentials — Gmail send/read/reply/triage, Docs write, Sheets read/append, Slides, Drive, Calendar. Requires `gws` CLI. The wider 93-skill `rad-google-workspace` was archived in April 2026 (see [archive/](archive/)). | CLI, Desktop |

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

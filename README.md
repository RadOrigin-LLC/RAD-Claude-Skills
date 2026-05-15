# RAD Claude Skills

A curated marketplace of plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — Anthropic's agentic coding tool. The lineup focuses on capabilities that add value beyond Opus 4.7's baseline competence: workflow lifecycle, MCP-backed live operations, structured planning, honest AI-pattern auditing, and domain-specific tools where they earn their place.

Install everything at once or cherry-pick individual plugins.

> **May 2026 — rad-planner 4.3 ships: M0.5 briefing reshape + conversational-continuation triggers (marketplace v1.8.2).** A real-session test of v4.2 exposed two related friction points. **First:** the M0.5 scope-confirmation gate fired but rendered as a dense identifier-heavy recap — schema column names, ADR numbers, and bit identifiers stacked high enough that a user reading the output couldn't easily separate what had been decided already from what the agent was newly inferring, even though structurally the gate was correct. **Second:** free-form planning-continuation utterances at session open ("let's continue the plan", "where did we leave off in the plan") didn't match the existing trigger phrases for the /plan skill, so they fell through to ad-hoc agent work that bypassed the M0.5 gate entirely. **rad-planner 4.3** addresses both: the M0.5 surface is reshaped into a prose-first briefing pattern matching rad-session's /startup doorman model — **Where we left off** + **Last accomplishment** + **Next logical step** + **Or you could start with** (2–3 concrete alternatives including a skip / execute / redirect option) + a single **Mechanical state** line for identifiers. Rendering rules forbid bullet lists of identifiers, ADR numbers, or schema column names in the friendly framing — those collapse into the Mechanical state line. Trigger phrases expand to catch continuation utterances ("continue the plan", "continue planning", "let's keep planning", "pick up the plan", "where did we leave off in the plan", "resume the plan", and similar) and route them to the improvement entry point so the M0.5 gate fires rather than letting free-form planning continuation become ad-hoc agent work. Cross-plugin consistency with rad-session's Path A / Path B / Path C alternatives is now a load-bearing design principle.
>
> **May 2026 — rad-planner 4.2 + rad-session 5.3 ship: the user-confirmation-surface pair (marketplace v1.8.1).** Two real-session defects surfaced after the v1.8.0 release. **First:** `/plan --improve` correctly parked canonical doc emission for a project on a custom doc structure, but still produced a 9-sub-section consolidation deliverable for sign-off without asking what scope of work the user wanted. **Second:** `/startup` on a clean routine open produced zero output, leaving the user wondering whether the skill had actually run. Both failures share the same root cause: the skill doing substantive work without first surfacing what it sees and confirming what the user wants. **rad-planner 4.2** adds an **M0.5 scope-confirmation hard gate** between mechanical M0 discovery and any substantive work. Fires on ALL entry points and ALL invocation modes including `--auto`. Surfaces a terse discovery summary + inferred scope + three options (confirm / different scope with depth menu / redirect). **rad-session 5.3** adds a **floor of one line on /startup** — silent completion violates the doorman model; the cleanest routine open emits at least a single confirmation line with status freshness, plan progress, and a pointer to docs/status.md. Anomalies stack above the floor; the floor always appears. Both patches encode the same principle: confirm the skill ran, surface what it sees, hand the next move back to the user.\n>\n> **May 2026 — rad-planner 4.1 + rad-session 5.2 (marketplace v1.8.0): permission-mode-safety pair.** A real fresh-greenfield test surfaced a defect: `/plan` ran unilaterally on a single paragraph of user intent, producing 8 ADRs and a full stack selection without asking a clarifying question — because a harness-level `<system-reminder>` about not asking clarifying questions (a permission-mode Auto default) was interpreted as "skip the M1–M5 planning conversation." The user's message had explicitly invited debate. **The fix was structural, not behavioral:**\n>\n> **rad-planner 4.1** declares `/plan` **conversational by design** in a third top-level CRITICAL block. M1–M5 each carry a "Conversational gate" blockquote requiring explicit user input before advancing. Harness autonomy hints apply to *tool-use approvals* (bash, Write, Edit, git, MCP), NOT to the planning conversation itself. New `--auto` flag is the ONLY way to suppress M1–M5 dialogue — and `--auto` does NOT write ADRs (candidate decisions land in `docs/planning/proposed-decisions.md` with LLM-inferred rationale explicitly labeled so the user can confirm or replace). DRAFT banners on every `--auto` output file; mandatory trade-off banner in the final summary names the speed-vs-confidence trade explicitly.\n>\n> **rad-session 5.2** splits permission-mode handling by **asymmetry of downside.** `/startup` Phase 0.5 Case C guard rail (overwrite/append/skip on operating manual >500 bytes) is data-loss-protected — prompts regardless of Auto / Bypass / `--non-interactive` because silent overwrite of user-authored content is hard to recover. Conversely, `/wrapup` Phase 3 gets a new `--auto` mode (productive autonomy) — writes candidate-decision ADRs with `DRAFT — auto-recorded` banner so the capture isn't lost; review surfaces automatically in next `/startup` Phase 1.5.1 briefing. The principle: **permission-mode autonomy is about not pestering for tool approvals, not silently making asymmetric-downside decisions for the user.**\n>\n> **Earlier in this release window** — v1.7.1 shipped rad-session 5.1 (`/init` folded into `/startup` Phase 0.5 to resolve the name conflict with Claude Code's built-in `/init`). v1.7.0 shipped rad-session 5.0 (canonical doc structure, intent-vs-reality split, evidence-based `docs/status.md` replaces `HANDOFF.md`, sectioned-writer rule with rad-planner for the operating manual, conditional CLAUDE.md/AGENTS.md per agent scope, milestone-shipped archive). v1.6.0 shipped rad-planner 4.0 (plan-first workflow, four entry points, four mechanical validators). **Upgrading from 3.x/4.x:** run [`plugins/rad-session/scripts/migrate-to-v5.py`](plugins/rad-session/scripts/migrate-to-v5.py) before installing 5.x. See [`docs/doc-conventions.md`](docs/doc-conventions.md) for the canonical structure.
>
> **April 2026 — Marketplace tightened.** The single-framework reviewer plugins (rad-react, rad-zod, rad-typescript, rad-nextjs, rad-fastify, rad-astro, rad-stripe-fastify-webhooks) have been archived — Opus 4.7 handles those framework-specific reviews well enough on its own. **rad-stack-guide is also archived**, with its stack-detection value absorbed into rad-session 3.0's new `/init` skill. **rad-google-workspace (93 skills) is also archived** — superseded by the focused [`rad-gws-core`](plugins/rad-gws-core/) (14 essential skills). All archived plugins are preserved in [`archive/`](archive/) for reference. The remaining 15 plugins are the ones that demonstrably add value Opus doesn't already provide.

---

## What's Here

```
RAD-Claude-Skills/
├── packages/                          # Standalone npm packages
│   └── coolify-mcp/                   # @radoriginllc/coolify-mcp — MCP server for Coolify API
├── plugins/                           # Claude Code CLI & Desktop plugins (multi-skill bundles)
│   ├── rad-a11y/                      # WCAG 2.2 AA accessibility toolkit
│   ├── rad-brainstormer/              # Ideation methodologies & creative tools
│   ├── rad-chrome-extension/          # MV3 Chrome extension development
│   ├── rad-code-review/               # Diff-aware adversarial code review
│   ├── rad-context-prompter/          # Prompt engineering for 30+ AI platforms
│   ├── rad-coolify-orchestrator/      # Coolify self-hosted PaaS management (MCP-backed)
│   ├── rad-gws-core/                  # Google Workspace core (14 essential skills)
│   ├── rad-para-second-brain/         # PARA second brain — organize, review, distill
│   ├── rad-planner/                   # Structured project planning + Python DAG validators
│   ├── rad-seo-optimizer/             # Complete SEO & AEO toolkit
│   ├── rad-session/                   # Session lifecycle: /startup (with first-run bootstrap) + /wrapup + /add-resource
│   ├── rad-supabase/                  # Full-stack Supabase development (MCP-backed)
│   └── rad-writer/                    # Domain-aware writing (9 domains) + Python validators for measured AI patterns
└── skills/                            # Claude.ai skills (ZIP upload / Project Knowledge)
    ├── rad-brainstormer/              # Ideation — Claude.ai adaptation of rad-brainstormer
    ├── rad-seo-aeo-reviewer/          # SEO/AEO — Claude.ai adaptation of rad-seo-optimizer
    └── rad-writer/                    # Writing — Claude.ai adaptation of rad-writer
```

---

## Plugins vs Skills — Two Formats, Two Environments

You'll notice that some names appear in both `plugins/` and `skills/` (rad-writer, rad-brainstormer). They cover the same knowledge, but they're built for different environments:

**`plugins/` — Claude Code CLI & Claude Desktop**
Full plugin bundles with multiple skills, autonomous agents, reference files, and automatic routing. They activate when you're working in a Claude Code session — they can read your filesystem, spawn subagents, and chain tools together. Install with `claude plugins add`.

**`skills/` — Claude.ai (the web app)**
Single-file skills designed for [claude.ai](https://claude.ai). They work as uploadable ZIP files via **Settings > Customize > Skills**, as Project Knowledge, or as conversation attachments. They consolidate plugin knowledge into one skill, use web search and URL fetching instead of filesystem tools, and output deliverables as artifacts. No CLI needed.

Three plugins have Claude.ai counterparts: `rad-writer`, `rad-brainstormer`, and `rad-seo-optimizer` (as `rad-seo-aeo-reviewer`). The table column **Works with** shows which environments each plugin supports.

---

## Why These Plugins?

Claude Code is powerful out of the box — but it doesn't know which MCP servers your project has wired up, which review patterns catch AI-generated mistakes in your specific framework, or how to deterministically validate the implementation plan it just generated. These plugins add value Opus 4.7 doesn't provide on its own: deterministic validators (Python scripts), MCP-backed live operations, structured workflow lifecycle, and domain-specific tools.

Each one installs in a single command and activates automatically when you ask Claude about relevant topics. No configuration, no manual invocation — just better answers for the specific problems they were built for. Use any plugin on its own, or run **`/rad-session:startup`** in a new project — on first run it bootstraps the project (detects your stack, asks once which agents are in scope, scaffolds the operating manual + status.md + profile) and recommends which other rad-* plugins fit; subsequent runs are a read-only briefing.

---

## Quick Install

### Option 1: Add as a Marketplace (recommended)

Add the entire marketplace to Claude Code or Claude Desktop — browse and install any plugin, with automatic updates on sync.

```bash
# Add the marketplace
claude plugin marketplace add https://github.com/radesjardins/RAD-Claude-Skills

# Install any plugin from the marketplace
claude plugin install rad-session@rad-claude-skills
claude plugin install rad-code-review@rad-claude-skills
claude plugin install rad-planner@rad-claude-skills
# ... any plugin from the list below

# Update all installed plugins
claude plugin marketplace update
```

### Option 2: Install Directly from Git

```bash
# Clone the repo
git clone https://github.com/radesjardins/RAD-Claude-Skills.git

# Install any plugin
claude plugins add ./RAD-Claude-Skills/plugins/rad-session
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
| [rad-session](plugins/rad-session/) | **4.0** — Three-phase workflow lifecycle with cross-machine continuity. `/init` bootstraps (deterministic stack detection, plugin recommendations, CLAUDE.md scaffold; merges `CLAUDE-FRAGMENT.md` if present from rad-planner ≤3.0, else auto-generates `@-imports` from detected strategic docs), `/startup` orients each session (verifies sync with origin before reading any handoff file, gap-checks strategic docs), `/wrapup` captures state (prompts to append tagged decisions to `DECISIONS.md`, prune protection, auto-commits + prompts to push). PreCompact safety net included. **Note:** rad-planner 4.0 writes the operating manual directly without a FRAGMENT — rad-session 4.0 still works but the FRAGMENT-merge path is unused; rad-session 5.0 (upcoming) picks up rad-planner 4.0's contract. | CLI, Desktop |
| [rad-code-review](plugins/rad-code-review/) | Catches bugs, AI anti-patterns, and security issues in your current diff — regardless of language or framework | CLI, Desktop |
| [rad-planner](plugins/rad-planner/) | **4.0** — Plan-first project planning with four entry points (`--full` / `--improve` / `--drift` / `--pivot`). Five-phase conversation produces the plan; M6 writes the approved doc set per the canonical structure aligned with published research at [`docs/doc-conventions.md`](docs/doc-conventions.md). Four mechanical validators (`plan-lint.py`, `status-validator.py`, `doc-redundancy.py`, `doc-contradiction.py`) back the workflow. Always-teaches in `/plan`; mentor vs dev mode in `.rad/profile` gates `/wrapup` teaching depth. | CLI, Desktop |
| [rad-writer](plugins/rad-writer/) | Domain-aware writing across 9 content types with measured AI-pattern auditing (Python validators), honest about what detection can/can't claim in 2026 | CLI, Desktop, Claude.ai |

After installing rad-session, run `/rad-session:startup` in your project — on first run, it bootstraps the project (stack detection, agent scope, operating manual scaffold, status.md scaffold, profile creation) and recommends which other rad-* plugins fit (no auto-install, just informed recommendations). Subsequent runs are a quick read-only briefing.

---

## Plugin Pipelines

Some plugins are designed to chain. The most common pipeline for a new project:

1. **[rad-brainstormer](plugins/rad-brainstormer/)** — explore the problem space, converge on an idea, produce a design spec (`/rad-brainstormer:brainstorm-session` → `/rad-brainstormer:design-sprint`)
2. **[rad-planner](plugins/rad-planner/)** — turn the spec into a project plan via the five-phase plan-first conversation. Four entry points (`/plan --full`, `--improve`, `--drift`, `--pivot`); M6 writes the approved doc set per [`docs/doc-conventions.md`](docs/doc-conventions.md). Four mechanical validators (`plan-lint`, `status-validator`, `doc-redundancy`, `doc-contradiction`) back the workflow.
3. **[rad-session](plugins/rad-session/)** — `/startup` orients each session; on first run for a project, its Phase 0.5 bootstrap populates the operating manual's Operational sections (Commands, Compact Instructions, Claude-specific behavior) — rad-planner 4.0 already wrote the Constitution sections. `/wrapup` captures state and prompts for ADR additions.
4. **[rad-code-review](plugins/rad-code-review/)** — review the code you generate from the plan (`/rad-code-review`)

Each plugin stands alone — the pipeline is a suggestion, not a requirement. The boundary between `design-sprint` and `plan` is: design-sprint produces a *spec* (architecture, components, APIs), plan produces an *ordered implementation plan* (DAG, tasks, complexity, risk) plus the 8-doc strategic/operational set.

---

## Plugins

### Workflow & Code Quality

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-session](plugins/rad-session/) | 4 | 0 | **4.0** — Three-phase workflow lifecycle. `/init` bootstraps once (stack detection, plugin recommendations, CLAUDE.md scaffold with FRAGMENT-merge / auto-generated / placeholder `@-imports` for strategic docs). `/startup` orients each session (Phase 0 fetches origin and prompts to pull when behind; Phase 1.5 gap-checks strategic docs and soft-warns). `/wrapup` captures each session (structured HANDOFF.md, mechanical session-log derivation, Phase 3.5 prompts to append tagged decisions to `DECISIONS.md` as sequence-numbered multi-line entries — skipped in `--quick` / non-interactive; CLAUDE.md prune-with-diff auto-skipped when unchanged; auto-commit + prompted push). `/add-resource`. Four Python scripts (`detect-stack.py`, `detect-resources.py`, `audit-plugin-bloat.py`, `migrate-to-v4.py`). PreCompact safety net. **rad-session 4.0 was built for the rad-planner 3.0 RAD 8-doc standard** (PRD / ARCHITECTURE / ASSUMPTIONS / DECISIONS / PLAN at root). rad-planner 4.0 ships with the new [canonical doc structure](docs/doc-conventions.md); rad-session 4.0 still functions but its FRAGMENT-merge path is unused with rad-planner 4.0. rad-session 5.0 (intent/reality split, status.md owned-by-session) is upcoming. | CLI, Desktop |
| [rad-code-review](plugins/rad-code-review/) | 1 | 1 | Diff-aware adversarial code review — blame-aware scoping, framework-specific IDOR (6 frameworks), AI slop detection (14 patterns), performance heuristics, 3 review roles | CLI, Desktop |
| [rad-planner](plugins/rad-planner/) | 5 | 3 | **4.0** — Plan-first project planning aligned with published OpenAI/Anthropic project-structure research at [`docs/doc-conventions.md`](docs/doc-conventions.md). `/plan` runs four entry points (`--full`, `--improve`, `--drift`, `--pivot`) detected from utterance + project state, with a universal four-direction menu as the ambiguity fallback. Five-phase conversation (Constitution & Frame → Goal-Backward Scope → Sequence with Size Discipline → Quality Gates → Doc-Set Recommendation) produces the plan with project-specific doc recommendations; M6 executes the approved doc set — operating manual (CLAUDE.md or AGENTS.md per agent scope), `docs/vision.md`, `docs/architecture.md`, `docs/planning/current.md`, `docs/status.md` scaffold (rad-session populates from evidence), `docs/decisions/`, optional `docs/roadmap.md`, `.rad/profile`. Four mechanical validators back the workflow: `plan-lint.py` (current.md sections + AC checkbox format + vague language), `status-validator.py` (freshness + 8-section + evidence-based results), `doc-redundancy.py` (cross-doc Jaccard duplicates), `doc-contradiction.py` (vision non-goals vs current ACs via stemmed token overlap). `validate-json.py` retained for subagent JSON contracts. Two test fixtures under [`plugins/rad-planner/fixtures/`](plugins/rad-planner/fixtures/). Always-teaches in `/plan`; mentor vs dev mode in `.rad/profile` (project-scoped) gates `/wrapup` teaching depth via rad-session. Migration from 3.0 not provided — neither prior version had public traffic. | CLI, Desktop |
| [rad-a11y](plugins/rad-a11y/) | 6 | 1 | WCAG 2.2 AA accessibility — 4 reference skills (semantic HTML, ARIA, keyboard/focus, forms), 1 setup skill (a11y-testing wires up real axe via jest-axe + Playwright), 1 static-analysis skill (a11y-review) + autonomous reviewer agent. **2.0 honesty pass:** every finding tagged `[STATIC]` / `[HEURISTIC]` / `[NEEDS-MANUAL]`; no Pass/Fail compliance verdict. **2.1 mechanical validators:** 4 pure-stdlib Python scripts (scan-jsx-patterns, check-tailwind-contrast with real WCAG sRGB math, check-target-size for WCAG 2.5.8, lint-aria wrapping eslint-plugin-jsx-a11y) run in Phase 0 before LLM judgment. **2.2 cross-model + stack-aware:** Phase 0 + Phase 1 issued as a single parallel tool-call burst on Opus 4.7/Sonnet 4.6 (Haiku falls back gracefully); Phase 8 stack slices only execute when detected stack matches (React/Next/Astro/Tailwind/Radix/Headless UI), plain HTML projects skip Phase 8 entirely. | CLI, Desktop |
| [rad-chrome-extension](plugins/rad-chrome-extension/) | 9 | 1 | Chrome MV3 extensions — WXT, React, security, messaging, storage, service workers, CWS compliance | CLI, Desktop |

### Productivity & Content

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-seo-optimizer](plugins/rad-seo-optimizer/) | 12 | 3 | Full SEO toolkit — site audits, AEO/AI visibility, keyword research, competitor analysis, link building, schema, technical SEO | CLI, Desktop, Claude.ai |
| [rad-brainstormer](plugins/rad-brainstormer/) | 10 | 3 | Structured ideation — SCAMPER, Six Hats, Five Whys, reverse brainstorming, design sprints, pre-mortem analysis | CLI, Desktop, Claude.ai |
| [rad-writer](plugins/rad-writer/) | 4 | 2 | Domain-aware writing across 9 content types — email, blog, web copy, reports, technical docs, social media. Python validators (`text-stats.py` for burstiness/em-dash/hedging/transitions, `check-blocklist.py` for word-list scans). AI patterns reorganized by durability tier. Honest about detection (impossible) and voice cloning (informal-genre limits). 2.0 honesty pass. | CLI, Desktop, Claude.ai |
| [rad-para-second-brain](plugins/rad-para-second-brain/) | 5 | 2 | PARA second brain — organize notes, run weekly reviews, progressive summarization, session handoffs, 12 favorite problems | CLI, Desktop |
| [rad-context-prompter](plugins/rad-context-prompter/) | 2 | 1 | Prompt engineering — write, debug, and optimize prompts for 30+ AI platforms. Includes decompiler for reverse-engineering existing prompts | CLI, Desktop |

### Backend & Infrastructure (MCP-backed live operations)

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-supabase](plugins/rad-supabase/) | 11 | 1 | Full-stack Supabase — local CLI workflows, MCP remote operations, RLS, migrations, auth, storage, edge functions, branching | CLI, Desktop |
| [rad-coolify-orchestrator](plugins/rad-coolify-orchestrator/) | 8 | 1 | Coolify self-hosted PaaS — deployments, databases, security, CI/CD, troubleshooting, observability, infrastructure. **2.0 ships 4 Python validators** (lint-dockerfile, lint-compose, check-coolify-env, audit-cicd) the coolify-reviewer agent runs before LLM judgment. Honest about what's experimental (Sentinel scope, Swarm, Caddy proxy, Railpack-NOT-yet-shipped). Bundles [`@radoriginllc/coolify-mcp`](packages/coolify-mcp/) (27 verified tools). | CLI, Desktop |

### Google Workspace

| Plugin | Skills | Agents | What It Does | Works with |
|--------|--------|--------|-------------|-----------|
| [rad-gws-core](plugins/rad-gws-core/) | 14 | 0 | Google Workspace essentials — Gmail send/read/reply/triage, Docs write, Sheets read/append, Slides, Drive, Calendar. Requires `gws` CLI. The wider 93-skill `rad-google-workspace` was archived in April 2026 (see [archive/](archive/)). | CLI, Desktop |

---

## Claude.ai Skills

Three plugins have been adapted as standalone Claude.ai skills. Import as a ZIP via **Settings > Customize > Skills**, add to a Project, or attach to any conversation.

| Skill | Based on | ZIP | What It Does |
|-------|----------|-----|-------------|
| [rad-writer](skills/rad-writer/) | rad-writer | `rad-writer.zip` | Domain-aware writing and editorial review across 9 content types, AI pattern avoidance, voice profiling |
| [rad-brainstormer](skills/rad-brainstormer/) | rad-brainstormer | `rad-brainstormer.zip` | Facilitated ideation, SCAMPER/Six Hats/Five Whys, pre-mortem analysis, design sprint |
| [rad-seo-aeo-reviewer](skills/rad-seo-aeo-reviewer/) | rad-seo-optimizer | `rad-seo-aeo-reviewer.zip` | SEO audit (URL or GitHub mode), competitor research, content strategy, AI search visibility |

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
- [Discussions](https://github.com/radesjardins/RAD-Claude-Skills/discussions) — questions & ideas

---

## License

[Apache License 2.0](LICENSE) — free to use, modify, and distribute. Includes patent protection and requires noting modifications.

---

Built with Claude Code by [RAD](https://github.com/radesjardins)

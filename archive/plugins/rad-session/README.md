# rad-session — agent session lifecycle: startup (with first-run bootstrap), wrapup, add-resource, with cross-machine continuity for Claude + Codex.

> **v5.6 — user-owned content visibility audit.** `/wrapup` Phase 4 and `/startup` Phase 1.5.3 invoke rad-planner 4.10's `audit-user-content.py` to surface stale terminology and dead paths in user-owned operating-manual sections — advisory only; neither plugin modifies the content. Findings auto-fade when you fix the underlying content (no state file).
>
> **v5.5 — compact milestone contract render at `/startup`.** When `docs/planning/current.md` has a `### Session contract` sub-section (rad-planner 4.8+), `/startup` renders it as the first user-visible block after the floor line — putting the 7-field build-readiness contract in context before the first tool call. Graceful skip when absent.
>
> **v5.4 — Lanes section recognized.** `/startup` and `/wrapup` recognize rad-planner v4.7+'s `Lanes` Constitution section (role-separation contract) and treat it as never-prunable.
>
> **v5.3 — floor of one line on `/startup`.** Silent completion violates the doorman model; even the cleanest routine open emits at least a single confirmation line with status freshness + plan progress + pointer to `docs/status.md`. Anomalies stack above the floor; the floor always appears.
>
> **v5.2 — permission-mode-safe.** Operations split by asymmetry of downside. `/startup` Phase 0.5 Case C guard rail (overwrite/append/skip on operating manual > 500 bytes) is **data-loss-protected** — prompts regardless of Auto / Bypass / `--non-interactive` because silent overwrite of user-authored content is hard to recover. Conversely, `/wrapup --auto` writes candidate-decision ADRs with a `DRAFT — auto-recorded` banner so the capture isn't lost; review surfaces automatically in the next `/startup` Phase 1.5.1 briefing.
>
> **v5.1 — `/init` folded into `/startup` Phase 0.5.** Resolved the name conflict with Claude Code's built-in `/init`. First-run bootstrap (stack detection, agent_scope question, operating-manual scaffold per sectioned-writer rule with rad-planner, plugin-bloat audit) now runs as Phase 0.5 of `/startup` on the first session in a project. Subsequent runs skip Phase 0.5 entirely.
>
> **v5.0 — canonical doc structure.** Intent-vs-reality split: `docs/planning/current.md` (intent, owned by rad-planner) vs `docs/status.md` (reality, owned by rad-session, written from evidence). Operating manual sectioned-writer rule. Conditional CLAUDE.md / AGENTS.md per agent scope. Milestone-shipped archive.

**What it is.** A three-skill plugin that gives agent-driven projects a structured session lifecycle: orient + bootstrap once at first run, capture each session at the end, register tools as you discover them. Works for a single agent on a single machine — and **transparently keeps PC ↔ GitHub ↔ Laptop in sync across Claude Code and Codex sessions** when a git remote exists.

**What it solves.** The default Claude / Codex experience loses session state at compaction, can't tell you what tools the project has, lets the operating manual grow forever, and forgets everything when you switch machines or agents. rad-session keeps `docs/status.md` (evidence-based reality), pairs it with `docs/planning/current.md` (intent — owned by rad-planner), archives shipped milestones, and pulls/commits/pushes the relevant files via git so your laptop sees what your PC did, and your Codex session sees what your Claude session did.

**What it isn't.** It is **not** an automation layer over your code: it never runs builds, never touches non-session files in commits, and never force-pushes. It does not write your strategic docs — that's rad-planner's job. It does not invent state — `/wrapup` writes from **evidence** (git diff, test output, plan-task state), not chat synthesis.

## The canonical doc structure (v5.0+)

rad-session is built around the canonical structure aligned with published OpenAI / Anthropic project-structure research. The structure is shared with rad-planner 4.0 via the **single-writer rule** (each file has exactly one automated writer) with a **sectioned-writer exception** for the operating manual.

```
<project-root>/
├── CLAUDE.md or AGENTS.md       # operating manual — conditional on agent scope
├── docs/
│   ├── vision.md                # rad-planner
│   ├── architecture.md          # rad-planner
│   ├── status.md                # rad-session — EVIDENCE-BASED reality
│   ├── planning/
│   │   ├── current.md           # rad-planner — INTENT for the active milestone
│   │   └── archive/             # rad-session — one file per shipped milestone
│   ├── decisions/               # rad-planner (creation); rad-session prompts at wrapup
│   │   ├── README.md
│   │   └── NNNN-*.md            # ADRs, sequence-numbered
│   └── roadmap.md               # optional
├── .rad/profile                 # mode (mentor/dev) + agent_scope + multi_branch_status
├── .claude/settings.json        # if Claude in scope
└── .codex/config.toml           # if Codex in scope
```

→ Canonical specs: [`docs/doc-conventions.md`](../../docs/doc-conventions.md), [`docs/cross-plugin-contracts.md`](../../docs/cross-plugin-contracts.md), [`docs/status-md-schema.md`](../../docs/status-md-schema.md)

## Intent vs. reality split (the v5.0 insight)

v4.0 conflated "what we're trying to do" with "what's actually true." v5.0 separates them:

| File | What it captures | Written by |
|---|---|---|
| `docs/planning/current.md` | **Intent** for the active milestone — objective, acceptance criteria, validation commands, planned changes, stop conditions | rad-planner `/plan` |
| `docs/status.md` | **Reality** — branch state, last completed work, files changed recently, latest validation results, decisions made during execution, blockers, next recommended step | rad-session `/wrapup` |

`/wrapup` writes `docs/status.md` from **evidence** (git log, git diff, test output, plan-task checkbox state) — not from what the LLM remembers about the conversation. This is the structural shift that makes the new artifact reliable across compaction, machine switches, and agent switches.

## Sectioned-writer rule (the operating manual)

The operating manual is the **one file with two automated writers**. The single-writer rule is preserved at the section level:

| Section | Owner |
|---|---|
| Project, Read order, Hard boundaries, Engineering rules, Definition of done, Escalate triggers | rad-planner `/plan` M6 (Constitution) |
| Commands, Compact Instructions (CLAUDE.md only), Claude-specific behavior (CLAUDE.md only), `@AGENTS.md` import line (CLAUDE.md shim case) | rad-session `/startup` bootstrap (Operational) |
| Any other section | User-owned. Plugins preserve as-is and surface in output. |

`/wrapup` Phase 5 (prune) operates on **Operational sections only**. Constitution sections are never touched by rad-session. User-added sections are never touched by either plugin.

## Agent scope routing

`/startup`'s bootstrap path asks once on first run whether the project will be worked by Claude, Codex, or both — and routes operating-manual writes accordingly:

| `agent_scope` | Files scaffolded |
|---|---|
| `claude_only` | `CLAUDE.md` (canonical) |
| `codex_only` | `AGENTS.md` (canonical) |
| `claude_and_codex` | `AGENTS.md` (canonical) + `CLAUDE.md` (`@AGENTS.md` shim with Claude-specific Operational sections) |

The choice is persisted to `.rad/profile`. `/startup` and `/wrapup` read the profile and behave per scope.

## The three skills

| Skill | When | What it does |
|---|---|---|
| **`/startup`** | Every session | **Phase 0** fetches origin and prompts to pull when behind. **Phase 0.5 — bootstrap check.** On first run (when `.rad/profile` / operating manual / `docs/status.md` are missing), runs the one-time setup inline: stack detection via Python scripts, agent_scope question, operating manual Operational sections scaffold (sectioned-writer rule), `docs/status.md` scaffold, `.rad/profile` creation, `.claude/settings.json` / `.codex/config.toml` per scope, plugin-bloat audit. **Phase 1+ in steady state** reads `.rad/profile`, the operating manual (per scope, including non-canonical filenames via header heuristic), `docs/status.md`, `docs/planning/current.md`, and surfaces a concise briefing (<35 lines, <5s wall clock — doorman model). Read-only in steady state; only writes during the one-time bootstrap path. |
| **`/wrapup`** | Every session | **9-phase workflow.** Refuses if no work changed since the last status (Phase 0). Writes `docs/status.md` from **evidence** (Phase 2). Detects candidate decisions mechanically (dep adds, schema changes, env additions, new top-level dirs) plus soft triggers (Phase 3). Mode-aware: mentor mode teaches and drafts an ADR; dev mode shows a quick list. Runs cross-doc validators from rad-planner (`doc-redundancy.py` + `doc-contradiction.py`) (Phase 4). Prunes the operating manual's Operational sections only (Phase 5). Detects milestone-shipped state (all ACs checked) and proposes archiving `current.md` to `planning/archive/YYYY-MM-DD-MN-slug.md` (Phase 6). Commits + prompts to push (Phase 7). Anomaly-gated final output (silent on success) (Phase 8). |
| **`/add-resource`** | Any time | Register a new MCP server, CLI tool, script, or note in the operating manual's Resources section so `/startup` picks it up next session. |

## Slash command flags

| Skill | Triggers | Flags |
|---|---|---|
| **`/startup`** | "/startup", "where did we leave off", "catch me up", "what's the state", "set up rad-session here", "bootstrap this project" | `--auto-pull` skip Phase 0 prompt, fast-forward silently · `--no-pull` skip sync entirely · `--bootstrap` force Phase 0.5 even if artifacts present · `--no-bootstrap` skip Phase 0.5 even if missing (diagnostic) · `--agents <scope>` set agent_scope during bootstrap (`claude_only` / `codex_only` / `claude_and_codex`) · `--non-interactive` suppress bootstrap prompts · `--dry-run` propose bootstrap scaffolds without writing |
| **`/wrapup`** | "/wrapup", "wrap up", "end of session", "save state" | `--push` skip Phase 7 prompt, push immediately · `--no-push` commit locally only · `--quick` skip Phase 3 deep scan + Phase 4 validators + Phase 5 prune · `--non-interactive` suppress all prompts · `--force` override Phase 0 no-work check |
| **`/add-resource`** | "add this MCP", "remember the supabase CLI", "register this resource" | (none) |

Combine flags freely — e.g. `/wrapup --push --quick` (autonomous-loop wrapup), `/startup --no-pull` (offline work), `/startup --bootstrap --agents claude_and_codex --non-interactive` (scripted setup).

Plus one hook:

| Hook | Event | What it does |
|---|---|---|
| `precompact` | `PreCompact` | Fires automatically when context compaction begins. Injects a systemMessage telling the agent to run `/wrapup` before the compacted context loses session state. |

## Mode-aware behavior (mentor vs. dev)

`.rad/profile` carries a `mode` field that gates teaching depth in `/wrapup`:

| Mode | `/wrapup` Phase 3 behavior |
|---|---|
| `mentor` (default) | When a candidate decision is detected, surface a teaching block explaining why this is decision-worthy, then draft an ADR for the user to review. |
| `dev` | Surface candidate decisions as a quick list. No teaching block, no draft. User picks Y/N. |

Mode is project-level; user can flip it any time by editing `.rad/profile`.

## Cross-machine + cross-agent continuity

If your project has a git remote, rad-session keeps the canonical docs in sync — across machines AND across agents (Claude ↔ Codex):

| Phase | What it does |
|---|---|
| `/startup` bootstrap (first run) | Ensures `docs/status.md`, `docs/planning/`, `docs/decisions/`, and the operating manual aren't gitignored. |
| `/wrapup` Phase 7 | Auto-commits `docs/status.md` + any `planning/archive/` entries + any new `decisions/NNNN-*.md` ADRs + operating-manual changes. Prompts: `Push session files to origin? (Y/n)`. Commit message: `session: YYYY-MM-DD on <hostname> — <status>`. |
| `/startup` Phase 0 | Fetches origin and prompts to pull when behind. Lists incoming commits before approval. On approval, fast-forwards. On decline, briefing leads with `⚠ Reading stale local state`. If the most recent session commit was made on a different host, briefing also leads with `Continuing from <other-host>`. |

**Auto-commit, prompted push.** Local commits are cheap so they always happen. Push is a deliberate "I'm about to switch machines" decision. Stack multiple unpushed session commits on the same machine; push when ready to hand off.

**Multi-branch active hybrid.** When `multi_branch_status = true` in `.rad/profile`, `/wrapup` writes per-branch status (e.g. `docs/status.feat-invoice-pdf.md` alongside the main `docs/status.md`). Opt-in for projects that maintain several active branches simultaneously.

**Safety:** wrapup never force-pushes, never touches non-session files, and bails cleanly on diverged history. Startup never merges, never rebases, never discards local work — it only attempts a fast-forward pull and warns if it can't.

## Working with rad-planner

rad-session and rad-planner are **soft-coupled** — each is independently useful, and they share contracts via the canonical doc structure:

1. **Operating manual (sectioned-writer).** rad-planner writes Constitution sections during `/plan` M6; rad-session writes Operational sections during `/startup` bootstrap. Each parses headers and modifies only its owned list.
2. **`docs/status.md` (single-writer, rad-session).** Written by `/wrapup` from evidence. Read by `/plan` to ground the conversation in current reality.
3. **`docs/planning/current.md` (single-writer, rad-planner).** Written by `/plan` from intent. Read by `/wrapup` to detect milestone-shipped state.
4. **`docs/decisions/` (creation by rad-planner; prompts by both).** rad-planner creates the directory + README at `/plan` M6 and seeds initial ADRs. rad-session prompts to add new ADRs when candidate decisions surface at `/wrapup`. The user's `y` is what authorizes the write.
5. **Cross-doc validators.** rad-planner ships four Python validators at `plugins/rad-planner/scripts/`: `plan-lint.py`, `status-validator.py`, `doc-redundancy.py`, `doc-contradiction.py`. rad-session's `/wrapup` Phase 4 invokes `doc-redundancy.py` and `doc-contradiction.py` against the project; if rad-planner is not installed, Phase 4 silently no-ops.

**rad-session works standalone** — `/startup` bootstrap notes when strategic docs are missing; `/wrapup` skips cross-doc validators gracefully. **rad-planner works standalone** — `/plan` produces strategic docs whether rad-session is installed or not.

## What `/startup`'s bootstrap does (first run only)

Fires automatically in Phase 0.5 when `.rad/profile` / operating manual / `docs/status.md` are missing. Skipped silently on every subsequent invocation.

1. **Verify Python availability** — falls back to LLM-based detection if missing.
2. **Run `detect-stack.py`** — scans languages, frameworks, package manager, scripts, deploy targets, infrastructure.
3. **Run `detect-resources.py --check-clis`** — scans `.mcp.json`, `.claude/settings.json`, marker files. Flags CLIs the project assumes but aren't installed.
4. **Ask agent-scope** — Claude only / Codex only / both. Persists to `.rad/profile`.
5. **Run `audit-plugin-bloat.py`** — proposes per-project `enabledPlugins` disables to cut token cost on projects that don't use a given plugin's stack.
6. **Scaffold operating manual Operational sections** per scope (sectioned-writer rule).
7. **Scaffold `docs/status.md`** with the 8-section schema, all sections marked "No data yet — populated by /wrapup from evidence."
8. **Scaffold `.claude/settings.json` and/or `.codex/config.toml`** per scope.
9. **Write `.rad/profile`** with mode + agent_scope + multi_branch_status.
10. **Bootstrap summary** — what was created/modified, what to do next (typically: `/rad-planner:plan` to populate strategic docs and Constitution sections). Then falls through to the normal Phase 1+ briefing.

Safe to re-run: merges, never overwrites. `/startup --bootstrap` forces it; `/startup --no-bootstrap` skips it. Has `--non-interactive`, `--dry-run`, `--agents <scope>` flags for autonomous setup runs.

## Example `/startup` briefing (steady state)

```
Project: wayfinder
Type: Coding (Next.js + Supabase + Drizzle)
Branch: main (up to date)
Mode: mentor    Scope: claude_only

Current milestone: M2 — Activity-constraint engine
Status: on track

Where we left off (status.md):
  - Constraint evaluator implemented at lib/constraints/evaluator.ts (24/24 tests passing)
  - Constraint type definitions locked at lib/constraints/types.ts

Open acceptance criteria (current.md):
  - [ ] Failure reasons surfaced (which constraint failed, by how much)
  - [ ] UI handles 1+ constraint sets per user
  - [ ] Visual Crossing rate-limit handling

Latest validation:
  - bun test lib/constraints/ → pass (24/24)
  - bun run typecheck → pass

Next recommended step:
  Start the Drizzle CRUD layer in lib/constraints/queries.ts. First decide: per-user vs per-account scope.

Ready to continue. What would you like to work on?
```

See `references/briefing-examples.md` for the full template set (5 shapes).

## Upgrading

### From rad-session 5.0 to 5.1

No project-level migration needed. v5.1 keeps the same artifacts (`.rad/profile`, operating manual Operational sections, `docs/status.md`); only the command surface changed:

- The separate `/init` skill is retired (it conflicted with Claude Code's built-in `/init`).
- Bootstrap logic moved to `/startup` Phase 0.5 — fires automatically on first run for a project; skipped on every subsequent run.
- If you typed `/rad-session:init` before, type `/rad-session:startup` now. It detects whether bootstrap is needed.

## How this compares to alternatives

|  | **rad-session 5.1** | claude-plugins-official/remember | claude-mem | thepushkarp/handoff |
|---|---|---|---|---|
| Project bootstrap (auto-fires in `/startup`) with deterministic stack detection | ✅ | ❌ | ❌ | ❌ |
| Multi-agent (Claude + Codex) support | ✅ **unique** | ❌ | ❌ | ❌ |
| Intent-vs-reality split (status.md from evidence) | ✅ **unique** | ❌ | ❌ | ❌ |
| Sectioned-writer operating manual | ✅ **unique** | ❌ | ❌ | ❌ |
| Cross-machine sync via git (auto-commit + prompted push) | ✅ | ❌ | ❌ | ❌ |
| Active operating-manual prune | ✅ | compression | ❌ | ❌ |
| Cross-doc validators (redundancy + contradiction) | ✅ | ❌ | ❌ | ❌ |
| PreCompact safety net | ✅ | ✅ | ✅ | ✅ |
| Zero dependencies for skills (Python optional for scripts) | ✅ | ❌ (Haiku) | ❌ (Chroma) | ✅ |

**When to use rad-session:** you want a structured workflow lifecycle for an agent-driven project across Claude and/or Codex — bootstrap once (automatically on first `/startup`), orient each session, capture each session from evidence.

## Quick Start

```bash
/plugin marketplace update rad-claude-skills
/plugin install rad-session@rad-claude-skills
```

**First time in a project (and every session thereafter):**

```
/startup                                # first time: bootstraps inline (interactive)
                                        # subsequent: read-only briefing (<5s)
/startup --non-interactive              # accept defaults during bootstrap
/startup --agents claude_and_codex      # pre-set agent scope; skips the prompt
/startup --auto-pull                    # fast-forward silently when behind
/startup --no-pull                      # skip sync entirely
/startup --bootstrap                    # force bootstrap re-run (refresh audit, etc.)
```

**Register resources as you discover them:**
```
remember we have the coolify MCP available for this project
```

**End of every session:**
```
/wrapup                 # auto-commits, prompts to push
/wrapup --push          # commit + push without prompting
/wrapup --no-push       # commit locally only
/wrapup --quick         # skip Phase 3/4/5 (terse wrapup)
```

**Switching machines or agents.** Run `/wrapup --push` on the PC (Claude). On the laptop (Codex), the user's Codex session reads the same `docs/status.md` directly — or via `/wrapup` Codex equivalents if the agent has its own session lifecycle. No manual git work, no copy-paste.

## What's NOT in scope

- **Does not write strategic docs** — that's rad-planner's `/plan`. `/startup`'s bootstrap notes missing strategic docs and recommends `/rad-planner:plan`.
- **Does not install rad-* plugins for you** — `/startup`'s bootstrap recommends; you decide.
- **Does not configure MCP servers** — detects what's already there.
- **Does not run tests, builds, or any side-effect commands** beyond detection scripts and `mkdir`.
- **Does not exec stack binaries** without `--check-clis` opt-in.
- **Does not read `.env`** — only `.env.example`, and only variable names.
- **Does not orchestrate code reviews** — use the specialist reviewers directly (rad-code-review for general, rad-supabase / rad-coolify-orchestrator / rad-a11y / rad-chrome-extension for their domains).

## Version

**5.1.0** — **`/init` folded into `/startup` Phase 0.5; resolves name conflict with Claude Code's built-in `/init`.** Same artifacts, same scaffolds, one less command surface to learn. Bootstrap auto-fires on first run for a project (detects missing `.rad/profile` / operating manual / `docs/status.md`); skipped on every subsequent run. New flags on `/startup`: `--bootstrap` (force re-run), `--no-bootstrap` (skip even if missing — diagnostic), `--agents <scope>` (set scope without prompting), `--non-interactive`, `--dry-run`. No project-level migration needed from 5.0.

**5.0.0** — **Canonical doc structure + intent-vs-reality split + multi-agent support.** Aligned with published OpenAI/Anthropic project-structure research.
- **`docs/status.md` replaces `HANDOFF.md`** — project-scoped, evidence-based, written from git + test output, not chat synthesis.
- **`docs/planning/current.md` (rad-planner-owned)** carries intent. `docs/status.md` (rad-session-owned) carries reality. The split makes each artifact reliable independently.
- **`docs/planning/archive/`** replaces `.claude/session-log.md` — one file per shipped milestone, not per session.
- **Sectioned-writer rule for the operating manual** — rad-planner writes Constitution; rad-session writes Operational. Each parses headers, modifies only owned sections, preserves user-added sections.
- **Agent scope routing** — first-run setup asks once (Claude / Codex / both); persists to `.rad/profile`; all skills read the profile and write to the correct file(s). (In 5.0 this was `/init`; folded into `/startup` Phase 0.5 in 5.1.)
- **Mode-aware `/wrapup` Phase 3** — `mentor` mode teaches and drafts ADRs; `dev` mode shows quick lists.
- **Cross-doc validators integrated** — `/wrapup` Phase 4 calls `doc-redundancy.py` and `doc-contradiction.py` from rad-planner.
- **Milestone-shipped archive** — `/wrapup` Phase 6 detects all ACs checked in `current.md` and prompts to archive.
- **Multi-branch active hybrid** — opt-in per-branch status via `multi_branch_status` in `.rad/profile`.
- **Anomaly-gated final output** preserved from 3.5.2 — silent on success.
- **PreCompact hook** preserved.

**4.0.0** — **8-doc standardization (soft-coupled with rad-planner 3.0).** Introduced `CLAUDE-FRAGMENT.md` handoff, strategic-doc gap-check in `/startup` Phase 1.5, `DECISIONS.md` prompt in `/wrapup` Phase 3.5. Single-writer rule: rad-session owned CLAUDE.md / HANDOFF.md / session-log; rad-planner owned PRD / ARCH / ASSUMPTIONS / DECISIONS / PLAN / tasks.md / FRAGMENT. **Retired in v5.0 in favor of the canonical doc structure.**

**3.7.0** — Removed Haiku model pin (context-window regression fix).

**3.6.0** — Per-project plugin-bloat audit (Step 5.5 in the bootstrap path). `audit-plugin-bloat.py` detects 10 stack signals and writes `enabledPlugins` disables to `.claude/settings.local.json`. ~1–3K tokens cut from baseline per turn on typical projects.

**3.5.2** — Anomaly-gated final output for `/wrapup` (silent on success).

**3.5.1** — Removed Phase 5 "surface insights" (empirically dead — zero downstream pickup across 12+ wrapups).

**3.5.0** — Haiku-pinned skills (reverted in 3.7), cached resource scan, low-activity auto-quick.

**3.4.0** — Maintenance mandatory + per-bullet caps. Closed the silent-skip-of-maintenance defect.

**3.3.0** — Verify-before-read sync on `/startup`. Fetches first, prompts to pull when behind, lists incoming commits.

**3.2.0** — Slim wrapup. Recency-bounded tagging, mechanical session-log derivation, auto-skip prune when unchanged.

**3.1.0** — Cross-machine continuity via auto-commit + prompted push.

**3.0.0** — Lifecycle expansion. Added `/init` (retired in 5.1, folded into `/startup`) and two Python detection scripts. Absorbed retired rad-stack-guide.

**2.x** — Original Resource Discovery and CLAUDE.md prune protection.

**1.0.0** — Initial release: `/wrapup` and `/startup` skills.

## License
Apache-2.0

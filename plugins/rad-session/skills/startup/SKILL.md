---
name: startup
description: >
  Start-of-session skill for v5.1 — orient a new session by reading the operating
  manual (CLAUDE.md / AGENTS.md per .rad/profile agent_scope), docs/status.md
  (evidence-based reality from last /wrapup), docs/planning/current.md (active
  plan), and presenting a concise resume briefing. On first run for a project
  (when .rad/profile / operating manual / docs/status.md are missing), bootstraps
  the project first — detects the stack, determines agent scope, scaffolds the
  operating manual's Operational sections per the sectioned-writer rule, creates
  docs/status.md, writes .rad/profile, and creates .claude/settings.json /
  .codex/config.toml per scope. Steady-state behavior is read-only and targets
  <5s wall clock. Bootstrap path is one-time and interactive.
  Trigger when the user says "/startup", "start session", "orient me", "what's
  the state", "session briefing", "where did we leave off", "catch me up", "what
  was I working on", "set up rad-session here", "bootstrap this project", "new
  project setup", "configure rad-session for this project".
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# Session Startup (v5.1)

Open the store: ensure rad-session machinery is in place (one-time bootstrap on first run), read the operating manual, read `docs/status.md` (where things actually are), read `docs/planning/current.md` (where things should go), surface the resume context concisely, and get out of the way.

**Doorman model** for steady state: quick, deliberate, no ceremony. Target under 5 seconds wall clock. **Janitor model** for the bootstrap path: a single one-time interactive setup that handles stack detection, agent scope, operating manual scaffold, status.md scaffold, profile creation.

> **Status:** rad-session 5.1 — `/init` retired and folded into `/startup`. v5.0 had a separate `/init` skill that conflicted with Claude Code's built-in `/init`. v5.1 detects whether bootstrap is needed and runs it in Phase 0.5 before normal startup; no separate command needed.

## What changed from v5.0

| v5.0 | v5.1 |
|---|---|
| `/init` (separate command, name-collides with Claude Code's built-in `/init`) | folded into `/startup` Phase 0.5 — auto-detect; bootstrap fires only when needed |
| Two commands to remember at project start (`/init` then `/startup`) | One command (`/startup`) — first run bootstraps; subsequent runs are read-only |
| Bootstrap is unconditional on `/init` invocation | Bootstrap fires only when `.rad/profile` / operating manual / docs/status.md are missing |

Functionally everything `/init` did is still here; just one less command surface to learn and no parser-level conflict with Claude Code's built-in `/init`.

## Mode flags

- `--auto-pull` — Skip the Phase 0 prompt; fast-forward silently when behind. For autonomous loops or when you've already decided to always sync.
- `--no-pull` — Skip the sync check entirely; read local files as-is. Briefing leads with a stale warning if origin has unpulled commits. For offline work.
- `--bootstrap` — Force Phase 0.5 bootstrap to re-run even if all artifacts are present. Use to refresh the plugin-bloat audit / stack summary or after manual changes to `.rad/profile`. Idempotent.
- `--no-bootstrap` — Skip Phase 0.5 even if artifacts are missing. Read-only fallback for diagnostics.
- `--agents <scope>` — Set agent scope without prompting during bootstrap (`claude_only` | `codex_only` | `claude_and_codex`). Only relevant if bootstrap fires.
- `--non-interactive` — Skip all user-confirmation prompts in the bootstrap path. Defaults apply. Pairs naturally with autonomous loops.
- `--dry-run` — In bootstrap path, run detection and propose scaffolds without writing. In steady state, no effect.

Default behavior: bootstrap fires automatically when needed; otherwise read-only orientation.

## Cross-model note

Output briefing format is identical across Opus 4.7, Sonnet 4.6, and Haiku 4.5. This skill runs in the **session model** — whatever tier you're already in. Resource discovery is delegated to `scripts/detect-resources.py` with caching, so the model rarely does scanning work itself.

---

## Execution: parallel-first (steady state)

Phase 0 (sync from origin) **must run first** because it can update the very files the rest of the skill reads. After Phase 0 resolves (pulled, declined, skipped, or aborted), Phase 0.5 runs the bootstrap check. If bootstrap is needed, Phase 0.5 is its own multi-step interactive flow. If bootstrap is skipped (steady state), Phases 1, 2, and 2.5 have no inter-phase dependencies — every read and shell command can be issued as a single parallel batch.

**Batch to issue at the start of the skill (after Phase 0 + Phase 0.5 resolve, in steady state):**

- Read `.rad/profile` (Phase 1.1 — determines which operating manual files to read)
- Read `CLAUDE.md` and/or `AGENTS.md` per agent_scope (Phase 1.2)
- Read `docs/status.md` or `docs/status-<branch>.md` per multi_branch_status (Phase 1.3)
- Read `docs/planning/current.md` (Phase 1.4)
- Read `docs/vision.md`, `docs/architecture.md` (Phase 1.5 file-existence checks)
- Glob `docs/decisions/*.md` (Phase 1.5)
- Read `.mcp.json`, `.claude/settings.json`, `.env.example`, `package.json`, `pyproject.toml` (Phase 2.5)
- Glob for stack marker files (Phase 2.5.2)
- Bash: combined `git status --short && git log --oneline -5 && git rev-parse --abbrev-ref HEAD && git rev-list --left-right --count HEAD...@{upstream}` (Phase 2.2)

Missing files error silently — skip them in the briefing. Do not re-attempt serial reads after a parallel batch.

---

## Phase 0: Sync from origin

A handoff is only useful if you're reading the latest state. Phase 0 confirms local matches origin **before** any operating manual / status.md / planning/current.md read fires.

### 0.1 Skip silently if any hold

- Project is not a git repo (`git rev-parse --git-dir` fails).
- Current branch has no upstream (`git rev-parse --abbrev-ref --symbolic-full-name @{u}` fails).
- An in-progress merge / rebase / cherry-pick (`.git/MERGE_HEAD` or `.git/REBASE_HEAD` exists).

### 0.2 Fetch and compare

```bash
git fetch --quiet 2>/dev/null
git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null
```

Output is `<ahead>\t<behind>`. Also check tree cleanliness with `git status --porcelain` — used to decide whether a fast-forward is even possible.

### 0.3 Act on the result

A fast-forward is possible when the tree is clean AND ahead = 0. Otherwise it's blocked (dirty tree or diverged).

| State | `--auto-pull` | `--no-pull` | Default (no flag) |
|---|---|---|---|
| Behind = 0 | continue silently | continue silently | continue silently |
| Behind > 0, FF possible | `git pull --ff-only` silently | stale-warn + read local | show incoming commits + prompt; on Y → pull, on N → stale-warn + read local |
| Behind > 0, FF blocked | block-warn + read local | block-warn + read local | block-warn + ask "Read local anyway? (Y/n)" — Y reads local, N aborts the briefing |

**Stale warning** (placed at the top of the Phase 3 briefing, above the Project line):
```
⚠ Reading stale local state — origin has N unpulled commits. Re-run /startup without --no-pull to sync.
```

**Block warning** (placed at the top of the Phase 3 briefing):
```
⚠ Couldn't sync — <dirty working tree | local diverged from origin>. Resolve with: <git stash | git pull --rebase>.
```

When prompting in the default behind-FF-possible case, list the incoming commits first via `git log HEAD..@{u} --oneline -10` so the user sees what's about to land. Default the prompt to Y.

### 0.4 Cross-machine handoff signal

Fires whenever the most recent commit to `docs/status.md` was made on another machine — independent of whether this turn pulled.

```bash
git log -1 --format='%s' -- docs/status.md 2>/dev/null
```

Parse for the canonical session-commit format `session: YYYY-MM-DD on <hostname> — <status>` written by `/wrapup`.

- Hostname differs from `$HOSTNAME` / `$COMPUTERNAME` / `hostname` → stash this Phase 3 note:
  ```
  Continuing from <other-host> — last status update committed there.
  ```
- Hostname matches → no note (continuing on the same machine).
- Commit doesn't match the canonical session format (manual commit) → skip silently.

The cross-machine note appears at the top of the Phase 3 briefing, above the Project line and below any stale/block warning.

---

## Phase 0.5: Bootstrap check (one-time per project)

Detect whether rad-session machinery is in place for this project. If everything is set up, skip the bootstrap path and continue to Phase 1 (steady-state orientation). If anything is missing, run the bootstrap inline, then continue to Phase 1.

### 0.5.1 Detection (read-only; always runs)

Quick presence check via parallel Glob:

| Artifact | Present? |
|---|---|
| `.rad/profile` | needed to know agent_scope before Phase 1.2 |
| Operating manual (`CLAUDE.md` and/or `AGENTS.md`, or non-canonical via header heuristic) | needed for Phase 1.2 read |
| `docs/status.md` | needed for Phase 1.3 read |

**Bootstrap decision matrix:**

| Detection | `--bootstrap` flag | `--no-bootstrap` flag | Default |
|---|---|---|---|
| All present | run bootstrap (forced refresh) | skip | skip |
| Any missing | run bootstrap | skip + warn | run bootstrap |

If `--no-bootstrap` is set and artifacts are missing, surface this single warning at the top of the Phase 3 briefing:

```
⚠ Bootstrap skipped (--no-bootstrap) but artifacts are missing: <list>. /startup ran in read-only diagnostic mode. Re-run /startup to bootstrap normally.
```

### 0.5.2 Bootstrap path (only fires when needed)

Notify the user first:

```
Bootstrapping rad-session for this project (first-run setup, one-time).
This is the path that v5.0 used /init for — folded into /startup in v5.1.
```

Then execute steps 1–10 below. The steps are mostly the same as v5.0's `/init` skill; the only difference is they run inside `/startup` rather than as a separate command.

#### Step 1: Verify Python is available

```bash
python3 --version 2>/dev/null || python --version 2>/dev/null
```

If neither, fall back to LLM-based detection (manual marker scan + package.json read) and warn the user.

#### Step 2: Run detection scripts in parallel

```bash
python3 ${plugin_root}/scripts/detect-stack.py "$PWD" --json > /tmp/rad-stack.json
python3 ${plugin_root}/scripts/detect-resources.py "$PWD" --check-clis --include-env-names --json > /tmp/rad-resources.json
```

Both complete in well under a second. Read both JSON outputs.

#### Step 3: Pre-flight discovery

##### 3a — Project directory

Default to `$PWD`. If `/startup` was invoked with an explicit path argument (rare), validate it exists and is writable, then use that. **Never write outside the project directory** — hard rule for all downstream steps.

##### 3b — Agent scope

Determine which coding agents will use this project.

**Detection order:**

1. If `.rad/profile` exists and has `agent_scope` set → use it (this is the `--bootstrap` refresh case; skip the prompt)
2. If `/startup` was invoked with `--agents <scope>` → use that
3. Otherwise → ASK:

> "Which coding agents will use this project?
> 1. Claude only (CLAUDE.md canonical)
> 2. Codex only (AGENTS.md canonical)
> 3. Both Claude and Codex (AGENTS.md canonical + CLAUDE.md `@AGENTS.md` shim)
> 4. Not sure yet — defaults to Claude only (this is a Claude plugin); can change later"

Save `agent_scope`. Defaults to `claude_only` if user is unsure — rad-session is a Claude plugin, Claude-native is the right default.

##### 3c — Existing state detection

Mechanical read-only inspection of the project directory. Compute a feature vector:

| Field | Source |
|---|---|
| `has_git` | `.git/` exists with at least 1 commit |
| `has_claude_md` | `CLAUDE.md` exists |
| `external_claude_init_residue` | `CLAUDE.md` <500 bytes AND no `@AGENTS.md` line AND no `## Compact Instructions` section (matches Claude Code's built-in `/init` default scaffold pattern) |
| `has_agents_md` | `AGENTS.md` exists |
| `external_codex_init_residue` | `AGENTS.md` <500 bytes AND matches Codex `/init` default scaffold pattern |
| `has_vision` | `docs/vision.md` exists with non-trivial content |
| `has_architecture` | `docs/architecture.md` exists with non-trivial content |
| `has_planning_current` | `docs/planning/current.md` exists with non-trivial content |
| `has_status` | `docs/status.md` exists with non-trivial content |
| `has_decisions` | `docs/decisions/` directory exists with at least `README.md` |
| `has_rad_profile` | `.rad/profile` exists |

**Note on `external_*_init_residue` fields:** these detect output from *external* init tools (Claude Code's built-in `/init` skill, Codex's `/init` command). They are NOT residue from a prior rad-session run. Rad-session's bootstrap path can safely enrich files showing this pattern.

Save the full feature vector for use in subsequent steps.

#### Step 4: Synthesize a stack summary for the user

Present detection results as a brief, scannable summary:

```
Detected stack:
  Languages:       [from detect-stack]
  Frameworks:      [from detect-stack]
  Package manager: [from detect-stack]
  Deploy targets:  [from detect-stack]
  Infrastructure:  [from detect-stack]

Detected resources:
  MCP servers:     [from detect-resources]
  Stack CLIs:      [from detect-resources, with installed/missing flags]

⚠ CLIs the project assumes but NOT in PATH: [list, if any]

Existing rad-session state (v4.0 canonical):
  Operating manual: {agent_scope-specific state — see Step 6}
  docs/vision.md:           [present | missing]
  docs/architecture.md:     [present | missing]
  docs/planning/current.md: [present | missing]
  docs/status.md:           [present | missing]
  docs/decisions/:          [present (N ADRs) | missing]
  .rad/profile:             [present | missing]
```

#### Step 5: Recommend rad-* plugins for the detected stack

Match detected stack to currently-shipping rad-* plugins. **Be honest about which actually exist.**

| Detected signal | Recommended plugin | What it adds |
|---|---|---|
| `supabase` (deploy_target or framework) | `rad-supabase` | RLS audit, MCP integration for live ops, migration patterns |
| `coolify` (deploy_target) or Dockerfile + Traefik patterns | `rad-coolify-orchestrator` | Coolify-specific deploy patterns + MCP for live operations |
| `manifest.json` + `wxt.config` or extension-shaped project | `rad-chrome-extension` | MV3 conventions, CWS compliance, manifest validation |
| Any frontend framework + accessibility concerns mentioned | `rad-a11y` | WCAG 2.2 AA review, axe-core integration |
| Coding project of any kind | `rad-code-review` | Diff-aware adversarial code review |
| Project planning needed | `rad-planner` | Plan-first workflow, four entry points, four mechanical validators (4.0) |
| Brainstorming / design needed | `rad-brainstormer` | Pre-planning ideation + design specs |
| Project explanation / pitch / grounded README work | `rad-explain` | Narrate / pitch / explain documents / ground READMEs against actual code |

For each recommendation, surface what's installed vs. not.

#### Step 5.5: Plugin / MCP bloat audit

Claude Code's user-scope plugin set carries a real per-turn token cost. This step proposes an `enabledPlugins` map in `.claude/settings.local.json` (gitignored, personal) that disables irrelevant plugins for **this** project specifically. User-scope plugins stay intact in other projects.

##### 5.5.1 Get the installed plugin list

```bash
claude plugin list 2>/dev/null | grep -E '^\s*>\s*[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+' > /tmp/rad-installed-plugins.txt || true
```

If `claude plugin list` is unavailable, ask the user to paste the output.

##### 5.5.2 Run the audit script

```bash
python3 ${plugin_root}/scripts/audit-plugin-bloat.py "$PWD" --json --installed-plugins-stdin < /tmp/rad-installed-plugins.txt > /tmp/rad-plugin-audit.json
```

The script detects ~10 stack signals, applies plugin-relevance rules, filters to only INSTALLED plugins, and outputs per-plugin recommendation (`keep` | `disable`) with reason.

##### 5.5.3 Present the audit to the user

```
Plugin / MCP audit ({total} installed):

Will keep ({N}):
  Core: rad-session, code-simplifier, ...
  Stack-matched: pyright-lsp (python), rad-supabase (supabase), ...

Recommend disable for this project ({N}):
  No matching signal:
    - chrome-devtools-mcp [MCP] — no frontend_web signal
    - rad-coolify-orchestrator [MCP] — no coolify signal
    - ...

Estimated savings: ~{N} tool names cut per turn, plus ~{N} skill descriptions.
```

##### 5.5.4 Get user confirmation

Default behavior: prompt the user.

```
Apply these disables to .claude/settings.local.json? [Y/n/edit]
```

In `--non-interactive` mode, auto-apply.

##### 5.5.5 Write the settings

Read existing `.claude/settings.local.json` if present. **Merge — do not replace**. Preserve `permissions`, any other fields. Add or update the `enabledPlugins` map.

##### 5.5.6 settings.json (committed) vs settings.local.json (gitignored)?

Default: `.claude/settings.local.json`. Ask once if the project is single-author or the user wants the disables shared.

##### 5.5.7 Note for activation

```
⚠ Plugin disables take effect on next session start. The current session continues with the full set already loaded.
```

##### 5.5.8 Re-running the audit

On subsequent invocations (with `--bootstrap` refresh), compare current settings against fresh audit recommendations and surface a diff.

#### Step 6: Operating manual scaffolding

Determine paths per `agent_scope`:

| Scope | Files written by bootstrap |
|---|---|
| `claude_only` | `CLAUDE.md` (canonical) |
| `codex_only` | `AGENTS.md` (canonical) |
| `claude_and_codex` | `AGENTS.md` (canonical) + `CLAUDE.md` (`@AGENTS.md` shim) |

**Critical: bootstrap writes Operational sections only.** Per the sectioned-writer rule:

- **Operational sections (rad-session writes):** Commands, Compact Instructions (CLAUDE.md only), Claude-specific behavior (CLAUDE.md only), `@AGENTS.md` import line (CLAUDE.md shim case)
- **Constitution sections (rad-planner `/plan` M6 writes):** Project, Read order, Hard boundaries, Engineering rules, Definition of done, Escalate triggers

If Constitution sections are missing, leave them missing — surface in Step 10 final report: "run `/rad-planner:plan` to populate Constitution sections."

##### 6.1 Detect existing state per file

For each target file (per agent_scope table above):

- **Case A: file doesn't exist.** Scaffold from template (see 6.2).
- **Case B: file exists with external `/init` residue** (per Step 3c `external_claude_init_residue` or `external_codex_init_residue`). Enrich — insert Operational sections; preserve everything else. Surface "Preserved existing content above."
- **Case C: file exists with substantial content.** Guard rail — three-option prompt:
  > "`{filename}` exists with N lines. Three options:
  > 1. Overwrite — replace existing content with rad-session scaffold (loses user content; backup made)
  > 2. Append Operational sections — preserve all existing content; insert Commands / Compact Instructions / Claude-specific behavior sections in their proper place
  > 3. Skip — leave file untouched"

  Default: append. Show diff before writing.

  **Data-loss-protected: this prompt fires regardless of permission mode.** Auto / Bypass / `--non-interactive` do NOT suppress Case C. Overwriting user-authored content has asymmetric downside (potential loss of substantial work); permission-mode autonomy is about not pestering for routine tool approvals, not about silently overwriting files the user wrote. If the harness signals "don't ask clarifying questions," interpret that as "don't ask trivial in-execution confirmations," NOT "skip the overwrite-vs-append-vs-skip choice on a file with substantial user content." The only flag that bypasses this prompt is an explicit `--force-overwrite` (not currently implemented — would require a future opt-in addition).

##### 6.2 Operating manual template (Operational sections only)

```markdown
## Commands

- Install: {from detected stack or placeholder}
- Dev server: {placeholder}
- Unit tests: {from package.json scripts or placeholder}
- Lint: {from package.json scripts or placeholder}
- Typecheck: {from package.json scripts or placeholder}
- Build: {from package.json scripts or placeholder}

{CLAUDE.md only:}

## Claude-specific behavior

- Use `/plan` for ambiguous, multi-file, or architectural work.
- Use subagents for broad codebase investigation, log triage, and post-change review so the main session stays focused.
- If the session drifts after repeated corrections, stop, update `docs/status.md`, and restart with a fresh session.

## Compact Instructions

When using compact:
- preserve the current objective
- preserve non-goals and hard boundaries
- preserve acceptance criteria
- preserve the current list of changed files
- preserve latest validation commands and results
- preserve blockers, open questions, and next step
- drop superseded exploration paths and abandoned ideas
```

For the CLAUDE.md shim case (claude_and_codex), the CLAUDE.md scaffold opens with:

```markdown
@AGENTS.md

## Claude-specific behavior
{...}

## Compact Instructions
{...}
```

(No Operational `## Commands` section in the shim — `AGENTS.md` carries Commands. The shim only adds Claude-specific Operational content.)

##### 6.3 Surface what was preserved

If user-added sections exist in the file (sections not in either rad-planner's owned list or rad-session's owned list), explicitly note in output:

> "Preserved user sections: `## Project gotchas`, `## Team notes`"

This makes preservation visible so the user can verify nothing was missed.

#### Step 7: docs/status.md scaffold

If `docs/status.md` doesn't exist:

```bash
mkdir -p docs
```

Create `docs/status.md` with the 8-section template per [`docs/status-md-schema.md`](../../../../docs/status-md-schema.md):

```markdown
# Status

## Current state
- Branch / worktree: (unknown — populated at first /wrapup)
- Current milestone: (unknown — populated from docs/planning/current.md)
- Overall status: No data yet — populated by rad-session /wrapup from evidence

## Last completed

No data yet — populated by rad-session /wrapup from evidence.

## Files changed recently

No data yet — populated by rad-session /wrapup from git evidence.

## Latest validation results

No data yet — populated by rad-session /wrapup from session evidence.

## Decisions made during execution

No data yet — populated by rad-session /wrapup when candidate decisions surface.

## Known issues or blockers

No data yet — populated by rad-session /wrapup.

## Next recommended step

No data yet — populated by rad-session /wrapup from planning/current.md and session context.

## If restarting from scratch

- Read {CLAUDE.md or AGENTS.md per agent_scope}
- Read docs/planning/current.md (if it exists — otherwise run /rad-planner:plan)
- Read docs/architecture.md (if it exists)
- Resume with: (populated at first /wrapup)
```

If `docs/status.md` already exists, leave it alone — user (or prior /wrapup) owns it.

#### Step 8: Tool-specific config scaffolding

Per [`docs/cross-plugin-contracts.md`](../../../../docs/cross-plugin-contracts.md), `.claude/settings.json` and `.codex/config.toml` are both rad-session-owned at creation; the human owns subsequent edits.

##### 8.1 `.claude/settings.json` (if Claude in scope)

If `agent_scope` includes Claude (`claude_only` or `claude_and_codex`) and `.claude/settings.json` is missing, scaffold with sensible defaults:

```json
{
  "permissions": {
    "allow": ["Read", "Glob", "Grep", "WebSearch", "WebFetch"],
    "ask": ["Write", "Edit", "Bash"]
  }
}
```

If `.claude/settings.json` already exists, leave it alone. Skip 8.1 entirely if `agent_scope == codex_only`.

##### 8.2 `.codex/config.toml` (if Codex in scope)

If `agent_scope` includes Codex (`codex_only` or `claude_and_codex`) and `.codex/config.toml` is missing, scaffold with sensible defaults:

```toml
# Codex project configuration
# rad-session scaffolds this file during /startup bootstrap; rad-planner adds hook entries on /plan M6.

approval_policy = "on-request"   # on-request | unless-allow-listed | never
sandbox_mode    = "workspace-write"  # read-only | workspace-write | danger-full-access

# [shell.env]
# Project-scoped environment variables Codex agents should inherit.

# [hooks]
# rad-planner /plan M6 adds approved hooks here based on the doc_set_draft.
```

If `.codex/config.toml` already exists, leave it alone. Skip 8.2 entirely if `agent_scope == claude_only`.

#### Step 9: .rad/profile

If `.rad/profile` doesn't exist:

```bash
mkdir -p .rad
```

Create with TOML content:

```toml
# rad-planner / rad-session project profile
mode = "mentor"               # mentor (teaching prompts in /wrapup) or dev (quick skip)
agent_scope = "{from Step 3b}"   # claude_only | codex_only | claude_and_codex
multi_branch_status = false   # true when per-branch status is opted in (active hybrid)
```

If `.rad/profile` exists, leave it alone — user owns it.

#### Step 10: Bootstrap summary

Show a brief summary before continuing to Phase 1:

```
Bootstrap complete.

Created/updated:
  - {operating manual file(s)}    ({new | enriched | additions made | unchanged})
  - docs/status.md                ({new | unchanged})
  - .claude/settings.json         ({new | unchanged | not applicable for codex_only scope})
  - .claude/settings.local.json   ({plugin disables added: N | unchanged})
  - .codex/config.toml            ({new | unchanged | not applicable for claude_only scope})
  - .rad/profile                  ({new | unchanged})

Strategic doc state:
  - {one of:}
    - "All v4.0 strategic docs present (vision, architecture, planning/current, status, decisions). Project fully set up."
    - "Some strategic docs missing: {list}. Recommend /rad-planner:plan --improve to complete."
    - "No strategic docs detected. Recommend /rad-planner:plan --full to create the plan and populate Constitution sections."

Now continuing with normal orientation...
```

Then fall through to Phase 1 (parallel reads + briefing). The user gets one combined output: bootstrap summary, then the regular briefing.

### 0.5.3 Notes on the bootstrap path

- **Idempotent.** Re-running with `--bootstrap` is safe — every step checks existing state and merges rather than overwrites.
- **One-time per project.** After the first successful bootstrap, subsequent `/startup` calls skip Phase 0.5 entirely (microseconds-level detection check).
- **Interactive by default.** Bootstrap asks for agent_scope unless `--agents <scope>` is set. Use `--non-interactive` for autonomous loops.
- **Backwards-compatible.** Projects bootstrapped under v5.0's separate `/init` look identical to those bootstrapped under v5.1's folded path. Same artifacts, same shapes.

---

## Phase 1: Read project state (steady state)

All reads in Phase 1 are issued as one parallel batch with Phases 2 and 2.5 (after Phase 0 + 0.5 resolve). The phase numbering is for human readability; execution is concurrent.

### 1.1 Read `.rad/profile`

Determine:

- `agent_scope` (`claude_only` / `codex_only` / `claude_and_codex`) — drives Phase 1.2
- `mode` (`mentor` / `dev`) — recorded but not used by /startup (used by /wrapup)
- `multi_branch_status` (`true` / `false`) — if true, Phase 1.3 reads `docs/status-<current-branch>.md` instead of `docs/status.md`

If `.rad/profile` doesn't exist (and Phase 0.5 was skipped via `--no-bootstrap`), default: `agent_scope = claude_only`, `mode = mentor`, `multi_branch_status = false`. Surface in briefing: "No .rad/profile detected — re-run /startup without --no-bootstrap to set up project profile."

### 1.2 Read operating manual

Per `agent_scope`:

- `claude_only` → read `CLAUDE.md`
- `codex_only` → read `AGENTS.md`
- `claude_and_codex` → read `AGENTS.md` (canonical) + `CLAUDE.md` (shim)

**Non-standard naming detection:** if the expected file is missing, Glob root for any `*.md` containing the heading `# Agent Operating Manual` or an `@AGENTS.md` import line. If found, treat that file as the operating manual — roll with what's there. Surface in briefing: "Operating manual: detected at non-standard path `<filename>`."

Extract:

- Project name and one-sentence purpose
- Read order (which docs to consult before what kind of work)
- Hard boundaries
- Engineering rules
- Definition of done
- Escalate triggers
- Commands (install / dev / test / lint / build)

Resolve `@-imports` one level deep. Missing import targets are reported silently with a "⚠ missing import: <path>" line in the briefing.

### 1.3 Read `docs/status.md` (the canonical handoff)

If `multi_branch_status == true`, read `docs/status-<current-branch>.md` instead.

Extract the 8 sections (per [`docs/status-md-schema.md`](../../../../docs/status-md-schema.md)):

1. **Current state** (branch, milestone, overall status: on track | blocked | validating | needs decision)
2. **Last completed**
3. **Files changed recently**
4. **Latest validation results**
5. **Decisions made during execution**
6. **Known issues or blockers**
7. **Next recommended step**
8. **If restarting from scratch** — load-bearing read order for the briefing

**If status.md doesn't exist** or all 8 sections show "No data yet — populated by rad-session /wrapup from evidence", fall through to Minimal Briefing in Phase 3.

### 1.4 Read `docs/planning/current.md` (the active plan)

Extract:

- Objective
- Current milestone
- Acceptance criteria (including checkbox state — count `[x]` vs `[ ]` for progress)
- Stop conditions
- Notes for the next session

If `current.md` doesn't exist, surface in briefing: "No active plan — recommend `/rad-planner:plan` to create one."

### 1.5 Strategic Doc Gap-Check (v4.0)

Soft gap-check for the v4.0 canonical strategic docs. The reads already happened in the parallel batch at the top of the skill — Phase 1.5 just inspects which Reads returned content vs. which silently errored.

| File | If missing |
|---|---|
| `docs/vision.md` | Add to "missing strategic docs" list |
| `docs/architecture.md` | Add to list |
| `docs/planning/current.md` | (already checked in 1.4) |
| `docs/status.md` | (already checked in 1.3) |
| `docs/decisions/` (directory with at least `README.md`) | Add to list |

**Output behavior:**

- **All present** → emit nothing. Strategic docs are in place.
- **Some missing** → single briefing line:
  ```
  ⚠ Missing strategic docs: <comma-separated list> — run /rad-planner:plan to create. (Soft warning; session continues.)
  ```

**Why soft.** Many sessions are pure execution against an existing plan; some are exploratory; some projects are too small for the full set. The warning informs without blocking — session continues regardless.

### 1.5.1 Draft-ADR check (NEW in v5.2)

After globbing `docs/decisions/*.md` in the parallel batch, count files whose first ~10 lines contain the string `DRAFT — auto-recorded` (the banner inserted by `/wrapup` Phase 3 under Auto mode). These are ADRs that were captured autonomously and need user review of LLM-inferred rationale.

**Output behavior:**

- **Zero draft ADRs** → emit nothing
- **One or more draft ADRs** → single briefing line (placed near the gap-check warnings):
  ```
  ⚠ N draft ADRs pending review: NNNN, NNNN — open and either remove the DRAFT banner to confirm, or edit/delete the rationale. Auto-recorded by previous /wrapup under harness autonomy.
  ```

This makes draft ADRs visible at session open so review doesn't get indefinitely deferred. Removing the banner is the user's signal that the ADR has been validated.

### 1.6 Status freshness check

Quick mtime check (or use `status-validator.py --mode freshness` if rad-planner is installed alongside):

```bash
python3 ${plugin_root}/../rad-planner/scripts/status-validator.py --mode freshness docs/status.md --json 2>/dev/null
```

If `status-validator.py` isn't available, inline check:

```bash
git log -1 --format='%ct' -- docs/status.md 2>/dev/null
git log -1 --format='%ct' HEAD 2>/dev/null
git rev-list "$(git log -1 --format=%H -- docs/status.md)..HEAD" --count 2>/dev/null
```

Compute:
- **fresh:** `(head_date - status_date) < 2 days` AND `commits_since_status < 5`
- **stale:** `(head_date - status_date) > 7 days` OR `commits_since_status > 20`
- **moderate:** in between

If stale, include warning in briefing:

```
⚠ docs/status.md is N days old (M commits since last update) — refresh at next /wrapup recommended.
```

If status.md doesn't exist at all, skip the freshness check.

---

## Phase 2: Detect Project Type

### 2.1 Project Type Detection

Use Glob to check for coding-project indicators (any of these):

```
package.json
Cargo.toml
pyproject.toml
go.mod
Makefile
*.sln
.git/
```

**Non-coding project:** none detected. Note this — the briefing drops git info.

### 2.2 Live State (Coding Projects Only)

Run as a single combined command:

```bash
git status --short 2>/dev/null && echo "---" && \
git log --oneline -5 2>/dev/null && echo "---" && \
git rev-parse --abbrev-ref HEAD 2>/dev/null && echo "---" && \
git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null
```

Capture: current branch, uncommitted changes, recent commits, ahead/behind vs. remote.

### 2.3 Detect Changes Since Last Status Update

If `docs/status.md` has been committed and the freshness check (1.6) returned non-fresh, spot-check for commits between the status's last-commit-date and HEAD. Flag in briefing as "changes since status last updated" — useful when work happened outside a rad-session session.

---

## Phase 2.5: Resource Discovery

Detect project-specific resources so Claude doesn't need to be reminded every session. All steps are read-only and issued in the parallel batch. Skip silently when nothing is found.

### 2.5.0 Preferred path: deterministic script (mtime-cached)

If Python is available, prefer the deterministic scanner over LLM-based marker scanning. Always pass `--cache` so cache-hit startups skip re-scanning entirely:

```bash
python3 ${plugin_root}/scripts/detect-resources.py "$PWD" --json --cache --include-env-names
```

The `--cache` flag writes results to `.claude/cache/resources.json`, keyed by mtimes of every input file. On cache hit, scanning is skipped — results return in milliseconds. The output adds a `"cache_status": "hit" | "miss"` field; surface under the briefing's resources block only if status is `miss` (e.g., `Resources: scanned fresh`); on `hit`, stay silent.

The script returns the same data structure as steps 2.5.1–2.5.6 below. Use JSON output verbatim. The LLM-based steps remain as fallback when Python is not available.

### 2.5.1 MCP Servers

Read `.mcp.json` at project root. Parse JSON and extract keys under `mcpServers`. Also read `.claude/settings.json` and collect names under `enabledMcpjsonServers` or plugin-scoped MCP entries. Merge without duplication. Malformed JSON → skip silently.

### 2.5.2 Stack CLIs (inferred from marker files)

Glob the project root for marker files. File-presence inference only — never exec any binary.

| Marker file(s) | Implied CLI |
|----------------|-------------|
| `supabase/config.toml` | `supabase` |
| `wrangler.toml`, `wrangler.jsonc` | `wrangler` |
| `netlify.toml` | `netlify` |
| `vercel.json` | `vercel` |
| `fly.toml` | `flyctl` |
| `firebase.json` | `firebase` |
| `.github/workflows/` (any *.yml) | `gh` |
| `Dockerfile`, `docker-compose.yml`, `compose.yaml` | `docker` |
| `coolify.json`, `.coolify/` | Coolify deploy target |
| `terraform/`, `*.tf` | `terraform` |
| `pulumi.yaml` | `pulumi` |
| `pyproject.toml` + `poetry.lock` | `poetry` |
| `Pipfile` | `pipenv` |
| `requirements.txt` (no poetry/pipenv) | `pip` |
| `Gemfile` | `bundle` |
| `deno.json`, `deno.jsonc` | `deno` |
| `bun.lockb`, `bunfig.toml` | `bun` |
| `Cargo.toml`, `rust-toolchain.toml` | `cargo` |
| `go.mod` | `go` |
| `mise.toml`, `.mise.toml` | `mise` |
| `.tool-versions` | `asdf` |
| `flake.nix`, `shell.nix` | `nix` |
| `devbox.json` | `devbox` |

Collect into a deduplicated list.

### 2.5.3 Package Manager & Scripts

If `package.json` exists:

- Read `packageManager` field. If absent, infer from lockfile.
- Extract top 5–8 keys from `scripts`. Prefer in order if present: `dev`, `build`, `test`, `typecheck`, `lint`, `start`, `check`, `format`.

Output example: `Scripts (pnpm): dev, build, test, typecheck, lint`

For Python: if `pyproject.toml` has a `[tool.poetry.scripts]` or `[project.scripts]` table, list up to 5 entries.

### 2.5.4 Environment Template

If `.env.example` exists, read it and extract variable names only (everything before `=` on each non-comment line). **Never read `.env`** or any file that may contain real values.

Output: `Env template: SUPABASE_URL, STRIPE_SECRET_KEY, ... (.env.example)`

### 2.5.5 Operating Manual Resources Section

If the operating manual (CLAUDE.md or AGENTS.md) contains a heading matching any of these (case-insensitive), extract its contents verbatim:

- `## Resources`
- `## MCP` / `## MCPs`
- `## Tools` / `## CLI Tools`

Treat as the **documented** source of truth for this project.

### 2.5.6 Reconciliation

Compare documented (2.5.5) against detected (2.5.1–2.5.4):

- **Documented + detected** → show normally in "Resources available."
- **Documented but not detected** → show with `⚠ documented but not found` — possible drift.
- **Detected but not documented** → show under `Also detected (not in operating manual):` — user may want to register via `/add-resource`.

If no Resources section exists in the operating manual, treat all detected items as primary with no drift warnings.

---

## Phase 3: Orient and Brief

Present a concise, scannable session briefing. Adapt the format based on what's available. Target **under 35 lines** (typically far less in routine cases) and **under 5 seconds wall clock**.

> **Floor of one line — never zero output (NEW in v5.3).** The first job of `/startup` is *to confirm it ran*. Silent completion violates the doorman model: the user just invoked a command and got nothing back, which reads as "did the tool actually run?" Even in the cleanest possible routine open (no anomalies, status fresh, plan healthy, no draft ADRs, no drift), `/startup` MUST emit at least a one-line confirmation that includes: status freshness signal, plan progress phrase, and a pointer to the canonical doc. Silence is the failure mode, not the goal.

### Briefing selection

| Condition | Template |
|---|---|
| Bootstrap fired this turn | **Bootstrap-then-brief** (Step 10 summary, then the appropriate steady-state template below) |
| status.md + planning/current.md both present + coding project | **Full Briefing** |
| status.md present, no planning/current.md | **Status-only Briefing** (recommend `/rad-planner:plan` to create the plan) |
| No status.md but operating manual exists | **Minimal Briefing** (no resume context to share; recommend `/wrapup` at end of next session to populate status) |
| No operating manual AND `--no-bootstrap` set | **No-bootstrap diagnostic** |
| No build-system markers | **Non-Coding Briefing** |

### Full Briefing structure

```
[warnings — one line each, in order: block, stale, cross-machine, gap-check, freshness]

Project: {from operating manual Project line}
Branch: {current_branch} ({clean | <N> uncommitted})
Plan: {milestone X of Y from planning/current.md; AC progress N/M ({pct}%)}

Last completed:
- {top 3-5 from status.md Last completed}

Recently changed:
- {top 3-5 files from status.md Files changed recently}

Validation: {from status.md Latest validation results — one line, only if recent and not 'No data this session'}

Open issues:
- {top 3 from status.md Known issues or blockers, only if any}

Next: {from status.md Next recommended step — one paragraph; use exact wording}

Resources: {from Phase 2.5 — MCPs / CLIs / scripts; omit if all categories empty}

Ready to continue. What would you like to work on?
```

### Status-only Briefing structure

```
[warnings]

Project: {from operating manual}
Branch: {current_branch}
Plan: (none — recommend /rad-planner:plan to create one)

Last completed: {from status.md, only if any}
Next: {from status.md Next recommended step, only if any}

Resources: {from Phase 2.5}

Ready to continue. What would you like to work on?
```

### Minimal Briefing structure

```
[warnings, if any]

Project: {from operating manual}
Branch: {current_branch}

No status.md yet — first session, or /wrapup hasn't run yet on this project.
Run /wrapup at the end of this session to populate status.md from evidence.

Resources: {from Phase 2.5}

Ready to continue. What would you like to work on?
```

### No-bootstrap diagnostic structure

Used when `--no-bootstrap` is set AND artifacts are missing. Read-only fallback for diagnostics:

```
⚠ Bootstrap skipped (--no-bootstrap) but artifacts are missing: <list>.
/startup ran in read-only diagnostic mode.

Project (guessed): {from directory name or detected stack}
Branch: {current_branch if git}

Re-run /startup (without --no-bootstrap) to bootstrap normally, OR /startup --bootstrap to force.
```

### Non-Coding Briefing structure

```
[warnings]

Project: {from operating manual} (non-coding)

{status.md Next, if present, else "No status.md."}

Ready to continue.
```

### Presentation rules

- Keep the briefing **under 35 lines** — this is a quick orientation.
- **Floor of one line.** The skill MUST produce at least one user-visible line even in the cleanest routine case. Silence violates the doorman model. See "Routine confirmation line" below.
- Use the **exact wording from status.md** — don't paraphrase. The wrapup chose those words from evidence; paraphrasing loses load-bearing detail.
- End with `Ready to continue. What would you like to work on?` to hand control back.
- **Omit empty blocks** — don't show "Validation: (none)" or empty Resources headers — BUT never omit the routine confirmation line.
- Cap each block at the line counts indicated; truncate with `...` if longer.
- If imports were resolved in Phase 1.2 and surfaced non-trivial content, add a single `Imports: <file1>, <file2>` line under Resources.
- If the "If restarting from scratch" section in status.md has a `Resume with:` line, prefer that verbatim as the Next-step content.

### Routine confirmation line (NEW in v5.3)

When all of the following hold:

- No sync warnings (block / stale / cross-machine all silent)
- No bootstrap fired (artifacts present)
- No strategic-doc gaps (1.5 emits nothing)
- No draft ADRs pending review (1.5.1 emits nothing)
- Status freshness check returns fresh (1.6 emits nothing)
- Git tree clean, no ahead/behind anomalies
- No resource drift

…the Full / Status-only / Minimal briefing structures above would emit a substantial scrollable block describing routine state. **In v5.3, the steady-state output collapses to a single-line confirmation when the underlying state is routine.** Template:

```
Routine open. docs/status.md fresh ({N} days, M{X} {Y}/{Z} ACs done). Read it to resume.
```

Concrete example:

```
Routine open. docs/status.md fresh (2 days, M3 2/5 ACs done). Read it to resume.
```

Anomalies add lines ABOVE the confirmation line. The confirmation line ALWAYS appears:

```
⚠ docs/status.md is 12 days old (8 commits since).
⚠ 2 draft ADRs pending review: 0007, 0008.

Routine open. M3 2/5 ACs done. Read docs/status.md to resume.
```

If status.md doesn't exist yet (Minimal Briefing case), the line shape adapts:

```
Routine open. No status.md yet — first session for this project, or /wrapup hasn't run. Read CLAUDE.md to orient; run /wrapup at session end to populate status.
```

If the operating manual is missing (First-time / no-bootstrap diagnostic case), the existing dedicated templates apply — those already have content, so the floor is naturally met.

### When to use the longer Full/Status-only briefing vs. the one-line routine confirmation

The decision is based on how much **non-status.md content** the briefing needs to surface:

| State | Briefing shape |
|---|---|
| Anomalies + non-status content (drift, resources, imports, draft ADRs, etc.) | Full / Status-only briefing as defined above, with all relevant blocks |
| No anomalies, routine state, status.md fresh | Single-line routine confirmation |
| Bootstrap fired this turn | Bootstrap summary then routine confirmation |
| First session / no operating manual | First-time briefing as defined above (already has content) |

Rationale: the Full Briefing's value is when status.md content needs to be *surfaced* (because anomalies exist alongside it, or because resource discovery added context). When status.md is fresh and clean, paraphrasing its sections in the briefing duplicates content the user can read directly. The one-line routine confirmation closes the "did anything happen?" gap without re-narrating what's already in canonical form.

**The exact wording rule still applies.** When the longer briefing fires, status.md sections appear verbatim. When the one-line routine confirmation fires, it points the user at status.md — they read the verbatim content there.

---

## What this skill does NOT do

- Does not modify files in steady state (strict read-only after Phase 0.5 detection — bootstrap path is the only write surface)
- Does not write `docs/status.md` from evidence — that's `/wrapup`'s job at session end (bootstrap path creates the scaffold only)
- Does not update `docs/planning/current.md` — that's `/rad-planner:plan` or human edits
- Does not invoke `/rad-planner:plan` — recommends only when missing
- Does not derive resume context from chat history — only from evidence on disk (status.md, planning/current.md, git)
- Does not run anything beyond read-only Bash commands + `detect-resources.py` in steady state
- Does not read `.env` or any file that may contain secret values
- Does not maintain `.claude/session-log.md` (retired in v5.0)
- Does not maintain `HANDOFF.md` (retired in v5.0 — replaced by `docs/status.md`)
- Does not write Constitution sections of the operating manual (rad-planner's job at `/plan` M6)
- Does not install plugins (the bloat audit only proposes per-project disables)

## Key references

**Canonical spec docs (top-level):**

- [`docs/doc-conventions.md`](../../../../docs/doc-conventions.md) — canonical file structure
- [`docs/cross-plugin-contracts.md`](../../../../docs/cross-plugin-contracts.md) — single-writer rule, sectioned-writer exception, .rad/profile protocol
- [`docs/status-md-schema.md`](../../../../docs/status-md-schema.md) — 8-section status schema with evidence sources

**Plugin internals:**

- `scripts/detect-stack.py` — deterministic stack scanner (used by bootstrap path)
- `scripts/detect-resources.py` — MCP + CLI scanner with drift detection and mtime cache
- `scripts/audit-plugin-bloat.py` — per-project plugin relevance audit (used by bootstrap path)
- `references/briefing-examples.md` — concrete v5.0+ briefing examples (5 templates: full / status-only / minimal / first-time / non-coding)
- `scripts/README.md` — full script documentation

## Mode flags (recap)

- `--auto-pull` — skip Phase 0 prompt, fast-forward silently when behind
- `--no-pull` — skip sync entirely; lead briefing with stale warning if behind
- `--bootstrap` — force Phase 0.5 bootstrap re-run even if artifacts present
- `--no-bootstrap` — skip Phase 0.5 even if artifacts missing (diagnostic mode)
- `--agents <scope>` — set agent scope during bootstrap (`claude_only` | `codex_only` | `claude_and_codex`)
- `--non-interactive` — suppress all prompts in bootstrap path
- `--dry-run` — in bootstrap path, propose scaffolds without writing

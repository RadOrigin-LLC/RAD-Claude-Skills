# rad-session — Claude Code workflow lifecycle: init, startup, wrapup, with cross-machine continuity.

**What it is.** A four-skill plugin that gives Claude Code projects a structured session lifecycle: bootstrap a project once, orient each session at the start, capture each session at the end, register tools as you discover them. Works for a single machine and **transparently keeps PC ↔ GitHub ↔ Laptop in sync** when a git remote exists.

**What it solves.** The default Claude Code experience loses session state at compaction, can't tell you what tools the project has, lets `CLAUDE.md` grow forever, and forgets everything when you switch machines. rad-session keeps a structured `HANDOFF.md` + capped session log so the next session (same or different machine) starts from a real briefing, prunes `CLAUDE.md` deliberately so it stays useful, and pulls/commits/pushes session files via git so your laptop sees what your PC did.

**What it isn't.** It is **not** an automation layer over your code: it never runs builds, never touches non-session files in commits, and never force-pushes.

> **v3.5 — Speed: Haiku-pinned skills + cached resource scan + low-activity auto-quick.** `/startup` and `/wrapup` now pin to Haiku 4.5 via per-skill `model:` frontmatter (the override applies for that turn only — your session model resumes on the next prompt). Resource detection is cached under `.claude/cache/resources.json`, keyed by input-file mtimes, so `/startup` skips re-scanning entirely when nothing has changed. `/wrapup` Phase 1.3 auto-applies `--quick` semantics when fewer than 10 substantive turns have happened since the last signal (`/wrapup`, `/checkpoint`, `/startup` briefing, or PreCompact). Together these typically cut `/startup` and `/wrapup` wall-clock time by 4–5× while preserving identical output formats. Override with `/model opus` before either skill if you want Opus-level synthesis on a specific run (e.g., monthly deep-clean wrapup).
>
> **v3.4 — Maintenance is mandatory + per-bullet caps.** Phase 3 split into 3.A (append, mechanical) and 3.B (maintenance, hard Bash-gated). Maintenance is no longer conditional on LLM judgment — Bash counts entries, and the count alone determines whether trim/promotion runs. Per-bullet length caps now hard-coded: HANDOFF bullets ≤ 3 sentences (~300 chars), session-log bullets ≤ 1 sentence (~150 chars), session-log entries hard-capped at 30 lines / 1.5 KB. Phase 6 final state assertion prints sizes with `⚠` flags so over-cap files are impossible to hide. Closes the silent-skip-of-maintenance defect that allowed one project's session-log to grow to 23 entries / 105 KB across 23 wrapups without a single trim.
>
> **v3.3 — Verify-before-read sync.** `/startup` now fetches origin and prompts to pull when local is behind, *before* reading HANDOFF.md / session-log.md / CLAUDE.md — so you're never silently reading a stale handoff after switching machines. New `--auto-pull` / `--no-pull` flag overrides for autonomous loops and offline work. Phase 0 streamlined into a single decision table; cross-machine handoff detection fires on hostname mismatch regardless of whether this turn brought in the commits.
>
> **v3.2 — Slim wrapup.** Recency-bounded conversation tagging, mechanical session-log derivation from HANDOFF.md, and auto-skipped CLAUDE.md prunes when nothing has changed since the last wrapup. New `--quick` mode for short sessions. Cuts wrapup wall time substantially without losing fidelity.
>
> **v3.1 — Cross-machine continuity.** `/wrapup` auto-commits session files and prompts to push; `/startup` runs `git pull --ff-only` and detects cross-machine handoffs via hostname in the commit message. `/init` ensures session files aren't gitignored. `--push` / `--no-push` overrides for autonomous loops.
>
> **v3.0 — Lifecycle expansion.** Adds `/init` for one-time project bootstrap, plus two Python scripts (`detect-stack.py`, `detect-resources.py`) that make stack and resource detection deterministic. Absorbs the retired rad-stack-guide.

## The three-phase lifecycle

| Phase | When | Skill | What it does |
|---|---|---|---|
| **Init** | Once, when you start work in a project | `/init` | Detects stack deterministically (Python scripts, no LLM guessing), finds MCPs and CLIs in the project, scaffolds CLAUDE.md or proposes additions, ensures session files aren't gitignored so cross-machine sync works, recommends which rad-* plugins fit your stack |
| **Startup** | Every session | `/startup` | **Fetches origin and prompts to pull when behind** (3.3 — verifies sync before reading any handoff file; lists incoming commits first; `--auto-pull` skips prompt, `--no-pull` skips sync entirely), reads HANDOFF.md + session log + CLAUDE.md, runs Resource Discovery, presents a concise briefing including a cross-machine note if the most recent session commit was made on a different host |
| **Wrapup** | Every session | `/wrapup` | Writes structured HANDOFF.md with "what NOT to do" field, derives a compressed session-log entry from it, prunes CLAUDE.md only if it's actually changed since the last wrapup (with diff confirmation; Resources protected), **auto-commits session files and prompts to push** |

Plus `/add-resource` (any time, registers a new tool) and a PreCompact hook (auto-fires on context compaction so state isn't silently lost).

## What's in the plugin

| Component | Triggers | What it does |
|---|---|---|
| **`/init`** *(new in 3.0)* | start of project work, "set up rad-session here", "bootstrap" | One-time project bootstrap. Runs the two detection scripts, scaffolds CLAUDE.md with detected stack/resources, recommends rad-* plugins for your stack, sets up `.claude/session-log.md`. Safe to re-run (merges, doesn't overwrite). |
| **`/startup`** | start of session, "/startup", "where did we leave off" | **Verifies sync with origin first** (3.3 — prompts to pull when behind, before reading any handoff files), then reads HANDOFF.md + session log, detects git state, runs Phase 2.5 Resource Discovery (uses `detect-resources.py` deterministically when Python is available), presents briefing |
| **`/wrapup`** | end of session, "/wrapup", "wrap up" | Writes HANDOFF.md with "What NOT to do" field, appends session log (20-entry cap), prunes CLAUDE.md with diff confirmation (**Resources section protected**), auto-commits session files and prompts to push |
| **`/add-resource`** | "add this MCP", "remember the supabase CLI", "register this resource" | Appends an MCP/CLI/script/note to CLAUDE.md's `## Resources` section so `/startup` picks it up next session |

### Slash commands and flags reference

Every flag accepted by every skill, plus all natural-language triggers:

| Skill | Triggers (any of) | Flags |
|---|---|---|
| **`/init`** | "/init", "set up rad-session", "bootstrap this project", "initialize rad-session", "start a new project here" | `--non-interactive` skip all prompts and accept proposed scaffold · `--dry-run` preview detection + scaffold without writing anything |
| **`/startup`** | "/startup", "start session", "orient me", "where did we leave off", "catch me up", "what's the state", "session briefing" | `--auto-pull` skip the Phase 0 prompt and fast-forward silently when behind · `--no-pull` skip the sync check entirely and read local files as-is (briefing leads with stale warning if origin is ahead) |
| **`/wrapup`** | "/wrapup", "wrap up", "end of session", "session handoff", "save session state", "wrap this up", "close out this session" | `--push` skip the Phase 6 push prompt and push the session commit immediately · `--no-push` skip push entirely, commit locally only · `--quick` 15-turn tagging window, skip CLAUDE.md prune, skip recurring-trap promotion |
| **`/add-resource`** | "add this MCP", "remember the supabase CLI", "register this resource", "track this tool" | (none) |

Combine flags freely — e.g. `/wrapup --push --quick` (autonomous-loop wrapup), `/startup --no-pull` (offline work), `/startup --auto-pull` (always-sync mode without prompting).

**Default behavior with no flags:**
- `/startup` prompts to pull when behind, lists incoming commits before asking.
- `/wrapup` always commits session files locally; prompts before pushing.
- `/init` walks through detection + scaffold proposal interactively.

Plus one hook:

| Hook | Event | What it does |
|---|---|---|
| `precompact` | `PreCompact` | Fires automatically when context compaction begins. Injects a systemMessage telling Claude to run `/wrapup` before the compacted context loses session state. |

Plus two Python scripts (new in 3.0):

| Script | What it does |
|---|---|
| `scripts/detect-stack.py` | Scans project for languages, frameworks (via package.json deps + marker files), package manager, deploy targets, infrastructure, toolchain. Returns structured JSON. |
| `scripts/detect-resources.py` | Scans for MCP servers (`.mcp.json` + `.claude/settings.json`), stack CLIs (marker-file inference + optional PATH check), parses CLAUDE.md `## Resources` section, computes drift. Returns structured JSON. |

Both are pure stdlib Python 3.8+. No `pip install` required. Used by `/init` and optionally by `/startup` Phase 2.5.

## Files the plugin maintains

| File | Purpose | Who writes it | Tracked by git |
|---|---|---|---|
| `CLAUDE.md` | Permanent project rules + **`## Resources` section** (MCPs, CLIs, scripts, notes) | `/init` (scaffold), `/add-resource` (additions); pruned by `/wrapup` (Resources protected) | Yes |
| `HANDOFF.md` | Current session state — status, decisions, what NOT to do, open work, insights | `/wrapup` (overwrites each session) | Yes — synced cross-machine |
| `.claude/session-log.md` | Session history, newest first, capped at 20 entries | `/init` (creates header), `/wrapup` (prepends one entry per session) | Yes — synced cross-machine |

## Cross-machine continuity (PC ↔ GitHub ↔ Laptop)

If your project has a git remote, rad-session keeps `HANDOFF.md` and `.claude/session-log.md` in sync across machines automatically:

| Phase | What it does |
|---|---|
| `/init` Step 7.5 | Detects if `.claude/` is gitignored; proposes `!.claude/session-log.md` exception so the log gets committed. |
| `/wrapup` Phase 6 | Auto-commits session files (silent, never `git add -A`). Prompts: `Push session files to origin? (y/N)`. Commit message: `session: YYYY-MM-DD on <hostname> — <status>`. |
| `/startup` Phase 0 *(streamlined in 3.3)* | Fetches origin and compares ahead/behind. **If behind, prompts to pull before reading any handoff file** — listing the incoming commits first so you see what's about to land. On approval, fast-forwards. On decline, briefing leads with `⚠ Reading stale local state`. If the most recent session commit was made on a different host, briefing also leads with `Continuing from <other-host> — last session committed there`. |

**Auto-commit, prompted push (wrapup) — fetch + prompted pull (startup).** Local commits are cheap so they always happen on wrapup. Pushing is a deliberate "I'm about to switch machines" decision. Pulling is a deliberate "I want to read the latest state" decision — `/startup` prompts on every behind state so you're never silently reading a stale handoff. Stack multiple unpushed session commits on the same machine; push when you're ready to hand off.

**Flag overrides:**
- `/startup --auto-pull` — skip the prompt, fast-forward silently when behind. For autonomous loops.
- `/startup --no-pull` — skip the sync check entirely. For offline work.
- `/wrapup --push` — skip the prompt, push immediately. For autonomous loops.
- `/wrapup --no-push` — skip the prompt, commit locally only.

**Safety:** wrapup never force-pushes, never touches non-session files, and bails cleanly on diverged history. Startup never merges, never rebases, never discards local work — it only attempts a fast-forward pull and warns if it can't (dirty tree or diverged → block warning surfaces in the briefing, never an auto-resolve).

## What `/init` does (the headline of 3.0)

**Run once per project.** Bootstraps everything `/startup` and `/wrapup` need.

1. **Verify Python availability** — falls back to LLM-based detection if missing, with a warning that the bootstrap will be less reliable.
2. **Run `detect-stack.py`** — scans languages, frameworks, package manager, scripts, deploy targets, infrastructure. Replaces "ask the LLM to read package.json."
3. **Run `detect-resources.py --check-clis`** — scans `.mcp.json`, `.claude/settings.json`, marker files. Verifies CLIs in PATH. **Flags CLIs the project assumes but aren't installed.**
4. **Synthesize a stack summary** — scannable report of what's there.
5. **Recommend rad-* plugins** — based on detected stack, only currently-shipping plugins (no references to retired ones). Tells you what each adds, doesn't auto-install.
6. **Propose CLAUDE.md scaffold** (greenfield) or **propose additions** (existing). Shows diff. Waits for confirmation.
7. **Create `.claude/session-log.md`** with header line if missing.
8. **Final report** — what was created/modified, what to do next.

Safe to re-run: merges, never overwrites. Has `--non-interactive` and `--dry-run` flags for autonomous setup runs.

### Why `/init` exists

Stack detection used to live in two places:
- `rad-stack-guide` had a `/detect-stack` skill (ran once per project)
- `rad-session`'s `/startup` Phase 2.5 (ran every session)

The duplication was awkward, and rad-stack-guide's other value (orchestrating specialist reviewers) collapsed when the framework reviewers were archived. **3.0 absorbs the per-project setup into rad-session's lifecycle.** rad-stack-guide is retired.

If you previously used rad-stack-guide's `/detect-stack`, your existing CLAUDE.md content stays intact — it was just markdown. Run `/init` once to re-establish the `## Resources` section in the new format.

## Phase 2.5 Resource Discovery in `/startup` (refined in 3.0)

`/startup` runs a read-only resource-detection pass every session. **In 3.0 it prefers `detect-resources.py` when Python is available** — same data, deterministic. The LLM-based marker scanning remains as fallback.

Detection covers:

- **`.mcp.json`** and `.claude/settings.json` → MCP servers available to the project
- **Stack marker files** → implied CLIs (full table in `skills/startup/SKILL.md` Phase 2.5.2)
- **`package.json`** → `packageManager` field + top scripts (`dev`, `build`, `test`, `typecheck`, `lint`, ...)
- **`.env.example`** → variable **names** only (never values)
- **CLAUDE.md `## Resources` section** → documented source of truth, reconciled against what's actually detected

### Example briefing output

```
Project: my-app
Type: Coding (Next.js + Supabase)
Branch: main (up to date)
Last session: 2026-04-25 — Auth flow complete, billing next

Where we left off:
  - Stripe checkout endpoint wired, webhook handler still TODO
  - Supabase RLS policies applied for users table

Watch out for:
  - Do not mock the Stripe webhook in integration tests — signature verify must hit real code path

Resources available:
  MCPs: supabase, stripe, coolify
  Stack CLIs: supabase, gh, docker
  Scripts (pnpm): dev, build, test, typecheck, lint
  Env template: DATABASE_URL, STRIPE_SECRET_KEY, SUPABASE_ANON_KEY (.env.example)

Ready to continue. What would you like to work on?
```

## Disciplined `/wrapup`

`/wrapup` writes a **structured HANDOFF.md** with sections most handoff tools skip:

- **What NOT to do** — failed approaches in the canonical `TRIED: … FAILED BECAUSE: … CORRECT APPROACH: …` form. Prefix tokens are load-bearing — `/startup` extracts them literally.
- **Key Decisions** — the *why* behind architecture/approach choices, not just the what.
- **Open Work** — state-of-play as descriptions, never as instructions ("EBirdProvider started, API auth not wired" — not "Next, wire up the eBird API auth").
- **Key Insights** — API quirks, environment gotchas, architectural constraints not in CLAUDE.md.

Then it derives a compressed session-log entry **mechanically from the HANDOFF.md it just wrote** (no second LLM synthesis pass — Status verbatim, Changes/Decisions/Traps compressed from the corresponding sections), prunes CLAUDE.md with **diff confirmation** (you see what's about to be removed and can say "undo item X" before anything is saved), **protecting the `## Resources` section** from removal, and finally commits the session files locally. The push is prompted, not automatic — local commits are cheap, push is the deliberate "I'm switching machines" decision.

**Slim wrapup mechanics (3.2 + 3.5):** conversation tagging is bounded by recency (window starts at the most recent `/wrapup`, `/checkpoint`, PreCompact systemMessage, or `/startup` briefing; 40-turn fallback cap). Phase 4 prune auto-skips when CLAUDE.md hasn't changed since the last wrapup. `--quick` flag drops the recency cap to 15 turns, skips the prune unconditionally, skips recurring-trap promotion. **3.5 adds a low-activity auto-quick short-circuit:** when a signal-bounded window contains fewer than 10 substantive turns, `/wrapup` automatically applies `--quick` semantics — no flag needed. Long sessions don't make wrapup proportionally slower; short sessions wrap up in seconds.

**CLAUDE.md prune safety (2.x):** the prune always shows a diff, always protects `## Resources` / `## MCP` / `## Tools`, and an auto-proceed threshold (≤3 removals, no rules/architecture sections, no "must/never/always" markers) lets small low-risk prunes skip the gate so autonomous and loop-mode sessions don't hang.

Nothing else in the Claude Code ecosystem actively shrinks CLAUDE.md.

## PreCompact safety net

When Claude Code's context compaction fires, the `PreCompact` hook injects a systemMessage instructing Claude to run `/wrapup` before anything else. The injected message enumerates the six capture targets explicitly (decisions, failed approaches, user corrections, modified files, open work, insights) so even smaller models with thin post-compaction context can reconstruct usable state.

No config required; the hook ships with the plugin.

## Quick Start

```bash
/plugin marketplace update rad-claude-skills
/plugin install rad-session@rad-claude-skills
```

**First time in a project:**
```
/init                   # interactive bootstrap
/init --non-interactive # accept proposed scaffold without prompting
/init --dry-run         # preview detection + scaffold without writing
```

**Start of every session:**
```
/startup                # fetches origin, prompts to pull if behind, then reads handoff
/startup --auto-pull    # fast-forward silently when behind (no prompt)
/startup --no-pull      # skip sync entirely, read local (with stale warning)
```

**Register resources as you discover them:**
```
remember we have the coolify MCP available for this project
```

**End of every session:**
```
/wrapup            # auto-commits, prompts to push
/wrapup --push     # commit + push without prompting
/wrapup --no-push  # commit locally, don't push
/wrapup --quick    # short-session mode (15-turn tagging window, skip prune)
```

**Switching machines.** Run `/wrapup --push` on the PC. On the laptop, run `/startup` — it fetches origin, shows the incoming session commits, asks once to pull, then leads the briefing with `Continuing from <PC-hostname>`. No manual git work, no copy-paste, no risk of silently reading a stale handoff. Use `/startup --auto-pull` if you don't want to be prompted on every machine switch.

Works with coding projects (captures git state + stack resources) and non-coding projects (scans recently modified files; still surfaces documented resources). Cross-machine sync is git-only — projects without a remote get the local lifecycle and skip the sync phases silently.

## How this compares to alternatives

| | **rad-session 3.5** | claude-plugins-official/remember | claude-mem | thepushkarp/handoff |
|---|---|---|---|---|
| Project bootstrap (`/init`) | ✅ **unique** | ❌ | ❌ | ❌ |
| Resource discovery (MCPs/CLIs/stack) | ✅ **unique** | ❌ | ❌ | ❌ |
| Active CLAUDE.md prune w/ diff | ✅ **unique** | compression | ❌ | ❌ |
| Cross-machine sync via git (auto-commit + prompted push) | ✅ **unique** (3.1) | ❌ | ❌ | ❌ |
| Deterministic stack detection (Python scripts) | ✅ | ❌ | ❌ | ❌ |
| "What NOT to do" field | ✅ | ❌ | ❌ | partial |
| PreCompact safety net | ✅ | ✅ | ✅ | ✅ |
| Zero dependencies for skills (Python optional for scripts) | ✅ | ❌ (Haiku) | ❌ (Chroma) | ✅ |
| Setup cost | plugin install + `/init` | plugin install | plugin install | plugin install |

**When to use rad-session:** you want structured workflow lifecycle for a project — bootstrap once, orient each session, capture each session.

## What's NOT in scope

- **Does not install rad-* plugins for you** — `/init` recommends; you decide.
- **Does not configure MCP servers** — detects what's already there. Adding new MCPs is a separate concern (`/configure-mcp` in rad-agentic-company-builder, or just edit `.mcp.json`).
- **Does not run tests, builds, or any side-effect commands** beyond two read-only Python scripts and `mkdir .claude/`.
- **Does not exec stack binaries** without `--check-clis` opt-in.
- **Does not read `.env`** — only `.env.example`, and only variable names.
- **Does not orchestrate code reviews** — that role belonged to retired rad-stack-guide. Use the specialist reviewers directly (rad-code-review for general, rad-supabase / rad-coolify-orchestrator / rad-a11y / rad-chrome-extension for their domains).

## Version

**3.5.1** — **Phase 5 removed.** The `/wrapup` "surface insights" phase has been deleted along with all references to it. Empirical evidence: across 12+ wrapups in one project, zero memory files were ever persisted from surfaced "Worth remembering" bullets — the surfacing was happening but nothing downstream was picking it up. The phase is gone in 3.5.1. The final state assertion no longer prints a "Worth remembering" line.

**3.5.0** — **Speed: Haiku-pinned skills + cached resource scan + low-activity auto-quick.** Cuts `/startup` and `/wrapup` wall-clock time by roughly 4–5× by routing routine session work to a faster, cheaper model and short-circuiting work that doesn't need to run.
- **Per-skill model pinning.** `/startup` and `/wrapup` SKILL.md frontmatter now pin to Haiku 4.5. The override applies for that turn only — the session model resumes automatically on the next prompt. The skills' explicit "tag-and-summarize" patterns and literal templates were already cross-model calibrated (Opus 4.7 / Sonnet 4.6 / Haiku 4.5), so output format and structure are unchanged. Override with `/model opus` before either skill if you want Opus-level synthesis on a specific run (e.g., a monthly deep-clean wrapup).
- **mtime-keyed cache for resource detection.** `/startup` Phase 2.5 now invokes `detect-resources.py --json --cache --include-env-names`, which writes results to `.claude/cache/resources.json` keyed by the mtimes of every input file (`.mcp.json`, `.claude/settings.json`, `CLAUDE.md`, `.env.example`, every CLI marker file, the script itself). Cache hits skip scanning entirely. Any input edit invalidates automatically — no manual cache busting. Cache is disabled when `--check-clis` is passed (PATH lookups must be live), so `/init` is unaffected.
- **Low-activity auto-quick in `/wrapup` Phase 1.3.** When the conversation window is signal-bounded (most recent `/wrapup`, `/checkpoint`, PreCompact, or `/startup` briefing) AND contains fewer than 10 substantive turns, `--quick` semantics now apply automatically: 15-turn cap, skip Phase 4 prune, skip recurring-trap promotion. Reduces wall time on short "I sat down for an hour" sessions without requiring the user to remember the flag.
- **Why Haiku is the right choice here.** Both skills do mechanical labeling (DECISION / FAIL / CORRECTION / INSIGHT / OPEN) and templated formatting (HANDOFF.md, session-log entries, briefings). The cross-model parity disclaimer in the skill bodies has been there since 2.x — 3.5 just makes it the default routing rather than something the user has to opt into via `/model`.

**3.4.0** — **Maintenance is mandatory + per-bullet caps.** Closes a structural defect: across one project, the session-log grew from 13 → 23 entries over 23 wrapups without a single trim firing, because Phase 3 maintenance was buried as a conditional sub-section that LLMs consistently skipped.
- `/wrapup` Phase 3 split into **3.A — Append (mechanical)** and **3.B — Maintain (hard gate, MANDATORY)**. 3.B is no longer conditional. It always runs. Bash (`grep -c "^## [0-9]"`) counts entries deterministically; the count alone determines whether trim/promotion fires.
- Per-bullet length caps now hard-coded in both the skill and the reference docs:
  - **HANDOFF.md:** bullets ≤ 3 sentences (~300 chars), total ≤ 100 lines / 8 KB.
  - **session-log:** bullets ≤ 1 sentence (~150 chars), entries hard-capped at 30 lines / 1.5 KB.
- Phase 6 final state assertion prints HANDOFF + session-log sizes with `⚠` flags when over cap. Silent skip is structurally impossible after 3.4 — every wrapup ends with the size truth visible.
- Maintenance notification (`Session log: trimmed N` / `no maintenance needed`) is now mandatory output regardless of whether trim ran. Was previously only emitted when trim fired.

**3.3.0** — **Verify-before-read sync on `/startup`.** Closes a contract gap from 3.1: previous behavior pulled silently on success but soft-failed to local state on any obstacle, which meant you could read a stale handoff without realizing it.
- `/startup` Phase 0 streamlined into a single decision table indexed on `(behind count, FF possible, flag)`. Replaces ~50 lines of conditional prose covering merge/rebase/cherry-pick/dirty/diverged with one scannable matrix.
- `/startup` now **fetches first, then prompts to pull when behind**, listing the incoming commits via `git log HEAD..@{u} --oneline` so you see what's about to land before approving. The prompt defaults to Y when fast-forward is possible (sync is the safe choice).
- New flag overrides: `--auto-pull` (skip prompt, fast-forward silently) and `--no-pull` (skip sync entirely, read local with stale warning). Symmetric to wrapup's `--push` / `--no-push`.
- Cross-machine handoff detection now fires on hostname mismatch in the most recent session commit *regardless* of whether this turn's pull brought it in. Fixes a bug where a previously-pulled cross-machine commit wouldn't surface the "Continuing from <other-host>" note.
- Stale and block warnings are explicit briefing-top callouts, not silent continues.
- README adds a comprehensive flags reference table (every skill, every flag, every trigger phrase).

**3.2.0** — **Slim wrapup.** Cuts wrapup wall time substantially without losing fidelity.
- `/wrapup` Phase 1.3 conversation tagging is now bounded by recency: the window starts at the most recent `/wrapup`, `/checkpoint`, PreCompact systemMessage, or `/startup` briefing, with a 40-turn fallback cap. Long sessions no longer scale wrapup cost linearly.
- `/wrapup` Phase 3 (session log) now derives entries mechanically from the HANDOFF.md just written — no second LLM synthesis pass. ~30–40% time savings on this phase.
- `/wrapup` Phase 4 (CLAUDE.md prune) auto-skips when CLAUDE.md hasn't been changed since the last wrapup (detected via `git log` + `git diff`). Most wrapups now skip the slowest non-synthesis phase entirely.
- New `--quick` flag: bounds Phase 1.3 to the last 15 turns, skips Phase 4 unconditionally, skips recurring-trap promotion. For "save state and go" wrapups during active work.

**3.1.0** — **Cross-machine continuity (PC ↔ GitHub ↔ Laptop).**
- New `/startup` Phase 0: `git pull --ff-only` before reading session files. Detects cross-machine handoff via hostname in the session commit message and surfaces it in the briefing.
- New `/wrapup` Phase 6: auto-commits `HANDOFF.md`, `.claude/session-log.md`, and `CLAUDE.md` (only if Phase 4 modified it). Prompts for push by default; `--push` and `--no-push` flag overrides for autonomous loops. Stages only session files — never `git add -A`. Bails cleanly on diverged history; never force-pushes.
- New `/init` Step 7.5: detects `.claude/` gitignore rules and proposes a `!.claude/session-log.md` exception so the log can travel.
- Commit message format: `session: YYYY-MM-DD on <hostname> — <status>` — load-bearing for Phase 0's cross-machine detection.

**3.0.0** — **Lifecycle expansion + rad-stack-guide consolidation.**
- New `/init` skill — one-time project bootstrap. Detects stack deterministically, scaffolds CLAUDE.md, recommends rad-* plugins for the detected stack.
- New `scripts/detect-stack.py` — pure-Python stack scanner. Languages, frameworks (via package.json deps + marker files), package manager, scripts, deploy targets, infrastructure.
- New `scripts/detect-resources.py` — pure-Python MCP + CLI scanner with PATH verification (`--check-clis`) and drift detection vs CLAUDE.md `## Resources`.
- `/startup` Phase 2.5 now prefers `detect-resources.py` when Python is available; LLM-based marker scanning remains as fallback.
- `rad-stack-guide` retired. Its stack-detection value is now in `/init`. Its review-orchestration value collapsed when the framework reviewers were archived; rad-code-review handles its multi-pass internally.
- README repositioned around the three-phase lifecycle (init → startup → wrapup).

**2.2.0** — Optimized for Opus 4.7. Parallel-batched `/startup` reads, explicit conversation-synthesis scan in `/wrapup`, auto-proceed threshold for low-risk CLAUDE.md prunes, stale-handoff auto-refresh from git log, canonical `TRIED / FAILED BECAUSE / CORRECT APPROACH` trap format, expanded stack marker table, PreCompact hook payload that enumerates capture targets explicitly.

**2.1.0** — PreCompact hook for silent-context-loss prevention; repositioned pitch around Resource Discovery and wrapup discipline.

**2.0.0** — Added `/add-resource` skill, `/startup` Phase 2.5 Resource Discovery, `/wrapup` prune protection for the Resources section.

**1.0.0** — Initial release: `/wrapup` and `/startup` skills.

## License
Apache-2.0

---
name: startup
description: >
  Start-of-session skill that reads HANDOFF.md, session log, and CLAUDE.md to
  orient a new session with full context from prior work. Read-only — never
  modifies files. Trigger when the user says "/startup", "start session",
  "orient me", "what's the state", "session briefing", "where did we leave off",
  "catch me up", "what was I working on".
model: haiku
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Session Startup

Orient a new session by reading the handoff state left by `/wrapup`, detecting the project type, discovering available resources, and presenting a concise briefing.

**This skill is read-only. It never creates, modifies, or deletes files.**

**Model selection (3.5).** The frontmatter pins this skill to **Haiku 4.5** for the duration of the startup turn. The session model resumes automatically on the next user prompt. Startup is read-heavy + templated briefing synthesis — Haiku handles it well at a fraction of the wall-clock cost. Resource discovery is delegated to `detect-resources.py` with caching (Phase 2.5.0), so the model rarely does any scanning work itself.

**Cross-model note.** The same logic produces comparable output on Opus 4.7, Sonnet 4.6, and Haiku 4.5. Output briefing format is identical regardless of model. Override with `/model opus` before `/startup` only if you want Opus-level synthesis on a stale-handoff auto-refresh (Phase 1.4).

## Mode flags

- `--auto-pull` — Skip the Phase 0 prompt; fast-forward silently when behind. For autonomous loops or when you've already decided to always sync.
- `--no-pull` — Skip the sync check entirely; read local files as-is. Briefing leads with a stale warning if origin has unpulled commits. For offline work.
- Neither → prompt at Phase 0 when behind (default).

---

## Execution: parallel-first

Phase 0 (sync from origin) **must run first** because it can update the very files that the rest of the skill reads, and may need to wait for a user response to the pull prompt. After Phase 0 resolves (pulled, declined, skipped, or aborted), the work inside Phases 1, 2, and 2.5 has **no inter-phase dependencies** — every read and every shell command can be issued as a single parallel batch. Opus 4.7 and Sonnet 4.6 should do exactly that. The only sequential step is Phase 3 (briefing synthesis), which depends on the results.

**Batch to issue at the start of the skill:**

- Read `CLAUDE.md`, `HANDOFF.md`, `.claude/session-log.md` (Phase 1.1–1.3)
- Read `.mcp.json`, `.claude/settings.json`, `.env.example`, `package.json`, `pyproject.toml` (if any exist — Phase 2.5)
- Glob for stack marker files (Phase 2.5.2)
- Bash: `git status --short`, `git log --oneline -5`, `git rev-parse --abbrev-ref HEAD`, `git rev-list --left-right --count HEAD...@{upstream}` — run as one combined command so the shell spawn cost is paid once (Phase 2.2)

If a file is missing, the corresponding Read call will error silently — that's fine, skip its content in the briefing. Do not re-attempt serial reads after a parallel batch.

---

## Phase 0: Sync from origin

A handoff is only useful if you're reading the latest state. Phase 0 confirms local matches origin **before** any HANDOFF.md / session-log.md / CLAUDE.md read fires. The owner approves push during `/wrapup`; startup verifies freshness on the way in.

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

When prompting in the default behind-FF-possible case, list the incoming commits first via `git log HEAD..@{u} --oneline -10` so the user sees what's about to land. Default the prompt to Y (sync is the safe choice when FF is possible).

### 0.4 Cross-machine handoff signal

Fires whenever the most recent session commit was made on another machine — independent of whether this turn pulled. This is what surfaces "Continuing from <PC>" on the laptop even if the pull came in earlier.

```bash
git log -1 --format='%s' -- HANDOFF.md .claude/session-log.md 2>/dev/null
```

Parse for the canonical session-commit format `session: YYYY-MM-DD on <hostname> — <status>` (written by `/wrapup` Phase 6.3).

- Hostname differs from `$HOSTNAME` / `$COMPUTERNAME` / `hostname` → stash this Phase 3 note:
  ```
  Continuing from <other-host> — last session committed there.
  ```
- Hostname matches → no note (continuing on the same machine).
- Commit doesn't match the canonical session format (manual commit) → skip silently.

The cross-machine note appears at the top of the Phase 3 briefing, above the Project line and below any stale/block warning.

---

## Phase 1: Discover Project State

Read handoff files. All are optional — skip silently if missing.

### 1.1 Read CLAUDE.md + resolve imports

Read `CLAUDE.md` at the project root. Note:
- Project name and type
- Tech stack
- Key conventions and rules

**Import resolution.** If CLAUDE.md contains lines matching `@<path>` (e.g., `@docs/architecture.md`, `@.claude/rules.md`), treat each as an imported file. Resolve each path relative to the CLAUDE.md location and Read the file in the same parallel batch. Include the imported content as additional project context in the briefing when relevant. Missing import targets are reported silently (note in the briefing under a subtle "⚠ missing import: <path>" line — do not error out).

Do not follow imports recursively beyond one level — imports of imports are out of scope for `/startup`, and following them risks pulling in unbounded content.

### 1.2 Read HANDOFF.md

Read `HANDOFF.md` at the project root. This is the primary handoff from the last session. Extract:
- Status line
- Where work was left off
- Key decisions from last session
- "What NOT To Do" traps (TRIED / FAILED BECAUSE / CORRECT APPROACH — see `references/handoff-template.md`)
- Open work items
- Modified files
- Key insights

### 1.3 Read Session Log

Read `.claude/session-log.md` if it exists. Focus on the most recent 3–5 entries for:
- Patterns across sessions (recurring traps, ongoing work threads)
- Context that the latest HANDOFF.md alone might not capture
- How long the current work has been in progress

### 1.4 Assess Handoff Freshness — with auto-refresh for stale handoffs

Check the date in HANDOFF.md against today's date:

- **Same day or yesterday:** Handoff is fresh — trust it fully.
- **2–7 days old:** Handoff is recent — trust it but note the gap.
- **7+ days old:** Handoff is stale. **Before presenting the briefing**, run an auto-refresh:
  1. `git log --oneline --since="<handoff date>" 2>/dev/null`
  2. `git diff --stat <commit-at-handoff-date>..HEAD 2>/dev/null` if resolvable, else skip
  3. Synthesize a one-paragraph "Changes since last session" block summarizing commits that weren't authored during a Claude Code session (i.e., commits not referenced in HANDOFF.md's "Modified Files" list).
  4. Include the synthesized block in the briefing under a `Changes since last session (outside Claude Code):` heading, and lead the briefing with a one-line staleness note: `⚠ Handoff is N days old — auto-refreshed from git log.`
- **No HANDOFF.md:** Note this is either a brand-new project or one that hasn't used `/wrapup` yet — fall through to the Minimal Briefing.

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

### 2.3 Detect Changes Since Last Session

If HANDOFF.md has a date and no stale-refresh was triggered in Phase 1.4, spot-check for commits between the handoff date and now that aren't referenced in the handoff's Modified Files list. If found, flag them in the briefing as "changes made outside the last session."

---

## Phase 2.5: Resource Discovery

Detect project-specific resources so Claude doesn't need to be reminded every session. All steps are read-only and issued in the parallel batch from "Execution." Skip silently when nothing is found.

### 2.5.0 Preferred path: deterministic script (mtime-cached in 3.5)

If Python is available, prefer the deterministic scanner over LLM-based marker scanning. Always pass `--cache` so cache-hit startups skip re-scanning entirely:

```bash
python3 ${plugin_root}/scripts/detect-resources.py "$PWD" --json --cache --include-env-names
```

The `--cache` flag (3.5) writes results to `.claude/cache/resources.json`, keyed by the mtimes of every input file (`.mcp.json`, `.claude/settings.json`, `CLAUDE.md`, `.env.example`, all marker files in the CLI table, and the script itself). On cache hit, scanning is skipped and the cached data is returned in milliseconds. Any input file edit invalidates the cache automatically — no manual cache busting required. The output adds a `"cache_status": "hit" | "miss"` field; surface it under the briefing's resources block only if status is `miss` (e.g., `Resources: scanned fresh`); on `hit`, stay silent — that's the common path and silence is correct.

The script returns the same data structure as steps 2.5.1–2.5.6 below — MCPs, stack CLIs, documented-resources reconciliation, drift detection. Use the JSON output verbatim. The LLM-based steps below remain as fallback when Python is not available.

### 2.5.1 MCP Servers

Read `.mcp.json` at the project root if it exists. Parse the JSON and extract the keys under `mcpServers`.

```json
{ "mcpServers": { "supabase": {...}, "coolify": {...} } }
```
→ `MCPs: supabase, coolify`

Also read `.claude/settings.json` and collect names under `enabledMcpjsonServers` or plugin-scoped MCP entries. Merge without duplication. Malformed JSON → skip silently.

### 2.5.2 Stack CLIs (inferred from marker files)

Glob the project root for these markers. File-presence inference only — **never exec any binary**.

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

- Read `packageManager` field (e.g., `pnpm@9.0.0`). If absent, infer from lockfile: `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `bun.lockb` → bun, else npm.
- Extract top 5–8 keys from `scripts`. Prefer in this order if present: `dev`, `build`, `test`, `typecheck`, `lint`, `start`, `check`, `format`.

Output example: `Scripts (pnpm): dev, build, test, typecheck, lint`

For Python: if `pyproject.toml` has a `[tool.poetry.scripts]` or `[project.scripts]` table, list up to 5 entries as `Scripts (poetry): ...`. For other non-Node stacks, skip unless trivially obvious.

### 2.5.4 Environment Template

If `.env.example` exists, read it and extract **variable names only** (everything before `=` on each non-comment line). **Never read `.env` or any file that may contain real values.**

Output: `Env template: SUPABASE_URL, STRIPE_SECRET_KEY, ... (.env.example)`

### 2.5.5 CLAUDE.md Resources Section

If CLAUDE.md contains a heading matching any of these (case-insensitive), extract its contents verbatim:

- `## Resources`
- `## MCP` / `## MCPs`
- `## Tools` / `## CLI Tools`

Treat the extracted contents as the **documented** source of truth for this project.

### 2.5.6 Reconciliation

Compare documented (2.5.5) against detected (2.5.1–2.5.4):

- **Documented + detected** → show normally in "Resources available."
- **Documented but not detected** → show with `⚠ documented but not found` — possible drift (config moved, tool uninstalled).
- **Detected but not documented** → show under a secondary line `Also detected (not in CLAUDE.md):` — signals the user may want to run `/add-resource` to register them.

If no CLAUDE.md Resources section exists, treat all detected items as primary with no drift warnings.

---

## Phase 3: Orient and Brief

Present a concise, scannable session briefing. Adapt the format based on what's available. Full example briefings (full, minimal, non-coding) are in `references/briefing-examples.md` — follow those structures verbatim.

### Briefing selection

| Condition | Template |
|-----------|----------|
| HANDOFF.md exists + coding project | Full Briefing (see `references/briefing-examples.md`) |
| No HANDOFF.md | Minimal Briefing |
| No build-system markers | Non-Coding Briefing |

### Presentation rules

- Keep the briefing **under 35 lines** — this is a quick orientation, not a report.
- Use the **exact wording from HANDOFF.md** for traps and open work — don't paraphrase. The original wording was chosen carefully and paraphrasing often loses the load-bearing detail.
- End with `Ready to continue. What would you like to work on?` to hand control back.
- If the handoff is **stale (7+ days)**, lead with the staleness + auto-refresh note before the briefing body.
- **Omit** the "Resources available" block entirely if every category (MCPs, CLIs, scripts, env) is empty — don't show an empty header.
- Cap the Resources block at **6 lines**; truncate with `...` if a category has more than 8 items.
- If imports were resolved in Phase 1.1 and surfaced non-trivial content (e.g., architecture notes not in CLAUDE.md body), add a single `Imports: <file1>, <file2>` line under the Resources block.

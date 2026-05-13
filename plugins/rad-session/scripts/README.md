# rad-session scripts

Deterministic detection layer for the rad-session skills. Replaces "ask the LLM to eyeball package.json" with structured Python scans. Saves tokens and gives reproducible results.

All scripts are pure Python 3.8+ stdlib. No `pip install` required.

## detect-stack.py

Scans a project directory and identifies its tech stack from lockfiles, config files, package.json dependencies, and source-file extensions.

```bash
python3 scripts/detect-stack.py <project-root>            # default: cwd
python3 scripts/detect-stack.py <project-root> --json
python3 scripts/detect-stack.py <project-root> --plain    # text only, no decorations
```

**Detects:**
- Languages (typescript, python, go, rust, ruby, etc. — via marker files + file-extension scan)
- Frameworks (next, react, vue, svelte, fastify, prisma, drizzle, zod, vitest, playwright, etc.)
- Package manager (pnpm, npm, yarn, bun, poetry, pipenv, cargo, go) via lockfile + `packageManager` field
- Top scripts from package.json (prioritized: dev, build, test, typecheck, lint)
- Deploy targets (vercel, netlify, fly, cloudflare, supabase, coolify, etc.)
- Infrastructure (docker, github-actions, terraform, etc.)
- Toolchain (mise, asdf, nix, devbox)
- Whether it's a coding project at all

**JSON output structure** — see the script's docstring for the full schema. Used by `/init` and optionally by `/startup` Phase 2.5.

**Exit codes:** `0` always (this is a measurement, not pass/fail), `2` script error.

## detect-resources.py

Scans for MCP servers and stack CLIs. Compares detected against documented (in CLAUDE.md `## Resources`) and reports drift.

```bash
python3 scripts/detect-resources.py <project-root>
python3 scripts/detect-resources.py <project-root> --json
python3 scripts/detect-resources.py <project-root> --check-clis           # verify CLIs in PATH
python3 scripts/detect-resources.py <project-root> --include-env-names    # also list .env.example var names
```

**Detects:**
- MCP servers from `.mcp.json` and `.claude/settings.json` (`enabledMcpjsonServers`)
- Stack CLIs inferred from marker files (supabase/config.toml → supabase, fly.toml → flyctl, etc. — same table as `/startup` Phase 2.5.2)
- CLI presence in PATH (with `--check-clis`) — useful at `/init` time to flag CLIs the project assumes but aren't installed
- Documented resources from CLAUDE.md `## Resources` section
- `.env.example` variable names (with `--include-env-names`) — names only, never values

**Drift detection:**
- `documented_but_missing` — listed in CLAUDE.md but not detected (config moved, tool uninstalled?)
- `detected_but_undocumented` — detected but not in CLAUDE.md (signals user may want to `/add-resource`)

**Exit codes:** `0` always, `2` script error.

## migrate-to-v4.py (4.0)

One-shot migration helper for projects upgrading from rad-planner 2.x / rad-session 3.x to the RAD 8-doc standard (rad-planner 3.0 / rad-session 4.0). Read the script's module docstring for the full contract; this section is a quick tour.

```bash
python3 scripts/migrate-to-v4.py <project-root>                    # interactive
python3 scripts/migrate-to-v4.py <project-root> --dry-run          # show plan, write nothing
python3 scripts/migrate-to-v4.py <project-root> --non-interactive  # apply safe transforms only
python3 scripts/migrate-to-v4.py <project-root> --json             # trailing JSON summary; implies --non-interactive
```

**Transforms applied:**

| Detected | Action |
|---|---|
| `implementation_plan.md` (v2.x mega-doc) | Split into PRD.md / ARCHITECTURE.md / ASSUMPTIONS.md / DECISIONS.md / PLAN.md using v2.x section heading heuristics. The "Key Design Decisions" table from section 2 seeds DECISIONS.md as sequence-numbered entries (`0001`, `0002`, …). ASSUMPTIONS.md is a placeholder (v2.x had no source for it). |
| `HANDOFF.md` written by `/checkpoint` | Archived. Heuristic: presence of `**Active run:**`, `## To Resume`, `--resume <run-id>`, or `.planner/state/` markers. The next `/rad-session:wrapup` regenerates the wrapup-format HANDOFF.md from session state. |
| `EXECUTION-PROMPT.md` | Archived. Role replaced by `/rad-session:startup` briefing in 4.0. |
| `docs/ARCHITECTURE.md` | Moved to `ARCHITECTURE.md` at project root (4.0 puts all strategic docs at root). When `implementation_plan.md` is also being split, the script flags this as ambiguous (would produce two ARCHITECTURE.md sources) and archives the duplicate. |
| `CLAUDE.md` from `generate-project-config` | Preserved as-is. `CLAUDE-FRAGMENT.md` is generated alongside so the next `/rad-session:init` can merge strategic `@-imports`. Heuristic: WHY/WHAT/HOW heading pattern. |

**Safety:**
- Archive-before-edit: every transformed original is copied to `.rad-archive/<timestamp>/` before any in-place change.
- `manifest.json` in the archive records what was archived, where it came from, and what was applied.
- `.rad-archive/` is added to `.gitignore` by default (override with `--no-gitignore`).
- Dry-run mode (`--dry-run`) shows the full plan without writing.
- Re-running on an already-migrated project is a no-op (exits clean with "nothing to migrate").

**Ambiguous transformations** require explicit confirmation in interactive mode and are skipped (with a note in the manifest) in `--non-interactive`. The current ambiguous cases are:
- Splitting `implementation_plan.md` when v4 strategic files already exist at root (would overwrite).
- Archiving `docs/ARCHITECTURE.md` when `implementation_plan.md` will also produce one (avoid two sources of truth).

**Rollback:** manual. The archive directory contains every original with the suffix `.orig` (path separators flattened to `-`). Restore by copying back from the archive timestamp directory, then deleting the new v4 files.

**Exit codes:** `0` migration applied (or dry-run completed), `1` nothing to migrate / all declined, `2` script error.

## audit-plugin-bloat.py (3.6)

Recommends which Claude Code plugins to disable per-project for token efficiency. Plugins shipping MCP servers add their tool registry to every turn's context; plugins shipping skills add their skill descriptions to the listing. For projects that don't use a given plugin's stack, those tokens are pure noise.

```bash
python3 scripts/audit-plugin-bloat.py <project-root>
python3 scripts/audit-plugin-bloat.py <project-root> --json
python3 scripts/audit-plugin-bloat.py <project-root> --json --installed-plugins-stdin < <plugin-list>
```

**How it works:**
- Detects 10 stack signals (supabase, stripe, coolify, chrome_extension, frontend_web, python, anthropic_sdk, 1password_secrets, claude_plugin_repo, content_site)
- Applies a built-in catalog of plugin-relevance rules (in `PLUGIN_RULES` at top of script — edit there to add/adjust)
- Categories: `core` (always keep), `stack-conditional` (keep iff signals match), `productivity` (default disable), `meta-authoring` (keep only in plugin-authoring repos)
- With `--installed-plugins-stdin`: reads `name@marketplace` IDs from stdin (tolerant of `claude plugin list` raw output) and filters audit to only installed plugins

**Output (JSON):** `stack_signals` map, `audit` list (per-plugin recommendation + reason + ships_mcp flag), `summary` counts. See script docstring for the full schema.

**The script is OPINIONATED.** It encodes "this plugin is worth its token cost only when these signals are present." Edit `PLUGIN_RULES` in the script to override or extend.

**Exit codes:** `0` always, `2` script error.

## When the skills run these

| Skill | Script | When |
|---|---|---|
| `/init` | `detect-stack.py --json` + `detect-resources.py --check-clis --json` + `audit-plugin-bloat.py --json --installed-plugins-stdin` | Once on project bootstrap. Drives the CLAUDE.md scaffold, rad-* plugin recommendations, and per-project `enabledPlugins` disables in `.claude/settings.local.json`. Safe to re-run for refresh. |
| `/startup` | `detect-resources.py --json --cache` | Every session, Phase 2.5. Cache-keyed by input mtimes (3.5). |
| (user-invoked) | `migrate-to-v4.py` | One-shot during upgrade from 2.x/3.x. Not called from any skill — the user runs it manually before installing rad-planner 3.0 / rad-session 4.0. |

## What these scripts deliberately do NOT do

- **Do not exec stack binaries** by default. File-presence inference only. `--check-clis` does run `which` (or Windows `where`) to verify PATH availability — that's the only exception, and it's opt-in.
- **Do not read `.env`** (only `.env.example`, and only variable names).
- **Do not modify any files.**
- **Do not call out to the network.** No registry lookups, no version checks. (For framework version verification, that's the LLM's job with WebSearch / Context7.)
- **Do not prescribe** which rad-* plugins to install. They surface what's there; `/init` decides what to recommend based on the data.

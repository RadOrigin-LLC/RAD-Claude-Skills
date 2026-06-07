# rad-session fixtures

End-to-end fixtures for the rad-session 5.0 workflow. Each fixture is a minimal but realistic project state that exercises a different combination of agent_scope, mode, and operating-manual layout.

The fixtures complement rad-planner's `standard-project` and `intentionally-broken` (which focus on validator behavior). These fixtures focus on **dimension coverage** — the v5.0 workflow's branching behavior depends on `.rad/profile` and the operating-manual layout, and each fixture isolates one dimension.

Together with rad-planner's `standard-project` (claude_only / mentor / canonical layout), the four fixtures here cover:

| Fixture | agent_scope | mode | Operating manual | What it exercises |
|---|---|---|---|---|
| `codex-only-project` | `codex_only` | `mentor` | `AGENTS.md` | Codex-canonical path; `.codex/config.toml` scaffold; `/startup` reads AGENTS.md (not CLAUDE.md); `/wrapup` Phase 5 prunes AGENTS.md Operational sections |
| `dual-scope-project` | `claude_and_codex` | `dev` | `AGENTS.md` (canonical) + `CLAUDE.md` (`@AGENTS.md` shim) | Both files coexist; CLAUDE.md is a shim importing AGENTS.md; mode = dev (no teaching prompts) |
| `nonstandard-manual` | `claude_only` | `mentor` | `GUIDE.md` | Heuristic detection of non-canonical manual filename via "Agent Operating Manual" header; `.rad/profile` records the override |
| `dev-mode-project` | `claude_only` | `dev` | `CLAUDE.md` | Milestone-shipped state (all acceptance criteria checked) — `/wrapup` should propose archiving `current.md` to `planning/archive/`; dev mode means terse prompts |

## Using the fixtures

These are not Python unit tests — they're worked examples that the rad-session skills read in real `/startup` and `/wrapup` calls. To exercise a fixture:

```bash
# From a project directory whose state you want to mimic, copy the fixture in:
cp -r plugins/rad-session/fixtures/codex-only-project/* /path/to/scratch/project/

# Then run the skills:
cd /path/to/scratch/project
# In Claude Code:
/rad-session:startup       # should briefly read AGENTS.md + status.md + current.md
/rad-session:wrapup        # should propose updates per fixture state
```

## What "exercising" looks like per fixture

### codex-only-project (Tidemark — Python CLI for tide-station data)

**/startup expectations:**
- Reads `AGENTS.md` (canonical), `.rad/profile`, `docs/status.md`, `docs/planning/current.md`
- Does NOT look for `CLAUDE.md`
- Briefing references M2 anomaly-detection progress

**/wrapup expectations:**
- Phase 1 reads `AGENTS.md` for owned-sections detection (not CLAUDE.md)
- Phase 5 prune (if invoked) operates on `AGENTS.md` Operational sections only
- mentor mode: full teaching prompts for any candidate decisions

### dual-scope-project (Ledgerline — TS accounting web app)

**/startup expectations:**
- Reads BOTH `AGENTS.md` (canonical) and `CLAUDE.md` (shim)
- Honors the `@AGENTS.md` import — CLAUDE.md is read as supplemental Claude-specific content
- Briefing mentions M4 invoice-PDF progress

**/wrapup expectations:**
- Phase 5 prune operates on BOTH files' Operational sections (per the sectioned-writer rule)
- dev mode: terse prompts; surfaces ADR 0003 (drafted but not yet committed) as a quick-list item rather than full teaching prompt

### nonstandard-manual (Graphkit — TS layout library, GUIDE.md)

**/startup expectations:**
- Reads `.rad/profile` first, sees `operating_manual_path = "GUIDE.md"`, then reads `GUIDE.md` (not `CLAUDE.md` or `AGENTS.md`)
- If `.rad/profile` did not record the override, falls back to header-heuristic scan for "Agent Operating Manual" — also finds `GUIDE.md`
- Briefing references M3 Sugiyama hierarchical layout

**/wrapup expectations:**
- Phase 5 prune targets `GUIDE.md` Operational sections — not CLAUDE.md or AGENTS.md
- Phase 7 sync commit list includes `GUIDE.md` (not the canonical names)

### dev-mode-project (Routebadge — TS JWT key rotation)

**/startup expectations:**
- Reads `CLAUDE.md`, `.rad/profile`, `docs/status.md`, `docs/planning/current.md`
- Detects all acceptance criteria are checked in `current.md`
- Briefing notes "milestone shipped — ready to archive" prominently

**/wrapup expectations:**
- Phase 0 passes (work done since last status — the M2 completion captures are evidence enough)
- Phase 6 milestone-shipped archive triggers — proposes moving `current.md` to `planning/archive/YYYY-MM-DD-M2-jwt-rotation.md`
- dev mode: terse archive prompt (no teaching block), accepts on default Y
- Phase 3 candidate-decision detection: ADR 0002 already committed; quick-list mode shows it as "committed" without re-prompting

## When to update fixtures

When the v5.0 workflow contract changes (new section in status.md, new field in `.rad/profile`, different operating-manual section boundaries), update both the fixtures and this README's expected-behavior block.

The fixtures are a regression check: if a fixture stops behaving as documented, either the fixture has drifted from the workflow contract or the workflow has drifted from the spec — and that's a signal to investigate.

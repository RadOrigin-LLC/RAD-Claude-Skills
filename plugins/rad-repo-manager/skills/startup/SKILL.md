---
name: startup
description: >
  This skill should be used when the user says "startup", "start session", "orient
  me", "where did we leave off", "catch me up", "what's the state", "session
  briefing", "what was I working on", or — on a fresh/empty repo — "set up this
  repo", "bootstrap this project", "new project setup", "get me started right". Two
  paths: first-run onboarding (scaffold the minimal doc structure) and steady-state
  orientation (read the active docs, surface where you are + a one-line health
  verdict). Intentionally lean — targets a few seconds in steady state.
argument-hint: "[--agents claude|codex|gemini|<comma-separated>]"
user-invocable: true
allowed-tools: Read Glob Grep Bash Write AskUserQuestion
---

# Startup — orient, or onboard a fresh repo

Get the coding agent starting on the right foot. Two paths, chosen by what's already
there. **Keep it lean** — this runs at the top of a session; it is not an audit. The
deep hygiene pass is `/rad-repo-manager:analyze`.

## Decide the path

Glob the repo. Determine onboarding vs steady-state:

- **Onboard (first run)** when there's no `AGENTS.md` AND no `docs/prd.md`/`docs/plan.md` — a fresh or near-empty repo, or one that has never been set up with this doc model.
- **Orient (steady state)** when `AGENTS.md` exists. The normal case.

## Path A — Onboard (first run)

Set up the minimal doc structure from the templates in `${CLAUDE_PLUGIN_ROOT}/templates/`. Lay the foundation; do not write product or plan content (that's the user's and `/rad-planner:plan`'s job).

1. **Agent scope.** If `--agents` was passed, use it. Otherwise ask (AskUserQuestion): which coding agents will use this repo — Claude, Codex, Gemini, or a mix? This decides which shims to create.
2. **Scaffold**, creating only what's missing (never overwrite existing files):
   - `AGENTS.md` ← `templates/AGENTS.md` (the operating manual; placeholders left for the user to fill)
   - Shims per agent scope: `CLAUDE.md` ← `templates/CLAUDE.md`, `GEMINI.md` ← `templates/GEMINI.md` (each a thin `@AGENTS.md` import). Codex reads `AGENTS.md` natively — no shim.
   - `docs/prd.md` ← `templates/prd.md` (skeleton)
   - `docs/plan.md` ← `templates/plan.md` (stub pointing at `/rad-planner:plan`)
   - `docs/handoff.md` ← `templates/handoff.md`
   - `docs/inbox/README.md` ← `templates/inbox-README.md`
   - `docs/archive/README.md` ← `templates/archive-README.md`
   - Do NOT create any reference docs — they appear only when a project needs one.
3. **Fill what's mechanical:** set the remote URL line in `AGENTS.md` from `git remote get-url origin` if available; leave the `<PLACEHOLDER>` sections for the user.
4. **Hand off.** Tell the user, in plain language: the structure is in place, the active read path is the four core docs, and the next step is `/rad-planner:plan` to create the plan, then to fill the `<PLACEHOLDER>` sections in `AGENTS.md` and `docs/prd.md`.

## Path B — Orient (steady state)

Read the active core in one parallel batch: `AGENTS.md`, `docs/prd.md`, `docs/plan.md`, `docs/handoff.md`. Then surface a short briefing:

- **Where we are** — from `docs/handoff.md` (resume point + current state). If handoff is missing or stale, say so plainly rather than inventing.
- **The plan** — the current milestone/focus from `docs/plan.md` (one line). If `plan.md` is still the stub, recommend `/rad-planner:plan`.
- **Health line** — the closing line (see below).

Do not deep-scan, do not audit, do not read reference or archive docs. If the user needs the full picture, point them at `/rad-repo-manager:analyze`.

## The health line

Run the cheap tripwire scan and print its one-line verdict as the last line:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/repo-scan.py . --json
```

It returns a loose-ends count and severity. Render exactly one line:

- 🟢 `Repo's tidy — nothing loose.` (0 loose ends)
- 🟡 `A few loose ends (N) — fine for now.` (1–4)
- 🔴 `Getting cluttered (N) — worth a /rad-repo-manager:analyze to sort it.` (≥5)

**Cooldown:** only append the explicit `/analyze` suggestion (the 🔴 tail) if it hasn't been shown in the last 3 sessions — check/update the `last_nudge` marker the scanner maintains. Otherwise show the count without the nudge. The count itself always shows — it's the trend the user watches.

Honesty: the green light means "the cheap signals are clean," not "everything is correct." Don't overclaim.

## What this skill does NOT do

- No deep audit (contradictions, redundancy, filing) — that's `analyze`.
- No writing of product or plan content — onboarding scaffolds skeletons only.
- No auto-commit.
- In steady state, no writes at all.

## References

- `${CLAUDE_PLUGIN_ROOT}/templates/` — the doc-model skeletons used at onboarding
- `${CLAUDE_PLUGIN_ROOT}/scripts/repo-scan.py` — the cheap tripwire scan behind the health line
- `${CLAUDE_PLUGIN_ROOT}/references/doc-model.md` — the tiers, the active set, the filing rules

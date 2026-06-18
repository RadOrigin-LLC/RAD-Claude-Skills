---
name: repo-init
description: >
  This skill should be used when the user says "set up this repo", "bootstrap this
  project", "new project setup", "scaffold the docs", "initialize the repo model",
  "get me started right", or when startup recommended it on a fresh repo. Scaffolds
  the compact doc model (AGENTS.md, docs/prd.md, docs/plan.md, docs/handoff.md, thin
  agent shims, and minimal folders) in a new or nearly empty repo. Creates only
  what's missing; never invents product content; never overwrites user-authored
  files without confirmation.
argument-hint: "[--agents claude|codex|gemini|<comma-separated>]"
user-invocable: true
allowed-tools: Read Glob Grep Bash Write AskUserQuestion
---

# Repo Init — scaffold the compact doc model

Lay the foundation for a fresh, nearly empty, or never-organized repo. Scaffold the
structure and leave placeholders — **do not write product, plan, or design content**
(that's the user's and `/rad-planner:plan`'s job). Use the templates in
`<plugin-root>/templates/` (where `<plugin-root>` is either `${CLAUDE_PLUGIN_ROOT}`, global config `plugins/rad-repo-manager`, or local workspace `plugins/rad-repo-manager`).

Use this only for greenfield setup. An established repo with drift goes to
`/rad-repo-manager:repo-align` instead.

## 1. Look before scaffolding

```bash
git status --short
git remote get-url origin   # for the AGENTS.md remote line, if set
```

Glob the repo. Detect the app type and package manager if obvious (`package.json`,
lockfiles, `pyproject.toml`, `Cargo.toml`, framework config) — this only informs the
`AGENTS.md` baseline, not product content.

Confirm this is greenfield: no `AGENTS.md` and no real `docs/prd.md`/`docs/plan.md`.
If the repo is already established, stop and recommend `repo-align`.

## 2. Agent scope

If `--agents` was passed, use it. Otherwise ask (via AskUserQuestion or `ask_question` on Antigravity): which coding agents
will use this repo — Claude, Codex, Gemini, or a mix? This decides which shims to
create. Codex reads `AGENTS.md` natively (no shim). If unclear, ask before creating
non-Codex shims.

## 3. Scaffold — only what's missing

Create only files that don't already exist. **Never overwrite a user-authored file
without explicit confirmation.**

Core active docs:

- `AGENTS.md` ← `templates/AGENTS.md` (operating manual; placeholders for the user)
- `docs/prd.md` ← `templates/prd.md` (skeleton)
- `docs/plan.md` ← `templates/plan.md` (stub pointing at `/rad-planner:plan`)
- `docs/handoff.md` ← `templates/handoff.md` (snapshot shape, placeholder values)

Agent shims (per scope; each a thin `@AGENTS.md` import — never duplicated content):

- `CLAUDE.md` ← `templates/CLAUDE.md`
- `GEMINI.md` ← `templates/GEMINI.md`

Minimal folders:

- `docs/reference/README.md` ← `templates/reference-README.md` (the closed catalog
  menu; do **not** create the reference docs themselves yet)
- `docs/archive/README.md` ← `templates/archive-README.md` (history banner)

Do **not** create `docs/status.md`, `docs/roadmap.md`, `docs/implementation-plan.md`,
`docs/inbox/`, a top-level `docs/design.md` (it appears only when design work starts),
loose root-level handoff/status/audit docs, or folder-specific
`AGENTS.md`/`CLAUDE.md`/`GEMINI.md`.

## 4. Fill only what's mechanical

Set the remote URL line in `AGENTS.md` from `git remote get-url origin` if available.
Stamp each scaffolded doc's `**Updated:** <YYYY-MM-DD>` with today's date (the
freshness scans key off it). Leave every other `<PLACEHOLDER>` section for the user.
Do not invent goals, roadmap, architecture, decisions, or validation promises.

## 5. Hand off

Tell the user, plainly: the structure is in place, the active read path is the four
core docs, and the next steps are (a) run `/rad-planner:plan` to create the plan and
(b) fill the `<PLACEHOLDER>` sections in `AGENTS.md` and `docs/prd.md`.

## Output format

```text
Repo init:
Detected repo type:
Agent scope:
Files created:
Files skipped (already exist):
Active read path:
Next step for the user:
Notes:
```

## References

- `<plugin-root>/templates/` — the doc-model skeletons
- `<plugin-root>/references/doc-model.md` — the tiers, the active core, the reference catalog

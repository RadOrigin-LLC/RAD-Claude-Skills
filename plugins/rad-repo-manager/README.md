# rad-repo-manager

A repo manager for vibe coders. It keeps a project's docs **minimal, consistent, and honest** so coding agents don't get confused or misled by contradictory information. Think of it as the *manager* and your coding agent as the *employee*: it onboards the workspace, checks in at the start and end of each session, and does a periodic deep clean — but it keeps things on track only *to a certain extent*, honestly scoped.

> Replaces **rad-session**. The old plugin was built around a canonical doc tree that became redundant and confused agents; this is a ground-up rebuild around a tiny, defended doc set.

## The problem it solves

Drift is invisible until it's a wreck. New docs pile up unnoticed, the active read-set creeps, docs start contradicting each other, and by the time you see it you're taking a long pause to untangle it. This plugin makes drift **visible early and cheaply**, and tells you when you're actually fine.

## The doc model — a tiny, declared, defended core

| Tier | Where | Read |
|---|---|---|
| **Active** | `AGENTS.md` · `docs/prd.md` · `docs/plan.md` · `docs/handoff.md` | every session |
| **Reference** | `docs/reference/*` — a closed, named catalog | only when the task touches it |
| **Inbox** | `docs/inbox/*` — new docs awaiting filing | flagged, then filed by `analyze` |
| **Archive** | `docs/archive/*` — history | never by default |

The active set is **declared in AGENTS.md and capped at four.** "On track" becomes mechanically checkable: reality matches the declared set, nothing floating, nothing bloated. See `references/doc-model.md` for the full model, the reference catalog, and the filing rules.

## Three commands

| Command | Job | Speed |
|---|---|---|
| `/rad-repo-manager:startup` | Orient (where you are + what's next + health line). **First run:** onboard — scaffold the structure, a lean `AGENTS.md`, agent shims, and skeletons, then point you at `/rad-planner:plan`. | fast |
| `/rad-repo-manager:wrapup` | Leave a clean handoff — overwrite `docs/handoff.md` from git evidence, then the health line. No auto-commit. | fast |
| `/rad-repo-manager:analyze` | The opt-in deep clean: contradictions, redundancy, stale/orphaned content, loose/unfiled docs, decisions-needed — fixes proposed interactively, never auto-applied. | deep |

## The health line — early warning without nagging

Every `startup`/`wrapup` ends with one quiet line:

- 🟢 `Repo's tidy — nothing loose.`
- 🟡 `A few loose ends (3) — fine for now.`
- 🔴 `Getting cluttered (7) — worth a /rad-repo-manager:analyze to sort it.`

The **loose-ends count is the trend you watch** — it climbs in plain sight (1→3→6), one line at a time, so you see the drift coming. A loose end is only ever a hard, mechanical signal (an unfiled `.md`, the active set grew, AGENTS.md bloated) so the count is trustworthy. The explicit `/analyze` nudge (red only) is rate-limited with a cooldown so it never becomes noise. The green light means "the cheap signals are clean," not "everything is correct" — honestly scoped.

## What it writes (and what it doesn't)

- **Authors:** `AGENTS.md` operational sections (never your authored content), the `CLAUDE.md`/`GEMINI.md` shims, `docs/handoff.md`. Scaffolds `prd.md`/`plan.md` skeletons once at onboarding.
- **Never writes** durable content — changes to `docs/prd.md` or `docs/reference/decision-log.md` are **surfaced** as a paste-ready update-prompt in `docs/inbox/` for you to apply. Product and decisions stay yours.
- **Never auto-acts** in `analyze` — every fold/extract/file is confirmed by you.

`docs/plan.md` is owned by [`rad-planner`](../rad-planner/), not this plugin. They share the active core with a clean boundary: planner owns the plan's content; repo-manager owns the handoff and the operating manual.

## Validators (scripts/)

Pure-stdlib Python 3.8+, human text or `--json`:

| Script | Role |
|---|---|
| `repo-scan.py` | the cheap health-line engine (loose ends, floating docs, inbox, AGENTS bloat) |
| `doc-contradiction.py` | PRD non-goals vs what the plan builds (catches scope-creep) |
| `doc-redundancy.py` | the same fact stated in two active docs |
| `audit-user-content.py` | orphaned terminology + dead paths in AGENTS.md's user-authored sections |

## Requirements

- **Python 3.8+** for the validators. Without it, `analyze`'s mechanical checks degrade to manual review against the documented model.
- Works with Claude Code, Codex (reads `AGENTS.md` natively), and Gemini CLI (via the shim).

## License

Apache-2.0

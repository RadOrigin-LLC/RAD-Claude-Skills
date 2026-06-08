# rad-repo-manager

A repo manager for vibe coders. It keeps a project's docs **minimal, consistent, and
honest** so coding agents don't get confused or misled by contradictory information.
Think of it as the *manager* and your coding agent as the *employee*: it orients you at
the start of a session, leaves a clean handoff at the end, sets up the doc model on a
fresh repo, and runs a periodic deep-clean when docs drift — honestly scoped, no
overclaiming.

> Replaces **rad-session**, and is the Claude-side counterpart to the Codex
> `rad-repo-manager` skills. The model is a tiny, declared, defended doc set.

## The problem it solves

Drift is invisible until it's a wreck. New docs pile up, the active read-set creeps,
docs start contradicting each other, and by the time you notice you're untangling it.
This plugin keeps the active set tiny and defended, and gives you an explicit pass to
catch drift before it's a mess.

## The doc model — a tiny, declared, defended core

| Tier | Where | Read |
|---|---|---|
| **Active** | `AGENTS.md` · `docs/prd.md` · `docs/plan.md` · `docs/handoff.md` | every session |
| **Conditional** | `docs/design.md` · `docs/reference/*` (closed catalog) · `docs/README.md` | only when the task touches it |
| **Archive** | `docs/archive/*` — history | never by default |

The active set is **declared in AGENTS.md and capped at four.** "Aligned" becomes
mechanically checkable: reality matches the declared set, nothing floating, nothing
bloated. See `references/doc-model.md` for the full model, the reference catalog, and
the plan ↔ handoff boundary.

**The boundary that matters most:** `docs/plan.md` owns everything durable (roadmap,
milestones, allowed/forbidden scope, validation gates, stop conditions);
`docs/handoff.md` owns only the short resume snapshot for the next chat. If a statement
must still be true after the next session, it belongs in the plan, not the handoff.

## Four skills

| Skill | Job | Speed |
|---|---|---|
| `/rad-repo-manager:startup` | Orient — read the four active docs + git state, surface where you are and what's next. Read-only; recommends `repo-init` (fresh repo) or `repo-align` (drift). | fast |
| `/rad-repo-manager:wrapup` | Leave a clean handoff — overwrite `docs/handoff.md` from git evidence, then reconcile the core docs with the session: offer scoped updates to the docs it owns (`plan.md`, AGENTS.md operational sections) and surface stale user-owned docs (prd/design/decisions). No auto-commit, never runs tests. | fast |
| `/rad-repo-manager:repo-init` | First-run setup — scaffold the compact doc model (core docs, agent shims, minimal folders) on a new or nearly empty repo. Never invents product content. | one-time |
| `/rad-repo-manager:repo-align` | The opt-in deep clean — find drift (contradictions, redundancy, stale/loose/misplaced docs, broken read paths) and propose fixes interactively. Proposes, never auto-acts; moves with `git mv`. | deep |

`startup` is read-only; `wrapup` is evidence-grounded — it writes the handoff, offers
scoped updates to the docs it owns, and surfaces stale user-owned docs, all within the
session's changes. The deep, whole-repo drift detection lives in `repo-align`, where
it's reviewed with your confirmation — not run on every session.

## What it writes (and what it doesn't)

- **Authors:** `AGENTS.md` operational sections (never your authored content), the
  `CLAUDE.md`/`GEMINI.md` shims, `docs/handoff.md`. Scaffolds `prd.md`/`plan.md`
  skeletons once at `repo-init`. At `wrapup`, offers scoped updates to `docs/plan.md`
  and `AGENTS.md` operational sections when the session made them stale.
- **Never writes** durable content — a change to `docs/prd.md` or
  `docs/reference/decision-log.md` is **surfaced** in plain language for you to apply.
  Product and decisions stay yours.
- **Never auto-acts** in `repo-align` — every fold/extract/move/archive is confirmed,
  and tracked files move with `git mv` so history is preserved.
- **Never creates** `docs/status.md`, `docs/roadmap.md`, `docs/implementation-plan.md`,
  loose root-level status/handoff/audit docs, or folder-specific agent files.

`docs/plan.md` is owned by [`rad-planner`](../rad-planner/), not this plugin. They share
the active core with a clean boundary: planner owns the plan's content; repo-manager
owns the handoff and the operating manual.

## Validators (scripts/)

Pure-stdlib Python 3.8+, human text or `--json`. They surface **candidates** for
`repo-align` — judgment decides which are real; nothing is auto-fixed:

| Script | Role |
|---|---|
| `repo-scan.py` | mechanical drift signals (floating/misplaced docs, active-set growth, AGENTS.md bloat) |
| `doc-contradiction.py` | PRD non-goals vs what the plan builds (catches scope-creep) |
| `doc-redundancy.py` | the same fact stated in two active docs |
| `audit-user-content.py` | orphaned terminology + dead paths in AGENTS.md's user-authored sections |

## Requirements

- **Python 3.8+** for the validators. Without it, `repo-align`'s mechanical checks
  degrade to manual review against the documented model.
- Works with Claude Code, Codex (reads `AGENTS.md` natively), and Gemini CLI (via the shim).

## License

Apache-2.0

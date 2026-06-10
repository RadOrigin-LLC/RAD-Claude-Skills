# rad-repo-manager

A repo manager for vibe coders. It keeps a project's docs **minimal, consistent, fresh,
and honest** so coding agents don't get confused or misled by contradictory or stale
information. Think of it as the *manager* and your coding agent as the *employee*: it
orients you at the start of a session, leaves a clean handoff at the end, sets up the
doc model on a fresh repo, watches for staleness ambiently, and runs a periodic
deep-clean when docs drift — honestly scoped, no overclaiming.

> Replaces **rad-session**, and is the Claude-side counterpart to the Codex
> `rad-repo-manager` skills. The model is a tiny, declared, defended doc set.

## The problem it solves

Drift is invisible until it's a wreck. New docs pile up, the active read-set creeps,
the handoff describes three sessions ago, the PRD describes a product you've since
changed — and by the time you notice you're untangling it. This plugin keeps the
active set tiny and defended, checks its freshness against git evidence at every
session start, and gives you an explicit deep pass for the judgment calls. Detection
is automatic; every fix is yours to confirm.

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
| `/rad-repo-manager:startup` | Orient — read the four active docs + git state, run the two cheap mechanical scans (loose docs, stale docs), surface where you are, what's next, and whether the docs are trustworthy. Read-only; recommends `repo-init` (fresh repo) or `repo-align` (drift). | fast |
| `/rad-repo-manager:wrapup` | Leave a clean handoff — overwrite `docs/handoff.md` from git evidence, then reconcile the core docs with the session: apply scoped updates to the docs it owns (`plan.md`, AGENTS.md operational sections) on your OK, and draft exact edits to stale user-owned docs (prd/design/decisions) applied only on per-edit confirmation. Ends with a one-line hygiene pulse. No auto-commit, never runs tests. | fast |
| `/rad-repo-manager:repo-init` | First-run setup — scaffold the compact doc model (core docs, agent shims, minimal folders) on a new or nearly empty repo. Never invents product content. | one-time |
| `/rad-repo-manager:repo-align` | The opt-in deep clean — find drift (contradictions, redundancy, stale/loose/misplaced docs, broken read paths) and propose fixes interactively. Proposes, never auto-acts; moves with `git mv`. | deep |

`startup` is read-only; `wrapup` is evidence-grounded. Staleness detection is no longer
deferred to the deep pass: the two cheap scans run at `startup` and via the
SessionStart hook, and `wrapup` ends with a one-line hygiene pulse — so a stale handoff
or an untouched PRD is caught at the next session start, not months later. The deeper
validators and all filing dispositions stay in `repo-align`, reviewed with your
confirmation.

## Hooks — the ambient layer

Skills only run when you remember to invoke them; the hooks catch what habit misses.
All three are **silent in repos that don't use the doc model** (they require
`AGENTS.md` plus `docs/prd.md` or `docs/handoff.md`), never block, and say nothing
when everything is green:

| Hook | When | What it does |
|---|---|---|
| SessionStart | session opens | Runs the two cheap scans; injects a one-line doc-health note only if something is stale or loose. |
| PreCompact | before context compaction | Tells the compaction summary to preserve the handoff's raw material verbatim (validation commands + results, files changed, current task, next action) — so a post-compaction `wrapup` isn't writing from amnesia. |
| Stop | end of a response | At most **once per session**, and only when real work is uncommitted and the handoff isn't fresh: one line reminding you `wrapup` exists. |

## What it writes (and what it doesn't)

- **Authors:** `AGENTS.md` operational sections (never your authored content), the
  `CLAUDE.md`/`GEMINI.md` shims, `docs/handoff.md`. Scaffolds `prd.md`/`plan.md`
  skeletons once at `repo-init`. At `wrapup`, offers scoped updates to `docs/plan.md`
  and `AGENTS.md` operational sections when the session made them stale.
- **Drafts, never decides** durable content — a change to `docs/prd.md`,
  `docs/design.md`, or `docs/reference/decision-log.md` is drafted as the exact edit
  (old → new) and applied **only on your explicit per-edit confirmation**. You own the
  decision; the plugin does the typing. A skip means hands off.
- **Never auto-acts** in `repo-align` — every fold/extract/move/archive is confirmed,
  and tracked files move with `git mv` so history is preserved.
- **Never creates** `docs/status.md`, `docs/roadmap.md`, `docs/implementation-plan.md`,
  loose root-level status/handoff/audit docs, or folder-specific agent files.

`docs/plan.md` is owned by [`rad-planner`](../rad-planner/), not this plugin. They share
the active core with a clean boundary: the planner owns the plan's content (and may
birth `docs/prd.md` from its discovery interview, per-section confirmed); the
repo-manager owns the handoff and the operating manual, and keeps both plan and PRD
fresh between planning sessions. When wrapup finds the plan *structurally* diverged —
not just a status line stale — it recommends `/rad-planner:replan` rather than
restructuring it itself. And if the whole repo is a mess with no trustworthy plan at
all, that's `/rad-planner:rescue` — archaeology plus a fresh plan; this plugin then
maintains what rescue produces.

## Validators (scripts/)

Pure-stdlib Python 3.8+, human text or `--json` (run with `python3`, or `python` on
Windows). They surface **candidates** — judgment decides which are real; nothing is
auto-fixed. The first two are cheap and run every session; the rest run in `repo-align`:

| Script | Role |
|---|---|
| `repo-scan.py` | mechanical drift signals (floating/misplaced docs, active-set growth, AGENTS.md bloat) |
| `doc-freshness.py` | stale active docs from git evidence (handoff behind the latest commits; prd/plan unchanged while code churned) |
| `doc-contradiction.py` | PRD non-goals vs what the plan builds (catches scope-creep) |
| `doc-redundancy.py` | the same fact stated in two active docs |
| `audit-user-content.py` | orphaned terminology + dead paths in AGENTS.md's user-authored sections |

## Requirements

- **Python 3.8+** for the validators and hooks (`python3` or `python` on PATH).
  Without it, the scans degrade to manual review against the documented model and the
  hooks stay silent — nothing breaks.
- Works with Claude Code, Codex (reads `AGENTS.md` natively), and Gemini CLI (via the
  shim). Hooks are Claude Code-only; the skills and scripts work everywhere.

## License

Apache-2.0

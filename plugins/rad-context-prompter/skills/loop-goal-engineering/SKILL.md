---
name: loop-goal-engineering
description: >
  This skill should be used when the user wants to author agentic loops or goal/completion
  conditions — "write a loop prompt", "loop engineering", "set up a ralph loop", "run Claude
  overnight", "write a /goal condition", "goal mode", "goal engineering", "stop condition for
  my agent", "completion criteria", "definition of done for the agent", "long-horizon task
  setup", "keep the agent working until", "make Codex run until tests pass", "PLANS.md",
  "harness for a long run", "my agent stops too early", "my agent never finishes", or wants
  Claude Code /loop, /goal, Stop hooks, or Codex Goal Mode set up well. Covers loop prompt
  authoring, goal condition design, the four-file long-horizon scaffold, and anti-reward-hacking
  hardening. For ordinary single-shot prompts, use prompt-engineering instead.
---

# Loop & Goal Engineering

Author the artifacts that drive autonomous agent runs: **loop prompts** (re-run
cold each iteration until a backlog is done), **goal conditions** (machine- or
evaluator-checkable completion criteria), and the **long-horizon file scaffold**
that carries state between iterations.

The runtime primitives exist — Claude Code `/goal` and `/loop`, Stop hooks,
Codex Goal Mode, bash while-loops. They all assume the human can already write
a good loop prompt or goal condition. That authoring step is this skill's job.

---

## Step 1 — Classify the Deliverable

| User wants | Deliverable | Primary reference |
|---|---|---|
| Agent grinds through a backlog / overnight run | **Loop prompt** (+ scaffold files) | `references/loop-patterns.md` |
| Agent keeps working until X is true | **Goal condition** | `references/goal-specs.md` |
| Multi-hour/multi-day autonomous project | **Four-file scaffold** + loop prompt + goal | both |
| A check that must gate with zero exceptions | **Stop-hook script spec** | goal-specs.md §2 |

If the request is really a one-shot prompt with no iteration ("write a prompt
that refactors this file"), hand off to the **prompt-engineering** skill.

## Step 2 — Pick the Harness

Use the harness selection table in `references/loop-patterns.md` §1. Ask at
most one question if the target runtime is ambiguous (Claude Code vs Codex vs
raw bash loop) — it changes the output format:

- **Claude Code `/goal`** → condition must be provable from the agent's own
  transcript output (the evaluator runs no commands itself)
- **Codex Goal Mode** → Goal / Context / Constraints / Done-when skeleton
- **Stop hook** → the condition becomes a script with exit codes
- **Bash/Ralph loop** → full loop prompt + four-file scaffold + safety rails

## Step 3 — Draft

**Loop prompts**: apply the ten rules in loop-patterns.md §2 — one task per
iteration, state in files/git, search-before-assuming, no placeholders,
in-iteration verification, protected tests, idempotency, per-iteration commits,
bounds, one-deliverable scope. Start from the template in §4.

**Goal conditions**: apply the four-part anatomy in goal-specs.md §1 —
measurable end state, stated proof check, constraints, bound. Use the
skeletons in §2 and the vague-goal rewrite table in §4.

**Scaffolds**: generate the four files (spec / plan / runbook / status log)
per loop-patterns.md §3, with per-milestone validation commands in the plan.

## Step 4 — Lint (mechanism before judgment)

Run the deterministic checker on every drafted goal condition or loop prompt
before delivering it:

```bash
PY=$(command -v python3 || command -v python)
"$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/check-goal.py" <draft-file> --json
# or pipe: echo "<draft>" | "$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/check-goal.py" - --json
```

The script flags: missing named command, vague success adjectives, missing
scope guard, missing bound, and seven of the eight gameability signatures
(G1-G7 in goal-specs.md §3). Fix CRITICAL and WARNING findings, then re-run.
The script exits 1 when findings exist — that's signal, not failure.

Then apply judgment the script can't: **G8 (revert-satisfiability — could the
agent pass by reverting to the original state?)**, whether the check is
*semantically* sufficient (a passing test suite that doesn't cover the feature
proves nothing), whether the goal is satisfiable at all, and whether two
experts would agree on pass/fail.

## Step 5 — Deliver

Same contract as prompt-engineering: a paste-ready block (or file set), one
line stating the target harness and what was optimized, and setup notes only
when genuinely needed (e.g., "save as PLAN.md in repo root", "requires a
Stop hook registered in settings.json").

For loop deliverables, ALWAYS include the safety footer when the run is
unattended: sandbox/worktree advice, credential scope, blast-radius
constraints (loop-patterns.md §5). Never deliver an unbounded loop.

---

## Hard Rules

- NEVER deliver a goal condition without a named command/check, a scope
  guard, and a bound. "Tests pass" alone is a documented failure mode.
- NEVER deliver a loop prompt that allows multiple tasks per iteration.
- NEVER let the condition's own success criteria be editable by the agent
  (tests, scoring scripts) without an explicit protection constraint.
- NEVER present "goal engineering" as established vocabulary in delivered
  artifacts — the vendors' terms are Goal Mode, `/goal` conditions, and
  "Done when" criteria. (Using the phrase conversationally is fine.)
- For Claude Code `/goal`: ALWAYS instruct the agent to show evidence
  (command output) in its transcript — the evaluator cannot run commands.

## Reference Files

| File | Read when |
|---|---|
| `references/loop-patterns.md` | Authoring loop prompts, choosing a harness, building the four-file scaffold, unattended-run safety |
| `references/goal-specs.md` | Authoring goal conditions, hardening against reward hacking, vague-goal rewrites |

Related: `prompt-engineering` skill (single-shot prompts, system prompts,
CLAUDE.md/AGENTS.md), `prompt-debugger` agent (F8 category diagnoses loop and
goal failures in prompts that already misbehaved).

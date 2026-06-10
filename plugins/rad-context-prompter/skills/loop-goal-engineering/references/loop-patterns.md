# Loop Patterns — Writing Prompts That Drive Agentic Loops

Rules and templates for authoring the prompt that a loop harness re-runs until
done. Sourced from Geoffrey Huntley's Ralph loop (ghuntley.com/ralph), Simon
Willison's "Designing agentic loops" (Sep 2025), Anthropic's long-running-agent
harness posts (Nov 2025, Mar 2026), OpenAI's "Run long horizon tasks with Codex"
(Feb 2026), and the official Claude Code `/loop` + `/goal` docs.

A loop prompt is a different artifact from a normal prompt: it must work when
run **cold, repeatedly, against changing state**. The model that reads iteration
12 has no memory of iterations 1-11 — everything it needs must come from files,
git, and the prompt itself.

---

## §1 — Harness Selection (pick the loop runtime first)

| Harness | What it is | Use when |
|---|---|---|
| **In-prompt iteration** | "Run the check and iterate in the same message" | Single session, small task, check is fast |
| **Claude Code `/goal`** | Separate evaluator re-checks a condition after every turn; agent keeps working until it holds | One session, machine-checkable end state, needs persistence past "looks done" |
| **Claude Code Stop hook** | Deterministic script blocks turn-end until it passes (harness overrides after 8 consecutive blocks) | The check is a command and must gate with zero exceptions |
| **Claude Code `/loop`** | Re-runs a prompt or slash command on an interval or self-paced | Recurring/polling work, or grinding through a backlog across sessions |
| **Codex Goal Mode (`/goal`)** | Outcome + testable success criteria; plan-act-test loop, persists across interruptions | Codex users; long autonomous runs with testable completion |
| **Bash while-loop (Ralph)** | `while :; do agent -p "$(cat PROMPT.md)"; done` — fresh process and context each pass | Overnight/multi-day runs, biggest backlogs; you own the safety rails |
| **Verification subagent** | Fresh model tries to refute the result so the worker isn't grading itself | Layer on any of the above when self-assessment can't be trusted |

These layer: a Ralph loop's inner prompt can itself demand a verification
subagent; a `/goal` condition can be backed by a Stop hook.

---

## §2 — The Loop Prompt Rules

Every rule here traces to a documented failure mode in the sources.

**1. One task per iteration.** The single most-violated, most-critical rule
(Huntley: "I need to repeat myself here — one item per loop"). The prompt picks
exactly ONE item from the plan file, finishes it, commits, and exits. Multiple
tasks per pass compound errors and exhaust context.

**2. State lives in files and git, never in context.** Each iteration starts
cold. The prompt must name its state files explicitly (see §3) and instruct:
read plan → pick top item → work → update plan → commit. Progress survives in
the repo, not the conversation. Anthropic's Mar 2026 harness guidance prefers
exactly this — clean-slate **context resets with a handoff artifact** over
in-context compaction for long-horizon work.

**3. Search before assuming.** Cold-start agents falsely conclude code isn't
implemented and write duplicates. Verbatim Ralph rule: "Before making changes,
search the codebase (don't assume not implemented) using subagents."

**4. Ban placeholders explicitly.** Loops amplify stub-itis: a placeholder
committed in iteration 3 becomes load-bearing by iteration 9. Verbatim:
"DO NOT IMPLEMENT PLACEHOLDER OR SIMPLE IMPLEMENTATIONS. WE WANT FULL
IMPLEMENTATIONS."

**5. Verify inside the iteration.** After implementing, run the tests for that
unit before committing. The best feedback is "clearly defined rules for an
output, then explaining which rules failed" (Anthropic Agent SDK guidance).
Tie checks to exit codes, not vibes.

**6. Protect the tests.** Agents under completion pressure edit tests to pass.
State it: "It is unacceptable to remove or edit tests; fix the code instead."
(Anthropic long-running-agents guidance.)

**7. Make it idempotent.** The prompt must produce correct behavior whether it
runs on iteration 1 or 40, whether the last iteration succeeded or crashed
mid-task. No "continue from where you left off" — instead "determine current
state from the plan file and git log, then act."

**8. Commit per iteration with descriptive messages.** Git is the loop's
rollback and memory mechanism — descriptive commits let later iterations
"revert bad code changes and recover working states."

**9. Bound the loop.** Iteration cap, time cap, or budget cap — always.
Stop conditions also belong in-prompt: "If the plan file has no remaining
items, output DONE and stop."

**10. One thread per task, not per project.** Both vendors converge here:
scope each loop to a single deliverable; spin a new loop (fresh plan file) for
the next one.

---

## §3 — The Four-File Scaffold

Two independent sources — Huntley's Ralph (Jul 2025) and OpenAI's official
long-horizon Codex guide (Feb 2026) — converged on the same four roles.
Ship all four for any multi-hour autonomous run:

| Role | Ralph name | OpenAI name | Contents |
|---|---|---|---|
| **Spec** | `PROMPT.md` / `specs/*` | `Prompt.md` | Goals + non-goals, hard constraints, deliverables, "Done when" checks |
| **Plan** | `fix_plan.md` | `Plan.md` | Prioritized milestones, each small enough for ONE iteration, with acceptance criteria + validation command per milestone. Stop-and-fix rule: if validation fails, repair before moving on |
| **Runbook** | `AGENT.md` | `Implement.md` | How to build, test, run — the commands the agent can't guess |
| **Status log** | (git log) | `Documentation.md` | What's done, key decisions, surprises — the handoff artifact for the next cold start |

The loop prompt references these files explicitly (e.g. `@fix_plan.md`,
`@AGENT.md`) so every iteration deterministically loads the same orientation.

---

## §4 — Loop Prompt Template

```
Read @PLAN.md and @RUNBOOK.md, and skim the last 5 git log entries.

Pick the SINGLE highest-priority unchecked item in PLAN.md. Work on only
that item this session.

Before writing any code, search the codebase to confirm the item is not
already implemented (use subagents for the search).

Implement it fully — no placeholders, no stubs, no TODO comments standing
in for logic.

Verify: run [VALIDATION COMMAND] for the unit you changed. If it fails,
fix the code — never edit or delete tests to make them pass.

When the item passes:
1. Mark it complete in PLAN.md (with one line on any surprises/decisions)
2. Commit everything with a descriptive message
3. Stop.

If PLAN.md has no unchecked items remaining: output exactly "ALL TASKS
COMPLETE" and stop.

Constraints:
- Touch only files under [SCOPE PATH]
- Never modify [PROTECTED PATHS: tests/, .github/, migrations/...]
- Stop and leave a note in PLAN.md instead of guessing if a decision
  requires product judgment.
```

Adapt names/commands per project. The skeleton enforces rules 1-10 above.

---

## §5 — Safety for Unattended Runs

From Willison's "Designing agentic loops" and Anthropic's own practice:

- **Pick loop-shaped problems**: clear success criteria, cheap-to-run checks.
  "Any time you find yourself thinking 'ugh, I'm going to have to try a lot of
  variations here'" is the signal a loop fits.
- **Sandbox**: container/VM/worktree. Anthropic's documented pattern for
  full-autonomy runs is "`--dangerously-skip-permissions` in a container
  without internet access."
- **Credentials**: test/staging only. "If a credential can spend money, set a
  tight budget limit."
- **Blast-radius rules in the prompt**: protected paths, no force-push, no
  schema drops, no external messages.
- **Review budget is real**: a wrong-path overnight run returns a large body of
  work that's expensive to review ("comprehension debt"). Smaller milestone
  loops with per-milestone validation beat one giant run.

---

## §6 — Loop Anti-Patterns

| Anti-pattern | Consequence | Fix |
|---|---|---|
| Multiple tasks per iteration | Compounding errors, context exhaustion | Rule 1: one item per loop |
| Progress tracked in conversation | Lost on every reset/crash | Files + git (§3) |
| "Continue where you left off" | Undefined on cold start | Idempotent state-derivation (Rule 7) |
| No iteration/time bound | Runaway cost | Cap in harness AND in prompt |
| Vague completion ("until it's good") | Never terminates or false-completes | See goal-specs.md |
| Same session forever | Quality degrades as context fills; "context anxiety" — models wrap up prematurely near perceived limits | Fresh context per iteration; resets over compaction |
| Worker grades its own work | Self-praise bias — agents "confidently praise the work, even when quality is obviously mediocre" (Anthropic, Mar 2026) | Independent evaluator / verification subagent |
| Tests editable by the loop | Reward hacking — tests get gutted to pass | Rule 6 + protected paths |

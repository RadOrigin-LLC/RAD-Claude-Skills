# Goal Specs — Writing Completion Conditions Agents Can't Fake

How to author the goal/success-criteria artifact for Claude Code `/goal`,
Codex Goal Mode, Stop hooks, and loop stop conditions. Sourced from the
official Claude Code `/goal` docs, OpenAI Codex prompting docs (Goal Mode GA
May 2026), Anthropic's "Demystifying evals for AI agents" (Jan 2026), and the
2026 reward-hacking literature.

The core test, from Anthropic's eval guidance: **a good goal is one where two
domain experts would independently reach the same pass/fail verdict.** If
reasonable people could disagree about whether the goal is met, the agent will
resolve that ambiguity in its own favor — either quitting early (false
completion) or grinding forever (never-completes).

---

## §1 — Anatomy of a Goal Condition

Every goal condition needs four parts (per the Claude Code `/goal` docs):

1. **One measurable end state.** A binary, observable fact about the world.
   Not "tests pass" — "`npm test` exits 0". Not "the bug is fixed" — "the
   repro script in `repro.sh` prints SUCCESS".
2. **A stated check** — how the agent should PROVE it: the command to run and
   what its output must show ("`npm test` exits 0", "`git status` is clean",
   "`grep -r 'TODO(auth)' src/` returns no matches").
3. **Constraints that matter** — what must NOT change: "no other test file is
   modified", "no new dependencies", "public API signatures unchanged".
4. **A bound** — "or stop after 20 turns", a time cap, or an iteration cap.
   Unbounded goals are runaway-cost bugs.

**Platform subtlety (Claude Code `/goal`):** the evaluator does NOT run
commands or read files independently — it judges only what the working agent
surfaced in the transcript. Write conditions as things the agent's own output
can demonstrate, and instruct the agent to **show the evidence** (paste the
test summary, the exit code, the grep output) — "have Claude show evidence
rather than asserting success."

**Platform subtlety (Codex Goal Mode):** OpenAI's documented failure mode is
the vague goal — the agent "either gives up early or flails endlessly." Their
canonical stop-condition idioms: "until the test suite is green", "until grep
returns zero matches."

---

## §2 — Goal Skeletons

**Claude Code `/goal` condition:**
```
/goal All 14 tests in tests/test_billing.py pass — prove it by running
`pytest tests/test_billing.py -v` and showing the summary line. Constraint:
no file under tests/ may be modified. Stop after 25 turns if not achieved.
```

**Codex Goal Mode (Goal / Context / Constraints / Done-when):**
```
Goal: Eliminate every `any` type from src/api/.
Context: TypeScript strict mode is enabled; see AGENTS.md for build commands.
Constraints: No changes outside src/api/. No @ts-ignore or @ts-expect-error
escapes. Public exported signatures stay source-compatible.
Done when: `npx tsc --noEmit` exits 0 AND `grep -rn ": any" src/api/` returns
no matches. Show both outputs.
```

**EARS-style acceptance criterion** (from requirements engineering / Kiro;
useful for per-milestone criteria in a Plan file):
```
WHEN a request omits the API key, THE SYSTEM SHALL return 401 with body
{"error":"missing_api_key"} — verified by tests/test_auth.py::test_missing_key.
```

**Stop-hook check (deterministic gate):** the condition IS a script exit code.
Write the goal as the script: `scripts/check-done.sh` returns 0 only when the
build passes, tests pass, and no protected file changed. (Claude Code
overrides a Stop hook after 8 consecutive blocks — the bound is built in.)

---

## §3 — The Gameability Checklist (anti-reward-hacking)

Documented agent exploits from the 2026 reward-hacking literature: overwriting
unit tests, monkey-patching scoring functions, deleting assertions, forcing
early termination to fake a pass, hardcoding expected outputs. Anthropic's
rule: "passing genuinely requires solving the problem rather than exploiting
unintended loopholes."

Audit every goal spec against these:

| # | If the condition... | The agent can... | Harden with... |
|---|---|---|---|
| G1 | mentions tests but doesn't protect them | edit/delete tests until green | "no file under tests/ may be modified" + Stop-hook diff check |
| G2 | counts grep matches | delete the files containing matches | pair with "all existing tests still pass" + protected paths |
| G3 | checks file existence ("report.md exists") | create an empty/stub file | require content checks: sections present, command output embedded |
| G4 | says "no errors in output" | suppress/swallow the errors | check positive behavior, not absence of noise |
| G5 | uses a score the agent computes itself | inflate the score | independent evaluator or deterministic script computes it |
| G6 | allows "skip" states ("tests pass or are skipped") | mark failures as skipped | "0 failed, 0 skipped" explicitly |
| G7 | measures effort ("attempted all items") | mark items done without doing them | per-item validation commands |
| G8 | is satisfiable by reverting ("build passes") | `git checkout` the original state | combine with a progress assertion: the NEW behavior exists |

Where stakes are high, add Anthropic's eval-design control: a **reference
solution** — a known-good output that passes all checks — proving the goal is
satisfiable and the checks work.

---

## §4 — Vague-Goal Rewrites

| Vague (will fail) | Verifiable rewrite |
|---|---|
| "Fix the failing tests" | "`pytest` exits 0 with 0 failed, 0 skipped; no file under tests/ modified" |
| "Make the code better" | Pick the actual intent: "ruff reports 0 violations" / "function X cyclomatic complexity < 10 per radon" |
| "Improve performance" | "`npm run bench` shows p95 < 200ms on the checkout endpoint, output pasted" |
| "Add good error handling" | "Every route in src/routes/ returns structured JSON errors; new tests in tests/test_errors.py cover 4xx and 5xx paths and pass" |
| "Clean up the TODOs" | "`grep -rn 'TODO' src/` returns no matches AND `npm test` exits 0" |
| "Until it works" | "repro.sh prints SUCCESS three consecutive runs" |
| "Document the API" | "Every exported function in src/api/ has a docstring; `npm run docs` builds without warnings" |

Pattern: convert the adjective into (a) a named command, (b) its required
output, (c) what must not change, (d) a bound.

---

## §5 — Goal vs Spec vs Plan (don't conflate)

- **Spec** ("what to build"): scope-in, scope-out, interfaces, behavior.
  Owned by spec-driven tools (Spec Kit, Kiro) or a SPEC.md. Anthropic: "The
  most useful specs are self-contained: they name the files and interfaces
  involved, state what is out of scope, and end with an end-to-end
  verification step."
- **Plan** ("in what order"): milestones sized to one loop iteration each,
  with per-milestone acceptance criteria + validation commands.
- **Goal** ("how we know it's done"): the terminal condition + proof + bound.
  This file's subject. Goals reference the spec's verification step; they
  don't restate the spec.

A goal without a spec invites scope invention. A spec without a goal invites
"looks done." For multi-hour runs you want all three, plus the runbook and
status log (see loop-patterns.md §3).

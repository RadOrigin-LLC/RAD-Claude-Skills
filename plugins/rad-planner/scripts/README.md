# rad-planner scripts

Mechanical validators that turn the plugin's "DAG enforcement / JSON-first contracts" claims from aspirational into actual. The skills invoke these scripts during plan generation and review; they also work standalone for users who want a quick check.

All scripts are pure Python 3.8+ stdlib. No `pip install` required (`validate-json.py` will use the optional `jsonschema` package if it's installed for fuller draft-07 coverage).

## plan-lint.py

Validates a tasks file against the rad-planner format documented at `references/task-format.md`.

```bash
python3 scripts/plan-lint.py --mode dag tasks.md         # cycles, orphans, phantom deps, complexity caps
python3 scripts/plan-lint.py --mode checklist tasks.md   # missing fields, vague language
python3 scripts/plan-lint.py --mode all tasks.md         # dag + checklist
python3 scripts/plan-lint.py --mode status tasks.md      # % complete, blocked, next eligible
python3 scripts/plan-lint.py --mode all tasks.md --json  # machine-readable
```

**What `dag` catches that an LLM eyeballing a 30-task plan will miss:**
- Subtle multi-hop cycles (S1 → S5 → S12 → S3 → S1)
- Phantom dependencies (`Dependencies: [S99]` where S99 doesn't exist)
- Complexity scores > 7 without subtasks
- Tasks orphaned from the dependency graph

**What `checklist` catches:**
- Missing required fields (`Validation`, `Rollback`, `Dependencies`, `Complexity`)
- Vague validation language: "verify it works", "make sure it runs", "looks right", "tbd", etc.
- Validation strings too short to plausibly be a runnable command

**Exit codes:** `0` clean, `1` issues found, `2` script error (file not found, parse failure).

## validate-json.py

Validates a JSON payload against a JSON Schema (the rad-planner subagent contracts at `references/subagent-prompts/*.schema.json`).

```bash
# Validate a file
python3 scripts/validate-json.py references/subagent-prompts/risk-assessment.schema.json output.json

# Validate from stdin (typical: pipe the agent's output)
echo "$AGENT_OUTPUT" | python3 scripts/validate-json.py <schema> -

# Extract first ```json block from markdown wrapper, then validate
python3 scripts/validate-json.py <schema> agent-output.md --extract-from-markdown

# Machine-readable
python3 scripts/validate-json.py <schema> output.json --json
```

The dispatching skills (`plan`, `review-plan`, `evaluate-stack`) use this to verify subagent JSON output against the documented contract before consuming it. On failure they re-prompt once with the validation errors before falling back to markdown parsing.

**Exit codes:** `0` valid, `1` invalid, `2` script error.

## Where these get invoked

| Caller | Script | When |
|---|---|---|
| `review-plan` skill | `plan-lint.py --mode all` | Step 2 (before / alongside risk-assessor dispatch) |
| `plan` skill | `plan-lint.py --mode all` | After Phase 3 (plan drafted, before risk-assessor) and after Phase 5 (post-approval) |
| `risk-assessor` agent | `plan-lint.py --mode all --json` | Pass 2 / Pass 3 — to skip mechanical re-checks the script already covered, focus LLM judgment on Pass 1 anti-patterns and Pass 6 architecture |
| `status` skill | `plan-lint.py --mode status` | Whenever invoked |
| `evaluate-stack` skill | `validate-json.py stack-eval.schema.json` | After stack-advisor returns |
| `review-plan` skill | `validate-json.py risk-assessment.schema.json` | After risk-assessor returns |

## What these scripts deliberately do NOT do

- **Do not judge plan quality.** Mechanical checks only. "Is this validation command actually sensible?" is still the LLM's job.
- **Do not check anti-patterns 1, 5, 8, 11–14.** Those require judgment. The risk-assessor still owns them.
- **Do not validate the JSON Schemas themselves.** If you edit a `.schema.json`, sanity-check it manually.
- **Do not auto-fix.** They report; the user (or a downstream skill) decides what to change.

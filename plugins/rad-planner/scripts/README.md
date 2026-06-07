# rad-planner scripts

Mechanical validators that complement the skill prompts with deterministic checks an LLM can miss. Both are pure Python 3.8+ stdlib — no `pip install` required.

## plan-lint.py

Validates `docs/plan.md` against the structure in `references/plan-template.md`.

```bash
python3 scripts/plan-lint.py docs/plan.md
python3 scripts/plan-lint.py docs/plan.md --json   # machine-readable
```

**What it catches:**

- **Missing required sections** — Objective, Scope, Key assumptions, Milestones, Tasks, Checkpoints, Risks & mitigations, Validation, Stop conditions. (`Stack` is recommended, not required — flagged LOW when absent.) Empty or placeholder-only required sections are flagged too.
- **Per-task field presence** — every task in `## Tasks` must carry all six fields: Objective, Files, Depends on, Done when, Validate, Rollback. A missing or placeholder field is HIGH.
- **Dependency integrity** — `Depends on` references must resolve to a task that exists in the file (no phantoms), no task may depend on itself, and the dependency graph must be acyclic. A cycle is CRITICAL.
- **Vague language** — phrases like "verify it works", "should work", "tbd", "looks right" in a task's `Done when` or `Validate` field are HIGH; those fields must be concrete and runnable.

**Exit codes:** `0` clean (or only LOW warnings), `1` CRITICAL or HIGH issues present, `2` script error.

Invoked from `/plan` Phase 4 (mechanical validation before the risk-assessor) and Phase 6 (final check), from `/review-plan` Step 2, and by the `risk-assessor` agent's Pass 0. Run it standalone for spot-checks during development.

## validate-json.py

Validates a JSON payload against a JSON Schema — the subagent contracts at `references/subagent-prompts/*.schema.json`.

```bash
python3 scripts/validate-json.py <schema.json> <data.json>
echo "$AGENT_OUTPUT" | python3 scripts/validate-json.py <schema> -
python3 scripts/validate-json.py <schema> agent-output.md --extract-from-markdown
python3 scripts/validate-json.py <schema> output.json --json
```

The dispatching skills use this to verify `stack-advisor` / `risk-assessor` JSON output against the documented contract before consuming it. On failure they re-prompt the agent once with the validation errors, then fall back to markdown parsing.

`pip install jsonschema` enables fuller draft-07 coverage; a pure-stdlib subset is used otherwise.

**Exit codes:** `0` valid, `1` invalid, `2` script error.

## What these deliberately do NOT do

- **Do not judge plan quality.** Mechanical checks only — "is this validation command sensible?" is the risk-assessor's or user's job.
- **Do not auto-fix.** They report; the user (or a downstream skill) decides what to change.
- **Do not validate the JSON Schemas themselves.** If you edit a `.schema.json`, sanity-check it manually.

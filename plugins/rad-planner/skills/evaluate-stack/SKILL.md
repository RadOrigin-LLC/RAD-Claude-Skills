---
name: evaluate-stack
description: >
  This skill should be used when the user says "what stack should I use", "evaluate my
  tech stack", "recommend a stack", "what framework for", "compare frameworks", "is this
  the right stack", "stack recommendation", "best framework for", "technology selection",
  "what database should I use", "Next.js vs Astro", "Supabase vs Firebase", "which ORM",
  "hosting recommendation", "deployment platform", or wants help choosing technologies
  for a new or existing project. Provides AI-native stack recommendations optimized for
  code generation accuracy.
argument-hint: "[project type or description] [--existing] [--non-interactive] [--resume <run-id>]"
user-invocable: true
allowed-tools: Read Glob Grep WebSearch WebFetch Agent Write Bash
---

# Evaluate Stack — AI-Native Technology Selection

Evaluate and recommend technology stacks optimized for AI-assisted development. Recommendations are grounded in the Golden Path proficiency matrix and verified against current information via Context7 / WebSearch where available.

The matrix itself reflects the maintainer's opinion plus dated observations of model behavior — see the date stamp in `references/golden-path-matrix.md`. Always trust the live verification over the matrix when they disagree.

## Cross-model note

This skill works identically across Opus 4.7, Sonnet 4.6, and Haiku 4.5. Parallel batching of WebSearch verification calls is handled inside the `stack-advisor` agent. The agent's JSON contract is identical regardless of model.

## Mode Flags

- `--existing` — Evaluate current stack rather than recommend new. The skill detects existing stack from `package.json` / `pyproject.toml` / `Cargo.toml` etc. before dispatching.
- `--non-interactive` — Skip user-confirmation on the recommendation. Emit the stack-advisor JSON directly as the result. Auto-proceed: `confidence: high|medium` → emit; `confidence: low` → emit with warnings in `awaiting_user_review`.
- `--resume <run-id>` — Load `.planner/state/<run-id>.json` and continue. Uses the shared checkpoint schema documented in `references/context-management.md`.

## Workflow

### 1. Gather Project Context

Ask the user (if not already provided):
- **Project type:** What are you building? (web app, API, CLI tool, mobile, data pipeline)
- **Scale:** Solo project, small team, or enterprise?
- **Key requirements:** Real-time? Heavy data processing? Content-heavy? AI features?
- **Existing infrastructure:** Any cloud providers, databases, or frameworks already committed?
- **Experience level:** What technologies does the team already know?

In `--non-interactive` mode, use whatever context was passed in the argument and record unanswered questions in `awaiting_user_review`.

### 2. Detect Existing Stack (if `--existing`)

Issue parallel Reads for project markers:
- `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`
- `tsconfig.json`, `next.config.*`, `astro.config.*`, `vite.config.*`
- `prisma/schema.prisma`, `drizzle.config.*`
- `tailwind.config.*`, `postcss.config.*`
- Deployment markers: `wrangler.toml`, `fly.toml`, `vercel.json`, `netlify.toml`, `Dockerfile`

Assemble an `existing_stack_json` object to pass to the stack-advisor.

### 3. Apply the Golden Path Matrix

Load `references/golden-path-matrix.md`.

Apply the AI-Native Proficiency Tiers and Project-Type Decision Matrix from the reference to select the right stack. Prefer Primary tier technologies unless the project has specific requirements that justify Secondary or lower tiers.

### 4. Dispatch Stack Advisor

Use the Agent tool to delegate to the `stack-advisor` agent with the substituted template from `references/subagent-prompts/stack-eval.md`. Pass:
- `project_context` (from Step 1)
- `mode` (`new_project` | `evaluate_existing` | `compare_frameworks`)
- `existing_stack_json` (from Step 2, if applicable)
- `frameworks_to_compare` (if user specified frameworks to compare)

The stack-advisor will:
- Use Context7 MCP (if available) to fetch current framework documentation
- Use WebSearch to verify current stable versions and recent breaking changes
- Check compatibility between all recommended components
- Confirm no known security vulnerabilities in recommended versions
- Return JSON per the `stack-eval.md` contract and `stack-eval.schema.json` schema

**Validate the agent's JSON output before consuming:**

```bash
echo "$AGENT_OUTPUT" | python3 ${plugin_root}/scripts/validate-json.py \
  ${plugin_root}/references/subagent-prompts/stack-eval.schema.json - --extract-from-markdown
```

Re-prompt the agent once on schema failure with the validation errors. If a second attempt also fails, fall back to the markdown structure documented in `agents/stack-advisor.md`.

Save checkpoint after Step 4.

### 5. Present Recommendation

Parse the stack-advisor JSON. Present the recommendation table from the JSON's `recommendation[]` array:

| Layer | Recommended | Version | AI Tier | Why |
|-------|-----------|---------|---------|-----|
| Language | TypeScript | 5.x | Primary | [rationale] |
| Frontend | [choice] | [version] | [tier] | [rationale] |
| ... | ... | ... | ... | ... |

Include:
- Alternatives considered and why they were rejected (from `alternatives_considered[]`)
- Compatibility verification results (from `compatibility_notes[]`)
- Any risks or version-pinning recommendations (from `risks[]` and `version_pins`)
- Verification sources (from `verification_sources[]`)

If `escalation_required: true` in the JSON, surface `escalation_reason` directly to the user and recommend rethinking scope via `/rad-brainstormer:brainstorm-session` or `/rad-brainstormer:design-sprint` rather than forcing a stack choice.

### 6. Answer Follow-Up Questions (interactive only)

Be prepared to:
- Justify any choice against a specific alternative the user prefers
- Explain trade-offs between Primary and Secondary tier options
- Provide migration guidance if switching from an existing stack
- Recommend specific libraries within the chosen framework (e.g., which ORM, which auth library)

In `--non-interactive` mode, skip this step and emit the trailing JSON directly.

### 7. Next Steps

After the user accepts the stack recommendation, suggest:
- Run `/rad-planner:plan` to build a full implementation plan using this stack
- Or proceed directly if this was a standalone evaluation

In `--non-interactive` mode, emit:

```json
{
  "evaluation_complete": true,
  "run_id": "string",
  "stack_recommendation": "{... full stack-advisor JSON ...}",
  "escalation_required": false,
  "awaiting_user_review": ["string"]
}
```

## What this skill does NOT do

- Does not test framework choices in your project — it recommends, you validate.
- Does not guarantee the stack is suitable for your specific scale / team / constraints; the rationale is documented but the call is yours.
- Does not migrate an existing stack — `--existing` evaluates fit, doesn't generate a migration plan.

## Key References

- `references/golden-path-matrix.md` — Decision matrix, proficiency tiers, project-type recommendations (date-stamped)
- `references/subagent-prompts/stack-eval.md` — Stack-advisor dispatch template
- `references/subagent-prompts/stack-eval.schema.json` — JSON contract validated before consumption
- `scripts/validate-json.py` — Schema validator

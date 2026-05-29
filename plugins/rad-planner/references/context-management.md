# Context Management: Document & Clear Protocol

AI reasoning quality tends to degrade as context windows fill — observable in longer coding sessions as repeated suggestions, hallucinated paths, and dropped instructions. The exact threshold and mechanism varies by model and workload; the directional effect is widely reported. The planner provides a Document & Clear protocol to mitigate this; the user (or a wrapping skill) must actually invoke `/clear` and rehydrate from the saved file.

## The Document & Clear Pattern

### Step 1: Status Checkpoint (Dump)

There are two complementary state files. Use both for a full handoff:

**Planner-side (this plugin's job — `/checkpoint`):** write `.planner/state/<run-id>.json` per the shared checkpoint schema below. This captures:
- Which skill was in flight (`plan` / `review-plan` / `evaluate-stack`)
- Current phase, run-id, model, codebase context, stack recommendation, risk-history
- Whatever the skill needs to resume mid-flight via `--resume <run-id>`

**Session-side (rad-session's job — `/rad-session:wrapup`):** write `docs/status.md` from evidence (git diff, test output, plan-task state). This captures:
- What actually changed this session, and the latest validation results
- Where you left off, known issues / blockers, and the next recommended step
- The evidence-based reality the next `/rad-session:startup` reads to orient

Per the single-writer rule (see `docs/cross-plugin-contracts.md`), **rad-planner does NOT write `docs/status.md`.** Run `/rad-session:wrapup` *before or after* `/rad-planner:checkpoint` if you want both kinds of state captured.

The two-step idiom is:
```
/rad-planner:checkpoint --run-id <id>    # saves .planner/state/<id>.json
/rad-session:wrapup                      # writes docs/status.md from evidence
/clear
```

For projects that aren't running a planner skill (just executing the plan), only `/rad-session:wrapup` is needed.

### Step 2: Wipe
Run `/clear` to completely reset the session. This erases all conversational context.

### Step 3: Rehydration
Start a fresh session. Point the AI to:
1. `docs/status.md` — the evidence-based reality from the last `/wrapup`
2. The active plan (`docs/planning/current.md`) — the current milestone's intent
3. Any committed changes in the Git branch
4. The operating manual (`CLAUDE.md` / `AGENTS.md`) for conventions

If a `.planner/state/<run-id>.json` file exists for a skill that was in flight, use the skill's `--resume <run-id>` flag instead of re-orienting from scratch.

The AI now operates with a pristine context window, focused only on the next phase of work.

## Shared Checkpoint Schema

All three multi-phase skills (`plan`, `review-plan`, `evaluate-stack`) share a single state file format at `.planner/state/<run-id>.json`:

```json
{
  "run_id": "string",
  "skill": "plan | review-plan | evaluate-stack",
  "phase": "string — skill-specific phase identifier",
  "started_at": "ISO-8601",
  "last_saved": "ISO-8601",
  "model": "opus | sonnet | haiku",
  "project_summary": "string",
  "codebase_context": {
    "root": "string",
    "claude_md_present": false,
    "stack_detected": ["string"]
  },
  "stack_recommendation": "JSON from stack-advisor or null",
  "plan_path": "string or null",
  "tasks_path": "string or null",
  "risk_history": [{"iteration": 1, "verdict": "REVISE", "issue_count": 0}],
  "escalation": {"required": false, "reason": "", "route_to": ""},
  "awaiting_user_review": ["string"]
}
```

Skills may add skill-specific fields without breaking the shared contract — use additive extension, not renaming. The `checkpoint` skill can read and write this file generically by passing `--run-id`.

## Trigger Conditions

### Mandatory Triggers (Always clear)
| Condition | Why |
|-----------|-----|
| **Task transitions** | Moving between unrelated features prevents context bleed |
| **Milestone completion** | Natural boundary; commit, celebrate, reset |
| **After 2 consecutive failures** | Context is polluted with failed approaches; fresh start needed |
| **Major topic change** | Database refactoring context should never bleed into UI work |

### Warning Triggers (Clear soon)
| Condition | Why |
|-----------|-----|
| **Approaching context capacity** | Reasoning quality begins degrading well before the hard limit |
| **Agent starts repeating itself** | Sign of attention mechanism losing earlier instructions |
| **Responses getting vague** | Model losing grip on specific details |
| **Unexpected suggestions** | AI proposing things outside the plan scope |

### Critical Trigger (Clear immediately)
| Condition | Why |
|-----------|-----|
| **Agent stuck in correction loop** | 2+ failed attempts = polluted context. STOP. Clear. Restart. |
| **Auto-compaction triggered** | The runtime silently summarizes history near capacity — lossy and unpredictable |
| **Agent hallucinating file paths or APIs** | Confidence in non-existent code = context corruption |

## Context Budget Rules

### Session Duration
- **Target:** 30-45 minute focus sessions
- **Maximum:** One bounded task per session
- **Rule:** Better to clear too early than too late

### What to Keep in Active Context
- The current phase of the plan (not the entire plan)
- Files being actively modified (not the whole codebase)
- Relevant test files for the current task
- The task's validation criteria and rollback procedure

### What to Externalize
- Completed work summaries (commit to git; surfaced in `docs/status.md` at `/wrapup`)
- Architecture decisions (store in `docs/decisions/`)
- Stack/library choices and conventions (store in the operating manual / `docs/architecture.md`)
- Full project plan (store in `docs/planning/current.md`, load only the current milestone)

## Dynamic Context Loading

Instead of hardwiring everything into CLAUDE.md (burns tokens on every message), store detailed references in separate files and load them on demand:

```markdown
## References (load when needed)
@docs/ARCHITECTURE.md — Read when: modifying system architecture
@docs/API.md — Read when: adding or modifying API endpoints
@references/golden-path-matrix.md — Read when: evaluating tech stack choices
```

This "progressive disclosure" pattern keeps the active context lean while making deep knowledge available when needed.

## Handoff Document

The canonical session handoff is `docs/status.md`, owned by rad-session (not rad-planner). See:
- `docs/status-md-schema.md` for the 8-section schema and per-field inference policy
- `plugins/rad-session/skills/wrapup/SKILL.md` for how it's populated from evidence

The `.planner/state/<run-id>.json` schema is documented above ("Shared Checkpoint Schema"). That's the only state file rad-planner writes directly.

## Integration with Plan Checkpoints

`docs/planning/current.md` is milestone-based, with a stop-and-checkpoint boundary at each milestone. Each checkpoint should:
1. Run the milestone's validation commands and check acceptance criteria
2. Commit all verified work to git
3. Update `.planner/state/<run-id>.json` if a planner skill is in flight (rad-planner's responsibility)
4. Run `/rad-session:wrapup` to write `docs/status.md` from evidence (rad-session's responsibility — keeps the single-writer rule intact)
5. Assess context usage — if approaching capacity, dump state, recommend `/clear`, provide rehydration instructions
6. If context is healthy: continue to the next milestone

# Context Management: Document & Clear Protocol

AI reasoning quality tends to degrade as context windows fill — observable in longer coding sessions as repeated suggestions, hallucinated paths, and dropped instructions. The exact threshold and mechanism varies by model and workload; the directional effect is widely reported. The planner provides a Document & Clear protocol to mitigate this; the user (or a wrapping skill) must actually invoke `/clear` and rehydrate from the saved file.

## The Document & Clear Pattern

### Step 1: Status Checkpoint (Dump)
Before clearing, instruct the AI to write a handoff document capturing:
- **Completed milestones** — what's done and verified
- **Current state** — what files were modified, what's in progress
- **Open decisions** — unresolved questions that need human input
- **Traps to avoid** — approaches that were tried and failed (TRIED / FAILED BECAUSE / CORRECT APPROACH format)
- **Immediate next steps** — exactly what to do when resuming

Save to: `HANDOFF.md`, `activeContext.md`, or `SCRATCHPAD.md`.

For active skill runs, also save to `.planner/state/<run-id>.json` per the shared checkpoint schema below. This enables `--resume <run-id>` on `plan`, `review-plan`, and `evaluate-stack`.

### Step 2: Wipe
Run `/clear` to completely reset the session. This erases all conversational context.

### Step 3: Rehydration
Start a fresh session. Point the AI to:
1. The saved handoff document
2. The master plan (`PLAN.md` in RAD 3.0+, or `implementation_plan.md` in v2.x legacy projects)
3. Any committed changes in the Git branch
4. The project's CLAUDE.md for conventions

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
- Completed work summaries (commit to git, reference in handoff)
- Architecture decisions (store in `decisions.md`)
- Stack/library choices (store in `CLAUDE.md`)
- Test strategies (store in `TESTING.md`)
- Full project plan (store in `PLAN.md`, load only current phase)

## Dynamic Context Loading

Instead of hardwiring everything into CLAUDE.md (burns tokens on every message), store detailed references in separate files and load them on demand:

```markdown
## References (load when needed)
@docs/ARCHITECTURE.md — Read when: modifying system architecture
@docs/API.md — Read when: adding or modifying API endpoints
@references/golden-path-matrix.md — Read when: evaluating tech stack choices
```

This "progressive disclosure" pattern keeps the active context lean while making deep knowledge available when needed.

## Handoff Document Template

```markdown
# Session Handoff — [Date] [Time]

## Status
**Phase:** [Current phase name]
**Milestone:** [M1/M2/etc.]
**Last completed task:** [Task ID and title]
**Next task:** [Task ID and title]
**Active run:** [run-id if a planner skill was in flight, else "none"]

## What Changed This Session
- [File 1]: [What was done]
- [File 2]: [What was done]
- Committed as: [commit hash or "uncommitted"]

## Open Decisions
- [ ] [Decision needed about X — context: Y]

## Traps (Do NOT Retry)
- **TRIED:** [Approach A]
  **FAILED BECAUSE:** [Specific reason]
  **CORRECT APPROACH:** [What to do instead]

## To Resume
1. Read this file
2. If active run-id exists: `/rad-planner:<skill> --resume <run-id>`
3. Otherwise: read PLAN.md, focus on Phase [N]
4. Start with task [ID]: [title]
5. Run `[validation command]` to verify current state
```

## Integration with Plan Checkpoints

The plan template includes checkpoints after every milestone. Each checkpoint should:
1. Run all validation checks for completed tasks
2. Commit all verified work to git
3. Generate/update the handoff document
4. If a planner skill is in flight, update `.planner/state/<run-id>.json`
5. Assess context usage — if approaching capacity, dump state, recommend `/clear`, provide rehydration instructions
6. If context is low: continue to next phase

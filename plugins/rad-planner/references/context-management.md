# Context Management: Document & Clear Protocol

AI reasoning quality tends to degrade as context windows fill — observable in longer coding sessions as repeated suggestions, hallucinated paths, and dropped instructions. The exact threshold varies by model and workload; the directional effect is widely reported. A plan should be structured so work can be done in bounded sessions with clean context boundaries between milestones. The planner builds those boundaries into the plan; the executor (or a wrapping skill) actually invokes `/clear` and rehydrates.

This reference informs two things: the **Checkpoints** section the planner writes into `plan.md` (a stop-and-clear boundary after every milestone), and the `risk-assessor`'s context-management pass (is each milestone small enough to finish in one bounded session?).

## The Document & Clear Pattern

### Step 1: Checkpoint (Dump)

At a milestone boundary: run the milestone's `Validate` commands, confirm each task's `Done when`, and commit all verified work to git. The commit history plus `plan.md` are the durable record — nothing needs to live only in the conversation.

### Step 2: Wipe

Run `/clear` to reset the session. This erases conversational context.

### Step 3: Rehydration

Start a fresh session pointed at:
1. `docs/planning/plan.md` — the plan; load the current milestone and its tasks, not the whole file
2. The committed changes on the Git branch
3. The operating manual (`CLAUDE.md` / `AGENTS.md`) for conventions, if the project has one

The agent now operates with a clean context window, focused only on the next milestone.

## Trigger Conditions

### Mandatory (Always clear)
| Condition | Why |
|-----------|-----|
| **Milestone completion** | Natural boundary; commit, reset |
| **Task transitions between unrelated areas** | Prevents context bleed |
| **After 2 consecutive failures** | Context is polluted with failed approaches |
| **Major topic change** | Database-refactor context should not bleed into UI work |

### Warning (Clear soon)
| Condition | Why |
|-----------|-----|
| **Approaching context capacity** | Reasoning degrades well before the hard limit |
| **Agent repeating itself** | Attention losing earlier instructions |
| **Responses getting vague** | Model losing grip on specifics |
| **Unexpected suggestions** | Proposing things outside plan scope |

### Critical (Clear immediately)
| Condition | Why |
|-----------|-----|
| **Stuck in a correction loop** | 2+ failed attempts = polluted context. Stop. Clear. Restart. |
| **Auto-compaction triggered** | The runtime silently summarizes near capacity — lossy |
| **Hallucinating file paths or APIs** | Confidence in non-existent code = context corruption |

## Context Budget Rules

### Session duration
- **Target:** one bounded milestone per session
- **Rule:** better to clear too early than too late

### Keep in active context
- The current milestone (not the whole plan)
- Files being actively modified (not the whole codebase)
- Relevant test files for the current task
- The task's `Validate` and `Rollback`

### Externalize
- Completed work → commit to git
- Durable facts the planning conversation surfaced (product behavior, decisions, architecture) → the update-prompt, for the user to record in the durable docs (the planner does not write those)
- The full plan → `docs/planning/plan.md`; load only the current milestone

## Sizing for context (what the risk-assessor checks)

A milestone that can't finish inside one bounded session is too big. The plan's size discipline (2–3 tasks per milestone, ~50% context budget) exists so each milestone fits a clean session with room for the inevitable back-and-forth. A milestone carrying more than ~5 tasks is a split candidate. Each milestone gets a Checkpoint in `plan.md` with its own gate / validate / rollback — that's the stop-and-clear boundary.

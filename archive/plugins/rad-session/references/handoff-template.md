# HANDOFF.md template (retired in v5.0)

`HANDOFF.md` is retired as of rad-session 5.0. Its session-tier handoff role is replaced by `docs/status.md` — a project-scoped, evidence-based status document owned by rad-session's `/wrapup`.

The canonical schema for the new artifact lives at the repo root:

→ **[`docs/status-md-schema.md`](../../../docs/status-md-schema.md)** — `docs/status.md` 8-section schema (canonical source)
→ **[`docs/doc-conventions.md`](../../../docs/doc-conventions.md)** — full doc structure
→ **[`docs/cross-plugin-contracts.md`](../../../docs/cross-plugin-contracts.md)** — `docs/status.md` is owned by rad-session; rad-planner reads it

## Why the change

v4.0's `HANDOFF.md` was session-scoped (overwritten each wrapup) and synthesis-based (the LLM summarized the conversation). Two structural problems:

1. **Session-scoped state is fragile** — a single bad wrapup wiped the previous handoff. `docs/status.md` is project-scoped: it persists across milestones and accumulates evidence.
2. **Synthesis is unreliable** — what the LLM remembers from a 200-turn conversation isn't the same as what actually changed. v5.0 `/wrapup` writes `docs/status.md` from **evidence** (git diff, test output, plan-task state) — not chat synthesis.

## If your project still has HANDOFF.md

It's no longer read or written by rad-session. You can archive or delete it. The structural lesson — capture failed approaches explicitly — lives on in v5.0's `docs/status.md` "Decisions made during execution" and "Known issues or blockers" sections.

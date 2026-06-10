---
name: design-sprint
description: >
  Design this, create a spec, design sprint, architecture for this, write a design doc.
  Post-ideation: architecture, components, data flow, error handling, testing. Not for
  ideation — use brainstorm-session for that.
---

# Software Design Sprint

Turn a chosen software approach into a complete, reviewable design spec ready for implementation planning.

**Prerequisite:** The user has already decided WHAT to build (either through brainstorm-session or by coming in with a clear idea). This skill handles HOW to design it.

<HARD-GATE>
Do NOT write any code, scaffold any project, or invoke any implementation tool until the design is approved by the user. This is a DESIGN skill, not an implementation skill.
</HARD-GATE>

## Execution: parallel-first

- **Step 1 context exploration** — file reads, recent commits, and related spec discovery have no inter-step dependencies. Batch them.
- **Step 5 unit isolation exploration** — if the design references multiple existing components or specs, Read them in parallel.
- **Step 8 spec review loop** — iterations are sequential (each depends on the prior iteration's fixes), but any file reads within an iteration are parallel.
- **Always serialize:** the per-section approval loop in Step 6 (user must respond before the next section). In `--non-interactive` mode, skip approvals and mark unconfirmed sections in `awaiting_user_review`.

## Mode Flags

This skill honors two mode flags when passed in the invocation:

- `--non-interactive` — Skip user-approval gates. Produce a best-effort design doc, write it to the default in-project path (no commit), and emit a trailing JSON block listing `awaiting_user_review` items. For agent/CI callers that deadlock on interactive menus.
- `--resume <run-id>` — Load checkpoint state from `.brainstorm/state/<run-id>.json` and continue from the last saved step.

## Checkpoint & Resume

Save state to `.brainstorm/state/<run-id>.json` at these transitions:

1. After Step 1 (context explored) and Step 2 (scope confirmed)
2. After Step 5 (isolation units mapped)
3. After each section in Step 6 is approved (incremental — compaction during long specs is common)
4. After Step 7 (spec written to disk)
5. After each Step 8 spec-review iteration

Checkpoint schema is the same as `brainstorm-session` (see that skill for the full JSON shape) with `skill: "design-sprint"` and phase values `1 | 2 | 5 | 6-<section> | 7 | 8-iter-N`.

On `--resume <run-id>`, load the file, announce the step you're resuming from, and continue without re-running completed steps.

## Checklist

Complete these steps in order:

1. **Explore project context** — Check files, docs, recent commits (including `docs/design.md` if present — that file is the project's brand / UI/UX design direction; honor it as a constraint, never write to it)
2. **Confirm scope** — Verify the chosen approach with the user. If they haven't chosen, route them back to brainstorm-session.
3. **Ask clarifying questions** — One at a time, focused on technical design decisions
4. **Design for isolation** — Break into units with clear boundaries and interfaces
5. **Present design sections** — One section at a time, get approval after each:
   - Architecture overview
   - Component breakdown
   - Data model / flow
   - API design (if applicable)
   - Error handling strategy
   - Testing strategy
   - Migration / deployment considerations (if applicable)
6. **Write design doc** — Deliver as one self-contained file; ask where (see "Delivering the spec" below)
7. **Spec review loop** — Dispatch spec-reviewer agent; fix issues and re-dispatch until approved (max 5 iterations)
8. **User reviews spec** — "Spec written to `<path>`. Please review and let me know about any changes."
9. **Transition** — Hand off to `/rad-planner:plan` for implementation planning (see "After the Design" below)

## Design Principles

### Design for Isolation and Clarity
- Break the system into smaller units that each have one clear purpose
- Units communicate through well-defined interfaces
- Each unit can be understood and tested independently
- Ask for each unit: what does it do, how do you use it, what does it depend on?
- Can someone understand what a unit does without reading its internals?
- Can you change internals without breaking consumers?
- When a file grows large, that's a signal it's doing too much

### Follow Existing Patterns
- Explore the current codebase structure before proposing changes
- Follow existing conventions (naming, file organization, testing patterns)
- Where existing code has problems that affect the work, include targeted improvements
- Don't propose unrelated refactoring

### YAGNI
- Remove unnecessary features from all designs
- Don't add configurability that hasn't been requested
- Don't design for hypothetical future requirements
- The right amount of complexity is the minimum needed for the current task

## Asking Questions

- One question per message
- Prefer multiple choice when the options are known
- Focus on decisions that affect the design (not implementation details)
- If a topic needs more exploration, break it into multiple questions

## Presenting the Design

- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
- Ask after each section whether it looks right
- Be ready to go back and revise if something doesn't make sense

## After the Design

### Delivering the spec
One self-contained markdown file — ask the user where, with two sensible options:

- **Into the project** (the usual choice): a dated doc under `docs/` (suggest
  `docs/YYYY-MM-DD-<topic>-spec.md`), with a header marking it **transient**:
  *"Design spec — consumed by `/rad-planner:plan`; archive after planning."* The
  repo's doc-hygiene tooling (rad-repo-manager) will later flag it for archiving —
  that's the designed lifecycle. **Never** write to `docs/design.md`: that file is
  the project's brand / UI/UX design direction, not a technical spec.
- **Personal folder** (pre-repo projects): suggest
  `~/Documents/Brainstorms/YYYY-MM-DD-<topic>-spec.md`; on Claude Desktop / Cowork,
  also surface the file so it can be saved or downloaded directly.

Use clear, concise language. Never auto-commit — the user commits via their normal flow.

### Spec Review Loop

Dispatch the `spec-reviewer` agent with the substituted `references/subagent-prompts/spec-review.md` template, passing the current `iteration` and `max_iterations` (default 5) and any prior iteration's `blocking_issues`. Parse the JSON response:

- `status: approved` → proceed to user review gate
- `status: issues_found` and `iteration < max_iterations` → fix the blocking issues, increment iteration, re-dispatch
- `escalation_required: true` (or `iteration >= max_iterations` with issues remaining) → **stop looping**. Surface the `unresolved_issues` JSON to the user with: "Spec review hit iteration cap with unresolved issues. Please decide: (a) accept these as known gaps, (b) rewrite the affected sections yourself, or (c) drop back to Step 5 to redesign." In `--non-interactive` mode, keep the current spec on disk and add the unresolved issues to `awaiting_user_review`.

Markdown fallback is accepted from the agent — parse best-effort if JSON is missing.

### User Review Gate
> "Spec written to `<path>`. Please review it and let me know if you want to make any changes before we start the implementation plan."

Wait for user response. If changes requested, make them and re-run spec review.

### Transition
Hand off to `/rad-planner:plan` to turn the approved spec into a release-map implementation plan with risk review — its discovery interview pre-fills from the spec, so the user won't be re-asked what the spec already answers. If `rad-planner` is not installed, surface this to the user and suggest installing it, or let the user invoke their preferred implementation-planning workflow.

Do NOT invoke frontend-design, mcp-builder, or any other implementation skill directly from design-sprint — implementation planning is a separate, reviewable phase.

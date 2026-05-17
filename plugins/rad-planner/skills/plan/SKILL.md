---
name: plan
description: >
  This skill should be used when the user says "plan my project", "create an
  implementation plan", "help me architect this", "I need a plan before coding",
  "let's plan before we build", "improve my plan", "deepen the current
  milestone", "continue the plan", "continue planning", "let's continue
  planning", "continue the planning session", "pick up the plan", "where did we
  leave off in the plan", "where did we leave off planning", "continue from
  where we left off" (when planning context is implied), "keep planning",
  "let's keep going on the plan", "resume the plan", "what's drifted from the
  plan", "are we sticking to the plan", "we're pivoting", "rescope this
  project", "scope creep check", "validate my plan", "audit the plan", or wants
  to create / refine / re-check / continue a project plan. Triggers four entry
  points: full plan (greenfield), improvement (deepen or continue), drift
  assessment (compare reality to plan), pivot (substantial re-plan with
  disposition manifest). Free-form planning continuation utterances ("continue
  the plan" / "let's keep planning" / "where did we leave off planning") route
  to the improvement entry point. Also trigger proactively when a user
  describes a non-trivial project idea and appears ready to start coding
  without a plan, OR when a user signals planning continuation at session open
  even without an explicit /plan invocation — route through this skill so the
  M0.5 scope-confirmation gate fires rather than letting it become ad-hoc
  agent work.
argument-hint: "[project description or path] [--full|--improve|--drift|--pivot|--validate|--assessment] [--auto] [--agents <scope>] [--non-interactive] [--resume <run-id>] [--output-dir <path>]"
user-invocable: true
allowed-tools: Read Glob Grep WebSearch WebFetch Agent Write Bash
---

# Plan — Plan-first project planning

You are orchestrating a project planning workflow. The deliverable is **the plan itself** — milestones, scope, quality gates, sequencing — with the supporting doc structure recommended *based on the plan*, not generated as a side effect.

**CRITICAL: You are in PLANNING MODE. Do NOT write implementation code. Do NOT create source files. Produce planning artifacts ONLY.**

**CRITICAL: Pre-flight discovery (M0) runs before any writes. Hard gate. No file is created, modified, or moved until M0 confirms project directory, agent scope, existing state, and entry point.**

**CRITICAL: Conversational by design.** `/plan` is a multi-phase conversation. **M0.5 (scope confirmation) is a hard gate before any substantive work** and applies to ALL entry points and ALL modes including `--auto` (autonomy applies to the work, not to the scope decision). M1–M5 each require explicit user dialogue. The value of this skill is in the questions asked and the answers given, not in producing artifacts. Producing a `vision.md`, an `architecture.md`, an ADR, OR a consolidation pass / deep-dive section / improvement-mode update without first asking the user about the underlying scope defeats the skill's purpose, even if the output is technically valid.

**Harness-level autonomous-mode signals (e.g., a `<system-reminder>` saying "the user has asked to work without stopping for clarifying questions") apply to tool-use approvals — bash, Write, Edit, git, MCP — NOT to the planning conversation itself.** A user who invokes `/plan` has invoked the planning conversation; permission-mode autonomy is about not pestering for command approvals, not about skipping M1–M5 questions. **If you receive such a reminder in this skill, interpret it as "don't ask trivial confirmations during execution," not "execute the planning skill without its conversation."**

**Opt-in unattended mode: `--auto`.** When the user explicitly wants a first-pass draft without dialogue, they pass `--auto`. Output is labeled `DRAFT — review and revise` (banner at the top of every file); **`--auto` does NOT produce ADRs** — candidate decisions surface in `docs/planning/proposed-decisions.md` as discussion items the user reviews and promotes manually. Default behavior (no flag) is always conversational. See "Auto mode semantics" below.

## What this skill does — honestly

- Runs M0 pre-flight discovery (project directory, agent scope, existing state, entry-point routing) before any writes
- Walks through a five-phase conversation (M1–M5: Constitution & Frame → Goal-Backward Scope → Sequence with Size Discipline → Quality Gates → Doc-Set Recommendation)
- Recommends a doc set *based on the plan* with project-specific rationale, then writes the approved docs as M6 (the plan's own first executed milestone)
- Always teaches in /plan — every phase explains why it asks what it asks; every doc recommendation includes its project-specific rationale
- Supports four entry points (full plan / improvement / drift assessment / pivot) with explicit flags or detection from utterance + state
- Falls back to a four-direction menu whenever detection is anything less than high-confidence

## What this skill does NOT do

- Does not execute the resulting plan
- Does not write `docs/status.md` content beyond a scaffold — rad-session populates from evidence at /wrapup
- Does not touch code — flags code paths for human cleanup during pivot disposition
- Does not write files outside the M0-determined project directory — never writes to cwd without confirmation
- Does not detect every anti-pattern; mechanical validators (`plan-lint.py`, `doc-redundancy.py`, `doc-contradiction.py`) catch field presence, DAG integrity, vague language, cross-doc duplication, and cross-doc disagreements. The risk-assessor agent handles judgment-required anti-patterns and architectural concerns.

## Cross-model note

This skill works across Opus 4.7, Sonnet 4.6, and Haiku 4.5. Opus/Sonnet handle parallel batching reliably; Haiku may follow phase order sequentially. The plan output, JSON contracts, and validator scripts are identical regardless of model.

## Mode flags

- `--full` — Greenfield entry; start from scratch
- `--improve` — Improvement entry; deepen or continue existing plan (sub-branch always-asked: continue vs deepen)
- `--drift` — Drift assessment entry; compare current state against plan, produce report
- `--pivot` — Pivot entry; substantial re-plan with disposition manifest
- `--validate` — Utility; run validators on existing plan artifacts, no conversation
- `--assessment` — Utility; **state-of-project read-only assessment**, no conversation, no writes. Distinct from `--drift` (which requires an existing plan to compare against): `--assessment` does NOT require a plan and does NOT produce a plan. It runs the internal assessor pass over whatever evidence exists (git history, existing docs, source structure, validator results) and emits a structured report describing what's there, what's missing, what's stale, and where the project sits relative to the canonical doc structure. Useful before deciding which entry point to invoke (full / improve / drift / pivot). Read-only — does not write to `docs/` or any project file.
- `--auto` — **Unattended mode.** Produces a first-pass DRAFT without M1–M5 dialogue. All output files get a `> **DRAFT — review and revise**` banner; **ADRs are NOT written under `--auto`** — candidate decisions land in `docs/planning/proposed-decisions.md` for user review. Default behavior is conversational; `--auto` is opt-in.
- `--agents <scope>` — Set agent scope without prompting (`claude_only` | `codex_only` | `claude_and_codex`)
- `--non-interactive` — Best-effort run without approval gates; emits trailing JSON with `awaiting_user_review` items. **Distinct from `--auto`:** `--non-interactive` is for CI / scripted runs (machine-readable output, no prompts); `--auto` is the user-facing flag for "produce a strawman I can react to."
- `--resume <run-id>` — Continue a saved planning session from `.planner/state/<run-id>.json`
- `--output-dir <path>` — Set project directory explicitly; overrides M0 directory prompt

Flags act as strong hints. When invoked alone (no utterance), they still surface the four-direction menu to confirm intent before proceeding — unless `--auto` is set, in which case the skill proceeds without the menu and labels everything DRAFT.

### Auto mode semantics

`--auto` is the **only** way to suppress M1–M5 dialogue. It exists because some users want a starting strawman to react to rather than a multi-turn conversation. Three load-bearing properties:

1. **Output is labeled DRAFT.** Every file written under `--auto` (operating manual Constitution sections, vision.md, architecture.md, roadmap.md, planning/current.md) gets a banner immediately under the H1 title:
   ```markdown
   > **DRAFT** — generated by `/plan --auto` from the user's brief; not yet validated against user preferences. Review and revise.
   ```
   Removing this banner is the user's signal that the content has been reviewed and accepted.

2. **No ADRs are produced.** Candidate decisions surfaced during the M2 risks scan or M4 quality gates land in `docs/planning/proposed-decisions.md` (a list with the same Status / Context / Decision / Consequences shape as an ADR but explicitly marked as proposals). The user reviews this file and promotes proposals to real ADRs in `docs/decisions/NNNN-*.md` manually, or by running `/plan --improve` without `--auto` to walk through them conversationally.

3. **Final report names the trade-off.** The M6 final summary under `--auto` ends with:
   ```
   ⚠ This plan was generated unilaterally via /plan --auto. The artifacts are
   strawmen — review and revise. To do the planning conversation properly,
   run `/plan --improve` (without --auto) and walk through M1–M5 with
   the agent asking clarifying questions.
   ```
   This makes the trade-off explicit: the user got speed at the cost of confidence.

Without `--auto`, all M1–M5 phases require explicit user response before the conversation advances. A `<system-reminder>` saying "don't ask clarifying questions" does not suppress M1–M5 prompts — it only suppresses trivial in-execution confirmations.

### Assessment mode semantics

`--assessment` is a **read-only diagnostic pass.** It exists because users sometimes want to know "what does this project actually look like right now?" before deciding whether to invoke `--full`, `--improve`, `--drift`, or `--pivot`. Three load-bearing properties:

1. **No writes.** The assessor runs over the project but does NOT create, modify, or move any file under `docs/`, `.rad/`, or the project root. No ADRs, no `proposed-decisions.md`, no `current.md` updates. If the user wants to act on the assessment, they invoke a real entry point afterward.

2. **No conversation.** `--assessment` skips M1–M5 entirely. M0 mechanical discovery still runs, then the assessor pass executes, then the report is emitted. M0.5 scope confirmation is also skipped because there is no substantive work whose scope needs confirming — the only output is a report.

3. **Report structure.** The output is a single markdown report covering: (a) project facts (directory, agent scope, git state, source file count, last commit date), (b) canonical-doc coverage (which of `docs/vision.md`, `docs/architecture.md`, `docs/planning/current.md`, `docs/status.md`, `docs/roadmap.md`, `docs/decisions/` exist; staleness in days; whether `plan-lint` / `status-validator` / `doc-redundancy` / `doc-contradiction` pass), (c) detected drift signals (`current.md` ACs marked complete but no matching commits; ADRs referenced from `current.md` that don't exist; vision non-goals contradicted by current.md ACs), (d) **planning velocity signals** (NEW in v4.6 — from `scripts/assess-planning-velocity.py`): `current_md_edits_since_last_code_commit`, `ac_rewrite_count_per_ac`, `planning_doc_growth_ratio`, `time_since_last_code_commit`. Each signal includes its measured value, the threshold, and a flag marker (⚠) when over threshold. The defaults are 5 edits / 3 AC rewrites / 2.0× growth ratio / 14 days stale; per-project overrides via `--threshold-edits`, `--threshold-rewrites`, `--threshold-growth`, `--threshold-stale-days`, `--window-days`. (e) inferred next-step suggestion (one of: run `--full`, run `--improve`, run `--drift`, run `--pivot`, or "current state is healthy, no planner action needed") with one sentence of rationale. Velocity signals feed the suggestion: when `time_since_last_code_commit` and `current_md_edits_since_last_code_commit` both flag, recommend executing the current plan rather than further refinement.

`--assessment` is the right flag when the user asks "where does this project stand?" or "what's the state of planning here?" without yet committing to a specific entry point.

## M0: Pre-flight Discovery

M0 establishes four things before any writes:

1. Project directory
2. Agent scope
3. Existing state
4. Entry point

**No file is created, modified, or moved until M0 completes.** Hard gate.

### Sub-step 0a: Project directory

Determine where the project lives. Three answer paths:

- **here** — cwd is the project root
- **named path** — user provides an explicit path that exists
- **doesn't exist** — user wants to plan a project at a path that doesn't exist yet; planner offers to create

**Detection order:**

1. If `/plan` was invoked with `--output-dir <path>` → use that as project directory; validate
2. If user's invocation text references a path like "plan my project at /foo" → infer, confirm with user
3. Otherwise → ASK explicitly:

> "Where does this project live?
> 1. Here (cwd: `<resolved absolute path>`)
> 2. A specific path I'll provide
> 3. The project doesn't exist yet — create it at a path I'll provide"

**Validation rules:**

- Resolve to absolute path
- If user picked option 3 (doesn't exist) → confirm `"Create directory at <path>?"` before any `mkdir`
- If path exists but isn't writable → surface error and ask again
- Save `discovery_state.project_dir` as the absolute path
- **Never write outside this path.** Hard rule for all downstream phases.

### Sub-step 0b: Agent scope

Determine which coding agents will use this project.

**Detection order:**

1. If `.rad/profile` exists at project dir with `agent_scope` set → use that, skip prompt
2. If user invoked with `--agents <scope>` → use that
3. Otherwise → ASK:

> "Which coding agents will use this project?
> 1. Claude only (CLAUDE.md canonical)
> 2. Codex only (AGENTS.md canonical)
> 3. Both Claude and Codex (AGENTS.md canonical with CLAUDE.md as `@AGENTS.md` shim)
> 4. Not sure yet — defaults to Claude only (this is a Claude plugin); can change later"

Save `discovery_state.agent_scope`. Defaults to `claude_only` if user is unsure — rad-planner is a Claude plugin, Claude-native is the right default. Later runs can change scope.

### Sub-step 0c: Existing state detection

Mechanical read-only inspection of the project directory. No writes. Computes a feature vector that downstream phases consume:

| Field | Type | Source |
|---|---|---|
| `has_git` | bool | `.git/` exists with at least 1 commit |
| `commit_count` | int | `git rev-list --count HEAD` |
| `source_file_count` | int | code files, excluding `node_modules/`, `.venv/`, `dist/`, `build/`, `target/`, `.pytest_cache/`, `__pycache__/`, similar |
| `has_operating_manual` | bool | `CLAUDE.md` or `AGENTS.md` exists with >500 bytes |
| `claude_init_residue` | bool | `CLAUDE.md` exists AND <500 bytes AND no `@AGENTS.md` line AND no `## Compact Instructions` section |
| `codex_init_residue` | bool | `AGENTS.md` exists AND <500 bytes AND matches Codex `/init` scaffold pattern |
| `has_strategic_docs` | bool | `docs/vision.md` OR `docs/architecture.md` exists |
| `has_planning_current` | bool | `docs/planning/current.md` exists with substantive content (>500 bytes) |
| `has_status` | bool | `docs/status.md` exists with populated fields (>500 bytes) |
| `planning_current_progress` | enum | none / partial / complete (acceptance-criteria checkbox state in current.md) |
| `recent_activity_spread` | enum | focused / mixed / diffuse (overlap of recent commits with current.md planned changes) |
| `status_freshness` | enum | fresh / moderate / stale |

**Heuristic specifics:**

- `recent_activity_spread`: take last `min(20, commits_since_status_mtime)` commits → set of changed files → overlap against current.md's "Planned changes" file list. `overlap >= 0.6` → focused; `< 0.3` → diffuse; in between → mixed. If "Planned changes" doesn't list specific files, fall back to directory-level match against milestone-referenced areas.
- `status_freshness`: `(head_date − status_mtime < 2 days) AND (commits_since_status < 5)` → fresh; `(> 7 days) OR (commits > 20)` → stale; in between → moderate.
- `claude_init_residue` and `codex_init_residue` are protective signals — when true, M6 enriches existing content rather than overwriting.

Issue parallel reads where possible: operating manual, key strategic docs, package manifest. Save full feature vector to `discovery_state.existing_state`.

### Sub-step 0d: Entry-point routing

Determine which of the four entry points applies. Follow the routing model in `docs/entry-point-routing.md`.

**Tier 1: Explicit flag**

If `/plan` was invoked with `--full`, `--improve`, `--drift`, `--pivot`, `--validate`, or `--assessment`:

- Use the flag as the entry point
- If utterance has substance that confirms → proceed with one-line confirmation: `"Running --improve against the existing plan at milestone 2 of 4. Proceeding."`
- If invocation is bare flag with no utterance → fall through to the four-direction menu to confirm intent with full state context
- **`--assessment` and `--validate` short-circuit early.** Both are read-only utility passes; after M0 mechanical discovery completes, route directly to the assessor (for `--assessment`) or the validator suite (for `--validate`). M0.5 scope confirmation does not fire and M1–M5 do not run.

**Tier 2: Utterance + state detection**

Parse utterance for entry-point keywords (full lists in `docs/entry-point-routing.md`). Compute state prior from the feature vector.

State priors:

- **Greenfield prior:** `has_git == false` OR (`commit_count < 3` AND `source_file_count < 10` AND `has_strategic_docs == false`)
- **Improvement prior:** `has_git == true` AND `has_planning_current == true` AND `planning_current_progress != complete` AND `status_freshness == fresh`
- **Drift / Pivot prior (weak):** existing strategic docs + planning/current.md — primarily utterance-driven
- **Ambiguous-existing prior:** `has_git == true` AND `has_planning_current == false`

State alone reliably distinguishes greenfield from "something exists" but cannot distinguish improvement vs drift vs pivot without utterance.

**Confidence reconciliation:**

- **High confidence** (state + utterance agree) → one-line confirmation: `"Greenfield project — empty directory, planning from scratch. Sound right?"`
- **Moderate confidence** (one strong signal, other absent) → confirmation with rationale: `"I see existing code and an active plan at docs/planning/current.md (milestone 2 of 4, last status update 3 days ago). Treating as improvement — confirming you want to deepen or continue, not pivot or drift-check?"`
- **Low confidence** (signals disagree or absent) → four-direction menu (Tier 3 below)
- **Hard contradiction** (state vs. utterance conflict) → surface explicitly: `"You said 'new project' but I see existing code and docs. Possibilities: starting fresh in a different directory, pivoting on existing work, or treating this code as scaffolding. Which?"`

**Tier 3: Four-direction menu (universal ambiguity fallback)**

When detection is anything less than high-confidence, render the menu verbatim:

```text
Discovery summary:
- Working directory: <project_dir>
- Git: <N commits / no git>
- Code: <N source files>
- Strategic docs: <list found / none>
- Current plan: <milestone X of Y, last updated N days ago / none>
- Status: <fresh / stale / none>
- Operating manual: <content / /init residue / none>

I'm not 100% clear which plan direction you want to take. Which matches?

1. Full plan — Start from scratch. Walk through goal, scope, milestones, quality
   gates; recommend a doc set; produce complete planning artifacts. Use for new
   projects or when existing docs need a full rewrite.

2. Drift assessment — Compare what's been built against what was planned.
   Output is a report, not a new plan. Use when you're not sure if the project
   has gone off course.

3. Improvement — Deepen the existing plan, fill in missing detail, or pick up
   where it left off. Existing docs stay; we add or refine. Use when the plan
   exists but needs more or you're stuck on next steps.

4. Pivot — Substantial re-plan because direction has changed. Existing context
   preserved (archived, not deleted); strategic docs may be revised; current
   plan replaced. Use when the project is shifting meaningfully.

(Run /plan --full, --drift, --improve, or --pivot to skip this question.)
```

User picks → `discovery_state.entry_point` is locked.

**Improvement sub-branch** (only fires when `entry_point == improvement`): always-ask, no detection:

> "Quick check — are we picking up the next thing in the plan (continue from where you left off), or adding detail to what we're already working on (deepen the current milestone)?"

Save `discovery_state.entry_point_sub_branch` (`continue` | `deepen`).

### Sub-step 0e: Save discovery state

Save discovery state to `.planner/state/<run-id>.json` for resume support. Schema:

```json
{
  "run_id": "string",
  "skill": "plan",
  "phase": "0.M0",
  "mode": "full | improve | drift | pivot | validate | assessment",
  "started_at": "ISO-8601",
  "last_saved": "ISO-8601",
  "model": "opus | sonnet | haiku",
  "discovery_state": {
    "project_dir": "/absolute/path",
    "agent_scope": "claude_only | codex_only | claude_and_codex | not_sure_yet",
    "existing_state": {
      "has_git": true,
      "commit_count": 42,
      "source_file_count": 87,
      "has_operating_manual": true,
      "claude_init_residue": false,
      "codex_init_residue": false,
      "has_strategic_docs": true,
      "has_planning_current": true,
      "has_status": true,
      "planning_current_progress": "partial",
      "recent_activity_spread": "focused",
      "status_freshness": "fresh"
    },
    "entry_point": "improvement",
    "entry_point_sub_branch": "deepen",
    "user_utterance": "I want more detail on M2"
  },
  "escalation": {"required": false, "reason": "", "route_to": ""},
  "awaiting_user_review": []
}
```

M0 ends with discovery confirmed and state saved. Downstream phases consume this state and never re-prompt for project directory, agent scope, or entry point unless the user explicitly re-routes.

## M0.5: Scope Confirmation (NEW in v4.2)

> **Hard gate.** After M0 completes silently and before ANY substantive work begins, `/plan` MUST pause and surface what it sees + what it thinks the user wants + offer the user the option to confirm, redirect, or expand scope. **This applies to ALL entry points (full / improve / drift / pivot) and ALL invocation modes including `--auto`.**

### Why this gate exists

`/plan` is conversational by design (per the third top-level CRITICAL block). The M1–M5 dialogue requirement guards against unilateral canonical-doc emission. But there's a second failure mode the M1–M5 gates don't cover: **substantive work in non-canonical shapes** — consolidation passes, deep-dive sections, custom doc updates, improvement-mode work where M5/M6 are parked.

A real-world failure mode: agent runs M0 silently, infers entry-point + scope from project state, then produces a 9-sub-section deliverable for sign-off without confirming the user wanted that depth of work. Each individual inference is reasonable; the cumulative effect overwhelms.

**The fix:** make the discovery summary + scope inference + user-confirmation prompt a single visible gate that fires after M0 and before any M1+ work or substantive output. Same doorman-model logic rad-session's `/startup` Phase 3 uses: confirm the skill ran, surface what it sees, hand the next move back to the user.

### What the gate does

The M0.5 output is a single user-facing surface with three parts:

**Part 1 — M0 discovery summary (terse, factual).** Project, branch + git state, status freshness, resume point if available, agent_scope, entry-point inference.

**Part 2 — Inferred scope.** What the agent thinks the user wants next. One short phrase.

**Part 3 — Three options.** Confirm / redirect / expand-scope, with depth choices where applicable.

### Template (NEW in v4.3 — prose-first briefing pattern)

The M0.5 surface renders as a friendly, layperson-readable briefing matching the doorman model rad-session's `/startup` uses for its Path A / Path B / Path C alternatives. Cross-plugin consistency is a design principle.

```
**Where we left off:** {one short prose sentence summarizing the most recent locked / shipped chunk of work. Plain language. Pulled from status.md §7 "what changed", current.md notes, the brainstorm or planning doc's "Resume point" line, or the most recent shipped milestone in planning/archive.}

**Last accomplishment:** {one or two short prose sentences naming what got done in that chunk. Plain language. Example: "The five decision-rich phases of Bit 17 each got their deep specs locked, and the weather-migration sub-slice was deleted per the Bit 15c revision."}

**Next logical step:** {one short prose sentence describing the inferred next scope in plain English. Example: "Finish the consolidation pass that reconciles the framework with the five locked deep specs before locking the main slice fully."}

**Or you could start with:**
  - {Alternative A — one prose sentence describing a different scope at the same altitude}
  - {Alternative B — one prose sentence describing a different scope or a skip-ahead option}
  - {Alternative C — at least one option that is "skip more planning, execute the next milestone instead" OR "redirect to something else entirely"}

**Mechanical state:** Project: {name} · Branch: {branch} ({clean | N uncommitted}) · Status: {fresh | N days old} ({M commits since}) · Agent scope: {scope} · Entry point: {entry} (inferred from {signal})

**What's the call?** Confirm the next step, pick an alternative, or redirect to something else entirely.
```

### Per-entry-point alternative menus

Populate the "Or you could start with" list with options appropriate to the inferred entry point.

**For `--improve` (deepen or continue):**
- Consistency check only — flag the drift, write nothing.
- Bigger consolidation that also captures route changes, migrations, and a build manifest.
- Skip planning — start building the next milestone now.
- Different milestone or topic — name which one.

**For `--full` (fresh plan):**
- Lite doc set — operating manual + planning/current only.
- Standard doc set — operating manual + vision + planning/current.
- Full doc set — operating manual + vision + architecture + roadmap + current + decisions.

**For `--drift` (assessment, no new plan):**
- Quick scan — diff against planning/current only.
- Full audit — diff against vision + architecture + planning/current.

**For `--pivot` (substantial re-plan):**
- Surgical pivot — disposition manifest only, keep existing docs.
- Full re-plan — fresh five-phase conversation with disposition manifest.

The agent always includes at least one "redirect entirely" option regardless of inferred entry point.

### Rendering discipline (load-bearing — do not drop)

These rules exist because v4.2 M0.5 output rendered too densely in real-world use. The reshape preserves the same gate; the rules preserve the friendlier framing:

1. **Prose, not bullet lists of identifiers.** ADR numbers, bit numbers, schema column names, file paths, and other technical identifiers belong in the **Mechanical state** line, not in the friendly framing. The four briefing lines (Where we left off / Last accomplishment / Next logical step / Or you could start with) must read as plain English.
2. **Readable to someone outside the project's vocabulary.** A reader who doesn't know the project's internal terms should be able to follow each line. If you reach for an abbreviation or a numeric reference to make a sentence work, rewrite at a higher altitude (e.g., "the five decision-rich phases" rather than "M.6 / M.7 / M.8 / M.9 / M.10").
3. **Acknowledge missing context.** If status.md / current.md / brainstorm doesn't yield enough context to summarize cleanly, say so explicitly: "Last accomplishment couldn't be confidently inferred from {sources read} — please confirm before I proceed." Better an honest gap than dense agent-inferred jargon filling the slot.
4. **Briefing first, JSON second.** The prose briefing is the user-facing surface. The JSON discovery state (saved per the schema below) is the machine-readable annex for downstream phases — not a substitute for the prose surface.
5. **No drift audit before the gate.** Do NOT produce a multi-item drift audit, consolidation analysis, or substantive recap of state as part of M0.5. The briefing names the scope and the alternatives in plain language; the actual work (audit, consolidation, etc.) happens after the user confirms which scope they want.

### `--auto` semantics at M0.5

`--auto` is the only mode that bypasses M1–M5 dialogue. **It does NOT bypass M0.5.** Even in `--auto` mode, the M0.5 scope confirmation fires once — because **autonomy applies to the work, not to the scope decision.**

`--auto` + M0.5 behavior:
- M0.5 surfaces the discovery summary + inferred scope as normal
- User confirms scope (or redirects, or expands: "go through Bits 18–22, knock them all out")
- After scope confirmation, `--auto` suppresses every subsequent prompt
- Output is DRAFT-labeled per the v4.1 contract; no ADRs written

This preserves "give me a scope I can react to" as the universal entry behavior. `--auto` is unattended *execution at confirmed scope*, not unattended *scope decision*.

### `--non-interactive` semantics at M0.5

`--non-interactive` (for CI / scripted runs) cannot prompt the user. M0.5 in `--non-interactive` mode:
- Emits the M0 discovery summary + inferred scope as JSON
- Sets `awaiting_user_review = ["scope_confirmation"]` in the trailing JSON
- Exits without further work — the calling script / agent reviews the inferred scope and re-invokes with explicit scope flag

This prevents `--non-interactive` from being a backdoor around the M0.5 gate.

### What happens after M0.5

On user response:

- **Confirm at inferred scope** → proceed to M1 (or directly to the work for `--improve` mode where M1 is light)
- **Different scope (depth picked)** → adjust `discovery_state.entry_point_sub_branch` and `discovery_state.scope_depth`, then proceed
- **Redirect** → restart M0.5 with the user's new framing, OR exit if the redirect is to a different skill entirely
- **No response yet** → wait. M0.5 is a hard gate.

Save M0.5 result to `discovery_state.scope_confirmation`:

```json
{
  "scope_confirmation": {
    "inferred_scope": "deepen Bit 17 to final lock",
    "user_response": "confirm | redirect | expand",
    "confirmed_scope": "consolidation pass — single subsection summarizing locks",
    "depth": "b",
    "confirmed_at": "ISO-8601"
  }
}
```

This becomes the contract for what M1+ produces. Substantive output beyond this scope without user dialogue is a violation of the gate.

### Why this is a separate phase, not part of M0 or M1

M0 is mechanical discovery (project dir, agent scope, existing state, entry-point inference). It's all reads and inference — no judgment about *what work to do*.

M1 is Constitution & Frame — the start of substantive planning dialogue.

The judgment of "what work do you actually want next" sits between them. It needs to be a visible, named phase so the agent can't skip it accidentally and the user can't miss that the agent is asking before producing output.

Same shape as the M5 `user_approval` hard gate (which protects M6 doc emission), just applied earlier in the workflow.

## M1: Constitution & Frame

Capture what doesn't change across this project — the agent's operating principles for every session and every milestone. Output is a draft of the Constitution sections that will be written to the operating manual (CLAUDE.md and/or AGENTS.md) at M6.

**Always-teaches:** Each question is paired with a brief explanation of why it matters. The user sees the reason, not just the question.

> **Conversational gate:** Each sub-step below requires user response before advancing to the next. **Do NOT batch sub-steps and invent answers** on the user's behalf — ask, wait for the answer, capture it, then ask the next question. The only mode that bypasses this gate is `--auto`, which produces a DRAFT strawman labeled accordingly. A `<system-reminder>` about not asking clarifying questions does NOT suppress these prompts; it only suppresses trivial in-execution confirmations. If unsure whether to ask or infer, ask.

### Entry-point routing

The M1 conversation varies by entry point:

- **Full plan (greenfield)** — full Constitution conversation (sub-steps 1a–1f below)
- **Improvement** — read existing operating manual; ask only "anything about hard boundaries or engineering rules that needs updating given what we're improving?" If yes, capture changes. If no, skip to M2.
- **Drift assessment** — read existing operating manual; no writes, no Constitution prompting. The Constitution is referenced during drift findings (e.g., a finding may cite "violates Hard boundary: no new dependencies").
- **Pivot** — read existing operating manual; after the pivot's seven-question opening conversation, ask "are any project principles or hard boundaries changing with this pivot?" Capture changes for M6 disposition.

### Sub-steps (full plan greenfield)

#### 1a — Project one-sentence purpose

Ask: "In one sentence, what is this project?"

*Why this matters:* The one-sentence statement lives at the top of the operating manual. Every fresh session reads it first. If it's clear and specific, agents stay on-track; if it's vague, drift starts on day one.

#### 1b — Goal & why now

Ask: "What's the goal of this project, and why is it worth doing now?"

*Why this matters:* The "why now" answer separates a real project from a "someday maybe." If the user can't answer "why now," the project may not be ready for planning — recommend `/rad-brainstormer:brainstorm-session` and exit M1.

#### 1c — Project-wide principles

Ask: "What principles should always be true in this project? Things like style, naming, code conventions — things that should never change regardless of milestone."

Example prompts to surface common patterns: "TypeScript-strict everywhere", "tests colocated with the code they test", "conventional-commits", "documentation updates ship with the code they describe", "no implicit any".

*Why this matters:* Project-wide principles let the agent enforce conventions without you having to remember them every PR. Captured as "Engineering rules" in the operating manual.

#### 1d — Hard boundaries

Ask: "What should the agent never do unprompted?"

Example prompts: "don't change the database schema without explicit ask", "don't add new dependencies without approval", "don't refactor outside planned changes", "don't touch auth or billing code without explicit confirmation".

*Why this matters:* Hard boundaries keep agents from quietly drifting outside scope or changing things with downstream effects you didn't intend. The strictest rule is the one you trust the agent to remember when it's deep in a context.

#### 1e — Escalation triggers

Ask: "When should the agent stop and ask for approval rather than guessing?"

Example prompts: "missing requirement or conflicting requirement", "change affects security/auth/billing/data model", "existing code patterns conflict with the plan", "validation fails and fix needs scope expansion".

*Why this matters:* Escalation triggers are the inverse of hard boundaries — instead of "never do X," they're "ask before doing X." Especially load-bearing for security, billing, auth, and data-model decisions.

#### 1f — Save Constitution draft

Save to `discovery_state.constitution_draft`:

```json
{
  "constitution_draft": {
    "project_purpose": "<one sentence>",
    "goal": "<what>",
    "why_now": "<rationale>",
    "principles": ["...", "..."],
    "hard_boundaries": ["...", "..."],
    "escalation_triggers": ["...", "..."]
  }
}
```

Save M1 checkpoint to `.planner/state/<run-id>.json`.

`read_order` is derived in M5 once the doc set is recommended. `definition_of_done` is derived in M4 from quality-gate specs. Both are populated into the operating manual at M6.

### Exit criteria

- All 5 questions answered (or explicitly skipped per entry-point logic)
- Constitution draft saved to run state
- User confirms the captured Constitution before M2 begins

### Iteration

User can revise prior answers at any time. If user re-enters M1 mid-conversation (e.g., during M3), restore the prior draft and re-prompt only the changed fields.

## M2: Goal-Backward Scope

> **Conversational gate** — same rule as M1. The goal statement, must-be-true / must-exist / critical-vs-nice items, hardest unknown, derailment risks, and non-goals all require explicit user input. Do NOT infer them from M1 or the user's opening utterance and call it done. `--auto` produces a DRAFT strawman; default mode requires dialogue.

Working backward from the goal, capture what must be true, what must exist, what's critical vs. nice-to-have, the hardest unknown, and what's explicitly deferred. Borrows GSD's goal-backward question scaffold. Risk surfaces here — no separate Risk phase.

**Output:** drafts of vision.md and planning/current.md scope/objective/risks sections. Saved to `discovery_state.scope_draft`. Written to disk in M6.

**Always-teaches:** Each question is paired with a brief "why this matters" explanation.

### Entry-point routing

- **Full plan (greenfield)** — full goal-backward conversation (sub-steps 2a–2f below)
- **Improvement** — skip most sub-steps. Ask focused: "What's the scope of this improvement? Adding what / changing what? Anything new in critical/nice-to-have given this?" Capture changes into existing scope.
- **Drift assessment** — read existing vision.md + planning/current.md scope; no prompting. The scope is referenced when reporting drift findings.
- **Pivot** — the seven-question opening from pivot already establishes most of this. M2 reads pivot conversation outputs into the scope_draft format and asks at most one verification question if anything's still unclear.

### Sub-steps (full plan greenfield)

#### 2a — Goal statement (2–3 sentences)

Ask: "Walk me through what success looks like for this project. What does done look like? Who's it for? What's the vision in 2–3 sentences?"

*Why this matters:* The goal statement is what every milestone is in service of. Without it, scope creep starts because the "why" of each task isn't clear. This becomes the body of vision.md.

#### 2b — Must be TRUE / must EXIST

Ask: "What must be TRUE for this project to be a success — hard requirements, qualities the system must have? And what must EXIST when this is done — tangible artifacts, features, integrations?"

Examples for "must be true": "users can complete the core flow without external help", "data persists across sessions", "load times under 2 seconds", "compliant with [standard]".

Examples for "must exist": "user authentication system", "admin dashboard", "API documentation", "deployment to production".

*Why this matters:* "Must be true" surfaces non-negotiable qualities; "must exist" surfaces non-negotiable tangibles. Together they make scope concrete. These become the acceptance criteria for planning/current.md milestones.

#### 2c — Critical vs. nice-to-have

Ask: "Of everything we've identified, what's CRITICAL and what's nice-to-have? Critical = the project doesn't ship without it. Nice-to-have = improvement we can defer if scope tightens."

*Why this matters:* The critical/nice-to-have split is how the planner protects against scope creep. Nice-to-haves go to roadmap.md's "Next" or "Later" sections; critical items become the focus of current.md.

#### 2d — Hardest unknown + derailment risks

Ask: "What's the hardest unknown going into this work? And what could derail this project beyond the technical unknowns — external dependencies, team constraints, business changes?"

Examples for hardest unknown: "we don't know if [library X] supports our use case at scale", "auth flow with provider Y is documented but no one's done it before", "data migration approach for legacy users".

Examples for derailment risks: "vendor X changing pricing model", "dependency on team Y who has competing priorities", "infrastructure migration mid-project".

*Why this matters:* The hardest unknown becomes the early-risk milestone — solve it first, before committing time to dependent work. Derailment risks go into current.md's Risks section with mitigations. Separating them (technical unknowns vs. external/contextual) keeps the risk model legible.

#### 2e — Non-goals (what's explicitly NOT in scope)

Ask: "What's explicitly NOT in scope for this project? Non-goals that are deliberate, not just unattended."

Examples: "not building a mobile app for v1", "no support for languages other than English", "no real-time collaboration features", "not optimizing for users beyond X concurrent".

*Why this matters:* Non-goals are as load-bearing as goals. Without them, scope expands silently. Land in vision.md's "Non-goals" section AND inform hard boundaries in the operating manual.

#### 2e-park — Parking lot (third option for ambiguous ideas)

> **New in v4.6.** Parking is a *third option* alongside in-scope and non-goal. Offer it when an idea surfaces during 2a–2e that doesn't cleanly fit either.

If during 2a–2e the user raises an idea that isn't a clear must-be-TRUE / must-EXIST / CRITICAL **and** isn't a clean non-goal — surface a third option explicitly:

> "That doesn't sound like it fits this milestone, but I don't think you want to foreclose it either. Three choices:
> 1. **Include in scope** — add to must-be-TRUE / must-EXIST / CRITICAL
> 2. **Mark as non-goal** — explicitly NOT building this (forecloses it)
> 3. **Park** — capture in `docs/planning/parked.md` for later; not a commitment, not a foreclosure"

When the user picks park, capture:
- One-line title
- Why parked (one line — "interesting but post-v1", "needs user research first", etc.)
- Source (which M2 sub-step / what surfaced it)
- Optional: "promote when" condition (what would make this worth revisiting)
- Brief description (one paragraph)

Append to `discovery_state.parked_drafts` array. Written to `docs/planning/parked.md` at M6 (file created if it doesn't exist; appended in reverse-chronological order otherwise).

**`--auto` does NOT offer parking.** Single-pass auto mode keeps the binary in-scope-or-non-goal cut; if the user wants nuance, they run `/plan --improve` without `--auto`.

*Why this matters:* Without a parking lot, ambiguous ideas pollute either non-goals (over-foreclosing) or roadmap.md (implying sequencing intent). Parking captures the idea without committing the project to it or against it. Question 3 of the build-readiness gate ("what is explicitly out of scope?") gets cleaner answers because non-goals stay reserved for true foreclosures.

#### 2f — Save scope draft

Save to `discovery_state.scope_draft`:

```json
{
  "scope_draft": {
    "goal_statement": "<paragraph>",
    "must_be_true": ["..."],
    "must_exist": ["..."],
    "critical": ["..."],
    "nice_to_have": ["..."],
    "hardest_unknown": "<text>",
    "derailment_risks": [{"risk": "...", "mitigation": "..."}],
    "non_goals": ["..."],
    "parked_drafts": [
      {
        "title": "...",
        "why_parked": "...",
        "source": "M2 sub-step <x>",
        "promote_when": "...",
        "description": "..."
      }
    ]
  }
}
```

Save M2 checkpoint to `.planner/state/<run-id>.json`.

### Exit criteria

- Goal statement captured (or read from existing vision.md for non-greenfield)
- Critical vs. nice-to-have split is explicit (every item categorized)
- Non-goals are explicit (minimum 1 entry; aim for 3–5)
- Hardest unknown identified (or explicitly "no unknowns")
- Scope draft saved to run state
- User confirms before M3 begins

### Iteration

User can revise prior answers. If a hardest unknown gets resolved during M3 sequencing, M2 can be re-entered to update the unknown and surface the next-hardest.

## M3: Sequence with Size Discipline

> **Conversational gate** — same rule as M1/M2. Milestone count, sizing, and risk-first ordering are user-confirmed decisions. The planner proposes; the user confirms or adjusts. Do not silently produce a 6-milestone roadmap without surfacing the proposal for review. `--auto` produces a DRAFT strawman.

Sequence the CRITICAL items from M2 into milestones following GSD's plan-size discipline: 2–3 tasks per milestone, milestones target ~50% context budget for planning and execution. Risk-first ordering — solve the hardest unknown before committing to dependent work.

**Output:** planning/current.md milestone structure, optional roadmap.md draft if >1 milestone. Saved to `discovery_state.milestone_draft`. Written to disk in M6.

**Always-teaches:** Each question is paired with a brief "why this matters" explanation.

### Entry-point routing

- **Full plan (greenfield)** — full sequencing conversation (sub-steps 3a–3e below)
- **Improvement** — focused. Usually a milestone is already in flight; M3 asks about deepening that milestone's task list (deepen sub-branch) or sequencing what comes next (continue sub-branch). Usually 1 milestone of new work; no roadmap change.
- **Drift assessment** — read existing milestones from planning/current.md; no prompting. The sequencing is referenced when drift findings cite "milestone ordering changed."
- **Pivot** — the seven-question opening already establishes new direction. M3 sequences the new plan's milestones, archiving the prior current.md per the disposition manifest.

### Sub-steps (full plan greenfield)

#### 3a — Risk-first sequencing

Ask: "From M2 we identified the hardest unknown. Should that be M1 — solve it first before committing to dependent work? Or does something else need to come first (e.g., scaffolding basic architecture, addressing a derailment risk)?"

Example: "Hardest unknown was 'will auth flow with provider Y work at scale.' M1 should be a spike to validate auth; M2 onwards depends on that decision."

*Why this matters:* Risk-first sequencing prevents wasted effort on dependent work that gets invalidated when the unknown resolves badly. GSD's "what must be TRUE for the goal" — start with the hardest TRUE.

#### 3b — Dependencies for CRITICAL items

Ask: "Of the remaining CRITICAL items, what depends on what? Can anything run in parallel?"

Example: "Need user accounts before user dashboard. Need data persistence before any user-facing reads. Auth and admin tooling can run in parallel since they don't share code."

*Why this matters:* Dependencies determine ordering. Items that parallelize can go into different milestones (or the same milestone if small) for speed. Items that depend on each other must serialize.

#### 3c — Group into milestones (with size discipline)

Ask: "Based on the sequencing and dependencies, propose 2–5 milestones. Each milestone should have a coherent theme — what it ships when done. Aim for **2–3 tasks per milestone**; if a milestone has >5 tasks, consider splitting it."

Example:
- M1: Auth spike + decision (2 tasks)
- M2: User accounts + basic CRUD (3 tasks)
- M3: Admin dashboard (3 tasks)
- M4: Polish + launch readiness (2 tasks)

*Why this matters:* The 2–3-task / ~50%-context bar protects against unimplementable plans. GSD found that bigger plans don't ship; they sit. Smaller, sharper milestones ship. If a milestone proposal has >5 tasks, surface a warning — but respect user agency. The user may have a real reason; don't auto-split.

#### 3d — Roadmap decision

If sequencing produced >1 milestone, recommend `roadmap.md`:

- **Now:** current milestone (M1)
- **Next:** next 1–2 milestones in sequence
- **Later:** parked/deferred items from M2's nice-to-have list
- **Parked:** items that may never ship

If only 1 milestone, skip roadmap.md — everything fits in planning/current.md.

*Why this matters:* roadmap.md keeps the multi-milestone horizon visible without bloating planning/current.md. current.md stays focused on "now"; roadmap.md captures "next / later / parked".

#### 3e — Save milestone draft

Save to `discovery_state.milestone_draft`:

```json
{
  "milestone_draft": {
    "milestones": [
      {
        "id": "M1",
        "theme": "Auth spike + decision",
        "exit_criteria_summary": "auth approach decided + working spike",
        "tasks_outline": ["validate provider Y", "implement basic flow", "test at expected scale"],
        "estimated_complexity": "low | moderate | high"
      }
    ],
    "current_milestone": "M1",
    "needs_roadmap": true,
    "parallel_opportunities": []
  }
}
```

`estimated_complexity` is a coarse enum. M7's plan-lint may surface finer-grained complexity scoring later.

Save M3 checkpoint to `.planner/state/<run-id>.json`.

### Exit criteria

- All CRITICAL items from M2 are sequenced into milestones
- Each milestone has ≤5 tasks (preferably 2–3; warning surfaced if >5, not blocked)
- Dependencies between milestones documented
- Roadmap decision made (yes/no)
- current_milestone identified
- Milestone draft saved to run state
- User confirms before M4 begins

### Iteration

User can revise sequencing. If during M4 the per-milestone quality gates surface that a milestone is too big to finish, M3 can be re-entered to split it.

## M4: Quality Gates

> **Conversational gate** — same rule as M1/M2/M3. Acceptance criteria, validation commands, stop conditions, and project-wide Definition of Done are user-confirmed. Do not invent ACs that the user hasn't seen — they are the contract for what "done" means. `--auto` produces a DRAFT strawman.

Take M3's milestone draft and add quality-gate detail per milestone: acceptance criteria, validation commands, stop conditions, and notes-for-next-session. Plus a project-wide Definition of Done for the operating manual (derived here, written at M6).

**Output:** drafts for planning/current.md's Acceptance criteria / Validation commands / Stop conditions / Notes for next session sections per milestone, plus the operating manual's "Definition of done" section. Saved to `discovery_state.quality_gates_draft`. Written to disk in M6.

**Always-teaches:** Each question is paired with a brief "why this matters" explanation.

### Entry-point routing

- **Full plan (greenfield)** — full quality-gates conversation (sub-steps 4a–4f below)
- **Improvement** — focused. Deepen sub-branch: refine quality gates for the in-flight milestone (often expanding acceptance criteria or adding validation). Continue sub-branch: define quality gates for the next milestone.
- **Drift assessment** — read existing quality gates from planning/current.md; no prompting. Used by drift findings to detect when acceptance criteria are being skipped or reinterpreted.
- **Pivot** — new milestone set from M3 needs fresh quality gates. The project-wide Definition of Done often survives the pivot unchanged; surface it for user confirmation rather than re-asking from scratch.

### Sub-steps (full plan greenfield)

#### 4a — Per-milestone acceptance criteria

For each milestone in `milestone_draft.milestones`, ask: "What are the concrete acceptance criteria for [milestone_id: theme]? Things specific enough that 'done' isn't subjective."

Examples:

- "Auth flow works end-to-end against provider Y at 100 concurrent users"
- "All M2.must_be_true items relevant to this milestone are satisfied"
- "All tests pass; lint and typecheck clean"
- "Documentation updated for the new endpoint"

*Why this matters:* Acceptance criteria are what makes a milestone "shippable" vs. "still in progress." Without them, "done" gets ambiguous and scope creep starts at milestone boundaries.

#### 4b — Validation commands

For each milestone, ask: "What commands do you run to verify the acceptance criteria? Concrete shell commands that produce pass/fail."

Examples:

- `npm test`
- `npm run lint && npm run typecheck`
- `python -m pytest tests/auth/ -v`
- `curl -s https://staging.example.com/health | grep "ok"`

*Why this matters:* Validation commands are how the agent verifies "done" vs. assuming. Mechanical checks beat self-assessment. These land in planning/current.md's "Validation commands" section and feed status.md's "Latest validation results" at /wrapup.

#### 4c — Guardrails (per milestone)

For each milestone, ask: "What must the agent NOT change while executing this milestone? Files, modules, contracts, behaviors that stay strictly out of scope."

Examples:

- "Do not touch `lib/auth/` — auth is M5, this milestone is M3"
- "Do not modify migration history — only add new migrations, never rebase existing ones"
- "Do not introduce packages outside the `lib/constraints/` dependency cone"
- "Do not change pricing or tier-gating logic"
- "Do not refactor the weather adapter contract — M1 callers depend on it as-is"

If the user struggles to name guardrails, prompt with examples in the project: large existing modules that should stay frozen, contracts other code depends on, anything sensitive (auth, billing, schema history).

*Why this matters:* Guardrails are the milestone-level "do not touch" contract. They convert implicit user assumptions ("obviously the agent won't rewrite auth this milestone") into a written constraint the agent inherits. This is question 6 of the build-readiness gate; without it, scope creep is one bad inference away. Lands in planning/current.md's "Guardrails" section.

#### 4d — User-visible behavior (per milestone)

For each milestone, ask: "What can an end user observe after this milestone ships? Walk through the surface — UI, API, CLI, whatever — as concretely as if explaining it to someone using the product."

Examples:

- "User opens /signup, fills the form with email + password, gets a verification email within 30s, and after clicking the link is logged in and redirected to /dashboard"
- "API caller hits `POST /api/v1/quotes` with a valid body and gets a `201` with the quote ID; an invalid body returns `422` with field-level errors"
- "CLI user runs `mytool process file.csv` and sees row-by-row progress, then a summary line; exit 0 on success, exit 1 with a clear error on failure"

A short scenario or numbered flow is fine — the test is "a fresh agent could walk through this without asking what 'works' means."

*Why this matters:* User-visible behavior is question 7 of the build-readiness gate. Acceptance criteria describe what's true; user-visible behavior describes what's observable. Without it, the agent can satisfy ACs while building something the user can't actually use. Lands in planning/current.md's "User-visible behavior" section.

#### 4e — Stop conditions (per milestone)

For each milestone, ask: "When should the agent stop and ask for approval rather than proceeding?"

Default stop conditions (research-canonical, surface as starting set):

- Scope must expand to satisfy a criterion
- A new dependency must be added
- A schema or contract must change
- Validation exposes a requirement conflict

User can add milestone-specific stops on top of the defaults.

*Why this matters:* Stop conditions are the milestone-level version of M1's escalation triggers. They tell the agent when to break out of execution mode and surface a decision rather than proceed unilaterally.

#### 4f — Project-wide Definition of Done

Ask: "Beyond per-milestone acceptance criteria, what's the project-wide 'done' bar? What must always be true before a change is considered complete?"

Default project DoD (research-canonical, surface as starting set):

- The acceptance criteria in `docs/planning/current.md` are satisfied
- Relevant validation commands have been run and results are recorded in `docs/status.md`
- The diff stays within the stated scope and non-goals
- New durable lessons are promoted into the operating manual, a path rule, or a skill when appropriate

User adds project-specific DoD items on top.

*Why this matters:* The project-wide DoD lives in the operating manual and applies to every change, regardless of milestone. This is the bar the agent uses to decide "ready to commit?" vs. "still working."

#### 4g — Notes for next session (per milestone)

For each milestone, ask: "What should the next session know about this milestone? Most likely next step, files likely to change, what must remain true."

Example:

> "Next step: implement the auth callback handler in `lib/auth/callback.ts`. Files likely to change: `lib/auth/*`, `routes/auth.ts`. What must remain true: existing session-based auth in `lib/auth/session.ts` continues to work — this is additive, not a replacement."

*Why this matters:* "Notes for next session" is how planning/current.md communicates across context boundaries. Without it, the next session starts cold even with the plan in place. This field is load-bearing for rad-session's /startup.

#### 4h — Save quality gates draft

Save to `discovery_state.quality_gates_draft`:

```json
{
  "quality_gates_draft": {
    "per_milestone": [
      {
        "milestone_id": "M1",
        "acceptance_criteria": ["..."],
        "validation_commands": ["..."],
        "guardrails": ["..."],
        "user_visible_behavior": "...",
        "stop_conditions": ["..."],
        "notes_for_next_session": "..."
      }
    ],
    "project_definition_of_done": ["..."]
  }
}
```

Save M4 checkpoint to `.planner/state/<run-id>.json`.

### Exit criteria

- Every milestone has ≥3 acceptance criteria (concrete, not subjective)
- Every milestone has ≥1 validation command
- Every milestone has stop conditions (defaults + project-specific)
- Project-wide Definition of Done captured (≥3 entries; defaults + project-specific)
- Notes for next session captured (at least for the current milestone)
- Quality gates draft saved to run state
- User confirms before M5 begins

### Iteration

User can revise. If during M5 doc-set recommendation a milestone needs different validation (e.g., user opts for a `--standard` doc set that doesn't include test files), M4 can be re-entered to update validation commands.

## M5: Doc-Set Recommendation

> **Conversational gate** — `user_approval: true` is the hard gate for M6. Without it, M6 cannot fire. The recommendation is the planner's; the approval is the user's. The doc set is not approved by inference. `--auto` skips this gate but produces DRAFT-labeled output without ADRs (see "Auto mode semantics" near the top of this file).

Take all prior drafts (M1 constitution, M2 scope, M3 milestones, M4 quality gates) and recommend the doc set that best supports *this* plan. The doc set is recommended *based on the plan* — every doc gets project-specific rationale, not a generic justification. Complexity routing chooses scale: `lite` (minimal), `standard` (most projects), `full` (substantial).

**Output:** approved doc set list with rationale, complexity routing decision, optional skills/hooks recommendations. Saved to `discovery_state.doc_set_draft`. **User approval is the hard gate for M6** — M5 is the last conversation phase before any writes.

**Always-teaches:** Each question is paired with a brief "why this matters" explanation. The per-doc rationale is itself a teaching moment — the user learns why each doc earns its place.

### Entry-point routing

- **Full plan (greenfield)** — full doc-set recommendation conversation (sub-steps 5a–5f below)
- **Improvement** — most docs already exist; M5 surfaces *additions or modifications* (e.g., "you have vision.md but no roadmap.md, and you've identified 4 milestones now — consider adding roadmap"). Existing docs not touched unless the guard rail prompts the user.
- **Drift assessment** — read existing doc set; M5 surfaces any *gaps* (docs that should exist but don't) as findings in the drift report, not as recommendations to add unilaterally.
- **Pivot** — the disposition manifest from pivot's seven-question opening already governed existing docs. M5 confirms the new doc set per the pivot's direction and surfaces any additions needed.

### Sub-steps (full plan greenfield)

#### 5a — Complexity assessment

Planner classifies the project complexity based on signals from M0–M4:

- **lite:** minimal scope (≤2 critical items from M2), 1 milestone from M3, solo work, no substantive architecture. Single combined operating manual carrying vision-level intent.
- **standard:** moderate scope, 2–4 milestones, recognizable architecture, ≥1 stack decision. Core set.
- **full:** substantial scope, ≥5 milestones, complex architecture, multiple integrations or unknowns. Core + roadmap + ADRs + hooks/skills recommendations.

Surface the assessment with rationale: "Looks like a **standard** project — you have 3 milestones, you raised auth-with-provider-Y as a hardest unknown, and your stack involves TypeScript + Next.js + Postgres. Sound right, or do you want to override?"

*Why this matters:* Complexity routing prevents two failure modes: a lite project drowning in 9 docs no one will maintain, or a substantial project sitting on 2 docs that don't capture the real complexity. Right-sized doc structure ships; wrong-sized doc structure rots.

#### 5b — Doc-set recommendation per complexity

Based on the complexity bucket, propose specific docs.

**Lite (minimal):**

- Operating manual (CLAUDE.md / AGENTS.md per agent scope) — folds in vision-level intent
- `docs/planning/current.md`
- `docs/status.md` scaffold
- `.rad/profile`

No separate `docs/vision.md` or `docs/architecture.md` — at this scale, the operating manual carries those concerns inline.

**Standard (most projects):**

- Operating manual
- `docs/vision.md`
- `docs/architecture.md`
- `docs/planning/current.md`
- `docs/status.md` scaffold
- `docs/decisions/README.md` (with NNNN-*.md entries for any decisions surfaced during M2 risks / M4 quality gates)
- `docs/roadmap.md` *if* >1 milestone from M3
- `.rad/profile`

**Full (substantial):**

All standard items, plus:

- `docs/roadmap.md` (always — substantial projects have horizon beyond current cycle)
- `.claude/settings.json` (if Claude in scope) with permissions + hook scaffolding
- `.codex/config.toml` (if Codex in scope)
- Recommended skills (see 5e)
- Recommended hooks (see 5e)

#### 5c — Project-specific rationale per doc

For each recommended doc, generate a one-line rationale tied to *this* project — not a generic justification.

Example for a standard project:

- "**vision.md** — your goal and non-goals (no real-time collab, no mobile v1) crystallized during M2; recording them now keeps future milestones aligned"
- "**architecture.md** — your stack (TypeScript + Next.js + Postgres) plus the auth-with-provider-Y unknown warrant a canonical home for invariants and the eventual decision"
- "**planning/current.md** — your M1 spike has 3 acceptance criteria and 2 validation commands; current.md captures the executable plan"
- "**status.md scaffold** — rad-session populates this from evidence at /wrapup; we just create the placeholder"
- "**decisions/README.md + 0001-drizzle-vs-prisma.md** — you raised ORM choice as a decision during M2 risks; ADR 0001 captures the rationale and supersession path"
- "**roadmap.md** — you have 4 milestones; roadmap.md keeps the multi-milestone horizon visible without bloating current.md"
- "**.rad/profile** — captures mode preference (mentor) and agent scope (claude_only)"

*Why this matters:* "Every artifact has a reason" is the senior-engineer move. Generic doc-set lists feel imposed; project-specific lists feel justified. If a doc can't earn a project-specific rationale, it probably shouldn't be in the recommendation.

#### 5d — User approval (and override)

Present the recommended doc set with rationale. Ask:

> "Approve this doc set? You can also:
> - Drop any recommendation that doesn't fit
> - Add a doc not on the list (e.g., for regulatory needs)
> - Switch complexity routing (lite / standard / full) — that re-runs steps 5a–5c"

User approves or modifies → final doc set locked.

*Why this matters:* The user owns the doc set, not the planner. Recommendation with rationale is the planner doing its job; final approval is the user doing theirs. If user drops a recommendation, capture the reason in `user_overrides` in case it matters later.

#### 5e — Skills and hooks (standard / full only)

For `standard` and `full` complexity, optionally recommend skills and hooks. Skip for `lite`.

**Skills** (placed in `.claude/skills/<name>/SKILL.md` or `.agents/skills/<name>/SKILL.md`):

- `review-diff` — review changes before commit; common starting skill
- `release-checklist` — pre-release validation
- Project-specific skills surfaced during M4 (e.g., "deploy-to-staging" if deployment is multi-step)

**Hooks** (placed in `.claude/settings.json` or `.codex/config.toml`):

- PreToolUse re-read plan before major edits (planning-with-files pattern; cheap)
- Secret-blocking on `.env` / credentials files
- Format-on-save for the project's lint/format tooling

For each recommended skill/hook, surface project-specific rationale per the 5c pattern.

*Why this matters:* Per the research: "Prose instructions are for judgment. Permissions and hooks are for guarantees." Skills and hooks are how you enforce things in code rather than prose. Skipping in `lite` respects the principle that small projects shouldn't be over-instrumented.

#### 5f — Save doc-set draft

Save to `discovery_state.doc_set_draft`:

```json
{
  "doc_set_draft": {
    "complexity": "lite | standard | full",
    "approved_docs": [
      {
        "path": "CLAUDE.md",
        "rationale": "operating manual; agent scope claude_only",
        "writer": "rad-planner (Constitution sections) + rad-session (Operational sections)",
        "guard_rail_check": "no pre-existing CLAUDE.md beyond /init residue"
      }
    ],
    "approved_skills": [],
    "approved_hooks": [],
    "user_overrides": [
      {"action": "drop", "doc": "docs/roadmap.md", "reason": "only 1 milestone"}
    ],
    "user_approval": true
  }
}
```

`user_approval: true` is the hard gate for M6. Without it, M6 cannot fire.

Save M5 checkpoint to `.planner/state/<run-id>.json`.

### Exit criteria

- Complexity assessment recorded (with user confirmation or override)
- Doc set proposed with project-specific rationale for every doc
- User approval captured (`user_approval: true`)
- Any user overrides recorded with reason
- Final doc set locked
- M5 checkpoint saved

### Iteration

User can revise complexity routing or doc set at any time. If they switch from `standard` to `full` mid-conversation, re-run 5a–5c with the new bucket. If they drop a doc, record the reason in `user_overrides`. M6 will not fire without `user_approval: true`.

## M6: Doc Creation (executes plan's M0)

M6 is execution, not conversation. The user already approved the doc set at M5 (`user_approval: true` is the hard gate). M6 reads the drafts from M1–M5 and writes the approved files to `project_dir`, honoring guard rails for any pre-existing content.

**Output:** files on disk per the approved doc set. Saved path list in `discovery_state.m6_writes`. Terminal M6 checkpoint marks completion of /plan.

**No new user-elicit questions.** M6 may prompt for guard-rail decisions when pre-existing content collides with a planned write.

### Entry-point routing

- **Full plan (greenfield)** — execute all sub-steps below; write all approved docs
- **Improvement** — targeted writes only (usually `docs/planning/current.md` updates plus any new ADRs). Vision/architecture untouched unless user explicitly approved updates in M5.
- **Drift assessment** — M6 is largely a no-op. The drift report is conversation output, not a written file. The exception: if the user picked "incorporate findings into the plan" at the drift output menu, M6 updates `docs/planning/current.md` to reflect the incorporated findings.
- **Pivot** — execute the disposition manifest from pivot's seven-question opening (archive old per disposition, write new per the rebuilt drafts, supersede ADRs with cross-references, save the manifest as `docs/planning/archive/YYYY-MM-DD-pivot-manifest.md`).

### Sub-steps

#### 6a — Pre-flight write check

Verify before any writes:

- `discovery_state.doc_set_draft.user_approval == true` (hard gate — refuse to proceed if false)
- `project_dir` exists and is writable; if it doesn't exist (M0 option 3 case), `mkdir -p`
- For each doc to be written, check whether the file already exists

If any pre-existing doc collides with a planned write, surface the guard rail:

- **Strategic docs** (vision.md, architecture.md, roadmap.md): three-option menu — overwrite / append / skip
- **planning/current.md:** special handling — "this archives the current `current.md` to `docs/planning/archive/YYYY-MM-DD-pre-replace.md` and writes the new one. Proceed?"
- **decisions/*.md:** never overwrite. If filename collision, increment ADR number.
- **Operating manual:** if init residue detected (per M0 `claude_init_residue` or `codex_init_residue`), enrich rather than overwrite — insert Constitution sections in their proper place; preserve any existing Operational sections and user-added sections; surface "Preserved user sections: \<list\>". If substantial content, three-option menu.

Save guard-rail decisions to `discovery_state.m6_guard_rails`.

#### 6b — Create directory structure

`mkdir -p` for missing subdirectories under `project_dir`:

- `docs/`
- `docs/planning/`
- `docs/planning/archive/`
- `docs/decisions/` (if any ADRs in the approved set AND `--auto` is NOT set; under `--auto` this directory is intentionally not created — proposed decisions go to `docs/planning/proposed-decisions.md` instead)
- `.rad/`
- `.claude/` (if Claude in scope)
- `.codex/` (if Codex in scope)
- `.agents/skills/` (if Codex in scope and skills approved)
- `.claude/skills/` (if Claude in scope and skills approved)
- `.claude/rules/` (if Claude in scope and path-scoped rules approved)

#### 6c — Write operating manual

Per `discovery_state.agent_scope`:

- **claude_only:** write `CLAUDE.md` with Constitution sections from M1
- **codex_only:** write `AGENTS.md` with Constitution sections from M1
- **claude_and_codex:** write `AGENTS.md` canonical with Constitution sections + `CLAUDE.md` shim (`@AGENTS.md` import + placeholders for Claude-specific Operational sections that rad-session fills during `/startup`'s Phase 0.5 bootstrap path)

**Auto-mode banner:** if `--auto` is set, insert a DRAFT banner immediately under the operating manual's H1 title (or at the very top of `AGENTS.md` if no H1):

```markdown
> **DRAFT** — Constitution sections generated by `/plan --auto` from the user's brief; not yet validated against user preferences. Review and revise.
```

Sections written by rad-planner (per `docs/cross-plugin-contracts.md` sectioned-writer exception):

- **Project** — from `constitution_draft.project_purpose`
- **Read order** — computed from `doc_set_draft.approved_docs` (which docs to read before what kinds of work)
- **Hard boundaries** — from `constitution_draft.hard_boundaries`
- **Engineering rules** — from `constitution_draft.principles`
- **Definition of done** — from `quality_gates_draft.project_definition_of_done`
- **Escalate triggers** — from `constitution_draft.escalation_triggers`

Sections NOT written by rad-planner (rad-session populates during `/startup`'s Phase 0.5 bootstrap path on first run):

- Commands (install / test / lint / build)
- Compact Instructions (CLAUDE.md only)
- Claude-specific behavior (CLAUDE.md only)

#### 6d — Write strategic docs

For each entry in `doc_set_draft.approved_docs`, write per the canonical template from `docs/doc-conventions.md`:

- **`docs/vision.md`** — from M2 (`goal_statement` → Product statement; `must_be_true` and `must_exist` → success signals; product principles synthesized from M1 principles where relevant; `non_goals` → Non-goals)
- **`docs/architecture.md`** — **SCAFFOLD only.** The planner emits the template structure (Current stack / Repository map / System boundaries / Core invariants / Canonical patterns / Commands agents should know / Secrets and environment / Known sharp edges / Change notes) with placeholders. **Surface to user explicitly: "architecture.md is a scaffold — fill in the per-section content as you go; M4 quality gates and rad-session /wrapup surface when sections drift from reality."**
- **`docs/roadmap.md`** (if approved) — from M3 (multi-milestone view → Now / Next / Later / Parked + Rules for proposing roadmap changes)
- **`docs/planning/current.md`** — from M3 + M4 (`current_milestone` + per-milestone `acceptance_criteria` + `validation_commands` + `guardrails` + `user_visible_behavior` + `stop_conditions` + `notes_for_next_session` + `risks` from M2 `derailment_risks`). All 8 required sections per `docs/doc-conventions.md` must be populated; `plan-lint.py` fails the milestone otherwise.
- **`docs/planning/parked.md`** — only if `discovery_state.scope_draft.parked_drafts` is non-empty. Use the format from `references/parked-template.md`. Append to the file if it already exists (reverse-chronological — newest entries at the top), or create with the file header otherwise. Skipped entirely under `--auto`.
- **`docs/status.md` scaffold** — empty 8-section template (see `docs/status-md-schema.md`) with explicit "No data yet — populated by rad-session /wrapup from evidence" markers per section

**ADR handling — branches on `--auto`:**

- **Default (no `--auto`):** Write `docs/decisions/README.md` (ADR index header per `docs/doc-conventions.md`) AND `docs/decisions/NNNN-*.md` per any decisions surfaced during M2 risks / M4 quality gates. Sequence-numbered starting from `0001`. These are real ADRs — the M5 dialogue confirmed the user's intent for each one.

- **Under `--auto`:** Do NOT write `docs/decisions/README.md` or any `NNNN-*.md` files. Instead, write `docs/planning/proposed-decisions.md` containing the candidate decisions in ADR-shape (Status / Context / Decision / Consequences) but explicitly marked as proposals:

  ```markdown
  # Proposed Decisions

  > **DRAFT** — generated by `/plan --auto`. These are CANDIDATE decisions surfaced from the user's brief; they are NOT yet ADRs. Review each proposal, then either:
  > - Promote to a real ADR at `docs/decisions/NNNN-*.md` (you write it, or re-run `/plan --improve` without `--auto` to walk through them conversationally)
  > - Edit the proposal to reflect a different decision
  > - Delete the proposal (decision not warranted)

  ## Proposal 1 — <title>

  **Status:** PROPOSED (not yet an ADR)
  **Context:** {from M2 risks or M4 quality gates}
  **Proposed decision:** {LLM's guess at a reasonable default}
  **Rationale (LLM-inferred):** {why this default; user should validate or replace}
  **Consequences (if accepted):** {positive + negative; LLM-drafted}

  ---

  ## Proposal 2 — ...
  ```

  Each proposal carries the LLM-inferred rationale explicitly so the user can see what the model guessed at and either confirm or replace. **`docs/decisions/` does NOT get created under `--auto`** — keep that directory clean until real, user-confirmed ADRs land.

**Auto-mode banners:** if `--auto` is set, insert a DRAFT banner immediately under the H1 title of each written file (`vision.md`, `architecture.md`, `roadmap.md`, `planning/current.md`):

```markdown
> **DRAFT** — generated by `/plan --auto` from the user's brief; not yet validated against user preferences. Review and revise.
```

`docs/status.md` scaffold and `docs/planning/proposed-decisions.md` already have their own draft framing.

#### 6e — Write config files

- **`.rad/profile`** (TOML, always written): `mode = "mentor"` (default), `agent_scope = "<from M0>"`, `multi_branch_status = false`
- **`.claude/settings.json`** (if Claude in scope and approved in M5): permissions + hooks per `doc_set_draft.approved_hooks`
- **`.codex/config.toml`** (if Codex in scope): approvals + sandbox + hooks per approved hooks

#### 6f — Write skills (if approved)

For each entry in `doc_set_draft.approved_skills`, create `.claude/skills/<name>/SKILL.md` (Claude scope) or `.agents/skills/<name>/SKILL.md` (Codex scope) with a scaffold. The scaffold contains the SKILL.md frontmatter and a brief description block; the user fills in the procedure body.

#### 6g — Post-write validation

Run validators (all four are implemented in M7 and live at `plugins/rad-planner/scripts/`):

- `plan-lint.py` on `docs/planning/current.md` — required-section presence, acceptance-criteria checkbox format, runnable validation commands, vague-language detection
- `status-validator.py` on `docs/status.md` — freshness vs git mtime, 8-section presence, evidence-based validation results, read-order non-empty
- `doc-redundancy.py` on `project_dir` — cross-doc bullet/heading duplicate detection via Jaccard similarity
- `doc-contradiction.py` on `project_dir` — vision.md non-goals vs current.md acceptance criteria via stemmed token overlap

Surface any issues to the user. plan-lint CRITICAL/HIGH issues are surfaced strongly but not gated — the user decides whether to fix before considering /plan complete. status-validator HIGH issues surface similarly. doc-redundancy MEDIUM and doc-contradiction findings are advisory.

#### 6h — Final summary

Surface to the user:

- **Files created** — list with absolute paths
- **Guard rail decisions** — what was preserved, overwritten, or skipped
- **Validation results** — pass / warn / fail per validator
- **Recommended next step** — "Run `/rad-session:startup` — its Phase 0.5 bootstrap will populate the operating manual's Commands / Compact / Claude-specific sections on first run, then the normal briefing begins your work"
- **Operating-manual handoff note** — "Commands, Compact Instructions, and Claude-specific sections are owned by rad-session — they'll be populated during `/startup`'s Phase 0.5 bootstrap on first run"

**Under `--auto`, append the trade-off banner verbatim:**

```
⚠ This plan was generated unilaterally via /plan --auto. The artifacts are
strawmen — review and revise. No ADRs were written; candidate decisions
live in docs/planning/proposed-decisions.md for your review.

To do the planning conversation properly, run `/plan --improve` (without
--auto) and walk through M1–M5 with the agent asking clarifying questions.
That will produce real ADRs from confirmed user input rather than LLM-
inferred proposals.
```

This banner is mandatory in `--auto` mode. Removing it silently is a contract violation — the user explicitly chose speed over confidence, and the final summary names that trade-off so a future Claude session doesn't mistake `--auto` output for fully-considered planning.

Save terminal M6 checkpoint to `.planner/state/<run-id>.json`:

```json
{
  "phase": "6.M6",
  "m6_writes": [
    {"path": "<abs path>", "action": "created | enriched | overwritten | skipped", "guard_rail": "<reason>"}
  ],
  "validator_results": {
    "plan_lint": "pass | warn | fail | not_run",
    "status_validator": "pass | warn | fail | not_run",
    "doc_redundancy": "pass | warn | fail | not_run",
    "doc_contradiction": "pass | warn | fail | not_run"
  },
  "completed_at": "ISO-8601"
}
```

### Exit criteria

- All approved docs exist in `project_dir` (or explicitly skipped via guard rail with user confirmation)
- No user content lost (guard rails honored; backups preserved in archive paths for any overwrite)
- Validator results surfaced (pass / warn / fail per validator)
- Final summary delivered to the user
- Terminal M6 checkpoint saved
- `discovery_state.m6_complete: true`

### Iteration

M6 is terminal for the /plan run. If the user wants changes after M6 ships, they re-invoke /plan with the appropriate entry-point flag (`--improve` for refinement, `--pivot` for direction change, `--drift` for an assessment check).

## Checkpoint & resume

Long planning runs are compaction-prone. Save state to `.planner/state/<run-id>.json` at these transitions:

0. After M0 (discovery complete)
1. After each M1–M5 phase
6. After M6 (artifacts written)

The model has to remember to write the checkpoint at each transition — there is no hook that does it automatically. On `--resume <run-id>`, load the file, announce the phase you're resuming from, and continue.

## Single-writer rule

Per `docs/cross-plugin-contracts.md`:

- **rad-planner writes:** vision.md, architecture.md, roadmap.md, planning/current.md, decisions/README.md, initial ADRs during /plan
- **rad-planner scaffolds:** status.md (rad-session populates from evidence at /wrapup)
- **rad-planner contributes:** operating manual Constitution sections (Project, Read order, Hard boundaries, Engineering rules, Definition of done, Escalate triggers)
- **rad-session owns:** operating manual Operational sections (Commands, Compact Instructions, Claude-specific behavior), status.md updates from evidence
- **User owns:** individual ADRs (docs/decisions/NNNN-*.md), edits to all strategic docs after creation

## Key references

**Canonical spec docs (top-level `docs/`):**

- `docs/doc-conventions.md` — canonical file structure, templates, ownership matrix
- `docs/cross-plugin-contracts.md` — single-writer rule, guard rails, .rad/profile protocol
- `docs/entry-point-routing.md` — four entry points, detection model, per-entry conversation shapes
- `docs/status-md-schema.md` — eight-section schema, evidence sources, inference policies

**Plugin internals — v4.0 (`plugins/rad-planner/`):**

- `scripts/README.md` — validator script documentation (plan-lint, status-validator, doc-redundancy, doc-contradiction, validate-json)
- `fixtures/README.md` — end-to-end test fixtures
- `fixtures/standard-project/` — reference v4.0 project showing what good output looks like

**Plugin internals — legacy v3.0 (retained for sibling skills not yet updated):**

The v4.0 `/plan` workflow (M0–M6) does not consume the v3.0 reference files below. They remain for the sibling skills (`checkpoint`, `status`, `review-plan`, `evaluate-stack`) and subagents (`plan-architect`, `risk-assessor`, `stack-advisor`) that are pending a future v4.x update:

- `references/plan-template.md`, `references/task-format.md`, `references/golden-path-matrix.md`, `references/anti-patterns.md`, `references/failure-state-template.md`, `references/tdd-constraints.md`, `references/context-management.md`
- `references/subagent-prompts/stack-eval.md`, `references/subagent-prompts/risk-assessment.md`
- `examples/example-plan.md` + `examples/example-tasks.md` — v3.0 examples; v4.0 reference output lives in `fixtures/standard-project/`

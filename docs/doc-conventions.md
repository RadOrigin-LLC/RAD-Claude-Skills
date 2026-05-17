# Document Conventions — RAD Canonical Structure

**Status:** Draft (Phase 0 spec, 2026-05-14)
**Replaces:** `file-conventions.md` (v3.0/v4.0 8-doc standard, deprecated)
**Companions:** `cross-plugin-contracts.md`, `entry-point-routing.md`, `status-md-schema.md`

Canonical specification for the documents that rad-planner 4.0 and rad-session 5.0 read, write, and prune. Aligned with the published OpenAI/Anthropic project-structure research (see "Best Practices for Lean, Reliable Vibe Coding Projects" deep-research synthesis). This file is the single source of truth for what a well-structured agentic project looks like.

## The three-band project memory model

The canonical structure is organized into three bands, matching the cross-vendor convergence in current research:

**Band 1 — Operating manual.** Always-loaded by the coding agent at session start. Tells the agent how to behave in every session. Short, factual, routing-and-rules. Files: `AGENTS.md` (Codex), `CLAUDE.md` (Claude), or both.

**Band 2 — Slower-changing project memory.** Documents that explain the product, architecture, roadmap, and durable decisions. Read on demand, not on every session. Files: `docs/vision.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/`.

**Band 3 — Volatile execution state.** Current plan, current status. Changes during active work. Files: `docs/planning/current.md`, `docs/planning/archive/`, `docs/status.md`.

The three-band split keeps stable rules, slower-changing memory, and current task state in different places — letting the agent act independently inside a contract that can be inspected, verified, and resumed.

## File naming convention

- **Root-level operational files: UPPERCASE.** `AGENTS.md`, `CLAUDE.md`, `README.md`, `LICENSE`. These are surfaced to humans as well as agents.
- **Strategic and operational docs under `docs/`: lowercase.** `docs/vision.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/status.md`, `docs/planning/current.md`, `docs/decisions/0001-*.md`.
- **Config files and rad-internal: lowercase.** `.rad/profile`, `.claude/settings.json`, `.codex/config.toml`.

This matches the research convention and what each vendor's tooling reads natively.

## Canonical file structure

```
project-root/
├── AGENTS.md              # operating manual (if Codex in scope)
├── CLAUDE.md              # operating manual (if Claude in scope; @AGENTS.md shim when both)
├── README.md              # human-facing project description (not rad-managed)
├── LICENSE                # (not rad-managed)
├── .rad/
│   └── profile            # mode preference, agent scope, multi-branch flag (TOML)
├── .codex/
│   ├── config.toml        # Codex deterministic enforcement (if Codex in scope)
│   └── agents/            # optional
├── .agents/
│   └── skills/            # optional: on-demand Codex skills
│       └── <skill>/SKILL.md
├── .claude/
│   ├── settings.json      # Claude permissions, hooks (if Claude in scope)
│   ├── rules/             # optional: path-scoped Claude rules
│   │   └── *.md
│   └── skills/            # optional: on-demand Claude skills
│       └── <skill>/SKILL.md
└── docs/
    ├── vision.md          # product intent
    ├── architecture.md    # current stack, repo map, invariants, canonical patterns
    ├── roadmap.md         # sequencing horizon (when >1 milestone)
    ├── status.md          # live handoff and audit log (rad-session-owned)
    ├── planning/
    │   ├── current.md     # current execution plan
    │   └── archive/       # shipped/superseded plans
    └── decisions/
        ├── README.md      # ADR index (when decisions exist)
        └── NNNN-*.md      # individual ADR entries
```

## Categorization

Not every project needs every file. The planner recommends a doc set based on project shape, with project-specific rationale.

### Core (every project that uses rad-planner / rad-session)

| File | Owner | Created at |
|---|---|---|
| `AGENTS.md` (if Codex in scope) | rad-session (file); rad-planner contributes Constitution sections | `/startup` bootstrap or `/plan` M6 |
| `CLAUDE.md` (if Claude in scope; as `@AGENTS.md` shim when both) | rad-session (file); rad-planner contributes Constitution sections | `/startup` bootstrap or `/plan` M6 |
| `docs/vision.md` | rad-planner | `/plan` M6 |
| `docs/architecture.md` | rad-planner | `/plan` M6 |
| `docs/planning/current.md` | rad-planner | `/plan` M6 |
| `docs/status.md` | rad-planner scaffolds; rad-session populates | `/startup` bootstrap or `/plan` M6 |
| `.rad/profile` | rad-planner or rad-session (whoever runs first) | first run |

### Strongly recommended (most non-trivial projects)

| File | Owner | Created at |
|---|---|---|
| `docs/roadmap.md` (when >1 milestone in view) | rad-planner | `/plan` M6 if Phase 3 produced multiple milestones |
| `docs/decisions/README.md` | rad-planner | `/plan` M6 if any ADRs warranted |
| `.claude/settings.json` (if Claude in scope) | rad-session scaffolds | `/startup` bootstrap (first run) |
| `.codex/config.toml` (if Codex in scope) | rad-session scaffolds | `/startup` bootstrap (first run) |

### Situational (planner recommends in Phase 5 when project warrants; human owns)

| File | Owner | Created at |
|---|---|---|
| `docs/decisions/NNNN-*.md` | Human (prompted by both plugins) | as decisions occur |
| `docs/planning/parked.md` | Human (rad-planner appends when user parks an idea during M2) | first park action |
| `.claude/rules/*.md` | Human (planner recommends) | post-plan |
| `.claude/skills/<name>/SKILL.md` | Human (planner recommends) | post-plan |
| `.agents/skills/<name>/SKILL.md` | Human (planner recommends) | post-plan |
| `docs/planning/archive/*.md` | rad-session (moves current.md here at milestone shipped) | `/wrapup` at milestone completion |

### rad-internal (not user-facing under normal use)

| File | Owner | Created at |
|---|---|---|
| `.rad-archive/<utc-timestamp>/` | Migration tools (rare) | only during migrations |

### Out of scope for v4.0/v5.0 (user-owned or deferred)

- `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` — user-level personal defaults across projects, not project-specific
- `CLAUDE.local.md` — optional machine-local Claude overrides
- `MEMORY.md` — Claude's auto-memory index (machine-local)
- `AGENTS.override.md` — nested AGENTS hierarchy (monorepo case, deferred)

## Per-file specifications

### Operating manual: `AGENTS.md` / `CLAUDE.md`

**Purpose:** Always-loaded operating manual. Tells the agent how to behave in every session.

**Conditional creation:**
- Claude-only project → `CLAUDE.md` is canonical
- Codex-only project → `AGENTS.md` is canonical
- Both in scope → `AGENTS.md` is canonical, `CLAUDE.md` is a thin `@AGENTS.md` import with Claude-specific compaction notes

**Template sections** (research-canonical, in order):
- Project (one-sentence purpose)
- Read order
- Hard boundaries
- Commands (install, dev, test, lint, typecheck, build)
- Engineering rules
- Definition of done
- Escalate instead of guessing

CLAUDE.md shim additions when both agents in scope:
- `@AGENTS.md` (first line)
- Claude-specific behavior
- Compact Instructions

**Target length:** ≤150 lines. The operating manual must stay short — agents read it every session and bloat reduces compliance.

**Update triggers:** project scope shift, new tool added, new conventions adopted, recurring correction pattern surfaces.

**Pruning:** rad-session `/wrapup` checks for operating-manual bloat and flags. Doesn't auto-prune — flags for user review.

**Does NOT contain:** long explanations, tutorials, frequently changing information, file-by-file codebase descriptions, current work-in-progress, TODOs, decisions still being deliberated, temporary workarounds.

### `docs/vision.md`

**Purpose:** Product intent. What this is, who it's for, what it's not.

**Template sections** (research-canonical):
- Product statement
- Problem
- Target users
- Product principles
- Non-goals
- Success signals

**Target length:** 50–150 lines.

**Update triggers:** scope change, audience change, product principle adopted or retired, non-goal added or removed.

**Pruning:** revise in place. No changelog tail; git history serves that role.

### `docs/architecture.md`

**Purpose:** Current state of the codebase from an agent operations perspective. NOT a static structure dump.

**Template sections** (research-canonical):
- Current stack (language, framework, package manager, test, lint/format, build/deploy, data store, external services)
- Repository map
- System boundaries
- Core invariants
- Canonical patterns
- Commands agents should know
- Secrets and environment
- Known sharp edges
- Change notes

**Target length:** 100–300 lines. Diagrams count toward the budget; if they push past 300, move to a focused `docs/diagrams/` folder.

**Update triggers:** new component, removed component, integration boundary changed, deprecation of an existing pattern, new sharp edge discovered.

**Pruning:** revise in place. Git history captures prior structure.

### `docs/roadmap.md`

**Purpose:** Sequencing horizon beyond the current cycle. Strategic direction over time.

**Template sections** (research-canonical):
- Now (Theme, In scope, Exit criteria)
- Next
- Later
- Parked
- Rules for proposing roadmap changes

**Target length:** 50–150 lines.

**Update triggers:** milestone shipped, new milestone surfaced, scope reordered, Parked entry revived or retired.

**When to create:** when the project has more than one milestone in view. Solo or very early projects can skip until a second milestone emerges.

### `docs/status.md`

**Purpose:** Live handoff and audit log. Project-scoped reality from evidence.

**Schema:** see `status-md-schema.md` for the full field-by-field specification.

**Target length:** under 150 lines under normal use. If sections grow past their soft caps repeatedly, that's a signal worth flagging.

**Update triggers:** every `/wrapup` (unless no work detected since last update — see guard rails in `cross-plugin-contracts.md`).

### `docs/planning/current.md`

**Purpose:** Current execution plan. Self-contained — a future agent should be able to restart from this file without chat history.

**Template sections** (research-canonical; **Guardrails** and **User-visible behavior** added in rad-planner v4.6 as build-readiness gate questions 6 and 7):
- Objective
- Why this matters (recommended)
- Non-goals (recommended)
- Current milestone
- Acceptance criteria
- Validation commands
- **Guardrails** — what the agent must NOT change while executing this milestone. Required. Bulleted list of files, contracts, modules, and behaviors that stay out of scope (e.g., "do not touch `lib/auth/`", "do not change migration history", "do not add packages outside the `lib/constraints/` cone").
- **User-visible behavior** — what an end user can observe after this milestone ships. Required. Short scenario or numbered flow describing the observable outcome at the UI / API / CLI surface. Concrete enough that a fresh agent could walk through it.
- Planned changes (recommended)
- Open questions (recommended)
- Risks (recommended)
- Stop conditions
- Notes for the next session

**Target length:** 100–400 lines.

**Required vs recommended:** `plan-lint.py` enforces all 8 required sections (Objective, Current milestone, Acceptance criteria, Validation commands, Guardrails, User-visible behavior, Stop conditions, Notes for the next session). Empty or placeholder-only required sections fail the lint. Recommended sections flag at LOW severity if missing — useful for non-trivial plans, optional for very small ones.

**Update triggers:** task state change, milestone boundary, scope adjustment, new task added, open question surfaced or resolved.

**Lifecycle:** current.md is replaced when the milestone ships. The previous current.md is moved to `docs/planning/archive/YYYY-MM-DD-mN.md` and a new current.md is initialized.

### `docs/planning/archive/`

**Purpose:** Historical record of shipped plans.

**Content:** previous `current.md` files, renamed with date and milestone identifier. Plus pivot manifests when pivots occur.

**Naming:** `YYYY-MM-DD-<milestone-id>.md` for plan archives; `YYYY-MM-DD-pivot-manifest.md` for pivot dispositions.

**Update triggers:** rad-session `/wrapup` moves current.md here when the user confirms a milestone is shipped.

**Pruning:** never automated. Archive is the historical record. Manual cleanup if it becomes unmanageable.

### `docs/planning/parked.md`

**Purpose:** First-class home for captured-but-not-committed ideas (rad-planner v4.6+). The third option alongside "in scope" and "non-goal" — for ideas that surface during planning but aren't ready to commit to and aren't worth foreclosing.

**Distinct from `vision.md` non-goals:** non-goals are foreclosure ("we are NOT building this"). Parked items are open ("worth thinking about, not now").

**Distinct from `roadmap.md` Later/Parked:** roadmap.md implies sequencing intent. parked.md is the holding pen with no implicit ordering or commitment.

**Update triggers:** during `/plan` M2 conversation when the user opts to park an idea that doesn't fit must-be-TRUE / must-EXIST / CRITICAL / non-goal. `--auto` does NOT park (single-pass mode skips the conversation branch). Manual promotion to a milestone or to a non-goal is user-initiated; no automatic decay or pruning.

**Owner:** Human-owned. rad-planner appends when the user explicitly opts to park during M2. Neither plugin auto-prunes or auto-promotes.

**Entry format** (research-canonical):

```markdown
## YYYY-MM-DD — Short title

**Why parked:** one-line reason (e.g., "interesting but post-v1", "needs user research first", "depends on retired feature returning")
**Source:** which M2 conversation / which milestone surfaced it / who raised it
**Promote when:** condition under which this should be revisited (optional)

Brief description of the idea, no more than a paragraph. Specific enough that future-you remembers what it was without re-deriving the context.
```

**Target length:** unbounded. Parking is unbounded by design — the cost of a stale parked item is low; the cost of foreclosing a good idea or polluting the roadmap is high.

**Pruning:** never automated. User decides whether to promote, drop, or leave.

### `docs/decisions/`

**Purpose:** Architecture Decision Records (ADRs). Append-only record of choices with sequence numbers and supersession.

**Structure:**
- `docs/decisions/README.md` — index, brief description of what ADRs are and how to read them
- `docs/decisions/NNNN-<slug>.md` — individual ADR entries

**ADR template sections** (research-canonical):
- Decision number, title, status (Accepted / Superseded / Proposed)
- Date
- Context
- Decision
- Why
- Alternatives considered
- Consequences (positive, negative, follow-up)
- Related files
- Supersedes or related decisions

**Numbering:** sequential, `0001` to whatever. Never re-used.

**Supersession:** when a decision is superseded, the new decision's body references the old (`Supersedes 0007`), and the old decision's status changes to `Superseded by NNNN`. Old decisions never deleted.

**Update triggers:** any architecture, tooling, scope, or interface choice with non-trivial downstream impact. Surfaced via /plan, /wrapup, or by the user directly.

## Templates

All file templates are research-canonical. The planner uses the exact section structures shown in this document. Project-specific extensions are allowed when the conversation surfaces real need (e.g., a "Regulatory constraints" section in vision.md for a HIPAA project), but the template is the starting point and most projects don't need additions.

## What does NOT belong in the operating manual

Per research, the operating manual (AGENTS.md / CLAUDE.md) must NOT contain:

- Long explanations or tutorials — these belong in `docs/` or as on-demand skills
- Frequently changing information — that's what `status.md` is for
- File-by-file codebase descriptions — that's `architecture.md`'s repository map
- Current work-in-progress — that's `planning/current.md`
- TODOs — that's planning or status
- Decisions still being deliberated — those don't exist yet; surface during /plan
- Temporary workarounds since resolved — should be pruned, not preserved

The operating manual is a routing and operating reference, not a project encyclopedia.

## Why this standard exists

### The underlying problem

AI-assisted coding sessions have recurring failure modes that compound across long projects and multiple agents:

- **Scope creep** — agents do a mile when asked for an inch
- **Context loss between sessions** — re-explaining the same project state repeatedly
- **Drift off mission** — agents revisit settled decisions or invent architecture not in the plan
- **Operating manual bloat** — the model reads it but doesn't index well; nothing gets pruned
- **Confusing aspiration with fact** — when plans and status live together, agents treat planned-but-not-shipped as done

The fix isn't a smarter agent. It's a richer, more structured starting context per project — a canonical document set with clear ownership, size caps, and update triggers.

### Convergence in current vendor guidance

OpenAI and Anthropic don't publish identical "one true" project skeletons, but their guidance converges on the same shape:

- One concise always-loaded instruction file
- Scoped rules closer to the code that needs them
- On-demand skills for repeatable procedures
- A living plan for complex work, separate from a status log of reality
- Append-only decision records
- Deterministic validation rather than chat memory

The canonical structure above operationalizes that convergence.

### Why split intent from reality

The biggest single insight in the research: `planning/current.md` describes *intent* (what we plan to do, acceptance criteria, stop conditions); `status.md` describes *reality* (what's actually been built, validation results, blockers, evidence-based). When those live in one file, the agent confuses aspiration with fact. The split is non-negotiable.

### Why this lives in this repo

Both rad-planner 4.0 and rad-session 5.0 reference this file as their canonical spec. The plugins are soft-coupled — either works without the other, but both honor this structure when generating or maintaining project artifacts.

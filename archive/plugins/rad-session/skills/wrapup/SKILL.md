---
name: wrapup
description: >
  End-of-session skill — writes docs/status.md from EVIDENCE (not chat
  synthesis), surfaces candidate decisions for ADR recording, runs cross-doc
  redundancy + contradiction checks via rad-planner validators, prunes the
  operating manual's Operational sections (sectioned-writer rule), archives
  the current plan if the milestone shipped, syncs session files to git. Mode-
  aware (mentor vs dev from .rad/profile). HANDOFF.md and .claude/session-log.md
  retire in v5.0 — docs/status.md replaces both. Trigger when the user says
  "/wrapup", "wrap up", "end of session", "session handoff", "save session
  state", "wrap this up", "close out this session".
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# Session Wrapup

Close the store: write `docs/status.md` from observed evidence, surface candidate decisions the user may want to record as ADRs, run cross-doc maintenance checks, prune the operating manual's Operational sections, archive shipped milestones, sync session files to git. Predictable and deliberate — wrapup is bounded; tomorrow's open should be fast.

**Janitor model:** clean up, ensure everything's in its place, move quickly when nothing's blocking, take time when something genuinely needs synthesis. No churn for ceremony.

> **Status:** Released — the marketplace ships this workflow. The current plugin version lives in `plugin.json` (don't hard-code it here — it only goes stale). Feature additions are marked inline with the version they landed in.

## What changed from v4.0

| v4.0 | v5.0 |
|---|---|
| Wrote `HANDOFF.md` from chat synthesis (Phase 1.3 tagging → narrative) | Writes `docs/status.md` from EVIDENCE: git diff, test output, plan-task state, validator results |
| Wrote `.claude/session-log.md` per session | Session-log retired — `docs/planning/archive/` serves the journal role |
| Phase 1.3 conversation tagging was the primary synthesis pass | Candidate-decision detection (mechanical + soft) is primary; conversation tagging secondary, scoped to ADR prompts only |
| Phase 4 pruned the whole CLAUDE.md | Phase 5 prunes ONLY Operational sections per sectioned-writer rule; Constitution sections never touched |
| Phase 6 committed HANDOFF.md + session-log.md | Phase 7 commits `docs/status.md` + archives + ADRs + pruned manual |
| (no cross-doc checks) | Phase 4 runs `doc-redundancy.py` and `doc-contradiction.py` from rad-planner (advisory findings) |
| (no milestone archive) | Phase 6 detects milestone completion + prompts to archive `current.md` to `planning/archive/` |
| (no work-detection gate) | Phase 0 refuses to run if no work since last status update (saves noise updates) |

## Mode flags

- `--push` — Skip Phase 7.4 push prompt and push the session commit immediately.
- `--no-push` — Skip push entirely; commit locally only.
- Neither push flag → prompt at Phase 7.4 (default).
- `--quick` — Fast wrapup: skip cross-doc checks (Phase 4), skip candidate-decision deep-scan (Phase 3), skip operating manual prune (Phase 5) unconditionally, simpler status update. Use when "I just sat down for an hour, save state and go."
- `--non-interactive` — Suppress prompts (candidate-decision menu, ADR append, archive prompt, push). Tagged decisions land in status.md anyway; the durable DECISIONS.md append is gated by user `y` so non-interactive defaults to skipping. **Cautious mode** — no ADR writes without explicit user input.
- `--auto` *(new in v5.2)* — Productive autonomy mode. No prompts, but candidate decisions are written as DRAFT-banner ADRs to `docs/decisions/NNNN-*.md` so the capture isn't lost. Each draft ADR explicitly labels the rationale as LLM-inferred and surfaces in Phase 8 anomaly block as "⚠ N draft ADRs auto-recorded — review when convenient." Also triggers when a harness-level `<system-reminder>` signals autonomous-mode behavior even without the explicit flag (see Phase 3.0.5). Use for autonomous loops / Auto permission mode where you want the captures but don't want to be interrupted. Distinct from `--non-interactive` (which is cautious / skip).
- `--force` — Override the Phase 0 no-work check. Used when you want a status refresh even though there's no commit activity (e.g., bookkeeping refresh after manual file edits outside session).

## Cross-model note

The phase logic uses explicit evidence-extraction patterns so output is reproducible from evidence regardless of which model tier the session runs in. The status.md content must be derivable from git diff, test output, and plan-task state — not from chat memory or model recall. Evidence is the contract.

**Python launcher.** Code blocks below invoke `python3` for brevity. Use whichever launcher exists — `python3`, else `python`, else the Windows `py` launcher; the validator scripts are launcher-agnostic pure-stdlib. Each Bash call is independent (shell state does not persist between calls), so resolve the launcher in the block that uses it. If none exists, the validator steps degrade gracefully (Phase 4 emits a "validators unavailable" note).

**Announce at start:** "Wrapping up — gathering evidence, writing status.md, surfacing candidate decisions, running cross-doc checks, pruning operating manual Operational sections, archiving milestone if shipped, syncing to git..."

---

## Phase 0: No-work check

If nothing has changed since the last status update, refuse to run. Forcing a noise update erodes status.md's evidence quality.

### 0.1 Evidence inputs

Check three signals:

```bash
# Commits since status.md was last updated
LAST_STATUS_COMMIT=$(git log -1 --format=%H -- docs/status.md 2>/dev/null)
[ -n "$LAST_STATUS_COMMIT" ] && COMMITS_SINCE=$(git rev-list "$LAST_STATUS_COMMIT..HEAD" --count 2>/dev/null || echo 0) || COMMITS_SINCE=0

# Uncommitted changes
DIRTY=$(git status --porcelain 2>/dev/null | wc -l)

# Plan-task changes (acceptance criteria flips)
PLAN_TASK_CHANGES=$(git diff docs/planning/current.md 2>/dev/null | grep -cE '^\+\s*-\s*\[' || echo 0)
```

### 0.2 Decision

- `COMMITS_SINCE > 0` OR `DIRTY > 0` OR `PLAN_TASK_CHANGES > 0` → proceed to Phase 1.
- All zero → refuse:

```
No work detected since last status update.

  Commits since last status: 0
  Uncommitted changes: 0
  Plan acceptance-criteria changes: 0

Nothing to wrap up. Options:
  1. Exit (default) — status.md is already current.
  2. Run anyway with --force to refresh the status.md timestamp.
```

In `--non-interactive` mode, exit silently with `wrapup_action: "skipped_no_work"` in the trailing JSON.

If `--force` is passed, proceed regardless of the check.

---

## Phase 1: Gather evidence (parallel)

All reads in Phase 1 are issued as one parallel batch. The phase numbering is for human readability.

### 1.1 Read config and prior state

- `.rad/profile` — extract `mode`, `agent_scope`, `multi_branch_status` (for Phase 2.1 status-file path and Phase 3 mode-aware surfacing)
- `docs/status.md` (or `docs/status-<current-branch>.md` if multi_branch) — prior status for diff and "last completed" carry-forward filtering
- `docs/planning/current.md` — current plan; acceptance-criteria state, planned changes, current milestone

### 1.2 Read operating manual

Per `agent_scope`:
- `claude_only` → CLAUDE.md
- `codex_only` → AGENTS.md
- `claude_and_codex` → both (AGENTS.md canonical + CLAUDE.md shim)

For Phase 5 prune logic.

### 1.3 Capture git evidence

Run as one combined command:

```bash
git status --porcelain 2>/dev/null && echo "---" && \
git diff --name-only 2>/dev/null && echo "---" && \
git diff --stat 2>/dev/null && echo "---" && \
git log --oneline -10 2>/dev/null && echo "---" && \
git log --since="$(git log -1 --format=%cI -- docs/status.md 2>/dev/null)" --format='%H|%s|%ai' 2>/dev/null && echo "---" && \
git rev-parse --abbrev-ref HEAD 2>/dev/null
```

Capture:
- Current branch
- Uncommitted changes (file list)
- Diff stat (lines added/removed per file)
- Recent commits (last 10)
- Commits since last status update
- Branch name

### 1.4 Detect dependency / schema / env changes (mechanical candidate-decision triggers)

Run mechanical detection for the most common ADR-worthy changes:

```bash
# Dependency additions in package.json (or equivalent)
git diff -- package.json 2>/dev/null | grep -E '^\+\s+"' | grep -v '^\+\s+"version"' || true

# New migration files
git diff --name-only --diff-filter=A 2>/dev/null | grep -E '(migrations|schema)/' || true

# .env.example additions
git diff -- .env.example 2>/dev/null | grep -E '^\+\s*[A-Z_]+=' || true

# New top-level directories
git diff --name-only --diff-filter=A 2>/dev/null | awk -F'/' '{print $1}' | sort -u || true
```

These feed into Phase 3 candidate-decision detection without needing model reasoning.

### 1.5 Optionally run validators

If rad-planner is installed at a sibling path, invoke its validators:

```bash
RAD_PLANNER_SCRIPTS="${plugin_root}/../rad-planner/scripts"

# Plan health check
[ -f "${RAD_PLANNER_SCRIPTS}/plan-lint.py" ] && \
  python3 "${RAD_PLANNER_SCRIPTS}/plan-lint.py" --mode all docs/planning/current.md --json 2>/dev/null

# Status freshness (re-run after Phase 2 writes the new status)
# Cross-doc validators run in Phase 4
```

If validators aren't available (rad-planner not installed), Phase 4 emits a "validators unavailable" note and skips cross-doc checks.

### 1.6 Conversation tagging (scoped, for candidate-decision input only)

Walk the recent conversation window — bounded the same way as v4.0 (most recent of: prior /wrapup signal, PreCompact marker, prior /startup briefing; default cap 40 turns, 15 in `--quick`).

Tag turns labeled `DECISION` (architecture choice, tool selection, naming rule, approach taken — with stated or inferable reason) — these feed Phase 3.

In v5.0, conversation tagging is **scoped to ADR prompts only**. The bulk of status.md content comes from evidence (git, validators, plan state), not from the chat narrative. This is the biggest behavioral shift from v4.0.

Other v4.0 tag categories (`FAIL`, `CORRECTION`, `INSIGHT`, `OPEN`) are NOT carried forward into v5.0 status.md — they were narrative-shaped, and v5.0 is evidence-shaped. If a real "what didn't work" or "open question" matters, it surfaces through plan-task state (acceptance criterion still unchecked) or git evidence (file changed but never tested), not from chat synthesis.

---

## Phase 2: Write docs/status.md from evidence

Write the canonical handoff per the 8-section schema in [`docs/status-md-schema.md`](../../../../docs/status-md-schema.md). Every field has a documented inference policy (DIRECT / HEURISTIC / SYNTHESIZED / USER-STATED). Status.md is **evidence-grounded** — the planner's "intent" lives in current.md; the session's "reality" lives in status.md.

### 2.1 Target path

```bash
if multi_branch_status:
  STATUS_PATH=docs/status-${current_branch}.md
else:
  STATUS_PATH=docs/status.md
```

### 2.2 Section-by-section content

For each of the 8 sections, populate from evidence. Reference `docs/status-md-schema.md` for the exact inference policy per field.

**1. Current state** (overwrite)
- Branch / worktree: DIRECT from `git rev-parse --abbrev-ref HEAD`
- Current milestone: DIRECT from `docs/planning/current.md` "Current milestone" section
- Overall status: HEURISTIC per the schema (on_track / blocked / validating / needs_decision)

**2. Last completed** (rewrite, top 5–10 items)
- HEURISTIC consolidation of commits since last status + AC checkboxes that flipped to `[x]`
- Each item: concrete completion (file path + what was done), not narrative
- DROP items already in the previous status.md's "Last completed" — that's history now

**3. Files changed recently** (rewrite, top 10)
- DIRECT from `git diff --name-only <last_status_commit>..HEAD` (or current diff if uncommitted)
- Path + one-line annotation per file (inferred from commit messages or diff content)
- If > 10 files, prepend header: "Recent activity touched N files; showing 10 most-recently-modified:"

**4. Latest validation results** (rewrite, evidence-strict)
- DIRECT: commands that actually ran in this session, with their actual pass/fail/partial/not-run results
- USER-STATED: results the user reported during the session
- If no validation ran this session: write "No validation run this session — last run YYYY-MM-DD with results: [from prior status.md]" (DO NOT fabricate)

**5. Decisions made during execution** (rewrite from Phase 3 output)
- HEURISTIC candidates + USER-STATED confirmations from Phase 3
- Items marked "recorded in ADR" can be dropped at next wrapup; items "no" or "pending" persist
- Format: `Decision: ...` / `Why: ...` / `Recorded in ADR? yes (decisions/NNNN-...) | no | pending`

**6. Known issues or blockers** (rewrite)
- DIRECT: failed validations from Phase 1 that weren't fixed in this session
- USER-STATED: blockers mentioned during the session
- HEURISTIC: open questions in current.md older than N days

**7. Next recommended step** (overwrite)
- SYNTHESIZED from current.md current milestone + acceptance criteria + Notes for the next session + any blockers from section 6
- 3-part format: most likely next action / first file to read / first question (if applicable)
- Bounded by current.md content — cannot invent goals

**8. If restarting from scratch** (overwrite)
- Read order (DIRECT): operating manual file (per agent_scope) + planning/current.md + architecture.md
- Resume question: SYNTHESIZED from section 7's content
- Conditional vision.md inclusion if user-facing work is in scope

### 2.3 Write the file

Write `STATUS_PATH` with the populated 8-section content. Sections that are explicitly empty MUST say so ("No data this session" / "No validation run this session — last run YYYY-MM-DD") rather than be silently blank.

---

## Phase 3: Candidate-decision detection + mode-aware surfacing

Surface decisions that may want to become ADRs. Combines mechanical triggers (Phase 1.4) and conversation tagging (Phase 1.6).

### 3.0 Skip conditions

Skip Phase 3 entirely if any of these hold:
- `--quick` mode (skip the deep scan; mechanical triggers still feed status.md Phase 2.5)
- `--non-interactive` (no prompt possible; candidates land in status.md but no ADR append — cautious CI default)
- Zero mechanical triggers AND zero `DECISION`-tagged turns

### 3.0.5 Autonomy detection (NEW in v5.2)

Detect whether the model is running under harness-level autonomy. Two signals:

1. **Explicit flag:** `--auto` was passed to `/wrapup` invocation
2. **Harness hint:** a `<system-reminder>` is present in the current conversation that signals autonomous-mode behavior (e.g., "the user has asked to work without stopping for clarifying questions", "auto-accept", or equivalent)

If either signal is present, Phase 3 enters **Auto mode** (sub-section 3.2 has a third branch for this; sub-section 3.3 writes draft-banner ADRs instead of prompting).

If neither signal is present and `--non-interactive` is NOT set, run Phase 3 in the normal interactive mode based on `.rad/profile` `mode` field (mentor or dev).

**Note on signal interpretation:** the harness autonomy hint covers tool-use approvals (Write, Edit, Bash). It does NOT cover the Case C guard rail in `/startup` Phase 0.5 (data-loss-protected). For `/wrapup` Phase 3 specifically — where the user's downside is "an auto-recorded ADR may have wrong rationale" rather than "I lose work" — the right behavior under autonomy is to write the ADR with a DRAFT banner so the user can review at their own pace. Better than skipping the capture entirely and losing the record.

### 3.1 Build the candidate list

Combine:
- Mechanical triggers from Phase 1.4 (new deps, schema changes, env additions, new top-level directories) → each becomes a candidate
- `DECISION`-tagged turns from Phase 1.6 conversation walk

For each candidate, compute:
- **Title:** 8-word max summary
- **Why:** one-clause rationale (from commit message, tag content, or "TBD — fill in")
- **Evidence:** specific file path, commit SHA, or turn reference

### 3.2 Mode-aware surfacing (read .rad/profile mode)

**Mentor mode** (`mode = mentor` in .rad/profile, or default):

For each candidate, show teaching + draft entry:

```
Candidate decision (mentor mode):

  Title: Adopt React Query for server-state management
  Why: Replaces the existing fetch-with-useEffect pattern (5 sites). React Query handles caching, retry, and revalidation that we've been re-implementing inconsistently.
  Evidence: package.json line 23 added "@tanstack/react-query"; commits a1b2c3, d4e5f6

  Why this is typically worth an ADR:
    Adding dependencies commits future code to that library's API and lifecycle.
    Without an ADR, the next session won't know whether to use React Query or
    fall back to the prior fetch-with-useEffect pattern when adding a new
    server-state read.

  Draft entry for decisions/0007-react-query.md:
    [full ADR template populated — Context, Decision, Why, Alternatives, Consequences]

Actions:
  [a] Accept — write decisions/0007-react-query.md as drafted
  [e] Edit — open the draft for your edits before writing
  [s] Skip — record in status.md only, no ADR
  [d] Defer — record in status.md as "pending — revisit next wrapup"
```

**Dev mode** (`mode = dev`):

Quick list, skip-friendly:

```
Candidate decisions surfaced:
  1. Adopt React Query — Evidence: pkg.json + 2 commits
  2. New migration: 0042_user_preferences.sql — schema change
  3. Add ANTHROPIC_API_KEY to .env.example — env addition

Actions per candidate: [a]ccept / [s]kip / [d]efer
Or: [A] accept all, [S] skip all, [D] defer all
```

**Auto mode** (detected per 3.0.5: `--auto` flag OR harness autonomy hint):

No prompt. Write all candidates as draft-banner ADRs directly. Surface counts in Phase 8 anomaly block.

```
(no terminal prompt — auto-recording)

Phase 8 anomaly will surface:
⚠ N draft ADRs auto-recorded this session: 0007, 0008, 0009 —
  review when convenient. Each carries a DRAFT banner; the rationale
  is LLM-inferred. Promote each ADR by removing the banner once you
  confirm the rationale matches your intent.
```

The DRAFT banner inserted at the top of each auto-recorded ADR (immediately under the H1 title):

```markdown
> **DRAFT — auto-recorded by `/wrapup`** under harness autonomy. Rationale was
> LLM-inferred from commit messages and changed files; review and revise.
> Remove this banner to promote the ADR to a confirmed decision.
```

Status.md section 5 entry under Auto mode reads:

```markdown
**Decision: Adopt React Query for server-state management**
- Status: DRAFT auto-recorded at decisions/0007-react-query.md
- Evidence: package.json line 23; commits a1b2c3, d4e5f6
- Action needed: review the LLM-inferred rationale; remove DRAFT banner to confirm
```

The point of Auto mode: capture the candidate decision (it would be lost otherwise) without falsely claiming user confirmation. The user can review draft ADRs at the next `/startup` (which surfaces them in the briefing as a soft-warning line) or whenever convenient.

### 3.3 Apply user decisions

**Default (mentor/dev mode):** for each accepted candidate:
- Compute next ADR sequence number (read decisions/ for highest NNNN, +1)
- Write `docs/decisions/NNNN-<slug>.md` with the canonical template (Context / Decision / Why / Alternatives / Consequences / Related files)
- Update status.md section 5 (Decisions made during execution) to mark `Recorded in ADR? yes (decisions/NNNN-...)`

For skipped: include in status.md section 5 with `Recorded in ADR? no` and capture the reason.

For deferred: include in status.md section 5 with `Recorded in ADR? pending — revisit next wrapup`.

**Auto mode (detected per 3.0.5):** for every candidate:
- Compute next ADR sequence number (read decisions/ for highest NNNN, +1)
- Write `docs/decisions/NNNN-<slug>.md` with the canonical template **plus the DRAFT auto-recorded banner immediately under H1** (template shown in 3.2 Auto mode block)
- Update status.md section 5 with the "Status: DRAFT auto-recorded at decisions/NNNN-..." format
- No "skip" or "defer" outcomes possible under Auto — every candidate gets a draft ADR. Discarding noise is the user's review-time job.

### 3.4 Notify

**Default mode:** emit one line per outcome to the Phase 8 anomaly block:
```
DECISIONS.md: appended N entries (NNNN–NNNN).
```

**Auto mode:** emit a single anomaly-block line that explicitly flags review-needed:
```
⚠ N draft ADRs auto-recorded this session: NNNN, NNNN, NNNN — review when convenient.
  Each carries a "DRAFT — auto-recorded" banner. Remove the banner on each to promote.
```

The next `/startup` briefing surfaces draft-banner ADR count as part of its strategic-doc gap-check, so the user sees pending review items at session open without needing to remember to look.

---

## Phase 4: Cross-doc checks (NEW)

Run rad-planner's cross-doc validators against the project's strategic docs. Findings are **advisory** — surface for user review, not blocking.

### 4.0 Skip conditions

Skip Phase 4 if any of these hold:
- `--quick` mode
- rad-planner scripts not available at the expected sibling path
- No strategic docs exist (vision.md / architecture.md / decisions/) — no cross-doc comparisons possible

### 4.1 Run validators

```bash
RAD_PLANNER_SCRIPTS="${plugin_root}/../rad-planner/scripts"

# Cross-doc redundancy
python3 "${RAD_PLANNER_SCRIPTS}/doc-redundancy.py" "$PWD" --json 2>/dev/null > /tmp/rad-redundancy.json

# Cross-doc contradiction
python3 "${RAD_PLANNER_SCRIPTS}/doc-contradiction.py" "$PWD" --json 2>/dev/null > /tmp/rad-contradiction.json

# User-owned content audit (NEW in v5.6 — visibility pass over the
# operating manual's user-owned sections; neither plugin modifies these,
# but staleness can be flagged for the user to act on)
python3 "${RAD_PLANNER_SCRIPTS}/audit-user-content.py" "$PWD" --json 2>/dev/null > /tmp/rad-user-content.json
```

### 4.2 Surface findings

Parse the JSON outputs.

**Redundancy findings:**
- MEDIUM (similarity ≥ 0.85): show as "Likely duplicate — consider referencing rather than copying"
- LOW (similarity in [threshold, 0.85)): show as "Related content — review for canonical placement"

**Contradiction findings:**
- MEDIUM (overlap ≥ 0.6): show as "Potential contradiction — vision non-goal overlaps with current AC"
- LOW (overlap in [threshold, 0.6)): show with note "may be a real contradiction or unrelated overlap"

**User-owned content findings (v5.6):**
- HIGH (`dead-path`): show as "Path referenced in user-owned section doesn't exist — confirm whether to update or remove the reference"
- MEDIUM (`orphan-terminology`): show as "Title-Case terminology in user-owned section appears nowhere else in the repo — possibly stale (brand reset, retired concept, renamed system)"

Display under a single block in the Phase 8 anomaly output (only if any findings):

```
Cross-doc maintenance:
  Redundancies: N (M MEDIUM, K LOW) — see /tmp/rad-redundancy.json or re-run doc-redundancy.py
  Contradictions: N (M MEDIUM, K LOW) — see /tmp/rad-contradiction.json or re-run doc-contradiction.py
  User-owned content: N (M HIGH, K MEDIUM) — see /tmp/rad-user-content.json or re-run audit-user-content.py
  Action: review for canonical placement; resolve before next /plan if blocking.
```

Cross-doc findings are advisory — no automatic file changes. The user decides what to fix.

**Honesty about the user-owned audit (v5.6):** the audit reads user-owned sections (anything not in either plugin's owned-section list — see `docs/cross-plugin-contracts.md`) but **does not modify them**. The single-writer rule keeps user-authored content safe; this advisory layer surfaces signals without crossing that boundary. The two heuristics in v1 catch **orphan terminology** (Title-Case phrases appearing only in this section, often a brand reset or renamed system that didn't propagate) and **dead paths** (markdown link or path-shaped tokens to files that no longer exist). False positives surface as confidently as true positives — the user is the final judge.

---

## Phase 5: Operating manual prune (Operational sections only)

Prune the operating manual per the sectioned-writer rule. ONLY Operational sections may be touched — Constitution sections are owned by rad-planner and must never be modified by /wrapup.

### 5.0 Skip conditions

Skip Phase 5 entirely if any of these hold:
- `--quick` mode
- Operating manual unchanged this session (`git diff --quiet HEAD -- <manual_path>` returns 0 AND last commit modifying it is older than last status.md commit)
- Operating manual doesn't exist (no work to prune)

If skipped, log: `Operating manual unchanged since last wrapup — prune skipped.`

### 5.1 Determine target file(s)

Per `agent_scope` from .rad/profile:
- `claude_only` → prune `CLAUDE.md`
- `codex_only` → prune `AGENTS.md`
- `claude_and_codex` → prune both (separate evaluations; CLAUDE.md may have shim-specific Operational content + `@AGENTS.md` import; AGENTS.md has its own Operational sections)

### 5.2 Section ownership table

| Section | Owner | /wrapup may prune? |
|---|---|---|
| Project | rad-planner | **NO** |
| Read order | rad-planner | **NO** |
| Hard boundaries | rad-planner | **NO** |
| Engineering rules | rad-planner | **NO** |
| Lanes (v4.7+) | rad-planner | **NO** — role-separation contract, never touched |
| Definition of done | rad-planner | **NO** |
| Escalate triggers | rad-planner | **NO** |
| Commands | rad-session | **YES** — prune stale entries |
| Compact Instructions (CLAUDE.md only) | rad-session | **YES** |
| Claude-specific behavior (CLAUDE.md only) | rad-session | **YES** |
| `@AGENTS.md` import line (CLAUDE.md shim) | rad-session | **YES** — only to update or remove import |
| User-added sections (any other heading) | User | **NO** — preserve |

### 5.3 Pruning heuristics (Operational sections only)

For each prunable section, evaluate:

| Question | If YES |
|----------|--------|
| Is this command referencing a binary or path that no longer exists? | Flag in diff; remove with user approval |
| Is this Claude-specific behavior referencing a workflow that retired? (e.g., "merge CLAUDE-FRAGMENT.md" — that's v4.0; retired in v5.0) | Flag in diff; remove with user approval |
| Is this entry duplicating what `docs/status.md` or `docs/planning/current.md` now captures? | Remove |
| Does this Compact Instructions section reference fields that don't exist in current.md? | Remove the dead reference |

If you encounter ANY section outside the prunable list — including Constitution sections, user-added sections, or unknown headings — preserve it. Surface in the output: "Preserved user/Constitution sections: <list>."

### 5.4 Show the diff

```
Operating manual changes ({CLAUDE.md | AGENTS.md | both}):
  - Removed: "[quoted text]" ([reason])
  - Updated: [section] — [what changed]
  - Preserved (Constitution + user sections): [N lines]
```

### 5.5 Auto-proceed threshold

Auto-proceed without prompting if ALL of these hold:
1. Total removals ≤ 3 lines/bullets
2. No removed line is from a Constitution-owned section (defensive guard)
3. No removed line contains the word "must", "never", "always", "required", or "forbidden"
4. Not the first wrapup on this project

Otherwise: wait for user approval ("looks good" / "fine" / "ok" → proceed; "undo X" → revert that change).

---

## Phase 6: Milestone-shipped archive (NEW)

Detect if the current milestone is complete and offer to archive `current.md` to `planning/archive/`.

### 6.0 Skip conditions

Skip Phase 6 if any of these hold:
- `--quick` mode
- `--non-interactive` mode (no prompt possible)
- `docs/planning/current.md` doesn't exist
- Current milestone hasn't shipped (Phase 6.1 check)

### 6.1 Milestone-shipped detection

Read acceptance criteria from `docs/planning/current.md`. A milestone is "shipped" when:
- All acceptance criteria are `[x]` checked
- OR the user explicitly marked completion in this session

Heuristic: count `[x]` vs `[ ]` checkboxes in the Acceptance criteria section. If 100% checked → milestone shipped.

### 6.2 Prompt the user

```
Milestone M{N} ({theme from current.md}) appears complete:
  Acceptance criteria: N/N checked
  Status: on track

Archive current.md to docs/planning/archive/YYYY-MM-DD-M{N}-{slug}.md and prepare for the next milestone? (y/N/edit)

  [y] Archive — move current.md to planning/archive/; you'll run /rad-planner:plan --improve to set up the next milestone
  [N] Skip — leave current.md alone (default)
  [edit] Mark some criteria as unverified and re-evaluate
```

### 6.3 Execute

On `y`:
- `mkdir -p docs/planning/archive`
- `git mv docs/planning/current.md docs/planning/archive/YYYY-MM-DD-M{N}-{slug}.md` (per git so history is preserved)
- Note in Phase 8 output: `Milestone M{N} archived to docs/planning/archive/YYYY-MM-DD-M{N}-{slug}.md. Run /rad-planner:plan --improve for the next milestone.`

On `N`: no action.

On `edit`: show acceptance criteria, let user uncheck some, re-evaluate.

---

## Phase 7: Cross-machine sync (auto-commit + prompted push)

Keep session files in sync across machines. Behavior aligns with v4.0 but the file list is updated for v5.0.

### 7.0 Skip conditions

Skip Phase 7 entirely if any of these hold:
- Not a git repo
- All target files unchanged
- In-progress merge / rebase / cherry-pick

### 7.1 Stage only session files

**Critical: never `git add -A` or `git add .`** Stage explicit paths only:

```bash
# Always stage status.md (Phase 2 wrote it)
git add docs/status.md
# Also stage status-<branch>.md if multi-branch
[ -n "$multi_branch_status_file" ] && git add "$multi_branch_status_file"

# Stage current.md if Phase 6 archived it
[ "$milestone_archived" = "true" ] && git add docs/planning/archive/

# Stage ADRs added in Phase 3
[ "$adrs_added" = "true" ] && git add docs/decisions/

# Stage operating manual if Phase 5 pruned it
[ "$manual_pruned" = "true" ] && git add CLAUDE.md AGENTS.md 2>/dev/null
```

If `git diff --cached --quiet`, skip the rest of Phase 7 silently.

### 7.2 Auto-commit

```bash
HOSTNAME="${HOSTNAME:-${COMPUTERNAME:-$(hostname 2>/dev/null || echo unknown)}}"
DATE=$(date +%Y-%m-%d)
# STATUS is from status.md "Current state" Overall status field
git commit -m "session: ${DATE} on ${HOSTNAME} — ${STATUS}"
```

### 7.3 Push decision

Priority order:
1. `--push` flag → push without prompting
2. `--no-push` flag → skip push
3. `--non-interactive` → skip push silently
4. Otherwise → prompt:
   ```
   Push session files to origin? (y/N)
   ```
   Default: skip (N). Y → push.

### 7.4 Execute push

If branch has upstream:
```bash
git push
```

On rejection: do not force, do not retry. Report:
```
⚠ Push rejected (likely diverged from origin). The session commit is safe locally. Resolve with: git pull --rebase  then  git push
```

### 7.5 Sync summary

For the Phase 8 anomaly block:
- Committed + pushed: `Sync: committed + pushed (<short-sha>)`
- Committed, push declined: `Sync: committed locally (<short-sha>) — N unpushed session commits`
- Committed, push failed: `Sync: committed locally (<short-sha>) — push rejected, resolve manually`

---

## Phase 8: Anomaly-gated final output

Run size assertions silently. Emit verbose output only when something anomalous happened.

### 8.1 Size assertions

```bash
STATUS_LINES=$(wc -l < docs/status.md 2>/dev/null || echo 0)
STATUS_BYTES=$(wc -c < docs/status.md 2>/dev/null || echo 0)
```

Status.md soft caps per section (from `docs/status-md-schema.md`):
- Section 1: < 5 lines
- Section 2: 5–10 bullets
- Section 3: 10 paths
- Section 6: < 10 blockers
- Section 7: 3–5 lines
- Section 8: 3–6 files + 1 resume line

Section 4 and 5 have no caps (strict evidence + variable candidates).

### 8.2 Anomaly checklist

An anomaly exists if any of these hold:
- `STATUS_LINES > 200` (status.md is getting bloated)
- Phase 3 appended ADRs to `docs/decisions/` (worth surfacing — DECISIONS just changed permanently)
- Phase 4 found cross-doc redundancies or contradictions (worth surfacing for user review)
- Phase 5 pruned the operating manual (file changed)
- Phase 6 archived a milestone (state shifted)
- Phase 7 push was rejected, declined explicitly, or skipped due to dirty tree / missing upstream

### 8.3 Success path (no anomalies)

Emit exactly one line:

```
Session wrapped up. Sync: pushed (<short-sha>).
```

If sync was skipped, drop the `Sync:` clause:

```
Session wrapped up.
```

### 8.4 Anomaly path

Emit the anomalous fields only, prefixed with `⚠` where appropriate:

```
Session wrapped up:
  ⚠ status.md: <N> lines — over soft cap (typical: <150 lines). Consider grooming.
  DECISIONS.md: appended N entries (NNNN–NNNN). Edit consequences as needed.
  Cross-doc: N redundancies, M contradictions surfaced (advisory; see /tmp/rad-*.json).
  Operating manual: pruned N changes (auto-proceeded | confirmed).
  Milestone M{N} archived to docs/planning/archive/YYYY-MM-DD-M{N}-{slug}.md.
  ⚠ Sync: push rejected — resolve with: git pull --rebase  then  git push
```

Each line conditional on its own anomaly. Do not mix success-path lines into the anomaly block.

---

## What this skill does NOT do

- Does not write `HANDOFF.md` (retired in v5.0 — `docs/status.md` replaces it)
- Does not write or maintain `.claude/session-log.md` (retired in v5.0 — `planning/archive/` serves the journal role)
- Does not write Constitution sections of the operating manual (rad-planner's at /plan M6)
- Does not write strategic docs (vision.md, architecture.md, planning/current.md — those are rad-planner or human-owned)
- Does not run `git add -A` or `git add .` (always stages explicit paths)
- Does not force-push (`git push --force`) under any circumstances
- Does not merge or rebase automatically
- Does not fabricate validation results — Section 4 is evidence-only

## Key references

**Canonical spec docs (top-level):**

- [`docs/doc-conventions.md`](../../../../docs/doc-conventions.md) — canonical file structure
- [`docs/cross-plugin-contracts.md`](../../../../docs/cross-plugin-contracts.md) — single-writer rule, sectioned-writer exception for operating manual
- [`docs/status-md-schema.md`](../../../../docs/status-md-schema.md) — 8-section status schema with evidence sources and inference policies

**rad-planner validators (used by Phase 4):**

- `${plugin_root}/../rad-planner/scripts/doc-redundancy.py` — cross-doc Jaccard duplicate detection
- `${plugin_root}/../rad-planner/scripts/doc-contradiction.py` — vision non-goals vs current ACs
- `${plugin_root}/../rad-planner/scripts/plan-lint.py` — planning/current.md health
- `${plugin_root}/../rad-planner/scripts/status-validator.py` — status.md schema validator

**Plugin internals:**

- `scripts/README.md` — full script documentation

## Mode flags (recap)

- `--push` / `--no-push` — push behavior override
- `--quick` — skip Phase 3 deep scan, Phase 4 cross-doc checks, Phase 5 prune
- `--non-interactive` — suppress all prompts (Phase 3 menu, Phase 6 archive prompt, Phase 7 push)
- `--force` — override Phase 0 no-work check

# Session Handoff — rad-planner + rad-session plugin work

**Date:** 2026-05-16
**Purpose:** Comprehensive pass-along for a fresh chat. Captures what's been shipped, what's been discussed but queued, design principles established, user context, and active improvement threads.
**Status:** Temporary. Move out of repo when no longer useful.
**Audience:** A fresh Claude session continuing improvements to rad-planner and rad-session.

---

## TL;DR for the next chat

We've shipped four sequential patches across two plugins in the last ~24 hours. All are on `origin/main`. The plugins are functional but several refinements have been discussed and queued. The user (Ryan) is actively testing the plugins against real projects (Faunero, ryandesjardins.com) and surfacing real-session defects which become patch material. Pattern: user reports defect from a real test → I diagnose → we discuss the fix → patch ships.

**Current versions on origin/main:**

| File | Version |
|---|---|
| `plugins/rad-planner/.claude-plugin/plugin.json` | 4.2.0 |
| `plugins/rad-session/.claude-plugin/plugin.json` | 5.3.0 |
| `.claude-plugin/marketplace.json` | 1.8.1 |

---

## Patch history (chronological, with context)

### rad-session 5.0 (commits `eda1bc3`, `783e909`, `8cbbb54`)

**Context:** This session opened mid-flight on the v5.0 milestone-driven rebuild — M1-M4 SKILL.md rewrites had landed in an earlier session; this session completed M5 (fixtures) and M6 (release prep).

**Shipped:**
- M1-M4: canonical doc structure + sectioned-writer + agent scope routing for /init, /startup, /wrapup
- M5: 4 end-to-end fixtures (codex-only / claude-and-codex / nonstandard-manual / dev-mode), all validators pass
- M6: plugin.json 4.0 → 5.0, marketplace 1.6.0 → 1.7.0, README rewrites, reference sweep
- HANDOFF.md retired → docs/status.md (evidence-based)
- .claude/session-log.md retired → docs/planning/archive/

### rad-session 5.1 (commit `7bf17ff`, marketplace 1.7.1)

**Context:** User pointed out `/init` conflicts with Claude Code's built-in `/init` skill. They had originally suggested folding bootstrap into `/startup` so there'd be no second command to remember.

**Shipped:**
- `/init` skill deleted
- `/startup` Phase 0.5 auto-bootstraps on first run (detects missing `.rad/profile` / operating manual / `docs/status.md`)
- New flags: `--bootstrap`, `--no-bootstrap`, `--agents <scope>`, `--non-interactive`, `--dry-run`
- Cross-plugin docs updated (cross-plugin-contracts.md, doc-conventions.md, plan-architect.md, plan SKILL.md)

### rad-planner 4.1 (commit `9ee6d17`)

**Context:** User showed a transcript of /plan running unilaterally on a single paragraph for ryandesjardins.com (greenfield test). 8 ADRs produced without asking a single question. The agent had attributed it to a `<system-reminder>` about "not asking clarifying questions." User correctly diagnosed: planning should be collaborative regardless of permission mode.

**Shipped:**
- Third top-level CRITICAL block declaring `/plan` conversational by design
- Per-phase "Conversational gate" blockquotes on M1, M2, M3, M4, M5
- `--auto` flag (the ONLY way to suppress M1-M5 dialogue)
- `--auto` does NOT write ADRs — candidate decisions land in `docs/planning/proposed-decisions.md`
- DRAFT banners on all `--auto` output files
- Mandatory trade-off banner in `--auto` final summary
- `--auto` distinct from `--non-interactive`

### rad-session 5.2 (commit `77e8081`, marketplace 1.8.0)

**Context:** Companion to rad-planner 4.1. Permission-mode-safety principle: operations split by asymmetry of downside.

**Shipped:**
- `/startup` Phase 0.5 Case C guard rail: data-loss-protected (always prompts regardless of Auto/Bypass/--non-interactive) because silent overwrite of operating manual content is hard to recover
- `/wrapup` Phase 3 new `--auto` mode: writes draft-banner ADRs to `docs/decisions/NNNN-*.md` so captures aren't lost when downside is just inferred rationale
- `/startup` Phase 1.5.1 (new): surfaces pending draft ADRs at next session open
- Phase 3.0.5 Autonomy detection: explicit `--auto` flag OR `<system-reminder>` hint
- DRAFT banner template: `> **DRAFT — auto-recorded by /wrapup**...`

### Second ryandesjardins.com test (validation of v4.1)

User re-ran the greenfield test on a fresh blank directory with the identical prompt. The agent correctly:
- Cited the v4.1 patch language nearly verbatim ("system-reminders about not asking clarifying questions apply to tool-approval prompts, not planning dialogue")
- Cited both saved memory AND skill protocol as reasoning (defense-in-depth)
- Stopped at M0 agent_scope question rather than steamrolling

**Strong substantive evidence the patch worked** — model variance can't explain the agent quoting language that didn't exist before the patch.

### rad-planner 4.2 (commit `c2f9056`)

**Context:** User showed a Faunero `/plan --improve` transcript where the agent correctly parked canonical doc emission (Faunero uses a custom bit-by-bit structure) but then produced a 9-sub-section consolidation deliverable without asking what scope of work the user wanted. v4.1 covered M1-M5 dialogue but didn't cover substantive work in non-canonical shapes.

**Shipped:**
- New **M0.5 scope-confirmation hard gate** between M0 (discovery) and M1 (Constitution)
- Surfaces discovery summary + inferred scope + three options (confirm / different depth / redirect)
- Depth-options menu adapts to entry point (improve / full / drift / pivot)
- Fires on ALL entry points and ALL modes including `--auto` — autonomy is for the WORK, not the SCOPE DECISION
- `--non-interactive`: emits inferred scope as JSON + `awaiting_user_review = ["scope_confirmation"]`, exits (no backdoor)
- Discovery state schema gains `scope_confirmation` field

### rad-session 5.3 (commit `801b0b0`)

**Context:** User ran /startup and got zero output. Reported feeling like they didn't know if anything had happened. Earlier in the conversation I had over-recommended a "minimal text" design; the model applied it preemptively to a live run, producing total silence.

**Shipped:**
- **Floor of one line** on `/startup` — never zero output
- Routine confirmation template: `Routine open. docs/status.md fresh (N days, M{X} {Y}/{Z} ACs done). Read it to resume.`
- Anomalies stack above the floor; the floor always appears
- Routine confirmation line REPLACES the verbose Full Briefing when state is routine and no non-status content needs surfacing
- Doorman-model vocabulary aligned with rad-planner M0.5 (cross-plugin consistency)

### marketplace 1.8.1 (commit `40d0dc9`)

Marketplace bump shipping the v4.2 + v5.3 pair as "the user-confirmation-surface pair." Top-level README marketplace blurb updated.

### Corrupt manifest fix (commit `bb461f1`)

**Context:** User reported plugin loader error: "Plugin rad-session has a corrupt manifest file ... JSON parse error: Expected '}'"

**Root cause:** v5.2 description paragraph (shipped in `77e8081`) contained unescaped inner double quotes around the phrase `"an auto-recorded ADR may have wrong rationale,"`. JSON string values can't contain unescaped `"` — they must be `\"`. The bug shipped with v5.2 but didn't surface until the loader's cache refreshed.

**Fix:** Escaped the inner quotes to `\"an auto-recorded ADR may have wrong rationale,\"`. No version bump (manifest correction, not behavior change).

**Validated post-fix:** all three manifests parse cleanly.

---

## Active design principles (load-bearing)

These principles emerged through this conversation series and now drive both plugins' behavior:

### 1. Conversational by design

`/plan` is multi-phase dialogue. M1-M5 each require explicit user input. M6 doc emission requires `user_approval: true` hard gate. The skill's value is in the questions asked and answers given, not in producing artifacts. (v4.1)

### 2. Discovery → confirm scope → produce work

After M0 mechanical discovery, `/plan` MUST pause at M0.5 with discovery summary + inferred scope + three options before any substantive work. Applies to ALL entry points and ALL modes including `--auto`. (v4.2)

### 3. Confirm the skill ran even when there's nothing to say

`/startup` must produce at least one user-visible line even in the cleanest routine case. Silent completion violates the doorman model. The user just invoked the command and needs to know it ran. (v5.3)

### 4. Permission-mode autonomy applies to tool approvals, not to substantive decisions

Harness signals (Auto / Bypass / `<system-reminder>`) about not asking clarifying questions cover bash / Write / Edit / git / MCP approvals. They do NOT cover M1-M5 planning dialogue, M0.5 scope confirmation, the Case C overwrite guard rail, or any decision where the user's downside is asymmetric. (v4.1, v4.2, v5.2)

### 5. Productive autonomy ≠ skipping the confirmation surface

`--auto` is opt-in unattended *execution at confirmed scope*, not unattended *scope decision*. It still respects M0.5 in `/plan`. Even autonomous capture in `/wrapup` Phase 3 writes draft-banner ADRs (capture preserved, rationale flagged as LLM-inferred for user review). (v4.1, v5.2)

### 6. Asymmetric downside protection

Operations split by recoverability of failure:
- Hard-recover downside (data loss in Case C overwrite) → always prompt, regardless of mode
- Soft-recover downside (auto-recorded ADR with inferred rationale) → write with DRAFT banner, surface for review later (v5.2)

### 7. status.md is canonical; agents read it, don't paraphrase it

`/wrapup` writes status.md from evidence. `/startup` points the user at status.md rather than re-narrating its contents. The agent's job in /startup is to surface anomalies + new context + a confirmation line, not to duplicate what status.md already says. (v5.0 + v5.3)

### 8. Doorman model

`/startup` is "quick, deliberate, no ceremony." Steady-state target under 5 seconds. Bootstrap path (first run only) is a one-time janitor pass. (v5.0, v5.1, v5.3)

---

## Queued ideas (discussed but not shipped)

### 1. project-story skill in rad-writer (or similar)

**Discussion:** User generated a `PROJECT-STORY.md` document for Faunero — a layperson-friendly narrative explaining the project (2,500 words, conversational, no ADR numbers without context). User specifically liked it for the "non-dev vibe coder learning" audience and asked whether the workflow should produce this kind of artifact automatically.

**Proposed design:**
- New `/rad-writer:project-story` skill
- Reads canonical doc set (vision.md, architecture.md, planning/current.md, roadmap.md, decisions/*.md)
- Produces layperson narrative following the Faunero template structure
- Writes to `PROJECT-STORY.md` at root (untracked by default) or `docs/scratch/`
- Regeneratable; `--diff` mode for tracking narrative changes
- Surfaced as recommended-next-step at `/plan` M6 completion and `/wrapup` milestone-shipped

**Template structure (13 sections):**
1. One-line vision sentence as scope test
2. Two-phase or staged product framing with recurring metaphor
3. Who it's for, in build order
4. What it explicitly is NOT
5. How the money works (or value layer)
6. Why we paused for planning
7. What we decided (simple list)
8. Where we are right now
9. How the implementation plan gets formed (before any code)
10. What the user will see when it ships
11. What's not done yet (honest list)
12. What changed by doing all this
13. The bottom line

**Status:** Not shipped. Queued for a focused future session.

### 2. Decisions-in-flight middle layer

**Discussion:** Faunero's /wrapup correctly deferred ADR creation for in-progress 17c sub-decisions ("will roll into a single 17c ADR after that deep-dive fully locks"). That's good judgment, but the intermediate sub-locks live in status.md §5 which is session-scoped and overwritten each wrapup. If the deep-dive stretches across 4-5 sessions, the trail of intermediate decisions could be lost.

**Gap identified:** The canonical doc structure has `decisions/*.md` (too final for in-flight sub-locks) and `planning/current.md` (active milestone, not for deep-dive sub-locks) but no slot for "decisions accumulating during a multi-session deep-dive."

**Proposed pattern (user-driven, not auto-generated):**
- `docs/planning/<topic>-working-decisions.md` as a user-added scratch doc
- Accumulates sub-locks during the deep-dive
- Gets folded into the final ADR and archived when the deep-dive locks

**Status:** Noted as a pattern, no skill/contract change shipped.

### 3. doc-redundancy.py layer-aware distinction

**Discussion:** Faunero's /wrapup surfaced 30 redundancy findings (20 MEDIUM, 10 LOW), but most were architecture.md ↔ ADR overlap that's EXPECTED by design (architecture describes what exists; ADRs say why decisions were made; both naturally reference Worker routes / tier entitlements / invariants).

**Proposed refinement:** doc-redundancy.py could distinguish:
- Layer overlap (architecture.md ↔ ADRs) → OK, expected
- Peer overlap (two ADRs both defining tier entitlements) → bad

**Status:** Refinement, not a bug. Not shipped.

### 4. JSON-strict-parse step in plugin-validator

**Discussion:** The corrupt-manifest bug (commit `bb461f1`) was an unescaped quote in a string value. The plugin-validator inspected manifest structure but didn't catch the literal JSON parse error. Adding a JSON-strict-parse step before structural checks would catch this category of defect before commit.

**Status:** Worth adding to rad-claude-skills' own validator tooling.

### 5. Cross-plugin contracts canonical home for v4.2 / v5.3 framing

**Discussion:** The validator suggested linking the M0.5 hard gate (v4.2) and floor-of-one-line (v5.3) sections from `docs/cross-plugin-contracts.md` so the shared user-confirmation-surface principle has a canonical home rather than living only in each plugin's manifest description and SKILL.md.

**Status:** Worth doing in a future doc-pass session.

---

## Known failure modes discovered through testing

These were surfaced by Ryan running the plugins against real projects:

### Failure mode 1: Unilateral planning under autonomy hint

**Trigger:** Permission-mode = Auto + bare invocation of /plan on greenfield. Pre-v4.1, /plan ran M1-M5 autonomously and produced 8 ADRs from one paragraph.

**Status:** FIXED in v4.1 (conversational-by-design block + per-phase gates).

### Failure mode 2: Substantive work without scope confirmation

**Trigger:** `/plan --improve` on a project with custom doc structure. Pre-v4.2, the agent correctly parked M6 canonical doc emission but produced 9 sub-sections of consolidation work without asking what scope.

**Status:** FIXED in v4.2 (M0.5 scope-confirmation hard gate).

### Failure mode 3: Total silence on routine /startup

**Trigger:** User invokes /startup on a project with no anomalies. Pre-v5.3 with the model preemptively applying a discussed-but-not-shipped minimal-text design, the agent produced ZERO output. User wondered if anything ran.

**Status:** FIXED in v5.3 (floor of one line, never silent).

### Failure mode 4: Plugin manifest with unescaped JSON

**Trigger:** Plugin loader cache refresh after a description-field edit that introduced unescaped inner quotes. Manifest fails to parse.

**Status:** FIXED in commit `bb461f1` (escaped the inner quotes in rad-session description).

### Failure mode 5 (unfixed): /plan invoked at session open without /startup having run

**Trigger:** User says "continue the plan" at fresh session. Agent does ad-hoc context loading (reads files, runs commands), then invokes /plan directly — skipping the /startup orientation. User has no idea what startup did.

**Status:** DISCUSSED but not patched. Initial proposal was /plan checking for /startup having run first, but user pushed back — they want skills to stay decoupled. The right fix is /plan's M0.5 surfaces enough orientation that /startup not having run becomes a non-issue (and user can always invoke /startup separately if they want). v4.2 partially addresses this; explicit guidance about session-open patterns is not codified.

### Failure mode 6 (architectural, not a bug): Rich projects stretch the canonical doc structure

**Trigger:** Faunero needed `doc-roles-contract.md` (custom) to track agent-scope decisions over time. The canonical structure (vision.md, architecture.md, planning/current.md, decisions/) doesn't have a slot for "agent-scope versioning" or "doc role contracts."

**Status:** Canonical structure is good as a floor; rich projects accrete custom slots. Worth noticing for future doc-structure evolution.

---

## User context & preferences

These are useful for the next Claude to know:

### Permission mode

Ryan has **Auto** permission mode set globally. This generates `<system-reminder>` hints about not asking clarifying questions. The conversational-by-design patches (v4.1, v4.2) explicitly handle this by reinterpreting the signal as "tool approval autonomy" not "skip planning conversation."

### Working style

- Tests plugins against real projects (Faunero, ryandesjardins.com)
- Catches defects via direct use, not synthetic tests
- Sophisticated consumer of LLM outputs — epistemologically careful about distinguishing "patch worked" from "model variance"
- Prefers structural fixes over behavioral nudges ("the model shouldn't be the only safeguard")
- Likes explicit options and depth menus over inferred decisions
- Values terse output but draws the line at total silence (doorman model)

### Doc preferences

- Likes the PROJECT-STORY.md pattern (layperson narrative). May ship as rad-writer skill later.
- Keeps scratch docs untracked at project root, moves them out when done. Knows about C:\Dev\plans\ for design specs but uses untracked root files for one-shot artifacts.
- Doesn't like "strawman" jargon (vibe coder accessibility concern); prefers "DRAFT" or "auto" language.

### Active projects using these plugins

**Faunero** (C:\Dev\Web-Apps\WildPlannerApp\) — wildlife/birding/photography travel planning PWA. Production-soaking. Currently at Bit 17 main slice locked, 17b + 17c queued. Uses a custom bit-by-bit doc structure that predates the canonical one. 19 ADRs. Multi-session planning history.

**ryandesjardins.com** (C:\Dev\Websites\ryandesjardins.com\) — photography portfolio + storefront. Greenfield. Used as the test bed for the v4.1 + v4.2 patches.

### Repo + harness boundary

Per `C:\Dev\rad-claude-skills\CLAUDE.md`:
- This repo is the source of truth for Claude-native skills, plugins, agents
- Do NOT optimize for Codex here — port to `C:\Dev\rad-codex-skills` instead
- Design specs go to `C:\Dev\plans\YYYY-MM-DD-<topic>-design.md` (local only, not tracked)

### What's intentionally NOT in git

These show up as untracked in `git status` and are correct to leave that way:
- `.claude/worktrees/` — worktree workspace
- `2026-05-14-*.md` — local plan scratch files (per CLAUDE.md)
- `AGENTS.md` at repo root — out-of-scope harness file
- `SESSION-HANDOFF.md` (this file) — temporary handoff doc

---

## Recent commits reference

All on `origin/main`. Most recent first:

```
bb461f1 fix(rad-session): escape inner quotes in plugin.json description (corrupt manifest)
40d0dc9 chore: marketplace 1.8.1 — rad-planner 4.2 + rad-session 5.3 user-confirmation-surface pair
801b0b0 feat(rad-session): 5.3 — floor of one line on /startup (never silent open)
c2f9056 feat(rad-planner): 4.2 — M0.5 scope-confirmation hard gate before substantive work
1fd0f87 chore: marketplace 1.8.0 — rad-planner 4.1 + rad-session 5.2 permission-mode-safety pair
77e8081 feat(rad-session): 5.2 — Case C data-loss-protected + /wrapup --auto draft-banner ADRs
9ee6d17 feat(rad-planner): 4.1 — conversational-by-design + --auto opt-in (no ADRs)
8cbbb54 feat(rad-session): v5.0 M6 — release prep (marketplace 1.7.0)
783e909 feat(rad-session): v5.0 M5 — end-to-end fixtures
eda1bc3 feat(rad-session): v5.0 M1–M4 — canonical doc structure + sectioned-writer + agent scope routing
7bf17ff fix(rad-session): v5.1 — fold /init into /startup Phase 0.5 (marketplace 1.7.1)
```

---

## Where to look for more detail

### Canonical specs

- `docs/doc-conventions.md` — canonical doc structure
- `docs/cross-plugin-contracts.md` — single-writer rule + sectioned-writer exception + Case C guard rail
- `docs/status-md-schema.md` — 8-section status.md schema with evidence sources
- `docs/entry-point-routing.md` — /plan's four entry points + four-direction menu

### Plugin sources

- `plugins/rad-planner/skills/plan/SKILL.md` — the planner conversation (M0–M6, now with M0.5)
- `plugins/rad-session/skills/startup/SKILL.md` — orientation + Phase 0.5 bootstrap (v5.1) + floor-of-one-line (v5.3)
- `plugins/rad-session/skills/wrapup/SKILL.md` — 9-phase wrapup including Phase 3 --auto mode (v5.2)
- `plugins/rad-session/fixtures/` — four end-to-end fixtures (codex-only / dual-scope / nonstandard-manual / dev-mode)

### Plugin READMEs (audience: human reading the repo)

- `plugins/rad-planner/README.md`
- `plugins/rad-session/README.md`
- `README.md` (top-level) — marketplace blurb with the v4.2 / v5.3 story

### Marketplace

- `.claude-plugin/marketplace.json` — version 1.8.1, 16 plugins total

---

## What a fresh chat should know if asked to make improvements

1. **The conversational-by-design and floor-of-one-line patches are recent and load-bearing.** Don't roll them back without a strong reason. The v4.1 patch specifically prevents the unilateral-planning failure mode; the v5.3 patch specifically prevents the silent-startup failure mode.

2. **The user has Auto mode on.** Any new skill or refinement should respect the same permission-mode-autonomy distinction: tool approvals can be skipped, but substantive decisions and confirmations cannot.

3. **The user is testing actively.** Defects discovered during real use become patches quickly. Take user reports seriously even when they sound like "feels off" — that's usually a real signal.

4. **The user prefers structural fixes over model-judgment fixes.** "Behavioral consistency comes from the skill, not from the model."

5. **Queue, don't ship in the same session, unless the user explicitly says ship.** Pattern: discuss the design, get user agreement, then ship in a focused commit. Don't preemptively implement during a discussion.

6. **status.md is the canonical handoff.** When uncertain about project state, read status.md first. /wrapup writes it from evidence.

7. **PROJECT-STORY.md pattern is queued for shipment.** If the user mentions it, they probably want to discuss shipping it as a rad-writer skill.

8. **The plugin-validator catches structural issues but not JSON-strict-parse issues.** Worth running `python -c "import json; json.load(open(path))"` on any plugin.json or marketplace.json after editing.

---

## Open threads at end of this session

- v4.2 / v5.3 are freshly shipped. Real-use validation pending — Ryan will test and may surface more refinement needs.
- project-story skill design is fully scoped; awaiting user decision to ship.
- Decisions-in-flight middle layer pattern is noted but not implemented.
- doc-redundancy layer-distinction refinement is noted but not implemented.
- Cross-plugin contracts canonical home for v4.2/v5.3 framing — recommended by validator, not actioned.

---

## Final state

- Working tree: clean (4 untracked files, all intentional)
- Sync: local and origin/main identical
- Three manifests: all parse cleanly
- Three plugins on marketplace: rad-planner 4.2.0, rad-session 5.3.0, marketplace 1.8.1

Ready for the next round of real-use testing. The fresh chat can pick up here and continue with whatever Ryan surfaces next.

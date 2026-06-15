# rad-planner 4.0 + rad-session 5.0 — Coordinated Upgrade Plan (Human Version)

**Date:** 2026-05-14
**Status:** Draft for review and iteration
**Audience:** Ryan, future Claude sessions
**Machine-readable companion:** `2026-05-14-rad-planner-rad-session-upgrade-plan-machine.md`

---

## Where we are now

rad-planner is at v3.0 in the local marketplace (Apr–May 2026 release). It emits five strategic docs at Phase 6 of a six-phase conversation: PRD, ARCHITECTURE, ASSUMPTIONS, DECISIONS, PLAN, plus tasks.md and a transient CLAUDE-FRAGMENT.md handoff.

rad-session is at v4.0. It owns CLAUDE.md, HANDOFF.md, and .claude/session-log.md across three skills: /init, /startup, /wrapup.

The first real-world test (Faunero project, May 13 2026) surfaced layered problems: heavy cross-doc redundancy, DECISIONS format drift, and a deeper structural issue — the plugin generates rather than plans. The follow-up conversation re-grounded the design around two principles: rad-planner is a planner first (docs are a downstream artifact of the plan); rad-session is a maintainer that rolls with what it finds (doesn't enforce structure).

Independent research surfaced three more things worth taking seriously: (1) the published OpenAI/Anthropic guidance converges on a three-band project memory model (operating manual / project memory / execution state); (2) the planner ecosystem is more crowded than expected (spec-kit at 99k stars, Superpowers on Anthropic's official marketplace, GSD with two parallel products, others); (3) rad-planner's genuinely uncommon ground is mechanical validators, reboot semantics with archival/supersession, and plan-session lifecycle pairing.

This plan is the coordinated major-version rebuild that addresses all of it.

Migration tooling for v3.0→v4.0 and v4.0→v5.0 has been dropped from scope: neither prior version was committed beyond the author's local machine, and there is no traffic on the public marketplace listing for either. If migration becomes necessary later, it can be addressed as a standalone skill.

---

## Where we're going

**rad-planner becomes a real planner.** Not a doc generator with a plan inside. The conversation is plan-shaped (five phases: Constitution & Frame, Goal-Backward Scope, Sequence with Size Discipline, Quality Gates, Doc-Set Recommendation). The doc set is recommended *based on the plan*, with project-specific rationale. Doc creation is the first milestone executed against the approved plan, not a side effect of running the command.

**rad-session becomes a real maintainer.** Operational scope only. Reads what's there, writes status.md from evidence, surfaces candidate decisions for ADR recording but doesn't write strategic docs unilaterally. Rolls with non-standard layouts. Bounded work — quick startup, deliberate wrapup, no ceremony.

**Both adopt the published doc structure** (research-canonical): AGENTS.md / CLAUDE.md as conditional operating manuals; docs/{vision,architecture,roadmap,status}.md plus docs/planning/{current.md, archive/} and docs/decisions/NNNN-*.md.

**Always-teaches in /plan; mode-gated teaching in /wrapup.** Vibe coders and learners get explanations and copy-paste-ready content; experienced devs get quick skip-friendly prompts. Mode preference is project-scoped, stored in .rad/profile, default mentor.

---

## A note on Gemini and other models

Real users (Ryan included) work across multiple agents. Claude and Codex are the primary code-writing agents; Gemini gets used for design, graphics, and third-pass review; open-source models fit specific niches.

v4.0/v5.0 supports two agent scopes first-class: **Claude-only, Codex-only, or both**. AGENTS.md is the canonical operating manual when both are in play; CLAUDE.md is the `@AGENTS.md` shim with Claude-specific compaction notes.

Gemini CLI, OpenCode, Cursor, Windsurf, and other agents that read the AGENTS.md format **get the operating manual for free** when AGENTS.md exists. That's the cross-agent portability the Skills standard opened up in Dec 2025. We don't write a GEMINI.md or OPENCODE.md shim by default — vendor-specific shims beyond CLAUDE.md are out of scope for v1 to keep the surface manageable.

If demand surfaces, GEMINI.md (and others) land on the v4.1/v5.1 roadmap. The README calls out this multi-agent reality explicitly so the limitation is honest, not hidden.

---

## How we get there

The work splits into four phases. Each phase has its own milestones, conversation points (decisions to lock with the user), action points (concrete work to execute), and exit criteria.

### Phase 0 — Lock the design (pre-work)

**Why this phase exists:** Without locked specs, both rebuilds will fragment. The conversation points here drive every implementation decision downstream.

**Conversation points to resolve:**
- Adopt the research report's doc structure as canonical (yes/refine)
- File ownership matrix (which plugin writes which file; the human-owned files)
- Mode preference location: `.rad/profile` vs operating-manual frontmatter
- Entry-point detection heuristics (what signals say greenfield vs improvement vs pivot vs plan-boost vs drift-check)
- status.md schema field-by-field with evidence sources documented

**Action points (after conversation):**
- Write `docs/doc-conventions.md` (replaces existing file-conventions.md)
- Write `docs/cross-plugin-contracts.md`
- Write `docs/entry-point-routing.md`
- Write `docs/status-md-schema.md`

**Exit criteria:**
- All four spec docs locked through user review
- No open spec questions blocking implementation
- 2–3 days of conversation, timeboxed to 5 days

---

### Phase 1 — Build rad-planner 4.0

**Why this phase exists:** The planner is the foundation. Until it produces a coherent plan-first conversation with project-specific doc recommendations, rad-session has nothing useful to maintain.

#### M0 — Pre-flight discovery

**Conversation points (with the user, every run):**
- Where does the project live? Three answers: "here" / "this path" / "doesn't exist yet, create at this path"
- Which agents will use this project? Claude / Codex / both / not sure yet
- Which entry point applies? (Heuristic detection; user confirms)

**Action points:**
- Implement discovery prompt sequence
- Implement existing-state detection (CLAUDE.md, AGENTS.md, docs/, .claude/, .agents/, including /init residue)
- Implement entry-point routing logic
- Implement project-directory validation (never write to cwd without confirmation)

**Exit criteria:**
- Discovery output deterministic across test fixtures
- No writes occur before discovery completes
- Existing /init residue detected correctly (Claude /init creates a small CLAUDE.md; Codex /init creates AGENTS.md)

#### M1–M5 — Five-phase conversation

**Phase 1: Constitution & Frame.** Discover the goal, why now, what principles bind the work, what success looks like. Output is operating-manual content (commands, hard boundaries, engineering rules, definition of done, escalation triggers). Writes to CLAUDE.md or AGENTS.md based on agent scope, enriching existing /init residue rather than replacing.

**Phase 2: Goal-Backward Scope.** Borrowing GSD's scaffold: what must be TRUE, what must EXIST, what's CRITICAL, what's deferred, what's the hardest unknown, what could derail this. Risk surfaces here. Outputs draft vision.md non-goals, planning/current.md objective, open questions, risks.

**Phase 3: Sequence with Size Discipline.** How CRITICAL items sequence, what parallelizes, do milestones fit 2–3 tasks / ~50% context budget. Outputs planning/current.md milestone, planned changes, acceptance criteria. Optional roadmap.md if >1 milestone in view.

**Phase 4: Quality Gates.** What "done" means per milestone, how we verify, when we stop. Outputs planning/current.md validation commands, stop conditions, notes for next session.

**Phase 5: Doc-Set Recommendation.** Based on this plan, here's the doc set with project-specific rationale and complexity routing (lite / standard / full). User approves; doc creation lands as M0 of the executed plan.

**Conversation points throughout:**
- Each phase teaches unconditionally (always-teaches mode)
- Each phase's outputs reviewed before next phase begins
- User can revise prior-phase outputs at any time without restarting

**Action points:**
- Draft phase-by-phase agent prompts (the substantive design work)
- Implement phase routing
- Implement phase output validation
- Implement always-teaches explanations
- Implement complexity routing in Phase 5

**Exit criteria:**
- All five phases produce valid drafts
- User has approved the final plan before M6 fires

#### M6 — Doc creation (executes the plan's M0)

**Action points:**
- Write operating manual (CLAUDE.md and/or AGENTS.md per agent scope)
- Write strategic docs (vision.md, architecture.md, planning/current.md, status.md scaffold, decisions/README.md)
- Optional writes (roadmap.md, settings.json, hook scaffolding)
- Write .rad/profile with mode preference
- All writes inside the M0-determined project directory

**Exit criteria:**
- All approved files exist in project directory
- No existing user content overwritten
- Validators pass on emitted docs

#### M7 — Validators

**Action points:**
- Reshape plan-lint.py for new doc set
- Add status-validator.py (freshness checks against git mtime)
- Add doc-redundancy.py (cross-doc duplicate detection)
- Add doc-contradiction.py (cross-doc disagreement detection)

**Exit criteria:**
- All validators have unit tests
- Validators run cleanly on fixture outputs

#### M8 — End-to-end validation

**Action points:**
- Fixture project per entry point (5 fixtures)
- Claude-only fixture, Codex-only fixture, dual-agent fixture
- Mentor-mode fixture, dev-mode fixture
- Token-budget observation per phase

**Exit criteria:**
- All fixtures pass
- Token budgets within target (no phase routinely burns >5k tokens before user value)

#### M9 — Release

**Action points:**
- Update SKILL.md for /plan
- Update plugin.json (3.0.0 → 4.0.0, human-readable description)
- Update marketplace catalog blurb
- Update README "May 2026" callout

**Exit criteria:**
- Plugin-validator agent passes clean
- Marketplace JSON valid

**Phase 1 duration estimate:** 2–3 weeks focused work.

---

### Phase 2 — Build rad-session 5.0

**Why sequenced after Phase 1:** Session reads what planner writes. Spec work for both happens together in Phase 0, but implementation is sequential.

#### M1 — /init rebuild

**Conversation points:**
- Project directory and agent scope (same as planner pre-flight)
- Existing /init residue detection
- Confirm: strategic doc creation deferred to /rad-planner:plan

**Action points:**
- Implement detection and enrichment logic
- Implement conditional operating-manual creation (Claude / Codex / both)
- Implement status.md scaffolding
- Implement settings.json defaults (if Claude in scope)
- Implement gap-recommendation messaging ("no project plan detected — recommend /rad-planner:plan")

**Exit criteria:**
- Existing /init content preserved
- Operating manual created appropriately for agent scope
- No strategic doc creation

#### M2 — /startup rebuild

**Action points:**
- Implement priority read sequence (operating manual → status.md → planning/current.md → cross-references)
- Implement freshness verification (status.md mtime vs git activity)
- Implement resume-context surfacing
- Measure execution time (target < 5 seconds wall clock)

**Exit criteria:**
- Startup completes in target time
- Resume context coherent across fixtures

#### M3 — /wrapup rebuild

**Action points:**
- Implement evidence-based reality assessment (git diff, test output, plan task completions)
- Implement status.md write from evidence (not chat narrative)
- Implement candidate-decision detection (mechanical triggers + soft model reasoning)
- Implement mode-aware surfacing (mentor: teaching + drafts; dev: quick list)
- Implement cross-doc redundancy check (via doc-redundancy.py)
- Implement cross-doc contradiction check (via doc-contradiction.py)
- Implement milestone-archive logic (current.md → planning/archive/)
- Bound work to avoid 10-minute spirals

**Exit criteria:**
- Wrapup writes status from evidence not chat
- Candidate decisions surface with mode-appropriate format
- Cross-doc checks complete in bounded time

#### M4 — Operating manual flavor adaptation

**Action points:**
- Implement detection heuristic for non-standard manual names
- Implement adaptive reading regardless of filename
- Don't impose canonical naming on existing projects

**Exit criteria:**
- Non-standard project layouts work
- No imposing of canonical naming

#### M5 — End-to-end validation

**Action points:**
- Full lifecycle fixture (init → plan → startup → wrapup × 2)
- Non-standard layout fixture
- Mentor and dev mode fixtures
- Single and dual agent fixtures

**Exit criteria:**
- All fixtures pass

#### M6 — Release

**Action points:**
- Update SKILL.md for /init, /startup, /wrapup, /checkpoint
- Update plugin.json (4.0.0 → 5.0.0)
- Update marketplace catalog blurb

**Exit criteria:**
- Plugin-validator passes clean

**Phase 2 duration estimate:** 1.5–2 weeks focused work.

---

### Phase 3 — Release and distribution

**Why this phase exists:** Without distribution, the redesign polishes something only we use. Marketplace plugins get scrutiny and discoverability that local-only doesn't.

**Action points:**
- Coordinated marketplace bump (1.5.0 → 1.6.0)
- Submit both plugins to Anthropic marketplace
- README updates explaining multi-agent reality and upgrade path
- Light adoption tracking setup (post-install issues, common questions, entry-point frequency)

**Exit criteria:**
- Marketplace submission accepted
- README accurate
- Upgrade path documented

**Phase 3 duration estimate:** 1 week, dependent on Anthropic's review timing.

---

## What we're not building (and why)

- **GEMINI.md / OPENCODE.md / other vendor-specific shims.** Surface area control. AGENTS.md serves these agents via portability. Users who want a Gemini-specific shim can write one by hand. v4.1/v5.1 roadmap if demand surfaces.
- **Migration tooling (v3→v4, v4→v5).** No real-world traffic on either older version — author's local-only use. If migration becomes necessary later, a standalone skill can address it.
- **External-LLM cross-review** (deep-plan pattern). Real value but opt-in, adds cost, doesn't affect foundation.
- **PreToolUse re-read hook** (planning-with-files pattern). Worth doing eventually, doesn't affect doc-set redesign.
- **Skills generation by the planner** (review-diff, release-checklist). Useful but downstream of getting doc structure right.
- **AGENTS.md hierarchy with nested overrides.** Complex; irrelevant to most projects; only relevant for monorepos.
- **GUI / terminal UI for planning.** The conversation is the UI.

---

## Honest risks

**Spec lock takes longer than estimated.** Edge cases keep surfacing. Mitigation: timebox to 5 days max; document remaining assumptions for implementation.

**Existing-detection heuristics produce false positives or negatives.** False positive: enriches a file that wasn't /init residue, surprising user. False negative: misses real /init residue, overwrites it. Mitigation: dry-run mode, fixture testing across detection patterns, conservative default (when in doubt, ask).

**Token cost spirals.** GSD's failure mode (4:1 orchestration overhead). Mitigation: per-phase soft budgets, observation during validation, mechanical validators preferred over model reasoning.

**Distribution gets blocked or delayed.** Polished plugins with no audience. Mitigation: README and metadata quality from day one; marketplace submission early enough that delays don't push release.

**The 5-phase conversation feels long for small projects.** Complexity routing in Phase 5 doesn't help if user already fled by Phase 3. Mitigation: --lite flag short-circuits to 3-phase mode; auto-detect bail-out signals from conversation tone.

---

## What good looks like

A user installs rad-planner 4.0 via the Anthropic marketplace. They run /plan in a new directory. The planner asks where the project lives, what agents will use it, what they're building. Five-phase conversation produces a plan they didn't have at the start of the session. Phase 5 recommends a specific doc set with rationale grounded in their plan. They approve. Docs land in their project directory, including a populated CLAUDE.md that's lean (not 200 lines of generic prose) and a planning/current.md that captures real intent.

They run /rad-session:startup the next day. It reads the operating manual, status.md, and current.md, and tells them where they were and what's next. Five seconds. They get to work.

They run /rad-session:wrapup at the end. It updates status.md from git evidence, flags a new dependency they added as a candidate decision (mentor mode includes a draft ADR), and points out that vision.md and current.md disagree about whether mobile is in scope. They resolve the contradiction or defer it.

When the user pivots their project three weeks later, /plan --pivot has a real conversation about what survives, what changes, what needs to be re-decided. Not a wipe-and-replace.

When the user opens the same project from Codex CLI, AGENTS.md is canonical and Codex reads it natively. No friction.

That's the bar.

---

## How we know we're done

- Both plugins pass their plugin-validator agents clean
- End-to-end fixture testing passes for all four entry points, both agent scopes, both modes
- Token budgets observed in validation are within target
- Marketplace submission accepted
- README accurately describes the multi-agent reality, single-plugin philosophy, and entry points
- This plan document gets updated with status: ✓ shipped (date)

---

## Deferred decisions (need closure before Phase 1 starts)

- **Phase 2 risk split** — whether to split Risk out of Phase 2 Scope as its own phase. Current proposal: Risk surfaces inside Phase 2.
- **Release coordination** — rad-planner 4.0 and rad-session 5.0 ship together as marketplace 1.6.0, or staggered. Current proposal: together.
- **Mode preference location** — `.rad/profile` file vs operating-manual frontmatter field. Current proposal: `.rad/profile` (separable, easier to migrate).

---

*Saved to `C:\Dev\rad-claude-skills\` for working reference. Long-term home is `C:\Dev\plans\` per the CLAUDE.md convention.*

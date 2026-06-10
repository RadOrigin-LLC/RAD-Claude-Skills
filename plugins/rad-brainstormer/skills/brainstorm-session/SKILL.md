---
name: brainstorm-session
description: >
  Let's brainstorm, I need ideas, help me think through, brainstorm with me, what
  should I build, how should I approach this, generate ideas, give me alternatives,
  I'm stuck, I don't know where to start, SCAMPER, six thinking hats, reverse
  brainstorm, how might we, creative unblock — open-ended exploration of
  possibilities on any topic (software, business, content, travel, creative,
  personal). Handles blank slate to refining an existing concept. A specific
  technique can be requested by name as a mode (e.g. "scamper", "six-hats",
  "reverse", "hmw", "unblock") and runs inside the session frame.
argument-hint: "[topic or problem] [technique: scamper|six-hats|reverse|hmw|starburst|unblock]"
---

# Brainstorming Ideas Into Reality

The ultimate brainstorming partner. Help turn problems, ideas, and blank slates into fully formed designs through natural collaborative dialogue, proven ideation methodologies, and structured evaluation.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have completed the brainstorming process and the user has approved the output. This applies regardless of perceived simplicity.
</HARD-GATE>

## Execution: parallel-first

This skill chains many phases with heavy sub-agent dispatch. To keep wall-clock time and context usage sane:

- **Context exploration** (Phase 1 state detection + Phase 1 file exploration + optional Phase 3 domain research) has no inter-step dependencies. Issue parallel Read/Glob/Grep calls, and if domain research is triggered, dispatch `domain-researcher` concurrently with the local file reads — do not serialize.
- **Phase 7 design presentation** reads existing files (codebase structure, related specs). Batch those reads.
- **Phase 11 spec review loop** — each iteration is a single `spec-reviewer` dispatch; iterations are inherently sequential, but any file reads the spec needs should be parallel within the iteration.
- **What to serialize, always:** the anti-anchoring question sequence in Phase 2 (user must respond before you offer ideas), and the divergent → convergent transition (mixing modes defeats the protocol).

Opus 4.7 and Sonnet 4.6 handle parallel batching well; Haiku 4.5 may prefer serial execution for reliability.

## Mode Flags

This skill honors two mode flags when passed in the invocation (`/rad-brainstormer:brainstorm-session --non-interactive`, etc.):

- `--non-interactive` — Skip all user-approval gates. Produce a best-effort output, write it to the default delivery path (no commit), and emit a trailing JSON block listing `awaiting_user_review` items (e.g., unconfirmed scope, unvalidated top pick, unresolved spec-review escalations). For agent/CI callers that deadlock on interactive menus.
- `--resume <run-id>` — Load checkpoint state from `.brainstorm/state/<run-id>.json` and continue from the last saved phase. See "Checkpoint & Resume" below.

If neither flag is present, run interactively as documented.

## Technique Modes

The standalone technique skills were folded into this session (v3.0). When the user
names a technique — in the invocation argument or in conversation ("run a SCAMPER on
this", "let's do six hats") — run that technique as the divergent phase, inside the
normal session frame (anti-anchoring first, convergent phase after). Techniques and
their instructions live in `references/methodology-catalog.md`:

| Mode | Technique |
|---|---|
| `scamper` | SCAMPER — Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse |
| `six-hats` | Six Thinking Hats — Blue/White/Green/Yellow/Black/Red perspectives |
| `reverse` | Reverse brainstorming — "how could we make it worse?", then invert |
| `hmw` | How Might We — reframe problems as opportunity questions |
| `starburst` | Starbursting — generate the questions before the answers |
| `unblock` | Creative unblocking — warm-ups and provocations (`references/creative-unblocking.md`) |

A named technique narrows the divergent phase; it never skips anti-anchoring or
convergence. (Root-cause analysis is different — that's `/rad-brainstormer:five-whys`.)

## Checkpoint & Resume

Long brainstorms (domain research + full divergent/convergent + design + spec review) are compaction-prone. Save state to `.brainstorm/state/<run-id>.json` at these transitions:

1. After Phase 1 (starting state detected, context explored)
2. After Phase 3 (domain research complete, if dispatched)
3. End of Phase 5 (divergent phase complete — all ideas captured)
4. End of Phase 6 (convergent phase complete — finalists selected)
5. After Phase 10 (output document written)
6. After each successful Phase 11 spec-review iteration

Checkpoint schema:
```json
{
  "run_id": "string",
  "skill": "brainstorm-session",
  "phase": "1 | 3 | 5 | 6 | 10 | 11-iter-N",
  "started_at": "ISO-8601",
  "last_saved": "ISO-8601",
  "topic": "string",
  "starting_state": "blank_slate | vague_idea | clear_idea | improving_existing | needs_evaluation",
  "domain_brief": "JSON from domain-researcher or null",
  "ideas_generated": ["string"],
  "finalists": ["string"],
  "recommended": "string or null",
  "output_path": "string or null",
  "spec_review_history": [{"iteration": 1, "status": "issues_found", "issues": []}],
  "awaiting_user_review": ["string"]
}
```

On `--resume <run-id>`, load the file, announce the phase you're resuming from, and continue. Do not re-run completed phases.

## Anti-Pattern: "This Is Too Simple To Need Brainstorming"

Every topic goes through at minimum a light brainstorming process. A simple utility, a quick feature, a business question — all of them. "Simple" topics are where unexamined assumptions cause the most wasted work. The process can be short (a few exchanges for truly simple things), but MUST explore before committing.

## Checklist

Complete these steps in order:

1. **Detect starting state** — Where is the user? (blank slate / vague idea / clear idea / improving existing)
2. **Explore context** — Check project files, docs, recent commits (if software-related)
3. **Anti-anchoring check** — Draw out the user's existing thinking BEFORE offering yours
4. **Domain orientation** — Does this need domain research? If yes, dispatch domain-researcher agent
5. **Divergent ideation** — Select and apply appropriate techniques based on starting state (or the requested technique mode)
6. **Convergent evaluation** — Filter and prioritize using appropriate framework
7. **Propose 2-3 approaches** — With trade-offs and a recommendation
8. **Present design/output** — Scaled to domain (spec for software, strategy doc for business, etc.)
9. **Deliver the output** — One self-contained markdown file; ask where (see "Delivering the output")
10. **Spec review loop** (if software) — Dispatch spec-reviewer agent, fix issues, repeat until approved
11. **User reviews output** — Get explicit approval
12. **Transition** — Route to appropriate next step based on domain

## Process Flow

```
Detect Starting State
       │
       ▼
Explore Context ──► Anti-Anchoring: Draw out user ideas first
       │
       ▼
Domain Research Needed? ──yes──► Dispatch domain-researcher agent
       │ no                              │
       ▼◄───────────────────────────────┘
SELECT METHODOLOGY (based on starting state, or the requested technique mode)
       │
       ▼
┌──────────────────────────────────────┐
│ DIVERGENT PHASE                      │
│ "We're in idea generation mode —     │
│  all ideas welcome, no filtering"    │
│                                      │
│ Apply selected techniques            │
│ Capture ALL ideas (user's + yours)   │
│ NO evaluation during this phase      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ CONVERGENT PHASE                     │
│ "Let's switch to evaluation mode"    │
│                                      │
│ Apply evaluation framework           │
│ Narrow to 2-3 top candidates         │
│ Optionally dispatch idea-challenger  │
└──────────────┬───────────────────────┘
               │
               ▼
Propose 2-3 Approaches (with trade-offs + recommendation)
               │
               ▼
Present Design/Output (section by section, get approval after each)
               │
               ▼
Deliver Output (one file — ask where; no auto-commit)
               │
               ▼
Domain-Specific Routing:
  Software → spec review loop → /rad-planner:plan
  Business → business model canvas → action plan
  Content  → content strategy doc → editorial calendar
  Research → research plan → methodology outline
  General  → action plan with next steps
```

## Phase 1: Starting State Detection

Before asking a single question about the topic, determine WHERE the user is:

| Signal | Starting State | Approach |
|--------|---------------|----------|
| "I want to build something but don't know what" | Blank slate | Creative unblocking → Starbursting → HMW |
| "I have this vague idea about..." | Vague idea | Clarifying questions → SCAMPER → Reverse Brainstorm |
| "I want to build X but need to think through the design" | Clear idea | Six Thinking Hats → Morphological Analysis → Design |
| "I have X but want to make it better" | Improving existing | SCAMPER → 5 Whys → TRIZ (if technical) |
| "I have several ideas and need help choosing" | Needs evaluation | Jump to Convergent Phase |

If unclear, ask: "Where are you in your thinking? Are you starting from scratch, exploring a vague idea, or refining something specific?"

## Phase 2: Anti-Anchoring Protocol

**CRITICAL — Do this BEFORE offering any ideas.**

Research on human–AI ideation consistently shows that when AI suggests ideas first, humans anchor on them — producing fewer, less varied, less original ideas. The brainstormer must counteract this:

1. Ask: "Before I share any ideas, what have you been thinking so far? Even half-formed thoughts are valuable."
2. Ask: "What direction appeals to you intuitively, regardless of whether it seems feasible?"
3. Ask: "Is there anything you've already ruled out? Why?"
4. Capture and acknowledge ALL user ideas before adding yours
5. When offering ideas, frame them as building on the user's: "Building on your idea about X, what if we also..."

## Phase 3: Domain Orientation

Assess whether domain research would improve the brainstorming:

- **Research needed**: The topic involves an industry, market, or technical domain where current context matters
- **Research not needed**: Personal/creative topics, well-understood domains, or user is the domain expert
- **Ask if unsure**: "I want to make sure I'm well-informed about [domain]. Want me to do some quick research before we dive in?"

If research is needed, dispatch the `domain-researcher` agent directly (it is defined in this plugin with `model: opus`, JSON-first output):

```
Agent tool:
  subagent_type: domain-researcher
  description: "Research [domain] for brainstorming"
  prompt: <substitute references/subagent-prompts/domain-research.md with {topic} and {session_context}>
```

Parse the JSON response (markdown fallback accepted — see the agent's output contract). Weave the brief into questions naturally — do not dump a research report on the user. If the brief contains items in its `surprises` field, flag them prominently before continuing.

## Phase 4: Methodology Selection

Reference `references/methodology-catalog.md` for detailed technique instructions.

### For Blank Slate:
1. Run a warm-up exercise (from `references/creative-unblocking.md`)
2. **Starbursting** — Generate questions about the problem space
3. **How Might We** — Reframe the best questions as opportunity statements
4. **Crazy 8s** (adapted) — Rapid-fire idea generation on the best HMW questions
5. → Convergent phase

### For Vague Idea:
1. Clarifying questions to understand the kernel of the idea
2. **SCAMPER** — Systematically explore modifications and variations
3. **Reverse Brainstorming** — "How could we make this fail?" then invert
4. **Analogical Thinking** — "How would [company/domain] approach this?"
5. → Convergent phase

### For Clear Idea Needing Design:
1. **Six Thinking Hats** — Explore from all perspectives
2. **Morphological Analysis** — Break into dimensions, combine options
3. → Convergent phase (lighter, since idea is already focused)

### For Improving Existing:
1. **SCAMPER** — What can be substituted, combined, adapted, modified, eliminated, reversed?
2. **5 Whys** — What's the root cause of what needs improving?
3. **TRIZ** (if technical contradiction exists) — Systematic inventive problem solving
4. → Convergent phase

### For Already Has Ideas:
1. Skip divergent phase (or brief expansion with analogical thinking)
2. → Jump directly to convergent phase

## Phase 5: Divergent Phase Discipline

During ideation:
- **Announce the mode**: "We're in idea generation mode — all ideas are welcome, no filtering yet."
- **Never evaluate during generation**: If the user says "that won't work," redirect: "Good concern — let's capture that for evaluation. What else comes to mind?"
- **Build, don't redirect**: Use "Yes, and..." to build on user ideas
- **Capture everything**: Keep a running list of all ideas generated
- **Know when to stop**: When ideas start repeating or becoming incremental, it's time to converge

## Phase 6: Convergent Phase

Reference `references/evaluation-frameworks.md` for detailed framework instructions.

1. Present the complete idea list: "We've generated [N] ideas. Let's evaluate them."
2. Select appropriate framework based on situation
3. Walk through evaluation with the user
4. Optionally dispatch idea-challenger agent for top candidates
5. Narrow to 2-3 finalist approaches

## Phase 7: Design & Output

### Delivering the output — one file, the user picks where

Brainstorming usually happens *before* a repo exists, and even inside one, scattered
brainstorm files become doc drift. So: every output is **one self-contained markdown
file**, and you **ask where to deliver it** (AskUserQuestion or a plain question) with
three options:

1. **Personal folder** (default for non-project and pre-repo topics) — suggest
   `~/Documents/Brainstorms/YYYY-MM-DD-<topic>.md` (Windows:
   `%USERPROFILE%\Documents\Brainstorms\`); the user can name any path. On Claude
   Desktop / Cowork / claude.ai, also surface the file itself so it can be saved or
   downloaded directly.
2. **Into the current project** (only when the topic IS that project) — a dated doc
   under `docs/`, with a header marking it **transient**: *"Brainstorm output —
   consumed by `/rad-planner:plan`; archive after planning."* The repo's doc-hygiene
   tooling (rad-repo-manager) will later flag it for archiving — that is the designed
   lifecycle, not drift. **Never** write to `docs/design.md` (that file is brand /
   UI/UX design direction, not brainstorm output).
3. **No file** — keep the output in the conversation only.

Never auto-commit. If the file landed in a repo, the user commits via their normal flow.

Adapt the output format to the domain:

### Software Projects
- Present design section by section, get approval after each (in `--non-interactive` mode, skip approvals and mark unconfirmed sections in `awaiting_user_review`)
- Cover: architecture, components, data flow, error handling, testing
- Deliver the spec per the rule above (in-project option 2 is the usual choice — `/rad-planner:plan` reads it from there)
- Run `spec-reviewer` agent (max 5 iterations — see escalation below)
- User reviews spec
- Transition: hand off to `/rad-planner:plan` for implementation planning — its discovery interview pre-fills from the spec, so the user won't be re-asked what the spec already answers. If `rad-planner` is not installed, surface this to the user and suggest installing it.

#### Spec Review Loop (Phase 11)

Dispatch `spec-reviewer` with the substituted `references/subagent-prompts/spec-review.md` template, passing the current `iteration` and `max_iterations` (default 5) and any prior iteration's `blocking_issues`. Parse the JSON response:

- `status: approved` → proceed to user review
- `status: issues_found` and `iteration < max_iterations` → fix blocking issues, increment iteration, re-dispatch
- `escalation_required: true` (or `iteration >= max_iterations` with issues remaining) → stop looping. Surface the `unresolved_issues` JSON to the user with: "Spec review hit iteration cap with unresolved issues. Please decide: (a) accept these as known gaps, (b) rewrite the affected sections yourself, or (c) drop back to design phase." In `--non-interactive` mode, keep the current spec on disk and add the unresolved issues to `awaiting_user_review`.

### Business/Strategy
- Present as a strategic brief
- Cover: value proposition, target audience, competitive positioning, key risks, next steps
- Deliver per the rule above (suggest `YYYY-MM-DD-<topic>-strategy.md`)
- Transition: action plan with concrete next steps

### Product Discovery
- Present as Opportunity Solution Tree or lean canvas
- Cover: target outcome, opportunities, solution candidates, experiments to run
- Deliver per the rule above (suggest `YYYY-MM-DD-<topic>-discovery.md`)
- Transition: experiment plan

### Content/Marketing
- Present as content strategy
- Cover: audience, topics, channels, differentiation, content calendar
- Deliver per the rule above (suggest `YYYY-MM-DD-<topic>-content.md`)
- Transition: editorial plan

### General Problem-Solving
- Present as action plan
- Cover: root cause, solution approach, steps, risks, success criteria
- Deliver per the rule above (suggest `YYYY-MM-DD-<topic>-plan.md`)
- Transition: next steps with owners and timelines

## Key Principles

- **One question at a time** — Don't overwhelm with multiple questions
- **Multiple choice preferred** — Lower cognitive load than open-ended when possible
- **Anti-anchoring always** — User ideas first, yours second
- **Phase discipline** — Never mix divergent and convergent modes
- **YAGNI ruthlessly** — Remove unnecessary complexity from all outputs
- **Explore alternatives** — Always generate multiple options before settling
- **Incremental validation** — Present output in sections, get approval before moving on
- **Be flexible** — Go back and re-explore when something doesn't make sense
- **Adapt to energy** — If user is stuck, switch techniques. If flowing, stay out of the way.
- **Domain-aware** — Research when needed, adapt output to domain

## Working in Existing Codebases (Software)

- Explore current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work, include targeted improvements as part of the design.
- Don't propose unrelated refactoring. Stay focused on the goal.

## Large Project Decomposition

Before asking detailed questions, assess scope. If the request describes multiple independent subsystems:
1. Flag it immediately
2. Help decompose into sub-projects: independent pieces, relationships, build order
3. Brainstorm the first sub-project through the normal flow
4. Each sub-project gets its own brainstorm → spec → plan cycle

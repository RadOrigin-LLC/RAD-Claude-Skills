# rad-brainstormer — The brainstormer that doesn't anchor you.

Most AI brainstorming has the same flaw: the AI dumps fifteen ideas at you immediately, and research on human–AI ideation shows what happens next — you anchor on them, and produce fewer, less varied, less original ideas of your own. rad-brainstormer is built around the opposite move: **it draws out your thinking first, every time**, then builds on it with proven facilitation methods (SCAMPER, Six Thinking Hats, reverse brainstorming, starbursting) under enforced divergent/convergent discipline — idea generation and evaluation are never mixed.

It brainstorms **anything**, not just software: business strategy, content plans, travel, creative projects, life decisions. Three autonomous agents back the session: live domain research woven into the questions, a pre-mortem stress-test of your top candidates, and a completeness review of any spec it produces.

## What You Can Do With This

- Run a guided brainstorm from a blank slate to a decided direction — on any topic
- Ask for a specific technique by name: "run a SCAMPER on this", "let's do six hats"
- Use Five Whys to find the real root cause of a recurring problem
- Evaluate options you already have with structured frameworks (Impact/Effort, pre-mortem, JTBD)
- Do a design sprint to go from a chosen software idea to a reviewed spec, then hand off to `/rad-planner:plan`

## Skills

Consolidated to four — the standalone technique skills (SCAMPER, six hats, reverse, HMW, idea-generation, creative-unblock) are now **modes of `brainstorm-session`**, invoked by naming the technique:

| Skill | Purpose |
|-------|---------|
| `brainstorm-session` | The facilitated session: anti-anchoring first, divergent → convergent phases, domain research when useful. Techniques selectable as modes (`scamper`, `six-hats`, `reverse`, `hmw`, `starburst`, `unblock`). |
| `idea-evaluation` | You already have the ideas — structured evaluation and prioritization (Impact/Effort Matrix, Assumption Mapping, Pre-Mortem, JTBD, Dot Voting). |
| `five-whys` | Root-cause analysis — a different job than ideation, kept separate on purpose. |
| `design-sprint` | Post-decision: turn a chosen software approach into a reviewable spec (architecture, components, data flow, error handling, testing), then hand off to the planner. |

| Agent | Purpose |
|-------|---------|
| `domain-researcher` | Live research on any topic — landscape, approaches, constraints, recent innovations — woven into the session's questions, not dumped as a report |
| `idea-challenger` | Pre-mortem analysis — feasibility, desirability, viability stress-test of top candidates |
| `spec-reviewer` | Reviews design specs for completeness, consistency, and implementation readiness (iterative, capped) |

## Where the output goes — your call, every time

Brainstorming usually happens **before** a repo exists, so outputs are never silently scattered into whatever directory you're sitting in. Every session produces one self-contained markdown file, and the skill asks where to deliver it:

1. **A personal folder** (default for non-project topics) — e.g. `Documents\Brainstorms\2026-06-10-topic.md`; on Claude Desktop / Cowork / claude.ai the file is also surfaced directly for download/save.
2. **Into the current project** (when the topic is that project) — a dated doc under `docs/`, explicitly marked *transient: consumed by `/rad-planner:plan`, archive after planning*. rad-repo-manager will later flag it for archiving — that's the designed lifecycle, not drift. It never writes to `docs/design.md` (that file is your brand / UI/UX design direction).
3. **No file** — sometimes a brainstorm is just thinking.

Never auto-committed.

## When to Use This vs rad-planner

[`rad-planner`](../rad-planner/) explicitly assumes the *what* is decided — its job is the *how* and *order*. rad-brainstormer owns the phase before that:

| Phase | Plugin | Output |
|-------|--------|--------|
| **Ideation** (divergent → decided) | `rad-brainstormer` | A decided direction |
| **Design** (shape it) | `rad-brainstormer:design-sprint` | A reviewable spec |
| **Planning** (order it) | `rad-planner:plan` | `docs/plan.md` — release map, milestones, six-field tasks |
| **Code** | your tools | Working software |

The hand-off is designed: the planner's discovery interview pre-fills from the design-sprint spec, so you aren't re-asked what the spec already answers. Clear idea already? Skip straight to `/rad-planner:plan`. Vague problem? Start here. Existing project in an unclear state? That's `/rad-planner:rescue`, not a brainstorm.

## Quick Start

```bash
claude plugin install rad-brainstormer@rad-claude-skills
```

> **Using Claude.ai instead?** See [`skills/rad-brainstormer/`](../../skills/rad-brainstormer/) for the Claude.ai skill version — a single ZIP of consolidated workflows with domain research via web search and deliverables as artifacts.

Then just say:

```
Let's brainstorm
I need ideas for X
Run a SCAMPER on this concept
Do a Five Whys on why this keeps happening
Help me evaluate these three options
Run a design sprint for this feature
```

## License
Apache-2.0

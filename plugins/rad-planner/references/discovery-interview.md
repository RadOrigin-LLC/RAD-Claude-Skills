# Discovery Interview — the grilling protocol

The planner's job in Discovery is to **understand the project better than the user can
articulate it cold**. Vibe coders can answer questions about their product all day —
what they can't do is volunteer the right information unprompted. So the planner drives
a structured interview: it asks, mirrors back, follows up, and doesn't move on until
every coverage area is *settled* or *explicitly unknown*.

This is rigor, not bureaucracy: capped rounds, no jargon, and nothing asked that the
repo already answers.

## The eight coverage areas

Every area must end in one of two states: **settled** (you can state the answer in one
sentence) or **explicitly unknown** (captured as an assumption or risk — never silently
skipped).

| # | Area | What "settled" looks like |
|---|---|---|
| 1 | **End goal** | One sentence describing the truly-done state, 6–12 months out — what makes the user say "this is what I set out to build." Not the MVP; the destination. |
| 2 | **Users & core workflow** | Who uses it, and the ONE workflow that must work end-to-end. |
| 3 | **MVP** | The smallest version the user would put in front of a real person. Extracted by question ("what's the first thing you want to see working?") — never assumed. |
| 4 | **Success criteria** | Observable signs it's working — not feelings ("it feels fast") but checkable facts ("a link shortens in under a second"). |
| 5 | **Hard constraints** | Money, time, skills, platform/devices, accounts and services already paid for or ruled out. |
| 6 | **Existing assets** | Repo, designs, data, domain names, prior attempts — anything that exists already. |
| 7 | **Deliberate exclusions** | At least two things this project is explicitly NOT building. If the user can't name any, propose candidates from the conversation and ask. |
| 8 | **Danger zones** | Does this touch auth, payments, personal data, or external integrations? These change planning rigor (extra checkpoints, stop conditions, security tasks). |

## Protocol

**Pre-fill from evidence first.** On an existing codebase, the repo answers many areas
before the user is asked anything (read order: `docs/prd.md`, `docs/handoff.md`,
existing `docs/plan.md`, `AGENTS.md`/`CLAUDE.md`, `README.md`, the manifest, directory
structure — in one parallel batch). Never ask a question the repo already answers;
instead *confirm*: "The PRD says X — still true?"

**Round 1 — open the areas (4–6 questions).** Target the least-known areas. Use
AskUserQuestion for choice-shaped questions (platform, audience type, quick-vs-full
below); free text for open ones. Rules for every question:

- Plain language, no jargon. "Where should this run — phone, browser, your own
  computer?" beats "What's your deployment target?"
- One topic per question.
- When the purpose isn't obvious, say why you're asking ("I ask because payments
  change how carefully we have to sequence this").

**The mirror.** After each round, restate the project back in 3–5 plain sentences —
"Here's what I believe you're building, for whom, and what done looks like" — and ask
what's wrong with it. The mirror is the highest-value move in the interview: users
correct a wrong summary far more reliably than they answer an abstract question.

**Rounds 2–3 — follow up only on unsettled areas.** Push on vagueness: if the user
says "people can share stuff," ask "share what, with whom, and what does the other
person see?" **Cap at 3 rounds.** Anything still open after round 3 is recorded as
*explicitly unknown* — it becomes a Key assumption (best guess, marked as guess) or a
Risk, and planning proceeds.

**Propose assumptions — never ask the user to invent them.** From the answers, draft
3–6 candidate assumptions ("No real users yet, so we can change anything freely" /
"You're the only developer" / "Data loss during development is acceptable") and ask
the user to confirm, deny, or edit each. Confirmed ones land in `plan.md`'s **Key
assumptions**.

## Closing the interview

Two gates, in order, before any planning begins:

**1. The speed fork (user's choice, not a heuristic).** Ask via AskUserQuestion:

> **Quick plan** — this is a single feature or small project; skip the stack
> evaluation agent, single risk pass. Faster, still lint-validated.
> **Full plan** — new project or significant build; full stack evaluation and
> iterative adversarial review.

Default recommendation: full for greenfield projects, quick for a feature in an
established codebase. The user decides.

**2. The PRD gap check.** If `docs/prd.md` is missing, a skeleton, or contradicts
what the interview established: offer to draft it — *"You've just told me everything
a PRD needs. Want me to write it up? You'll confirm each section."* On yes, draft each
PRD section (Purpose, Users & primary workflow, In scope, Non-goals, Acceptance
criteria) **from the user's own interview answers** — no invention — and confirm
per section via AskUserQuestion (apply / reword / skip) before writing the file. The
user owns the decision; the planner does the typing. On no, plan anyway and note the
gap in Key assumptions.

## Interview → output mapping

| Interview area | Lands in |
|---|---|
| End goal | `## Objective` (**End goal** line) + `## Release map` (Later) |
| Users & workflow | PRD draft; plan `## Objective` |
| MVP | `## Release map` (Now) — the scope of this plan's milestones |
| Success criteria | PRD Acceptance criteria; plan `## Validation` |
| Constraints | `## Key assumptions` + `## Scope` |
| Existing assets | Phase 3 sequencing (don't rebuild what exists) |
| Deliberate exclusions | `## Scope` non-goals; PRD Non-goals |
| Danger zones | `## Stop conditions`, checkpoints, security tasks |

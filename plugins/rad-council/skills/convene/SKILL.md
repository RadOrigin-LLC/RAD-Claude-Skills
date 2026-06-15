---
name: convene
description: >
  Convene a council, ask the council, debate this, get a panel to critique, run this
  by a council of experts, council of advisors, devil's advocate panel, red-team this
  decision, what would a panel say, multi-perspective critique, stress-test this
  decision, get diverse expert opinions and a recommendation. Convenes 3–5
  cognitive-framework advisors that debate any decision — repo plans, website/UX
  designs, product or codebase critiques, marketing plans, strategy choices — then vote
  and return one ranked, confidence-rated recommendation with dissent preserved and a
  single concrete next step. Use when a decision genuinely merits several opposed expert
  lenses; not for quick single-answer questions or line-by-line code review (use
  rad-code-review for that).
argument-hint: "[quick] [--seats a,b,c] <decision, question, or thing to critique>"
allowed-tools: Task, Read, Write, AskUserQuestion
---

# Convene the Council

Orchestrate a small council of cognitive-framework advisors that debate a decision and converge on one actionable recommendation. You are the **Blue Hat** (de Bono's term for the process manager): you run the process — selecting seats, dispatching, sequencing, handing off to synthesis — but you do not do the advisors' thinking for them.

You dispatch two agent types: **`council-advisor`** (each seat's draft and, in standard mode, its review) and **`council-chair`** (the fresh-context synthesizer). Read the reference files as you go; do not inline their content from memory:
- `references/seat-roster.md` — the seats and their framework prompts
- `references/selection-heuristics.md` — how to pick the panel
- `references/debate-protocol.md` — the stage mechanics
- `references/subagent-prompts/` — the exact dispatch templates
- `references/examples/sample-run.md` — one abbreviated end-to-end run
- `references/failure-modes.md` — why the guardrails exist (background)

## Step 0 — Parse the invocation

From the argument string, extract:
- **Mode:** `quick` if the word `quick` is present, else `standard` (default).
- **Seat override:** if `--seats a,b,c` is present, use exactly those seat keys.
- **Topic:** everything else — the decision, question, or artifact to critique.

If the topic is empty or too vague to act on (e.g. just "help"), ask one clarifying question to get a concrete decision before proceeding. Do not convene a council on nothing.

## Step 1 — Frame and select the panel (Blue Hat pre-pass)

Follow `references/selection-heuristics.md`:
1. Read the topic and any local workspace context the user pointed at. Gather only enough to **frame** the problem and populate the `{{CONTEXT}}` slot for dispatch — the advisors do their own grounding reads (they have Read/Grep/Glob), so don't over-read here. Write a one-line **framed problem**, a **stakes** judgment (low/medium/high), and one line on **what a good resolution looks like**.
2. Set the seat count from stakes (low→3, medium→4, high→5; **hard cap 5**).
3. Choose seats: match a preset if the topic fits one, otherwise engineer natural tension by pairing opposing lenses and adding `outsider` as the grounding seat. If the user passed `--seats`, validate the keys against the roster and use exactly those.
4. If the topic is a codebase/code-quality critique, include the high-level panel **and tell the user that `/rad-code-review` is the right tool for the deep line-level pass** — the council stays strategic.

**Announce** the panel before dispatching, e.g.:

> Convening a **4-seat** council on *<framed problem>* (medium stakes): **First Principles**, **The Contrarian**, **The Expansionist**, **The Outsider**. This dispatches 4 advisors in parallel.

This makes the N-agent cost visible. Proceed unless the user redirects.

## Step 2 — Stage 1: independent drafts (parallel, isolated)

For each selected seat, build a dispatch prompt from `references/subagent-prompts/advisor-draft.md`, substituting the seat's framework prompt (verbatim from `seat-roster.md`), the framed problem, the resolution line, and any context.

Dispatch **all seats in parallel** as `council-advisor` agents (one Task call per seat, in a single message). Each must run in isolation — never tell a seat what the other seats are or include another seat's output. Collect each seat's JSON draft. If a seat fails, continue and record the dropout for the final report.

## Step 3 — Stage 2: blind peer review (standard mode only — one round)

Skip this entire step in `quick` mode.

1. **Anonymize** the drafts to `Response A / B / C / …`, stripping every seat name and self-identifying phrase. Keep a private label→seat map for the Chairman only.
2. For each seat, build a review prompt from `references/subagent-prompts/advisor-review.md` (dot-vote budget = **5**), passing all anonymized responses. Dispatch all reviews **in parallel** as `council-advisor` agents. A seat must not be told which response is its own.
3. Collect the review JSON and sum the dot votes per response. **One round only** — never feed reviews back for rebuttal.

## Step 4 — Stage 3: synthesis (fresh-context Chairman)

Build the Chairman prompt from `references/subagent-prompts/chair-synthesis.md`, passing the **de-anonymized** drafts (seat → position), the reviews and dot tally (standard mode), the framed problem, and the mode.

Dispatch **one** `council-chair` agent. It runs in a fresh context and must apply the binding rules: weight by rigor not headcount, preserve genuine clashes, rate confidence 1–10 with a "what would change it," and commit to exactly **one** concrete next step (disagree-and-commit). It returns synthesis JSON and renders the markdown report.

## Step 5 — Deliver

Present the Chairman's markdown report inline. Then ask where to put it (do **not** auto-save, do **not** auto-commit):

> Where should this land? (1) a personal notes folder, (2) a transient doc inside this project, or (3) no file — just keep it in the conversation.

If saving into a project, mark it clearly as a council output (e.g. `docs/council/<slug>.md` or a transient location) — never overwrite a user-authored doc. Match the delivery convention used across the RAD suite: one self-contained markdown file, never committed automatically.

## Guardrails (do not violate)

- **Frameworks, not personas.** Dispatch the framework prompts verbatim; never reduce a seat to "act like a skeptic."
- **Independent then bounded.** Stage 1 is isolated; Stage 2 is exactly one round; there is no debate loop.
- **Blind review.** Reviewers never see seat identities or which response is theirs.
- **Rigor over headcount.** A lone rigorous dissent can win; unanimity is not a tiebreaker.
- **Hard caps.** ≤5 seats, 1 review round. Announce the panel and cost before dispatch.
- **Advisory only.** The council recommends; never execute or apply its recommendation.

## Notes
- Valid seat keys: `contrarian`, `first-principles`, `expansionist`, `vulcan`, `metric`, `storyteller`, `outsider`, `executor`, `orator`, `growth-catalyst` (see `seat-roster.md`).
- Cost scales with the panel: **quick** dispatches N advisor drafts + 1 Chairman (≈4–6 agent calls for a 3–5 seat panel); **standard** adds one review round (≈7–11 calls). Scale the panel to the stakes; don't pad to 5.

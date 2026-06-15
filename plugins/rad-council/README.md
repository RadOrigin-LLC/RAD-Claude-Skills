# rad-council

A council of **cognitive-framework advisors** that debates any decision you bring it — planning a repo, designing a website, critiquing a product or codebase, building a marketing plan, choosing between options — then votes and returns **one ranked, confidence-rated recommendation** with dissent preserved and a single concrete next step.

It is the *convergent pressure-test* of the RAD suite. rad-brainstormer diverges (generate options); **rad-council converges** (stress-test a decision from incompatible perspectives); rad-planner sequences the chosen work.

- **Skills:** 1 (`convene`)
- **Agents:** 2 (`council-advisor`, `council-chair`)

## Why cognitive frameworks, not personas

Telling an AI *who to be* ("a skeptical CFO") produces roleplay and polite collapse into agreement. Telling it *how it must think* — with hard constraints ("you are REQUIRED to find at least one fatal flaw") — produces genuine, non-redundant tension. This is corroborated by research: in controlled study, **perspective diversity and reasoning strength are the dominant drivers** of multi-agent debate quality, while structural knobs (turn order, confidence visibility) barely move the needle. rad-council invests in diverse, strongly-constrained lenses rather than elaborate debate plumbing.

The design also follows the literature's clearest warning: **more debate rounds is not better.** Extended back-and-forth amplifies sycophantic convergence — agents drift toward shared errors. So the council generates **independently**, reviews **once** (blind), and synthesizes by **rigor, not headcount**.

## How it works

```
CONVENE     Blue Hat orchestrator classifies the problem and selects 3–5 seats
            engineered for natural tension (hard cap 5; count scales with stakes)
DRAFT       Each seat answers independently, in parallel, in isolation
REVIEW      Drafts anonymized (A/B/C); each seat critiques + spends a dot-vote
            budget (standard mode only — one round)
SYNTHESIZE  A fresh-context Chairman weights by rigor, preserves genuine clashes,
            rates confidence 1–10, and commits to exactly one next step
```

## The seat roster

Mix-and-matched per topic by the orchestrator:

| Seat | Thinks by… | Catches |
|---|---|---|
| The Contrarian | hunting fatal flaws and failure modes | premature consensus, optimism |
| First Principles Thinker | rebuilding from irreducible truths | wrong-problem, flawed foundations |
| The Expansionist | ignoring risk to hunt upside | missed opportunity, over-caution |
| The Vulcan | decomposing system limits & tech debt | vision-vs-feasibility gap |
| The Metric | demanding evidence & falsifiability | decisions on unverified assumptions |
| The Storyteller | grounding in human stakes | ignored human/emotional factors |
| The Outsider | reasoning with zero context | curse of knowledge |
| The Executor | asking "what do you do Monday?" | strategy with no path to action |
| The Orator | prioritizing ethics, values, brand | metrics at the expense of values |
| The Growth Catalyst | lateral thinking, problem-reversal | conventional ruts |

## Usage

```
/rad-council:convene <your decision or question>
/rad-council:convene quick <something low-stakes>
/rad-council:convene --seats contrarian,metric,outsider <topic>
```

Natural language also triggers it: "convene a council on…", "ask the council…", "debate this…", "get a panel to critique…".

**Modes**

- **standard** (default) — independent drafts → one blind review round + dot-vote → synthesis.
- **quick** — parallel critics → synthesis (no review round); cheapest, for low-stakes gut-checks.

## What you get

One self-contained **markdown report**: the verdict and confidence up top, then the preserved clashes, blind spots caught, dot-vote tally, and the full transcript below. The skill asks where to deliver it; it is **never auto-committed**.

## Example

```
/rad-council:convene Should we add a freemium tier to our open-source CLI tool?
```

The orchestrator frames it as a medium-stakes strategy choice and convenes a 4-seat, tension-engineered panel:

> Convening a **4-seat** council (medium stakes): **The Expansionist**, **The Contrarian**, **The Metric**, **The Outsider**. This dispatches 4 advisors in parallel.

Each seat drafts in isolation, reviews the others blind (votes: Metric 11, Contrarian 6, Expansionist 3), and a fresh-context Chairman synthesizes:

> ## Verdict — confidence 7/10
> **Don't build a freemium tier yet.** Run a willingness-to-pay test on a *net-new* team feature (SSO + shared config); never gate anything already free.
> **Next step:** ship a one-page "Teams (coming soon)" waitlist and measure signups for 2 weeks.
> **What would change this:** waitlist conversion above your threshold → flip to a build decision.
>
> *Where the council clashed: build-now (Expansionist) vs. validate-first (Metric). Sided with validate-first on rigor — it's the only falsifiable path and sidesteps the community-fork risk the Contrarian flagged.*

Note the Chairman **sided with a minority on rigor** (not the dot tally), **preserved the dissent**, and committed to **exactly one** next step. See the full step-by-step run — framing, every seat's draft, the blind review, and the complete synthesis — in [references/examples/sample-run.md](references/examples/sample-run.md).

## Honest limits

- **Cost.** A council is a multi-agent run. Quick mode dispatches one advisor per seat plus a Chairman (≈4–6 model calls for a 3–5 seat panel); standard mode adds a blind review round (≈7–11 calls). The orchestrator caps seats at 5, scales the panel to the stakes, and announces the seat count before dispatching.
- **Not a code reviewer.** For a deep code pass, the codebase-critique panel stays high-level and recommends `/rad-code-review` rather than duplicating it.
- **Claude-only (v0.1).** All seats run on Claude, differentiated by cognitive framework. An optional cross-vendor seat (via OpenRouter) is on the roadmap, not in this version.
- **Advisory, not autonomous.** The council recommends; it never executes or applies its recommendation.

## Pairs with

- **rad-brainstormer** — diverge (generate options) → rad-council to converge (pressure-test the shortlist).
- **rad-planner** — once the council picks a direction, plan the work.
- **rad-code-review** — the deep code pass the council will point you to.

## License

Apache-2.0

## Changelog

### 0.1.0
- Initial release. One `convene` skill (quick + standard modes), `council-advisor` and `council-chair` agents, the 10-seat cognitive-framework roster with stakes-scaled auto-selection, dot-voting, rigor-weighted synthesis with preserved dissent, and built-in guardrails against conformity drift, sycophancy, false consensus, and runaway cost. Claude-only.

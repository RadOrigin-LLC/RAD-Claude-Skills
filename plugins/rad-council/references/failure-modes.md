# Failure Modes & Guardrails

Multi-agent debate has well-documented ways of going wrong. Each is designed out of rad-council rather than left to chance. This file is the rationale; the mechanics live in `debate-protocol.md` and `selection-heuristics.md`.

| Failure mode | What it looks like | Guardrail in rad-council |
|---|---|---|
| **Conformity drift / groupthink** | Agents anchor on an early or majority answer and align to avoid disagreeing; the panel converges prematurely. | Independent generation in isolated contexts (Stage 1, NGT); **single** bounded review round — no iterative debate loop. |
| **Sycophancy / politeness collapse** | Seats with thin personas drop their stance to be agreeable. | Seats are **cognitive frameworks with mandated moves**, not personas. Each is REQUIRED to perform a specific intellectual act (e.g. surface a fatal flaw) it cannot satisfy by agreeing. |
| **Silent hallucination** | A confident, wrong answer passes unchallenged. | Blind peer review explicitly asks for each response's biggest blind spot and what everyone missed; the Chairman discounts unsupported claims and rates confidence with a "what would change it." |
| **Logical fallacies / bad arguments** | Straw-manning, ad hominem, attacking views nobody holds. | Blind anonymization removes the target's identity, forcing argument-on-merit; the review schema has an explicit `fallacies_flagged` field. |
| **False consensus** | The panel "lives with" a lowest-common-denominator compromise to end the process. | Synthesis weights by **rigor not headcount**, **preserves dissent**, and forbids "it depends" hedging (disagree-and-commit). |
| **Runaway token cost** | Parallel agents and extra rounds inflate cost; loops drain budget. | Hard cap **≤5 seats**; review capped at **one round**; seat count **scales with stakes**; the panel and N-agent cost are **announced before dispatch**. |
| **Coverage-stacking** | Selecting many same-direction critics; the panel piles on and misses whole dimensions. | Selection engineers **natural tension** (opposing pairs) and requires at least one constructive/opportunity or human lens unless a pure red-team is requested. |

## Design stance

- **Diversity over depth.** Controlled study finds perspective diversity and reasoning strength dominate debate quality; structural knobs (turn order, confidence visibility) barely matter. So rad-council spends its complexity budget on *distinct, strongly-constrained lenses* and keeps the plumbing simple.
- **One bounded round, never a loop.** The clearest empirical warning in the literature is that more rounds is not better and often worse. rad-council has no "keep debating until consensus" path in v0.1.

## Deferred (not in v0.1)
- **iMAD-style escalation gating** — only escalate from a single advisor to a full council when an initial self-critique signals likely error (large token savings). Candidate for a future `auto` mode.
- **Adaptive stability detection** (KS-test / Beta-Binomial consensus modeling) — academically real but overkill for a prompt-driven plugin; would only matter for a multi-round `deep` mode.

## Sources
Key references behind these guardrails: Du et al. (multi-agent debate improves reasoning), "Can LLM Agents Really Debate?" (diversity dominates), "Talk Isn't Always Cheap" and "Stay Focused" (failure modes / problem drift), iMAD (efficiency), Karpathy's LLM Council and the claude-council / claude-blattman /council implementations (mechanics), and "Disagree and commit" (Grove/Amazon). The maintainer's full verified source list with links lives in the project design doc.

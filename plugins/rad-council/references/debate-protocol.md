# Debate Protocol — Stages 1–3

The protocol exists to extract genuine disagreement and then converge **without** falling into the consensus trap. It is built on three evidence-backed rules:

1. **Generate independently before anyone sees anyone else** (Nominal Group Technique) — prevents early anchoring and conformity drift.
2. **Review blind** — strip seat identity so arguments are judged on rigor, not on which lens produced them.
3. **One review round, then stop** — extended debate amplifies sycophantic convergence (agents drift toward shared errors). There is no "go another round" loop in standard mode.

---

## Stage 1 — Independent draft (NGT)

- Dispatch every seat **in parallel**, each in its own isolated context.
- Each seat receives: the framed problem, its framework prompt (from `seat-roster.md`), and the draft template (`subagent-prompts/advisor-draft.md`).
- **No seat sees another seat's output.** This is the whole point of the stage.
- Each returns a JSON draft (schema in the draft template).

If a seat fails or returns nothing, proceed with the remaining seats and note the dropout in the final report. Never silently shrink the panel without saying so.

---

## Stage 2 — Blind peer review (standard mode only — exactly one round)

1. **Anonymize.** Collect the Stage 1 drafts and relabel them `Response A`, `Response B`, `Response C`, … Strip every seat name and any self-identifying phrasing. Keep a private map (A → which seat) for the Chairman; the reviewing advisors never see it.
2. **Dispatch review** to each seat in parallel using `subagent-prompts/advisor-review.md`. Each seat sees all the anonymized responses (including, unknowingly, its own) and answers: strongest response and why, biggest blind spot, what everyone missed, any logical fallacies, and a **dot-vote allocation**.
3. **Dot voting.** Each reviewer has a budget of **5 points** to distribute across the responses (e.g. 3 to A, 2 to C, 0 to B). Points express *relative* preference and may be concentrated or spread. A reviewer may not give all 5 to a single response unless it genuinely dominates — encourage at least a 4/1 split when a second response has any merit.
4. **One round only.** Do not feed reviews back for rebuttal. Collect and proceed to synthesis.

**Quick mode skips this entire stage** — drafts go straight to synthesis.

---

## Stage 3 — Synthesis (Chairman, fresh context)

The Chairman is a separate `council-chair` agent run in a **fresh context** — it must not inherit the conversation that produced the drafts and reviews. It receives, as input data:
- the de-anonymized drafts (seat → position),
- the reviews and the dot-vote tally,
- the original framed problem and "what resolved looks like."

It produces the synthesis per `subagent-prompts/chair-synthesis.md`. The binding rules:

- **Weight by rigor, not headcount.** A single advisor with a falsifiable, well-evidenced argument that dismantles the others outweighs four advisors who politely agree. Unanimity is not a tiebreaker and is not inherently trustworthy. The Chairman may — and should — side with a minority when its reasoning is stronger, and must say so.
- **Preserve genuine clashes.** Do not smooth disagreement into mush. Where advisors genuinely conflicted, present both sides and explain *why reasonable lenses disagreed*.
- **Rate confidence 1–10** and state exactly what evidence or condition would change the score.
- **Disagree and commit.** No "it depends," no splitting the difference. Choose the most logically defensible path and commit to **exactly one concrete next step** the user can act on immediately.

---

## Dropouts, ties, and degenerate cases

- **All seats agree (no clash):** report it honestly as high-confidence agreement, but the Chairman must still run a skeptical pass — "is this real convergence, or did the panel miss the same thing?" — and note any shared blind spot.
- **Dot-vote tie:** ties are not decisive anyway (rigor wins). Break presentation order by which option has the more rigorous supporting argument, not by points.
- **A seat went off-topic / produced filler:** the Chairman discounts it and notes the low-signal contribution rather than averaging it in.

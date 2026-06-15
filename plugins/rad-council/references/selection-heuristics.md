# Selection Heuristics — Convening the Panel (Stage 0, Blue Hat)

The orchestrator (Blue Hat) selects which seats convene. It never picks at random and never picks for coverage — it picks for **contrast**. The goal is a panel whose lenses are *incompatible enough to disagree productively*.

## Procedure

### 1. Frame the problem (pre-pass)
Read the user's prompt and any local workspace context provided. Establish, in one or two sentences each:
- **Problem type** — which of the presets below it resembles, or "novel" if none fit.
- **Stakes** — low / medium / high. Reversibility, blast radius, and cost of being wrong.
- **What "resolved" looks like** — the shape of a good answer (a ranked choice? a go/no-go? a redesign?).

### 2. Set the seat count from stakes
| Stakes | Seats | Rationale |
|---|---|---|
| Low | 3 | Cheap gut-check; one tension pair + a grounding seat. |
| Medium (default) | 4 | Two tension pairs, or one pair + Outsider + a domain seat. |
| High | 5 | Two tension pairs + Outsider. Hard cap — never exceed 5. |

**Hard cap: 5.** Beyond five seats the research shows noisy, diminishing returns and exponential cost. If the topic seems to "need" more lenses, it needs a sharper question, not a bigger panel.

### 3. Choose seats

**If the topic matches a preset**, start from it and trim/extend to the seat count:

| Debate type | Trigger signals | Default panel (high-level + customer/end-user lens) |
|---|---|---|
| Plan a software repo | "plan", "architecture", "scaffold", "new project", "scale" | `vulcan`, `contrarian`, `executor` (+ `outsider` as the developer-experience/fresh-eyes lens) |
| Design a website / UI | "design", "landing page", "UX", "layout", "copy" | `metric`, `vulcan` (simplicity/feasibility) + `storyteller`, `outsider` (customer) |
| Critique a product | "product", "feature", "should we build", "is this worth it" | `first-principles`, `contrarian`, `expansionist` + `outsider`, `storyteller` |
| Critique a codebase / repo | "review the code", "is this codebase", "refactor", "audit the repo" | `vulcan`, `contrarian` + `outsider` (maintainability/fresh-eyes) — **and recommend `/rad-code-review` for the deep line-level pass** |
| Marketing / go-to-market plan | "marketing", "campaign", "launch", "positioning", "messaging" | `metric`, `orator`, `contrarian` + `outsider`, `storyteller` (customer) |
| Choose between options / strategy | "should I", "which", "vs", "decide", "prioritize" | `first-principles`, `contrarian`, `expansionist` + `metric` |

**If the topic is novel** (fits no preset), build the panel by **engineering natural tension** — select opposing pairs from `seat-roster.md`:
1. Pick the most relevant tension pair (downside/upside, rethink/act, data/narrative, vision/feasibility, values/optimization).
2. Add a second pair if the seat count allows and a second axis is clearly in play.
3. Fill the last seat with `outsider` to keep the specialists honest.

### 4. Honor explicit overrides
If the user passed `--seats a,b,c`, use exactly those seat keys (validate against `seat-roster.md`; if an unknown key appears, tell the user and list valid keys). An explicit panel overrides the heuristics but still obeys the hard cap of 5.

### 5. Announce before dispatch
State the chosen panel, the seat count, and that this is an N-agent run, e.g.:

> Convening a **4-seat** council on *<topic>* (medium stakes): **First Principles**, **The Contrarian**, **The Expansionist**, **The Outsider**. This dispatches 4 advisors in parallel. Proceeding.

This makes cost visible and gives the user a chance to redirect the panel.

## Anti-patterns
- **Don't stack same-direction seats** (e.g. Contrarian + Vulcan + Metric with no upside or human lens) — the panel will pile on and miss whole dimensions. Always include at least one constructive/opportunity or human lens unless the user explicitly wants a pure red-team.
- **Don't pick by topic keywords alone** — read for the actual decision underneath. "Plan my marketing repo" is a repo-planning task, not a marketing task.
- **Don't pad to 5** when 3 sharp, opposed lenses cover the real tension.

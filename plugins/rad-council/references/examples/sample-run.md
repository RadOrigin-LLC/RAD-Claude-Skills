# Sample Run — one abbreviated end-to-end council (standard mode)

A worked example to calibrate the pipeline. Real runs produce fuller JSON; this is trimmed for illustration. The point is the *shape*: frame → announce → isolated drafts → blind review + dot-vote → rigor-weighted synthesis with one next step.

---

**Invocation**

```
/rad-council:convene Should we add a freemium tier to our open-source CLI tool?
```

## Step 0 — Parse
- Mode: `standard` (no `quick` token).
- Seat override: none.
- Topic: "Should we add a freemium tier to our open-source CLI tool?"

## Step 1 — Frame & select
- **Framed problem:** Decide whether to introduce a paid tier on top of an existing free, open-source CLI — and if so, what stays free.
- **Stakes:** medium → 4 seats.
- **What resolved looks like:** a go/no-go with the boundary (what's free vs paid) and the first concrete step.
- **Panel (strategy/choice preset, tension-engineered):** `expansionist` × `contrarian` (upside vs downside), `metric` (evidence), `outsider` (will a new user even understand the split?).

**Announce:**
> Convening a **4-seat** council on *whether to add a freemium tier to the open-source CLI* (medium stakes): **The Expansionist**, **The Contrarian**, **The Metric**, **The Outsider**. This dispatches 4 advisors in parallel.

## Step 2 — Stage 1 drafts (parallel, isolated) — abbreviated

```json
{ "seat": "The Expansionist", "position": "Yes — a hosted/team tier captures the value power users already get for free.",
  "mandated_finding": "Biggest upside: a team tier with SSO + shared config could 10x revenue per account vs per-seat.",
  "confidence": 7 }
```
```json
{ "seat": "The Contrarian", "position": "A freemium split risks fracturing the community that built the tool.",
  "mandated_finding": "Fatal flaw: gating any feature contributors already shipped reads as a rug-pull and invites a fork.",
  "confidence": 8 }
```
```json
{ "seat": "The Metric", "position": "Undecided — there is no evidence of willingness-to-pay yet.",
  "mandated_finding": "Unproven claim: that paid demand exists. Measure it (waitlist/landing-page test) before building anything.",
  "confidence": 6 }
```
```json
{ "seat": "The Outsider", "position": "A new user won't know what they're missing or why some things are locked.",
  "mandated_finding": "The free/paid boundary is invisible to someone arriving cold; the value of 'paid' isn't legible.",
  "confidence": 7 }
```

## Step 3 — Stage 2 blind review (one round) — abbreviated

Drafts anonymized to A/B/C/D. Each seat critiques and spends **5** dot points. Summed tally (mapped back):

| Option | Dot points | 
|---|---|
| Metric (test demand first) | 11 |
| Contrarian (don't gate existing features) | 6 |
| Expansionist (team tier) | 3 |
| Outsider (boundary legibility) | 0* |

\*Outsider's point was procedural ("none of these address onboarding"), captured as `everyone_missed`, not a competing option.

Representative review note (Contrarian, on the Expansionist response): *"Biggest blind spot — assumes a paid tier without checking whether the audience pays for dev tools at all."*

## Step 4 — Stage 3 synthesis (fresh-context Chairman) — abbreviated JSON

```json
{
  "verdict": "Don't build a freemium tier yet. First run a willingness-to-pay test on a *net-new* team feature (SSO + shared config) — never gate anything already free.",
  "confidence": 7,
  "what_would_change_it": "A landing-page/waitlist test converting >X% of team users would flip this to a build decision.",
  "high_confidence_agreements": ["Gating existing free features is off the table — community-fracture risk."],
  "preserved_clashes": [
    { "topic": "Build now vs. validate first", "side_a": "Expansionist: real upside in a team tier", "side_b": "Metric: no evidence of paid demand yet", "why_reasonable": "Upside is real but unmeasured; building before testing risks the Contrarian's fork scenario." }
  ],
  "blind_spots_caught": ["Outsider: the free/paid boundary must be legible to a cold user, or the tier won't convert regardless."],
  "dot_vote_tally": { "Metric": 11, "Contrarian": 6, "Expansionist": 3 },
  "weighting_rationale": "Sided with the Metric minority-by-rigor: it's the only falsifiable path and it neutralizes the Contrarian's fatal-flaw risk by adding net-new value rather than gating.",
  "one_next_step": "Ship a one-page 'Teams (coming soon)' waitlist describing SSO + shared config; measure signups for 2 weeks.",
  "dissent_register": ["The Expansionist still prefers building now but commits to the test as the faster path to the same upside."]
}
```

**Rendered report (top section only):**

> ## Verdict — confidence 7/10
> **Don't build a freemium tier yet.** Run a willingness-to-pay test on a *net-new* team feature (SSO + shared config); never gate anything already free.
> **Next step:** ship a one-page "Teams (coming soon)" waitlist and measure signups for 2 weeks.
> **What would change this:** waitlist conversion above your threshold → flip to a build decision.
>
> *Where the council clashed: build-now (Expansionist) vs. validate-first (Metric). Sided with validate-first on rigor — it's the only falsifiable path and sidesteps the community-fork risk the Contrarian flagged.*

---

**Notes on what this illustrates**
- The panel was **tension-engineered** (upside vs downside + an evidence lens + a fresh-eyes lens), not a pile of critics.
- The Chairman **sided with a minority** (Metric got the most dots *and* the strongest argument here, but the rule is rigor, not the tally) and **said why**.
- Dissent is **preserved and committed** (disagree-and-commit), and there is **exactly one** next step.

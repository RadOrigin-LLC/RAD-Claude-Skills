# rad-writer

Writing assistance in Claude Code, transitioning to an engineer-writing focus (technical docs, READMEs, CHANGELOGs, commits, PRs, ADRs, runbooks, technical posts). Four skills, two agents, two Python scripts that actually measure what the skills describe.

> **Two distributions, two audiences.**
>
> - **This plugin (`plugins/rad-writer/`)** — engineer-writing focus in Claude Code. The orchestrators currently also handle the broader genre set; that coverage migrates out as the pivot completes.
> - **Claude.ai skill (`skills/rad-writer/`)** — multi-genre writing (email, blog, web copy, reports, presentations, prose, social media). Import the ZIP via **Settings > Customize > Skills** for those use cases.

## Read this first: what this plugin will NOT do

If you came here looking for "make AI text undetectable," you came to the wrong plugin. The honest April-2026 reality:

- **Will not detect AI authorship.** Perfect AI text detection is mathematically impossible (arXiv:2509.11915, Sept 2025). Stanford HAI documented 61.3% false-positive rate against non-native English writers; one detector flagged 97.8% of TOEFL essays as AI. Multiple major universities (Vanderbilt, Cornell, multiple UC campuses, Pittsburgh, Iowa, Waterloo, Johns Hopkins position) have disabled AI detection tools institutionally.
- **Will not guarantee text passes any specific AI detector.** Humanizer tools and detectors are in an unwinnable arms race. Anything we did this week to "evade" detection could be patched next week. Most claims of "undetectable AI writing" are vendor marketing.
- **Will not impersonate your voice.** Voice profiles work well for register and structural defaults; they do not reliably capture idiosyncratic informal voice. EMNLP 2025 Findings tested 40,000+ generations and found informal-genre voice mimicry hits 19-21% accuracy on blogs and 50-66% on Reddit forums — and going from 2 to 10 samples yielded "very little" improvement. The voice-analyst extracts a useful style baseline; the LLM applying it is doing approximation, not impersonation.
- **Will not save you from a false-positive accusation.** The reframing this plugin offers (craft improvement) is what actually defends writing — not stylometric tricks.
- **Will not produce text that's guaranteed to "sound human."** It produces text that follows craft principles which happen to also reduce structural patterns associated with AI output. That's a useful side effect, not a guarantee.

If you want a marketing pitch about "undetectable AI writing," it's elsewhere. If you want a domain-aware writing tool that's honest about what stylistic patterns mean in 2026, keep reading.

## What this plugin DOES do

- **Writes domain-appropriate text from scratch** with context gathering and craft constraints baked into generation. Nine domains, each with its own conventions.
- **Improves existing text** with numbered, accept/reject suggestions. Stale clichés, structural uniformity, vague attribution, weak word choice. Backed by `check-blocklist.py` for deterministic word matches.
- **Reviews writing** with scored categories and prioritized findings. Standard for short documents; dispatches the writing-reviewer agent for thorough multi-pass analysis on longer/high-stakes work.
- **Audits AI patterns honestly** — runs `text-stats.py` for measured metrics (burstiness, em-dash density, hedging, transitions, lexical-tell counts), then layers LLM judgment on what scripts can't measure (specificity gap, vague attribution, voice). Reports patterns, not verdicts.
- **Voice profiles** that capture measurable style baselines (sentence length distribution, vocabulary level, formality) — useful for biasing generation toward the writer's defaults, honest about what they can and can't do.

## How AI patterns are organized in 2026

The plugin's `references/ai-writing-patterns.md` is reorganized by **durability**:

| Tier | What | 2026 reliability |
|---|---|---|
| **Tier 1** | Specificity gap, vague attribution, copula suppression, rule-of-three abuse, synonym rotation, present participle stacking | **Most durable** — emerge from next-token dynamics, hard to suppress |
| **Tier 2** | Em dash density, mechanical transitions, hedging clusters, "tada" intros, anaphora abuse, listicle-in-trench-coat | **Degrading but informative in clusters** — many being trained out (GPT-5.1 suppressed em dashes specifically) |
| **Tier 3** | The famous lexical tells (delve, leverage, foster, tapestry, robust, etc.) | **Largely deprecated** — newer models suppress them; humans absorb them; humanizers strip them in one pass. Still worth replacing as **clichés**, but their AI-tell status is a lagging signal. |

The skills lead with Tier 1 findings; Tier 3 lexical tells are relegated to "soft style noise" with explicit caveats.

## Skills

| Skill | Trigger | What it does |
|---|---|---|
| `/rad-writer:write` | "write me a...", "draft a...", "compose a..." | Context-aware generation across 9 domains. Avoids stale clichés and structural uniformity during generation. Uses voice profile if present. |
| `/rad-writer:improve` | "improve this", "fix this writing", "make this better" | Numbered accept/reject suggestions on existing text. Runs `check-blocklist.py` first; layers craft suggestions on top. |
| `/rad-writer:review` | "review this writing", "feedback on", "critique this" | Scored diagnostic with prioritized findings. Runs both scripts first for measured metrics. Dispatches writing-reviewer agent for `--thorough` reviews. |
| `/rad-writer:ai-audit` | "check for AI patterns", "AI audit", "does this sound like AI" | Pattern-by-pattern report organized by durability tier. **Explicitly not a detector.** Reports patterns with measurable scores; suggests fixes. |

## Agents

| Agent | Purpose |
|---|---|
| `voice-analyst` | Builds a voice profile from 3-5 samples. Captures aggregate stylistic features (register, vocabulary level, sentence rhythm); honest about what the LLM applying it can and can't do per EMNLP 2025 research. |
| `writing-reviewer` | Three-pass adversarial review (structure & flow, sentence & word craft, AI patterns by tier). Dispatched by `review --thorough`; can be invoked directly. Uses script-computed metrics; reserves judgment for what scripts can't see. |

## Scripts (the measurement layer)

What earlier versions claimed but didn't enforce, these scripts now actually compute. Pure stdlib Python 3.8+. No `pip install` required.

### `scripts/text-stats.py`
Burstiness (sentence-length SD), em-dash density per 250 words, hedging density per 100 words, mechanical transition density per paragraph, paragraph length distribution, lexical-tell counts. Each metric ships with the same caveat: 2023-2024-era stylometric features; newer models suppress some; convergent patterns matter more than any single number.

```bash
python3 scripts/text-stats.py file.md
python3 scripts/text-stats.py file.md --json
python3 scripts/text-stats.py file.md --mode burstiness
echo "$TEXT" | python3 scripts/text-stats.py -
```

### `scripts/check-blocklist.py`
Deterministic word-list scan with line/column locations and replacement suggestions. Catches single words (delve, leverage, foster, etc.) and multi-word phrase patterns ("it's important to note", "let's dive in", "in today's [X] landscape"). Severity tiers: always-avoid / context-dependent / watch.

```bash
python3 scripts/check-blocklist.py file.md
python3 scripts/check-blocklist.py file.md --severity always-avoid
python3 scripts/check-blocklist.py --list  # print blocklist itself
```

### What the scripts deliberately do NOT do
- Compute an "AI score" — there is no defensible single number
- Modify the text — they report; you (or a downstream skill) decide
- Check semantic patterns (specificity gap, register drift, vague attribution) — those need LLM judgment
- Validate that newer-model AI output looks like older-model AI output
- Claim authorship — "patterns associated with AI" ≠ "this is AI"

## Writing domains

Every skill adapts to the type of writing. Specify a domain or let the plugin infer it:

| Domain | What the plugin knows |
|---|---|
| Email | Tone calibration across contexts (cold outreach, colleague, executive, customer, bad news), subject line patterns, F-pattern scanning, passive-aggressive anti-patterns |
| Blog | Open-with-tension hooks, voice development, In Media Res openings, bucket brigades (Brian Dean), STEPPS virality framework (Jonah Berger), Full Circle endings |
| Web copy | 4U headline formula (Michael Masterson, AWAI), Eugene Schwartz awareness levels, PAS framework, FAB product descriptions, first-person CTAs, risk reversal microcopy |
| Business report | Pyramid Principle / MECE (Barbara Minto), executive summary formula, Action Titles for data, "What-So What-Now What" framework (Borton, 1970), zombie noun elimination, trade-off framing |
| Research | IMRaD abstract scaffold, literature review synthesis, hedging calibration, discipline-specific conventions (STEM, humanities, social sciences) |
| Presentation | Billboard test, 6x6 rule, SCR framework (McKinsey, derived from Minto's SCQA), Action Titles on data slides |
| Prose | Right-branching sentences (Pinker), Given-Before-New principle (Halliday), Burrito Paragraph (informal pedagogy term), Classic Style (Thomas & Turner), Pull-a-Sentence test |
| Technical | Diataxis framework (Daniele Procida), README adoption patterns, "Time to First Call" for API docs (Postman), one-concept-per-snippet principle, progressive disclosure |
| Social | LinkedIn hook-story-insight, 10-Tweet Architecture, "No Link" Rule, Two-Second Test, Hayakawa's Ladder of Abstraction (1949), 3-2-1 newsletter format |

Frameworks that are real and properly attributed dominate the list. The plugin's older "4-Part Hook Formula" reference has been reframed as the author's own synthesis (not a citable canonical framework). "Burrito Paragraph" and "one-concept-per-snippet" are flagged as informal pedagogy / descriptive principle, not named rules.

## Voice profiles — honest scope

The voice-analyst studies 3-5 writing samples to build a profile of measurable patterns: sentence length distribution, vocabulary preferences, tone markers, structural habits, anti-patterns.

**Works well for:**
- Register and tone matching (formality level, vocabulary level, hedging tendency)
- Structured-genre voice (emails, business reports, news-style — EMNLP 2025: 95-97% authorship-verification accuracy)
- Style guidance for the model

**Works less well for:**
- Idiosyncratic informal voice (blogs, social — EMNLP 2025: 19-21% accuracy)
- Signature moves, in-jokes, recurring metaphors
- Lived-experience specificity, personality quirks

Profiles persist across sessions on CLI/Desktop (`~/.rad-writer/profiles/`) or export as artifacts for claude.ai Project Knowledge.

## Quick Start

```bash
claude plugins add ./RAD-Claude-Skills/plugins/rad-writer
```

Then ask naturally:

```
Write me a follow-up email to the client about the delayed launch
Draft a blog post about why we redesigned our onboarding
Improve this [paste text]
Review this writing
Run an AI pattern audit on this document
```

Or with flags:

```
Write me an email --coach          # explains writing decisions
Review this report --thorough      # dispatches writing-reviewer for deep 3-pass analysis
```

## What changed in 2.0

This is a major release because the framing changed.

### Removed (overclaim / wrong / outdated)
- **Claim that this plugin can help users "evade" AI detection** — perfect detection is mathematically impossible (arXiv:2509.11915); reframed as craft improvement
- **Unsourced frequency multipliers** — "foster 10.8x," "tapestry 7.2x," "landscape 6.1x," "nuanced 4.8x" — direction was right but specific numbers had no source. Replaced with verified findings (Shapira/Scientific American on delve, Goedecke on em dashes, ecology abstracts study).
- **Em dash "every 50-80 words vs. every 500" ratio** — practitioner folklore, no peer-reviewed source. Replaced with citations to the actual studies.
- **"Delve 50% spike" undershot the real number** — actual is ~654% in PubMed (Shapira, Scientific American). Updated.
- **"4-Part Hook Formula"** — could not locate this as a named published framework. Reframed as rad-writer's own synthesis (with credit to Brunson's Hook-Story-Offer and Brian Dean's APP as canonical alternatives).
- **"Zoom-In Ladder"** — replaced with the actual canonical reference, **Hayakawa's Ladder of Abstraction (1949)**.
- **"Burrito Paragraph" and "Single Concept Rule"** — flagged as informal pedagogical terms / descriptive principles, not citable named frameworks.

### Reframed (was misleading, now accurate)
- **AI patterns reorganized by durability** — Tier 1 (structural, durable) → Tier 2 (degrading) → Tier 3 (lexical tells, largely deprecated). Earlier versions led with the Tier 3 word lists; the consensus has moved.
- **Voice profile claims** — README now honest about EMNLP 2025 findings on what few-shot voice mimicry can and can't do. Schema doc updated.
- **`ai-audit` skill** — leads with "this is not an AI detector" and explains why. Reports patterns with their tier explicitly.
- **Framework attributions corrected** — credit Borton (1970) for "What-So What-Now What", Masterson/AWAI for the 4U formula, Hayakawa for the Ladder of Abstraction.
- **All skills point at `references/wikipedia-signs-of-ai-writing.md`** — Wikipedia's Sept 2025 guide is the credible 2026 reference; the plugin's role is to be aligned with that, not invent its own authority.

### Added
- **`scripts/text-stats.py`** — measures burstiness, em-dash density, hedging, transitions, paragraph distribution, lexical tells. Pure stdlib Python. JSON output for skill consumption, text for humans.
- **`scripts/check-blocklist.py`** — deterministic word-list scan with line/column locations and replacement suggestions. Catches single words and multi-word phrases.
- **`references/wikipedia-signs-of-ai-writing.md`** — pointer to and relation note for Wikipedia's canonical guide
- **All four skills now run the scripts first** — saves tokens, gives reproducible numbers, lets the LLM focus on what mechanical metrics can't see

## Philosophy

This plugin is not anti-AI. It's anti-*bad*-AI-writing.

The patterns that make AI text feel mechanical — uniform sentence lengths, hollow hedging, mechanical transitions, vague attribution, missing specificity — are the same patterns that make any text worse. Fix the writing quality, and you've done the actually-useful work. Whether or not it "passes" some detector is not what matters; the writing itself is what matters.

Using AI to draft is legitimate. Producing drafts full of cliché vocabulary, uniform sentence structures, and empty qualifiers is not. This plugin fixes the output quality, which is valuable regardless of who wrote the first draft.

## Platform Support

| Feature | CLI | Desktop | claude.ai |
|---|---|---|---|
| All 4 skills | Yes | Yes | Yes |
| File input/output | Yes | Yes | Upload/paste, artifacts |
| Voice profiles | Persistent (`~/.rad-writer/`) | Persistent (`~/.rad-writer/`) | Project Knowledge artifact |
| Long doc chunking | Yes | Yes | Yes |
| Accept/reject workflow | Yes | Yes | Yes |
| Coach mode | Yes | Yes | Yes |
| Validator scripts | Yes (Python required) | Yes (Python required) | Skill-only fallback |

## Sources

The plugin's claims are now grounded in:

- [Wikipedia: Signs of AI Writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) — primary 2026 reference
- [Uncertainty in Authorship (arXiv:2509.11915)](https://arxiv.org/html/2509.11915v1) — perfect AI detection is mathematically impossible
- [Catch Me If You Can? Not Yet — EMNLP 2025 Findings](https://aclanthology.org/2025.findings-emnlp.532.pdf) — voice mimicry capability ceilings
- [Kobak et al. 2024 — ChatGPT excess vocabulary (arXiv:2406.07016)](https://arxiv.org/html/2406.07016v1) — measured vocabulary shifts
- [Pangram Labs: Why Perplexity and Burstiness Fail](https://www.pangram.com/blog/why-perplexity-and-burstiness-fail-to-detect-ai) — practical rebuttal
- [Stanford HAI: AI-Detectors Biased Against Non-Native English Writers](https://hai.stanford.edu/news/ai-detectors-biased-against-non-native-english-writers/) — false-positive evidence
- [The em dash dilemma — Sean Goedecke](https://www.seangoedecke.com/em-dashes/) — controlled em dash counts across model versions
- [Em dashes in ecology abstracts — Piece of K](https://www.pieceofk.fr/the-rise-of-the-em-dash-in-ecology-abstracts/) — 10K-abstract empirical study
- [Delving into delve — Philip Shapira](https://pshapira.net/2024/03/31/delving-into-delve/) — PubMed delve frequency tracking

When the plugin makes a factual claim, it cites the source. When it makes a stylistic recommendation, it labels it as such. When it doesn't know, it says so.

## Requirements

- Claude Code CLI installed and authenticated
- **Python 3.8+** for the validator scripts. Without Python, the validators reduce to "the LLM eyeballs the metrics" — i.e., earlier-version behavior.

## License

Apache-2.0

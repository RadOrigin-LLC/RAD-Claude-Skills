# rad-website-design

Vision implementer for 2026 web design — translates a user's vision into code that meets modern standards, and proposes concrete fixes for existing sites.

## Positioning

This plugin is the **execution discipline layer** between vision and shipped code. It assumes the user has already brainstormed and planned (use `rad-brainstormer` and `rad-planner` upstream) and is now asking Claude to design or improve a site. Its job is to ensure Claude's output meets 2026 standards instead of defaulting to AI-slop patterns.

**Two surfaces:**

1. **New design** — `web-design-implement` ensures every page Claude generates meets the must-do baseline, applies the chosen aesthetic discipline (Calm UX default + overrides), uses semantic tokens, and avoids generic defaults.
2. **Existing design** — `web-design-improve` identifies issues against the 2026 anti-pattern catalog (with damage cited from real research) and proposes concrete change diffs. Accepts source paths or live URLs.

## What this plugin is — and what it isn't

It contains:
- 9 skills (knowledge layer + action layer)
- 1 autonomous reviewer agent
- 6 slash commands
- 3 pure-stdlib Python validators
- 10 reference docs

**It does NOT:**
- Brainstorm or do requirements discovery — pair with `rad-brainstormer`
- Plan multi-week project implementation — pair with `rad-planner`
- Run Lighthouse or measure real Core Web Vitals (LCP/INP/CLS) — pair with Chrome DevTools / WebPageTest
- Take screenshots or render JS-heavy SPAs — pair with `chrome-devtools-mcp`
- Run axe-core at runtime — pair with `rad-a11y`
- Do visual regression — pair with Playwright / Percy / Chromatic
- Verify computed contrast ratios — pair with axe / Stark / browser DevTools
- Detect AI-slop copywriting tone — needs human read

Findings are tagged **[STATIC]** / **[HEURISTIC]** / **[NEEDS-MANUAL]** by detection confidence. **No Pass/Fail verdict** is issued because static analysis cannot defensibly produce one.

## Components

### 9 Skills

**Knowledge layer** (surface authoritative 2026 guidance):
| Skill | Purpose |
|---|---|
| `web-design-must-do` | Must-do baseline — typography, color, layout, spacing, a11y, perf, content, mobile, viz hierarchy |
| `web-design-should-do` | Should-do recommendations — motion, dark mode, tokens, i18n, AEO, conversion, microcopy, errors, loading, empty/onboarding, social proof |
| `web-design-anti-patterns` | Severity-tiered catalog with damage cited (FTC fines, INP fail rates, conversion drops) |
| `web-design-aesthetic` | Calm UX default + documented Liquid Glass / Maximalism / Refined Minimalism / High-Energy overrides |
| `web-design-agentic-ux` | 2026 AI-native UX: Intent Preview, Autonomy Dial, Action Audit & Undo |
| `web-design-aeo` | llms.txt, answer-first content, AI bot allowlist (honest adoption caveats) |

**Action layer** (apply guidance to code):
| Skill | Purpose |
|---|---|
| `web-design-implement` | Vision → code. Ensures Claude's new design meets 2026 standards. |
| `web-design-improve` | Existing → fixes. Identifies issues + proposes concrete diffs for source paths or live URLs. |
| `web-design-review` | Pure static-analysis report (no fix proposals). Mirrors `rad-a11y/a11y-review` style. |

### 1 Agent

- **`web-design-reviewer`** — autonomous static analysis. Runs pure-stdlib validators in parallel, then LLM judgment phases.

### 6 Slash Commands

- `/rad-website-design:implement [vision]` — generate new design code that meets 2026 standards
- `/rad-website-design:improve [path or URL]` — identify + propose fixes for existing
- `/rad-website-design:review [path]` — pure static-analysis report
- `/rad-website-design:must-do [feature]` — must-do checklist tailored to a feature
- `/rad-website-design:anti-patterns [path]` — anti-pattern scan or catalog
- `/rad-website-design:aesthetic [context]` — aesthetic direction picker

### 3 Validators (`scripts/`)

Pure-stdlib Python, no dependencies:

- `check-viewport-meta.py` — flags `user-scalable=no` and missing viewport meta
- `check-pure-bw.py` — flags `#000` / `#fff` / `#000000` / `#ffffff` (eye-strain anti-pattern)
- `check-tap-targets.py` — flags Tailwind `w-N h-N` < 44px on interactive elements

### 10 References

In `references/`:
- `typography-2026.md`
- `color-contrast-apca.md` — WCAG 2.2 AA + WCAG 3.0 APCA Lc values
- `layout-spacing-2026.md`
- `modern-css-2026.md` — container queries, `@layer`, subgrid, `dvh`, `color-mix()`, `:has()`
- `conversion-microcopy.md`
- `design-tokens-w3c-dtcg.md`
- `agentic-ux-patterns.md`
- `aesthetic-directions.md`
- `anti-patterns-catalog.md` — damage-cited, severity-ranked
- `aeo-llms-txt.md`

## Workflows

### Building something new

```
1. (Upstream)  Brainstorm with rad-brainstormer if you don't know what to build
2. (Upstream)  Plan with rad-planner if it's a multi-week project
3.             /rad-website-design:implement <your vision + brand inputs>
4.             /rad-website-design:review <path>     ← sanity check before ship
5. (Pair)      Run Lighthouse + chrome-devtools-mcp for runtime verification
```

### Improving something existing

```
1. /rad-website-design:improve <path or live URL>
2. Apply quick wins (Tier 1 + Small effort)
3. (Pair) chrome-devtools-mcp for screenshots + runtime perf
4. (Pair) rad-a11y for accessibility deep-dive
5. Re-run /rad-website-design:improve to verify
```

## Triggers

The skills self-trigger on natural language. Examples:

- "Design my SaaS dashboard for HR teams" → `web-design-implement`
- "What's wrong with my landing page?" → `web-design-improve` (or `review` for report-only)
- "Improve my homepage at example.com" → `web-design-improve` (URL mode)
- "Pick an aesthetic for a fintech tool" → `web-design-aesthetic`
- "Set up llms.txt" → `web-design-aeo`
- "What should I follow for 2026 web design?" → `web-design-must-do`

## Install

This plugin is part of the [rad-claude-skills marketplace](https://github.com/radesjardins/RAD-Claude-Skills).

```
/plugin marketplace add radesjardins/RAD-Claude-Skills
/plugin install rad-website-design
```

## Honest scope (full)

This plugin is **execution discipline + static analysis + change proposal**. It cannot:

- Replace design judgment on layout/composition decisions
- Generate fully production-ready code without iteration (it produces well-structured starters)
- Create images, illustrations, or final brand assets
- Guarantee conversion (that requires user testing + iteration)
- Catch real-world INP/LCP/CLS values (need RUM or Lighthouse)
- Verify actual computed contrast (needs DOM inspection or runtime tools)
- Detect AI-slop copywriting tone (needs human read)
- Catch information-scent failures (needs real users)
- Detect dark patterns embedded in copy (needs human judgment)
- Catch browser-specific rendering bugs (needs actual browsers)
- Render JS-heavy SPAs when fetching live URLs (use `chrome-devtools-mcp`)

Use this plugin as the **execution layer** — pair with the right runtime tools (`chrome-devtools-mcp`, Lighthouse, `rad-a11y`) and the right upstream tools (`rad-brainstormer`, `rad-planner`, `rad-explain`) for a complete workflow.

## Source attribution

Damage data (FTC fines, conversion drops, % bounce, INP fail rates) is sourced from web research — citations in `references/anti-patterns-catalog.md`. Notebook source content was synthesized from two NotebookLM notebooks ("Web Design" and "Web Design - Anti-Design") on 2026-04-29.

## License

Apache-2.0

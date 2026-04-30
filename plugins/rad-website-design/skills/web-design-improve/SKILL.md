---
name: web-design-improve
description: >
  Identify design issues on an existing site and propose specific changes. Accepts source code
  paths OR live URLs. Use when the user asks "improve my site", "fix my landing page", "what
  should I change", "modernize my homepage", "my site feels dated", "redesign these issues",
  "propose changes to <url>", "audit and fix my design", "what would you change about
  example.com", or any request to take an existing design and propose concrete improvements.
  Differs from web-design-review (which only reports findings) by also proposing the fixes —
  diffs, replacements, structural changes. Pairs with the chrome-devtools-mcp plugin for visual
  and runtime evaluation; does NOT take screenshots or measure runtime performance on its own.
argument-hint: "[source path or live URL]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, Skill, Agent
---

# Web Design — Improve (Existing → Propose Fixes)

This skill activates when the user has **an existing site** and wants Claude to identify what's wrong and propose concrete changes. It is the active counterpart to `web-design-review`'s passive reporting.

## What this skill is — and what it isn't

This skill performs **issue identification + change proposal** over either:

1. **Source code** — file paths, directories, repos. Same surface as `web-design-review` but adds proposed fixes.
2. **Live URLs** — fetched via `WebFetch`. Analyzes rendered HTML, schema, robots.txt, llms.txt, meta tags.

It is **not:**
- A screenshot tool — does not capture rendered visuals (use `chrome-devtools-mcp`)
- A runtime perf measurement tool — does not measure real LCP/INP/CLS (use Lighthouse)
- A real browser — does not execute JS, does not render SPAs (use `chrome-devtools-mcp` for that)
- A visual regression tool — does not compare designs across time

For runtime + visual evaluation, recommend installing `chrome-devtools-mcp` (Claude Code plugin) alongside this one. They complement: this skill does the analysis layer; chrome-devtools-mcp does the runtime/visual layer.

## Triggers

- "Improve my landing page"
- "Fix the design on /signup"
- "Modernize this site"
- "What should I change about my homepage"
- "Audit and propose changes to example.com"
- "My site feels dated — what's wrong"

If the user says "review" / "what's wrong" without "fix" / "propose" → use `web-design-review` (report-only).

## Workflow

### Phase 1 — Determine input shape

Detect from the user's request:
- **Path-shaped input** (`./src`, `index.html`, repo dir) → source mode
- **URL-shaped input** (`https://...`) → URL mode
- **Both** — accept and run both modes

### Phase 2 — Source mode

Invoke the `web-design-reviewer` agent on the path. It runs:
- Three pure-stdlib Python validators in parallel (viewport-meta, pure-bw, tap-targets)
- Static-analysis phases (layout, typography, motion, stack-specific)
- Heuristic phases (LLM judgment marked clearly)

Capture the agent's `[STATIC]` / `[HEURISTIC]` / `[NEEDS-MANUAL]` findings.

### Phase 3 — URL mode

Use `WebFetch` to retrieve the rendered HTML.

Limitations to surface:
- WebFetch returns server-rendered HTML — JS-heavy SPAs (React/Vue/Svelte client-rendered) will return shell markup, not the user-facing content
- Cannot fetch authenticated pages
- Cannot detect runtime behaviors (focus rings on click, scroll-jacking, animation hijacks)

Analyze the fetched HTML for:
- Viewport meta (`user-scalable=no` / `maximum-scale<5`)
- `<title>` and `<meta name="description">` quality
- Heading hierarchy (`H1` count, skip levels)
- `<img>` width/height/alt presence
- Schema.org JSON-LD presence
- Open Graph / Twitter Cards
- Pure black/white in inline styles
- AI-slop content markers (em-dash density, "not only... but also" phrases)
- Form structure (labels, fieldset, autocomplete)

Also fetch:
- `robots.txt` — check AI bot allowlist (GPTBot, PerplexityBot, etc.)
- `llms.txt` — present? valid format?

### Phase 4 — Propose changes

For each finding, output a **change proposal** with the structure:

```
### Finding: <name>
- **Severity:** Tier 1 (AVOID-AT-ALL-COSTS) / Tier 2 (SHOULD-AVOID)
- **Confidence:** [STATIC] / [HEURISTIC]
- **Where:** <file:line> or <selector on URL>
- **What's wrong:** <quoted snippet or pattern>
- **Damage:** <citation from anti-patterns-catalog>
- **Proposed change:**
  ```diff
  - <old>
  + <new>
  ```
  or
  > Replace `<X>` with `<Y>` because <reason>.
- **Effort:** Small / Medium / Large
```

For source mode, you can offer to apply the change directly via `Edit` (ask first).
For URL mode, output diffs the user can apply manually.

### Phase 5 — Prioritization

Group changes by **impact × effort**:

1. **Quick wins** (Tier 1/2 + Small effort) — do first
2. **Big fixes** (Tier 1 + Medium/Large effort) — schedule
3. **Polish** (Tier 2 + Small effort) — backlog
4. **Investigate** ([NEEDS-MANUAL] follow-ups) — surface for human review

### Phase 6 — Surface NEEDS-MANUAL gaps

What this skill cannot do, but the user should:

- **Real Core Web Vitals** → Lighthouse, WebPageTest, RUM
- **Real contrast on actual surfaces** → axe-core, Stark, browser DevTools
- **Visual regression** → Playwright + Percy/Chromatic
- **Screenshot review** → `chrome-devtools-mcp` plugin
- **JS-heavy SPA content** → render with `chrome-devtools-mcp` first, then re-run improve
- **AI-slop tone evaluation** → human read or `rad-writer:ai-audit`
- **Information scent / nav UX** → real user testing
- **Conversion impact** → A/B testing

## Output structure

```markdown
# Web Design — Improvement Proposals: <target>

> Static analysis + WebFetch (URL mode) only. Does not measure runtime performance, does
> not take screenshots, does not render JS-heavy SPAs. Pair with chrome-devtools-mcp and
> Lighthouse for runtime layer.

## Summary
- Target: <path or URL>
- Mode: source / URL / both
- Findings: X Tier 1, Y Tier 2
- Quick wins: N
- Big fixes: M

## Quick wins (do today)
[changes with diffs]

## Big fixes (schedule)
[changes with diffs]

## Polish (backlog)
[changes with diffs]

## NEEDS-MANUAL follow-ups
- ...
```

## Cross-skill flow

- For pure findings without proposals → `web-design-review`
- For new design from scratch → `web-design-implement`
- For accessibility deep-dive → `rad-a11y` plugin
- For copy / AI-slop tone → `rad-writer:ai-audit`
- For SEO depth beyond AEO basics → `rad-seo-optimizer`
- For runtime / visual layer → `chrome-devtools-mcp` plugin

## Honesty rules

- Never claim "WCAG compliant" or "production-ready" after applying changes — neither is verifiable from static analysis alone.
- Tag every proposal with confidence: did you find it via regex (high), inference (medium), or read (low)?
- If a fix has tradeoffs, surface them. Tell the user when a change involves judgment, not just rule-following.
- Don't propose fixes the user didn't ask for. If you find issues outside the scope of "improvement," list them in NEEDS-MANUAL — don't expand scope unilaterally.

## Source

Mirrors web-design-reviewer agent's static analysis + adds change proposal layer.
NotebookLM "Web Design - Anti-Design" (2026) + 2026 web research.

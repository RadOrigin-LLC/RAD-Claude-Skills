---
name: web-design-review
description: >
  Static-analysis review pass over HTML/CSS/JSX/Astro source for 2026 web design anti-patterns
  and must-do violations. Does NOT run Lighthouse, does NOT measure real Core Web Vitals,
  does NOT run axe-core at runtime, does NOT do visual regression. Use when the user asks for
  a "design review", "check my page", "audit my landing page", "review this component",
  "scan for design issues", "pre-launch design check", "is this ready to ship", or any request
  to scan a web page, component, or codebase for 2026 design failure patterns. Findings are
  tagged by detection confidence; the report does NOT produce a Pass/Fail verdict because
  static analysis cannot defensibly produce one.
argument-hint: "[path/to/component, directory, or 'all' for full codebase scan]"
allowed-tools: Read, Glob, Grep, Bash
---

# Web Design Review — Static Analysis

Perform a structured **static analysis pass** over the specified component, page, or codebase. Execute the phases in order and produce an actionable, severity-ranked report with each finding tagged by confidence level.

## What this skill is — and what it isn't

This skill performs **pattern-based static analysis** over `.tsx`/`.jsx`/`.astro`/`.html`/`.css` source. It is **not** a Lighthouse audit, does **not** run axe-core, does **not** measure Core Web Vitals, does **not** detect AI-slop copy, does **not** test real users.

**What this skill catches well (high confidence — `[STATIC]`):**
- Missing or `user-scalable=no` viewport meta
- `#000` / `#fff` / `#000000` / `#ffffff` in CSS (eye-strain anti-pattern)
- Sub-44px Tailwind tap targets (`w-8 h-8` on buttons)
- `h-screen` / `100vh` without `dvh` fallback
- `<img>` missing `width`/`height`/`aspect-ratio` (CLS risk)
- `outline: none` / `outline-none` without `:focus-visible` replacement
- Missing `prefers-reduced-motion` query when CSS animations exist
- Pixel font-sizes (`font-size: 14px`) — should be `rem` + `clamp()`

**What this skill catches with lower confidence (`[HEURISTIC]`):**
- Possible feature overload (>3 primary CTAs visible)
- Possible navigation maze (>4 layers of `<nav>` nesting on desktop layouts)
- Possible AI-slop aesthetic (Inter + purple gradient + glassmorphism stack)
- Possible long forms (>7 input fields without progressive disclosure)

**What this skill cannot catch (`[NEEDS-MANUAL]`):**
- Real LCP / INP / CLS values — pair with Lighthouse / WebPageTest / RUM
- Computed contrast ratios — pair with axe-core / Stark / DevTools
- Sycophantic AI tone — needs human read
- AI-slop copywriting tics — needs human read
- Information scent failures / nav confusion — needs real users
- Dark patterns embedded in copy — needs human judgment

## How to invoke

This skill is best invoked through the `web-design-reviewer` agent, which runs the validators in parallel and synthesizes findings. Invoke the agent via natural language ("review my page") or via `/rad-website-design:review [path]`.

**This skill reports findings only — it does not propose fixes.** If the user wants concrete change proposals (diffs, replacements), route to `web-design-improve` instead.

Individual validators may also be run directly:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-viewport-meta.py <path>
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-pure-bw.py <path>
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-tap-targets.py <path>
```

## Review Phases

When asked to perform a review, execute these phases in order:

### Phase 0 — Stack Detection

Detect the project stack:
- React / Next.js / Astro / Vite / plain HTML
- Tailwind / vanilla CSS / CSS modules / styled-components
- Framework-specific Phase 5 slices only run when relevant.

### Phase 1 — Mechanical Validators (parallel)

Run all three Python validators. They are pure stdlib (no install needed):
- `check-viewport-meta.py` — `[STATIC]` findings
- `check-pure-bw.py` — `[STATIC]` findings
- `check-tap-targets.py` — `[STATIC]` findings (Tailwind only — flagged as `[HEURISTIC]` for non-Tailwind)

### Phase 2 — Visual Hierarchy + Layout

Grep for:
- `100vh` / `h-screen` without `dvh` (`[STATIC]`)
- Missing `width`/`height` on `<img>` (`[STATIC]`)
- `outline: none` / `outline-none` without `:focus-visible` (`[STATIC]`)
- `<button>` / `role="button"` without an accessible name (`[HEURISTIC]`)
- More than 3 elements with `cta-primary` / `bg-primary` class on a single page (`[HEURISTIC]` — possible competing CTAs)

### Phase 3 — Typography

Grep for:
- `font-size: \d+px` declarations (`[STATIC]` — pixel font sizing)
- More than 2 `@import` font URLs (`[HEURISTIC]` — possible font clutter)
- `font-family` listing more than 1 display + 1 body family (`[HEURISTIC]`)

### Phase 4 — Motion & Animation

Grep for:
- `@keyframes` or `animation:` declarations
- For each, check whether the same file has `@media (prefers-reduced-motion: reduce)`
- Flag missing `[STATIC]`

### Phase 5 — Stack-specific (Tailwind/React)

If Tailwind detected:
- Tap target validator runs (already in Phase 1)
- Grep for `bg-purple-500.*to-blue-500` or `from-purple` + `to-blue` (`[HEURISTIC]` — AI-slop gradient tell)

If React detected:
- Grep for `<button>` without `aria-label` AND text content (`[HEURISTIC]`)
- Grep for `onClick` on `<div>` / `<span>` without `role` + keyboard handler (`[STATIC]`)

### Phase 6 — Anti-pattern Heuristics (LLM judgment)

Read 2–3 representative pages or components and assess:
- **Feature overload** — is one primary CTA per view evident?
- **AI-slop aesthetics** — Inter + purple gradient + generic glassmorphism without purpose?
- **Microcopy** — vague button labels ("Submit", "Click here", "Pioneering Tomorrow")
- **Scroll-jacking** — any custom wheel/scroll JS?

These are `[HEURISTIC]` findings — flag with rationale, never as `[STATIC]`.

### Phase 7 — Anti-pattern NEEDS-MANUAL list

Surface the categories that static analysis cannot defensibly verify, with a one-line guide for each:
- AI-slop copywriting → human read
- Real Core Web Vitals → run Lighthouse
- Real contrast ratios → use axe-core or Stark
- Dark patterns in copy → human read
- Information scent → user testing
- Sycophantic AI tone → human read of agent prompts

## Report Format

```
# Web Design Review — <target>

## Summary
- Files scanned: N
- [STATIC] findings: X
- [HEURISTIC] findings: Y
- [NEEDS-MANUAL] follow-ups: Z

## Tier 1 — AVOID-AT-ALL-COSTS findings
[STATIC] file:line — pattern — fix
...

## Tier 2 — SHOULD-AVOID findings
[HEURISTIC] file:line — pattern — rationale — verify
...

## NEEDS-MANUAL follow-ups
- AI-slop copy check → human read
- Core Web Vitals → Lighthouse
- ...
```

**Never issue a Pass/Fail verdict.** Static analysis cannot defensibly produce one.

## Source

Mirrors the rad-a11y review structure. Validators in `scripts/`. Anti-pattern catalog in `references/anti-patterns-catalog.md`.

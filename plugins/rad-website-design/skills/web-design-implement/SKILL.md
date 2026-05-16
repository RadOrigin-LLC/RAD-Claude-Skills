---
name: web-design-implement
description: >
  Vision implementer for new web design work. Use when the user is creating a new design from
  scratch and asks Claude to "design my landing page", "build a new website", "implement my brand
  on a new site", "code my homepage", "create a SaaS dashboard", "design a portfolio", "build my
  marketing site", "implement this Figma", "make a new product page", or any request to GENERATE
  new design code (not review existing). The user typically supplies inputs (brand colors, fonts,
  audience, type of site, sometimes Figma references); this skill ensures Claude's output meets
  2026 standards — must-do baseline, chosen aesthetic discipline, semantic tokens, accessible
  defaults, performance budgets, and avoidance of AI-slop generic patterns. This skill assumes
  upstream brainstorming and planning are already done — pair with rad-brainstormer or rad-planner
  if not.
allowed-tools: Read, Write, Edit, Glob, Grep, Skill
---

# Web Design — Implement (Vision → Code)

This skill activates when the user is **building new web design code from a vision they already have**. They've done the brainstorming. They have a brand, an audience, a purpose. They're asking Claude to design and code it.

This skill's job is **execution discipline.** It ensures Claude's output meets 2026 standards instead of defaulting to AI-slop patterns (Inter on white, purple-to-blue gradient, generic glassmorphism).

## What this skill is — and what it isn't

This skill **directs Claude's design generation.** It is **not** a brainstorming partner, **not** a requirements-gathering workshop, **not** an information-architecture sprint. The user has already decided what to build; this skill ensures it gets built well.

For upstream work:
- Ideation / "what should I build?" → `rad-brainstormer`
- Architecture planning / multi-week project plans → `rad-planner`
- Brand strategy / writing voice → `rad-explain` (narrative + pitch; not a voice tool)

## When to engage this skill

Engage when the user is asking Claude to **generate new design code or markup**, not to review or critique existing work. Typical triggers:

- "Design my landing page for <product>"
- "Build a SaaS dashboard for <use case>"
- "Implement this Figma" (with file/screenshot reference)
- "Code a homepage for <brand>"
- "Make a new product page that converts"

If the user says "review" / "audit" / "fix" / "improve" → use `web-design-improve` instead.

## Pre-flight: gather the vision

Before writing code, capture (in 1–2 quick questions, not a workshop):

1. **What and for whom** — type of site (landing / dashboard / e-commerce / portfolio / docs) and primary audience.
2. **Brand inputs (if any)** — colors, fonts, logo, tone-of-voice, existing design system references.
3. **Aesthetic direction** — if not specified, default to **Calm UX** (utility) or ask which override fits (Liquid Glass / Maximalism / High-Energy / Refined Minimalism — see `web-design-aesthetic`).
4. **Tech stack** — React/Next/Astro/HTML/Vue, Tailwind/CSS modules/styled-components.
5. **Constraints** — accessibility level required, browser support, performance targets.

If the user volunteers all of this, skip the questions. Do not workshop — they came to build, not plan.

## Implementation discipline (the core of this skill)

Apply these in every design Claude generates:

### 1. Token-first, not hex-first

Generate a token layer **before** any component code:

```css
:root {
  --color-surface-base: oklch(99% 0.005 270);
  --color-surface-elevated: oklch(96% 0.005 270);
  --color-text-primary: oklch(20% 0 0);
  --color-text-secondary: oklch(50% 0 0);
  --color-action-primary: oklch(60% 0.18 var(--brand-hue, 270));
  --space-section: clamp(2rem, 5vw, 5rem);
  --type-display: clamp(2rem, 4vw + 1rem, 4rem);
  --motion-duration: 200ms;
  --motion-easing: cubic-bezier(0.4, 0, 0.2, 1);
}
```

Components reference tokens, never raw hex. See `references/design-tokens-w3c-dtcg.md`.

### 2. Must-do baseline applied automatically

Every page Claude generates must include:

- `<meta name="viewport" content="width=device-width, initial-scale=1">` (no `user-scalable=no`)
- Semantic HTML structure (`<header>`, `<main>`, `<article>`, `<section>`, sequential H1→H3)
- Body font ≥ 16px, line-height 1.5–1.6
- `:focus-visible` ring (≥2px, ≥3:1 contrast)
- Min-height: `100dvh` on hero sections (NOT `100vh`)
- `<img>` with explicit `width`/`height` or `aspect-ratio`
- Tap targets ≥ 44×44px (56–60px primary CTAs), 8px+ spacing
- `prefers-reduced-motion` media query if any animation
- WCAG 2.2 AA contrast (4.5:1 body, 3:1 large)

See `web-design-must-do` for the full baseline.

### 3. Aesthetic commitment, not defaults

If the user hasn't specified a direction, **default to Calm UX**: muted palette, one accent, typography hierarchy via weight/size (not color), generous whitespace, subdued motion (≤200ms).

If they specified or you proposed an override (Liquid Glass / Maximalism / Refined Minimalism / High-Energy), apply its anchors consistently. See `web-design-aesthetic` for the matrix and `references/aesthetic-directions.md` for code shapes.

**Never default to:**
- Inter on white with purple-to-blue gradient — AI-slop tell
- Heavy generic glassmorphism without purpose
- Any combination that reads as a 2024–2025 AI-generated template

### 4. Mobile-first construction

Write CSS / Tailwind classes mobile-first:

```jsx
<div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-6">
```

Single-column at <768px; expand at ≥768px. Use container queries (`@container`) for component-level responsiveness — see `references/modern-css-2026.md`.

### 5. Performance defaults

- Images: WebP/AVIF, < 200KB each, `loading="lazy"` for below-fold, preload only the hero
- Fonts: variable fonts, one file per family, `font-display: swap`
- 3rd-party scripts: `defer` or `async`; never block the main thread
- Inline critical CSS only when justified by LCP measurement

### 6. Conversion-aware structure (when relevant)

If the page has a primary action (signup, checkout, demo request):

- One primary CTA per view — never multiple competing
- Trust signals adjacent to the CTA, not in the footer
- Testimonials with name + role + photo + specific outcome
- Inline form validation; descriptive errors with icons + text

See `references/conversion-microcopy.md`.

### 7. Agentic UX patterns (when AI features exist)

If the design includes AI/agent functionality, integrate the three trust patterns:

- Intent Preview before agent acts
- Autonomy Dial in settings
- Action Audit & Undo log

See `web-design-agentic-ux` and `references/agentic-ux-patterns.md`.

### 8. AEO defaults (if a public site)

For public-facing content sites: set up `llms.txt`, allow AI bots in robots.txt, use answer-first content structure, add JSON-LD schema. See `web-design-aeo` for honest adoption caveats.

## Output structure

When generating new design code, structure the output as:

1. **Brief recap** (3–5 lines) — what's being built, target audience, aesthetic direction, tech stack. Confirms the vision before code.
2. **Token layer** — CSS variables / Tailwind config / token JSON (whichever the stack uses).
3. **HTML/JSX structure** — semantic, accessible, mobile-first.
4. **Component CSS** — references tokens, follows the chosen aesthetic.
5. **Honest scope note** — what this code is and isn't (e.g., "starter scaffold for the hero + nav; you'll need to wire data and add copy").

## Cross-skill flow

1. If the user is **brainstorming what to build** → defer to `rad-brainstormer` first
2. If the user **has the vision and wants code** → this skill
3. After implementation, before shipping → run `web-design-review` for static analysis check
4. If the user later wants to **iterate on existing code** → `web-design-improve`

## Honest scope (what this skill cannot do)

- Cannot replace design judgment on layout/composition decisions
- Cannot generate fully production-ready code without iteration — it produces well-structured starters
- Cannot create images, illustrations, or final brand assets
- Cannot guarantee conversion — that requires user testing and iteration
- Cannot magically transform a poor brief into a great design — garbage in, garbage out

This skill is execution discipline, not a substitute for designer skill or user testing.

## Source

NotebookLM "Web Design" (2026) + 2026 web research. Cross-references all sibling skills in this plugin.

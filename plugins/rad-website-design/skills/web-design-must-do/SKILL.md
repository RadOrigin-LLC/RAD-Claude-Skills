---
name: web-design-must-do
description: >
  2026 web design MUST-DO baseline — typography, color, layout, spacing, accessibility, performance,
  content structure, mobile/responsive, and visual hierarchy. Use when the user asks about
  modern web design, "what should my page have", "design my landing page", "design baseline",
  "web design best practices 2026", "build a website", "what's the minimum I need",
  "redesign", "modernize my site", "make this feel current", or any request for the non-negotiable
  defaults of contemporary web design. These are the rules that survive framework churn —
  concrete numbers, exact values, no aesthetic prescriptions.
allowed-tools: Read, Glob, Grep
---

# 2026 Web Design — MUST-DO Baseline

These are the **non-negotiables**. They are the floor every modern website must meet — independent of aesthetic direction, framework, or industry.

When the user asks for a website, page, or component, apply these by default. Note exceptions explicitly only when the user has stated a specific reason to deviate (and document the reason in code comments).

## Typography

- **Body font ≥ 16px.** Smaller body text triggers iOS auto-zoom on form focus and excludes 40+ vision.
- **Variable fonts.** One file per family, fluid scaling via `font-variation-settings`. Reduces HTTP requests vs. multiple weight files.
- **Contrast (WCAG 2.2 AA, today's legal floor):** 4.5:1 normal text, 3:1 large text (≥18pt or 14pt bold).
- **Contrast (WCAG 3.0 APCA, future-proofing):** Lc ~90 for 14pt body, Lc ~75 for 18pt labels, Lc ~60 for 24pt, Lc ~45 for 36pt headings. APCA is perceptually accurate where the 4.5:1 ratio fails on near-black colors. See `references/color-contrast-apca.md`.

## Color

- **60-30-10 palette.** 60% neutral background, 30% secondary, 10% high-contrast accent reserved for primary CTAs.
- **Semantic color mapping.** `--color-success`, `--color-error`, `--color-info` — never raw hex for status. Reduces cognitive load and eases dark-mode pivots.
- **Dark mode without halation.** Never `#000` or `#FFF`. Use off-blacks (`#121212`, deep charcoal) and off-whites. Pure black + bright text causes "halation" (glowing edges) and eye strain.

## Layout

- **CSS Grid bento, 12-col base.** 16px gaps, 24px container padding for clean compartments.
- **Tile size = priority, not content volume.** Hero KPI in 4–6 col tiles; secondary metrics in 1–2 col tiles.
- **Wide-screen wrapper.** `max-width: 1400px` (or `max-w-7xl`) centered, prevents stretched/unreadable lines on ultra-wide monitors.
- **`min-h-[100dvh]`, NOT `100vh`/`h-screen`.** `100vh` jumps when mobile browser toolbars collapse. Dynamic viewport units (`dvh`) are stable.

## Spacing

- **Fluid spacing via `rem` + `clamp()`.** Static pixel margins break across viewports.
- **Whitespace is architectural.** Treat it as an active element separating clusters and directing the eye to a single primary objective per view.

## Accessibility (WCAG 2.2 AA floor)

- **`:focus-visible` ring.** ≥2 CSS px thickness, ≥3:1 contrast against background. Keyboard-only (`:focus-visible` excludes mouse clicks).
- **`aria-label` on every icon-only button.** Without it, screen readers announce "button" with no purpose.
- **Logical keyboard tab order** — match visual L→R, T→B flow.
- **Never `user-scalable=no`** on the viewport meta. Users with vision impairments must retain pinch-zoom. Validator: `scripts/check-viewport-meta.py`.

For deeper accessibility, install `rad-a11y` alongside this plugin.

## Performance — Core Web Vitals

- **LCP ≤ 2.5s.** Preload hero with `<link rel="preload">`. Serve images as WebP/AVIF. Keep individual images < 200KB.
- **INP ≤ 200ms.** Defer non-critical 3rd-party scripts. Break up long JS tasks (>50ms blocks). 43% of sites currently fail INP — scripts and tracking pixels are the usual cause.
- **CLS ≤ 0.1.** Always set explicit `width`/`height` on `<img>`/`<video>` or use `aspect-ratio`. Reserve space for ads, embeds, and skeletons.

## Navigation

- **Cmd+K command palette** for any SaaS/web app with >10 features. Bypasses nested menus entirely.
- **Mobile bottom tab bar:** 3–5 primary destinations, fixed position, **always pair icons with text labels** (icons alone are ambiguous).

## Content Structure

- **Semantic HTML.** `<header>`, `<main>`, `<article>`, `<section>`, sequential `H1`→`H3`. Required for screen readers, SEO, and AI agent parsing.
- **Answer-first inverted pyramid.** Put the direct answer in the first 40–50 words of every section. AI overviews extract from openings.

## Mobile & Responsive

- **Thumb zone.** Place primary interactive elements (checkout, primary nav) in the bottom 60% of the mobile viewport for one-handed use.
- **Tap targets ≥ 44×44px (Apple) / 48×48dp (Android).** 56–60px for primary CTAs. ≥8px spacing between clickable elements. Validator: `scripts/check-tap-targets.py`.
- **Mobile-first.** Collapse the 12-col bento to a single-column 12-span at <768px; expand at ≥768px. Container queries (`@container`) for component-level adaptation — see `references/modern-css-2026.md`.

## Visual Hierarchy

- **Spatial weight signals importance.** Large tile = priority, NOT content volume.
- **Functional micro-interactions.** 200–500ms organic spring easing, tied to feedback (button ripple from click coords, layout transitions). Decoration-only animation is an anti-pattern — see `web-design-anti-patterns`.
- **Loading rule (1-3-10):** <1s no indicator; 1–3s spinner; 3s+ definite progress bar. Replace spinners with skeleton screens within 100ms.

## Cross-skill references

- For motion, dark mode tuning, design tokens, AEO, conversion, microcopy: load `web-design-should-do`.
- For dark patterns and damage-cited failures: load `web-design-anti-patterns`.
- For aesthetic direction (Calm UX vs Liquid Glass vs Maximalism): load `web-design-aesthetic`.
- For AI-era patterns (Intent Preview, Autonomy Dial): load `web-design-agentic-ux`.
- For applying this baseline to NEW design code: load `web-design-implement`.
- For applying this baseline as fixes to EXISTING code: load `web-design-improve`.

## Source

Synthesized from NotebookLM "Web Design" (2026-04-29) and 2026 web research. Damage data citations are in `references/anti-patterns-catalog.md`.

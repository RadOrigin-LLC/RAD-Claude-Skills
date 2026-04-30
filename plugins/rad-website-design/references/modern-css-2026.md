# Modern CSS — 2026 Reference

The CSS features below shipped in late 2024–2025 and are baseline-supported across Chromium, Safari, and Firefox in 2026. Use them.

## Container queries (`@container`)

Replace media queries for component-driven layouts. Components adapt to their container, not the viewport.

```css
.gallery { container-type: inline-size; }

@container (min-width: 600px) {
  .gallery-item { grid-column: span 2; }
}
```

Use `container-name` for explicit reference:

```css
.dashboard { container: dash / inline-size; }

@container dash (min-width: 1024px) { ... }
```

## Cascade layers (`@layer`)

Define precedence explicitly. Eliminates specificity wars and `!important` arms races.

```css
@layer reset, tokens, base, components, utilities;

@layer base {
  h1 { font-weight: 800; }
}

@layer utilities {
  .text-bold { font-weight: 700; }
}
```

In a thousand-component micro-frontend, this is non-negotiable.

## Subgrid

Nested grids inherit parent track sizes:

```css
.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

.card {
  display: grid;
  grid-template-rows: subgrid;
  grid-row: span 3; /* title, body, footer all align across cards */
}
```

## `:has()` — relational selector

Style a parent based on its descendants. Removes most "I need to add a class to the parent in JS" cases.

```css
/* Form with errors → highlight the wrapper */
form:has(input[aria-invalid="true"]) { border-color: var(--color-error); }

/* Card containing a video → larger padding */
.card:has(video) { padding: 2rem; }
```

## Dynamic viewport units (`dvh`, `lvh`, `svh`)

- `100dvh` — current viewport (changes as toolbars appear/disappear)
- `100lvh` — large (toolbar collapsed)
- `100svh` — small (toolbar visible)

Replace `100vh` everywhere on mobile-affected layouts.

## `color-mix()` and OKLCH

```css
:root {
  --primary: oklch(60% 0.18 270);
  --primary-hover: color-mix(in oklch, var(--primary), white 15%);
  --primary-active: color-mix(in oklch, var(--primary), black 10%);
}
```

OKLCH is perceptually uniform — equal chroma values look equally saturated across hues, unlike HSL.

## Logical properties

Use `margin-inline`, `padding-block`, `inset-inline-end` instead of `margin-left`/`padding-top`/`right`. RTL languages flip automatically.

```css
.callout {
  margin-inline: auto;
  padding-inline: 1rem;
  border-inline-start: 4px solid var(--color-accent);
}
```

## `@scope`

Limit selector reach to a subtree. Removes the need for BEM-like naming or aggressive child-combinators.

```css
@scope (.card) {
  :scope { padding: 1rem; }
  h2 { font-size: 1.5rem; }
}
```

## Anchor positioning (newer)

Native CSS for tooltip/popover positioning relative to an anchor element. Replaces JS positioning libraries (Floating UI, Popper) for many cases.

```css
.tooltip {
  position-anchor: --button;
  inset-area: top;
  margin-block-end: 0.5rem;
}

.button { anchor-name: --button; }
```

Browser support is rolling out — verify before relying on it.

## View Transitions API

Smooth same-document and cross-document transitions:

```css
@view-transition { navigation: auto; }

::view-transition-old(root) { animation: fade-out 200ms; }
::view-transition-new(root) { animation: fade-in 200ms; }
```

Adds polish to MPA navigation that previously required SPAs. Respect `prefers-reduced-motion`.

## What this replaces

- Media queries for component layouts → `@container`
- BEM/CSS Modules namespacing → `@scope`, `@layer`
- JS-driven parent state → `:has()`
- 100vh hacks → `dvh`
- Floating UI / Popper for tooltips → CSS anchor positioning
- HSL token systems → OKLCH

## Anti-patterns

- Over-generic selectors even with `@layer` (still hurts readability)
- Skipping `prefers-reduced-motion` checks for view transitions
- Using `oklch()` without verifying browser fallback (older Safari)

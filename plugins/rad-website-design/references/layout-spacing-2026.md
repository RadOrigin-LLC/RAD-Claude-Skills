# Layout & Spacing — 2026 Reference

## Bento grid (default for dashboards)

12-column CSS Grid, 16px gaps, 24px container padding.

```css
.bento {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1rem;
  padding: 1.5rem;
  max-width: 1400px;
  margin-inline: auto;
}

.tile-hero { grid-column: span 6; }
.tile-half { grid-column: span 6; }
.tile-third { grid-column: span 4; }
.tile-quarter { grid-column: span 3; }
.tile-twelfth { grid-column: span 1; }

@media (max-width: 768px) {
  .bento > * { grid-column: 1 / -1; }
}
```

**Tile size = priority, not content volume.** A small KPI gets a small tile even if the data fits more.

## Container queries (component-level responsive)

Container queries replace media queries for component-driven layouts. Browser support: Chrome 105+, Safari 16+, Firefox 110+ (~92% global).

```css
.card-list {
  container-type: inline-size;
}

.card { padding: 1rem; }

@container (min-width: 480px) {
  .card { padding: 1.5rem; flex-direction: row; }
}

@container (min-width: 768px) {
  .card { padding: 2rem; gap: 2rem; }
}
```

The card adapts to its container, regardless of viewport — perfect for design systems where the same card lives in narrow sidebars and full-width hero slots.

## Subgrid

Subgrid lets nested grids inherit the parent's track sizes. Browser support: stable since 2023.

```css
.outer-grid {
  display: grid;
  grid-template-columns: 200px 1fr 1fr 200px;
  gap: 1rem;
}

.card-row {
  grid-column: 2 / 4;
  display: grid;
  grid-template-columns: subgrid;
}
```

Use for consistent alignment across nested cards (pricing tables, feature comparisons).

## Spacing scale

Use a 4px or 8px base scale. Tailwind defaults to 4px (1 unit = 4px). Stick to the scale — ad-hoc values (`margin-top: 13px`) break rhythm.

| Token | px | Use |
|---|---|---|
| `space-1` | 4 | Tightest internal padding |
| `space-2` | 8 | Default tight spacing |
| `space-3` | 12 | |
| `space-4` | 16 | Default block spacing |
| `space-6` | 24 | Section internal |
| `space-8` | 32 | Section external |
| `space-12` | 48 | Major section breaks |
| `space-16` | 64 | Hero / above-fold breaks |
| `space-24` | 96 | Top-level page breaks |

Fluid alternative with `clamp()`:

```css
:root {
  --space-section: clamp(2rem, 5vw, 5rem);
}
```

## Wide-screen wrapper

Always cap content width on ultra-wide monitors. Otherwise lines stretch unreadably.

```css
.container { max-width: 1400px; margin-inline: auto; padding-inline: 1.5rem; }
```

For text-heavy content, narrower (65–75ch):

```css
.prose { max-width: 70ch; margin-inline: auto; }
```

## Dynamic viewport units

`100vh` jumps when mobile browser toolbars collapse/expand. Use:

- `100dvh` — dynamic viewport height (current)
- `100lvh` — large viewport height (toolbar collapsed)
- `100svh` — small viewport height (toolbar visible)

```css
.hero { min-height: 100dvh; }
```

For Tailwind users: `min-h-[100dvh]` instead of `h-screen`.

## Mobile-first breakpoints (Tailwind defaults)

| Token | Width |
|---|---|
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px |
| `xl` | 1280px |
| `2xl` | 1536px |

Default to mobile (no prefix). Add larger sizes with prefixes: `md:grid-cols-3`.

## Cascade Layers (`@layer`)

End the specificity wars. Define explicit precedence:

```css
@layer reset, tokens, base, components, utilities, overrides;

@layer base {
  body { font-family: system-ui; }
}

@layer components {
  .card { /* ... */ }
}
```

`utilities` always wins over `components`. No more `!important`.

## Anti-patterns

- `100vh` / `h-screen` without dvh fallback → MUST-DO violation
- Stretched content > 1400px on ultra-wide → MUST-DO violation
- Forced bento on content that doesn't suit it → SHOULD-AVOID #3

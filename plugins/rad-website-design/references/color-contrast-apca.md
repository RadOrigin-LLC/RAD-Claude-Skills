# Color Contrast — WCAG 2.2 AA + APCA (WCAG 3.0 ready)

## Two standards in 2026

- **WCAG 2.2 AA** — current legal floor (ADA, EAA). Ratio-based.
- **WCAG 3.0 APCA** — perceptually accurate. Working Draft. Future-proof.

These are **not backwards-compatible.** A combination passing 2.2 may fail APCA, and vice versa. Test for both. As of 2026, ship to 2.2 AA for compliance and additionally meet APCA targets for forward readiness.

## WCAG 2.2 AA — the floor

| Text | Min ratio |
|---|---|
| Normal body text | 4.5:1 |
| Large text (≥18pt or 14pt bold) | 3:1 |
| UI components and graphics | 3:1 |
| Focus indicators | 3:1 |

Test with axe-core, Stark, or browser DevTools.

## APCA — perceptual contrast

APCA outputs an **Lc value** (Lightness contrast) from roughly Lc 0 to ±Lc 106. It accounts for font weight, font size, and how human vision actually perceives contrast — particularly near-black colors where the 4.5:1 ratio fails.

### APCA targets (2026 draft)

| Use | Lc target |
|---|---|
| Body text (14pt) — intensive reading | Lc ~90 |
| Standard labels (18pt) | Lc ~75 |
| Sub-headings (24pt) | Lc ~60 |
| Display headings (36pt+) | Lc ~45 |
| UI accents, decorative | Lc ~30 (acceptable for non-essential text) |

### Why APCA matters

- **Near-black colors:** 4.5:1 ratio passes for `#222 on white` but APCA shows it's not as readable as the ratio implies.
- **Font weight:** thin fonts at light colors fail APCA more aggressively than 2.2.
- **Background variation:** APCA distinguishes light-on-dark vs dark-on-light better.

### Tools

- **APCA Reader** — browser extension, official from Andrew Somers
- **Polychrom** — Figma plugin; outputs Lc values
- **Web AIM Contrast Checker** — adds APCA mode

## Practical defaults

**Body text on white:**
- 2.2 AA pass: `#595959` (4.51:1) — minimal
- APCA-comfortable: `#3a3a3a` (Lc ~80) for 14pt body
- Recommended: `#222` (Lc ~92) for body

**Body text on charcoal `#121212`:**
- 2.2 AA pass: `#a8a8a8` (4.51:1)
- APCA-comfortable: `#cccccc` (Lc ~85) for body

## Dark mode pitfalls

- **Pure black `#000` background:** causes halation with bright text. Use `#121212`, `#0a0a0a`, or token like `--surface-base: oklch(15% 0.005 270)`.
- **Pure white `#FFF` text on black:** same halation issue. Use `#f5f5f5` or `#fafafa`.
- **Saturated colors look brighter on dark.** Reduce saturation 15–25% for dark-mode tokens.

## OKLCH for token systems

`oklch()` is the perceptually-uniform color space arriving in 2024–2025 browsers. Recommended for design tokens:

```css
:root {
  --color-surface-base: oklch(98% 0.005 270);
  --color-surface-elevated: oklch(96% 0.005 270);
  --color-text-primary: oklch(20% 0 0);
  --color-text-secondary: oklch(45% 0 0);
  --color-action-primary: oklch(60% 0.18 270);
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-surface-base: oklch(15% 0.005 270);
    --color-surface-elevated: oklch(20% 0.005 270);
    --color-text-primary: oklch(95% 0 0);
    --color-text-secondary: oklch(75% 0 0);
    --color-action-primary: oklch(70% 0.16 270);
  }
}
```

Saturation in OKLCH (the chroma value) stays perceptually consistent across hues. With HSL, equal saturation values appear different brightnesses by hue — a long-standing pain point.

## Anti-patterns (cross-ref)

- Light-gray-on-white text → SHOULD-AVOID #10
- Pure black/white surfaces → SHOULD-AVOID (halation)
- Color-only state signaling (red without icon) → MUST avoid (excludes color-blind)

## Sources

- WCAG 2.2 AA — https://www.w3.org/TR/WCAG22/
- APCA — https://git.apcacontrast.com/documentation/APCA_in_a_Nutshell.html
- WCAG 3.0 Working Draft — https://www.w3.org/TR/wcag-3.0/

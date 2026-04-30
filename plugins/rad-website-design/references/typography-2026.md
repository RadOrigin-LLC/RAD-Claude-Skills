# Typography — 2026 Reference

## Defaults (must-do)

- **Body font ≥ 16px.** Smaller triggers iOS auto-zoom on form focus. Excludes 40+ vision.
- **Variable fonts.** One file per family; control weight/optical-size via `font-variation-settings`. Reduces HTTP requests vs. multiple weight files.
- **`rem` + `clamp()` for sizes** — never raw `px`. Pixel sizes disable the browser's user font-size control.
- **Line-height:** body 1.5–1.6, headings 1.1–1.25. Tighter for display, looser for body.
- **Max line length:** 65–75ch for body. Beyond ~80ch, comprehension drops.

## Variable font axes

| Axis | Tag | Use |
|---|---|---|
| Weight | `wght` | 100–900; the most useful for hierarchy |
| Optical size | `opsz` | Match font shape to size — small text gets sturdier letterforms |
| Width | `wdth` | Condensed/expanded for layout fit |
| Slant | `slnt` | Slant without italic glyph variants |
| Italic | `ital` | True italic (not slanted) |

```css
.headline {
  font-family: "Inter Var";
  font-variation-settings: "wght" 760, "opsz" 32;
  font-size: clamp(2rem, 4vw + 1rem, 4rem);
  line-height: 1.05;
}
```

## Pairing

- **One display + one body family.** More than two = clutter (anti-pattern).
- **Don't pair** Inter + Roboto (both neutral, no contrast). Pair contrast: serif display + sans body, or geometric + humanist.
- **Avoid the 2024–2025 default** of Inter on white with purple gradient — it reads as AI-slop.

## Distinctive type choices (away from defaults)

- Geometric: Söhne, Aktiv Grotesk, GT America
- Humanist: Inter Display (NOT Inter), Recoleta, Söhne Mono
- Editorial: Tiempos, Editorial New, GT Sectra
- Variable + Mono: Berkeley Mono, JetBrains Mono Variable, Commit Mono
- Open-source bold choices: Geist, Migra, PP Editorial New, Author

For **public/free options**, Google Fonts has solid variable fonts: Inter Var, Crimson Pro, Outfit, Lexend, Manrope, Space Grotesk (use sparingly — it's overused).

## Hierarchy without color

In Calm UX, **weight + size + spacing** carry hierarchy — not color. Reserve color for state (CTA, success, error, info), not importance.

Example:
```css
:root {
  --type-display: 4rem;
  --type-h1: 2.5rem;
  --type-h2: 1.75rem;
  --type-h3: 1.25rem;
  --type-body: 1rem;
  --type-small: 0.875rem;
  --weight-display: 760;
  --weight-bold: 600;
  --weight-regular: 400;
}
```

## Anti-patterns (cross-ref)

- Pixel sizing → SHOULD-AVOID #9
- Font clutter (>2 families) → SHOULD-AVOID #9
- AI-slop default (Inter/Roboto/Arial + purple gradient) → SHOULD-AVOID #17

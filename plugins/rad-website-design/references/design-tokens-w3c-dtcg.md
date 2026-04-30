# Design Tokens — W3C DTCG Reference

## Why DTCG

The W3C Design Tokens Community Group (DTCG) format is the **vendor-neutral** token spec. Adopting it means:

- Tools (Figma, Style Dictionary, Tokens Studio, etc.) can read and write the same `.tokens.json` files.
- AI coding agents (via MCP, Cursor, Claude Code) can consume tokens directly to output theme-consistent code.
- Migration between platforms is mechanical, not a rewrite.

Spec: https://tr.designtokens.org/format/

## File structure

A token file is JSON with `$type`, `$value`, and optional `$description` per token.

```json
{
  "color": {
    "neutral": {
      "50":  { "$type": "color", "$value": "#fafafa" },
      "100": { "$type": "color", "$value": "#f5f5f5" },
      "900": { "$type": "color", "$value": "#121212" }
    }
  }
}
```

## Three-tier hierarchy

1. **Global (raw values)** — `color.neutral.900: #121212`
2. **Semantic (intent)** — `color.surface.background.default → {color.neutral.50}`
3. **Component (specific)** — `button.primary.background → {color.surface.action.default}`

Every layer references the previous via `{}` reference syntax. Never hardcode a hex into a component token; always reference semantic.

```json
{
  "color": {
    "neutral": { "50": { "$type": "color", "$value": "#fafafa" } },
    "surface": {
      "background": {
        "default": { "$type": "color", "$value": "{color.neutral.50}" }
      }
    }
  },
  "button": {
    "primary": {
      "background": {
        "$type": "color",
        "$value": "{color.surface.background.default}"
      }
    }
  }
}
```

## Token types ($type)

- `color` — `#rrggbb`, `oklch(...)`, etc.
- `dimension` — `16px`, `1rem`, `clamp(...)`
- `fontFamily`, `fontWeight`, `fontSize`
- `duration` — `200ms`
- `cubicBezier` — `[0.4, 0, 0.2, 1]`
- `shadow` — composite (offsetX, offsetY, blur, spread, color)
- `border` — composite (color, style, width)
- `gradient` — composite (color stops)
- `transition` — composite

## Theming via mode-aware tokens

```json
{
  "color": {
    "surface": {
      "background": {
        "$type": "color",
        "$value": "{color.neutral.50}",
        "$extensions": {
          "modes": {
            "light": "{color.neutral.50}",
            "dark": "{color.neutral.900}"
          }
        }
      }
    }
  }
}
```

Tools like Tokens Studio and Style Dictionary read `$extensions.modes` and emit per-theme CSS variables.

## Style Dictionary pipeline

`style-dictionary` is the canonical tool for transforming `.tokens.json` into platform output (CSS, iOS, Android, JS).

Output formats:
- CSS variables: `:root { --color-surface-background-default: #fafafa; }`
- JS/TS: `export const colorSurfaceBackgroundDefault = '#fafafa';`
- iOS: Swift Color extensions
- Android: XML colors

## Naming conventions

- Use kebab-case in CSS: `--color-surface-background-default`
- Use dot.notation in JSON: `color.surface.background.default`
- Prefix by type: `color`, `space`, `font`, `shadow`, `radius`, `border`, `motion`
- Order generic → specific: `color.action.primary.background.hover`

## Pitfalls

- **Don't skip the semantic layer.** Components referencing `color.blue.500` directly is brittle — when you re-theme, every component breaks.
- **Don't over-normalize.** Five layers of indirection is unreadable. Three tiers (global / semantic / component) is the sweet spot.
- **Don't fork tokens per app.** A monorepo with one source of truth + per-app overrides via mode is cleaner than copies.
- **Don't expose internal tokens to product code.** Apps consume semantic + component, not global.

## Integration with AI coding agents

Via MCP, expose your tokens file to Claude Code, Cursor, etc. The agent can:
- Read tokens to output CSS variables consistent with your system
- Suggest token names for new component variants
- Detect components hardcoding values that should be tokenized

Recommended MCP server: `tokens-mcp` or roll your own thin wrapper around the tokens JSON.

## Anti-patterns

- Raw hex in components (skips semantic layer) → SHOULD-AVOID
- Naming tokens by appearance (`color.blue.500`) instead of intent (`color.action.primary`) → bad pattern; will break on re-theme

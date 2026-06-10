# rad-a11y validators

Four pure-stdlib Python 3.8+ scripts that turn the LLM regex passes inside `/a11y-review` into deterministic, JSON-emitting validators. The skill and the `a11y-reviewer` agent run these first; LLM judgment then fills the gaps that static analysis can't decide ([HEURISTIC] findings).

No `pip install` required. All scripts share the same exit-code convention: `0` on success (regardless of how many findings), `2` on path errors, `3` on `--no-fallback` enforcement failure.

## What's here

| Script | What it does | Confidence tag emitted |
|---|---|---|
| `scan-jsx-patterns.py` | High-confidence pattern scan over `.tsx` / `.jsx` / `.astro` / `.html` / `.svelte` / `.vue` / CSS for the top WCAG failure patterns: `outline-none` w/o `focus-visible` replacement, `aria-hidden` on focusable, missing/bad `alt`, hardcoded ARIA states (`aria-expanded="true"` as string literal in JSX), `<div onClick>` without role + key handlers, redundant ARIA roles, positive `tabindex`, `<a>` without `href` used as click target. | `[STATIC]` |
| `check-tailwind-contrast.py` | Real WCAG sRGB → relative luminance → contrast ratio math over Tailwind class pairs (`text-X-Y` + `bg-X-Y` on the same `className`). Built-in Tailwind v3 default palette; best-effort regex parse of `tailwind.config.{js,ts,cjs,mjs}` for custom colors. Border-on-bg contrast (3:1) checked separately. | `[STATIC]` (ratio < 3.0), `[HEURISTIC]` (ratio 3.0–4.5, could pass for large text) |
| `check-target-size.py` | WCAG 2.5.8 (Target Size Minimum, new in 2.2): scans interactive elements (`<button>`, `<a>`, `<div role="button">`) for Tailwind sizing/padding classes producing sub-24×24px targets. Padding-aware. | `[STATIC]` for `<button>` / `role="button"`; `[HEURISTIC]` for `<a>` (inline-link exception applies) |
| `lint-aria.py` | Wraps `eslint-plugin-jsx-a11y` via `npx eslint --no-eslintrc -c ...` when available. Falls back to a curated regex ruleset (~10 rules: `alt-text`, `anchor-has-content`, `no-autofocus`, `no-distracting-elements`, `tabindex-no-positive`, `iframe-has-title`, `html-has-lang`, `scope`, `media-has-caption`, `no-redundant-roles`) when not. Always emits a `recommendation` field nudging users toward installing the real plugin. | `[STATIC]` (real eslint or regex fallback) |

## Usage

```bash
# Default: JSON to stdout for skill/agent consumption
python plugins/rad-a11y/scripts/scan-jsx-patterns.py ./src

# Human-readable for ad-hoc inspection
python plugins/rad-a11y/scripts/scan-jsx-patterns.py ./src --pretty

# Custom excludes (default: node_modules, dist, build, .next, .astro, etc.)
python plugins/rad-a11y/scripts/scan-jsx-patterns.py ./src --exclude "node_modules,vendor"

# Contrast: optionally point at a tailwind config explicitly
python plugins/rad-a11y/scripts/check-tailwind-contrast.py ./src --config ./tailwind.config.ts

# ARIA lint: force fallback even if eslint-plugin-jsx-a11y is installed
python plugins/rad-a11y/scripts/lint-aria.py ./src --fallback

# ARIA lint in CI: fail if real plugin isn't installed
python plugins/rad-a11y/scripts/lint-aria.py ./src --no-fallback
```

## Output schema

All four scripts emit JSON of this shape:

```json
{
  "tool": "<script-name>",
  "version": "1.0.0",
  "files_scanned": 42,
  "findings_count": 7,
  "findings": [
    {
      "category": "outline-none-no-focus-visible",
      "wcag": "2.4.7",
      "severity": "critical",
      "confidence": "STATIC",
      "file": "src/Button.tsx",
      "line": 12,
      "snippet": "outline-none",
      "fix": "Replace outline removal with a visible focus indicator. ..."
    }
  ]
}
```

Tool-specific extra fields:
- **scan-jsx-patterns**: `tag`, `attribute`, `value`, `role`, `has_role`, `has_keyhandler`
- **check-tailwind-contrast**: `fg_class`, `fg_hex`, `bg_class`, `bg_hex`, `ratio`, `required_normal`, `required_large`, `required` (border)
- **check-target-size**: `tag`, `computed_width_px`, `computed_height_px`, `threshold_px`
- **lint-aria**: `column`, `message`, `source` (`eslint-plugin-jsx-a11y` or `regex-fallback`), `recommendation`

## What these scripts do NOT do

- **Do not run a real browser engine.** None of these execute axe-core. Real axe needs a DOM. Set up `@axe-core/playwright` or `jest-axe` via the `a11y-testing` skill for that.
- **Do not measure runtime focus visibility quality.** Source-level focus-replacement detection only.
- **Do not classify large vs. body text** for the 3:1 vs. 4.5:1 contrast threshold. Pairs in the 3.0–4.5:1 range are tagged `[HEURISTIC]` so the reader can decide.
- **Do not parse function-based or imported color palettes** in `tailwind.config.*`. Object-literal palettes only. If the script can't parse your custom colors, classes referencing those colors are silently skipped (you'll see fewer findings, not wrong findings).
- **Do not test screen reader announcement quality.** Source can't tell you that.

## Why these exist

Before 2.1, `/a11y-review` did all this work as LLM regex passes. That's slow, non-deterministic across model runs, and produces output the user can't reproduce or audit. Moving the high-confidence patterns into Python scripts:

- Makes the deterministic part deterministic.
- Lets the LLM focus on what it's good at — `[HEURISTIC]` judgment about alt-text meaningfulness, ARIA logic in complex widgets, reading order.
- Gives the user something they can run themselves, in CI, without invoking Claude.
- Aligns rad-a11y with the validator pattern other rad-* plugins follow (rad-coolify-orchestrator's 4 lint scripts, rad-planner's DAG/checklist validators).

The honesty constraint from rad-a11y 2.0 stays in force: every finding still carries a confidence tag, the report still produces no Pass/Fail verdict, and `[NEEDS-MANUAL]` flags are still surfaced for things only a browser, screen reader, or human can verify.

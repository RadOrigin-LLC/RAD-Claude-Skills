---
name: a11y-review
description: >
  Static analysis pass over JSX/HTML/CSS source for WCAG 2.2 AA failure patterns. Does NOT run
  axe-core, does NOT measure real contrast, does NOT test runtime behavior — pair with a11y-testing
  for that. Use when the user asks for an accessibility review, a11y check, WCAG review, "is this
  accessible?", "does my site meet WCAG?", "check my component for accessibility", "review
  accessibility of", "check for a11y issues", "fix accessibility issues", or any request to scan
  a web page, component, or codebase for WCAG 2.2 AA failure patterns. Findings are tagged by
  detection confidence; the report does not produce a Pass/Fail verdict because static analysis
  cannot defensibly produce one.
argument-hint: "[path/to/component, directory, or 'all' for full codebase scan]"
allowed-tools: Read, Glob, Grep, Bash
---

# Accessibility Review (static analysis)

Perform a structured **static analysis pass** over the specified component, page, or codebase. Execute all eight phases in order and produce an actionable, severity-ranked report with each finding tagged by confidence level.

## What this skill is — and what it isn't

This skill performs **pattern-based static analysis** over `.tsx` / `.jsx` / `.astro` / `.html` / `.css` source. It is **not** a WCAG audit, does **not** run axe-core, does **not** test runtime focus behavior, does **not** measure real contrast ratios, and does **not** test with screen readers.

**What this skill catches well (high confidence):**
- Missing `alt` on `<img>`, missing `<label>` association, missing accessible name on icon buttons
- `outline: none` / `outline-none` without a focus-visible replacement (Tailwind users — axe often misses this because it inspects computed styles)
- `aria-hidden="true"` on focusable elements or their ancestors
- Hardcoded ARIA states (`aria-expanded="true"` as a string literal, not driven by component state)
- `<div onClick>` / `<span onClick>` without role + keyboard handlers
- Skipped heading levels, missing landmarks
- React-specific focus drift (modal close handlers without focus restoration)

**What this skill flags but cannot confirm (medium confidence):**
- Color contrast — flags suspect Tailwind class combinations by name; real sRGB → WCAG ratio math and Tailwind palette parsing is not yet implemented
- ARIA state synchronization beyond the simplest cases
- Whether a `<fieldset>` correctly wraps a logical group

**What this skill cannot see at all (requires runtime / manual):**
- Whether `alt` text is *meaningful* — only checks presence and obvious anti-patterns
- Reading order matches visual order — needs DOM traversal at runtime
- Focus indicator is *sufficiently visible* — needs a browser
- Live region announcements arrive at the right time — needs real assistive tech
- Keyboard interactions feel logical to a user — needs a human
- Custom widget keyboard contracts implemented end-to-end — needs APG-pattern verification with a screen reader
- Screen reader announcement coherence — needs NVDA / JAWS / VoiceOver

For runtime verification, use `a11y-testing` to set up real axe via jest-axe and @axe-core/playwright. For manual verification, use a real screen reader.

## Audit Scope

When invoked with a path, audit that file or directory. When invoked with "all" or no argument, locate the main source directory (src/, app/, components/, pages/) and audit the full codebase.

Exclude: `node_modules`, `dist`, `build`, `.next`, `coverage`, `.astro`.

---

## Phase 1: Orient — Build the File Map

Before checking anything:

1. Use Glob to discover all UI files:
   - `**/*.tsx`, `**/*.jsx`, `**/*.astro` — components and pages
   - `**/*.html` — static markup
   - `**/*.css`, `**/*.scss`, `**/*.module.css` — stylesheets
   - `**/tailwind.config.*` — Tailwind configuration

2. Read `package.json` to detect the stack:
   - React / Next.js / Astro / Vue / Svelte
   - Radix UI / Headless UI / Tailwind CSS
   - Testing libraries (jest-axe, @axe-core/playwright)

3. Count total component files. Report: "Scanning X components across Y directories."

---

## Phase 2: Semantic Structure

Check every component file for semantic HTML violations.

### Heading Hierarchy (WCAG 1.3.1)
- Flag any heading that skips a level (e.g., `<h1>` → `<h3>` with no `<h2>`)
- Flag multiple `<h1>` elements on a single page
- Flag headings used purely for visual sizing (e.g., `<h4>` inside a card that is `font-bold text-sm`)
- Flag missing `<h1>` on page-level components

### Landmark Regions (WCAG 1.3.6)
- Flag pages missing `<main>`, `<header>`, `<nav>`, or `<footer>` landmarks
- Flag multiple `<nav>` or `<header>` elements that lack unique `aria-label` or `aria-labelledby`
- Flag `<div id="content">` patterns that should be `<main>`

### Semantic Element Usage (WCAG 4.1.2)
- Flag `<div onClick>` and `<span onClick>` without `role` and `tabindex`
- Flag `<div role="button">` when a `<button>` should be used
- Flag `<a>` tags without `href` used as buttons
- Flag `<b>` / `<i>` used for semantic emphasis (should be `<strong>` / `<em>`)
- Flag missing `<label>` wrapping for icon-only inputs
- React: Flag wrapper `<div>` inside `<ul>`, `<ol>`, `<table>` — suggest Fragments

### Images and Alt Text (WCAG 1.1.1)
- Flag `<img>` without `alt` attribute
- Flag `<img alt="image">`, `<img alt="photo">`, or file-name-as-alt anti-patterns
- Flag `<img>` with redundant alt (same as adjacent caption text)
- Flag decorative images without `alt=""` or `role="presentation"`

---

## Phase 3: ARIA Usage

Check all ARIA attribute usage across components.

### The ARIA First Principles
- **No ARIA is better than bad ARIA.** Flag every instance where ARIA overrides correct native semantics.
- Flag `role="button"` on `<button>` — redundant
- Flag `role="heading"` on `<h1>`–`<h6>` — redundant
- Flag `role="list"` on `<ul>` / `<ol>` — only needed in some browsers with Tailwind `list-none`

### aria-hidden Misuse (WCAG 1.3.1, 4.1.2)
- **Critical:** Flag `aria-hidden="true"` on any element that is focusable or contains focusable children
- Flag interactive buttons/links inside an `aria-hidden` ancestor
- Flag SVG icons missing `aria-hidden="true"` when decorative (or inside a labeled button)

### Missing Accessible Names (WCAG 4.1.2, 2.4.6)
- Flag `<button>` with no text content, no `aria-label`, and no `aria-labelledby`
- Flag icon-only buttons: `<button><svg>...</svg></button>` with no accessible name
- Flag `<a>` with no text, no `aria-label`, no `aria-labelledby`
- Flag `<input type="image">` without `alt`

### ARIA State Synchronization (WCAG 4.1.2)
- Flag `aria-expanded` attributes hardcoded to `"true"` or `"false"` that are not driven by state
- Flag disclosure components (accordions, dropdowns) missing `aria-expanded` entirely
- Flag `aria-checked`, `aria-selected`, `aria-pressed` not connected to component state
- React: Flag string literals `aria-expanded="true"` — should be `aria-expanded={isOpen}`

### Live Regions (WCAG 4.1.3)
- Flag dynamic status updates (toasts, alerts, loading states) with no `aria-live`, `role="status"`, or `role="alert"`
- Flag `role="alert"` used for non-urgent messages (should be `role="status"`)
- Flag live regions whose content is set before being added to the DOM (screen readers miss the announcement)

---

## Phase 4: Keyboard and Focus

Check keyboard operability across all interactive components.

### Focus Visibility (WCAG 2.4.7, 2.4.11)
- **Critical:** Flag any CSS with `outline: none`, `outline: 0`, or Tailwind `outline-none` that is not immediately followed by a custom focus indicator
- Flag Tailwind `focus:outline-none` without `focus-visible:ring-*` replacement
- Flag `*:focus { outline: none }` global CSS reset without a replacement

### Focus Order (WCAG 2.4.3)
- Flag `tabindex` values greater than 0 (breaks natural DOM order)
- Flag visually ordered content whose DOM order is inverted via CSS `order`, `float`, or `position: absolute`

### Keyboard Traps (WCAG 2.1.2)
- Flag custom dropdown, popover, or menu components with no `Escape` key handler
- Flag modal/dialog implementations that do not trap focus inside when open
- Flag custom components that intercept `Tab` without providing a clear exit

### Skip Links (WCAG 2.4.1)
- Flag page-level layouts that have no "Skip to main content" link
- Flag skip links present but permanently hidden (not just visually hidden until focused)

### Interactive Element Requirements (WCAG 2.1.1)
- Flag `<div role="button">` / `<div tabindex="0">` missing `keydown`/`keyup` handlers for `Enter` and `Space`
- Flag custom checkbox / radio implementations missing keyboard activation

### React-Specific Focus Drift
- Flag `useEffect` that removes a modal/panel from the DOM without calling `.focus()` on the trigger element
- Flag dialog close handlers that do not restore focus: look for `setIsOpen(false)` or `onClose()` without a preceding `triggerRef.current?.focus()`

---

## Phase 5: Color Contrast and Motion

### Contrast (WCAG 1.4.3, 1.4.11)
Check Tailwind color utility classes and CSS color values for likely contrast failures:
- Flag text on colored backgrounds where the combination is known-low-contrast (e.g., `text-gray-400 bg-white`, `text-yellow-300 bg-white`)
- Flag UI component borders/outlines that use light neutrals (`border-gray-200`, `border-gray-300`) on white backgrounds — likely fail 3:1
- Flag placeholder text (`::placeholder`) styled with low-contrast colors
- Note: Full contrast ratios require a browser tool — flag suspects, recommend using axe DevTools or Colour Contrast Analyser for verification

### Color-Only Meaning (WCAG 1.4.1)
- Flag error states indicated only by red border/text with no icon, label, or pattern
- Flag status indicators (badges, dots) that rely solely on color with no text or shape alternative
- Flag link text that is only differentiated from body text by color (no underline)

### Motion and Animation (WCAG 2.3.3)
- Flag CSS `animation` or `transition` on non-UI state changes (page decorations, hero animations) without `@media (prefers-reduced-motion: reduce)` override
- Flag Tailwind animations (`animate-spin`, `animate-bounce`, `animate-pulse`) applied to non-status elements without `motion-reduce:` or `motion-safe:` modifier
- Flag auto-playing videos or carousels with no pause/stop control
- Flag content that flashes or blinks (potential seizure trigger)

### Target Size (WCAG 2.5.8 — new in 2.2)
- Flag interactive targets smaller than 24×24px — look for `w-4 h-4`, `p-0`, `text-xs` buttons that are icon-only
- Flag tightly packed link lists with less than 24px spacing between targets

---

## Phase 6: Forms

Check all form components.

### Label Association (WCAG 1.3.1, 3.3.2)
- **Critical:** Flag `<input>`, `<select>`, `<textarea>` without an associated `<label>` (via `for`/`id` or wrapping)
- Flag `htmlFor` in React that does not match an `id` on any input
- Flag `placeholder` used as the only labeling mechanism

### Required and Validation (WCAG 3.3.1, 3.3.2)
- Flag required fields with no `required` attribute or `aria-required="true"`
- Flag required indicators (asterisks) with no explanation in the form instructions
- Flag error messages that are not programmatically linked to their input via `aria-describedby`
- Flag `aria-invalid` not set to `"true"` on invalid inputs during validation

### Fieldset/Legend (WCAG 1.3.1)
- Flag groups of related checkboxes or radio buttons not wrapped in `<fieldset>` + `<legend>`
- Flag `<legend>` used but empty or containing only whitespace

---

## Phase 7: SVG and Icons

Check all SVG usage.

### Decorative SVGs (WCAG 1.1.1)
- Flag inline `<svg>` without `aria-hidden="true"` when inside a labeled button or link (screen readers will attempt to read raw SVG content)
- Flag `<svg>` without `focusable="false"` in IE/Edge-compatible codebases

### Informative SVGs (WCAG 1.1.1)
- Flag standalone SVGs (logos, charts, illustrations) without `role="img"` and either `aria-label` or a hidden text alternative
- Flag SVGs with a `<title>` but no `aria-labelledby` pointing to it (cross-browser reliability issue)

---

## Phase 8: Stack-Specific Checks

### Tailwind CSS
- Flag `outline-none` without `focus-visible:ring-*` replacement (most common Tailwind a11y failure)
- Flag missing `sr-only` on icon-only button text labels
- Confirm `motion-safe:` / `motion-reduce:` usage on animated elements
- Check for `list-none` on `<ul>` — some screen readers strip list semantics; recommend `role="list"` if semantics matter

### React
- Confirm `aria-*` props use JSX booleans correctly: `aria-expanded={isOpen}` not `aria-expanded="true"`
- Flag `key` props on focusable list items that change order (forces DOM remount, loses focus position)
- Flag `dangerouslySetInnerHTML` in components — requires manual a11y verification of injected content

### Astro
- Flag islands using `client:visible` or `client:idle` on keyboard-interactive components — risk of hydration dead zones
- Recommend pre-hydrated ARIA states via `data-*` attributes for components that render with `client:visible`
- Check for skip link in the root layout (`src/layouts/*.astro`)

### Radix UI / Headless UI
- Check that `asChild` usage spreads all props and forwards refs — missing ref breaks Radix focus management
- Confirm Radix `Dialog.Content` has `aria-labelledby` pointing to `Dialog.Title`

---

## Reporting Format

Group findings into four severity levels. Report only findings with evidence. **Every finding must carry a detection-confidence tag** in addition to its severity — readers should be able to see which findings the static scan can prove and which are pattern-based heuristics or hand-offs to manual verification.

### Detection-confidence tags

- **`[STATIC]`** — Deterministic detection: the pattern is present in source and the failure mode is unambiguous from source alone. Example: `<img>` with no `alt`, `aria-hidden="true"` on a `<button>`, `outline-none` with no `focus-visible:` replacement on the same element. These are PR-blockers when they're also Critical/Serious severity.
- **`[HEURISTIC]`** — LLM judgment over patterns where source isn't dispositive. Example: "this `aria-label` looks redundant with adjacent visible text," "this `<div role="button">` *probably* needs keyboard handlers." These should be reviewed before fixing — the model can be wrong.
- **`[NEEDS-MANUAL]`** — The pattern *suggests* a problem, but only a browser, axe runtime, or screen reader can confirm. Example: contrast pair flagged by class name (no real ratio computed), live region timing, focus indicator visibility quality, alt-text meaningfulness. Surfaced so the reader knows what to verify next.

### Severity levels (orthogonal to confidence)

#### Critical (blocks PR when `[STATIC]`)
Issues that make the UI completely unusable for keyboard or screen reader users.
- Keyboard traps (no Escape, focus stuck) — `[HEURISTIC]` from source; needs runtime confirmation
- Missing focus indicators (bare `outline-none` with no replacement) — `[STATIC]`
- `aria-hidden="true"` on focusable elements — `[STATIC]`
- Interactive `<div>` with no keyboard handler — `[STATIC]`

#### Serious (fix before ship)
Issues that significantly impair assistive technology users.
- Missing form labels — `[STATIC]` (presence) / `[HEURISTIC]` (correct association)
- Icon-only buttons with no accessible name — `[STATIC]`
- Missing heading structure on pages — `[STATIC]`
- Dynamic content with no live region announcement — `[STATIC]` (missing markup) / `[NEEDS-MANUAL]` (timing)

#### Moderate (fix in next sprint)
Issues that degrade the experience for some users.
- Skipped heading levels — `[STATIC]`
- Missing skip links — `[STATIC]`
- Hardcoded ARIA states not driven by component state — `[STATIC]`
- Decorative SVGs not hidden from screen readers — `[STATIC]`

#### Minor (best practice)
Low-impact issues or recommendations.
- Missing `lang` on `<html>` — `[STATIC]`
- Generic link text ("click here", "read more") — `[HEURISTIC]`
- `tabindex > 0` values — `[STATIC]`
- Missing `aria-label` on duplicate landmarks — `[STATIC]`

For each finding, output:
```
[SEVERITY] [CONFIDENCE] WCAG X.X.X — Short description
File: path/to/file.tsx:line
Code: <the problematic snippet>
Fix: Specific remediation
[Notes: <any caveat — e.g., "real contrast ratio not computed; verify with axe DevTools">]
```

### End-of-report summary

Do **not** issue a Pass / Fail / Compliance verdict. Static analysis cannot produce a defensible WCAG 2.2 AA pass/fail — that requires runtime + manual + assistive-tech verification. Instead, end with:

```
Static scan summary
-------------------
[STATIC]      findings: <N> Critical, <N> Serious, <N> Moderate, <N> Minor
[HEURISTIC]   findings: <N> total — review before fixing, model can be wrong
[NEEDS-MANUAL] flags:    <N> total — verify with axe DevTools / screen reader

Top 3 priority fixes (highest severity × highest confidence):
  1. <file:line> — <description>
  2. <file:line> — <description>
  3. <file:line> — <description>

Recommended next steps:
  - Set up real axe runtime (use the a11y-testing skill) — covers categories static scan can't
  - Manual screen reader pass on <list any [NEEDS-MANUAL] flagged components>
  - Browser-based contrast verification on <list any color-related [NEEDS-MANUAL] flags>
```

---

## What real axe / Lighthouse catches that this skill doesn't, and vice versa

Real axe (running in a browser via jest-axe or @axe-core/playwright) catches a different subset than this static skill. They overlap heavily but each catches things the other misses.

**Real axe catches but this static skill cannot:**
- Computed contrast ratios (real sRGB → WCAG math against rendered colors)
- Duplicate `id` after dynamic component rendering
- ARIA attribute validity against the resolved role
- Some keyboard accessibility paths that depend on runtime DOM

**This static skill catches but real axe often misses:**
- Tailwind `outline-none` written without a `focus-visible:ring-*` replacement (axe sees the resolved `:focus` style, which may have a default UA outline depending on browser/version, leading to false negatives)
- Hardcoded ARIA state literals in JSX source (`aria-expanded="true"` as a string instead of `={isOpen}`) — axe sees the value at the moment of scan, missing the bug that the value never updates
- React modal close handlers that don't restore focus to the trigger (axe sees the focus state after close, but the underlying source pattern is invisible to it)
- Astro `client:visible` / `client:idle` on keyboard-interactive components (hydration timing issues)

The honest framing: **`/a11y-review` and real axe are complementary, not redundant.** Run both. The widely-cited "axe catches 30–80%" range refers to real axe — `/a11y-review` covers a subset of that range plus some patterns axe misses, which is why every finding here is tagged with detection confidence so you know what you actually have.

# rad-a11y — WCAG 2.2 AA accessibility patterns + static review for Claude Code.

**What it is.** A six-skill plugin plus an autonomous reviewer agent. Four skills are *reference/teaching content* on accessible patterns (semantic HTML, ARIA, keyboard/focus, forms). One skill (`a11y-testing`) helps you set up real automated testing with axe-core, jest-axe, and Playwright. One skill (`a11y-review`) and the `a11y-reviewer` agent perform a *static analysis pass* over your source code, flagging the categories of WCAG failures that are reliably detectable from JSX/HTML/CSS without a browser.

**What it solves.** Most accessibility regressions are introduced as code is written — `outline: none` without a focus replacement, an `aria-hidden` on a focusable element, an icon button with no accessible name, a hardcoded `aria-expanded="true"` string. These are catchable from source. rad-a11y catches them before the PR, and explains the fix with the WCAG criterion cited. For things that genuinely require runtime or human judgment (real contrast ratios, screen reader announcement quality, focus visibility quality, alt-text *meaning*), it tells you so explicitly rather than pretending its scan is sufficient.

**What it isn't.** It is **not** an audit. It does not run axe-core, does not test focus behavior at runtime, and does not test with a screen reader. It cannot tell you whether your alt text is meaningful, whether your reading order makes sense, or whether your focus indicator is sufficiently visible — those need a browser, an AT, or a human. Tailwind contrast ratios *are* computed with real sRGB → WCAG math via `check-tailwind-contrast.py`, but contrast on arbitrary inline / runtime-computed styles still needs a browser audit. It is also **not** a compliance certifier; no static tool can produce a defensible WCAG 2.2 AA pass/fail verdict, and rad-a11y does not pretend to.

## What You Can Do With This

- **Get an accessible-by-default pattern** for any custom interactive component (dialogs, menus, tabs, accordions, comboboxes) — with the WAI-ARIA APG keyboard contract spelled out.
- **Run a static review pass** over a component or full codebase that flags high-confidence WCAG 2.2 AA failures with file paths, line numbers, and specific fixes.
- **Set up real automated testing** with eslint-plugin-jsx-a11y (write-time), jest-axe (component), and @axe-core/playwright (e2e) — the actual axe engine, in your CI.
- **Get explicit guidance on what static review *can't* catch** so you know when to reach for a browser, axe DevTools, or a screen reader.

## How It Works

| Skill | Type | What it does |
|-------|------|---------|
| `a11y-semantic-html` | Reference | Semantic structure, heading hierarchy, landmark regions, "which element should I use" |
| `a11y-aria-patterns` | Reference | ARIA roles, attributes, live regions, APG keyboard contracts — when to use, when not to |
| `a11y-keyboard-focus` | Reference | Keyboard navigation, focus rings, focus trapping, skip links, focus restoration |
| `a11y-forms` | Reference | Labels, errors, required fields, fieldset/legend, validation announcement |
| `a11y-testing` | Setup | Configure eslint-plugin-jsx-a11y, jest-axe, @axe-core/playwright. Real axe runs in your project, not in this plugin. |
| `a11y-review` | Scanner | Static pattern-match over JSX/HTML/CSS. Findings tagged `[STATIC]` / `[HEURISTIC]` / `[NEEDS-MANUAL]`. No Pass/Fail verdict. |

| Agent | Type | What it does |
|-------|------|---------|
| `a11y-reviewer` | Autonomous scanner | Runs the same static pass as `/a11y-review` but proactively, on completed UI work. Same honesty rules — flags what static analysis can see, surfaces what it can't. |

## What automated tools (real axe / Lighthouse) can and can't catch

This is the honest framing rad-a11y operates under, including itself:

**Reliably caught by automation:**
- Missing `alt` attributes (presence)
- Missing `<label>` association
- Duplicate `id` values
- Invalid ARIA attribute names and values
- Empty buttons / links (no accessible name)
- Some contrast failures (when both colors are computed and resolvable)
- Some keyboard accessibility failures (`tabindex` on non-interactive without role)

**Not caught — requires manual verification:**
- Whether `alt` text is *meaningful* (not just present)
- Reading order matches visual order
- Focus indicator is *sufficiently visible*
- Live region announcements arrive at the right time
- Keyboard interactions feel logical to a real user
- Custom widgets follow APG keyboard patterns end-to-end
- Screen reader announcements are coherent

The widely-cited "axe catches 30–80%" range comes from research on real axe runs against real pages. **rad-a11y's `a11y-review` is *static source analysis*, not real axe** — it catches a subset of what real axe catches, plus some patterns axe misses (like Tailwind `outline-none` without `focus-visible:ring-*` because axe sees the computed style after `:focus`, not the source class). Use both: rad-a11y at write-time, real axe at runtime.

## Quick Start

```bash
claude plugins add ./RAD-Claude-Skills/plugins/rad-a11y
```

```
Review my accessibility
Is this component keyboard accessible?
Check for WCAG violations
Set up axe-core testing
What's the right ARIA pattern for a combobox?
```

## What's NOT in scope

- **Does not run axe-core or any real browser engine.** The `a11y-review` skill is static pattern matching. To run real axe in your project, use `a11y-testing` to set up jest-axe / Playwright integration.
- **Does not verify contrast on arbitrary inline or runtime-computed styles.** Tailwind class pairs *are* checked with real sRGB → WCAG ratio math via `check-tailwind-contrast.py`, but contrast on inline `style` attributes or runtime-computed colors still needs a browser audit.
- **Does not test screen reader announcement quality.** That requires a real screen reader (NVDA, JAWS, VoiceOver) and a human.
- **Does not certify WCAG 2.2 AA compliance.** No static tool can. The reporting format gives you a confidence-tiered summary, not a Pass/Fail verdict.
- **Does not cover Vue or Svelte specifically.** Generic HTML rules apply, but no framework-specific checks for those stacks. React, Astro, and plain HTML/Tailwind are the first-class supported targets.

## Version

**2.2.0** — **Cross-model + stack-aware.**
- Phase 0 (validators) and Phase 1 (file map + stack detection) now issued as a single parallel tool-call burst on Opus 4.7 and Sonnet 4.6. Haiku 4.5 falls back to sequential phases if parallel batching misbehaves; the four validators still run in parallel via `&` + `wait` shell. Final report is identical regardless of model.
- Phase 1 builds a stack-detection record from `package.json` + config files: `react`, `nextjs`, `astro`, `tailwind`, `radix`, `headlessui`, `plain_html`. Phase 8 (stack-specific) only executes slices matching detected stack. Plain HTML projects skip Phase 8 entirely with a one-line note.
- `check-tailwind-contrast.py` self-skips when no Tailwind class pairs are present in source — no spurious "no findings" output for plain CSS projects.
- New `Cross-model note` and `Execution: parallel-first` sections in `/a11y-review` SKILL.md document the parallel batch and Haiku fallback explicitly.
- Same parallel-first + stack-aware pattern mirrored into the `a11y-reviewer` agent prompt.
- No behavior change in the four validators — same JSON output schema, same correctness.

**2.1.0** — **Mechanical validators (four Python scripts).**
- `scripts/scan-jsx-patterns.py` — high-confidence static scan over JSX/HTML/CSS for `outline-none` w/o focus replacement, `aria-hidden` on focusable, missing/bad `alt`, hardcoded ARIA states, `<div onClick>` without role + handlers, redundant ARIA roles, positive `tabindex`, `<a>` without `href` used as click target. Pure stdlib, JSON output.
- `scripts/check-tailwind-contrast.py` — **real WCAG sRGB → relative luminance → contrast ratio math** over Tailwind class pairs. Built-in v3 default palette + best-effort regex parse of `tailwind.config.{js,ts,cjs,mjs}` for custom colors. Border-on-bg contrast (3:1 UI threshold) checked separately.
- `scripts/check-target-size.py` — WCAG 2.5.8 (added in 2.2): scans interactive elements for sizing/padding classes producing sub-24×24px targets. Padding-aware. `<a>` tagged `[HEURISTIC]` (inline-link exception applies).
- `scripts/lint-aria.py` — wraps `eslint-plugin-jsx-a11y` via `npx eslint` when installed. Curated regex fallback (~10 rules: alt-text, anchor-has-content, no-autofocus, no-distracting-elements, tabindex-no-positive, iframe-has-title, html-has-lang, scope, media-has-caption, no-redundant-roles) when not.
- `/a11y-review` and `a11y-reviewer` agent now run all four validators in **Phase 0** as a single parallel Bash batch, before any LLM work. LLM phases now cover only what scripts can't decide — alt-text meaningfulness, complex ARIA logic, reading order, cross-element analysis.
- Validator findings are used **verbatim** by the skill/agent — no paraphrasing, no second-guessing. Determinism preserved end-to-end.
- Skips Phase 0 silently if Python is unavailable; LLM fallback runs and the report header notes `⚠ fallback mode`.

**2.0.0** — **Honesty pass.**
- Every `a11y-review` finding tagged `[STATIC]` / `[HEURISTIC]` / `[NEEDS-MANUAL]`. The reader knows the confidence level of each item.
- Pass/Fail verdict in the report dropped — replaced with a confidence-tiered summary that doesn't overclaim what static analysis can prove.
- "Compliance audit" framing dropped from skill and agent descriptions; replaced with "static review" / "static analysis pass."
- Vue / Svelte support claims dropped from plugin description and README — they were never actually backed by skill content.
- Tightened the "30–80% caught by automation" framing — specifies which categories are reliably caught by real axe vs. which require manual verification, and clarifies that `a11y-review` is *static source analysis*, not real axe.
- `a11y-testing` skill kept as the path to real axe / jest-axe / Playwright. That's where actual browser-engine accessibility testing lives.
- Reference skills (`a11y-semantic-html`, `a11y-aria-patterns`, `a11y-keyboard-focus`, `a11y-forms`) now explicitly labeled as "Reference" type to distinguish from "Scanner" and "Setup" skills.

**1.0.0** — Initial release: 6 skills + 1 reviewer agent covering WCAG 2.2 AA static review and pattern reference.

## License
Apache-2.0

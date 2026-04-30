---
name: web-design-should-do
description: >
  2026 web design SHOULD-DO recommendations — strongly recommended but not absolute requirements.
  Covers motion/animation, dark mode tuning, design tokens (W3C DTCG), internationalization,
  AI-era SEO/AEO, conversion patterns, microcopy, error handling, loading/empty states,
  onboarding, social proof, trust signals, risk reversal. Use when the user asks about
  conversion rate optimization, microcopy, error UX, loading/empty states, design systems,
  i18n, onboarding, trust signals, or any "polish" layer above the must-do baseline.
allowed-tools: Read, Glob, Grep
---

# 2026 Web Design — SHOULD-DO

These are recommendations that meaningfully lift quality but aren't legal/usability minimums. Apply them when (a) the project has time/budget, (b) the user is building beyond MVP, or (c) the user explicitly asks for polish.

If a should-do conflicts with a must-do baseline, the must-do wins.

## Motion & Animation

- **Functional animations 200–500ms** with non-linear spring easing (organic, tactile feel).
- **Tied to feedback only.** Button ripple from click coordinates, layout transitions, value changes. **Never decoration.**
- **Respect `prefers-reduced-motion: reduce`.** Wrap motion in a media query; replace with instant transitions or fade.

## Dark Mode (Tuning)

- Treat dark mode as a baseline expectation (>82% of users default to it).
- Never pure black `#000` or pure white `#FFF` — use deep charcoals + off-whites. Eye strain + halation.
- Dark mode is not "invert colors" — re-tune contrast, accent saturation, and elevation shadows separately.

## Design Tokens (W3C DTCG)

- **Adopt W3C DTCG `.tokens.json` format.** Vendor-neutral; portable across Figma, Style Dictionary, Tailwind, etc.
- **Three-tier hierarchy:**
  - **Global:** raw values (`color.gray.900: #121212`)
  - **Semantic:** intent (`color.surface.action.primary`)
  - **Component:** specific (`button.primary.background`)
- AI coding agents (via MCP) read tokens to output theme-consistent code without re-prompting.
- Full reference in `references/design-tokens-w3c-dtcg.md`.

## Internationalization

- Per-language slugs, localized SEO meta, localized navigation blocks.
- WCAG 3.0 clear language: explain idioms; provide unambiguous alternatives for non-native speakers.
- Multi-currency support at checkout for global products.

## AI-Era SEO / AEO

- **`llms.txt`** at site root — markdown summary for LLM crawlers. **Honesty caveat:** as of 2026, real-world LLM bot adoption of llms.txt is **mixed**; treat it as a low-cost signal, not a traffic driver. See `references/aeo-llms-txt.md` for the spec and adoption notes.
- **Answer-first content** (40–50 word answer in section opener) for AI overview citations.
- **Allow AI bots in robots.txt:** `GPTBot`, `PerplexityBot`, `Google-Extended`. Blocking them removes you from AI-driven search.
- **Rich schema markup:** Product, FAQ, HowTo, Article. JSON-LD at the appropriate scope.

## Conversion

- **Staged qualification.** Don't dump a 12-field form upfront. Ask for triage data first, deeper context after.
- **One-page checkout.** Forced account creation = 63% abandonment. Support guest checkout + Apple Pay / Google Pay.

## Microcopy

- **Active, benefit-driven.** "Syncing your data. Almost there!" — not "Processing data synchronization."
- **Supportive copy near opt-outs.** "You can change this at any time in settings." Reinforces autonomy, lifts opt-in rates.

## Error Handling

- **Inline real-time validation on blur.** Don't wait for submit.
- **Errors must be descriptive + actionable.** "Card expired — choose another or update this one" — not "Something went wrong."
- **Never color-alone.** Pair red error states with an icon + clear text. Color-blind users miss color-only signals.

## Loading States

- **Skeleton screens, not spinners.** Render placeholder layout matching final content within 100ms of fetch.
- **Skeletons must match exact dimensions** of loaded content — prevents CLS.
- **1-3-10 rule:** <1s no indicator; 1–3s spinner; 3s+ definite progress bar.

## Empty States

- **Educational, not voids.** Branded screen explaining what the feature does + a clear primary action to populate it.

## Onboarding

- **60-second rule.** First meaningful success within one minute.
- **Cap at 3–5 screens.** More = drop-off.
- **Progressive disclosure.** Reveal advanced features via contextual tooltips after the user masters basics.

## Social Proof & Trust

- **Strongest proof above the fold:** 4.5+ star aggregate, user count ("Trusted by 50,000+"), top client logos.
- **Testimonials must include:** real name, role, photo, specific outcome. Generic praise reads fake.

## Risk Reversal

- **Trust markers next to commitment points.** SSL/PCI badges adjacent to checkout button or lead form.
- **Explicit guarantees near CTAs:** "60-day refund, no questions" / "No credit card required" / "Cancel anytime in one click."

## Cross-skill references

- Hard floor for everything above: `web-design-must-do`.
- What NOT to do (with damage cited): `web-design-anti-patterns`.
- AI-era patterns deeper than AEO: `web-design-agentic-ux`.

## Source

NotebookLM "Web Design" (2026-04-29) + 2026 web research.

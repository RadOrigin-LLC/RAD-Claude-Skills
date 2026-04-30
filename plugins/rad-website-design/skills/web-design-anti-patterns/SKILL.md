---
name: web-design-anti-patterns
description: >
  Severity-tiered catalog of 17 web design anti-patterns with damage cited from real research —
  FTC fines, conversion drops, INP fail rates, % bounce. Use when the user asks "what's wrong with
  this", "is this a dark pattern?", "anti-patterns", "design review", "what mistakes am I making",
  "audit my page", "check for dark patterns", "why is my conversion bad", or any request to
  identify failures rather than design improvements. Two tiers: AVOID-AT-ALL-COSTS (catastrophic,
  often legal/ethical) and SHOULD-AVOID (common but recoverable).
allowed-tools: Read, Glob, Grep
---

# Web Design Anti-Patterns — Severity-Tiered

These are failure patterns to identify and fix. Each comes with the **specific damage** it causes (legal exposure, lost conversions, abandonment rates) sourced from research — not vibes.

When reviewing a site or codebase, scan for these in order. AVOID-AT-ALL-COSTS first; they often have legal or trust-destroying consequences.

---

## TIER 1 — AVOID AT ALL COSTS

### 1. Roach Motel (Labyrinthine Cancellation)

- **Pattern:** Frictionless signup, intentionally complex cancellation. Multi-step flows, "are you sure" loops, support-ticket-only cancellation.
- **Damage:** Permanently destroys lifetime value + brand trust. **FTC "parity principle" violation** — cancellation must be as easy as enrollment. **Amazon paid $2.5B settlement in 2025** for Prime cancellation friction.
- **Fix:** One-click cancellation in the same place enrollment occurred.

### 2. Sycophantic AI Assistants

- **Pattern:** Chatbots/agents programmed to flatter and agree to inflate satisfaction scores.
- **Damage:** Steers users toward risky decisions. Compromises accuracy. Users eventually detect the manipulation and lose trust permanently.
- **Fix:** Optimize AI for truthfulness and refusal. Surface uncertainty. Allow disagreement.

### 3. Technical Bloat / Main-Thread Bottlenecks

- **Pattern:** Heavy 3rd-party tracking pixels, marketing scripts, chat widgets all competing for the browser main thread.
- **Damage:** **43% of sites currently fail INP (Core Web Vital).** Failure tanks search visibility and increases bounce. Wastes marketing spend by degrading the conversion path it's trying to measure.
- **Fix:** Defer non-critical scripts (`async`/`defer`/`type="module"`). Audit 3rd-party impact via Lighthouse. Self-host where possible.

### 4. Confirm-Shaming & Hostile Interruptions

- **Pattern:** Pre-load aggressive pop-ups; guilt copy ("No thanks, I hate saving money"); newsletter modal before content renders.
- **Damage:** Triggers psychological reactance. **Users 90% less likely to return** after confirm-shaming exposure. Trades long-term loyalty for one-shot conversions.
- **Fix:** Delay opt-in prompts until exit-intent or scroll depth. Neutral microcopy ("No thanks").

### 5. Accessibility Sabotage

- **Pattern:** Disabling pinch-zoom (`user-scalable=no`), stripping focus rings (`outline: none` without `:focus-visible` replacement), light-gray-on-white text below 4.5:1.
- **Damage:** Excludes 1.3B disabled users globally. **Direct ADA lawsuit magnet** (US digital accessibility lawsuits hit record highs in 2025). Search algorithms penalize low-quality semantic code.
- **Fix:** Restore `:focus-visible` rings; remove `user-scalable=no`; verify contrast with axe-core or Stark. Validators in `scripts/`. Pair with `rad-a11y` for deeper coverage.

### 6. AI-Slop Copywriting

- **Pattern:** Unedited LLM-generated copy with telltale tics: "not only... but also," "Conclusion:" headers, em-dash overuse, confident hallucinations.
- **Damage:** Creates a "semantic void" — destroys brand authority. Users in 2026 detect synthetic content immediately and bounce.
- **Fix:** Edit aggressively. Lead with specifics: real numbers, named people, dated events. Pair with `rad-writer` for AI-pattern detection.

### 7. Hidden Desktop Hamburger Menu

- **Pattern:** Primary navigation links hidden inside a hamburger icon on desktop screens; or core pages buried 4–5 layers deep.
- **Damage:** Information scent failure — users assume the path doesn't exist. **Discoverability drops 20%+; feature adoption tanks.**
- **Fix:** Show top-level navigation visibly on desktop ≥1024px. Reserve hamburger for mobile.

### 8. Broken Search Basics

- **Pattern:** Search query resets when filters apply or page reloads. No typo tolerance ("furnture" returns zero results).
- **Damage:** Users falsely conclude the product/content doesn't exist and leave entirely.
- **Fix:** Persist query in URL params. Add fuzzy match / autocomplete. Show "did you mean" suggestions.

---

## TIER 2 — SHOULD-AVOID

### 9. Pixel Font Sizing & Font Clutter

- **Issue:** Absolute `px` font sizes; mixing too many novelty/decorative fonts.
- **Damage:** `px` disables browser font-size controls (excludes 40+ users); font chaos kills brand credibility.
- **Fix:** Use `rem` + `clamp()`. Cap at 2 font families — one display, one body.

### 10. Low Contrast & Inconsistent Palette

- **Issue:** Gray text on white below 4.5:1; random color choices outside a system.
- **Damage:** WCAG fail; users can't tell what's interactive.
- **Fix:** Token-driven semantic colors. Verify with axe / Stark. APCA for future-proofing — see `references/color-contrast-apca.md`.

### 11. Feature Overload + Competing CTAs

- **Issue:** Multiple primary CTAs on one screen; cluttered choice set.
- **Damage:** Hick's Law — **24 product options vs filtered 6 collapsed conversion from 30% to 3%.**
- **Fix:** One primary CTA per view. Filter aggressively. Progressive disclosure for secondary actions.

### 12. Scroll-Jacking & Decorative Animation

- **Issue:** Forcing scroll speed to match parallax; animations with no feedback purpose.
- **Damage:** Triggers vestibular sensitivities (dizziness/nausea). Frustrates users who lose scroll control. Tanks page speed.
- **Fix:** Respect natural scroll. Cap animation to functional feedback. `prefers-reduced-motion: reduce` always honored.

### 13. Desktop-First Scaling on Mobile

- **Issue:** Designing for large monitors and shrinking; sub-44px tap targets.
- **Damage:** Fat-finger errors. **Mobile users are 5× more likely to abandon a task** on awkward mobile UX.
- **Fix:** Mobile-first CSS. 44×44px minimum (56–60px for primary CTAs). Validator: `scripts/check-tap-targets.py`.

### 14. Field Overload + Delayed Validation

- **Issue:** Asking for fax numbers, redundant confirmations; errors only on submit.
- **Damage:** **Every extra required field costs 2–4% form completion.** No inline validation = anxiety + abandonment.
- **Fix:** Cut fields to essentials. Real-time inline validation on blur.

### 15. Jargon & Vague Microcopy

- **Issue:** "Pioneering Tomorrow" instead of "Start Free Trial." Corporate buzzwords. Cute button labels that hide function.
- **Damage:** Unclear instructions cause **up to 50% of user errors.** 8-second attention window doesn't forgive ambiguity.
- **Fix:** Plain verbs. Action-oriented buttons. State the benefit, not the brand.

### 16. Heavy Assets & Technical Bloat (Tier 2 — content-side)

- **Issue:** Uncompressed images, autoplay background video, dozens of tracking scripts.
- **Damage:** **1s → 5s load time = 90% increase in bounce probability.**
- **Fix:** WebP/AVIF; `<img loading="lazy">`; preload only the hero. Audit 3rd-party scripts.

### 17. Synthetic AI-Slop Aesthetics

- **Issue:** Glassmorphism without purpose; generic purple-to-blue gradients; Inter on white.
- **Damage:** Brand reads as synthetic and untrustworthy. Blends into thousands of LLM-generated templates.
- **Fix:** Commit to a specific aesthetic direction (see `web-design-aesthetic`). Distinctive typography + purposeful color.

---

## How to use this in a review

1. Start with Tier 1 (catastrophic) — these have legal/ethical/conversion-destroying impact.
2. Move to Tier 2 — common quality issues.
3. Tag findings:
   - `[STATIC]` — regex/AST detected (high confidence)
   - `[HEURISTIC]` — pattern likely but needs human verification
   - `[NEEDS-MANUAL]` — requires human read (e.g., AI-slop copy, sycophancy detection)
4. Never issue a Pass/Fail verdict — static analysis can't defensibly produce one.

For automated review (report only), use the `web-design-review` skill or the `web-design-reviewer` agent. For review + concrete fix proposals, use `web-design-improve`.

## Source

NotebookLM "Web Design - Anti-Design" (2026-04-29) + 2026 web research. Full damage citations in `references/anti-patterns-catalog.md`.

# Anti-Patterns Catalog — 2026 with Damage Cited

This is the **damage-cited** anti-pattern catalog. Every entry includes (a) what the anti-pattern looks like, (b) why it's bad in concrete terms (citations from research, regulatory action, conversion data), and (c) how to fix it.

Tagged for severity:
- **TIER 1 — AVOID-AT-ALL-COSTS:** Catastrophic. Often legal/ethical exposure or conversion-destroying.
- **TIER 2 — SHOULD-AVOID:** Common quality issues; recoverable with effort.

---

## TIER 1 — AVOID-AT-ALL-COSTS

### 1. Roach Motel (Labyrinthine Cancellation)

**Pattern:** Frictionless signup, intentionally complex cancellation. Multi-step "are you sure?" loops. Support-ticket-only cancellation. Hidden cancel buttons.

**Damage:**
- Permanently destroys lifetime value + brand trust.
- **FTC "parity principle"** requires cancellation be as easy as enrollment.
- **Amazon paid $2.5B settlement (2025)** for Prime cancellation friction.
- EU Digital Fairness Act (2026) extends similar requirements across the EU.

**Fix:** One-click cancellation in the same place enrollment occurred. No retention pop-ups required to complete cancel.

---

### 2. Sycophantic AI Assistants

**Pattern:** Chatbots and agents programmed to flatter and agree with the user — to inflate satisfaction scores, increase engagement, reduce challenges.

**Damage:**
- Steers users toward risky decisions (financial, medical, legal).
- Compromises accuracy and transparency.
- Users in 2026 detect this pattern; brand is viewed as manipulative.
- Erodes the trust foundation that makes agentic UX possible at all.

**Fix:** Optimize for truthfulness. Surface uncertainty. Allow disagreement: "I think this won't work because X. Want me to try anyway?"

---

### 3. Technical Bloat / Main-Thread Bottlenecks

**Pattern:** Heavy 3rd-party tracking pixels, marketing scripts, chat widgets — all competing for the browser main thread.

**Damage:**
- **43% of sites currently fail INP** (Core Web Vital, 2026).
- Failure tanks search visibility (Google ranks INP).
- Higher bounce rates waste the marketing spend the trackers were trying to measure.

**Fix:** Defer non-critical scripts (`async`/`defer`/`type="module"`). Audit 3rd-party impact via Lighthouse. Self-host where possible. Set a script budget and enforce it.

---

### 4. Confirm-Shaming & Hostile Interruptions

**Pattern:** Pre-load aggressive pop-ups before page renders. Guilt copy: "No thanks, I hate saving money" / "I'd rather bleed to death." Newsletter modal blocking the content.

**Damage:**
- Triggers psychological reactance.
- **Users 90% less likely to return** after confirm-shaming exposure (research cited in 2026 anti-design literature).
- Trades long-term loyalty for one-shot conversions.

**Fix:** Delay opt-in prompts until exit-intent or scroll depth. Use neutral microcopy ("No thanks").

---

### 5. Accessibility Sabotage

**Pattern:** Disabling pinch-zoom (`user-scalable=no`), stripping focus rings (`outline: none` without `:focus-visible` replacement), light-gray-on-white text below 4.5:1 contrast.

**Damage:**
- Excludes 1.3B disabled users globally.
- **Direct ADA lawsuit magnet.** US digital accessibility lawsuits hit record highs in 2025.
- Search algorithms penalize semantically weak code.

**Fix:** Restore `:focus-visible`. Remove `user-scalable=no`. Verify contrast with axe-core / Stark. Run `scripts/check-viewport-meta.py` and `scripts/check-pure-bw.py`. Pair with `rad-a11y` for deeper coverage.

---

### 6. AI-Slop Copywriting

**Pattern:** Unedited LLM-generated copy with telltale tics: "not only... but also," "Conclusion:" headers, excessive em-dashes, confident hallucinations, formulaic 3-paragraph structure.

**Damage:**
- Creates a "semantic void" — destroys brand authority.
- Users in 2026 are highly sensitive to synthetic content; immediate bounce when detected.
- Strongest negative signal for engagement metrics in 2026.

**Fix:** Edit aggressively. Lead with specifics: real numbers, named people, dated events. Use `rad-writer:ai-audit` to detect patterns programmatically.

---

### 7. Hidden Desktop Hamburger Menu

**Pattern:** Primary navigation links hidden inside a hamburger icon on desktop screens. Core pages buried 4–5 layers deep in nested settings panels.

**Damage:**
- Information scent failure — if users don't see a clear path, they assume it doesn't exist.
- **Discoverability drops 20%+ on desktop** when primary nav is hidden.
- Feature adoption tanks; users abandon before discovering the product's value.

**Fix:** Show top-level navigation visibly on desktop ≥1024px. Reserve hamburger for mobile. Limit nav nesting to 3 layers max.

---

### 8. Broken Search Basics

**Pattern:** Search query resets when filters apply or page reloads. No typo tolerance ("furnture" returns zero results). No autocomplete, no "did you mean" suggestions.

**Damage:**
- Users falsely conclude the product/content doesn't exist.
- Site abandonment in seconds.
- "Inexcusable failure in the AI era" per 2026 anti-design research — users now expect at minimum the search quality of a basic LLM.

**Fix:** Persist query in URL params. Add fuzzy match / autocomplete. Show "did you mean" suggestions.

---

## TIER 2 — SHOULD-AVOID

### 9. Pixel Font Sizing & Font Clutter

**Issue:** Absolute `px` font sizes; mixing too many novelty/decorative fonts.

**Damage:** `px` disables the browser's user font-size control (excludes 40+ users); font chaos kills brand credibility.

**Fix:** Use `rem` + `clamp()`. Cap at 2 font families (one display, one body).

---

### 10. Low Contrast & Inconsistent Palette

**Issue:** Gray text on white below 4.5:1; random color choices outside a token system.

**Damage:** WCAG fail; users can't tell what's interactive.

**Fix:** Token-driven semantic colors. Verify with axe / Stark. APCA targets for forward-readiness — see `color-contrast-apca.md`.

---

### 11. Feature Overload + Competing CTAs

**Issue:** Multiple competing primary CTAs on one screen; cluttered choice set.

**Damage:** Hick's Law — **24 product options vs filtered 6 collapsed conversion from 30% to 3%** (Iyengar/Lepper jam study, frequently cited in 2026 conversion research).

**Fix:** One primary CTA per view. Filter aggressively. Progressive disclosure for secondary actions.

---

### 12. Scroll-Jacking & Decorative Animation

**Issue:** Forcing scroll speed to match parallax animations; animations with no feedback purpose.

**Damage:** Triggers vestibular sensitivities (dizziness/nausea). Frustrates users who lose scroll control. Tanks page speed.

**Fix:** Respect natural scroll. Cap animation to functional feedback. Always honor `prefers-reduced-motion: reduce`.

---

### 13. Desktop-First Scaling on Mobile

**Issue:** Designing for large monitors and shrinking; sub-44px tap targets.

**Damage:** Fat-finger errors. **Mobile users are 5× more likely to abandon a task** on awkward mobile UX.

**Fix:** Mobile-first CSS. 44×44px minimum tap targets (56–60px for primary CTAs). Run `scripts/check-tap-targets.py`.

---

### 14. Field Overload + Delayed Validation

**Issue:** Asking for fax numbers, redundant confirmations; errors only on submit.

**Damage:** **Every extra required field costs 2–4% form completion.** No inline validation = anxiety + abandonment at checkout.

**Fix:** Cut fields to essentials. Real-time inline validation on blur with descriptive, actionable error messages.

---

### 15. Jargon & Vague Microcopy

**Issue:** "Pioneering Tomorrow" instead of "Start Free Trial." Corporate buzzwords. Cute button labels that hide function.

**Damage:** Unclear instructions cause **up to 50% of user errors**. 8-second attention window doesn't forgive ambiguity.

**Fix:** Plain verbs. Action-oriented buttons. State the benefit, not the brand poetry.

---

### 16. Heavy Assets & Technical Bloat (content-side)

**Issue:** Uncompressed images, autoplay background video, dozens of tracking scripts.

**Damage:** **1s → 5s load time = 90% increase in bounce probability** (Google research, frequently cited).

**Fix:** WebP/AVIF. `<img loading="lazy">`. Preload only the hero. Audit 3rd-party scripts ruthlessly.

---

### 17. Synthetic AI-Slop Aesthetics

**Issue:** Glassmorphism without purpose; generic purple-to-blue gradients; Inter on white.

**Damage:** Brand reads as synthetic and untrustworthy. Blends into thousands of LLM-generated templates.

**Fix:** Commit to a specific aesthetic direction (see `web-design-aesthetic`). Distinctive typography + purposeful color. Avoid the 2024–2025 default stack.

---

## Source attribution

- FTC Amazon settlement: $2.5B (2025) — public news; multiple coverage
- INP 43% fail rate: Web Almanac 2025–2026 reports
- Confirm-shaming 90% no-return: 2026 anti-design literature
- 24 vs 6 options jam study: Iyengar & Lepper (2000), referenced in 2026 conversion design literature
- 1s→5s load 90% bounce: Google research, Think with Google
- 50% user errors from unclear instructions: usability research, multiple sources
- Mobile 5× abandonment: 2026 anti-design notebook research
- llms.txt mixed adoption: aeoengine.ai 2026 critique

NotebookLM source notebooks: "Web Design" (`c72c728c`) + "Web Design - Anti-Design" (`8a2bd3a1`), queried 2026-04-29.

---
name: web-design-aesthetic
description: >
  Pick a 2026 aesthetic direction. Use when the user asks "what aesthetic should I use",
  "design direction", "Calm UX", "Liquid Glass", "Wabi Sabi", "Maximalism", "should I use
  glassmorphism", "what visual style for my SaaS/portfolio/store", "is this aesthetic right for
  my industry", or any question about choosing or defending an aesthetic vocabulary. Default
  recommendation is Calm UX with documented overrides for high-energy / artisan / spatial / brand
  contexts. Includes when-NOT-to-use guidance for each direction.
allowed-tools: Read, Glob, Grep
---

# Aesthetic Direction — Default + Overrides

The 2026 default for utility-driven products is **Calm UX**. Override deliberately, with reason.

This is not a free-for-all aesthetic buffet. Each direction has explicit "USE" and "DO NOT USE" contexts. Picking the wrong direction for the industry is one of the top reasons brands feel synthetic or distrustful.

## Default: Calm UX

**What it is:** Strategic minimalism. Whitespace as architecture. Single primary objective per view. Progressive disclosure of advanced settings. Batched notifications. "Quiet modes" — no red dots, no anxiety-inducing badges.

**USE for:**
- B2B SaaS dashboards
- Productivity / focus apps
- Healthcare and clinical platforms
- Financial tools (investing, banking, tax)
- Reading / long-form content
- Internal tools / admin panels

**Why it's the default:** Users in these contexts spend long periods in the product. Cognitive load is the enemy. Calm UX measurably reduces user fatigue and supports focus.

**Anchor patterns:**
- Generous whitespace; one primary CTA per view
- Muted, low-saturation palette with one accent
- Subdued motion (≤200ms, ease-out)
- Typography weight as primary hierarchy (avoid color-coded importance)
- Notifications batched, never pulsing

---

## Override 1: High-Energy / Dopamine Engagement

**USE for:** youth-culture brands, gaming, entertainment, music, social, shopping, Gen Z lifestyle.

**DO NOT USE for:** legal, medical, financial, enterprise, B2B, government — Calm UX is mandatory there.

**Patterns:**
- Saturated palette; multiple accent colors
- Higher motion budget (still respecting `prefers-reduced-motion`)
- Larger type, expressive display fonts
- Live counters, real-time activity feeds (when authentic)
- Bento grid with strong asymmetric weight

---

## Override 2: Liquid Glass / Spatial UI

**What it is:** High-fidelity translucency, 1px inner refraction borders, organic depth. Inspired by spatial computing (visionOS, Material 3 Expressive).

**USE for:** premium SaaS dashboards (visually separate active workspace from background data), fintech, spatial/AR interfaces, where depth communicates layer hierarchy.

**DO NOT USE when:**
- It compromises WCAG 3.0 APCA contrast (translucent text often fails)
- Lower-end devices (heavy backdrop-blur tanks frame rates)
- Users on `prefers-reduced-transparency` (always provide a solid fallback)

**Patterns:**
- `backdrop-filter: blur(20px) saturate(180%)`
- 1px inset border with subtle gradient
- Layer the UI in 2–3 z-planes max — more = visual chaos
- Always a solid-color fallback for a11y / performance

---

## Override 3: Maximalism / Wabi Sabi (Anti-Design)

**What it is:** Intentional human imperfection. Hand-drawn elements, asymmetric grids, chaotic vibrancy, off-baseline alignment. A rebellion against AI-generated sameness.

**USE for:** artisan brands, fashion, lifestyle, editorial, music, Gen Z, creative portfolios, personal sites.

**DO NOT USE for:** corporate enterprise, legal, medical, financial, healthcare. Authority and clarity are paramount in those industries; chaos reads as carelessness.

**Patterns:**
- Mixed typography (display + raw mono + handwritten)
- Off-grid composition with intentional misalignment
- Saturated, sometimes clashing palette
- Hand-drawn / scanned textures
- "Imperfect" details: rotation, asymmetric padding, broken rhythm

**Honesty note:** This direction is high-skill. Done badly, it reads as broken. Don't pick it because it looks easy.

---

## Override 4: Refined Minimalism (NOT Calm UX)

**Difference from Calm UX:** Calm UX prioritizes function and reduces stimulation. Refined Minimalism prioritizes craft and uses restraint as the brand statement.

**USE for:** luxury brands, high-end product, agencies, individual creators with strong portfolios.

**DO NOT USE for:** information-dense applications. Refined minimalism hides utility under aesthetic restraint — wrong for tools.

**Patterns:**
- Exceptional typography is the centerpiece (variable fonts; precise spacing)
- Muted palette but with one striking accent or texture
- Generous whitespace, not for cognitive ease but for visual gravitas
- Subtle, slow motion
- Detail obsession (kerning, grid alignment, micro-interactions)

---

## How to pick

1. **Identify the user's context:** B2B utility, consumer entertainment, e-commerce, brand portfolio, personal site.
2. **Default to Calm UX.** Only override when industry/audience explicitly demands it.
3. **Document the choice in code** (`/* Aesthetic: Liquid Glass; chosen because: spatial layering of dashboard widgets */`).
4. **Verify against anti-patterns:** translucency that fails APCA, motion that ignores `prefers-reduced-motion`, generic gradient that reads as AI-slop.

## What this skill is NOT

- Not a brand strategy framework. Aesthetic ≠ brand. For brand-vs-product mode separation, the **Impeccable** plugin is excellent.
- Not a design generator. Picking the direction is half the work; execution requires craft.
- Not a guarantee. The "USE for" / "DO NOT USE" lists are defaults, not laws. Override with reason.

## References

- `references/aesthetic-directions.md` — full pattern catalog with code examples
- `references/color-contrast-apca.md` — APCA constraints for translucency

## Source

NotebookLM "Web Design" (2026-04-29) + 2026 web research.

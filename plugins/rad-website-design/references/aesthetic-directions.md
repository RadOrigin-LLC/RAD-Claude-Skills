# Aesthetic Directions — 2026 Reference

The 2026 default for utility-driven products is **Calm UX**. Override deliberately, with reason.

## Calm UX (default)

**Use for:** B2B SaaS dashboards, productivity apps, healthcare, financial tools, reading, internal admin.

**Anchors:**
- Generous whitespace; one primary CTA per view
- Muted, low-saturation palette + one accent
- Typography weight as primary hierarchy (not color)
- Subdued motion (≤200ms ease-out)
- Batched notifications, no pulsing red dots
- Progressive disclosure of advanced settings

**Code shape:**
```css
:root {
  --color-surface: oklch(99% 0.005 270);
  --color-text: oklch(20% 0 0);
  --color-text-muted: oklch(50% 0 0);
  --color-accent: oklch(60% 0.18 270);
  --space-section: 4rem;
  --motion-duration: 200ms;
  --motion-easing: cubic-bezier(0.4, 0, 0.2, 1);
}
```

## High-Energy / Dopamine

**Use for:** youth-culture brands, gaming, entertainment, music, social, lifestyle.
**DO NOT use for:** legal, medical, financial, enterprise, B2B utility.

**Anchors:**
- Saturated palette, multiple accents
- Higher motion budget (still respect `prefers-reduced-motion`)
- Larger expressive display fonts
- Real-time activity feeds where authentic
- Asymmetric bento with strong weight contrast

## Liquid Glass / Spatial UI

**Use for:** premium SaaS dashboards, fintech, AR/spatial interfaces — where depth communicates layer hierarchy.
**DO NOT use when:** translucency compromises APCA contrast, lower-end devices choke on backdrop-blur, or `prefers-reduced-transparency` requires solid fallback.

**Anchors:**
- `backdrop-filter: blur(20px) saturate(180%)`
- 1px inset border with subtle gradient (refraction effect)
- 2–3 z-planes max
- Always solid-color fallback

```css
.surface-glass {
  background: oklch(95% 0.005 270 / 0.6);
  backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid oklch(100% 0 0 / 0.15);
  box-shadow: inset 0 1px 0 oklch(100% 0 0 / 0.5);
}

@media (prefers-reduced-transparency: reduce) {
  .surface-glass {
    background: oklch(98% 0.005 270);
    backdrop-filter: none;
  }
}
```

## Maximalism / Wabi Sabi (Anti-Design)

**Use for:** artisan brands, fashion, lifestyle, editorial, music, Gen Z, creative portfolios.
**DO NOT use for:** corporate enterprise, legal, medical, financial, healthcare.

**Anchors:**
- Mixed typography (display + raw mono + handwritten)
- Off-grid composition with intentional misalignment
- Clashing or saturated palette
- Hand-drawn / scanned textures
- Imperfect details — rotation, asymmetric padding, broken rhythm

**Honesty:** This direction is high-skill. Done badly, it reads as broken. Don't pick because it looks easy.

## Refined Minimalism (NOT the same as Calm UX)

**Difference:** Calm UX prioritizes function. Refined Minimalism prioritizes craft — restraint as the brand statement.

**Use for:** luxury brands, high-end products, agencies, individual creators with strong portfolios.
**DO NOT use for:** information-dense applications.

**Anchors:**
- Exceptional typography is the centerpiece
- Muted palette + one striking accent or texture
- Generous whitespace for visual gravitas
- Subtle, slow motion
- Detail obsession (kerning, grid alignment, micro-interactions)

## Brutalism (rare and risky)

**Use for:** anti-corporate brands, art, music, indie. Almost never for products users need to use.
**DO NOT use for:** anything sold to a large general audience.

**Anchors:**
- Raw HTML aesthetic — sometimes literally undesigned
- System fonts, unstyled buttons
- High-contrast, sometimes disorienting layouts
- No micro-interactions

## Cyber / Retro-Futuristic

**Use for:** tech-themed brands, AR/VR products, sci-fi storytelling, gaming.
**DO NOT use for:** general-audience SaaS — alienates non-tech users.

**Anchors:**
- Neon accents on dark base
- Mono font + variable type as expressive layer
- Glitch effects (sparingly)
- HUD-inspired UI elements (use functional, not decorative)

## Aesthetic decision matrix (rough)

| Industry | Default | Acceptable overrides |
|---|---|---|
| B2B SaaS / utility | Calm UX | Liquid Glass for premium |
| Consumer SaaS | Calm UX | High-Energy for entertainment focus |
| E-commerce | Calm UX | Refined Minimalism for luxury |
| Fashion / lifestyle | Maximalism / Wabi Sabi | Refined Minimalism for luxury |
| Healthcare / legal / financial | Calm UX | (none) |
| Education / nonprofit | Calm UX | Refined Minimalism |
| Gaming / entertainment | High-Energy | Cyber |
| Agencies / portfolios | Refined Minimalism | Maximalism |
| Personal sites | Anything | (your call) |

## Anti-patterns (cross-ref)

- AI-slop aesthetic stack (Inter + purple gradient + glassmorphism) → SHOULD-AVOID #17
- Wrong-direction-for-industry (Maximalism on a legal site) → trust killer

## Sources

NotebookLM "Web Design" (2026) + 2026 web research on aesthetic trends + Calm UX literature (Calm Tech, Bagaar).

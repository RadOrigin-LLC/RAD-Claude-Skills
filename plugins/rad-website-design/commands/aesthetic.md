---
description: Pick a 2026 aesthetic direction. Calm UX default + documented overrides for high-energy / Liquid Glass / Wabi Sabi / Refined Minimalism.
argument-hint: "[product type, industry, audience]"
allowed-tools: Read, Skill
---

The user wants help picking an aesthetic direction. Context: `$ARGUMENTS`.

Load the `web-design-aesthetic` skill via the Skill tool.

Then walk the user through the decision:

1. **Identify their context.** Ask 1–2 clarifying questions if `$ARGUMENTS` is vague:
   - Industry (B2B / consumer / e-commerce / portfolio / personal)
   - Audience (general utility user / Gen Z / luxury buyer / artisan customer / enterprise)
   - Function (utility tool / brand site / content destination)

2. **Recommend a direction** based on the skill's USE/DO-NOT-USE matrix:
   - Default to Calm UX
   - Override only when industry/audience explicitly demands

3. **Surface the rule the recommendation depends on** — quote the "USE for" / "DO NOT USE for" lines from the skill.

4. **Show 3–5 anchor patterns** for the recommended direction (typography, color treatment, motion budget, key visual moves).

5. **Note the trade-offs** explicitly — if they pick Liquid Glass, surface APCA contrast risk and `prefers-reduced-transparency`. If they pick Maximalism, note it's high-skill execution territory.

Be direct. Don't hedge with "it depends" — the skill provides specific defaults. If their context is genuinely ambiguous, pick the safer option (Calm UX or Refined Minimalism) and explain why.

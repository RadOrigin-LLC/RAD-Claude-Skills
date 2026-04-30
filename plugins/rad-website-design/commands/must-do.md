---
description: Surface the 2026 must-do design baseline for a feature, page, or component the user describes.
argument-hint: "[feature/page description]"
allowed-tools: Read, Skill
---

The user is asking for the 2026 must-do design baseline for: `$ARGUMENTS` (or, if empty, "general web page").

Load the `web-design-must-do` skill via the Skill tool. Use its content to produce a tailored checklist for the user's specific feature/page.

Tailor the checklist:
- If `$ARGUMENTS` mentions "landing page" → emphasize hero, above-fold trust signals, CTA, performance
- If `$ARGUMENTS` mentions "form" or "checkout" → emphasize tap targets, inline validation, semantic forms, microcopy
- If `$ARGUMENTS` mentions "dashboard" or "SaaS" → emphasize Calm UX defaults, Cmd+K, semantic color, density
- If `$ARGUMENTS` mentions "mobile" → emphasize thumb zone, 44×44 targets, mobile bottom tabs
- Otherwise → present the full baseline

Format as a categorized checklist (Typography / Color / Layout / A11y / Performance / Mobile / etc.) with concrete numbers where the skill provides them.

Do not pad. Do not invent rules not in the skill content. If something is `[NEEDS-MANUAL]` — say so.

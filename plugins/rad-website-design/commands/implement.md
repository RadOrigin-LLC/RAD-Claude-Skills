---
description: Implement a new web design from a vision. Ensures Claude's output meets 2026 standards (must-do baseline, chosen aesthetic, semantic tokens, a11y, perf).
argument-hint: "[brief description of what to build]"
allowed-tools: Read, Write, Edit, Glob, Grep, Skill
---

The user wants to implement a new web design: `$ARGUMENTS`.

Load the `web-design-implement` skill via the Skill tool. It contains the execution discipline for translating a vision into 2026-standard code.

**Workflow:**

1. **Capture the vision** — if `$ARGUMENTS` is detailed (type, audience, brand, stack), use it as-is. If it's terse, ask 1–2 quick questions to fill gaps. Do not workshop — the user is here to build, not plan.

2. **Confirm aesthetic direction** — if not specified, default to **Calm UX** for utility products and ask the user to confirm or override (Liquid Glass / Maximalism / Refined Minimalism / High-Energy).

3. **Generate code that meets 2026 standards:**
   - Token layer first (CSS variables / Tailwind config / token JSON)
   - Semantic HTML structure (header, main, sequential headings)
   - Mobile-first responsive (≤768px collapse, ≥768px expand)
   - All must-do baselines (viewport meta correct, focus-visible rings, dvh, 44px tap targets, prefers-reduced-motion, WCAG AA contrast)
   - Avoid AI-slop defaults (Inter+purple gradient stack)
   - Reference the `web-design-aesthetic` skill for the chosen direction's anchors

4. **Output structure:**
   - Brief recap of what's being built (3–5 lines)
   - Token layer
   - HTML/JSX structure
   - Component CSS / Tailwind classes
   - Honest scope note ("starter scaffold; you'll need to wire data, finalize copy, etc.")

If the user asks for something this skill can't do (full production code, brand strategy, image generation), say so explicitly and recommend the right plugin (rad-brainstormer, rad-writer, etc.).

For upstream brainstorming and planning, recommend `rad-brainstormer` and `rad-planner`.
For post-implementation review, recommend `/rad-website-design:review` or `/rad-website-design:improve`.

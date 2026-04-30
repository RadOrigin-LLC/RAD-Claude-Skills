---
name: web-design-agentic-ux
description: >
  2026 AI-native and agentic UX patterns. Use when the user asks about "agentic UX",
  "AI agent UI", "Cmd+K palette", "Intent Preview", "Autonomy Dial", "Action Audit",
  "AI takes action on my behalf", "how do I design for an AI agent", "ChatGPT-style UI",
  "agent confirmation patterns", or any question about UX where an AI takes multi-step
  autonomous action for a user. Covers the three core trust patterns: Intent Preview, Autonomy
  Dial, Action Audit & Undo. Includes when to require human confirmation (irreversible actions).
allowed-tools: Read, Glob, Grep
---

# Agentic UX — 2026 AI-Native Patterns

In 2026, AI is no longer a chatbot widget bolted to the corner of the screen. It is **invisible infrastructure** that takes multi-step actions on the user's behalf. This requires entirely new UX vocabulary.

The three core patterns below are the floor for any agentic interface. They exist because users will not trust an AI that acts opaquely or irreversibly.

## The Three Core Patterns

### 1. Intent Preview

**Pattern:** Before the agent acts, summarize what it will do — in plain language, with the specific objects and parameters.

**Example:**
> "I'll send this email to alice@example.com with the subject 'Q3 review' and attach Q3-summary.pdf. Send it?"

**Why:** Closes the gap between user intent and AI interpretation. Catches misunderstandings before they cost time, money, or trust.

**Implementation:**
- Show the action's verb, object(s), and any parameters that matter (recipient, file, dollar amount, duration)
- Use the user's own words where possible — echo phrasing back so they can verify intent was understood
- Make confirmation a deliberate act (button click, not Enter-key autofire)
- Surface anything the agent inferred (defaults, assumptions, retrieved data)

### 2. Autonomy Dial

**Pattern:** Let the user set how independently the agent operates.

**Levels (typical):**
- **Suggest** — Agent proposes; user clicks to act.
- **Confirm** — Agent prepares actions; user confirms each.
- **Notify** — Agent acts; user gets notified after.
- **Auto** — Agent acts silently within explicit boundaries.

**Why:** Different tasks tolerate different risk. The user — not the designer — should set the dial per task or task class.

**Implementation:**
- Persistent UI control (settings panel + per-task override)
- Default to `Confirm` for new users; never default to `Auto` for first-run
- Per-action-type granularity ideal (auto for low-stakes, confirm for high-stakes)
- Always show the current dial position in the surface where the agent acts

### 3. Action Audit & Undo

**Pattern:** Persistent, scrollable log of what the agent did — with one-click reversal where possible.

**Why:** Every autonomous action must be reviewable and (ideally) reversible. This is the safety net that lets users grant higher autonomy.

**Implementation:**
- Activity feed with timestamps, action verbs, affected objects, source (user vs agent)
- "Undo" button on each entry where reversal is feasible
- For irreversible actions: explicit human confirmation BEFORE the action — no audit-only post hoc
- Filter by agent vs user; filter by date; export for compliance contexts

## When NOT to Use Full Autonomy

Even with all three patterns above, certain actions **must require human confirmation regardless of dial setting:**

- **Irreversible financial transactions** — purchases, transfers, refunds, subscription changes with billing impact
- **Data deletion** — accounts, messages, files, history
- **High-stakes domains** — medical advice, legal advice, contractual signing
- **Identity actions** — auth changes, password resets, role assignments
- **Cross-account actions** — sharing, granting access, posting on behalf of the user externally

For these, the dial is informative, not authoritative. Hard-code the confirmation gate.

## Cmd+K Command Palette

For any web app with **>10 features**, implement a Cmd+K (or Ctrl+K) command palette:

- Indexes all actions, settings, and resources by keyword
- Fuzzy search; supports natural language ("find invoices over $500")
- Each result shows the action verb + the keyboard shortcut
- AI integration: surface agent suggestions inline ("Generate report from last week's data")

Cmd+K bypasses nested menus entirely. It is the single highest-ROI navigation pattern for agentic UX in 2026.

## Anti-Patterns (cross-reference `web-design-anti-patterns`)

- **Sycophantic AI assistants** — programmed to flatter and agree to inflate satisfaction. Steers users to risky decisions; brand reads as manipulative.
- **Auto-fired actions without preview** — agent takes action before the user can verify the interpretation.
- **Hidden audit trails** — actions happen but the user can't see what the agent did or why.
- **Irreversible defaults** — destructive operations as the default mode.

## Multimodal Note

Voice-only AI interfaces are largely obsolete in 2026. The standard is **multimodal** — voice + touch + visual handoff. The UX challenge is the **handoff:** knowing when the system should listen, display, or wait. Default to visual; promote to voice only when:
- User is hands-busy (driving, cooking, AR/VR)
- User is accessibility-impaired in a way voice better serves
- Public-space privacy is not a constraint

## References

- `references/agentic-ux-patterns.md` — full pattern catalog with code sketches
- `references/anti-patterns-catalog.md` — sycophantic AI section

## Source

NotebookLM "Web Design" (2026-04-29) + 2026 web research.

---
description: Identify design issues on an existing site (source path or live URL) and propose specific changes with diffs.
argument-hint: "[source path or live URL]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, Skill, Agent
---

The user wants to improve an existing design at: `$ARGUMENTS`.

Load the `web-design-improve` skill via the Skill tool. It performs issue identification + concrete change proposals over either source paths or live URLs.

**Determine input shape:**

- Path-shaped (`./src`, `index.html`, repo dir) → **source mode**: invoke the `web-design-reviewer` agent for static analysis, then propose fixes for each finding
- URL-shaped (`https://...`) → **URL mode**: WebFetch the rendered HTML and analyze; surface JS-SPA limitations honestly
- Both — run both and merge findings

**Workflow:**

1. Run the analysis (source via reviewer agent, URL via WebFetch)
2. For each finding, output a change proposal with: severity tier, confidence tag, location, what's wrong, damage citation, proposed diff/replacement, effort estimate
3. Group by impact × effort: Quick wins → Big fixes → Polish → NEEDS-MANUAL follow-ups
4. For source mode: offer to apply changes via Edit (ask first; never apply unilaterally)
5. For URL mode: output diffs the user can apply manually

**Honesty rules:**

- Never claim "WCAG compliant" or "production-ready" after applying changes
- Tag every proposal with detection confidence
- Surface tradeoffs explicitly when a fix involves judgment
- Do not expand scope — list out-of-scope issues in NEEDS-MANUAL, don't propose fixes for them

**Pair recommendations:**

- Runtime perf and screenshots → `chrome-devtools-mcp` plugin
- Accessibility depth → `rad-a11y` plugin
- AI-slop copy detection → human read
- SEO depth → `rad-seo-optimizer`

If `$ARGUMENTS` is empty, ask once for the path or URL. Do not guess.

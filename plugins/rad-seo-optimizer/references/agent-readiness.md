# Agent Readiness — Lighthouse Agentic Browsing checks

A third pillar alongside SEO (rank in search) and AEO (get cited in AI answers):
**agent readiness** — can an AI agent operating a browser on a user's behalf
(Gemini-in-Chrome, ChatGPT agents, computer-use models) understand and drive your site?

Chrome's Lighthouse ships an experimental **Agentic Browsing** category
(developer.chrome.com/docs/lighthouse/agentic-browsing, May 2026). It reports a
pass-ratio, not a 0-100 score, and is based on proposed standards — frame all findings
as forward-looking, not ranking factors.

## The six Lighthouse agentic-browsing audits

| Audit | What it checks | Static checkability |
|---|---|---|
| Registered WebMCP tools | WebMCP tools declared and discoverable | Grep for WebMCP registration in source |
| Forms missing declarative WebMCP | Interactive forms not exposed via WebMCP schema | Compare `<form>` elements vs WebMCP declarations |
| WebMCP schema validity | Declarations meet the proposed spec | Parse + validate declarations |
| llms.txt | Machine-readable site summary at root | `audit-ai-access.py` (existence + format shape) |
| Accessibility for agents | Accessibility tree supports machine interaction | Standard a11y signals: roles, names, labels |
| Layout stability | CLS that disrupts agent interactions | CLS *risk factors* statically; numbers need Lighthouse |

## How to audit each, honestly

- **WebMCP (3 audits):** WebMCP is a *proposed* standard for declaring site capabilities
  as tools agents can call. For most 2026 sites the finding is "no WebMCP declarations
  found" at **info** severity — adoption is early; recommend only for sites with
  significant interactive flows (booking, checkout, dashboards). Do not present WebMCP
  absence as a defect.
- **llms.txt:** see `references/ai-crawl-access.md` — recommend with the both-truths
  framing (Lighthouse recommends it; it is not a ranking/citation factor).
- **Accessibility for agents:** agents drive sites through the accessibility tree, so
  classic a11y failures are now also *agent* failures: unlabeled buttons, div-as-button
  click handlers, missing form labels, missing landmark roles, content only reachable by
  hover. The pitch to clients: accessibility work now has a second ROI — agent
  compatibility. (Deep a11y auditing belongs to rad-a11y; here, flag the overlap.)
- **Layout stability:** late-loading banners and unreserved embeds that shift layout can
  make an agent click the wrong element. Reuse the CLS risk-factor checks from
  `technical-seo` §2.3 with this added framing.

## Severity guidance

Everything in this category is **info** by default (proposed standards, experimental
category), with two exceptions:

- a11y failures that block machine interaction (unlabeled controls on key flows) —
  **warning**, because they hurt human users today and agents tomorrow.
- A server error (5xx) serving /llms.txt — **warning** (mirrors Lighthouse, which only
  fails the audit on server error).

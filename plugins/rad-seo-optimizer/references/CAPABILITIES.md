# rad-seo-optimizer — Capabilities & Honest Limits

This plugin does real work on the surface area where Claude Code has edge — static analysis of the user's codebase, content structure auditing and rewriting, JSON-LD schema generation, and observational research over the open web via WebFetch/WebSearch.

It does NOT replace measurement-dependent SEO platforms (Ahrefs, Semrush, Screaming Frog, Lighthouse/PSI, Google Search Console) because the underlying measurement infrastructure isn't available to the Claude Code runtime. This file documents exactly what's in-scope, what's out-of-scope, and what integrations would unlock the gaps.

## In-scope (the plugin actually does this well)

| Capability | How |
|---|---|
| Codebase SEO linting | Glob/Grep/Read over HTML/MDX/template files — detects missing meta, bad H1 hierarchies, absent alt text, invalid canonicals, broken JSON-LD, robots.txt misconfigurations |
| JSON-LD schema generation | Produces valid, typed JSON-LD from page content for any schema.org type |
| AI-extractability content linter | Scores the user's content on structural signals that tend to earn AI citations (question headings, direct-answer leads, quotable stats, FAQ schema presence, semantic chunking) — measures *content structure*, not *actual AI citations* |
| Content rewriting for AEO | Converts H2s to question format, leads sections with direct answers, bolds quotable stats, adds FAQ schema — real file transforms |
| Broken-link audit over repo | Parses `href` references, verifies targets exist in the codebase, flags 404s and redirect chains in config |
| Internal-linking graph | Builds the link graph from templates + content, identifies orphans, over-linked pages, hub/spoke gaps |
| SERP feature observation | WebSearch returns who owns featured snippets, PAA, image/video thumbnails, AI Overview citations (when surfaced) for specified keywords |
| AI crawl access audit | `scripts/audit-ai-access.py` — robots.txt per-AI-bot matrix (training vs citation class), llms.txt existence/format, Content-Signal/RSL/noai detection, JS-dependence heuristic, optional CDN-block UA probe |
| Agent-readiness review | Static checks aligned with Lighthouse's experimental Agentic Browsing category (llms.txt, accessibility-tree quality, layout-shift risk, WebMCP presence) — see `references/agent-readiness.md` |
| Keyword ideation + intent classification | Generates keyword candidates, classifies search intent (informational/navigational/transactional/commercial), clusters semantically |
| Competitor content gap analysis | WebFetch of competitor pages + observation of their content patterns, topics, formats |
| Content audit + scoring | Scores the user's own content on quality + E-E-A-T + AI-extractability structure |
| Editorial calendar + content strategy | Pure reasoning task — maps topics, clusters, publishing cadence recommendations |
| Schema validation | Parses existing JSON-LD / Microdata / RDFa, checks against schema.org specs |
| Code-level page-speed risk factors | Flags unoptimized images, render-blocking scripts, missing lazy loading, unminified bundles — *risk factors visible in code*, NOT measured CWV numbers |

## Out-of-scope without external infrastructure

| Capability | Why it can't work from Claude Code alone | Path B integration that unlocks it |
|---|---|---|
| Numerical Core Web Vitals (LCP, CLS, INP) | CWV requires a real browser with paint timers. WebFetch gives you HTTP response time (TTFB), which is NOT LCP. | Lighthouse CLI / PageSpeed Insights API MCP |
| Whole-site crawling | Discovering every page on a live site, respecting rate limits, executing JS for SPAs, building a complete URL inventory | A crawler MCP (Screaming Frog CLI, Sitebulb, or custom Playwright-based crawler MCP) |
| JavaScript-rendered content analysis | WebFetch returns raw HTML — SPAs render client-side, so the fetched HTML is empty for those sites | Browser MCP (Playwright/Puppeteer-based) |
| Keyword search volume | Real volume data comes from Google, aggregated by keyword tools | DataForSEO / Semrush / Ahrefs / Keywords Everywhere MCP |
| Keyword difficulty scoring | Requires link-graph + SERP competitor strength analysis | Same — DataForSEO / Ahrefs / Moz MCP |
| Backlink counts + referring domains | Requires a crawled link graph of the open web | Ahrefs / Majestic / SEMrush / Moz MCP |
| Domain authority / domain rating | Same as backlinks — needs the link graph | Same link-graph MCPs |
| Organic traffic estimates per page | Comes from GSC (your own site) or third-party estimators for others | GSC MCP (your site) / Similarweb MCP (competitors) |
| Actual current rankings | Rank tracking requires repeated SERP scraping with proxy infrastructure | GSC MCP (your site) or a rank-tracker MCP |
| Actual AI citation rates in ChatGPT / Perplexity / Gemini | Requires querying those products' chat APIs. WebSearch returns web search results, NOT ChatGPT's answer to a question. | Direct API integration with OpenAI / Perplexity / Gemini / Anthropic / Microsoft — either via platform APIs or via a chat-scraping MCP |
| AI-platform sentiment / accuracy scoring | Same as above — can't score what you can't query | Same direct API integrations |
| Real PageSpeed Insights / Lighthouse scores | Requires a real measurement run | PSI API / Lighthouse CLI MCP |

## How skills/agents should handle gaps

Every audit skill and agent in this plugin honors the same rule: **if a category requires out-of-scope infrastructure, return observable code/content signals for what you CAN see, fill `measurement_gaps[]` in the JSON output with the specific gap + the Path B integration that would unlock it, and never fabricate a number for the missing score.**

When a user asks a question that requires out-of-scope infrastructure ("What's my Core Web Vitals score?", "What's my domain authority?", "How often does ChatGPT cite me?"), the response should be:
1. Acknowledge the question
2. State the specific gap honestly
3. Offer the observable proxy (code-level risk factors, content structure, WebSearch observation)
4. Name the Path B integration that would give the real answer

## Path B integration priorities

If the user wants to extend the plugin's real measurement capability, these are the highest-leverage integrations in order:

1. **Lighthouse / PageSpeed Insights MCP** — unlocks real CWV scoring. Cheapest to add (Google provides a free API key).
2. **Google Search Console MCP** — unlocks real ranking + traffic data for the user's own site. Free for site owners.
3. **DataForSEO MCP** — unlocks keyword volume + difficulty + SERP analysis. Paid but reasonable.
4. **Browser/crawler MCP (Playwright-based)** — unlocks JS-rendered content + real site crawling. Open-source options available.
5. **Ahrefs / SEMrush MCP** — unlocks backlink data + competitor traffic. Expensive.
6. **AI-platform query MCP** (if/when it exists) — unlocks real AI citation measurement. Currently limited by platform ToS.

Each integration should be added as an optional capability — skills detect presence and use real measurement when available, fall back to honest observation when not.

# rad-seo-optimizer — Honest codebase-scoped SEO tooling for Claude Code.

This plugin does real work on the surface area where Claude Code has edge — static analysis of your codebase, content structure auditing and rewriting, JSON-LD schema generation, and observational research over the open web. It does NOT replace measurement-dependent SEO platforms (Ahrefs, Semrush, Screaming Frog, Lighthouse) because the underlying measurement infrastructure isn't available to the Claude Code runtime. See [`references/CAPABILITIES.md`](./references/CAPABILITIES.md) for the full capability statement and the Path B integrations that would unlock the gaps.

## What You Can Actually Do With This

- **Lint your codebase for SEO issues** — find missing meta, bad H1 hierarchies, absent alt text, invalid canonicals, broken JSON-LD, robots.txt misconfigurations
- **Audit your AI crawl access** — per-AI-bot robots.txt matrix (training vs citation bots), CDN-level block detection, llms.txt check, Content-Signals/RSL detection, JS-dependence heuristic (`scripts/audit-ai-access.py`)
- **Generate valid JSON-LD schema** — from observable page content, any schema.org type (with current rich-result deprecation awareness — FAQ/HowTo rich results are gone)
- **Score your content on AI-extractability** — structural readiness to be cited by ChatGPT/Perplexity/Gemini (NOT actual citation rates, which need Path B)
- **Rewrite content for AEO** — convert H2s to question format, lead with direct answers, add FAQ schema, add comparison tables
- **Fix broken links** — crawl your repo, verify targets, patch 404s and redirect chains
- **Audit internal linking** — orphan pages, over/under-linked pages, hub-and-spoke gaps
- **Observe SERP features** — who owns featured snippets, PAA, and observable AI Overview citations for your target keywords
- **Ideate keywords** — seed expansion, intent classification, semantic clustering (qualitative competitiveness signals, NOT numerical volume/difficulty)
- **Research competitor content** — topics they cover, content patterns they use, SERP feature ownership
- **Plan content strategy** — topical authority mapping, gap analysis, 12-week editorial calendar
- **Plan link building** — linkable asset identification, tactic selection, 12-week outreach cadence with templates

## What This Plugin Explicitly Does NOT Do (Without Path B)

- **Measure numerical Core Web Vitals** (LCP, CLS, INP) — needs Lighthouse/PSI MCP
- **Return real search volumes or keyword difficulty scores** — needs DataForSEO/Ahrefs/Semrush MCP
- **Count backlinks or measure domain authority** — needs Ahrefs/Majestic/Semrush/Moz MCP
- **Estimate organic traffic** — needs Similarweb/Semrush MCP (competitors) or GSC MCP (own site)
- **Crawl entire live sites** — needs a crawler MCP (Screaming Frog / Sitebulb / Playwright-based)
- **Analyze JavaScript-rendered SPA content** — needs a browser MCP
- **Measure actual AI citation rates** in ChatGPT/Perplexity/Gemini/Claude/Copilot — needs direct AI-platform API integration

When you ask a question requiring any of the above, the plugin will observe what it CAN from your codebase + WebSearch + WebFetch, fill `measurement_gaps[]` in its JSON output with the specific gap, and name the Path B MCP that would unlock it. It never fabricates numbers.

## Skills

| Skill | Purpose |
|-------|---------|
| `full-seo-audit` | Scoped 6-phase audit over codebase + URL list (not full site crawl) |
| `on-page-optimizer` | Title tags, meta, headings, internal linking, E-E-A-T signals (code transforms) |
| `keyword-discovery` | Seed expansion, intent classification, qualitative difficulty, topic clustering |
| `competitor-intelligence` | Observable competitor research — content, SERP features, AI citation patterns (NOT backlinks) |
| `content-strategist` | Topical authority mapping, content gap analysis, 12-week editorial calendar |
| `link-building-strategy` | Linkable assets, tactic selection, 12-week outreach playbook with templates |
| `schema-architect` | JSON-LD generation + validation (one of the plugin's strongest capabilities) |
| `technical-seo` | Crawlability, AI-crawler access matrix, canonicals, redirects, page-speed CODE-LEVEL risk factors (NOT numerical CWV) |
| `aeo-optimizer` | AI-extractability content linter + seeding strategy + consistency audit + content conversion |
| `fix-seo` | Issue router + remediation (applies fixes, doesn't just diagnose) |
| `broken-link-fixer` | Crawl repo for hrefs, verify targets, fix 404s and redirect chains |
| `seo-report-generator` | Aggregate audit findings into prioritized report with honest measurement-gap surfacing |

## Agents

| Agent | Purpose |
|-------|---------|
| `seo-dominator` | Autonomous scoped SEO audit with honest measurement-gap handling |
| `competitor-spy` | Autonomous observable competitor research |
| `content-auditor` | Autonomous content quality + AI-extractability audit over user's own content |

All three agents default to **Opus** (Sonnet is a first-class fallback; Haiku for narrow-scope). All emit **JSON-first output** per the schemas in `references/subagent-prompts/` for reliable cross-model parsing.

## What's New in 2.2

The AI-crawl-access release. Research-grounded against the 2026 landscape (Lighthouse Agentic Browsing, AI Mode query fan-out, the May 2026 FAQ rich-result retirement).

- **New validator: `scripts/audit-ai-access.py`** — robots.txt per-AI-bot allow/block matrix classed *training* (GPTBot, ClaudeBot, Google-Extended, CCBot…) vs *citation* (OAI-SearchBot, ChatGPT-User, Claude-SearchBot/User, PerplexityBot/User, Bingbot, Googlebot), llms.txt existence + format check, Content-Signal/RSL/noai detection, JS-dependence heuristic (no AI crawler executes JS), and an optional `--check-fetch` probe for CDN-level blocking (Cloudflare blocks AI crawlers by default on new domains since July 2025).
- **llms.txt handled with both truths**: not a Search ranking/citation factor (Google's stated position + crawl-log evidence), but recommended by Chrome Lighthouse's experimental Agentic Browsing audits — so the plugin recommends it without overpromising. New `references/ai-crawl-access.md` and `references/agent-readiness.md`.
- **aeo-optimizer gained Phase 0 (AI Crawl Access Gate)** — content extractability is moot if citation bots are blocked or content is CSR-only; technical-seo gained §1.7 (AI Crawler Access).
- **Schema deprecation pass**: FAQ rich results retired by Google May 2026 (HowTo in 2023; Book Actions/Course Info/ClaimReview/etc. June 2025) — every skill/reference now frames FAQPage/HowTo as AI-parsing aids, never rich-result opportunities.
- **validate-jsonld.py 1.1.0**: now genuinely handles framework JSON-LD — unwraps `dangerouslySetInnerHTML`/`set:html`/JSX template-literal forms and validates them; dynamic `JSON.stringify(expr)` blocks get an honest `dynamic_jsonld` info finding instead of being silently skipped or falsely failed. audit-meta-tags now checks `twitter:image`. Doc fixes in check-broken-links.
- **De-versioned model references** (Opus/Sonnet/Haiku without point versions) to end the per-release review tax.

## What's New in 2.0

This is a major revision. The previous 1.x version marketed itself as a full SEO tool replacement but silently fabricated scores for categories it couldn't actually measure. 2.0 retrenches to what's honestly measurable from Claude Code alone, and marks every gap with its Path B MCP unlock.

**Honesty changes:**
- **Retired the fake 6-dimension AI visibility scorecard** (Presence/Accuracy/Sentiment/Position/Completeness/Consistency querying ChatGPT/Perplexity/Gemini via WebSearch — which returned web search results, not AI chat responses). Replaced with the **AI-Extractability Content Linter** that scores the user's *own content structure* on signals that tend to earn AI citations.
- **Dropped numerical keyword volume and difficulty scores.** Keyword-discovery now produces qualitative competitiveness signals from observable SERP patterns.
- **Dropped backlink count / domain authority claims.** Competitor-intelligence and link-building-strategy now produce qualitative observations + tactical playbooks.
- **Dropped numerical Core Web Vitals scoring.** Technical-seo and full-seo-audit now report *code-level page-speed risk factors*, not measured LCP/CLS/INP numbers.
- **Added `references/CAPABILITIES.md`** — explicit statement of what the plugin can and cannot measure, with the Path B MCP that would unlock each gap.
- **Every agent + skill surfaces `measurement_gaps[]`** in its JSON output — gaps are declared, not papered over.

**Platform pass (applied to the honest surface):**
- Opus-default on all three agents, Sonnet documented as first-class fallback
- JSON-first subagent output contracts at plugin-level `references/subagent-prompts/{site-audit,competitor-research,content-audit}.md`
- Flattened agent layout: `agents/<name>/AGENT.md` → `agents/<name>.md`
- Fixed broken hex color codes — runtime doesn't recognize them. Switched to named colors (orange, teal, purple).
- Cross-model notes on every skill
- Parallel-first execution guidance in multi-phase skills
- `--non-interactive` mode on `full-seo-audit`, `aeo-optimizer`, `competitor-intelligence`, `content-strategist`, `evaluate-stack` equivalents
- `--resume <run-id>` + shared checkpoint schema at `.seo/state/<run-id>.json`

## Path B Roadmap

When you want the measurement capabilities back, these are the highest-leverage MCP integrations in priority order:

1. **Lighthouse / PageSpeed Insights MCP** — real Core Web Vitals. Free API.
2. **Google Search Console MCP** — real ranking + traffic data for your own site. Free for site owners.
3. **DataForSEO MCP** — keyword volume + difficulty + SERP analysis. Paid but reasonable.
4. **Browser/crawler MCP (Playwright)** — JS-rendered content + real site crawling. Open-source options.
5. **Ahrefs / SEMrush MCP** — backlink data + competitor traffic. Expensive.
6. **AI-platform query MCP** (when ToS-compatible options emerge) — real AI citation measurement.

Each integration is additive — skills detect presence and use real measurement when available, fall back to honest observation when not.

## Quick Start

```bash
claude plugins add ./RAD-Claude-Skills/plugins/rad-seo-optimizer
```

> **Using Claude.ai instead of CLI?** See [`skills/rad-seo-aeo-reviewer/`](../../skills/rad-seo-aeo-reviewer/) for the Claude.ai skill version — a single ZIP with consolidated workflows, URL fetching, web search, and artifact output. No CLI required. (Refreshed to match the honesty pass: extractability linter instead of the retired AI-visibility scorecard, CWV risk-factor framing, AI-crawler access checks, and current schema deprecations.)

Then ask:

```
Audit my SEO (codebase + URL list)
Score my content for AI-extractability
Find keyword ideation opportunities
Check my competitors' observable SEO signals
Fix my missing meta descriptions
Generate FAQPage schema for my FAQ pages
```

## License
Apache-2.0

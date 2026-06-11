---
name: full-seo-audit
description: >
  Audit my SEO, run an SEO audit, SEO score, SEO health check, full SEO analysis —
  comprehensive multi-category request. Performs a scoped 6-phase audit over the user's
  codebase plus a user-provided URL list (typically 5-10 URLs). Covers technical SEO,
  on-page SEO, content/E-E-A-T, schema, internal linking, and AI-extractability. Does
  NOT crawl the entire live site, does NOT measure Core Web Vitals numerically, does
  NOT infer backlinks — those require Path B MCP integrations. For single-area requests,
  route to the specialized skill instead.
argument-hint: "[URL or path to audit] [--urls=url1,url2,...] [--non-interactive] [--resume <run-id>]"
allowed-tools: Read Glob Grep Write Bash WebFetch WebSearch Agent
---

# Full SEO Audit — Scoped Master Orchestrator

Coordinate a complete analysis across six phases over a defined audit surface (codebase + user-provided URL list), produce a unified score, and deliver a plain-English report with prioritized, actionable fixes.

**This is a scoped audit, not a full-site crawl.** Real full-site crawling requires a crawler MCP (Screaming Frog / Sitebulb / browser-based). Real Core Web Vitals require Lighthouse / PageSpeed Insights. This skill does the work that can be done honestly from static analysis + limited live fetches. The report explicitly lists what was and was not measured.

Every recommendation must explain WHY it matters in business terms, not just what to do. Write for a business owner who does not know what a canonical tag is.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. Opus/Sonnet batch codebase reads, URL fetches, and reference loads in parallel. Haiku may follow sequentially if parallel batching misbehaves.

## Execution: parallel-first

- **Phase 0 setup**: all config/sitemap/robots reads independent — single batch
- **Phase 1 technical**: template Globs + config Reads + user URL fetches all independent — single batch
- **Phase 2 on-page**: per-page checks independent within a phase — batch
- **Phase 3 schema**: JSON-LD extraction per file independent — batch
- **Phase 4 content/AEO**: per-page scoring independent — batch
- **Phase 5 internal linking**: needs Phase 2's discovered page list — serialize start, parallelize per-page link extraction
- **Phase 6 competitive**: WebSearch queries independent — batch
- **What to serialize, always**: phase transitions (each phase may feed into the next phase's scope decision), user-approval gates in interactive mode

## Capability Honesty

Read `references/CAPABILITIES.md` at the start. Key constraints:
- **Cannot measure**: numerical Core Web Vitals, keyword volumes, backlink counts, domain authority, actual AI citation rates, JS-rendered SPA content, full-site URL inventory
- **Can measure**: static-analysis findings across the user's codebase, observable findings from user-provided URLs (via WebFetch), SERP feature ownership (WebSearch), content structure quality, schema validity, code-level page-speed risk factors, internal linking graph for provided pages

Any category the user wants that requires unavailable infrastructure is reported in `measurement_gaps[]` with the Path B integration that would unlock it.

## Mode Flags

- `--non-interactive` — Skip Phase 0 question gates. Use reasonable defaults, record unanswered context in `awaiting_user_review`. Auto-proceed through phase transitions. Emit trailing JSON with the final report path.
- `--resume <run-id>` — Load `.seo/state/<run-id>.json` and continue from the last saved phase.
- `--urls=url1,url2,...` — Explicit URL list to fetch (overrides the Phase 0 question)

## Checkpoint & Resume

Save state to `.seo/state/<run-id>.json` at each phase boundary. Shared schema with other rad-seo multi-phase skills. See `references/CAPABILITIES.md` and the subagent-prompts for the full schema.

---

## Phase 0: Discovery

Gather required context before auditing. Ask the user and do not proceed until you have at least the codebase path or URL list:

1. **Audit surface** — Is this a codebase audit, URL-list audit, or both?
2. **Codebase path** — If applicable, the local path to the source code
3. **URL list** — If applicable, the live URLs to fetch (default limit ~10 to stay within budget; ask to confirm if more)
4. **Business type** — E-commerce, SaaS, local service, publisher, etc.
5. **Target audience** — Who they're trying to reach (geography, demographics, intent)
6. **Top 3 competitors** — URLs of the websites they compete with for search traffic
7. **Primary business goal** — Leads, sales, brand awareness, publishing — this weights recommendations

In `--non-interactive` mode, use whatever context was passed and record unanswered items in `awaiting_user_review`.

Save Phase 0 checkpoint.

---

## Phase 1: Technical SEO (20% weight)

Static analysis + limited live fetches for the technical foundation that search engines need to crawl, index, and serve the site properly.

### Crawlability & Indexation (static analysis — scored fully)
Parallel batch: read `robots.txt`, XML sitemaps, template/layout files, framework config (`next.config.*`, `astro.config.*`, `vite.config.*`), `.htaccess`, `_headers`, `vercel.json`, `netlify.toml`.
- `robots.txt` exists? blocking important paths?
- XML sitemap at standard paths? referenced in robots? well-formed?
- Canonical tags present? self-referencing?
- `noindex` meta tags on pages that should be indexed?
- Redirect rules (configs): chains? loops?

### Page-Speed Code-Level Risk Factors (static analysis — scored honestly, NOT CWV numbers)
Flag *risk factors* observable in code — NOT LCP/CLS/INP numbers, which require Lighthouse/PSI measurement:
- Large unoptimized images (`.png`/`.jpg` > threshold, missing width/height)
- Render-blocking scripts in `<head>` without `defer`/`async`
- Missing lazy loading on below-fold images
- Unminified JS/CSS in production
- Excessive third-party tags

The category's score reflects presence/absence of risk factors. If the user has a Lighthouse MCP available, use it for the real CWV score and merge; otherwise mark method as `static-analysis` in the JSON output.

### Mobile Readiness (static analysis — scored fully)
- Viewport meta tag present
- Fixed-width elements that would break on small screens
- Tap target sizing

### Security (static analysis — scored fully)
- HTTPS configuration (visible from URL list fetches)
- Mixed content (HTTP resources on HTTPS pages)
- Exposed sensitive paths (`.env`, `.git`, admin without protection)

### URL Structure (static analysis — scored fully)
- Clean, descriptive URLs vs. query-string-heavy
- Trailing slash consistency
- 301 redirect hygiene (from config)

For deeper technical analysis, delegate to the **technical-seo** skill.

---

## Phase 2: On-Page SEO & E-E-A-T (15% weight)

Per-page analysis from codebase templates + URL fetches.

### Title Tags & Meta Descriptions
- Every indexable page has a unique title (50-60 chars)
- Every indexable page has a unique meta description (120-160 chars)
- Titles contain primary keyword near the front
- Flag duplicates

### Heading Structure
- Exactly one H1 per page, containing primary keyword
- Logical H1→H2→H3 hierarchy, no skipped levels
- Flag missing or multiple H1s

### Content Quality Signals
- Flag thin content (< 300 words on competitive-term pages)
- Keyword stuffing patterns
- Image alt text present, descriptive, not filename gibberish

### E-E-A-T Signals
- Author bylines and author bio pages
- About page, Contact page, Privacy Policy
- Trust signals: testimonials, reviews, certifications, credentials
- For YMYL (Your Money Your Life) sites, these are critical — flag missing signals as high priority

Why E-E-A-T matters: Google's quality raters evaluate these signals. Sites lacking them — especially in health, finance, or legal — face an uphill battle regardless of technical SEO quality.

---

## Phase 3: Content & AI-Extractability (20% weight)

Content quality + structural readiness for AI search engines. Uses the AI-extractability linter logic from `aeo-optimizer` Phase 1 (six structural dimensions).

### Content Quality Scoring
For each key page: relevance to intent, depth, freshness, readability, unique value.

### AI-Extractability Structure
- Question-format H2s (ratio)
- Direct-answer first-sentence pattern
- Quotable bold stats
- FAQ schema presence
- Comparison tables / structured formats
- Semantic chunking

**Honest framing**: this scores *content's readiness to be cited by AI*, not *actual AI citation rate*. See `references/CAPABILITIES.md`.

For deeper content analysis, delegate to **on-page-optimizer** or the **content-auditor** agent.
For keyword gaps, delegate to **keyword-discovery**.

---

## Phase 4: Schema & Structured Data (10% weight)

Parallel-batch parse JSON-LD / Microdata / RDFa from templates and fetched pages.

### Current Schema Audit
- Validate each schema block against schema.org
- Flag invalid, incomplete, deprecated types
- Check required properties per type

### Missing Opportunities
By business type:
- **All sites**: Organization, WebSite, BreadcrumbList, SiteNavigationElement
- **E-commerce**: Product, Offer, AggregateRating, Review
- **Local business**: LocalBusiness, OpeningHoursSpecification, GeoCoordinates
- **Publishers/blogs**: Article, BlogPosting, Author (FAQPage only as an AI-parsing aid)
- **Service businesses**: Service (HowTo/FAQPage only as AI-parsing aids)
- **Events**: Event with proper date and location markup

### Rich Snippet Potential
Flag pages close to qualifying for rich results but missing one or two properties —
**checking deprecations first** (`references/schema-types-guide.md`): FAQ and HowTo rich
results no longer exist (HowTo retired 2023, FAQ retired May 2026), so never list them as
rich-result opportunities. Live opportunities: Product/Review stars, Article, Event,
Recipe, VideoObject, Breadcrumb, JobPosting.

Why schema matters: Structured data does not directly boost rankings, but live rich-result
types increase click-through rates, and clean entity markup aids AI parsing.

For detailed schema implementation, delegate to **schema-architect**.

---

## Phase 5: Internal Linking & Site Architecture (10% weight)

### Orphan Pages
Pages in the sitemap or indexable but with zero internal links — invisible to search engines during crawling.

### Link Distribution
- High-value keyword pages receive enough internal links
- Flag pages with 100+ outbound internal links (dilutes value)
- Identify pages with 1-2 internal links that should have more

### Hub-and-Spoke Analysis
- Topic clusters: pillar (hub) → subtopic (spokes) → back to hub
- Flag disconnected content silos
- Recommend hub pages to create

### Navigation & Depth
- Important pages reachable within 3 clicks from homepage
- Breadcrumb navigation present and logical
- Flag deep pages (4+ clicks) targeting important keywords

Why internal linking matters: One of few ranking factors entirely within the site owner's control. Distributes authority; tells search engines which pages matter most.

---

## Phase 6: Competitive Positioning (observational — feeds prioritization, no direct score weight)

Compare the site against competitors via observable signals. Uses the competitors identified in Phase 0.

### Content Gaps
Topics and keywords competitors rank for that the user does not. Prioritize by observable signal strength + business relevance.

### Link Gaps (observational only)
Note if competitors appear to have stronger backlink profiles *via observable signals* (e.g., press coverage, linkable assets). Do NOT report numerical backlink counts without Path B integration.

### AI Citation Pattern Observation
Observe what content patterns competitors use that tend to earn AI citations. This is pattern observation, NOT a measurement of their actual citation rates.

### Feature Comparison
- Schema markup coverage across competitors
- Code-level page-speed risk factors observable from fetched HTML
- Rich results competitors earn that the audited site does not

For deeper competitive analysis, delegate to **competitor-intelligence** or the `competitor-spy` agent.

---

## Scoring System

Read `references/audit-scoring-rubric.md` for the full category weights, severity deductions, A-F scale, and scoring methodology.

**Important**: categories whose measurement requires unavailable infrastructure are marked `method: not-measured` and excluded from the overall weighted score — NEVER fabricated. The report explicitly lists those gaps in the `measurement_gaps` section.

---

## Report Generation

After completing all six phases, produce the audit report. Write in plain English for a non-technical business owner.

```
# SEO Audit Report: [Website]
## Date: [date]
## Audit Scope: [codebase | URL list | both] — [pages audited]
## Overall Score: [X]/100 (Grade: [A-F])
## Measurement Gaps: [list categories requiring Path B — their Path B unlock]

### Executive Summary
[2-3 paragraphs. Lead with the biggest finding. Summarize what works, what needs urgent attention,
and the single highest-impact action. Name the measurement gaps honestly.]

### Score Breakdown
| Category | Score | Grade | Method | Critical | Warnings | Opportunities |
|---|---|---|---|---|---|---|
| Technical SEO | /100 | | static-analysis | | | |
| On-Page SEO | /100 | | static-analysis | | | |
| Content & E-E-A-T | /100 | | static-analysis | | | |
| Schema & Structured Data | /100 | | static-analysis | | | |
| Internal Linking | /100 | | graph-built | | | |
| Page Speed (code-level risk) | /100 | | static-analysis | | | |
| Page Speed (CWV numbers) | N/A | | not-measured (needs Lighthouse MCP) | | | |
| Mobile Usability | /100 | | static-analysis | | | |
| AI-Extractability | /100 | | static-analysis | | | |
| **Overall (Weighted, measured categories only)** | **/100** | | | | | |

### Critical Issues (Fix Immediately)
[Per issue: impact, category, what's wrong, why it matters in business terms, how to fix with Claude Code command]

### Warnings (Fix Within 30 Days)
[Per issue: same format]

### Opportunities (Nice to Have)
[Per issue: same format]

### 30/60/90 Day Roadmap
#### Days 1-30: Foundation Fixes
#### Days 31-60: Content & Authority
#### Days 61-90: Growth & Competitive Edge

### AI-Extractability Score
[What it means: "measures how structurally ready your content is to be cited by AI engines.
Does NOT measure actual AI citations — that would require Path B MCP integration."
Then: current score, top 3 things helping, top 3 things hurting, specific conversion recommendations.]

### Measurement Gaps (What This Audit Did NOT Measure)
[For each gap: what you wanted, why it requires external infrastructure, which Path B MCP
would unlock it.]

### Next Steps
- Re-audit in: [30/60/90 days depending on severity]
- Ongoing monitoring: [what to track weekly/monthly — only things you can actually measure]
- Quick wins completed during audit: [list fixes applied]
- Path B integrations to consider: [ranked list of MCPs that would unlock measurement gaps]
- Specialist skills to run next: [list of relevant rad-seo skills]
```

---

## Execution Rules

1. **Complete all 6 phases.** If a phase has no issues, say so and score accordingly.
2. **Fix simple issues on the spot.** Codebase access + missing meta description or broken schema? Fix it during the audit. Note under "Quick wins completed during audit."
3. **Be specific, not generic.** "The /pricing page has no meta description — here's the exact command to add one" beats "improve meta descriptions."
4. **Rank by impact vs. effort.** Quick win > Strategic > Fill-in > Deprioritize.
5. **Provide exact commands.** Every fix includes a Claude Code command or copy-paste file edits.
6. **Explain business impact.** "LCP risk factor: unoptimized 3MB hero image" → "This hero image likely delays the main page paint noticeably on mobile. Compress to < 200KB."
7. **Be honest about measurement gaps.** Never fabricate a number. Always surface the Path B unlock.
8. **Respect the report template.** Keep reports consistent so they're comparable over time.

---

## Output JSON (for --non-interactive)

```json
{
  "audit_complete": true,
  "run_id": "string",
  "audit_scope": "codebase | urls | both",
  "overall_score": 0,
  "overall_grade": "A | B | C | D | F",
  "report_path": "seo-audit-report.md",
  "measurement_gaps": [
    {"category": "string", "path_b_integration": "string"}
  ],
  "critical_count": 0,
  "warning_count": 0,
  "opportunity_count": 0,
  "quick_wins_applied": 0,
  "escalation_required": false,
  "awaiting_user_review": ["string"]
}
```

---

## Cross-Skill Delegation Reference

| Situation | Delegate To | What It Does |
|---|---|---|
| Complex crawl issues, redirect chains, server config | **technical-seo** | Deep technical analysis on static + config surface |
| Need keyword targets | **keyword-discovery** | Keyword ideation + intent (volumes require Path B) |
| Content rewriting | **on-page-optimizer** | Content quality + AEO conversion |
| Schema needs writing or fixing | **schema-architect** | JSON-LD implementation + validation |
| Detailed competitor breakdown | **competitor-intelligence** | Observable competitive research |
| Ongoing scheduled auditing | **full-seo-audit** | Run on a cadence |

Always complete the full audit first. Delegate to specialists for implementation, not for the audit itself.

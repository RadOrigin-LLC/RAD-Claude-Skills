---
name: seo-report-generator
description: >
  SEO report, generate audit report, summarize SEO findings, SEO dashboard, SEO roadmap.
  Aggregates findings from completed audit skills into a prioritized report. Runs AFTER
  audit skills. Produces scores, executive summary, and 30/60/90-day roadmap. Honestly
  surfaces which categories were measured vs. require Path B MCP integrations.
argument-hint: "[audit report directory or JSON dump]"
allowed-tools: Read Glob Grep Write Bash
---

# SEO Report Generator

Aggregate findings from every other skill in the RAD SEO Optimizer plugin and produce a single, prioritized, actionable report a business owner or developer can follow step-by-step. The report must be honest about what was measured vs. what requires external measurement infrastructure.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. This is primarily a synthesis/formatting task; parallel batching matters only when reading many input artifacts.

## Execution: parallel-first

- **Phase 1 data collection**: Reads of audit artifacts (JSON + markdown) from sibling skills are independent — batch
- **Phase 2 prioritization**: synthesis, serial
- **Phase 3 report generation**: serial (requires full inputs)

## Capability Honesty

Read `references/CAPABILITIES.md`. This report aggregates whatever was measured by the audit skills. If an audit skill marked a category as `method: not-measured` or populated `measurement_gaps[]`, the report:
1. Does NOT fabricate a number to fill the missing category
2. Excludes that category from the overall weighted score (redistributes weight across measured categories)
3. Surfaces the gap explicitly in the report's Measurement Gaps section
4. Names the Path B MCP that would unlock it

---

## Phase 1: Data Collection

Gather results from all completed audit skills. Parse JSON outputs where available (preferred — the 2.0 skills emit JSON-first); fall back to parsing markdown reports.

### Required Data Sources

| Source Skill | Data Collected |
|---|---|
| `technical-seo` | Crawlability, indexing, robots.txt, sitemap, HTTPS, canonical tags, redirects, status codes, page-speed risk factors |
| `on-page-optimizer` | Title tags, meta descriptions, headings, keyword usage, image alt text, URL structure findings |
| `content-auditor` agent | Content quality scores, E-E-A-T signals, AI-extractability structure |
| `schema-architect` | Structured data types present, validation errors, coverage gaps |
| `broken-link-fixer` | Internal link graph analysis, orphan pages, broken links, redirect chains |
| `aeo-optimizer` Phase 1 | AI-Extractability Content Linter scores (structural readiness, NOT actual AI citation rates) |
| `competitor-intelligence` | Competitor observable signals, content gaps, SERP feature ownership, qualitative link opportunities |
| `keyword-discovery` | Target keywords, search intent, qualitative difficulty, topic clusters |
| `link-building-strategy` | Linkable asset audit, outreach prospect list, tactic recommendations |

If a skill has not yet been run, note it as **"Not audited — run [skill name] first"** in the report and exclude its category from the overall score.

### Categories That Require Path B

These categories are aggregated ONLY if the user integrated a Path B MCP:

| Category | Path B MCP |
|----------|------------|
| Numerical Core Web Vitals (LCP/CLS/INP) | Lighthouse / PageSpeed Insights |
| Search volume + keyword difficulty | DataForSEO / Ahrefs / Semrush |
| Backlink counts + DA/DR | Ahrefs / Majestic / Semrush / Moz |
| Organic traffic estimates | Similarweb / Semrush |
| Actual AI citation rates | Direct AI-platform APIs |

If Path B data is present, merge it into the relevant category. If not, exclude the numerical sub-category and surface the gap.

---

## Phase 2: Priority Ranking

Score every individual finding using three dimensions.

### Scoring Model

**Impact (1-10)**: Estimated ranking improvement if the issue is resolved.

| Impact Range | Meaning |
|---|---|
| 9-10 | Blocking indexing or causing major ranking loss |
| 7-8 | Significant ranking drag; fixing yields visible improvement within weeks |
| 4-6 | Moderate effect; contributes to cumulative ranking gains |
| 1-3 | Minor polish; unlikely to move rankings alone |

**Effort**:

| Label | Time Estimate | Multiplier |
|---|---|---|
| Quick Fix | < 30 minutes | 1 |
| Moderate | 1-4 hours | 2 |
| Project | 1+ days | 4 |

**Priority Score** = Impact / Effort Multiplier

Sort all findings by priority descending. Group into three tiers:
- **Critical Issues** — Priority ≥ 5 or Impact ≥ 9
- **Warnings** — Priority ≥ 2.5 and Impact ≥ 4
- **Opportunities** — Everything else worth acting on

---

## Phase 3: Report Generation

Output the report in the template below. Replace every `[placeholder]` with real data. Remove any section whose source skill was not run, but keep the heading with a note that the audit is pending.

````markdown
# SEO Domination Report: [Website Name]
**Generated**: [Date]
**Overall Score (measured categories only)**: [X]/100 (Grade: [A-F])
**AI-Extractability**: [X]/60 (content structural readiness — NOT actual AI citations)

---

## Executive Summary

[3-4 paragraphs in plain English covering:
- Current state of the website's SEO health
- Biggest opportunities for improvement
- Expected impact of implementing recommendations
- Competitive observations (where observable)
- Honest naming of measurement gaps]

---

## Measurement Gaps (What This Report Did NOT Measure)

| Category | Why | Path B MCP That Would Unlock |
|---|---|---|
| Numerical Core Web Vitals | No Lighthouse/PSI measurement present | Lighthouse CLI / PageSpeed Insights API |
| Keyword search volumes | No keyword-data API integration | DataForSEO / Ahrefs / Semrush |
| Backlink counts + DA | No link-graph API integration | Ahrefs / Majestic / Semrush / Moz |
| Actual AI citation rates | No AI-platform API integration | Direct AI-platform APIs |
| (etc. — only include gaps relevant to this audit) |

(Omit this section entirely if no gaps — i.e., all Path B MCPs are integrated.)

---

## Score Dashboard

### Category Scores

| Category | Score | Grade | Method | Critical | Warnings | Opportunities |
|----------|-------|-------|--------|----------|----------|---------------|
| Technical SEO | X/100 | X | static-analysis | X | X | X |
| On-Page SEO | X/100 | X | static-analysis | X | X | X |
| Content & E-E-A-T | X/100 | X | static-analysis | X | X | X |
| Schema Markup | X/100 | X | static-analysis | X | X | X |
| Internal Linking | X/100 | X | graph-built | X | X | X |
| Page-Speed Risk Factors | X/100 | X | static-analysis | X | X | X |
| Page-Speed CWV (numerical) | N/A | — | not-measured (Path B: Lighthouse) | — | — | — |
| Mobile & Accessibility | X/100 | X | static-analysis | X | X | X |
| AI-Extractability | X/100 | X | content-structure-linter | X | X | X |

**Grading Scale**: A = 90-100, B = 80-89, C = 70-79, D = 60-69, F = below 60

### AI-Extractability Breakdown

This scores your **content structure** on signals that tend to earn AI citations.
It does NOT measure actual citation rates. See Measurement Gaps for details.

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Question-Format Headings | X/10 | [qualitative assessment] |
| Direct-Answer Leads | X/10 | [qualitative assessment] |
| Quotable Stats / Bolded Data | X/10 | [qualitative assessment] |
| FAQ Schema Presence | X/10 | [qualitative assessment] |
| Comparison / Structured Data | X/10 | [qualitative assessment] |
| Semantic Chunking | X/10 | [qualitative assessment] |

---

## Critical Issues (Fix Immediately)

### 1. [Issue Title]
- **Category**: [Technical/On-Page/Content/Schema/Linking/Speed/AEO]
- **Impact**: [X]/10 | **Effort**: [Quick Fix/Moderate/Project] | **Priority**: [X]
- **What's wrong**: [Plain English explanation]
- **Why it matters**: [How this affects rankings and revenue]
- **How to fix with Claude Code**:
  ```
  claude "[exact command to fix this issue]"
  ```
- **Manual fix steps**: [Step-by-step where needed]

[Repeat for every critical issue, numbered sequentially]

---

## Warnings (Fix Within 30 Days)

[Same format as Critical]

---

## Opportunities (Implement for Growth)

[Same format]

---

## Competitive Analysis Summary (observable signals)

| Metric | Your Site | [Comp 1] | [Comp 2] | [Comp 3] |
|--------|-----------|----------|----------|----------|
| Content Pages (observable) | X | X | X | X |
| Schema Coverage | X% | X% | X% | X% |
| Core Web Vitals (if Lighthouse MCP present) | Y/N | Y/N | Y/N | Y/N |
| SERP Features Owned | X | X | X | X |
| AI-Extractability (content structure) | X/60 | X/60 | X/60 | X/60 |
| AI Overview Citations Observed | X | X | X | X |

**Metrics requiring Path B (omit row if not integrated):**
| Metric | Your Site | Comps | Path B |
|--------|-----------|-------|--------|
| Domain Authority / DR | — | — | Ahrefs / Semrush MCP |
| Organic Keywords | — | — | Ahrefs / Semrush MCP |
| Monthly Traffic Estimate | — | — | Similarweb / Semrush MCP |
| Backlink Count | — | — | Ahrefs / Majestic MCP |

---

## 30/60/90 Day Implementation Roadmap

### Days 1-30: Foundation Fixes
**Goal**: Fix all critical issues and quick wins

1. [Specific action] — `claude "[command]"`
2. ...

**Expected outcome (qualitative)**: [directional prediction]

### Days 31-60: Content & Authority Building

1. [Specific action] — `claude "[command]"`

**Expected outcome (qualitative)**: [directional prediction]

### Days 61-90: Growth & Competitive Edge

1. [Specific action] — `claude "[command]"`

**Expected outcome (qualitative)**: [directional prediction]

---

## Keyword Opportunities

| Keyword | Intent | Qual. Difficulty | Qual. Volume Signal | Current Rank* | Target Rank | Action |
|---------|--------|------------------|---------------------|---------------|-------------|--------|
| [kw] | [informational/transactional/navigational] | [Easy/Moderate/Hard] | [High/Medium/Low] | [pos or N/A] | [pos] | [Create/Optimize/Build links] |

*Current rank requires Google Search Console MCP or rank-tracker MCP. Populated only if integrated.

---

## Link Building Opportunities

| Tactic | Target | Effort | Priority | Status |
|--------|--------|--------|----------|--------|
| [Broken link / Resource page / Guest post / etc.] | [URL or domain] | [Quick/Moderate/Project] | [High/Medium/Low] | [Pending] |

(Numerical "Expected DA" columns omitted unless Ahrefs/Semrush MCP integrated.)

---

## Content Recommendations

| Content Piece | Type | Target Keyword | Word Count | Priority | Status |
|---------------|------|----------------|------------|----------|--------|
| [Title] | [Blog/Landing/Pillar/FAQ] | [keyword] | [est.] | [High/Medium/Low] | [To create/To update] |

---

## AEO Action Plan

1. **Structured Data Expansion** — Add Article, Organization, and Product schema to key
   pages; FAQPage/HowTo only as AI-parsing aids (their Google rich results are retired —
   HowTo 2023, FAQ May 2026; see `references/schema-types-guide.md`)
   ```
   claude "Add FAQ schema markup to [page] based on top questions about [topic]"
   ```
2. **Direct Answer Optimization** — Restructure content to lead with concise answers
3. **Entity Clarity** — Ensure primary entities are unambiguously defined
4. **Source Authority** — Build citations on authoritative third-party sites
5. **Freshness Signals** — Content update cadence for high-value pages
6. **Multi-Engine Consistency** — Verify information parity across platforms (Phase 3 of aeo-optimizer)

---

## Re-Audit Recommendation

- **Next full audit**: [Date — typically 90 days out]
- **Interim check (critical items only)**: [Date — typically 30 days out]
- **Focus areas for next audit**: [Top 3 areas to re-evaluate]
- **KPIs to track between audits (measurable without Path B)**:
  - Content volume published on priority channels
  - AI-extractability score trend (re-run aeo-optimizer Phase 1)
  - Number of pages with FAQ schema
  - Consistency issues remaining (Phase 3 of aeo-optimizer)
  - Confirmed new links earned (manual tracking)

- **KPIs that require Path B**:
  - Organic traffic trend (GSC MCP)
  - Core Web Vitals pass rate (Lighthouse MCP)
  - Keyword ranking movement (rank-tracker / GSC MCP)
  - Referring domain count change (Ahrefs / Semrush MCP)

---
*Generated by RAD SEO Optimizer — Claude Code Plugin*
````

---

## Phase 4: Export Options

After generating the report, offer three choices:

1. **Display in conversation** (default) — Output the full markdown report directly
2. **Save to file** — Write to `./seo-reports/[domain]-[YYYY-MM-DD].md`
3. **Create task lists** — Break into separate actionable files:
   - `critical-fixes.md` — Critical Issues with checkboxes
   - `30-day-plan.md` — Days 1-30 roadmap as checklist
   - `60-day-plan.md` — Days 31-60 as checklist
   - `90-day-plan.md` — Days 61-90 as checklist
   - `content-calendar.md` — Content recommendations as production schedule
   - `link-building-tracker.md` — Link prospects with status tracking columns

---

## Scoring Reference

### Overall Score Calculation

The overall score is the weighted average of **measured** category scores. If a category is marked `method: not-measured`, its weight redistributes proportionally across measured categories.

| Category | Weight |
|----------|--------|
| Technical SEO | 20% |
| On-Page SEO | 15% |
| Content & E-E-A-T | 20% |
| Schema Markup | 10% |
| Internal Linking | 10% |
| Page Speed (risk factors) | 5% |
| Page Speed (CWV numerical) | 5% (if measured; redistributes if not) |
| Mobile & Accessibility | 5% |
| AI-Extractability | 10% |

### Grade Thresholds

| Grade | Score Range | Interpretation |
|-------|------------|----------------|
| A | 90-100 | Excellent — maintain and iterate |
| B | 80-89 | Strong — a few targeted improvements needed |
| C | 70-79 | Average — meaningful gains available |
| D | 60-69 | Below average — significant work required |
| F | 0-59 | Poor — critical intervention needed |

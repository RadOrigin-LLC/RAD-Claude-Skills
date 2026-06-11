---
name: aeo-optimizer
description: >
  AEO, AI visibility, AI search optimization, generative engine optimization, LLM seeding,
  AI citations, answer engine optimization, brand presence in ChatGPT/Perplexity/Google AI
  Overviews. This skill optimizes the user's OWN content structure and distribution for
  AI-extractability. It does NOT measure actual AI citation rates — that requires direct
  AI-platform API integration (Path B).
argument-hint: "[brand name or URL] [--non-interactive] [--resume <run-id>]"
allowed-tools: Read Glob Grep Write Bash WebFetch WebSearch Agent
---

# AEO Optimizer — AI Engine Optimization Skill

Make the target brand's content more extractable, recommended, and accurately represented by AI search engines. This skill owns what you can actually *do* about AEO — reformat your content for AI extractability, fix consistency across your owned profiles, seed authoritative sources, and build co-citation patterns. It does NOT pretend to measure how often ChatGPT/Perplexity/Gemini cite you, because that measurement requires those platforms' APIs (Path B).

Traditional SEO gets a site ranked on Google. AEO gets the brand recommended by AI. When a user asks ChatGPT "What's the best project management tool?" or Perplexity "Compare CRM platforms" — AEO determines whether the brand appears, how it is described, and whether it is positioned favorably. This skill produces the content patterns and distribution plan that tend to earn those citations. Whether they actually materialize requires separate measurement.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. Opus/Sonnet should batch reference loads + multi-page content Reads + parallel WebSearch for consistency checks into parallel bursts. Haiku may follow phase order sequentially if parallel batching misbehaves.

## Execution: parallel-first

- **Phase 1 (content-structure audit)**: Glob then parallel-Read the user's content files in batches. Independent per file.
- **Phase 3 (consistency audit)**: WebSearch + WebFetch calls for each third-party profile in parallel.
- **Phase 4 (content conversion)**: Per-file rewrites are independent — batch.
- **What to serialize, always**: Phase transitions (user approval gates in interactive mode), and Phase 2 seeding-plan decisions that depend on Phase 1 findings.

## Capability Honesty

Read `references/CAPABILITIES.md` before running. Core facts:
- **You CAN** audit and rewrite the user's content structure, fix consistency across their owned profiles, generate distribution plans, add FAQ/Speakable schema, identify co-citation opportunities via WebSearch observation.
- **You CANNOT** measure the user's actual brand presence in ChatGPT/Perplexity/Gemini responses. WebSearch returns web search results, not ChatGPT's answer. Without direct AI-platform API integration, any "AI visibility score" is fabricated.
- **The honest substitute** is the Phase 1 AI-Extractability Content Linter below — it scores your *content's structural readiness* to be cited, not your actual citation rate. High extractability is a necessary but not sufficient condition for actually being cited.

## Mode Flags

- `--non-interactive` — Skip user-approval gates. Produce best-effort output, commit artifacts, emit trailing JSON with `awaiting_user_review` items.
- `--resume <run-id>` — Load `.seo/state/<run-id>.json` and continue from the last saved phase.

## Checkpoint & Resume

Save state to `.seo/state/<run-id>.json` at these transitions: after Phase 0 (crawl access gate), after Phase 1 (structure audit), after Phase 3 (consistency audit), after Phase 4 (content conversion), after Phase 5 (co-citation map), after output plan.

Checkpoint schema (shared with other rad-seo multi-phase skills):
```json
{
  "run_id": "string",
  "skill": "aeo-optimizer | full-seo-audit | competitor-intelligence | content-strategist",
  "phase": "string",
  "started_at": "ISO-8601",
  "last_saved": "ISO-8601",
  "model": "opus | sonnet | haiku",
  "target": "string — brand name or URL",
  "phase_outputs": {},
  "measurement_gaps": ["string"],
  "awaiting_user_review": ["string"]
}
```

---

## Phase 0: AI Crawl Access Gate

Before optimizing content for AI extraction, verify AI systems can fetch it at all.
Run the deterministic check (knowledge in `references/ai-crawl-access.md`):

```bash
python scripts/audit-ai-access.py --origin https://example.com --check-fetch --json
```

Gate logic:
- **Citation-class bot blocked** (OAI-SearchBot, ChatGPT-User, Claude-SearchBot/User,
  PerplexityBot/User, Bingbot, Googlebot) — via robots.txt or CDN — every later phase is
  moot for that engine. Fix access first.
- **CSR-only content** (JS-dependence finding) — AI crawlers execute zero JavaScript;
  content that only exists after hydration cannot be extracted no matter how well it's
  structured. SSR/prerender before reformatting.
- **Training-class blocks** (GPTBot, ClaudeBot, Google-Extended, CCBot) — report as a
  licensing choice; do NOT treat as an AEO problem.
- **llms.txt** — recommend with the both-truths framing from the reference: Lighthouse's
  Agentic Browsing audits recommend it and browsing agents may use it; it does not affect
  rankings or AI citations. Never promise gains from it.

---

## Phase 1: AI-Extractability Content Linter

**This replaces the fabricated "AI Visibility Scorecard" from v1.x.** Instead of pretending to query ChatGPT/Perplexity/Gemini (which WebSearch cannot actually do), this phase scores the user's own content structure on observable signals that correlate with AI citation: question headings, direct-answer leads, quotable stats, FAQ schema, comparison tables, semantic chunking.

### Inputs

Target for audit:
- User's codebase content files (preferred — direct Read)
- User's URL list (fetched via WebFetch)
- Or both

### Six Structural Dimensions

Score each page on a 0-10 scale:

| # | Dimension | Observable Signal |
|---|-----------|-------------------|
| 1 | **Question-Format Headings** | Ratio of H2s phrased as questions / total H2s |
| 2 | **Direct-Answer Leads** | First 1-2 sentences after each heading directly answer the implied question |
| 3 | **Quotable Stats / Bolded Data** | Presence of specific numbers + bold formatting or `<strong>` on key claims |
| 4 | **FAQ Schema Presence** | Valid FAQPage JSON-LD on pages with Q&A structure (an AI-parsing aid only — Google retired FAQ rich results entirely in May 2026; never promise rich-result appearance) |
| 5 | **Comparison / Structured Data** | Tables, feature matrices, pro/con lists |
| 6 | **Semantic Chunking** | Short paragraphs (2-4 sentences), logical subsection density, not wall-of-text |

### Per-Page Composite Score (0-60)

Tiers (structural readiness, NOT actual AI visibility):

| Score | Tier | Interpretation |
|-------|------|----------------|
| 0-12 | Illegible to AI | Wall-of-text, no structural signals — AI would struggle to extract anything |
| 13-24 | Partially extractable | Some structure; AI could extract a few quotes but not full answers |
| 25-36 | Extractable | Structure supports most extraction; add FAQ schema + bold stats to push higher |
| 37-48 | Highly extractable | Most signals present; content is ready for AI to cite cleanly |
| 49-60 | AI-native | Content is structurally optimal for AI extraction — actual citation depends on authority + consensus (Phases 2-8) |

### What This Score Means (and doesn't)

- **Means**: Your content is (or isn't) structurally ready for AI to cite cleanly
- **Does NOT mean**: AI is actually citing you right now
- **To measure actual citations**: Add a Path B AI-platform MCP integration (see `references/CAPABILITIES.md`)

### Per-Page Findings

For each page, identify:
- Missing question-format H2s (which sections would benefit)
- Sections that lead with preamble instead of direct answers
- Statistics that should be bolded / quotable
- Q&A sections without FAQ schema
- Comparison opportunities (tables, matrices)
- Paragraphs over 5 sentences that should be broken up

These findings become the Phase 4 conversion queue.

**Evidence basis:** the strongest published result on generative-engine visibility
(Princeton GEO study, KDD 2024, ~10k queries) found that adding **statistics,
quotations, and source citations** lifted visibility ~30-40%, while keyword stuffing did
nothing — which is why dimensions 2-3 weight direct answers and quotable data. Industry
citation studies converge on the same signals plus freshness and self-contained chunks
(AI Mode retrieves at passage level via query fan-out, not page level).

---

## Phase 2: LLM Seeding Strategy

AI models learn from the open web. Control where and how brand information appears to influence what LLMs absorb.

### WHERE to Publish (Source Priority)

Publish brand-relevant content on these platforms, ordered by observed LLM training influence (exact weight varies by model and version, but the relative order is well-observed):

| Priority | Platform | Why It Matters | Action |
|----------|----------|---------------|--------|
| 1 | **The Brand Website** | Primary source of truth. Must be crawlable, well-structured, fast. | Ensure clean HTML, proper schema markup, no JS-only rendering. |
| 2 | **Wikipedia / Wikidata** | High-authority factual source for most LLMs. | Create or improve the Wikipedia page (only if notability criteria are met). Add Wikidata entity. |
| 3 | **Reddit** | Heavily weighted in many LLM training corpora. Authentic discussions. | Engage genuinely in relevant subreddits. Never astroturf. |
| 4 | **Stack Overflow / Quora** | Q&A format is ideal for LLM extraction. | Answer questions where your product is genuinely the solution. |
| 5 | **Medium / Substack / LinkedIn** | Long-form platforms LLMs crawl regularly. | Publish thought leadership, case studies, tutorials. |
| 6 | **Industry Publications** | Authoritative third-party validation. | Guest posts, contributed articles, expert commentary. |
| 7 | **Review Platforms** (G2, Trustpilot, Capterra) | LLMs use reviews for sentiment and feature extraction. | Actively collect reviews. Respond to all reviews. |
| 8 | **GitHub** | Critical for developer/technical products. | Maintain active repos, quality READMEs, community engagement. |
| 9 | **News Sites** | Recency signal. LLMs with web access pull recent news. | Digital PR, press releases, newsworthy launches. |

### WHAT Content Format to Use

These content formats tend to be disproportionately extracted and cited by LLMs:

**1. Structured "Best Of" Lists** — Always include testing methodology to establish authority.

**2. Comparison Tables** — LLMs extract tabular data cleanly.

**3. FAQ-Style Content** — Q&A is training data gold:
```markdown
## What is [Brand]?
[Brand] is [direct 1-sentence definition]. It [key differentiator].

## How much does [Brand] cost?
[Brand] pricing starts at [price] for [tier]. [Additional detail].

## How does [Brand] compare to [Competitor]?
[Brand] excels at [strengths] while [Competitor] is better for [their strengths].
```

**4. Original Data and Statistics** — Make statistics bold and quotable:
> **"X% of teams using [Brand] reported a Y improvement in [metric]"**
(Only publish numbers you've actually measured. Fabricated statistics damage long-term authority.)

**5. Free Tools, Calculators, Templates** — Utility content earns natural mentions and links.

**6. Branded Strategies with Memorable Names** — Coin a methodology with a name. Example: "The RAPID Framework for Content Optimization." LLMs remember named frameworks.

---

## Phase 3: Consensus and Consistency Audit

AI models recommend brands when multiple independent sources agree on the same facts. Inconsistency creates uncertainty, and uncertain LLMs hedge or omit.

### Sources to Audit (parallel WebSearch + WebFetch)

Check that the following information is identical across all platforms:

| Data Point | Sources to Check |
|-----------|-----------------|
| Company name and spelling | Website, social profiles, directories, Wikipedia |
| Founding date | About page, Crunchbase, LinkedIn, Wikipedia |
| Product description | Homepage, G2, Capterra, LinkedIn, press releases |
| Pricing | Pricing page, G2, Capterra, review sites |
| Feature list | Product pages, comparison sites, documentation |
| Leadership / founders | About page, LinkedIn, Crunchbase, press mentions |
| Company size / metrics | About page, LinkedIn, Crunchbase, press releases |
| Contact information | Website, Google Business, directories |
| Category / industry | All profiles and listings |

### Fix Protocol

For every inconsistency found:
1. Determine the **canonical truth** (usually your website)
2. Update every third-party profile you control to match
3. Submit corrections to platforms you don't control
4. Re-audit periodically to verify propagation

---

## Phase 4: AI-Friendly Content Conversion

Transform existing content so LLMs can extract clean, quotable answers. Queue comes from Phase 1 findings.

### Conversion Rules

**Rule 1: Convert H2 Headings to Question Format**
```
BEFORE: ## Our Pricing Plans
AFTER:  ## How Much Does [Brand] Cost?
```

**Rule 2: Lead Every Section with a Direct Answer**
```
BEFORE:
## How Much Does Acme Cost?
When it comes to choosing the right plan, there are many factors to consider.
Our flexible pricing is designed to scale with your needs...

AFTER:
## How Much Does Acme Cost?
Acme costs $29/month for individuals and $99/month for teams of up to 10.
Enterprise pricing starts at $499/month with custom configuration.
```

**Rule 3: Make Statistics Bold and Quotable**
```
**Acme processes over 2 million requests per day with 99.97% uptime.**
```
(Only publish numbers you can actually verify.)

**Rule 4: Add FAQ Schema Markup** — generate valid FAQPage JSON-LD for any Q&A content.

**Rule 5: Build Comparison Tables** for pricing, features, brand-vs-competitor.

**Rule 6: Use Semantic Chunking** — paragraphs 2-4 sentences, descriptive headings, bulleted lists for features, numbered lists for steps.

**Rule 7: Add Speakable Schema** for voice-assistant content:
```json
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".summary", ".key-answer", ".product-description"]
  }
}
```

### Conversion Commands

```bash
# Audit a page for AI-extractability
claude "Read [URL/FILE] and score it for AI extractability using the Phase 1 six
        dimensions. Check: heading format, answer directness, quotable stats,
        schema markup, paragraph length, and semantic structure. Provide specific rewrites."

# Bulk convert headings to question format
claude "Scan all content files in [DIRECTORY]. Convert every H2 that isn't a
        question into question format. Preserve meaning."

# Add FAQ schema to existing content
claude "Read [FILE] and generate FAQPage schema markup based on the existing Q&A
        content. Output the JSON-LD script tag."
```

---

## Phase 5: Co-Citation Strategy

LLMs associate brands that appear together frequently. Get the target brand mentioned alongside industry leaders to inherit authority signal.

### Tactics

1. **Publish Comparison Content** — "[Brand] vs [Leader]: [Specific Differentiator]"
2. **Earn Roundup Mentions** — Target "best of" and "top tools" articles with a clear inclusion angle
3. **Participate in Industry Panels and Podcasts** — Transcripts get crawled
4. **Get Listed in Curated Directories** — Industry-specific tool directories, awesome-lists on GitHub
5. **Engage on Reddit and Quora** — Provide genuinely helpful answers mentioning the product with honest trade-offs
6. **Joint Content and Integrations** — Co-publish with complementary (non-competing) established brands

### Co-Citation Observation Command

```bash
claude "Search for '[BRAND]' and identify which other brands it is most
        frequently mentioned alongside in review sites and comparison articles.
        Map the observable co-citation network. Identify gaps where [BRAND]
        should appear but doesn't. Note: this is observable from WebSearch —
        NOT a measurement of what AI chat engines actually say, which would
        require direct platform API integration."
```

For detailed phase-by-phase execution steps for Phases 6-8, consult `references/aeo-phases.md`.

---

## Phase 6: Platform-Specific Optimization

Each AI platform has different data sources and ranking signals. Optimize for Google AI Overviews (structured data + top-10 rankings), ChatGPT (high-authority factual sources + Reddit + training data), Perplexity (real-time web search + citations), Claude (depth + original research), and Microsoft Copilot (Bing index + social signals).

For detailed platform-by-platform signal tables and audit commands, consult `references/aeo-phases.md`.

---

## Phase 7: Visual Optimization for AI

Optimize visuals for AI interpretation: real product screenshots, descriptive full-sentence captions, keyword-rich alt text, infographics with embedded text, video transcripts.

For detailed image optimization rules and code examples, consult `references/aeo-phases.md`.

---

## Phase 8: Distribution and Seeding Plan

Systematic content distribution to maximize AI training data coverage across UGC platforms, digital PR, affiliate/review coverage, expert quote placement, and content syndication.

For detailed distribution tactics and platform-specific strategies, consult `references/aeo-phases.md`.

---

## Output: AEO Action Plan

After completing all phases, generate a prioritized action plan organized by time horizon.

### Quick Wins (Week 1-2)
0. **Unblock AI access** (Phase 0) — allow citation-class bots in robots.txt and the CDN's bot settings; SSR any CSR-only key pages
1. **Fix consistency issues** (Phase 3) — update all profiles to match canonical information
2. **Add FAQ schema** to existing high-traffic pages
3. **Reformat top 5 pages** using Phase 4 conversion rules
4. **Update image alt text and captions** per Phase 7
5. **Claim and optimize** unclaimed business profiles on review platforms
6. **Add Speakable schema** to homepage and product pages
7. **Fix any inconsistencies** that make LLMs hedge

### Medium-Term (Month 1-3)
1. **Create 10 FAQ-style pages** targeting questions AI is asked in the category
2. **Publish 3 comparison pages** with honest, detailed analysis
3. **Write an original research piece** with verified quotable statistics
4. **Build genuine Reddit presence** in 5 relevant subreddits
5. **Publish 5 guest articles** on industry publications and high-authority platforms
6. **Create or improve Wikipedia page** (if notability criteria are met)
7. **Launch a branded framework or methodology** with a memorable name
8. **Build comparison tables** for all product/pricing pages

### Long-Term (Month 3-12)
1. **Publish quarterly industry reports** with original verified data
2. **Execute co-citation strategy** (joint content, roundup targeting, integration partnerships)
3. **Build and maintain UGC presence** across Reddit, Quora, and forums
4. **Launch digital PR campaign** targeting AI-crawled publications
5. **Create free tools/calculators** that earn natural mentions
6. **Establish expert quote pipeline** via HARO/Connectively
7. **Re-run the Phase 1 extractability audit quarterly** — track structural score improvement
8. **If Path B AI-platform MCP becomes available**: start measuring actual citation rates

---

## Output JSON (for --non-interactive)

```json
{
  "aeo_complete": true,
  "run_id": "string",
  "target": "string",
  "phase_1_extractability": {
    "pages_audited": 0,
    "avg_score": 0,
    "tier": "illegible | partially | extractable | highly | ai_native",
    "conversion_queue_size": 0
  },
  "phase_3_consistency": {
    "sources_checked": 0,
    "inconsistencies_found": 0
  },
  "phase_4_conversions": {
    "pages_rewritten": 0
  },
  "action_plan_path": "string",
  "measurement_gaps": [
    "actual AI citation rates require Path B AI-platform API integration",
    "brand sentiment scoring across AI chat responses requires direct platform APIs",
    "accuracy measurement of AI responses requires querying each AI chat interface directly"
  ],
  "escalation_required": false,
  "awaiting_user_review": ["string"]
}
```

## Measurement and Re-Audit

Track AEO progress with:
- **Monthly**: Re-run the Phase 1 content-extractability audit on new/updated pages. Track structural-readiness score trend.
- **Quarterly**: Full skill re-run. Compare phase-by-phase progress.
- **If actual AI citation measurement matters**: integrate a Path B AI-platform MCP (see `references/CAPABILITIES.md`). Without that, you're measuring structural readiness to be cited, not actual citations.

**Metrics you CAN track:**
- Phase 1 avg extractability score over time
- Number of pages with FAQ schema
- Number of consistency issues remaining
- Content volume published on priority distribution channels

**Metrics you CANNOT track without Path B:**
- Actual mentions in ChatGPT / Perplexity / Gemini / Copilot answers
- First-mention rate
- Accuracy of AI responses
- Sentiment of AI responses

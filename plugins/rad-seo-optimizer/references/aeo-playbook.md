# AEO/GEO Playbook: Dominating AI Search

Generative Engine Optimization (GEO) — also called Answer Engine Optimization (AEO) — is the practice of optimizing content to appear in AI-generated answers on ChatGPT, Perplexity, Claude, Google AI Overviews, and other AI search platforms.

## The Fundamental Shift

Traditional SEO optimizes for clicks from a results page. AEO optimizes for **citations** in AI-generated responses. The goal is no longer just to win a click — it's to earn a citation and influence what AI tools say about your brand.

## Core AEO Frameworks

### 1. LLM Seeding
Publish content in the specific formats and places that LLMs are most likely to scrape, summarize, and cite.

**Where LLMs look:**
- Your website (if well-structured and crawlable)
- Wikipedia and Wikidata
- Reddit, Quora, Stack Overflow (UGC hubs)
- Medium, Substack, LinkedIn articles
- Industry publications and news sites
- GitHub (for technical products)
- Review platforms (G2, Trustpilot, Capterra)
- Government and educational (.gov, .edu) sites

**What to publish:**
- Structured "Best Of" lists with explicit testing methodology
- Comparison tables with brand-vs-brand verdicts
- FAQ-style content (Q&A is LLM training data gold)
- Original data, statistics, and research
- Free tools, calculators, and templates (citation magnets)
- Branded strategies with memorable names (creates citable entities)

### 2. Consensus & Consistency
AI models recommend brands when they find **consensus** (multiple sources agree) and **consistency** (information matches across the web).

**Consensus audit checklist:**
- [ ] Brand mentioned positively on 3+ independent review platforms
- [ ] Product details match exactly across your site, social profiles, and third-party listings
- [ ] Pricing, features, and capabilities are consistent everywhere
- [ ] Industry publications or experts have mentioned/endorsed the brand
- [ ] User-generated reviews exist on multiple platforms

**Consistency audit checklist:**
- [ ] Business name, address, phone (NAP) identical everywhere
- [ ] Product descriptions don't contradict across platforms
- [ ] Feature lists are up-to-date on all third-party profiles
- [ ] No outdated pricing or deprecated features mentioned anywhere
- [ ] Social media profiles are active and aligned with website messaging

### 3. Co-Citation Strategy
Get your brand mentioned alongside established industry leaders. AI models learn entity relationships from co-occurrence patterns.

**Tactics:**
- Publish comparison content: "Brand X vs. [Your Brand] vs. Industry Leader"
- Earn mentions in roundup articles alongside competitors
- Participate in industry panels, podcasts, and conferences where leaders are present
- Get listed in the same "best of" lists as recognized players
- Engage in forums where industry leaders are discussed

## AI-Friendly Content Formatting

### Semantic Chunking
Break content into easily digestible sections that AI can extract independently:
- Use descriptive H2/H3 headings that read as complete questions or statements
- Keep paragraphs short (2-4 sentences max)
- Lead each section with a direct, concise answer before expanding
- Use logical transitions between sections

### Quotable Statements
Include clear, bold statements that AI systems can instantly extract:
- Statistics with specific numbers: "Companies using X saw a 47% increase in Y"
- Definitive claims: "X is the most effective method for Y because..."
- Named frameworks: "The Three-Pillar Approach to..."
- Observation: pages with direct quotes and specific statistics tend to be cited more often by AI systems. The exact lift varies by niche and measurement methodology — treat as directional, not as a specific measured rate.

### FAQ-Style Headings
Format subheadings as actual customer questions:
- "What is [topic]?" followed by a direct 1-2 sentence answer
- "How does [product] compare to [competitor]?" with structured comparison
- "When should you use [method]?" with clear use-case scenarios

### Schema Markup for AI
Implement structured data that explicitly tells AI what your content means (parsing
aids — Google requires no special schema for AI features, and FAQ/HowTo rich results
are retired):
- FAQ schema on question-answering pages
- HowTo schema on tutorial/guide pages
- Product schema with complete specifications
- Organization schema with full business details
- Review/Rating schema with aggregate data

## Platform-Specific Optimization

### Google AI Overviews
- Already uses your indexed content — focus on being in top 10 results (~75% of AI
  Overview citations overlap with top-10 rankings per industry studies)
- Google's official guidance: NO special markup or schema is required for AI features —
  standard indexability governs inclusion; AI Mode retrieves passage-level chunks via
  query fan-out, so self-contained answer-first sections matter most
- "Speakable" schema marks content as suitable for voice/AI reading

### ChatGPT / OpenAI
- Training data includes web content, Wikipedia, Reddit, academic papers
- Browse/search plugins pull real-time web results
- Optimize for clear, authoritative, well-structured content
- Being cited in Wikipedia dramatically increases ChatGPT visibility

### Perplexity AI
- Real-time web search — your current content matters
- Heavily cites structured, well-organized pages
- Sources with clear author attribution rank higher
- Comparison and "best of" content is frequently cited

### Claude / Anthropic
- Training data includes diverse web sources
- Values well-reasoned, nuanced content over keyword-stuffed pages
- Original analysis and expert insights are weighted heavily
- Web search integration pulls current results

## The AEO Content Optimization Checklist

### Content Structure
- [ ] H2 headings formatted as questions users would ask
- [ ] Each section leads with a direct, concise answer (1-2 sentences)
- [ ] Short paragraphs (2-4 sentences)
- [ ] Bullet points and numbered lists for scannable data
- [ ] Comparison tables for product/feature evaluations
- [ ] Original statistics or data points (citation magnets)

### Entity Optimization
- [ ] Brand name used consistently (exact same format everywhere)
- [ ] Product/service names are specific and unique
- [ ] Branded methodology or framework names exist
- [ ] Organization schema markup is implemented
- [ ] Author entities are well-defined with Person schema

### Distribution Strategy
- [ ] Content published on your site (primary source of truth)
- [ ] Key insights reshared on Medium, LinkedIn, Substack
- [ ] Helpful answers posted on Reddit and Quora (non-promotional)
- [ ] Expert quotes earned in industry publications (HARO/Connectively)
- [ ] Affiliate/review programs encourage third-party coverage
- [ ] Official records (licenses, certifications) explicitly listed on site

### Visual Optimization for AI
AI models increasingly use image processing (CLIP) to understand visuals:
- [ ] Real in-product screenshots (not stock photos)
- [ ] Descriptive, full-sentence image captions
- [ ] Keyword-rich alt text that describes the image content
- [ ] Infographics with embedded text that AI can parse
- [ ] Video content with accurate transcripts

### Monitoring & Measurement

**Honest framing**: actual AI citation tracking requires direct AI-platform API integration (Path B — see `CAPABILITIES.md`). Without that, the best available proxies are:

- [ ] **Manual spot-checks** — manually query ChatGPT / Perplexity / Gemini with target questions, screenshot results, compare over time. Labor-intensive but real.
- [ ] **Google Search Console AI Overview impressions** — GSC reports AI Overview impressions for your own site. Requires the user's own GSC integration.
- [ ] **Referral traffic from AI platforms** — server log analysis or GA4 for `referrer=perplexity.ai`, `referrer=chat.openai.com`, etc. Captures users who clicked through from an AI citation.
- [ ] **Re-run the AI-Extractability Content Linter** (`aeo-optimizer` Phase 1) on your content quarterly — tracks your *structural readiness to be cited*. This is NOT the same as measured citations; high extractability is necessary but not sufficient for actual citation.
- [ ] **Consistency audit** (`aeo-optimizer` Phase 3) — re-run to verify your canonical info stays consistent across platforms.

## The Retired 6-Dimension AEO Scorecard

The original v1.x of this plugin claimed to score brands across six dimensions (Presence / Accuracy / Sentiment / Position / Completeness / Consistency) by querying AI platforms via WebSearch. **That scorecard was retired in v2.0 because WebSearch returns web search results, NOT ChatGPT/Perplexity/Gemini responses — the scoring was measuring something it couldn't actually measure.**

What replaced it (see `skills/aeo-optimizer` Phase 1): the **AI-Extractability Content Linter**, which scores the user's own content structure on signals that tend to earn AI citations — question-format headings, direct-answer leads, quotable stats, FAQ schema, comparison tables, semantic chunking. This is a *measurement of your content's readiness to be cited*, not a measurement of *actual citations*.

For real citation measurement, integrate an AI-platform API MCP (Path B). Until then, the content linter + manual spot-checks are the honest baseline.

# AEO Optimizer — Detailed Phase Execution Steps

This reference contains the detailed execution steps for Phases 6-8 of the AEO Optimizer skill.

---

## Phase 6: Platform-Specific Optimization

Each AI platform has different data sources and ranking signals. Optimize for each individually.

### Google AI Overviews

Google AI Overviews pull from top-ranking search results and structured data.

| Signal | Action |
|--------|--------|
| Search ranking | The site must rank in top 10 for target queries (traditional SEO still matters) |
| Structured data | Implement Product, Review, and Organization schema (Google: no special schema is *required* for AI features; FAQPage/HowTo are parsing aids only — their rich results are retired) |
| Content freshness | Update key pages quarterly with current data |
| E-E-A-T signals | Author bios, credentials, cited sources, methodology |
| Direct answers | First paragraph must answer the query in 1-2 sentences |

**Audit checklist:** Check search ranking for target keywords, structured data implementation, content freshness date, author attribution, and direct-answer formatting in the first paragraph.

### ChatGPT

ChatGPT relies on training data (with a knowledge cutoff) plus web browsing. Heavy Wikipedia and Reddit influence.

| Signal | Action |
|--------|--------|
| Wikipedia presence | Create or improve the Wikipedia article with citations |
| Reddit mentions | Genuine engagement in relevant subreddits |
| Structured content | Clean HTML, clear headings, extractable facts |
| Consistent facts | Same information across all sources ChatGPT might access |
| Recency (browsing) | Fresh content on crawlable pages for browsing-enabled queries |

**Audit checklist:** Check if the brand has a Wikipedia page. If yes, audit for accuracy and completeness. If no, assess notability criteria and draft a neutral, well-sourced article outline.

### Perplexity AI

Perplexity performs real-time web search and cites sources directly. Quality and structure matter most.

| Signal | Action |
|--------|--------|
| Content quality | Well-written, factual, comprehensive content |
| Author attribution | Clear author names, bios, and credentials on content |
| Page structure | Clean headings, short paragraphs, extractable answers |
| Source diversity | Multiple authoritative pages about the brand |
| Recency | Recently published or updated content ranks higher |

**Audit checklist:** Search Perplexity for target queries and analyze: Is the brand cited? Which sources are used? What content format do cited pages use? Identify what the brand's content needs to match.

### Claude

Claude values nuanced, well-reasoned content over keyword density.

| Signal | Action |
|--------|--------|
| Depth of analysis | Publish genuinely insightful, non-obvious content |
| Original research | Unique data, case studies, and first-party findings |
| Balanced perspective | Acknowledge trade-offs honestly (builds trust signal) |
| Technical accuracy | Precise, verifiable claims with methodology |
| Clean writing | Well-structured prose, not keyword-stuffed SEO content |

### Microsoft Copilot / Bing Chat

Copilot uses Bing's index. Bing SEO signals apply.

| Signal | Action |
|--------|--------|
| Bing ranking | Optimize for Bing (social signals matter more than on Google) |
| Social proof | Active social media profiles linked from the site |
| Schema markup | Full structured data implementation |
| Bing Webmaster Tools | Submit the sitemap, monitor indexing |

---

## Phase 7: Visual Optimization for AI

Modern AI models process images using vision models (CLIP and similar). Optimize visuals for AI interpretation.

### Image Optimization Rules

**1. Use Real Product Screenshots**
AI models can identify and describe UI screenshots. Use actual in-product images rather than stock photography.

**2. Write Descriptive Full-Sentence Captions**
```html
<!-- BEFORE -->
<figcaption>Dashboard</figcaption>

<!-- AFTER -->
<figcaption>[Brand]'s analytics dashboard showing real-time conversion
tracking, revenue attribution, and campaign performance metrics.</figcaption>
```

**3. Write Keyword-Rich Alt Text**
```html
<img src="dashboard.png"
     alt="[Brand] analytics dashboard displaying conversion rates,
          revenue by channel, and A/B test results for e-commerce campaigns">
```

**4. Create Infographics with Embedded Text**
AI vision models read text in images. Infographics with statistics, process flows, and branded data are extractable by multimodal LLMs.

**5. Add Video Transcripts**
Every video should have an accurate, timestamped transcript. AI cannot watch video but can read transcripts.

**Audit checklist:** Check all images for alt text quality, caption descriptiveness, image relevance, and whether real product screenshots are used vs stock photos. Generate improved alt text and captions for each image.

---

## Phase 8: Distribution and Seeding Plan

Systematic content distribution to maximize AI training data coverage.

### UGC Hub Strategy

Build organic brand mentions in user-generated content platforms:

- **Reddit**: Identify 5-10 relevant subreddits. Contribute value for 30+ days before any brand mentions. Answer questions where the product genuinely helps. Never create fake accounts or astroturf.
- **Quora**: Answer high-traffic questions in the target category. Provide detailed, expert answers. Mention the product only when directly relevant.
- **Industry Forums**: Identify niche forums in the vertical. Become a recognized contributor.
- **Discord/Slack Communities**: Join relevant communities. Be helpful first. Product mentions come naturally.

### Digital PR for AI Citation Earning

Traditional PR now serves double duty: human readers and AI training data.

- Publish data-driven press releases with quotable statistics.
- Create annual industry reports that journalists and AI will reference.
- Pitch stories to publications that AI platforms crawl (major news, tech press, industry publications).
- Distribute via newswires that feed into multiple databases.

### Affiliate and Review Coverage

- Launch or optimize an affiliate program to incentivize honest review content.
- Send product access to review creators on YouTube, blogs, and podcasts.
- Make reviewer onboarding frictionless (dedicated landing pages, press kits).
- Respond publicly to all reviews (positive and negative).

### Expert Quote Placement

- Use HARO (Help a Reporter Out) / Connectively / Quoted to place expert quotes in articles.
- Offer expert commentary to journalists covering the industry.
- Create a spokesperson page on the site with ready-to-use quotes and bios.

### Content Syndication

Republish and syndicate content to AI-crawled platforms:
- Syndicate blog posts to Medium, LinkedIn, and industry publications (with canonical tags).
- Repurpose long-form content into Twitter/X threads, LinkedIn carousels, and short-form video transcripts.
- Submit content to aggregators and newsletters in the vertical.

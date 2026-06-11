---
name: on-page-optimizer
description: >
  Optimize this page, title tags, meta descriptions, heading structure, E-E-A-T, on-page
  SEO, content quality score — single page optimization. Covers title tags, meta, headings,
  keyword usage, E-E-A-T signals, and image alt text. Real code transforms over the user's
  content — no Path B dependencies.
argument-hint: "[URL or page to optimize] [--non-interactive]"
allowed-tools: Read Glob Grep Write Bash WebFetch
---

# On-Page SEO + E-E-A-T Optimizer

Analyze and optimize individual pages for search visibility, content quality, and E-E-A-T compliance. Every issue includes a Claude Code fix command. This skill works directly on the user's content files — no external measurement infrastructure required.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. Per-page rewrites are independent; batch across pages in parallel when auditing multiple pages.

## Execution: parallel-first

- **Multi-page audits**: Reads across pages independent — batch
- **Per-page rewrites**: each section's audit independent (title, meta, headings, alt text) — batch within a page
- **WebFetch for URL-based audit**: parallel per URL

---

## 1. Title Tag Optimization

### Rules

| Criterion              | Requirement                                              |
|------------------------|----------------------------------------------------------|
| Length                  | 50-60 characters (Google truncates at ~60)               |
| Primary keyword         | Front-loaded in the first 3-5 words                      |
| Uniqueness             | No duplicate titles across the site                      |
| Emotional modifiers    | Include power words or numbers ("Best", "2026", "Guide") |
| Brand name             | Appended at end, separated by ` | ` or ` - `            |

### Audit Checklist

1. Measure character count. Flag if < 50 or > 60.
2. Confirm the primary keyword appears within the first 30 characters.
3. Compare against all other `<title>` tags on the site for duplicates.
4. Check for a modifier word or current year.
5. Verify brand name placement (end position, after separator).

### Before / After

```
BEFORE  <title>Our Services</title>
AFTER   <title>Professional SEO Services for Small Business | Acme</title>
```

```
BEFORE  <title>Blog Post About Running Shoes</title>
AFTER   <title>Best Running Shoes for Flat Feet in 2026 - RunGear</title>
```

### Fix Commands

```bash
# Replace a title tag in an HTML file
claude "In index.html, change the <title> to 'Best Running Shoes for Flat Feet in 2026 - RunGear'. Keep it under 60 characters with the primary keyword front-loaded."

# Audit all title tags across the site for duplicates and length
claude "Scan every HTML file in ./src/pages/. List each <title> with its character count. Flag any duplicates or titles outside the 50-60 character range."
```

---

## 2. Meta Description Optimization

### Rules

| Criterion       | Requirement                                        |
|-----------------|----------------------------------------------------|
| Length           | 150-160 characters                                 |
| Target keyword  | Included naturally, not forced                     |
| CTA / benefit   | Clear call-to-action or value proposition          |
| Uniqueness      | One unique description per page                    |

### Audit Checklist

1. Measure character count. Flag if < 150 or > 160.
2. Confirm the target keyword appears at least once.
3. Check for an action verb or benefit statement.
4. Compare against all other meta descriptions for duplicates.

### Before / After

```
BEFORE  <meta name="description" content="Welcome to our website.">
AFTER   <meta name="description" content="Discover 12 proven local SEO strategies that drive foot traffic in 2026. Free checklist included — start ranking higher today.">
```

```
BEFORE  <meta name="description" content="We sell shoes online. Check out our store for great deals on shoes.">
AFTER   <meta name="description" content="Shop top-rated running shoes for flat feet with free returns. Compare 50+ models and find your perfect fit in under 2 minutes.">
```

### Fix Commands

```bash
# Rewrite a meta description
claude "Rewrite the meta description in /src/pages/local-seo.html to be 150-160 characters, include the keyword 'local SEO strategies', and end with a clear CTA."

# Bulk audit meta descriptions
claude "Check every HTML file under ./src/pages/ for meta descriptions. Report character count, missing keywords, and any duplicates in a markdown table."
```

---

## 3. Heading Structure

### Rules

| Criterion              | Requirement                                                      |
|------------------------|------------------------------------------------------------------|
| H1 count               | Exactly one per page                                             |
| H1 content             | Contains the primary keyword                                     |
| Hierarchy              | Logical H2-H6 nesting, no skipped levels (e.g., H2 then H4)    |
| H2 format              | Section summaries or questions (AEO-friendly)                    |
| Keyword distribution   | Spread naturally across H2-H3 headings                           |
| Paragraphs per heading | 2-4 sentences under each heading for readability                 |

### Audit Checklist

1. Count H1 tags. Flag if count != 1.
2. Verify the primary keyword appears in the H1.
3. Walk the heading tree; flag any level skip (e.g., H2 -> H4).
4. Check that at least 2 of the H2s are phrased as questions.
5. Confirm paragraphs beneath headings are 2-4 sentences long.

### Before / After

```
BEFORE
  <h1>Welcome</h1>
  <h3>Our Services</h3>        <!-- skipped H2 -->
  <h3>Contact Us</h3>

AFTER
  <h1>Affordable SEO Services for Small Businesses</h1>
  <h2>What SEO Services Do Small Businesses Need?</h2>
  <h3>Technical SEO Audits</h3>
  <h3>Content Strategy</h3>
  <h2>How Much Does Small Business SEO Cost?</h2>
```

### Fix Commands

```bash
# Fix heading hierarchy
claude "In /src/pages/services.html, restructure headings so there is exactly one H1 with the keyword 'SEO services', H2s as questions, and no skipped heading levels."

# Audit heading structure across all pages
claude "Scan all HTML files in ./src/pages/. For each file, list the heading hierarchy (H1-H6) and flag: multiple H1s, skipped levels, or missing keywords in H1."
```

---

## 4. Content Quality Scoring

Score each page on a **0-100 scale** using six dimensions. Each dimension is worth up to
~17 points. A page scoring below 70 needs improvement; below 50 is critical.

| Dimension        | Weight | What to Evaluate                                               |
|------------------|--------|----------------------------------------------------------------|
| Depth            | 17     | Covers the topic comprehensively; no obvious gaps              |
| Originality      | 17     | Unique insights, proprietary data, or fresh perspectives       |
| Readability      | 17     | Short paragraphs, bullet lists, visuals, clear language        |
| Intent match     | 17     | Satisfies the search intent for the target keyword             |
| Freshness        | 16     | Information is current; published/updated dates are visible    |
| Keyword usage    | 16     | Natural placement at 1-2% density; no stuffing                 |

### Audit Checklist

1. **Depth** -- Compare word count and subtopics against the top 5 ranking pages.
2. **Originality** -- Flag if content closely paraphrases competitor pages with no new data.
3. **Readability** -- Paragraphs > 4 sentences? Missing lists or visuals? Flag them.
4. **Intent match** -- Identify the keyword's intent (informational, transactional, navigational)
   and verify the page format matches.
5. **Freshness** -- Check for a visible published or "last updated" date. Flag if older than
   12 months or missing entirely.
6. **Keyword usage** -- Calculate keyword density. Flag if < 0.5% (under-optimized) or
   > 2.5% (stuffing).

### Fix Commands

```bash
# Score a page's content quality
claude "Analyze /src/pages/guide.html for content quality. Score it 0-100 across depth, originality, readability, intent match, freshness, and keyword usage. Show the breakdown and specific improvement actions."

# Fix keyword density
claude "In /src/pages/guide.html, the keyword 'email marketing' appears at 0.3% density. Add 4-6 natural mentions in existing paragraphs to reach 1-1.5% density without stuffing."

# Improve readability
claude "In /src/pages/guide.html, break any paragraph longer than 4 sentences into shorter ones. Add bullet lists where 3+ items are listed in prose."
```

---

## 5. E-E-A-T Assessment

Reference: `eeat-checklist.md` for the full scoring rubric.

### The Four Pillars

| Pillar             | Key Signals                                                        |
|--------------------|--------------------------------------------------------------------|
| **Experience**     | First-hand evidence: personal photos, case studies, "I tested"     |
| **Expertise**      | Author credentials visible: bio, qualifications, certifications    |
| **Authoritativeness** | Site recognition: awards, media mentions, backlink profile       |
| **Trustworthiness**   | HTTPS, accurate info, transparency, clear contact details        |

### Audit Checklist

1. **Author bio** -- Confirm every article has an author bio with name, credentials, photo,
   and links to professional profiles.
2. **About Us page** -- Verify it exists, describes the organization's mission, and lists
   team credentials.
3. **Citations** -- At least 3 outbound links to authoritative sources per 1,000 words.
4. **Dates** -- Published and "last updated" dates are visible on every content page.
5. **YMYL check** -- If the page covers health, finance, legal, or safety topics, apply
   heightened standards: medical review, professional credentials, disclaimers.
6. **Experience signals** -- Look for original photos, screenshots, personal anecdotes,
   or case study data that prove first-hand experience.
7. **Trust signals** -- HTTPS active, privacy policy linked, contact page accessible,
   no deceptive ads or popups.

### Before / After

```
BEFORE
  <p>This supplement helps with weight loss.</p>

AFTER
  <p>After testing this supplement for 90 days and tracking my results weekly,
  I lost 8 pounds. Below are my before-and-after photos and full bloodwork
  comparison.</p>
  <p><em>Reviewed by Dr. Jane Smith, MD, Board-Certified Nutritionist</em></p>
  <p>Sources: <a href="https://pubmed.ncbi.nlm.nih.gov/...">PubMed study</a>,
  <a href="https://www.niddk.nih.gov/...">NIH guidelines</a></p>
  <p><small>Last updated: March 2026</small></p>
```

### Fix Commands

```bash
# Add author bio schema
claude "Add an author bio section to /src/pages/guide.html with name, credentials, photo placeholder, and Person schema markup. Place it below the article title."

# Add citations
claude "In /src/pages/health-tips.html, find every factual claim without a source and add an appropriate citation link to an authoritative domain (.gov, .edu, or peer-reviewed)."

# Add published/updated dates
claude "Add a visible 'Published' and 'Last Updated' date to every HTML file in ./src/pages/ that currently lacks one. Use a <time> element with datetime attribute."

# YMYL compliance check
claude "Scan /src/pages/financial-advice.html for YMYL compliance. Flag missing professional credentials, absent disclaimers, unverified claims, and suggest specific fixes."
```

---

## 6. Image Optimization

### Rules

| Criterion         | Requirement                                                   |
|-------------------|---------------------------------------------------------------|
| Alt text          | Descriptive, includes keyword where natural (max 125 chars)   |
| Dimensions        | Explicit `width` and `height` attributes (prevents CLS)       |
| Format            | WebP primary with `<picture>` fallback to JPEG/PNG            |
| Lazy loading      | `loading="lazy"` on all below-fold images                     |
| Original images   | Prefer original photos/screenshots over stock (E-E-A-T)      |
| File names        | Descriptive, hyphenated (e.g., `seo-audit-dashboard.webp`)   |

### Before / After

```html
BEFORE
  <img src="IMG_3847.jpg">

AFTER
  <picture>
    <source srcset="seo-audit-dashboard.webp" type="image/webp">
    <img src="seo-audit-dashboard.jpg"
         alt="SEO audit dashboard showing a 92 content quality score"
         width="800" height="450"
         loading="lazy">
  </picture>
```

### Fix Commands

```bash
# Add missing alt text
claude "Find every <img> in /src/pages/ missing an alt attribute. Add descriptive alt text that includes the page's target keyword where natural. Keep each under 125 characters."

# Add width/height to prevent CLS
claude "In /src/pages/guide.html, find all <img> tags missing width or height attributes. Read the actual image dimensions and add them."

# Convert to WebP with fallback
claude "For every <img> in /src/pages/blog.html, wrap it in a <picture> element with a WebP <source> and the original format as fallback. Update src filenames to be descriptive and hyphenated."

# Add lazy loading
claude "Add loading='lazy' to every <img> tag in ./src/pages/ that is NOT the first image on the page (first image should be eager for LCP)."
```

---

## 7. Internal Link Optimization

### Rules

| Criterion               | Requirement                                              |
|-------------------------|----------------------------------------------------------|
| Links per page          | At least 3 contextual internal links                     |
| Anchor text             | Descriptive and keyword-relevant (never "click here")    |
| Pillar-cluster linking  | Supporting pages link up to their pillar page             |
| Broken links            | Zero broken internal links                               |

### Audit Checklist

1. Count internal links per page. Flag any page with fewer than 3.
2. List all anchor text. Flag generic text ("click here", "read more", "this page").
3. Verify every supporting page links to its pillar/hub page.
4. Crawl all internal hrefs and flag any returning 404.

### Before / After

```html
BEFORE
  <p>We also offer other services. <a href="/services">Click here</a> to learn more.</p>

AFTER
  <p>Our <a href="/services/technical-seo-audit">technical SEO audit service</a>
  identifies crawl errors and indexing gaps. Pair it with our
  <a href="/services/content-strategy">content strategy package</a> for
  comprehensive coverage.</p>
```

### Fix Commands

```bash
# Audit internal links
claude "Crawl all HTML files in ./src/pages/. For each page, list the count of internal links, flag any with generic anchor text, and identify pages with fewer than 3 internal links."

# Fix generic anchor text
claude "In /src/pages/services.html, find any anchor text that says 'click here', 'read more', or 'learn more' and replace it with descriptive, keyword-rich anchor text based on the linked page's topic."

# Add pillar-cluster links
claude "Identify the pillar page for the 'SEO' topic cluster. Ensure every supporting page in ./src/pages/seo/ links to it with relevant anchor text. Add missing links in context."

# Find broken internal links
claude "Check every internal <a href> in ./src/pages/ and verify the target file exists. List all broken links with the source file and broken href."
```

---

## 8. AEO-Ready Content Formatting

Optimize content for AI answer engines (Google AI Overviews, ChatGPT, Perplexity) by
making it easy to extract clean, citable answers.

### Rules

| Criterion                | Requirement                                                   |
|--------------------------|---------------------------------------------------------------|
| H2 as questions          | Phrase at least 50% of H2s as natural-language questions       |
| Direct answers           | First 1-2 sentences after each H2 directly answer the heading |
| Quotable statistics      | Key stats in **bold** for easy extraction                     |
| FAQ section              | Dedicated FAQ section with `FAQPage` schema                   |
| Comparison tables        | Use `<table>` for any feature/product/option comparisons      |
| Extractable paragraphs   | Keep paragraphs to 2-3 sentences max                          |

### Before / After

```html
BEFORE
  <h2>Pricing</h2>
  <p>There are many factors that go into our pricing model. We consider the
  size of your website, the number of pages, your industry, competition level,
  and several other variables. Generally speaking, most clients end up paying
  somewhere in the range of a few hundred to a few thousand dollars per month
  depending on what they need.</p>

AFTER
  <h2>How Much Does SEO Cost per Month?</h2>
  <p>SEO costs <strong>$500 to $5,000 per month</strong> for most small
  businesses. The exact price depends on site size, competition, and scope.</p>
  <p>Key pricing factors:</p>
  <ul>
    <li>Site size: 10-page sites start at $500/mo</li>
    <li>Competition: high-competition niches cost 2-3x more</li>
    <li>Scope: technical + content + link building is a full package</li>
  </ul>
```

### FAQ Schema Example

```html
<section>
  <h2>Frequently Asked Questions</h2>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "How long does SEO take to show results?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Most sites see measurable improvements in 3-6 months. Competitive keywords may take 6-12 months."
        }
      }
    ]
  }
  </script>
  <h3>How long does SEO take to show results?</h3>
  <p>Most sites see measurable improvements in <strong>3-6 months</strong>.
  Competitive keywords may take 6-12 months.</p>
</section>
```

### Fix Commands

```bash
# Convert headings to questions
claude "In /src/pages/pricing.html, rewrite H2 headings as natural questions users would search for. Keep the same section content but rephrase the heading."

# Add direct answers after headings
claude "In /src/pages/guide.html, ensure the first 1-2 sentences after every H2 directly and concisely answer the heading question. Move background info below the direct answer."

# Bold key statistics
claude "In /src/pages/guide.html, find all statistics, percentages, dollar amounts, and time ranges. Wrap each in <strong> tags for AEO extractability."

# Add FAQ schema
claude "Add a FAQ section to /src/pages/services.html with 5 common questions about SEO services. Include FAQPage structured data that mirrors the visible Q&A content."

# Convert prose comparisons to tables
claude "In /src/pages/comparison.html, find any section that compares features, plans, or products in paragraph form. Convert them to responsive HTML tables with clear column headers."

# Shorten long paragraphs
claude "In /src/pages/guide.html, split every paragraph longer than 3 sentences into shorter paragraphs of 2-3 sentences each."
```

---

## Full-Page Optimization Workflow

Run these steps in order for a complete on-page audit:

```bash
# Step 1 -- Audit everything at once
claude "Run a full on-page SEO audit on /src/pages/target-page.html for the keyword 'target keyword'. Check: title tag (50-60 chars, keyword front-loaded), meta description (150-160 chars, CTA), heading structure (single H1, no skipped levels, H2s as questions), content quality (score 0-100), E-E-A-T signals, image optimization, internal links (3+ per page), and AEO formatting. Output a prioritized list of issues with severity (critical/warning/info)."

# Step 2 -- Apply all fixes
claude "Apply every critical and warning fix identified in the audit of /src/pages/target-page.html. Preserve existing content meaning while optimizing structure, meta tags, headings, images, and links."

# Step 3 -- Verify
claude "Re-audit /src/pages/target-page.html and confirm all critical and warning issues are resolved. Show the before and after content quality score."
```

---

## Quick Reference: Ideal Page Anatomy

```
<title>Primary Keyword + Modifier + Year | Brand</title>           50-60 chars
<meta name="description" content="Benefit statement + CTA">        150-160 chars

<h1>Primary Keyword in Natural Phrase</h1>                          Exactly 1
  <p>2-3 sentence intro answering the core question.</p>

<h2>Question Containing Secondary Keyword?</h2>                     AEO-ready
  <p>Direct answer in 1-2 sentences. <strong>Key stat.</strong></p>
  <p>Supporting detail in 2-3 sentences.</p>

  <h3>Subtopic</h3>                                                  No skipped levels
    <p>Short paragraph with contextual <a href="/related">internal link</a>.</p>

<picture>                                                            Optimized image
  <source srcset="descriptive-name.webp" type="image/webp">
  <img src="descriptive-name.jpg" alt="Descriptive alt with keyword"
       width="800" height="450" loading="lazy">
</picture>

<section>FAQ with FAQPage schema</section>                          AEO + rich results

<footer>Author bio + credentials + last updated date</footer>       E-E-A-T
```

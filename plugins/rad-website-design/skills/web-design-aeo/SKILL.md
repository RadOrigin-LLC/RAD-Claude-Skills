---
name: web-design-aeo
description: >
  Answer Engine Optimization (AEO) and AI-era SEO for 2026. Use when the user asks about
  "llms.txt", "llms-full.txt", "AEO", "AI SEO", "ChatGPT citations", "Perplexity ranking",
  "AI overviews", "answer engine optimization", "how do I get cited by AI", "robots.txt for
  AI bots", "GPTBot", "Google-Extended", "PerplexityBot", or any question about visibility in
  AI-driven search and answer engines. Includes honest adoption caveats — llms.txt has mixed
  real-world LLM bot adoption and should be treated as a low-cost signal, not a traffic driver.
allowed-tools: Read, Glob, Grep
---

# Answer Engine Optimization (AEO) — 2026

AEO is SEO for AI engines. The goal is to be **cited and summarized accurately** by ChatGPT, Perplexity, Google AI Overviews, Claude, etc. — not just ranked in blue links.

## Honesty up front

The 2026 evidence on AEO tactics is **mixed**:

- **llms.txt** has been proposed since September 2024. Real-world LLM bot adoption of the spec is **inconsistent**. Some independent crawl studies show major LLM bots ignore it.
- AI overviews **do extract** from well-structured pages. The "answer-first" pattern measurably improves citation likelihood.
- Schema markup (JSON-LD) **continues to matter** — it predates AEO and is also consumed by AI engines.
- Allowing AI bots in robots.txt **is required** to be in the eligible pool. Blocking them is the only thing more certain than allowing them.

**Bottom line:** Implement AEO tactics as low-cost defaults. Don't expect them to drive traffic the way SEO does. Optimize for being *citable*, not *clicked*.

## What to do

### 1. `llms.txt` (low cost, low confirmed ROI)

A markdown file at site root summarizing your content for LLM crawlers.

**Spec:**
- Hosted at `https://yourdomain.com/llms.txt`
- One H1 title (your site name + tagline)
- One blockquote summary (1–3 sentences, max ~50 words)
- Zero or more H2 sections, each containing a curated list of key URLs

**Example:**
```markdown
# Acme Tools — Production-grade developer utilities

> Acme builds CLI tools for cloud teams. Open-source core, paid managed tiers.

## Documentation
- [Getting Started](/docs/start.md)
- [API Reference](/docs/api.md)

## Pricing
- [Pricing & Plans](/pricing.md)
```

**`llms-full.txt`** — extended version with full text content of key pages (not just links). Higher token cost for crawlers but richer extraction.

### 2. Answer-First Content Structure

In every section, put the **direct answer in the first 40–50 words**.

- Inverted pyramid: answer first, support second, exploration last.
- Self-contained sections: each H2 should answer the question its heading asks without forcing the reader (or AI) to read prior sections.
- Use definition lists, tables, and clear lists where structure aids extraction.

### 3. AI Bot Allowlist in `robots.txt`

Allow these bots — blocking them removes you from AI-driven search visibility:

```
User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: CCBot
Allow: /
```

**Block selectively** if you have a paid-content gate or want to opt out of training. But understand: opting out reduces your citations, not just your training contribution.

### 4. Rich Schema Markup (JSON-LD)

Schema continues to matter — humans don't read it, but AI engines parse it cleanly:

- **Article** for blog/content pages — `headline`, `author`, `datePublished`, `image`
- **Product** for e-commerce — `name`, `price`, `aggregateRating`, `availability`
- **FAQ** for FAQ sections — pairs of `Question` + `Answer`
- **HowTo** for tutorials — ordered `step` array with `name` + `text`
- **Organization** site-wide — `name`, `url`, `logo`, `sameAs` (social profiles)

JSON-LD in a `<script type="application/ld+json">` tag at the appropriate scope (page-level for Article, site-level for Organization).

### 5. Page-Level Signals

- **Canonical URLs** — prevent fragmentation across query parameters and tracking codes
- **`<title>` and `<meta name="description">`** — still consumed by AI engines for snippet generation
- **Open Graph + Twitter Cards** — AI engines often retrieve OG metadata as a structured fallback

## What NOT to do

- **Don't keyword-stuff for AI engines.** They detect it as easily as Google does.
- **Don't fake authority.** AI engines triangulate citations; fabricated credentials get caught.
- **Don't gate everything.** Paywalled content can't be cited. Free article + paid premium is the working pattern.
- **Don't generate llms.txt with the same LLM that crawls it.** Self-referential summaries lose information. Curate by hand.

## Validation

- llms.txt: validate as Markdown; check it's served as `text/plain` or `text/markdown`; no auth required.
- robots.txt: test with multiple bot user-agents (Google has a tester; Perplexity does not).
- Schema: validate with Google's Rich Results Test (still works for non-Google engines).

## What this skill is NOT

- Not a guarantee of citations. AI engine citation policies change frequently.
- Not a replacement for traditional SEO. Both layer.
- Not a substitute for being *worth citing*. Authoritative, accurate, well-structured content is the substrate AEO sits on.

## References

- `references/aeo-llms-txt.md` — full spec + adoption notes
- For deeper SEO + AEO: install the `rad-seo-optimizer` plugin

## Source

2026 web research + Jeremy Howard's llms.txt proposal (Sept 2024) + adoption critique (aeoengine.ai 2026).

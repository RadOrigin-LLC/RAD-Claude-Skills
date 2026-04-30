# AEO & llms.txt — 2026 Reference (with adoption caveats)

## Honest framing up front

The 2026 evidence on AEO tactics is **mixed**:

- `llms.txt`: spec proposed Sept 2024 (Jeremy Howard). Real-world LLM bot adoption is **inconsistent**. Some independent crawl studies in 2026 show major LLM bots ignore the file.
- AI overviews **do extract** from well-structured pages; "answer-first" content measurably improves citation likelihood.
- Schema markup (JSON-LD) **continues to matter** — predates AEO and is consumed by AI engines.
- Allowing AI bots in `robots.txt` **is required** to be in the eligible pool.

**Bottom line:** Implement AEO tactics as **low-cost defaults**. Don't expect them to drive traffic the way SEO did. Optimize to be *citable*, not just *clicked*.

## llms.txt spec

A markdown file at site root summarizing your content for LLM crawlers.

- Hosted at `https://yourdomain.com/llms.txt`
- Served as `text/plain` or `text/markdown`, no auth
- One H1 title (site name + tagline)
- One blockquote summary (1–3 sentences, max ~50 words)
- Zero or more H2 sections, each containing curated lists of key URLs

```markdown
# Acme Tools — Production-grade developer utilities

> Acme builds CLI tools for cloud teams. Open-source core, paid managed tiers.

## Documentation
- [Getting Started](/docs/start.md): Five-minute walkthrough
- [API Reference](/docs/api.md): Complete API surface

## Pricing
- [Pricing & Plans](/pricing.md): Free, Pro, Enterprise
```

## llms-full.txt

Extended version including full text content of key pages (not just links). Higher token cost for crawlers, richer extraction.

Format: same H1 + blockquote + H2 sections, but each section may contain full markdown content.

## Adoption caveats (the honest part)

As of 2026:
- **OpenAI's GPTBot** does not consistently fetch llms.txt — its crawler operates from sitemap.xml and direct page fetches.
- **Perplexity** has acknowledged the spec but adoption signals are unclear.
- **Anthropic's ClaudeBot** does fetch llms.txt for some sites; not universally.
- Independent studies (aeoengine.ai 2026) show "zero usage" for some major LLM bots.

Implication: build llms.txt because it's near-zero cost and forward-compatible, but **don't gate AEO strategy on it**.

## What actually works for AEO (2026)

### 1. Answer-first content structure

Put the direct answer in the first 40–50 words of every section. AI overviews extract from openings.

```markdown
## How do container queries work?

Container queries let CSS rules respond to the size of a parent container, not the viewport. They use `@container (min-width: ...)` syntax. Browser support: Chrome 105+, Safari 16+, Firefox 110+ (~92% global).

[More detail follows...]
```

### 2. Allow AI bots in robots.txt

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

Block selectively if you have paid-content gates or want to opt out of training. Understand: opting out reduces your AI citations, not just your training contribution.

### 3. Schema.org JSON-LD

Schema continues to matter. AI engines parse it cleanly.

- **Article** — `headline`, `author`, `datePublished`, `image`
- **Product** — `name`, `price`, `aggregateRating`, `availability`
- **FAQ** — pairs of `Question` + `Answer` (high AEO citation rate)
- **HowTo** — ordered `step` array with `name` + `text`
- **Organization** — site-wide `name`, `url`, `logo`, `sameAs`

Place in `<script type="application/ld+json">` at the appropriate scope.

### 4. Self-contained sections

Each H2 should answer the question its heading asks without forcing the reader (or AI) to read prior sections. AI engines extract sections, not whole pages.

### 5. Page-level metadata

- **Canonical URLs** — prevent fragmentation across query parameters
- **`<title>`** + **`<meta name="description">`** — AI engines use them for snippet generation
- **Open Graph + Twitter Cards** — structured fallback when JSON-LD is absent

## What does NOT work

- **Keyword stuffing for AI** — detected as easily as Google detects it.
- **Faking authority** — AI engines triangulate citations; fabricated credentials get caught.
- **Gating everything** — paywalled content can't be cited. Free article + paid premium is the working pattern.
- **LLM-generating your llms.txt** — self-referential summaries lose information. Curate by hand.

## Validation

- **llms.txt:** validate as Markdown. Confirm `text/plain` or `text/markdown`. No auth.
- **robots.txt:** test with multiple bot user-agents (Google has a tester; Perplexity does not).
- **Schema:** Google Rich Results Test (still works for non-Google engines).

## What to measure

- **Citation rates in AI overviews** — manually sample queries weekly; track which content gets cited.
- **AI-bot user agents in logs** — are they fetching at all? At what rate?
- **AI-driven referral traffic** — limited but appearing in analytics under `chat.openai.com`, `perplexity.ai`, etc.

There's no equivalent to Google Search Console for AEO yet (2026). Tracking is manual.

## Cross-plugin

For full SEO + AEO strategy beyond this reference: install `rad-seo-optimizer`.

## Sources

- llms.txt spec: Jeremy Howard, Sept 2024
- llms.txt zero usage critique: aeoengine.ai (2026)
- Schema.org: schema.org/docs
- Google's AI bot opt-out: Google Search Central documentation
- Anthropic ClaudeBot: Anthropic documentation
- 2026 web research synthesis

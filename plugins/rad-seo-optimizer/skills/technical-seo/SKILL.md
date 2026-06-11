---
name: technical-seo
description: >
  Code-level technical SEO audit: crawlability, robots.txt (including the AI-bot
  allow/block matrix and llms.txt), sitemap issues, indexation, redirects, canonicals,
  JS rendering, security headers, URL structure, and page-speed
  code-level risk factors. Does NOT measure numerical Core Web Vitals (LCP/CLS/INP) —
  those require a Lighthouse/PSI MCP (Path B). Does NOT crawl whole sites — operates on
  the user's codebase plus a provided URL list.
argument-hint: "[URL or path to audit] [--non-interactive]"
allowed-tools: Read Glob Grep Write Bash WebFetch
---

# Technical SEO Skill

Run a comprehensive technical SEO audit over the user's codebase and a provided URL list. Every issue includes a why-it-matters explanation, an exact fix command, and an expected impact rating. Be honest about which categories are measured vs. observable-only vs. requiring Path B integration.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. Opus/Sonnet batch config Reads, template Globs, and URL fetches in parallel. Haiku may follow sequentially if parallel batching misbehaves.

## Execution: parallel-first

- **Section 1 (crawlability)**: robots.txt + sitemap fetch/parse + template Glob are independent — single batch
- **Section 2 (page-speed risk factors)**: per-template Reads + per-URL fetches independent — batch
- **Section 3 (mobile)**: inspections across URL list independent — batch
- **Section 4 (security)**: header inspections across URL list independent — batch
- **Section 5 (URL structure)**: config Reads + sitemap URL parsing independent — batch
- **Section 6 (JS SEO)**: per-URL no-JS fetches independent — batch
- **Section 7 (redirects)**: redirect chain walks can parallelize per URL

## Capability Honesty

Read `references/CAPABILITIES.md`. Key constraints:
- **Numerical Core Web Vitals** (LCP/CLS/INP values) require Lighthouse or PSI API — Path B
- **JS-rendered SPA content** requires a browser-based MCP — Path B
- **Full-site crawl** requires a crawler MCP — Path B
- **What this skill DOES measure honestly**: static analysis of config + templates + framework files; observable signals from WebFetch of specific URLs (no JS execution); redirect behavior (via HTTP following)

---

## 1. Crawlability & Indexation (static analysis + WebFetch — scored honestly)

### 1.1 robots.txt Validation

Read `robots.txt` at the site root (from codebase or WebFetch). Check:

- **Missing robots.txt** — not strictly required but signals neglect
- **Blocking important paths** — any `Disallow` rule covering pages meant to rank (e.g., `/blog/`, `/products/`)
- **Missing sitemap directive** — robots.txt should contain `Sitemap:` line
- **Wildcard overreach** — rules like `Disallow: /*?` can block faceted navigation unintentionally

**Why it matters:** A misconfigured robots.txt can deindex entire site sections.

**Fix command:**
```
claude "Read robots.txt, remove rules blocking /blog and /products, add Sitemap: https://example.com/sitemap.xml, and write the corrected file."
```

**Expected impact:** High. Blocked pages cannot rank at all.

### 1.2 XML Sitemap

Fetch the sitemap from the `Sitemap:` directive, or try `/sitemap.xml` and `/sitemap_index.xml`. Validate:

- Sitemap exists and returns HTTP 200
- Listed URLs return 200 (no 404s, no redirects) — check in parallel
- Under 50,000 URLs per file (protocol limit)
- `<lastmod>` dates present and accurate
- No URLs blocked by robots.txt appear in the sitemap
- Sitemap referenced in robots.txt

**Why it matters:** Sitemaps guide crawlers. Broken entries waste crawl budget.

**Expected impact:** Medium. Accelerates discovery; critical on large sites.

### 1.3 Canonical Tag Audit

For every indexable page in the codebase/URL list, inspect `<link rel="canonical">`:

- Missing canonical on indexable pages
- Conflicting canonical (chain)
- Self-referencing canonical with trailing slash / protocol / www differences
- Cross-domain canonical (flag unless intentional)
- Paginated pages canonicalizing to page 1 (wrong — should self-canonicalize)

**Why it matters:** Incorrect canonicals consolidate signals to the wrong URL or cause deindexation.

**Expected impact:** High.

### 1.4 Noindex / Nofollow Audit

Scan pages for `<meta name="robots" content="noindex">` and `X-Robots-Tag` headers:

- Flag pages with `noindex` that appear in the sitemap
- Flag pages with `noindex` that receive internal links as if indexable
- Flag `nofollow` on internal links (leaks PageRank)
- Flag conflicting directives between meta tag and HTTP header

**Expected impact:** High for affected pages.

### 1.5 Orphan Page Detection (codebase + sitemap)

Compare sitemap URLs against URLs reachable via internal links from the codebase/homepage:
- Pages in sitemap but not internally linked → orphans
- Pages linked but missing from sitemap → sitemap gaps

**Expected impact:** Medium. Orphans often gain rankings once linked.

### 1.6 Crawl Budget Risk Factors

Check for crawl-budget drains visible in code/config:
- Infinite-scroll or faceted navigation generating unbounded URL permutations
- Session IDs / tracking parameters in internal URLs
- Soft-404 patterns (200 status + "not found" template)
- Duplicate content accessible at multiple paths

**Expected impact:** Medium-High on sites with 10,000+ pages; negligible on small sites.

### 1.7 AI Crawler Access (deterministic — `scripts/audit-ai-access.py`)

Run the bundled validator; knowledge in `references/ai-crawl-access.md`:

```
python scripts/audit-ai-access.py --origin https://example.com --check-fetch --json
python scripts/audit-ai-access.py --robots ./public/robots.txt --html-root ./public --json
```

It reports:
- **Per-AI-bot robots.txt matrix**, classed *citation/search* (OAI-SearchBot,
  ChatGPT-User, Claude-SearchBot/User, PerplexityBot/User, Bingbot, Googlebot — blocking
  these removes the site from AI answers) vs *training* (GPTBot, ClaudeBot,
  Google-Extended, CCBot, … — blocking is a licensing choice with no AEO impact)
- **Google-Extended scope note** — it controls Gemini training only; AI Overviews/AI Mode
  run off Googlebot. Never imply otherwise.
- **CDN-level blocking probe** (`--check-fetch`) — Cloudflare blocks AI crawlers by
  default on new domains since July 2025; robots.txt Allow + WAF 403 is a common silent
  misconfiguration. Probe results are indicative (some WAFs verify crawler IPs).
- **llms.txt** existence + format shape — *info only*: not a ranking/citation factor, but
  recommended by Lighthouse's Agentic Browsing audits (see `references/agent-readiness.md`)
- **Content-Signal / RSL / noai** declarations — informational
- **JS-dependence heuristic** — see §6.1; CSR content is invisible to AI crawlers

**Why it matters:** A site that wants AI citations while blocking the citation-class bots
(or letting its CDN do so) is invisible to ChatGPT/Claude/Perplexity regardless of
content quality.

**Expected impact:** High for AI answer visibility; zero ranking impact from the
training-class choices.

---

## 2. Page-Speed Code-Level Risk Factors (NOT numerical CWV)

**Honest framing**: This section flags *risk factors visible in code* that tend to correlate with poor Core Web Vitals. It does NOT produce numerical LCP/CLS/INP values. Those require Lighthouse or PSI measurement (Path B).

For numerical CWV measurement, integrate a Lighthouse MCP or use the PageSpeed Insights API directly.

### 2.1 LCP Risk Factors (observable from code)

Likely-LCP elements (hero images, heading banners, video posters) — check:
- Image served in next-gen format (WebP/AVIF)? Flag legacy PNG/JPG for hero
- Explicit `width` and `height` attributes? Missing → CLS risk
- Preloaded with `<link rel="preload">` where appropriate?
- Render-blocking CSS/JS in `<head>` without `defer`/`async`?
- Critical CSS inlined vs. linked?

Framework-specific fixes: see `references/platform-fixes.md`.

### 2.2 INP Risk Factors (observable from code)

Scan for long-running handler patterns:
- Synchronous `localStorage` or `sessionStorage` reads in event handlers
- Heavy computation without Web Workers / `requestIdleCallback`
- Debouncing absent on input handlers
- Third-party scripts in `<head>` without defer
- React hydration patterns (look for `hydrateRoot` placement)

### 2.3 CLS Risk Factors (observable from code)

- Images/videos without explicit `width`/`height` or CSS `aspect-ratio`
- Web fonts without `font-display: swap` + size-adjusted fallback
- Ads / embeds without reserved space (`min-height`)
- Content injected above the fold after initial paint
- Dynamic banners (cookie consent, promos) that push content instead of using `transform`

For framework-specific fixes, see `references/platform-fixes.md`.

### 2.4 Numerical CWV Measurement — NOT PROVIDED

This skill does not measure LCP, CLS, or INP numerically. To get real numbers, integrate:
- Lighthouse CLI MCP (free, self-hosted)
- PageSpeed Insights API MCP (free with API key)

The skill flags *risk factors*; measurement tells you *whether the factors matter in practice*.

---

## 3. Mobile-First (static analysis — scored honestly)

### 3.1 Viewport Meta Tag

Verify `<meta name="viewport" content="width=device-width, initial-scale=1">` in `<head>`. Flag `maximum-scale=1` or `user-scalable=no` (accessibility violation).

**Expected impact:** Critical when missing.

### 3.2 Mobile Content Parity

Compare rendered content between mobile and desktop user agents via WebFetch. Flag:
- Hidden mobile content
- Missing images / structured data on mobile markup

**Expected impact:** High on mobile-first indexing.

### 3.3 Touch Target Sizing

Scan interactive elements for minimum 48x48 CSS px and 8px spacing between adjacent targets (check CSS / Tailwind utilities).

### 3.4 Font Sizes

Body text at least 16px; no text requiring zoom.

### 3.5 Horizontal Scrolling

Detect viewport overflow on mobile widths (360-414px): fixed widths, tables without scroll wrappers, images without `max-width: 100%`.

---

## 4. Security (static + header analysis)

### 4.1 HTTPS Everywhere

- All pages load over HTTPS (check URL list)
- No mixed content (HTTP resources on HTTPS pages)
- HTTP-to-HTTPS 301 redirect
- SSL certificate valid + not expiring soon

**Why it matters:** HTTPS is a confirmed ranking signal.

### 4.2 HSTS Header

`Strict-Transport-Security` header with `max-age` ≥ 31536000, `includeSubDomains`, `preload`.

### 4.3 Content-Security-Policy

Check for CSP header. Flag if missing or overly permissive (`unsafe-inline`, `unsafe-eval`, `*`). Verify `frame-ancestors` set.

### 4.4 Sensitive File Exposure

Check for publicly accessible `.env`, `.git/`, `wp-config.php`, database dumps, backup files (via WebFetch of known paths).

**Expected impact:** Low ranking impact, critical for site safety. Hacked sites get deindexed.

---

## 5. URL Structure (static analysis)

### 5.1 Clean, Descriptive URLs

Evaluate URL patterns:
- Readable words, not IDs or hashes (bad: `/p/12345`; good: `/products/blue-widget`)
- Hierarchy reflects site structure
- Not excessively deep (4+ path segments)

### 5.2 Lowercase, Hyphen-Separated

Flag uppercase characters, underscores, spaces, encoded characters in paths.

### 5.3 Query Parameters on Important Pages

Flag important content accessible only via query strings (`?id=123`). Flag sorting/filtering that generates indexable duplicates.

### 5.4 Pagination Handling

- Each paginated page self-canonicalized (not to page 1)
- `rel="next"` / `rel="prev"` link tags
- Paginated pages in sitemap
- No infinite scroll without progressive URLs

---

## 6. JavaScript SEO

### 6.1 Server-Side Rendering Check

Fetch each key URL without JS (WebFetch returns raw HTML). Flag:
- Empty `<body>` with only root `<div>` + `<script>` → client-side-only rendering
- Title, meta description, headings, body text missing from initial HTML
- Internal links as elements other than `<a href>`

**Why it matters:** Googlebot queues JS pages for rendering, delaying indexation — and
**no other major crawler renders JS at all**: AI crawlers (GPTBot, ClaudeBot,
PerplexityBot, OAI-SearchBot) execute zero JavaScript, so CSR-only content is invisible
to ChatGPT, Claude, and Perplexity even when those bots are allowed.

**Expected impact:** Critical. Client-side-only rendering delays Google indexation by
days and excludes the content from AI answers entirely.

**Note:** Full SPA analysis requires a browser MCP (Path B). This skill detects the symptom; diagnosing specific hydration issues needs a browser runtime.

### 6.2 Dynamic Rendering Detection

Detect Rendertron / Puppeteer / prerender.io setups. Flag if used as permanent solution instead of SSR.

### 6.3 JavaScript-Dependent Content

Identify critical content loaded asynchronously (prices, reviews, article text, internal links rendered by JS frameworks).

### 6.4 Lazy-Loading Implementation

- Above-the-fold images MUST NOT be lazy-loaded (harms LCP risk)
- Below-the-fold images use `loading="lazy"`
- Lazy-loaded images have `<noscript>` fallbacks

---

## 7. Redirects

### 7.1 Redirect Chain Detection

Follow every redirect to its final destination. Flag:
- Chains of 2+ hops
- Chains exceeding 3 hops (Googlebot may stop after 5)
- Internal links pointing to URLs that redirect

### 7.2 Mixed Redirect Types

- Permanent moves → 301 or 308
- Temporary → 302 or 307, but flag 302s in place 30+ days (probably should be 301)

### 7.3 Redirect Loops

Detect circular redirects. Flag any redirect that doesn't terminate in a 200 within 10 hops.

**Expected impact:** Critical. Redirect loops make pages inaccessible.

---

## Output Format

```
## Summary Scorecard
| Category | Score | Method | Critical | Warnings | Passed |
|----------|-------|--------|----------|----------|--------|
| Crawlability & Indexation | A-F | static-analysis | count | count | count |
| AI Crawler Access | A-F | audit-ai-access.py | count | count | count |
| Page-Speed Risk Factors | A-F | static-analysis | count | count | count |
| Page-Speed CWV (numerical) | N/A | not-measured (Path B: Lighthouse MCP) | — | — | — |
| Mobile-First | A-F | static-analysis | count | count | count |
| Security | A-F | static + headers | count | count | count |
| URL Structure | A-F | static-analysis | count | count | count |
| JavaScript SEO | A-F | static + no-JS fetch | count | count | count |
| Redirects | A-F | http-following | count | count | count |
| **Overall (measured categories only)** | **A-F** | | | | |

## Measurement Gaps
- Numerical Core Web Vitals (LCP, CLS, INP): integrate Lighthouse MCP or PSI API
- JS-rendered SPA content: integrate browser MCP (Playwright-based)
- Full-site crawl: integrate crawler MCP (Screaming Frog / Sitebulb)
```

### Issue Format

```
### [CRITICAL|WARNING] Issue Title
**Category:** Category Name > Sub-check
**Why it matters:** One-sentence SEO impact
**Affected URLs:** List of URLs or "site-wide"
**Fix command:** claude "exact fix command"
**Expected impact:** High | Medium | Low — brief explanation
```

### Priority Order

1. Critical issues blocking indexation (noindex on key pages, redirect loops, missing SSR)
2. Page-speed risk factors with high user-visibility impact
3. Mobile-first violations
4. Redirect problems
5. URL structure issues
6. Security hardening

---

## Framework Detection

Auto-detect the framework from package.json / config files / HTML signals before running checks. See `references/platform-fixes.md` for framework detection patterns and tailored fix commands. When ambiguous, ask before proceeding.

# rad-seo-optimizer scripts

Four pure-stdlib Python 3.8+ validators that turn the plugin's "static SEO analysis" claims from LLM eyeballing into deterministic checks. No `pip install` required.

> Windows note: the examples use `python3`; on Windows use `python` (or `py`).

## validate-jsonld.py

Extracts `<script type="application/ld+json">` blocks from HTML / JSX / Astro / Svelte / Vue source (or accepts raw `.json` files) and validates against a bundled subset of schema.org type definitions.

```bash
python3 scripts/validate-jsonld.py <path>
python3 scripts/validate-jsonld.py <root> --files src/Layout.tsx,public/index.html
python3 scripts/validate-jsonld.py <root> --json
```

**Checks per block:**

- Valid JSON (parse error → critical)
- `@context` references schema.org
- `@type` is a known type
- For recognized types: required + recommended properties present
- URL-shaped fields (`url`, `image`, `logo`, `thumbnailUrl`, `sameAs`, etc.) are absolute URLs
- Date fields (`datePublished`, `dateModified`, `startDate`, etc.) match ISO-8601

**Bundled type set** (SEO-impactful subset; ~20 types): Article, NewsArticle, BlogPosting, Product, Offer, Organization, Person, WebSite, WebPage, BreadcrumbList, FAQPage, Question, Answer, HowTo, Recipe, Event, LocalBusiness, SoftwareApplication, VideoObject. For other types the validator parses-only and emits an `info`.

**Supports `@graph` form** and arrays of objects at top level.

**Framework handling (JSX/TSX/Astro/Svelte/Vue):** literal JSON is unwrapped and
validated from `dangerouslySetInnerHTML={{ __html: `...` }}` (including self-closing
tags), Astro `set:html={...}`, and JSX-children `{`...`}` forms. Dynamically built
JSON-LD (`JSON.stringify(expr)`, variable refs, `${}` interpolation) cannot be verified
statically — those blocks emit an `info`-severity `dynamic_jsonld` finding telling you to
validate the rendered HTML, rather than being silently skipped or falsely failed.

**Exit codes:** `0` clean, `1` warnings/critical, `2` script error.

## audit-meta-tags.py

Audits HTML-shaped templates for SEO meta-tag completeness.

```bash
python3 scripts/audit-meta-tags.py <path>
python3 scripts/audit-meta-tags.py <root> --files src/Layout.tsx
python3 scripts/audit-meta-tags.py <root> --json
```

**Checks per file:**

- `<title>` presence + length (35-65 acceptable, 50-60 ideal)
- `<meta name="description">` presence + length (120-180 acceptable, 140-160 ideal)
- `<link rel="canonical">` presence + absolute URL shape; duplicate detection
- `<meta charset>` declared
- `<meta name="viewport">` present (critical if missing — breaks mobile)
- `<meta name="robots">` sanity (warn on `noindex`)
- Open Graph: `og:title`, `og:description`, `og:image`, `og:url`, `og:type`
- Twitter Card: `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image` (info; falls back to og:* when absent)
- `hreflang` structure: if ≥2 alternates, warn when `x-default` is missing

Works on JSX/Astro/Svelte even though they aren't strict HTML — extracts `<head>` block when present, otherwise scans the whole document.

**Exit codes:** `0` clean, `1` warnings/critical, `2` script error.

## check-broken-links.py

Parallel HTTP HEAD scanner for 4xx / 5xx / network errors. Pure stdlib (urllib + concurrent.futures).

```bash
python3 scripts/check-broken-links.py --urls https://a.com,https://b.com
python3 scripts/check-broken-links.py --url-list urls.txt
python3 scripts/check-broken-links.py --sitemap https://example.com/sitemap.xml
python3 scripts/check-broken-links.py --html-root ./public
python3 scripts/check-broken-links.py --html-root ./public --concurrency 20 --timeout 10
python3 scripts/check-broken-links.py --html-root ./public --json
```

**Input modes:**

- `--urls <list>` — inline comma-separated (full URLs with `https://` scheme required)
- `--url-list <file>` — one URL per line
- `--sitemap <url-or-file>` — parses `<loc>` entries from XML sitemap (URL or local file)
- `--html-root <dir>` — scans `.html`/`.htm` files for absolute `href`/`src` attributes

Combine any of the above; URLs are deduped across sources.

**Method:** HEAD first (cheap); falls back to GET with `Range: bytes=0-0` if HEAD returns 405. Parallel via `ThreadPoolExecutor` (default 10 workers). User-Agent set to identify the scanner.

**Categorization:**

- `ok` (2xx)
- `redirect` (3xx) — reported, not flagged
- `client_err` (4xx) — flagged
- `server_err` (5xx) — flagged
- `network_err` — connection failure / timeout / DNS / SSL — flagged
- `bad_url` — URL doesn't parse — flagged

**Exit codes:** `0` clean, `1` any 4xx/5xx/network_err/bad_url, `2` script error.

**Honest scope:** runs at the time of invocation only. Not a continuous monitor. For ongoing link health, schedule via cron / GitHub Actions.

## audit-ai-access.py

Audits the AI-crawl access layer: robots.txt AI-bot policy, llms.txt, Content Signals,
RSL, noai meta, and JS-dependence. Knowledge reference: `references/ai-crawl-access.md`.

```bash
python3 scripts/audit-ai-access.py --origin https://example.com
python3 scripts/audit-ai-access.py --origin https://example.com --check-fetch
python3 scripts/audit-ai-access.py --robots ./public/robots.txt --html-root ./public
python3 scripts/audit-ai-access.py --origin https://example.com --json
```

**Checks:**

- **Per-AI-bot robots.txt matrix** — 16 known AI user-agents, classed *citation/search*
  (blocking removes you from AI answers: OAI-SearchBot, ChatGPT-User,
  Claude-SearchBot/User, PerplexityBot/User, Bingbot, Googlebot) vs *training*
  (licensing choice, no AEO impact: GPTBot, ClaudeBot, Google-Extended, CCBot, …).
  Citation-bot full blocks → warning; Googlebot/Bingbot blocks → critical; training
  blocks → info. Includes the Google-Extended scope explainer (it does NOT control AI
  Overviews).
- **llms.txt** — existence (absence = info only; it is not a ranking/citation factor but
  Lighthouse's Agentic Browsing audits recommend it), spec-shape check (H1 + Markdown
  links), 5xx → warning (mirrors Lighthouse).
- **Content-Signal / RSL `License:` lines** in robots.txt — informational.
- **noai/noimageai meta** in local HTML — informational.
- **JS-dependence heuristic** — near-empty visible text + scripts + SPA shell markers →
  warning (no major AI crawler executes JavaScript).
- **`--check-fetch`** — probes the origin with AI user-agent strings vs a browser
  baseline to catch CDN/WAF-level blocking that contradicts robots.txt. Indicative only
  (some WAFs verify crawler IPs).

**Exit codes:** `0` clean, `1` warnings/critical, `2` script error.

## When these run

| Caller | When |
|---|---|
| `/rad-seo-optimizer:technical-seo` | The skill invokes `validate-jsonld.py`, `audit-meta-tags.py`, and `audit-ai-access.py` over the templates/origin it scans. |
| `/rad-seo-optimizer:aeo-optimizer` | Phase 0 (AI Crawl Access Gate) runs `audit-ai-access.py` before content work. |
| `/rad-seo-optimizer:broken-link-fixer` | Wraps `check-broken-links.py` for the discover-and-fix flow. |
| User direct | Standalone via `python3 plugins/rad-seo-optimizer/scripts/<validator>.py` |
| CI | Same, with `--json` and selective inputs for sitemap or URL-list mode |

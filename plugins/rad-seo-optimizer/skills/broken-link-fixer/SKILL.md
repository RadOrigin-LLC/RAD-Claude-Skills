---
name: broken-link-fixer
description: >
  Broken links, 404 errors, dead links, redirect chains, link checker, fix links. Scans
  the user's codebase for broken internal/external links, redirect chains, mixed-content
  issues, and unlinked brand mention opportunities. Real code work — no Path B dependencies.
argument-hint: "[URL or path to check] [--non-interactive]"
allowed-tools: Read Glob Grep Write Bash WebFetch
---

# Broken Link Fixer Skill

Find every broken link on the target site, trace redirect chains, uncover link reclamation opportunities, and generate exact fix commands for every issue. Operates over the user's codebase (Glob + Grep for link references, verify targets) plus limited WebFetch for external link verification.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. Link verification is primarily tool-call orchestration; all three models handle the batch coordination reliably.

## Execution: parallel-first

- **Phase 1 link discovery**: Glob + Grep across the codebase in a single batch
- **Phase 2 link verification**: WebFetch / head requests per external link independent — batch (mindful of rate-limit politeness on any single domain)
- **Phase 3 redirect chain tracing**: redirect walks per URL independent — batch

---

## Phase 1: Link Discovery

### 1.1 Codebase Scan

Grep the project source for all link references. Target these patterns:

- **HTML href attributes:** `href="..."` in `.html`, `.htm`, `.jsx`, `.tsx`, `.vue`, `.svelte`, `.php` files.
- **Markdown links:** `[text](url)` and `[text]: url` reference-style links in `.md` and `.mdx` files.
- **CSS url() references:** `url(...)` in `.css`, `.scss`, `.less` files (images, fonts, imports).
- **JavaScript/TypeScript:** String literals matching URL patterns in `.js`, `.ts` files (fetch calls, API endpoints, `window.location`).
- **Image sources:** `src="..."` on `<img>`, `<video>`, `<source>`, `<script>`, `<iframe>` tags.
- **Sitemap entries:** URLs listed in `sitemap.xml`.
- **Configuration files:** URLs in `robots.txt`, `.htaccess`, `next.config.js`, `vercel.json`, `netlify.toml`.

```
claude "Grep all files for href=, src=, url(, markdown links, and fetch/axios URLs. Output a deduplicated list with source file and line number for each link found."
```

### 1.2 Live Site Crawl

Use WebFetch starting from the root URL. For each page:

1. Fetch the page and extract all links from the rendered HTML.
2. Categorize each link:
   - **Internal links:** Same domain as the root URL.
   - **External links:** Different domain.
   - **Resource links:** Images, CSS, JS, fonts, downloads (by file extension or tag type).
3. Follow internal links recursively up to a configurable depth (default: 5 levels).
4. Respect `robots.txt` disallow rules during crawl.

```
claude "Use WebFetch to crawl {url} up to 5 levels deep. Extract all href, src, and srcset URLs from each page. Build a complete link inventory with source page, target URL, link text, and link type."
```

---

## Phase 2: Status Check

For every unique URL discovered, check the HTTP status code. Classify each result:

| Status | Classification | Action |
|--------|---------------|--------|
| 200 | OK | No action needed |
| 301 | Permanent redirect | Record destination; check for chains |
| 302 | Temporary redirect | Record destination; flag if older than 30 days |
| 403 | Forbidden | Flag — may indicate misconfigured permissions |
| 404 | Not Found | **BROKEN** — fix immediately |
| 410 | Gone | Intentionally removed — remove link or replace |
| 500+ | Server error | Flag — may be intermittent, recheck before reporting |
| Timeout | Unreachable | Flag — retry once, then report if still unreachable |

**Rate limiting:** Pause 200 ms between requests to the same domain. For external links, pause 500 ms to avoid triggering rate limits.

```
claude "Check HTTP status for every URL in the link inventory. For non-200 responses, record the status code, response headers, and redirect destination if applicable. Retry timeouts and 5xx errors once after 3 seconds."
```

---

## Phase 3: Redirect Chain Detection

For every URL that returns 301 or 302, follow the redirect path to the final destination. Flag:

- **Redirect chains (2+ hops):** A redirects to B, B redirects to C. Each hop adds 100-300 ms latency and leaks PageRank.
- **Redirect chains (3+ hops):** Recommend flattening to a single redirect. Googlebot may abandon chains beyond 5 hops.
- **Redirect loops:** A redirects to B, B redirects to A. These make the page completely inaccessible.
- **Mixed-protocol redirects:** HTTP to HTTPS (expected) vs. HTTPS to HTTP (broken — flag immediately).
- **302 chains:** Temporary redirects chained together rarely pass full link equity.

For each chain, output the full path and recommend the flattened redirect.

```
claude "Trace every redirect to its final destination. Flag chains with 2+ hops. For each chain, output: Source -> Hop 1 -> Hop 2 -> ... -> Final. Generate a flattened redirect rule mapping source directly to final destination."
```

---

## Phase 4: Link Reclamation Opportunities

### 4.1 Unlinked Brand Mentions

Use WebSearch to find pages that mention the brand name but do not link to the site:

```
claude "Use WebSearch to find '{brand}' mentions across the web. For each result, use WebFetch to check whether the page links to {domain}. Report pages that mention the brand without linking."
```

These are outreach targets — contact the site owner and request a link.

### 4.2 Competitor Broken Link Building

Identify broken outbound links on competitor sites that pointed to content similar to the target site's:

```
claude "Use WebSearch to find pages in {niche} that link to now-dead resources. Use WebFetch to verify the links are truly broken (404/410). Cross-reference with our content to find suitable replacement pages."
```

This is a proven link-building tactic. See `link-building-tactics.md` for outreach templates and best practices.

### 4.3 Reclaimed Link Prioritization

Rank reclamation opportunities by:

1. Domain authority of the linking site.
2. Relevance of the linking page to the target site's content.
3. Likelihood of success (editorial sites are more responsive than forums).

---

## Phase 5: Fix Recommendations

For each broken link, provide a specific fix with an executable Claude Code command.

### 5.1 Internal 404s

The highest priority. These are links you fully control.

**Diagnosis:** Determine why the page is missing — was it moved, renamed, or deleted?

**Fix commands:**

```
# URL was moved — update all references
claude "Find every file that links to '/old-path'. Replace with '/new-path'. Verify no other references remain."

# Page was deleted — remove the link or replace with relevant alternative
claude "Find every file that links to '/deleted-page'. Replace the link with '/relevant-alternative' or remove the link element entirely if no alternative exists."

# Typo in URL — correct the path
claude "Find every file that links to '/missspelled-url'. Correct the URL to '/correct-url'."
```

### 5.2 External 404s

Links to other sites that have gone dead.

```
# Replace with an alternative resource
claude "The link to 'https://dead-site.com/resource' on '/our-page' is returning 404. Find the page on the Wayback Machine or locate an equivalent resource. Replace the broken URL with the working alternative."

# Remove if no alternative exists
claude "Remove the broken link to 'https://dead-site.com/resource' from '/our-page'. Rewrite the surrounding text so it reads naturally without the link."
```

### 5.3 Redirect Chains

Flatten every chain to a direct link.

```
# Update internal links to point to final destination
claude "Find all links pointing to '{redirect-source}'. Update them to point directly to '{final-destination}' to eliminate the redirect chain."

# Update server redirect rules
claude "In the redirect configuration, replace the chain {A -> B -> C} with a single rule {A -> C}. Remove the intermediate rule {B -> C} only if B has no other inbound links."
```

### 5.4 Mixed Content (HTTP to HTTPS)

```
claude "Find all HTTP URLs in the codebase (http://). For each, verify the HTTPS version works. Replace http:// with https:// for all valid URLs. Flag any that don't support HTTPS."
```

---

## Phase 6: 404 Page Optimization

Check whether the site has a custom 404 page. Use WebFetch to request a known-bad URL and inspect the response.

### Requirements for a Good 404 Page

1. **Correct HTTP status code:** Must return 404, not 200 (soft 404s confuse search engines).
2. **Friendly error message:** Tell the user what happened in plain language.
3. **Search functionality:** Include a search bar so users can find what they were looking for.
4. **Popular page links:** List 5-10 of the most visited pages on the site.
5. **Navigation:** Include the site header and footer so users can navigate away.
6. **Consistent branding:** Match the site's design and tone.

**Fix command if no custom 404 page exists:**

```
claude "Create a custom 404 page that returns HTTP 404 status. Include: a friendly message ('We could not find that page'), a search bar, links to the 5 most important pages, and the standard site header/footer. Match the existing site design."
```

**Fix command if 404 page returns 200 (soft 404):**

```
claude "The custom 404 page is returning HTTP 200. Update the server configuration to return a 404 status code for missing pages while still rendering the custom error template."
```

---

## Output Format

Present results using this structure:

```
# Broken Link Report

## Summary
- Total links scanned: X
- Broken links found: X (internal: X, external: X)
- Redirect chains: X
- Mixed content issues: X
- Link reclamation opportunities: X
- 404 page status: [Custom / Soft 404 / Missing]

## Broken Internal Links (Fix Immediately)
| Source Page | Broken URL | Status | Fix |
|------------|-----------|--------|-----|
| /about | /old-team | 404 | Update to /team |
| /blog/post-1 | /products/removed | 410 | Remove link |

## Broken External Links
| Source Page | Broken URL | Status | Recommended Replacement |
|------------|-----------|--------|------------------------|
| /resources | https://example.com/gone | 404 | https://alternative.com/resource |
| /blog/post-2 | https://dead-site.com/page | Timeout | Remove or find alternative |

## Redirect Chains (Flatten)
| Source | Redirect 1 | Redirect 2 | Final Destination |
|--------|-----------|-----------|-------------------|
| /old-a | /old-b (301) | /old-c (301) | /current (200) |

## Mixed Content Issues
| Source Page | HTTP URL | HTTPS Available | Fix |
|------------|---------|----------------|-----|
| /contact | http://cdn.example.com/style.css | Yes | Update to https:// |

## Link Reclamation Opportunities
| External Page | Mention/Context | Current Link Status | Our Replacement URL |
|--------------|----------------|--------------------|--------------------|
| blog.example.com/post | Brand mention, no link | N/A (unlinked) | /homepage |
| competitor-linker.com/resources | Links to dead resource | 404 | /our-equivalent-resource |

## Fix Commands (Copy-Paste Ready)
1. `claude "Find every file linking to '/old-team'. Replace with '/team'."`
2. `claude "Remove the dead link to '/products/removed' from /about. Rewrite surrounding text."`
3. ...
```

### Priority Order

Fix issues in this order:

1. **Internal 404s** — these are fully controllable and directly hurt user experience and crawl efficiency.
2. **Redirect chains** — each hop leaks PageRank and adds latency.
3. **Mixed content** — triggers browser warnings and undermines HTTPS.
4. **Soft 404 page** — confuses search engine crawlers.
5. **External 404s** — replace dead links to maintain content quality.
6. **Link reclamation** — pursue opportunities for new inbound links.

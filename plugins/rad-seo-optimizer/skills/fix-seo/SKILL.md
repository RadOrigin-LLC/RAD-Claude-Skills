---
name: fix-seo
description: >
  Fix my SEO, fix this SEO issue, fix missing meta, fix broken links, fix page speed
  code-level risk, fix schema — user has a specific SEO problem to remediate. Routes to
  specialized skills and applies fixes. For diagnosis without fixing, use full-seo-audit
  instead. Fixes that require numerical measurement (e.g., "fix my LCP to 2.5s") need a
  Path B MCP to verify — surfaced in the route.
argument-hint: "[SEO issue to fix] [--non-interactive]"
allowed-tools: Read Glob Grep Edit Write Bash WebFetch
---

# Fix SEO — Issue Router and Remediation

Fix the specified SEO issue by identifying all instances, explaining the impact, applying the fix, and verifying the result. Routes to the appropriate specialist skill when the fix category matches.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. Fix application is primarily code transforms + verification; all three models handle reliably.

## Execution: parallel-first

- **Issue identification**: Glob + Grep across the codebase in parallel
- **Bulk fixes** (e.g., adding alt text across multiple images): per-file Edits independent — batch
- **Verification**: re-reads post-fix independent — batch

---

## Fix Process

1. **Identify** all instances of the issue in the codebase.
2. **Explain** why this issue matters for rankings (plain English for a non-technical business owner).
3. **Show** the current state (what is wrong).
4. **Apply** the fix using the appropriate approach from `references/claude-code-fix-recipes.md`.
5. **Show** the after state (what was fixed).
6. **Verify** the fix is correct and no regressions were introduced.

---

## Issue Routing Table

Route each issue type to the appropriate specialist skill for deeper context and methodology.

| Issue Type | Route To | Examples |
|---|---|---|
| Title tags, meta descriptions, headings | **on-page-optimizer** | Missing meta, duplicate titles, heading hierarchy |
| Schema, structured data, JSON-LD | **schema-architect** | Missing schema, invalid markup, rich snippet issues |
| Page speed, Core Web Vitals, crawlability | **technical-seo** | Slow LCP, CLS issues, robots.txt problems |
| Broken links, 404 errors, redirect chains | **broken-link-fixer** | Dead links, redirect loops, mixed content |
| Content quality, E-E-A-T, keyword usage | **on-page-optimizer** | Thin content, missing author bios, keyword stuffing |
| Content gaps, editorial planning | **content-strategist** | Missing topics, outdated content, no content plan |
| AI visibility, AEO, LLM citations | **aeo-optimizer** | Not appearing in AI answers, inaccurate AI mentions |
| Competitor gaps, SERP features | **competitor-intelligence** | Losing to competitors, missing featured snippets |
| Keyword targeting, search intent | **keyword-discovery** | Wrong keywords, missing intent alignment |
| Backlink profile, link acquisition | **link-building-strategy** | Low domain authority, no backlink plan |
| Schema implementation details | **schema-architect** | FAQ schema, Product schema, Organization schema |

---

## Common Quick Fixes

### Missing Meta Descriptions
```
Scan every page for missing or duplicate meta descriptions. Add unique, 150-160 character
descriptions that include the target keyword and a call to action.
```

### Heading Hierarchy
```
Check every page for exactly one H1, logical H2-H6 nesting, no skipped levels. Fix any
violations while preserving content meaning.
```

### Missing Alt Text
```
Find every <img> missing an alt attribute. Add descriptive alt text that includes the
page's target keyword where natural. Keep each under 125 characters.
```

### Missing Schema Markup
```
Identify page type and generate appropriate JSON-LD schema. At minimum: Organization on
homepage, Article/BlogPosting on blog posts, BreadcrumbList on all pages.
```

### Broken Internal Links
```
Crawl all internal <a href> references and verify targets exist. Update or remove broken
links. Check for redirect chains and flatten them.
```

### Slow Page Speed
```
Check for render-blocking resources, unoptimized images, missing lazy loading, and
excessive third-party scripts. Apply fixes appropriate to the detected framework.
```

### Robots.txt Issues
```
Read robots.txt and verify no important paths are blocked. Ensure sitemap directive is
present. Remove overly broad wildcard rules.
```

---

## Fix Verification

After applying any fix, verify:

- The fix resolves the original issue.
- No new issues were introduced.
- The page still renders correctly.
- Any schema changes are valid JSON-LD.
- Internal links still resolve to 200 status codes.

Report the before and after state to the user with a summary of changes made.

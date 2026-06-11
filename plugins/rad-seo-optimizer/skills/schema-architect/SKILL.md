---
name: schema-architect
description: >
  Add schema, structured data, JSON-LD, rich snippets, schema markup, generate schema.
  Generates valid JSON-LD, validates existing markup, and identifies missing schema
  opportunities. Real deliverable — Claude reliably produces valid, typed JSON-LD.
  No Path B dependencies.
argument-hint: "[URL or page for schema] [--non-interactive]"
allowed-tools: Read Glob Grep Write Bash WebFetch
---

# Schema Architect

Generate valid, comprehensive JSON-LD structured data that earns rich results and optimizes pages for AI-driven search engines. This is one of the plugin's highest-utility skills — Claude reliably produces valid, typed JSON-LD from observable page content.

> **Reference**: See `schema-types-guide.md` for the full schema.org type catalog.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. Schema generation is a well-defined structured output task all three models handle reliably.

## Execution: parallel-first

- **Multi-page schema audits**: per-page Reads independent — batch
- **Schema validation per existing JSON-LD block**: parallel within a page
- **WebFetch for URL-based schema generation**: parallel per URL

---

## Phase 1: Page Type Identification

Analyze the target page and map it to one or more schema types.

| Page Kind | Primary Schema Types |
|---|---|
| Homepage | `Organization` + `WebSite` + `BreadcrumbList` |
| Blog post | `Article` / `BlogPosting` + `BreadcrumbList` + `FAQPage` (if Q&A present) |
| Product page | `Product` + `BreadcrumbList` + `Review` / `AggregateRating` |
| Service page | `Service` + `Organization` + `BreadcrumbList` |
| FAQ page | `FAQPage` + `BreadcrumbList` |
| How-to guide | `HowTo` + `BreadcrumbList` |
| Author / team | `ProfilePage` + `Person` |
| Contact page | `LocalBusiness` / `Organization` + `ContactPoint` |
| Event page | `Event` + `BreadcrumbList` |
| Recipe | `Recipe` + `BreadcrumbList` |
| Video page | `VideoObject` + `BreadcrumbList` |
| Job listing | `JobPosting` + `Organization` |

**Steps**:
1. Read the page source or URL provided by the user.
2. Inspect headings, meta tags, Open Graph data, and visible content blocks.
3. Select every applicable schema type (pages often need more than one).
4. If ambiguous, ask the user to confirm the page purpose before proceeding.

---

## Phase 2: Content Extraction

Populate every schema property from **real page data**. Never invent or use
placeholder values such as "Lorem ipsum" or "example.com".

Extract the following where available:

- **Core**: title, meta description, canonical URL, language.
- **Authorship**: author name, author URL, author image.
- **Dates**: published date, modified date (look in `<time>`, meta tags, CMS
  fields).
- **Images**: featured image, Open Graph image, product gallery images.
  Collect `url`, `width`, `height`, and `caption` when present.
- **Product details**: name, SKU, GTIN/UPC, price, currency, availability,
  brand, condition, reviews, aggregate rating.
- **FAQ pairs**: every visible question + answer on the page.
- **How-to steps**: ordered step text, step images, tools, supplies, total
  time.
- **Event details**: name, start/end dates, location (physical or virtual),
  performer, ticket URL, offers.
- **Video**: name, description, thumbnail URL, upload date, duration,
  content URL or embed URL.
- **Job posting**: title, description, date posted, valid through, hiring
  organization, salary, location.

If a required property cannot be found on the page, flag it in the output and
recommend the user add the missing content.

---

## Phase 3: Schema Generation

Generate complete JSON-LD wrapped in `<script type="application/ld+json">`.

### Rules

1. Include all **required** properties per Google's structured data docs.
2. Include as many **recommended** properties as the page data supports.
3. Nest related types properly (e.g., `author` as a full `Person` object
   inside `Article`, not a plain string).
4. Use **absolute URLs** everywhere -- never relative paths.
5. Format all dates as **ISO 8601** (`YYYY-MM-DDTHH:MM:SSZ` or with offset).
6. Reference images with full URLs and include `width`/`height` when known.
7. Use `@graph` to combine multiple types in a single script block when they
   share the same page context.

### Example Structure (Article)

```jsonld
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Extracted page title",          // Required -- max 110 chars
  "image": [
    "https://example.com/images/hero.jpg"      // Required -- at least one
  ],
  "datePublished": "2026-01-15T08:00:00Z",    // Required -- ISO 8601
  "dateModified": "2026-03-10T12:30:00Z",     // Recommended
  "author": {                                   // Required -- nest as Person
    "@type": "Person",
    "name": "Author Name",
    "url": "https://example.com/author"
  },
  "publisher": {                                // Recommended
    "@type": "Organization",
    "name": "Site Name",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  },
  "description": "Extracted meta description", // Recommended
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://example.com/article-slug"
  }
}
</script>
```

Provide **two versions** of every schema block:

1. **Minimal** -- required properties only. Useful for quick implementation.
2. **Complete** -- every recommended property the page data supports.

Add inline comments (`//`) explaining what each property does and why it
matters for rich results.

---

## Phase 4: Rich Snippet Opportunity Analysis

After generating schema for the current page, identify **additional** schema
types that could unlock rich result features the page is not yet using.

**Deprecation check first** (see `references/schema-types-guide.md`): Google retired
HowTo rich results (2023) and FAQ rich results entirely (May 2026), plus Book Actions,
Course Info, ClaimReview, Estimated Salary, Learning Video, Special Announcement, and
Vehicle Listing (June 2025). Still recommend `FAQPage`/`HowTo` markup where the content
fits — as AI-parsing aids — but never present them as rich-result opportunities.

| Rich Result Feature | Schema Required | Visual Benefit |
|---|---|---|
| Review stars | `Review` / `AggregateRating` | Star rating in snippet |
| Price & availability | `Product` + `Offer` | Price badge in results |
| Event dates | `Event` | Date/time + location in SERP |
| Recipe card | `Recipe` | Image, rating, cook time card |
| Video thumbnail | `VideoObject` | Video preview in results |
| Breadcrumb trail | `BreadcrumbList` | URL path replaced with breadcrumbs |
| Sitelinks searchbox | `WebSite` + `SearchAction` | Search box on branded queries |
| Speakable | `Speakable` (on `Article`) | Content read by voice assistants and AI |

For each opportunity found:
- Explain the expected SERP enhancement.
- Note any content the user would need to add to the page first.
- Rate the implementation effort (low / medium / high).

---

## Phase 5: Validation

Run every generated schema block through these checks before delivering it.

### Checklist

- [ ] All **required properties** present for every declared `@type`.
- [ ] Markup matches **visible page content** -- no hidden or fabricated data.
- [ ] The **most specific type** is used (`BlogPosting` over `Article` when
      applicable, `LocalBusiness` subtype over generic `LocalBusiness`).
- [ ] No **duplicate schema** for the same entity on the same page.
- [ ] Every URL is **absolute** (starts with `https://`).
- [ ] Every date is **ISO 8601** formatted.
- [ ] Referenced images **exist and are accessible** (flag any 404s).
- [ ] `@context` is set to `"https://schema.org"`.
- [ ] JSON is syntactically valid (no trailing commas, unquoted keys, etc.).

### External Testing

Recommend the user paste the final markup into:

1. **Google Rich Results Test** -- https://search.google.com/test/rich-results
   (note: no longer reports FAQ — support removed June 2026)
2. **Schema.org Validator** -- https://validator.schema.org/
   (also run the bundled `scripts/validate-jsonld.py` for a deterministic local check)
3. **Google Search Console** -- monitor the Enhancements report after
   deployment for errors or warnings.

---

## Phase 6: Integration Guidance

Provide copy-paste implementation instructions tailored to the user's stack.

### Next.js (App Router)

```tsx
// app/blog/[slug]/page.tsx
export default function BlogPost({ params }) {
  const jsonLd = { /* generated schema object */ };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={
          { __html: JSON.stringify(jsonLd) }
        }
      />
      {/* page content */}
    </>
  );
}
```

Use Next.js `metadata.other` or a dedicated head component as alternatives.

### React (Generic / Vite / CRA)

Create a reusable component:

```tsx
function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={
        { __html: JSON.stringify(data) }
      }
    />
  );
}
```

Render `<JsonLd data={schema} />` inside the page component. For SSR
frameworks (Remix, Gatsby), place it in the document head.

### WordPress

- **Plugin route**: Use Yoast SEO, Rank Math, or Schema Pro -- they auto-
  generate most types. Add custom schema via their "Custom Schema" UI.
- **Manual route**: Add a `wp_head` action in `functions.php` or paste the
  `<script>` block directly into a Custom HTML block in the editor.

### Static HTML

Place the `<script type="application/ld+json">` block immediately before
`</head>` or at the end of `<body>`. Both locations are valid; `<head>` is
conventional.

### Google Tag Manager

1. Create a **Custom HTML** tag.
2. Paste the full `<script type="application/ld+json">...</script>` block.
3. Set the trigger to fire on the relevant page(s).
4. Use GTM variables to inject dynamic values (product price, page title)
   when managing schema across many pages.

---

## Phase 7: AEO (Answer Engine Optimization) Schema Priorities

These schema types are critical for visibility in AI-powered search engines,
LLM-driven answers, and voice assistants.

| Schema Type | AEO Impact |
|---|---|
| `FAQPage` | LLMs extract Q&A pairs directly as answers. High citation rate. |
| `HowTo` | Step-by-step content is highly citable by AI summaries. |
| `Organization` | Defines the brand entity; helps AI attribute information correctly. |
| `Product` | Enables AI-driven product recommendations and comparisons. |
| `Speakable` | Explicitly marks sections for voice assistants and AI reading. |
| `Review` / `AggregateRating` | AI uses ratings to rank recommendations and surface trust signals. |

### AEO Implementation Notes

- **Always pair** `FAQPage` schema with visible FAQ content on the page.
  Google penalizes FAQ schema that does not match rendered content.
- **Add `Speakable`** to key introductory paragraphs and summary sections.
  Use CSS selectors or `xpath` to identify speakable blocks.
- **Keep `Organization` schema** on every page (via site-wide header/footer
  injection) so AI engines consistently associate content with the brand.
- **Combine `HowTo` with `FAQPage`** on tutorial pages -- the how-to
  captures the process and the FAQ captures common follow-up questions.

---

## Output Format

Every response from Schema Architect must include:

1. **Page type determination** with reasoning.
2. **JSON-LD code blocks** ready to paste, with `//` inline comments.
   - Minimal version (required properties only).
   - Complete version (all recommended properties the data supports).
3. **Rich snippet opportunities** not yet covered.
4. **Validation summary** confirming all checks pass (or listing issues).
5. **Integration snippet** for the user's framework (ask if unknown).
6. **AEO recommendations** highlighting which schema types to prioritize for
   AI search visibility.

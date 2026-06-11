# Schema Types Guide

Complete reference for SEO-relevant structured data types. Use JSON-LD format (Google's strong recommendation over Microdata/RDFa).

## Deprecation Status — read before recommending (current as of mid-2026)

Google has been steadily retiring rich result types. Recommending these for *rich
results* is stale advice; the markup remains valid schema.org and can still aid AI/LLM
parsing, but never promise SERP features from it:

- **HowTo** — rich results removed (Sept 2023)
- **FAQPage** — restricted to gov/health sites (2023), then dropped entirely (May 2026);
  Rich Results Test support removed June 2026
- **June 2025 retirements:** Book Actions, Course Info, ClaimReview (fact-check label),
  Estimated Salary, Learning Video, Special Announcement, Vehicle Listing

Still earning rich results and worth implementing: Organization, LocalBusiness, Product
/ Offer / Review / AggregateRating, Article, Event, Recipe, JobPosting, BreadcrumbList,
VideoObject. Google's official position on AI features: **no special schema is required**
for AI Overviews/AI Mode — standard indexability governs inclusion; schema's AI value is
entity disambiguation and clean parsing, not eligibility.

## Implementation Rules

1. **JSON-LD only** — easier to maintain, less error-prone, supports nesting, injectable via GTM
2. **Match visible content** — never mark up content hidden from users
3. **Use most specific type** — don't label woodworking instructions as Recipe
4. **Completeness over quantity** — fewer but highly complete properties beat many sparse ones
5. **Validate always** — use Google Rich Results Test before deploying

## Schema Types by Category

### Business & Organization
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| Organization | Every site (homepage) | name, url, logo, sameAs, contactPoint | Knowledge Panel |
| LocalBusiness | Physical locations | address, geo, openingHours, priceRange | Local Pack |
| ProfilePage | Author/team pages | mainEntity (Person), dateCreated | Enhanced profile |

### Content & Articles
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| Article | News/blog posts | headline, author, datePublished, image | Top Stories |
| BlogPosting | Blog content | Same as Article + blog-specific | Article rich result |
| HowTo | Step-by-step guides | step[], totalTime, tool[], supply[] | None (retired 2023) — AI-parsing aid only |
| FAQPage | FAQ sections | mainEntity[Question > acceptedAnswer] | None (retired May 2026) — AI-parsing aid only |
| QAPage | Single Q&A | mainEntity[Question > acceptedAnswer] | Q&A rich result |

### E-Commerce
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| Product | Product pages | name, image, offers, review, sku | Product snippet |
| ProductGroup | Variant products | productGroupID, variesBy, hasVariant | Grouped products |
| AggregateOffer | Price ranges | lowPrice, highPrice, offerCount | Price range display |
| MerchantReturnPolicy | Return info | returnPolicyCategory, returnWindow | Return info snippet |
| ShippingService | Shipping details | deliveryTime, shippingRate | Shipping snippet |
| MemberProgram | Loyalty programs | membershipPoints, tiers | Loyalty display |

### Reviews & Ratings
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| Review | Individual reviews | reviewRating, author, itemReviewed | Review stars |
| AggregateRating | Rating summaries | ratingValue, reviewCount, bestRating | Star snippet |
| EmployerAggregateRating | Employer reviews | ratingValue, reviewCount | Employer stars |

### Events & Courses
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| Event | Events/conferences | startDate, location, offers, performer | Event listing |
| Course | Educational content | name, provider, hasCourseInstance | Course Info retired June 2025 |
| CourseInstance | Specific offerings | courseMode, instructor, courseSchedule | Enhanced course |

### Media
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| VideoObject | Video content | name, uploadDate, thumbnailUrl, duration | Video carousel |
| Clip | Video segments | name, startOffset, endOffset | Key moments |
| BroadcastEvent | Live streams | isLiveBroadcast, startDate | LIVE badge |
| Movie | Film pages | name, director, dateCreated | Movie panel |
| Book | Book pages | name, author, isbn, workExample | Book Actions retired June 2025 |
| Recipe | Recipes | recipeIngredient, recipeInstructions, nutrition | Recipe card |

### Navigation & Structure
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| BreadcrumbList | All pages | itemListElement[position, name, item] | Breadcrumb trail |
| ItemList | List/carousel pages | itemListElement[], numberOfItems | Carousel |
| WebSite | Homepage | name, url, potentialAction[SearchAction] | Sitelinks searchbox |

### Professional & Jobs
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| JobPosting | Job listings | title, datePosted, hiringOrganization, salary | Job listing |
| EducationOccupationalProgram | Degree programs | programType, provider | Program listing |

### Specialized
| Type | Use When | Key Properties | Rich Result |
|------|----------|---------------|-------------|
| SoftwareApplication | Software/app pages | name, operatingSystem, offers, rating | App snippet |
| MathSolver | Math tools | potentialAction[SolveMathAction] | Math solver |
| ClaimReview | Fact checks | claimReviewed, reviewRating | Retired June 2025 |
| Speakable (BETA) | Voice/AI-ready content | cssSelector or xpath | Voice assistant |
| VacationRental | Rental listings | address, geo, numberOfRooms | Rental listing |

## JSON-LD Template

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "TypeName",
  "property1": "value1",
  "property2": {
    "@type": "NestedType",
    "nestedProperty": "value"
  }
}
</script>
```

## Framework Integration

### Next.js (App Router)
Use the `metadata` export or a `<Script>` component with `strategy="beforeInteractive"` to inject JSON-LD into the page head. Serialize the schema object with `JSON.stringify()`.

### React (General)
Create a `<JsonLd>` component that renders a `<script>` tag with `type="application/ld+json"` and the serialized schema data. Use a sanitization library if the data includes user-generated content.

### Static HTML
Place the `<script type="application/ld+json">` block directly in the `<head>` or `<body>` of your HTML.

### Google Tag Manager
Inject JSON-LD via Custom HTML tags — useful for sites where you can't modify source code directly.

## AEO-Critical Schema Types

These schema types are particularly important for AI search visibility (as parsing aids —
none of this is a Google rich-result promise; FAQPage and HowTo earn no rich results anymore):
1. **FAQPage** — LLMs extract Q&A pairs directly
2. **HowTo** — Step-by-step content is highly citable
3. **Organization** — Defines your brand entity for AI
4. **Product** — Enables AI product recommendations
5. **Speakable** — Explicitly marks content for voice/AI reading
6. **Review/AggregateRating** — AI uses ratings for recommendations

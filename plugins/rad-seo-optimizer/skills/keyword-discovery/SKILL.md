---
name: keyword-discovery
description: >
  Keyword research, find keywords, what keywords should I target, keyword analysis.
  Covers seed discovery, expansion, intent classification, qualitative difficulty
  assessment, and topic clustering. Produces 150-300 prioritized keywords. Does NOT
  return numerical search volumes or difficulty scores — those require a keyword-data
  MCP (DataForSEO / Ahrefs / Semrush — Path B). Instead, uses observable SERP signals
  for relative assessment.
argument-hint: "[topic or seed keyword] [--non-interactive]"
allowed-tools: Read Glob Grep Write Bash WebFetch WebSearch
---

# Keyword Discovery Skill

Walk the user through a complete keyword research pipeline, producing a prioritized keyword plan they can act on immediately. Assume the user has never done keyword research before — explain every concept in plain language, but keep the process moving.

## Cross-model note

Works identically on current Opus / Sonnet / Haiku models. Expansion + intent classification + clustering all benefit from batch parallelism where per-keyword work is independent.

## Execution: parallel-first

- **Phase 1 seed gathering**: user interview serializes naturally
- **Phase 2 expansion**: long-tail / question / modifier / LSI / medium-tail expansion runs per-seed; per-seed WebSearch-autocomplete checks parallelize
- **Phase 3 intent classification**: per-keyword SERP inspection independent — batch WebSearch calls
- **Phase 4 difficulty assessment**: per-keyword SERP + competitor inspection independent — batch
- **Phase 5 clustering**: synthesis step, not parallelizable
- **Phase 6 prioritization**: synthesis step, not parallelizable

## Capability Honesty

Read `references/CAPABILITIES.md`. Key constraints:
- **Real search volume numbers** (e.g., "1,200 searches/month") require a keyword-data API — Path B
- **Real keyword difficulty scores** (e.g., "KD 42") require link-graph + SERP competitor strength — Path B
- **What this skill DOES provide**: observable SERP signals (who ranks, SERP feature presence, autocomplete prominence, competition density) interpreted qualitatively (High/Medium/Low, Easy/Moderate/Hard)

When the user wants real numbers, recommend a DataForSEO / Ahrefs / Semrush MCP integration.

## Mode Flags

- `--non-interactive` — Use reasonable defaults for Phase 1 questions, record unanswered items in `awaiting_user_review`

---

## Overview

Six phases in order:

1. **Seed Keyword Discovery** — gather raw inputs
2. **Keyword Expansion** — broaden the list
3. **Search Intent Classification** — tag every keyword
4. **Qualitative Difficulty Assessment** — observable competition signals
5. **Topic Cluster Mapping** — organize into hierarchy
6. **Prioritization** — produce ranked action plan

Work through each phase sequentially. Present findings after each phase before moving on.

---

## Phase 1: Seed Keyword Discovery

### Gather Context

Before generating a single keyword, ask:

1. **Business basics** — What does the business do? Products / services?
2. **Target audience** — Ideal customers? Language / jargon they use?
3. **Top 3 competitors** — Up to three main rivals (URLs or brands)
4. **Existing keywords** — Already targeting any? List them, or "none"

### Seed Sources

Mine seeds from every source below:

| Source | What to extract |
|---|---|
| **Business context** | Industry terms, product names, service categories, brand modifiers |
| **Competitor analysis** | Terms competitors rank for (from WebSearch of competitor sites); recurring themes in their title tags, H1s, meta descriptions |
| **Customer language** | Phrases from support tickets, reviews, forum posts, testimonials — words *customers* use, not marketing copy |
| **Question mining** | Questions from Reddit, Quora, "People Also Ask" boxes (observable via WebSearch) |
| **Google autocomplete** | Type each seed + capture suggested completions; same for YouTube + Amazon if relevant |
| **Internal site search** | If available, top queries visitors type on-site |

Deliver as a numbered table. Aim for **30-50 seed keywords** before moving on.

---

## Phase 2: Keyword Expansion

Expand each seed using four strategies. Go from ~40 seeds to **150-300 candidate keywords**.

### 2a. Long-Tail Variations (3-5 word phrases)
Add specificity. Long-tail keywords convert better because they match precise needs.

### 2b. Question-Based Keywords
Prepend: who, what, when, where, why, how.

### 2c. Modifier Keywords
- **Best / Top / Review / Comparison / vs** — commercial intent
- **Alternative / Cheap / Free** — budget-conscious buyers
- **Near me / [City]** — local intent
- **Template / Example / Checklist** — resource seekers
- **For beginners / For enterprises / For [audience]** — audience fit

### 2d. LSI / Semantic Keywords
Related terms that appear alongside the seed in top-ranking content.

### 2e. Medium-Tail Keywords
"Sweet spot" — 2-3 words, moderate competition. Often fastest wins.

Group the expanded list by strategy so the user can see where each keyword came from.

---

## Phase 3: Search Intent Classification

Every keyword gets exactly one intent tag.

### Intent Types

| Intent | Signal words | What Google shows |
|---|---|---|
| **Informational** | how to, what is, guide, tutorial, why, tips | Blog posts, Wikipedia, knowledge panels, videos |
| **Commercial** | best, top, review, comparison, vs, alternative | Listicles, review sites, comparison tables |
| **Transactional** | buy, price, discount, coupon, sign up, download | Shopping results, product pages, pricing pages |
| **Navigational** | [brand name], login, support, contact, app | Official site, login, app store |

### How to Classify

Look at the actual SERP (WebSearch):
- Shopping carousel / product ads → Transactional
- Video pack or PAA → likely Informational
- Comparison articles dominate → Commercial
- Single brand dominates positions 1-3 → Navigational

Mixed intent → label dominant, note secondary.

Add an "Intent" column to the keyword table.

---

## Phase 4: Qualitative Difficulty Assessment

**Honest framing**: This phase uses observable SERP signals to estimate relative difficulty (Easy / Moderate / Hard). It does NOT produce numerical difficulty scores. For real Keyword Difficulty metrics, integrate a DataForSEO / Ahrefs / Semrush MCP (Path B).

### Factors to Evaluate (per target keyword, batch WebSearch)

| Factor | Easy signal | Hard signal |
|---|---|---|
| **Who ranks now** | Forums, small blogs, thin content | Major brands, .gov, Wikipedia |
| **Content format** | Short articles, outdated posts | In-depth guides, interactive tools |
| **SERP features** | Featured snippet available | Knowledge panel from Wikipedia |
| **Commercial value** | No ads = lower commercial value | Heavy ads = lucrative but competitive |
| **Domain diversity** | 10 different domains on p1 | 3 domains own 7 results |
| **Content age** | Many results from 3+ years ago | All results from last 6 months |

### Difficulty Scale (qualitative)

- **Easy**: Thin/outdated content ranks; few strong domains; featured snippet available. Well-written article can rank in weeks.
- **Moderate**: Mix of strong and weak pages; requires comprehensive content + some backlinks. Expect 2-6 months.
- **Hard**: P1 is all high-authority with deep content. Requires significant authority, backlinks, time (6-12+ months).

Add "Difficulty" and "Observed Opportunity" columns:

```
#  | Keyword | Intent | Difficulty | Observed Opportunity
1  | project management for nonprofits | Commercial | Easy | Featured snippet slot available, weak top-3
2  | project management software | Commercial | Hard | Heavy ad spend, strong DR domains
```

### Volume Signal (qualitative, not numerical)

Use observable signals to estimate relative volume:
- **High signal**: prominent autocomplete, multiple SERP features, heavy ad coverage
- **Medium signal**: autocomplete present, some SERP features
- **Low signal**: no autocomplete, thin SERP, no ads

Do NOT invent "monthly search volume" numbers. Mark relative volume as High/Medium/Low.

---

## Phase 5: Topic Cluster Mapping

Organize keywords into a content hierarchy.

### Hierarchy

```
Pillar Topic (broad, 1-2 words, high relative volume)
  +-- Subtopic A (medium-tail, 2-3 words)
  |     +-- Long-tail query 1
  |     +-- Long-tail query 2
  +-- Subtopic B
        +-- Long-tail query 3
        +-- Long-tail query 4
```

### How to Build Clusters

1. **Identify pillars** — broadest, highest-relative-volume terms → comprehensive pillar pages (2,000-4,000 words)
2. **Group subtopics** — medium-tail as subtopics → supporting articles (1,000-2,000 words)
3. **Attach long-tail** — become sections within subtopic articles, standalone FAQ entries, or short posts
4. **Map internal links** — every subtopic links up to pillar; pillar links down to every subtopic; subtopics in same cluster link to each other where relevant

Present the full cluster map and confirm with the user before prioritization.

---

## Phase 6: Prioritization

### Scoring Criteria (qualitative)

| Criterion | Scale | Description |
|---|---|---|
| **Business relevance** | 1-10 | How closely does this keyword relate to the product/service? |
| **Volume signal (relative)** | High / Medium / Low | From observable SERP signals — NOT numerical volume |
| **Competition level** | Easy / Moderate / Hard | From Phase 4 |
| **Content gap** | Yes / No | Does the site already have content targeting this? |
| **Estimated effort** | Low / Medium / High | Time + resources to create ranking content |

### The Three Lists

#### 1. Top 10 Quick Wins
Keywords where content already exists (or is easy to create), competition signals easy, rank in weeks.

#### 2. Top 10 Strategic Targets
High-relevance with moderate competition. Dedicated content + some link building. Expect results in 2-6 months.

#### 3. Top 10 Long-Term Plays
High-competition, high-reward. Build toward these by first ranking for easier related keywords.

### Content Type Recommendations

| Content Type | When to use |
|---|---|
| Blog post | Informational long-tail, how-tos |
| Landing page | Transactional, product comparisons |
| Comprehensive guide | Pillar topics, informational medium-tail |
| Tool or calculator | "Calculator", "template", "generator" queries |
| Video | "How to" queries where Google shows video results |
| FAQ section | Question-based long-tail |
| Case study | "[Industry] + results/example" |

### The 70/20/10 Content Mix

- **70% Foundation** — how-to guides, tutorials, listicles, FAQ. Safe, proven formats. Start here.
- **20% Growth** — original research, data-driven posts, expert roundups, detailed comparisons. Higher effort, differentiates.
- **10% Moonshots** — interactive tools, contrarian pieces, original frameworks, viral-potential content. Most underperform but wins are outsized.

Tag each content calendar entry with its mix category.

---

## Delivery Checklist

- [ ] 30-50 seed keywords with sources
- [ ] 150-300 expanded keywords grouped by strategy
- [ ] Every keyword tagged with search intent
- [ ] Top 50+ keywords assessed for qualitative difficulty
- [ ] Complete topic cluster map with pillar-subtopic hierarchy
- [ ] Internal linking plan between cluster pages
- [ ] Top 10 Quick Wins with specific actions
- [ ] Top 10 Strategic Targets with content recommendations
- [ ] Top 10 Long-Term Plays with cluster-building roadmap
- [ ] Content type recommendation for each priority keyword
- [ ] 70/20/10 mix labels on all recommended content
- [ ] Measurement-gaps note: "For numerical search volumes and KD scores, integrate a DataForSEO / Ahrefs / Semrush MCP"

## Tone and Style

- Plain language. Define jargon first time used.
- Specific actions. "Write a blog post" is not actionable. "Write a 2,000-word comparison of X vs Y targeting commercial intent" is.
- Tables for any list > 5 items.
- Summary after each phase.
- When lacking real search volume data, say so honestly and use relative estimates based on observable signals.

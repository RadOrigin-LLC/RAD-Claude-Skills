# AI Crawl Access — robots.txt, CDN blocking, llms.txt, and machine-readability signals

The AI-crawl layer is the 2026 addition to technical SEO: which AI systems can fetch
your content, and whether your declared policy (robots.txt) matches what your CDN
actually serves. Use `scripts/audit-ai-access.py` for the deterministic checks; this
reference is the knowledge behind its findings.

## The two classes of AI bots — the load-bearing distinction

Blocking the wrong class is the most common AI-access mistake. Always audit and report
the two classes separately:

**Citation / search class — blocking these makes you invisible in AI answers:**

| User-agent | Operator | Role |
|---|---|---|
| `Googlebot` | Google | Google Search index — also powers AI Overviews and AI Mode |
| `Bingbot` | Microsoft | Bing index — powers Copilot and (partially) ChatGPT Search |
| `OAI-SearchBot` | OpenAI | Builds the ChatGPT Search index |
| `ChatGPT-User` | OpenAI | Live fetch when a ChatGPT user asks about your pages |
| `Claude-SearchBot` / `Claude-User` | Anthropic | Claude search indexing / live user fetch |
| `PerplexityBot` / `Perplexity-User` | Perplexity | Perplexity answer index / live user fetch |

**Training class — blocking these is a content-licensing choice with NO effect on AI answer visibility:**

| User-agent | Operator | Notes |
|---|---|---|
| `GPTBot` | OpenAI | Model training |
| `ClaudeBot` | Anthropic | Model training |
| `Google-Extended` | Google | Gemini training/grounding ONLY — see below |
| `CCBot` | Common Crawl | Corpus feeds many training sets |
| `Applebot-Extended` | Apple | AI training opt-out token |
| `Meta-ExternalAgent` | Meta | AI training |
| `Bytespider` | ByteDance | Documented history of ignoring robots.txt |
| `Amazonbot` | Amazon | Alexa/AI |

**Recommended posture for a site that wants AI citations (AEO):** explicitly allow the
entire citation class; set the training class per the owner's licensing preference and
say clearly that it won't change AI answer visibility either way.

## Google-Extended is not an AI Overviews opt-out

AI Overviews and AI Mode are built from **Googlebot's** index. `Google-Extended` only
controls Gemini training/grounding. To control AI-feature appearance, the levers are:

- **Search Console AI-features control** (shipped June 2026, UK-first rollout) — opt out
  of AI Overviews / AI Mode / Discover AI without a ranking penalty.
- `nosnippet` / `max-snippet` robots meta — Google confirmed these apply to AI
  Overviews/AI Mode, but they also kill regular snippets (CTR tradeoff).

Flag any audit narrative that implies blocking Google-Extended removes a site from AI
Overviews — that's a widespread misconception.

## Declared policy vs. actual behavior — CDN blocking

Since July 2025, **Cloudflare blocks known AI crawlers by default on new domains** and
runs a pay-per-crawl marketplace. Akamai/Fastly offer similar bot management. Result:
robots.txt can say Allow while the WAF returns 403 to every AI bot — the site owner
usually doesn't know.

- A static robots.txt parse alone is therefore insufficient. `audit-ai-access.py
  --check-fetch` probes the origin with AI user-agent strings and compares against a
  browser-UA baseline.
- Caveat to always state: some WAFs verify crawler IP ranges, so a spoofed-UA probe is
  indicative, not proof, in either direction. Server logs are the ground truth.

## llms.txt — both truths, stated honestly

- **Not a Search or citation factor.** Google's John Mueller: no AI system uses llms.txt
  for ranking; server-log studies show ~0.1% of AI-bot requests touch it; a 300k-domain
  study (Nov 2025) found no correlation with AI citations. Never score its absence as a
  failure, and never promise ranking/citation gains from adding it.
- **But it is institutionalized.** Chrome's Lighthouse now ships an experimental
  **Agentic Browsing** category whose llms.txt audit recommends a spec-compliant file at
  the site root (404 = Not Applicable; only a server error fails). Developer-tool
  ecosystems (Mintlify, Vercel, Supabase, MCP doc servers) generate and consume it, and
  browsing agents may use it as a cheap site map. See `references/agent-readiness.md`.
- **Recommendation language:** "Cheap to add, recommended by Lighthouse's agentic-browsing
  audits, may help browsing agents — will not change rankings or AI citations."
- **Format (llmstxt.org):** H1 title, optional `>` blockquote summary, `##` sections of
  `- [Title](url): description` links. `llms-full.txt` is the concatenated full-content
  variant.

## Other declarative signals (report informationally, never pass/fail)

- **Content Signals Policy** (Cloudflare, Sept 2025): `Content-Signal: search=yes,
  ai-input=no, ai-train=no` lines in robots.txt. Preference declaration; compliance is
  voluntary and Google has not committed to honoring `ai-input`.
- **RSL (Really Simple Licensing)** 1.0 (Dec 2025): `License:` directive in robots.txt /
  headers / RSS for machine-readable licensing. Backed by CDNs and publishers; no
  foundation-model operator has agreed to honor it yet.
- **noai / noimageai** robots meta (DeviantArt-originated): non-standard, voluntary,
  unevenly honored. Flag a conflict if present on a site that wants AI citations.
- **IndexNow:** instant URL submission to the Bing index — the index ChatGPT Search,
  Copilot, and DuckDuckGo draw from. Free, 10k URLs/day. The closest thing to a
  freshness lever for AI answers. Google does not support it.

## JS-dependence — the highest-impact AI-access finding

**No major AI crawler executes JavaScript.** Analyses of 500M+ GPTBot fetches show zero
JS execution; only Googlebot renders. Client-side-rendered content is invisible to
ChatGPT, Claude, and Perplexity even when every bot is allowed.

- Heuristic check (in `audit-ai-access.py`): near-empty visible text + scripts present +
  SPA shell markers (`<div id="root">`, `id="app"`, `id="__next"`).
- Definitive check: diff raw-HTML text against rendered DOM (browser MCP — Path B).
- Fix direction: SSR or prerender any page whose content should be citable by AI.

## Auditing order

1. Parse robots.txt → per-bot matrix (training vs citation), flag per class.
2. With an origin: `--check-fetch` UA probes for CDN-level mismatch.
3. llms.txt existence + format shape (informational).
4. Content-Signal / RSL / noai detection (informational).
5. JS-dependence heuristic on key templates/pages (warning).
6. Bing presence: since Bing's index feeds ChatGPT Search and Copilot, confirm Bingbot
   access + recommend Bing Webmaster Tools (its AI Performance report, public preview
   Feb 2026, shows actual Copilot citation counts — the only free AI-citation telemetry).

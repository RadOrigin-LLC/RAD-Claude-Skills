---
name: draft-pitch
description: >
  This skill should be used when the user says "draft a pitch", "write a pitch for [project]",
  "one-pager", "executive summary", "investor pitch", "grant proposal", "pitch deck content",
  "partnership memo", "draft a funding pitch", "write a long-form pitch", or wants a longer-form
  pitch document (one-pager, executive summary, or deck-equivalent text) for a project. Different
  shape from `elevator-pitch` (which is the ~150-word compressed version). `draft-pitch` is for
  funding applications, grant proposals, partnership memos, and pitch-deck text. Output is grounded
  in repo source via check-grounding.py; no overpromising via check-overpromise.py.
argument-hint: "[--shape one-pager|exec-summary|deck-content] [--audience investor|grant|partner] [--output <path>] [--repo <path>]"
user-invocable: true
allowed-tools: Read Glob Bash Write Edit Grep WebSearch
---

# Draft Pitch — One-pager / executive summary / deck-equivalent

You are drafting a longer-form pitch document. Three shape options; choose based on the user's stated need:

- **`one-pager`** (~500-700 words) — single-page document for sharing with potential funders, partners, or stakeholders
- **`exec-summary`** (~300-500 words) — denser front-matter for a longer proposal or memo
- **`deck-content`** (~600-1000 words, structured into slide-shaped sections) — text content for a pitch deck (slide titles + 2-4 bullet points per slide; user assembles the actual visual deck)

All three are LONGER than `elevator-pitch` (~150 words) but SHORTER than a full proposal. They serve as the first-touch document a reviewer sees.

## Foundational rules

1. **Grounded.** Every substantive claim must trace to repo source. Quantitative claims (user counts, revenue, traction metrics) must be backed by repo evidence (a stats file, a metrics dashboard reference, a README line, etc.) or labeled as estimates/projections.
2. **Not overpromising.** No superlatives. No "the only" without backing. No vague-quantity claims without enumeration. The validators will catch these; pre-edit so they don't have to.

## Audience modes

### `investor` (default for `one-pager` / `exec-summary`)

For a VC, angel, or accelerator evaluating commercial potential.

Required sections:
1. **The opportunity** (problem + market context, 1 paragraph)
2. **What we're building** (solution shape, 1-2 paragraphs)
3. **Why now** (timing — what's changed that makes this viable, 1 paragraph)
4. **Who it's for** (target customer in measurable terms, 1 paragraph)
5. **Differentiation** (vs named alternatives — concrete, not superlative, 1 paragraph)
6. **Stage and traction** (current metrics, growth trajectory, what's been validated, 1 paragraph)
7. **The team** (only if user-provided; do NOT invent)
8. **Business model** (how money flows, 1 paragraph)
9. **What we're asking for** (only if user-specifies; do NOT invent)

### `grant`

For an academic, foundation, or government grant application.

Required sections (most grants want):
1. **Project summary** (1 paragraph)
2. **Problem and significance** (the public/scientific/social good case)
3. **What we'll do** (specific activities)
4. **What we'll produce** (deliverables)
5. **Why we can do it** (capability — only what traces to source)
6. **Budget and timeline** (only if user-provided)
7. **How we'll measure success**

### `partner`

For a potential integration / co-marketing / strategic partnership.

Required sections:
1. **What we offer** (capabilities)
2. **What we're looking for** (the ask)
3. **Mutual fit** (why this partnership specifically)
4. **Integration shape** (technical: APIs, data flows, joint go-to-market shape)
5. **Stage and timing**

## Shape: deck-content

When `--shape deck-content`, structure the output as slide-shaped sections.

Each "slide" is:
- A 4-8 word slide title (H2)
- 2-4 bullet points (each ~10-15 words)
- An optional "speaker note" paragraph below

Standard deck shape (8-12 slides):

1. Title slide (project name + one-line description)
2. The problem (what's broken in the world)
3. The solution (what we built)
4. How it works (architecture / flow / mechanism)
5. Market / audience (who needs this)
6. Differentiation (vs named alternatives)
7. Traction (metrics, milestones, validated outcomes)
8. Business model (if applicable)
9. Team (if user-provided)
10. Ask + timeline
11. Closing slide

Skip slides without source backing; don't invent.

## Workflow

### Step 1: Determine shape and audience

If `--shape` and `--audience` were both passed, proceed. Otherwise ask:

```
What shape?

  1. One-pager (~500-700 words) — single-page share
  2. Executive summary (~300-500 words) — proposal front-matter
  3. Deck content (~600-1000 words) — pitch deck text

Who's it for?

  1. Investor (VC / angel / accelerator)
  2. Grant (academic / foundation / government)
  3. Partner (integration / co-marketing / strategic)
```

### Step 2: Confirm output target

Offer:

- `PITCH.md` / `EXEC-SUMMARY.md` / `DECK.md` at repo root
- `docs/pitch/<audience>-<shape>.md` (in-repo persistence)
- Custom path

### Step 3: Read source

In parallel:

- `README.md`
- `package.json` / `pyproject.toml` / similar manifest
- `docs/vision.md` (if present) — primary source for problem/solution/audience
- `docs/architecture.md` (if present) — for solution shape
- `docs/roadmap.md` (if present) — for stage and trajectory
- `docs/status.md` (if present) — for current metrics
- `docs/decisions/*.md` (if present) — for differentiation, why-this-choice context
- Recent commits via `git log --oneline -20` — for stage signal
- For investor pitch: optionally search web for the named alternatives the user mentions (verify they exist; don't invent competitors)

### Step 4: Surface gaps before drafting

Before writing, surface to the user:

```
Source coverage for {shape} / {audience}:

  ✓ Have: {list of sources found}
  ✗ Missing: {list of sources not found, with what they would have provided}

Substantive gaps that would weaken this pitch:
  {list — e.g., "no team section because no team info in repo", "no traction
   metrics because no docs/status.md or analytics file", etc.}

How to proceed:
  1. Draft what's possible from the available sources; flag gaps as TODO inline
  2. Pause; you fill in the gaps first, then come back
  3. Draft with placeholders; you fill in before sending
```

### Step 5: Draft section by section

For each section:

1. Pull source content
2. Convert to audience-appropriate prose
3. Cross-check every claim against source
4. If claim has no source: drop, soften, or mark as TODO/placeholder (never invent)

### Step 6: Run validators

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-grounding.py {output-path} --repo <repo-root> --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-overpromise.py {output-path} --json
```

For investor pitches especially: any superlative or vague-quantity claim that the validators flag is one a real investor will ask about in due diligence. Better to fix it now.

### Step 7: Surface what you did

```
Pitch written to {path}.

Shape: {one-pager | exec-summary | deck-content}
Audience: {investor | grant | partner}
Word count: {N}
Sources used: {list}
Sections with source backing: {N} / {M}
Sections with TODO/placeholder (you need to fill these): {list}
Validators: grounding {pass|N flagged}, overpromise {pass|N flagged}

Specific things to verify before sending:
  - {list of claims that needed user judgment to keep}
  - {team/financial/legal claims user must provide}
```

## Rendering rules

- Specific verbs and nouns. "rad-explain runs a grounding validator that flags untraceable claims" > "rad-explain provides advanced validation capabilities."
- Concrete numbers when source-backed. Range them honestly when uncertain ("v0.1.0 with 5 skills + 2 validators", "in active use across [N] projects this month").
- Comparison-shaped differentiation. "Unlike X, we do Y because Z" — not "the best at A."
- Cite alternatives by name. "ChatGPT will puff your project; rad-explain flags the puff" is better than "other tools puff your project."
- One claim per sentence in the heavy-traffic sections (Solution, Differentiation, Traction).

## Cross-plugin notes

- For a much shorter pitch (~150 words / 30 seconds spoken), use `elevator-pitch`.
- For a full project narrative, use `narrate-project` in this plugin.
- For interpreting a specific repo file or plan, use `explain-document` in this plugin.
- Both validators live in this plugin's `scripts/` dir.

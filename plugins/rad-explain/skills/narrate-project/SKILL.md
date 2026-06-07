---
name: narrate-project
description: >
  This skill should be used when the user says "narrate this project", "explain this project in
  plain English", "describe what this repo does", "summarize this project for a non-developer",
  "write a project narrative", "tell me what this project is", "explain this codebase to a
  collaborator", "draft an onboarding brief", "explain this project to my parents", "non-dev summary",
  or wants a plain-language description of a project synthesized from its source artifacts (code,
  docs, planning files, README, package.json). Works on any repo. Adapts to the named audience.
  Every substantive claim in the output is grounded against the repo source via check-grounding.py;
  no overpromising via check-overpromise.py. The output is prose for a human reader, not a planning
  artifact.
argument-hint: "[--audience non-dev|investor|future-self|new-collaborator] [--output <path>] [--repo <path>]"
user-invocable: true
allowed-tools: Read Glob Bash Write Edit Grep
---

# Narrate Project — Plain-English description from repo source

You are synthesizing a plain-language description of a project from whatever artifacts the repo actually has. The deliverable is **prose for a human reader**: someone who needs to understand what the project is, who it's for, and what it does, without reading the code.

This skill is the **cross-project default** in rad-explain. It works on any repo whether or not rad-planner is in use. It reads a `docs/` directory if present (a PRD, plan, decision log) and falls back to README + manifest + source structure otherwise.

## Foundational rules

Both rules are enforced by validators at the end of generation. If either fails, surface the findings to the user and offer to revise before writing.

1. **Grounded.** Every substantive claim must trace to repo source. The `check-grounding.py` validator runs against the output before it's finalized.
2. **Not overpromising.** No superlatives, marketing fluff, vague-quantity claims without enumeration, or sensational framing. The `check-overpromise.py` validator runs against the output.

If you find yourself wanting to write something that's NOT in the source, **surface it to the user as a gap** rather than inventing it.

## Input — adaptive to what the repo has

Try these in order. Stop reading once you have enough material for the chosen audience.

| Priority | Source | Why |
|---|---|---|
| 1 | `docs/vision.md` / `docs/architecture.md` / `docs/planning/current.md` / `docs/status.md` / `docs/decisions/*.md` (rad-planner canonical structure) | Highest-signal — these were authored for synthesis use |
| 2 | `README.md` at repo root | Almost always present; primary user-facing description |
| 3 | `package.json` `description` field, `pyproject.toml` `description`, similar manifests | One-line product summary |
| 4 | `AGENTS.md` / `CLAUDE.md` | Operating-manual content; secondary signal |
| 5 | `CHANGELOG.md` / `docs/roadmap.md` | What's been built and what's next |
| 6 | Source structure: top-level directories, file names | What the codebase is shaped to do |
| 7 | Source content: imports, exports, public APIs | What the codebase actually exposes |
| 8 | `tests/` or `__tests__/` directories | What's verified to work |

If a `docs/` directory is present (a PRD, plan, decision log), read it for richer, source-grounded coverage; otherwise fall back to README + manifest + source structure.

## Audience modes

Adapt the narrative depth, vocabulary, and section emphasis based on the audience.

### `non-dev` (default if not specified)

For someone who isn't a developer: a family member, a stakeholder, a friend, a marketing partner.

- Plain English only. No code terms unless explained in plain words.
- Lead with "what it does for whom" not "what tech stack it uses."
- Skip the code architecture entirely. Skip jargon.
- Length: short. ~80-150 lines.
- Output a single Markdown file with H2 headings and short paragraphs.

Sections:
1. **What this project is** (one paragraph, one-liner first)
2. **Who it's for** (the actual humans served)
3. **What it does that's useful** (concrete capabilities)
4. **What it doesn't do** (scope boundaries — from any "non-goals" section, or inferred from project size)
5. **Where it is** (live / WIP / planning / experimental — based on git history + last commit + version)

### `investor`

For someone evaluating commercial potential.

- Lead with the problem and the solution
- Quantify what's known (users, downloads, traction); be explicit about what's not yet measured
- Highlight differentiation (what no one else has) — only if it traces to source
- Surface stage, business model (if any), and what's next

Sections:
1. **What this project is** (one line + paragraph)
2. **Who it's for** (target market shape)
3. **The problem we're solving** (and the alternative)
4. **Where it is** (stage, key metrics where known)
5. **What's next** (next milestone, timeline if known)
6. **Open questions** (honest about what's not figured out yet)

### `future-self`

For the project author returning after time away.

- Bias toward "what I'll forget" — decisions made, things tried that didn't work, why things are the way they are
- Highlight current-state context: what's broken, what's WIP, what's queued
- Skip product-marketing language entirely; this is a working note

Sections:
1. **What this is** (refresher line)
2. **Where you left off** (from `status.md` or recent commits)
3. **What's done** (locked / shipped)
4. **What's in progress** (with current state and known-blocker info)
5. **Decisions worth remembering** (from `decisions/` or commit history)
6. **What's next** (concrete next action)

### `new-collaborator`

For someone joining the project who needs to ramp up.

- Lead with project shape: what code lives where, what's the entry point, where to start reading
- Surface key conventions (from `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md`)
- Highlight decisions that constrain how they should work
- Point at the tests / docs / build commands

Sections:
1. **What this project is** (orientation)
2. **What's where** (repo map)
3. **How to run it** (install / dev / test commands)
4. **Conventions to know** (from operating manual)
5. **What's currently being worked on** (current.md / status.md or recent commits)
6. **Decisions that matter** (locked architectural choices)
7. **Where to start** (concrete first-PR / first-issue suggestions if possible)

## Workflow

### Step 1: Determine audience

If `--audience` was passed, use it. Otherwise ask:

```
Who is this narrative for?

  1. Non-dev / general audience (default)
  2. Investor / commercial evaluator
  3. Future-self / working note
  4. New collaborator / onboarding
```

### Step 2: Determine output path

If `--output` was passed, use it. Otherwise offer:

- `PROJECT-NARRATIVE.md` at repo root (temporary share)
- `docs/narrative.md` (in-repo persistence)
- Custom path

### Step 3: Read source artifacts

In parallel, gather what's available. **Always read** `README.md`, `package.json` / `pyproject.toml` / `Cargo.toml` / equivalent manifest. **If present**, also read the rad-planner canonical doc set, `AGENTS.md` / `CLAUDE.md`, `CHANGELOG.md`, top-level directory structure.

If a `docs/` directory is present (a PRD, plan, decision log), read those for richer, source-grounded coverage.

### Step 4: Synthesize section by section per audience

For each section:

1. Pull source content
2. Convert to plain-language prose at the audience level
3. **Cross-check:** does every claim trace to a source you read?
   - If yes → keep
   - If no → either drop the claim, or surface as a gap to the user before writing

### Step 5: Run validators against the draft

Before writing the final output:

```bash
# Use /tmp/draft.md as a temporary location
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-grounding.py /tmp/draft.md --repo <repo-root> --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-overpromise.py /tmp/draft.md --json
```

If either validator returns findings:

1. Surface a brief summary to the user (how many findings, severities)
2. Offer to revise (default), accept-as-is, or abort
3. If revising, regenerate the flagged sections and re-validate

### Step 6: Write the final file

Single Markdown file. No frontmatter. H2 section headings.

Add a footer:

```
*Generated by /rad-explain:narrate-project on YYYY-MM-DD. Audience: {audience}.
Grounding: {N claims traced} / {M total}.  Overpromise scan: {clean | N findings}.
Sources used: {file list}.*
```

### Step 7: Surface what you did

A 5-line summary to the user:

```
Project narrative written to {path}.

Audience: {audience}
Sources read: {comma-separated list of files}
Validators: grounding {pass|N flagged}, overpromise {pass|N flagged}
Sections written: {list}
```

## Rendering rules

- Plain English. No jargon unless `README.md` or `vision.md` itself uses it.
- No marketing language. The validators will catch most of it; you should self-edit first.
- Voice: knowledgeable narrator, not breathless, not corporate. Match the existing project voice if there is one.
- Length proportional to project complexity. A README-only repo gets a short narrative. A full rad-planner-shaped project gets longer.
- Don't invent. If a section has no source backing, omit it and note the gap to the user.

## Cross-plugin notes

- Reads a `docs/` directory if present; otherwise works from README + manifest + source structure.
- The two validators (`check-grounding.py` and `check-overpromise.py`) live in this plugin's `scripts/` dir; they can be invoked by other plugins too.
- This skill does NOT write to canonical docs. It reads them; never modifies them.

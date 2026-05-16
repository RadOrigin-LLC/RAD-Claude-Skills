---
name: explain-document
description: >
  This skill should be used when the user says "explain this document", "interpret this file",
  "what does this plan commit me to", "what does this ADR say", "interpret this architecture doc",
  "what does this AI-generated plan actually mean", "decompile this doc", "what's this file saying",
  "explain this to me in plain English", "what are the implications of this doc", "where could this
  plan go wrong", or wants a specific repo file (a plan, an ADR, an architecture spec, an
  AI-generated proposal, a contract-shaped doc, a config file) interpreted in plain English with
  attention to what it commits to, what it assumes, and where it could go wrong.
argument-hint: "<file> [--mode interpret|commitments|assumptions|risks|all] [--audience non-dev|technical] [--output <path>]"
user-invocable: true
allowed-tools: Read Glob Bash Write Edit Grep
---

# Explain Document — Interpret a specific repo file

You are reading a specific document in the repo and producing a plain-English interpretation. The output answers questions the document doesn't make obvious on first read:

- **What is this document actually saying?** (interpretation)
- **What does it commit me to?** (commitments)
- **What does it assume?** (assumptions, named and unstated)
- **Where could this go wrong?** (risks, gotchas, conditions for failure)

This is the inverse of writing a doc — you're decompiling one. Useful when:

- An AI generated a plan / spec / proposal and you want to know what you're actually agreeing to before approving it
- You're onboarding to a repo and need to understand an existing ADR / architecture doc
- You're reviewing a contract-shaped doc (terms of service, license, agreement) in the repo
- A complex config file's effects aren't obvious from the syntax

## Foundational rules

1. **Grounded.** Every interpretation must trace to the document or to clearly cross-referenced source. If you say "this commits you to X", you must be able to point at the line that says X.
2. **Not overpromising.** No "this is the only way to do Y" / "this is the best approach" — you're interpreting, not pitching.
3. **Honest about uncertainty.** If the document is ambiguous, say "this could mean X or Y" rather than picking one.

## Modes

### `interpret` (default)

The general case: plain-English summary of what the document is saying, structured for a reader who didn't write it.

Output structure:
1. **What this document is** (one paragraph: what kind of doc, what it's for, who wrote it if knowable)
2. **The core message** (1-3 paragraphs: what it actually says in plain words)
3. **The structure** (how the doc is organized; helps the reader navigate the original)
4. **Key terms defined** (any jargon or shorthand the doc uses, translated)

### `commitments`

Specifically focused on what the document commits the project (or its readers) to.

Output structure:
1. **Hard commitments** (things the doc says will / must happen)
2. **Soft commitments** (things the doc proposes / recommends but doesn't lock)
3. **Out of scope** (things the doc explicitly says it won't do — surface these because they bound the commitment)
4. **What approval means** (if the doc is a proposal: what specifically is the user agreeing to if they sign off?)

### `assumptions`

Specifically focused on what the document assumes (named and unstated).

Output structure:
1. **Named assumptions** (things the doc explicitly labels as assumptions)
2. **Unstated assumptions** (assumptions baked into the doc that aren't called out — surface them)
3. **Dependencies on external things** (things outside the doc's scope that have to hold for the doc to work)
4. **What happens if any assumption breaks** (concrete failure modes per assumption)

### `risks`

Specifically focused on where the document's plan / spec / approach could fail.

Output structure:
1. **Acknowledged risks** (risks the doc surfaces itself)
2. **Unacknowledged risks** (risks the doc doesn't surface that a careful reader would spot)
3. **Misalignment risks** (places where the doc's plan diverges from what other repo docs say — surface and link)
4. **Implementation risks** (places where the plan looks fine but execution will be hard)

### `all`

All four modes combined into a single document. Longer output (typically 2-4x longer than any single mode).

## Workflow

### Step 1: Confirm the target document and mode

If the user named a specific file, use it. Otherwise ask:

```
Which document do you want me to interpret?

  (paste path or pick from these recently-modified docs in the repo:
   {list of 3-5 candidates from git log + ls})
```

If `--mode` wasn't passed, ask:

```
Which lens?

  1. Interpret — plain-English summary (default)
  2. Commitments — what does this commit to?
  3. Assumptions — what does this assume?
  4. Risks — where could this go wrong?
  5. All — combined view
```

### Step 2: Read the document and cross-references

Read the document itself. Then read documents it cross-references (if it links to other docs in the repo, read those for context too).

If the document references concepts defined elsewhere (e.g., "per the canonical architecture", "per ADR-0042"), read those references — they're load-bearing for interpretation.

### Step 3: Read the surrounding repo context

For the document to be interpretable, you need to know enough about the project. Read:

- `README.md`
- `docs/vision.md` (if present)
- `docs/architecture.md` (if present)
- Any sibling files in the document's directory (e.g., other ADRs if interpreting an ADR)

### Step 4: Synthesize per mode

For the chosen mode, walk through the structure above. For each section:

1. Find the source content in the document
2. Translate to plain English
3. **For assumptions/risks modes specifically:** apply careful-reader judgment. Surface what the document doesn't say but should.

### Step 5: Cross-check interpretation against source

Before finalizing:

- For each substantive claim about the document, you should be able to cite a specific line/section
- For each "unstated assumption" or "unacknowledged risk", be explicit that it's your inference, not the document's text
- Distinguish doc-says-this from your-interpretation-of-this throughout

### Step 6: Run validators

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-grounding.py {output-path} --repo <repo-root> --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-overpromise.py {output-path} --json
```

Common failure mode for `explain-document`: drifting into evaluating the document instead of interpreting it. The overpromise validator will catch some of this ("this is a great plan", "this approach is excellent"). Pre-edit to keep your output interpretive, not evaluative.

### Step 7: Surface output

If `--output` was passed, write to that file. Otherwise default to stdout or offer:

- Print to stdout
- Write to `EXPLANATION-{filename}.md` next to the original
- Custom path

Surface a 5-line summary:

```
Explanation of {original-file} written to {path}.

Mode: {interpret | commitments | assumptions | risks | all}
Audience: {non-dev | technical}
Cross-references read: {list}
Validators: grounding {pass|N flagged}, overpromise {pass|N flagged}

If you disagree with any interpretation, run with --mode {other} or revise the original.
```

## Audience modes

### `non-dev` (default)

For a stakeholder, reviewer, or future-self who isn't deep in the code.

- Strip technical jargon; translate to plain English
- Skip implementation detail unless it changes the meaning
- Lead with "what this means for you" over "what this says technically"

### `technical`

For a developer who will work with the doc directly.

- Keep technical terms; cross-reference precisely (file paths, function names, line numbers)
- Surface implementation implications (what files this would touch, what tests this would need, what dependencies this would add)
- Compare to current codebase state where relevant

## Rendering rules

- Distinguish "this doc says X" from "my interpretation is Y." Use markup like blockquotes for "doc says" passages.
- Cite specific line numbers / sections / passages in the source document when possible.
- For unstated assumptions and unacknowledged risks, lead with "This document doesn't say but..." to make the inference explicit.
- Don't evaluate the document. You're interpreting; opinions belong elsewhere.

## Cross-plugin notes

- For a narrative summary of a whole project, use `narrate-project` (any repo) or `/rad-planner:project-story` (rad-planner-shaped projects).
- For pitching, use `elevator-pitch` or `draft-pitch`.
- For auditing a README specifically, use `ground-readme`.
- For interpreting a specific PROMPT (not a project document), see rad-context-prompter's `prompt-decompiler` skill.
- Both validators live in this plugin's `scripts/` dir.

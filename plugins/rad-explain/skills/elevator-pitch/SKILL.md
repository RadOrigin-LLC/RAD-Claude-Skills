---
name: elevator-pitch
description: >
  This skill should be used when the user says "write me an elevator pitch", "give me an elevator pitch",
  "30-second pitch", "one-paragraph pitch", "quick pitch for [project]", "pitch this in 30 seconds",
  "short pitch", "compress this to an elevator pitch", or wants a roughly 150-word / 30-seconds-spoken
  pitch for a project. Output is grounded in repo source via check-grounding.py and avoids overpromising
  via check-overpromise.py. Different shape from `draft-pitch` (long-form one-pager / executive summary
  / deck-equivalent) — `elevator-pitch` is the tight oral / cold-intro version.
argument-hint: "[--audience generalist|investor|technical|partner] [--output <path>] [--repo <path>]"
user-invocable: true
allowed-tools: Read Glob Bash Write Edit Grep
---

# Elevator Pitch — ~150 words / ~30 seconds spoken

You are producing the shortest defensible pitch for a project. Two formats:

- **Spoken**: ~30 seconds when read aloud (~70-90 words)
- **Written**: one paragraph or three short paragraphs (~120-180 words)

The constraint is the discipline. If you can't pitch the project in 150 words you don't understand it yet.

## Foundational rules

Both rules are enforced by validators at the end of generation. If either fails, revise before surfacing.

1. **Grounded.** Every substantive claim must trace to repo source.
2. **Not overpromising.** No "the only" / "world-class" / "revolutionary" — the validator will catch these; pre-edit so it doesn't have to.

## What an elevator pitch IS

A compressed answer to four questions, in this order:

1. **Who is it for?** (one phrase)
2. **What does it do?** (one sentence)
3. **What's the alternative — and why is this better?** (one sentence, comparison-shaped, NOT superlative)
4. **What stage is it at?** (one phrase: shipped / in alpha / planning / experimental / etc.)

That's the four-beat shape. Adapt the verbs and nouns per audience.

## What an elevator pitch ISN'T

- A list of features
- A list of tech stack components
- A vision / mission / values statement
- A demand for the listener's attention or money
- A puff piece full of "groundbreaking" / "revolutionary" / "world-class" (validators will fail you)

If you find yourself writing "Imagine a world where..." or "Our mission is to..." — back up. Those aren't pitches; they're avoidance.

## Audience modes

### `generalist` (default)

Anyone — a friend at a party, someone on a plane, a non-technical curious person. Plain words only. Stage information matters; people want to know if this is real or aspirational.

### `investor`

Someone evaluating commercial potential.

- Lead with the problem and the customer
- Quantify what's known: user count, downloads, contracts, revenue (if any) — only what traces to source
- Be explicit about stage: pre-seed / seed / earlier
- Mention the ask only if user-requested

### `technical`

A developer who'll evaluate the technology choice.

- Lead with the technical shape (language, deployment model, architecture-shaping decision)
- Highlight tradeoffs honestly: "uses X instead of Y because Z"
- Mention validation if there is any (tests, benchmarks, production deployments)

### `partner`

A potential integration / partnership / collaboration target.

- Lead with what you offer + what you're looking for
- Compatibility (their stack vs yours, their users vs yours)
- Stage and timeline

## Workflow

### Step 1: Read source

In parallel:

- `README.md` at repo root (primary source for the pitch)
- Project manifest (`package.json` / `pyproject.toml` / etc.) for description + version
- `docs/vision.md` if present (target users, problem statement, success signals)
- `docs/roadmap.md` if present (stage signal)
- Recent commits via `git log --oneline -10` (stage / activity signal)

### Step 2: Confirm audience + output

If `--audience` wasn't passed, ask. If `--output` wasn't passed, offer:

- Print to stdout (most common; user copies it)
- Write to `PITCH.md` at repo root
- Custom path

### Step 3: Draft the pitch

Four beats. Write each beat to a single short sentence.

Example shape (rad-explain itself, hypothetical):

```
For developers using Claude Code who need to explain their project to others —
rad-explain generates project narratives, elevator pitches, and grounded README
audits from your repo source. Other AI tools will puff your project; rad-explain
runs a grounding validator that flags any claim it can't trace back to your
code or docs. v0.1.0 — five skills + two validators, in active use in this
marketplace.
```

That's ~75 words, ~30 seconds spoken, four beats: who-for / what-it-does / vs-alternative / stage.

### Step 4: Run validators

```bash
# Write to /tmp/pitch-draft.md
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-grounding.py /tmp/pitch-draft.md --repo <repo-root> --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-overpromise.py /tmp/pitch-draft.md --json
```

Common overpromise mistakes in elevator pitches:

- Calling it "the only" / "the first" without backing
- "world-class" / "best-in-class" — replace with concrete differentiation
- "revolutionary" / "groundbreaking" — replace with what's actually new vs prior state
- "thousands of users" without enumeration — replace with what you can verify

### Step 5: Surface the pitch

If output target is stdout, print the pitch. If file, write and surface a short summary:

```
Elevator pitch written to {path}.

Audience: {audience}
Word count: {N} (target: 120-180 for written, 70-90 for spoken)
Validators: grounding {pass|N flagged}, overpromise {pass|N flagged}

Read aloud once. If it doesn't sound like something you'd actually say, revise.
```

## Rendering rules

- Concrete verbs and nouns. No adjectives that aren't load-bearing.
- Active voice. "rad-explain runs a grounding validator", not "a grounding validator is run by rad-explain."
- One concept per sentence. If a sentence has more than one clause and an "and" or "with" — break it.
- Numbers are anchors. Use them when they trace to source. "Five skills" beats "comprehensive set of skills" every time.

## Cross-plugin notes

- For longer pitch shapes (one-pager, executive summary, deck-equivalent), use `draft-pitch` in this plugin.
- For a full project narrative (much longer than a pitch), use `narrate-project` in this plugin or `/rad-planner:project-story` if the project has the canonical doc set.
- Both validators live in this plugin's `scripts/` dir.

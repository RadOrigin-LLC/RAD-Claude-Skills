---
name: rescue
description: >
  This skill should be used when the user says "rescue this project", "this repo
  is a mess", "help me out of this", "I don't know where this project stands",
  "get this back on track", "untangle this project", "I abandoned this and want
  to restart", "figure out what state this is in", or has an existing project
  with unclear status, missing or garbage docs, and no trustworthy plan. Runs
  project archaeology (evidence-based state assessment from code + git, no code
  changes), reconstructs intent through the discovery interview, hands structure
  work to rad-repo-manager, drafts a PRD from the answers if none exists, and
  produces a fresh release-map plan from wherever the project actually is. It
  assesses and plans — it never fixes, runs, or deletes code.
argument-hint: "[optional: what you remember about what you were trying to build]"
user-invocable: true
allowed-tools: Read Glob Grep WebSearch WebFetch Agent Write Bash AskUserQuestion
---

# Rescue — from "this repo is a mess" to an approved plan

The second door into planning. `plan` is for greenfield or a clear next effort;
`rescue` is for a project whose state, docs, or direction got away from its owner.
The output is the same thing `plan` produces — a release-map `docs/plan.md` (and
usually a PRD) — but it starts from evidence, not a blank page.

**CRITICAL: Rescue assesses and plans. It does NOT fix.** No source edits, no
running the project's code or tests, no deleting anything, no "while I'm here"
corrections. Stabilization work the project needs becomes *tasks in the plan*, not
actions taken now. Files written: `docs/plan.md`, conditionally `docs/prd.md`
(per-section confirmation, only when missing/skeletal), conditionally
`docs/[date]-update-prompt.md`.

## 1. Archaeology — what's actually here (read-only)

Build the evidence before asking the user anything. In parallel batches:

- **Shape:** Glob the tree; read the manifest(s), top-level config, entry points.
- **History:** `git log --oneline -30`, `git log -1 --format=%cI` (last activity),
  `git status --short` (work left uncommitted mid-flight is a strong signal of where
  it stopped).
- **Surviving docs:** any README, `docs/**/*.md`, `CLAUDE.md`/`AGENTS.md`, TODO/FIXME
  scan (`Grep` for `TODO|FIXME|HACK|XXX`).
- **Half-built signals:** routes/components/exports that nothing references, test
  files with no implementation (or the reverse), config for services that never
  appear in code.

Compose the **State of the project** report — plain language, evidence-cited,
honestly hedged (this is *inference from reading*, not tested truth — nothing was run):

```text
State of the project:
What this appears to be:   <best inference of the goal, from code + docs>
Looks complete:            <pieces with implementation + tests/usage>
Half-built:                <pieces started but not wired up — say what's missing>
Ambiguous:                 <can't tell without running it — say so plainly>
Last activity:             <date, and what the final commits were doing>
Docs situation:            <missing / stale / contradictory — one line>
```

## 2. Intent interview — evidence-led grilling

Run the discovery interview (`references/discovery-interview.md` — load it), with the
rescue twist: **lead every question with the evidence.** "The code suggests you were
building X and got partway into login — is X still what you want? Is login still the
approach?" beats asking a frustrated person to summarize their own mess from memory.

Add the rescue-specific area: **keep / cut / unknown** for each major piece found in
archaeology. Salvage decisions belong to the user — never assume half-built work is
worth finishing, and never assume it isn't. Capture cuts as deliberate exclusions.

Close with the same two gates as `plan` (speed fork; PRD gap check — in a rescue the
PRD is almost always missing or stale, so expect to draft it from the answers,
per-section confirmed).

## 3. Structure handoff — don't duplicate rad-repo-manager

If the repo lacks the doc model or its docs are a mess, pause and say so:
`/rad-repo-manager:repo-init` (nothing there yet) or `/rad-repo-manager:repo-align`
(docs exist but drifted) — then resume here. If the user prefers to skip that,
proceed anyway; rescue only *requires* a `docs/` folder to write into. Rescue never
files, archives, or restructures docs itself — that's the repo-manager's job.

## 4. Plan from where the project actually is

Build the plan per `plan`'s Phase 3 discipline (goal-backward, risk-first, six-field
tasks, release map), with the rescue-specific anchor:

- **"Now" starts from reality, not zero.** The first milestone is typically
  *stabilize and verify*: tasks that get the project to a known-good state (e.g.
  "T1 — get the build running and record the command", "T2 — write the one smoke
  test that proves the core workflow"). Verification the rescue couldn't do
  read-only becomes the plan's first validated tasks.
- Half-built pieces the user kept become explicit tasks with honest Done-when; cut
  pieces land in Scope non-goals with the strike decision recorded.
- The Release map's "Later" is the end goal the interview established — the thing
  the user was trying to accomplish all along.

Then the standard close: lint (`python3`, or `python` on Windows) →
`plan-lint.py` → fix CRITICAL/HIGH → risk pass per the chosen speed fork → present
per `plan`'s Phase 5 (plain summary, release map, decisions, then detail) → user
approval → `APPROVED`, stamp, update-prompt if anything durable surfaced.

## What this skill does NOT do

- Does not modify, run, build, test, delete, or "clean up" any code — assessment is
  read-only; fixes become plan tasks.
- Does not file, archive, or restructure docs — it recommends the repo-manager and
  resumes.
- Does not decide what to salvage — keep/cut is the user's call, asked explicitly.
- Does not present inference as fact — anything unverified is labeled ambiguous and
  becomes an early verification task.
- Does not edit an existing real PRD — only births one from the interview when
  missing/skeletal, per-section confirmed.

## Key references

- `references/discovery-interview.md` — the interview protocol + both closing gates
- `references/plan-template.md` — output structure, release map, enforced rules
- `references/subagent-prompts/risk-assessment.md` — risk-pass dispatch
- `scripts/plan-lint.py` — mechanical validation

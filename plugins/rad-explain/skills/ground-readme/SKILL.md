---
name: ground-readme
description: >
  This skill should be used when the user says "audit my README", "ground my README against the
  code", "check if my README overpromises", "review my README honestly", "rewrite my README without
  marketing language", "audit my marketplace listing", "check my plugin description", "ground this
  description against the code", "is my README honest", "does my README match the code", or wants
  to (a) audit an existing README/marketplace listing against actual code to find overpromise +
  unbacked claims, or (b) generate a README/listing from code with grounding controls so it doesn't
  overpromise. Two modes: `audit` (check existing) and `generate` (create new).
argument-hint: "[--mode audit|generate] [--target README.md|plugin.json|marketplace-entry] [--repo <path>] [--output <path>]"
user-invocable: true
allowed-tools: Read Glob Bash Write Edit Grep
---

# Ground README — Audit or generate honest project listings

You are either auditing an existing README/marketplace listing for overpromise and unbacked claims, or generating a new one from actual code with grounding controls.

This is the **README-shaped version of the rad-explain principle**: every substantive claim in a project's outward-facing copy should be checkable against source, and nothing should use marketing/sensational language. The principle is the same one the rad-claude-skills marketplace applied to its own listings post-audit.

## Foundational rules

1. **Grounded.** Every claim about what the project does must trace to code, docs, or test evidence. The `check-grounding.py` validator runs against the output.
2. **Not overpromising.** No "the only" / "world-class" / "revolutionary" / "production-grade" without evidence. The `check-overpromise.py` validator runs against the output.

These are non-negotiable. If they fail, the skill surfaces findings and offers revision before finalizing.

## Modes

### `audit` (most common)

Review an existing README, marketplace listing, plugin.json description, or similar outward-facing copy. Produce a findings report.

Workflow:
1. Read the target file (default: `README.md` at repo root)
2. Run `check-overpromise.py` against it
3. Run `check-grounding.py` against the repo
4. Read the actual code/docs to verify capability claims
5. Surface findings with line numbers + suggested rewrites
6. Optionally write a revised version

Output: a findings report (Markdown) listing:

| Section | What was flagged |
|---|---|
| **Overpromise findings** | Each flagged phrase with line number, severity, and a suggested concrete replacement |
| **Unbacked claims** | Each claim with no traceable source, with suggested either: remove, add source, or rephrase |
| **Capability mismatches** | Claims that traced to source but the source DOESN'T support the claim (e.g., README says "supports MongoDB" and there's no MongoDB code) |
| **Missing claims** | Things the code actually does that the README doesn't mention (the inverse — under-promising) |
| **Suggested rewrites** | For high-severity findings, a concrete replacement sentence |

### `generate`

Create a new README / marketplace listing from actual code with grounding controls.

Workflow:
1. Read the codebase structure (top-level files, directory layout)
2. Read `package.json` / `pyproject.toml` / equivalent for description, dependencies, entry points
3. Read `docs/vision.md` if present (highest-signal for project intent)
4. Identify capabilities by walking source (public exports, CLI entry points, documented commands)
5. Identify dependencies and external requirements
6. Draft the README with sections grounded in actual source
7. Run validators
8. Write the output

Output: a Markdown README following the standard shape (Install, Usage, Features, Examples, License) but constrained to what the code actually supports.

## Workflow

### Step 1: Determine mode and target

If `--mode` was passed, use it. Otherwise infer:
- If there's an existing `README.md` and the user said "audit" / "review" / "check" → `audit`
- If they said "generate" / "create" / "write" → `generate`
- If ambiguous, ask

Default target for `audit`: `README.md` at repo root. Otherwise the user can specify a marketplace listing JSON path or plugin.json or similar.

### Step 2 (audit only): Read target + run validators

Read the target file. Run both validators:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-overpromise.py <target> --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-grounding.py <target> --repo <repo-root> --json
```

Capture results.

### Step 2 (generate only): Read source

In parallel:

- Project manifest (`package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` / etc.)
- `docs/vision.md` / `docs/README.md` / `docs/getting-started.md` if present
- Top-level directory structure
- Source files for public-API surfaces (e.g., `index.ts`, `__init__.py`, `lib.rs`)
- Test directory (signal for what's actually verified)
- `CHANGELOG.md` if present
- Any existing README (to migrate or replace)

### Step 3 (audit only): Cross-check capability claims

For each capability claim in the target (e.g., "supports X", "integrates with Y", "validates Z"):

1. Extract the claim's substantive terms (X, Y, Z)
2. Grep the repo for those terms in source files
3. Read the matched contexts to verify the capability is actually implemented
4. Classify each claim:
   - **Backed**: source supports the claim
   - **Unbacked-token-absent**: claim's terms not in source at all
   - **Unbacked-token-present-but-no-implementation**: terms appear (often in commit messages or unrelated docs) but implementation isn't there
   - **Stale**: source had this once but no longer does

### Step 4 (audit only): Identify under-promising

Walk the source for capabilities the README doesn't mention:

- Public exports / CLI commands / API endpoints not documented in README
- Configuration options not documented
- Test coverage / supported platforms / dependency requirements that would be useful for users

Flag these as `info`-severity "missing claim" findings. (Some are intentional omissions; some are real gaps.)

### Step 5 (generate only): Draft section by section

Standard README sections (skip any without source backing):

1. **Title** (project name, from manifest)
2. **One-line description** (from manifest description field, refined for accuracy)
3. **What it does** (from vision.md or inferred from source — public API surface)
4. **Install** (from manifest install command + any setup steps in docs/getting-started.md)
5. **Usage** (concrete example using actual public API; pulled from existing tests or README, NOT invented)
6. **Configuration** (only if present in source — flag found options)
7. **Requirements** (dependencies from manifest)
8. **Development** (commands from scripts in package.json or similar; tests, build, lint commands)
9. **License** (from LICENSE file)

For each section, the substantive content must come from a specific file. If a section has no source, omit it.

### Step 6: Run validators on the output

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-overpromise.py <output-path> --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-grounding.py <output-path> --repo <repo-root> --json
```

### Step 7: Revise based on findings

If either validator surfaces critical/warning findings:

For each finding:
1. Show the user the flagged phrase + suggested replacement
2. Default: replace. User can accept the original.
3. Re-run validators after revision until clean (or user accepts remaining findings)

### Step 8: Write output and surface summary

For `audit` mode, write a findings report (or print to stdout if no `--output`):

```markdown
# README Audit: {target-file}

## Overpromise findings

[N critical, M warning, K info]

### Critical: line N "{matched phrase}"
**Suggested rewrite:** "..."

### Warning: line N "{matched phrase}"
**Suggested rewrite:** "..."

...

## Grounding findings

[N unbacked claims]

### Line N: "{claim text}"
Unbacked tokens: {list}
**Suggestion:** {drop | add evidence | rephrase}

...

## Capability mismatches

[N claims source doesn't support]

...

## Missing claims (under-promising)

[N capabilities the source has but README doesn't mention]

...
```

For `generate` mode, write the README to `<output-path>` (default `README.md`) and surface:

```
README generated and written to {path}.

Sections written: {list}
Sections skipped (no source backing): {list with reason}
Validators: grounding {pass|N flagged}, overpromise {pass|N flagged}

If you want to add unbacked content (vision-aspirational, marketing context),
add it manually and re-run /rad-explain:ground-readme --mode audit to keep it
in check.
```

## Rendering rules

- Concrete capability claims only ("supports X" must mean source supports X)
- Comparisons must be named ("unlike Y" with Y being a real, named alternative)
- No "the only" / "the first" / "the best" without evidence
- Version numbers, capability counts, and dependency lists must trace to manifest or code
- Examples in Usage section must use actual public API (no invented method names)

## Cross-plugin notes

- For a longer project narrative (much more than a README), use `narrate-project` in this plugin.
- For pitches (different shape — persuasive vs informational), use `elevator-pitch` or `draft-pitch`.
- For interpreting a specific file (not generating one), use `explain-document`.
- Both validators live in this plugin's `scripts/` dir.

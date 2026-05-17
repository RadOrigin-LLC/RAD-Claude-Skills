# rad-planner scripts

Mechanical validators that complement the `/plan` SKILL.md prompts with deterministic checks an LLM can miss. v4.0 scripts target the canonical doc structure from `docs/doc-conventions.md` (planning/current.md, status.md, vision.md, etc.); v3.0 targeted `tasks.md` (a DAG that has retired in v4.0).

All scripts are pure Python 3.8+ stdlib. No `pip install` required.

The validators surface candidates for user review. They are invoked from `/plan` M6 (post-write validation) and can be run standalone for spot-checks.

## plan-lint.py

Validates `docs/planning/current.md` against the canonical template.

```bash
python3 scripts/plan-lint.py --mode sections docs/planning/current.md     # required-section presence
python3 scripts/plan-lint.py --mode checklist docs/planning/current.md   # field-level checks
python3 scripts/plan-lint.py --mode status docs/planning/current.md      # AC progress
python3 scripts/plan-lint.py --mode all docs/planning/current.md         # sections + checklist
python3 scripts/plan-lint.py --mode all docs/planning/current.md --json  # machine-readable
```

**What `sections` catches:**

- Missing required sections (Objective, Current milestone, Acceptance criteria, Validation commands, **Guardrails**, **User-visible behavior**, Stop conditions, Notes for the next session — Guardrails + User-visible behavior added in v4.6 per build-readiness gate questions 6 and 7)
- Empty required sections (or sections containing only template-placeholder content like `[Single clear outcome]`)
- Missing recommended sections (Why this matters, Non-goals, Planned changes, Open questions, Risks) — surfaced as LOW

**What `checklist` catches:**

- Acceptance criteria written as bullets instead of `- [ ]` checkboxes (progress untrackable)
- Vague language in acceptance criteria and validation commands ("verify it works", "should work", "tbd", "looks right", etc.)
- Validation commands that don't look runnable (no backticked command, too short to plausibly be a real check)
- Empty Stop conditions or Notes for the next session

**Exit codes:** `0` clean (or only MEDIUM/LOW warnings), `1` CRITICAL or HIGH issues present, `2` script error.

## status-validator.py

Validates `docs/status.md` against the canonical schema in `docs/status-md-schema.md`.

```bash
python3 scripts/status-validator.py --mode freshness docs/status.md       # mtime vs git HEAD
python3 scripts/status-validator.py --mode sections docs/status.md        # 8-section presence
python3 scripts/status-validator.py --mode evidence docs/status.md        # validation results evidence-based
python3 scripts/status-validator.py --mode read_order docs/status.md      # restart read-order has files
python3 scripts/status-validator.py --mode all docs/status.md --json      # everything + freshness
```

**Freshness thresholds (canonical):**

- `fresh`: < 2 days AND < 5 commits since last status update
- `stale`: > 7 days OR > 20 commits since last status update
- `moderate`: in between

Falls back to file mtime if git isn't available (not in a git repo, no commits yet).

**What `sections` catches:** missing or silently-empty status sections. Empty sections should explicitly say "No data this session — last run YYYY-MM-DD" rather than be blank.

**What `evidence` catches:** vague phrases in Latest validation results ("should pass", "tests pass" without command, "looks good") and missing backticked commands.

**What `read_order` catches:** "If restarting from scratch" section missing or has no file references — this section is load-bearing for `/startup`.

**Exit codes:** `0` clean or freshness-only mode, `1` HIGH issues present, `2` script error.

## doc-redundancy.py

Cross-doc duplicate detection. Compares bullet items and headings across the canonical doc set (`vision.md`, `architecture.md`, `roadmap.md`, `planning/current.md`, `decisions/NNNN-*.md`) using Jaccard token similarity.

```bash
python3 scripts/doc-redundancy.py /path/to/project
python3 scripts/doc-redundancy.py /path/to/project --threshold 0.6
python3 scripts/doc-redundancy.py /path/to/project --json
```

**Severity:**

- `MEDIUM` — similarity ≥ 0.85 (likely duplicate content)
- `LOW` — similarity in [threshold, 0.85) (related content; user judgment)

**What this catches:** the failure mode that drove the planner-first inversion — same non-goals listed verbatim in vision.md AND current.md, same architectural pattern in architecture.md AND a related ADR, etc. Each item should have one canonical home; others should reference rather than copy.

**What this does NOT catch:** semantic equivalence with different wording. "We don't support mobile" vs "Mobile is out of scope" won't match. That's the contradiction validator's softer-recall territory.

**Exit codes:** `0` clean or only LOW findings, `1` any MEDIUM finding, `2` script error.

## doc-contradiction.py

Cross-doc disagreement detection. Flags potential contradictions between docs that should agree.

```bash
python3 scripts/doc-contradiction.py /path/to/project
python3 scripts/doc-contradiction.py /path/to/project --threshold 0.4
python3 scripts/doc-contradiction.py /path/to/project --json
```

**v4.0 check:** `vision.md` non-goals vs `planning/current.md` acceptance criteria — is the plan doing things vision says we won't do?

**Approach:** tokenize both with simple plural stemming, strip negation words from non-goals (so the substantive concept can be matched), compute Jaccard. Flag pairs above threshold for user review.

**Severity is always MEDIUM or LOW** — never CRITICAL/HIGH. The validator surfaces signals; the user judges whether each is a real contradiction or unrelated overlap.

**What this does NOT catch:** semantic contradictions that don't share vocabulary. "We don't optimize for scale" vs "Auth must handle 10k concurrent users" won't match on tokens. That needs natural-language reasoning.

**Future v4.x checks:** architecture.md canonical patterns vs decisions/*.md ADRs; planning/current.md milestone vs status.md last-completed.

**Exit codes:** `0` always (findings are advisory), `2` script error.

## estimate-validator.py (v4.1)

Flags planning files that carry no effort/size signal. Plans should have SOMETHING — a t-shirt size, a time range, a context-window bar — so reviewers can reason about scope vs capacity.

```bash
python3 scripts/estimate-validator.py docs/planning/current.md
python3 scripts/estimate-validator.py docs/planning/current.md --json
```

**Accepted signals (any one passes):**

- Section heading: `## Effort`, `## Estimate`, `## Size`, `## Sizing`, `## Complexity`
- Inline field: `Effort: M`, `Estimate: ~2 days`, `Size: Large`, `Complexity: medium-high`, `Context bar: ~50%`
- T-shirt size suffix on the milestone line: `M2 (M): User-defined constraints` or `M3 [L]`
- Per-AC parenthetical: `- [ ] Task X (S)`, `- [ ] Task Y (~2d)`, `- [ ] Task Z (3pts)`

**Severity:** MEDIUM if no signal found; LOW if signal exists but partial (e.g., 2 of 8 ACs have estimates).

**Exit codes:** `0` at least one signal present, `1` MEDIUM/HIGH issues, `2` script error.

## dependency-cycle-detector.py (v4.1)

DFS cycle detection across milestone dependency declarations. Detects cycles within a single planning directory and (optionally) across the archive.

```bash
python3 scripts/dependency-cycle-detector.py docs/planning/
python3 scripts/dependency-cycle-detector.py docs/planning/ --include-archive
python3 scripts/dependency-cycle-detector.py docs/planning/ --json
```

**Dependency declarations recognized:**

- Dedicated `## Dependencies` section listing milestone IDs (`M1`, `M2`, …)
- Inline `Depends on: M1, M3` field anywhere in the doc
- Per-AC `(depends on M2)` parenthetical

**Milestone ID resolution:** prefers the `M\d+` prefix on the first non-blank line of `## Current milestone`; falls back to filename pattern (`2026-04-30-M3-foo.md` → `M3`).

**Severity:** HIGH on detected cycle; MEDIUM on self-dependency; LOW on parse warnings.

**Exit codes:** `0` clean, `1` cycle detected, `2` script error.

## coverage-validator.py (v4.1)

Flags acceptance criteria with no apparent verification path. Computes stemmed token overlap between each AC and the entries in `## Validation commands`.

```bash
python3 scripts/coverage-validator.py docs/planning/current.md
python3 scripts/coverage-validator.py docs/planning/current.md --threshold 0.15
python3 scripts/coverage-validator.py docs/planning/current.md --json
```

**Severity policy:**

- HIGH: no `## Validation commands` section, or empty.
- MEDIUM: a specific AC has overlap below threshold (default 0.15) with every validation command.
- LOW: ACs:commands ratio looks suspicious (≥5 ACs, ratio < 0.2).

**Heuristic.** Token overlap can miss legitimate pairings (an AC about "rate limiting" validated by a command named `test:api`). The validator surfaces signals; the user judges.

**Exit codes:** `0` clean, `1` HIGH/MEDIUM issues, `2` script error.

## scope-creep-detector.py (v4.1)

Detects when current.md is doing things vision.md said are non-goals. Complementary to `doc-contradiction.py` but more targeted: focuses on the case where the milestone non-goals have ALSO failed to preserve the project-level boundary.

```bash
python3 scripts/scope-creep-detector.py /path/to/project
python3 scripts/scope-creep-detector.py /path/to/project --threshold 0.35
python3 scripts/scope-creep-detector.py /path/to/project --json
```

**Two signals:**

1. **Dropped non-goal**: a vision.md non-goal whose substantive tokens don't appear in current.md's `## Non-goals` section.
2. **Active creep**: a dropped non-goal whose tokens DO appear in current.md's `## Acceptance criteria` or `## Planned changes`.

**Severity:** HIGH on active creep; MEDIUM on dropped-only; LOW on weak match.

**Exit codes:** `0` clean, `1` HIGH/MEDIUM issues, `2` script error.

## assess-planning-velocity.py (v4.6)

Surfaces overplanning signals from git history. Built for the `/plan --assessment` flow but usable standalone. Catches the planning-as-avoidance pattern (rewriting plans without shipping code).

```bash
python3 scripts/assess-planning-velocity.py <project-dir>
python3 scripts/assess-planning-velocity.py <project-dir> --json
python3 scripts/assess-planning-velocity.py <project-dir> \
  --threshold-edits 8 --threshold-rewrites 5 \
  --threshold-growth 3.0 --threshold-stale-days 21 \
  --window-days 30
```

**Four signals:**

1. `current_md_edits_since_last_code_commit` — commits to `docs/planning/current.md` since the last commit touching non-docs files. Default threshold: 5.
2. `ac_rewrite_count_per_ac` — how many times the Acceptance criteria section was rewritten across git history (via `git log -L`). Default threshold: 3.
3. `planning_doc_growth_ratio` — ratio of docs/ line-change volume to source line-change volume over the last N days. Default threshold: 2.0× (planning outpacing shipping).
4. `time_since_last_code_commit` — days since last non-docs commit. Flagged only when current.md is also fresh (< 7 days). Default threshold: 14 days.

**Graceful skip:** if the project directory is not a git repository, the validator emits a "git not initialized" note and exits 0 — signals are unavailable but the validator does not fail.

**Exit codes:** `0` no signals flagged or git unavailable; `1` at least one signal flagged; `2` script error.

**Threshold tuning:** the defaults are heuristics, not laws. Marketplace meta-repos (like rad-claude-skills itself) have unusual planning-doc activity by nature. Per-project overrides via `--threshold-*` flags. Document the chosen thresholds in `docs/planning/current.md` if they differ from defaults.

## validate-json.py

Validates a JSON payload against a JSON Schema (the rad-planner subagent contracts at `references/subagent-prompts/*.schema.json`). Unchanged from v3.0.

```bash
python3 scripts/validate-json.py <schema.json> <data.json>
echo "$AGENT_OUTPUT" | python3 scripts/validate-json.py <schema> -
python3 scripts/validate-json.py <schema> agent-output.md --extract-from-markdown
python3 scripts/validate-json.py <schema> output.json --json
```

The dispatching skills use this to verify subagent JSON output against the documented contract before consuming it. On failure they re-prompt once with the validation errors before falling back to markdown parsing.

**Exit codes:** `0` valid, `1` invalid, `2` script error.

## Where these get invoked

`/plan` M6 (Doc Creation) runs `plan-lint`, `status-validator`, `doc-redundancy`, and `doc-contradiction` after writing the doc set. Validator results land in the terminal M6 checkpoint under `validator_results`.

`validate-json` is invoked from `/plan` Phase 2 (after `stack-advisor` returns) and Phase 4 (after `risk-assessor` returns) — though these phases retire in v4.0 if/when M5's `--lite` complexity routing makes them optional.

All scripts can be run standalone outside the `/plan` workflow for spot checks during development.

## What these scripts deliberately do NOT do

- **Do not judge plan quality.** Mechanical checks only. "Is this validation command sensible?" is still the LLM's or user's job.
- **Do not catch semantic contradictions.** Token-overlap detection can't model "we say X" vs "we say not-X with different vocabulary." A future v4.x iteration may add lightweight NL reasoning; v4.0 is mechanical.
- **Do not auto-fix.** They report; the user (or a downstream skill invocation) decides what to change.
- **Do not validate the JSON Schemas themselves.** If you edit a `.schema.json`, sanity-check it manually.

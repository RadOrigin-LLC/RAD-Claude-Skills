# rad-repo-manager scripts

Pure-stdlib Python 3.8+ (no `pip install`). Each emits human text by default and a
single JSON object with `--json`. Run with `python3` (or `python` on Windows). The two
cheap scans (`repo-scan`, `doc-freshness`) run at `startup` and via the SessionStart
hook; `wrapup` ends with a `repo-scan` hygiene pulse; all five run in
`/rad-repo-manager:repo-align`. They surface **candidates** — judgment decides which
are real, and nothing is auto-fixed.

## repo-scan.py — mechanical drift signals (every session)

High-precision, mechanical signals only — so the count is trustworthy and never cries
wolf. `startup`/`repo-align` read its `--json`; fuzzy checks (contradiction,
redundancy) have their own scripts below.

```bash
python3 repo-scan.py <project-dir> --json --no-record
```

Signals (each a loose end): active-set growth (AGENTS.md read path > 4), floating docs
(a `.md` at repo root or directly under `docs/` that isn't a known core/allowed file —
scoped shallow so component READMEs never false-flag), legacy inbox items
(`docs/inbox/*.md` — a retired tier, flagged so its contents get filed out), AGENTS.md
bloat (past a soft line cap). Severity: 0 green, 1–4 yellow, ≥5 red. Exit 0 always.

## doc-freshness.py — stale active docs (every session)

The "active doc unchanged while code churned" signal, from pure git evidence. Per core
doc: last commit date and how many *code-touching* commits (excludes all `.md` churn)
landed since. Flags a stale `docs/handoff.md` (MEDIUM when any code commit is newer
than it, HIGH at ≥5 commits or ≥7 days — suppressed while an uncommitted handoff edit
is in flight) and an untouched `prd.md`/`plan.md` (LOW/MEDIUM at soft commit
thresholds: prd 15/30, plan 10/20). Missing/untracked docs and no-history repos are
INFO, never stale. Exit 0 always.

```bash
python3 doc-freshness.py <project-dir> --json
```

## doc-contradiction.py — prd vs plan (deep, in repo-align)

Flags where the plan commits to building something the PRD lists as a non-goal (catches
scope-creep). Compares `docs/prd.md` "Non-goals" against `docs/plan.md` task Objectives
+ In-scope, via stemmed token overlap. Severity MEDIUM/LOW — advisory candidates, not
verdicts. Exit 0 always.

```bash
python3 doc-contradiction.py <project-dir> --json
```

## doc-redundancy.py — same fact in two docs (deep, in repo-align)

Flags near-duplicate bullets/headings across the active core (`AGENTS.md`, `docs/prd.md`,
`docs/plan.md`, `docs/handoff.md`, `docs/reference/decision-log.md`) — the duplication
that drifts apart and confuses agents. Jaccard similarity; MEDIUM ≥0.85, LOW above
threshold. Exit 1 on any MEDIUM, else 0.

```bash
python3 doc-redundancy.py <project-dir> --json
```

## audit-user-content.py — AGENTS.md staleness (deep, in repo-align)

Visibility pass over the **user-authored** sections of `AGENTS.md` (operational sections
from the template are exempt). Two heuristics: orphan terminology (Title-Case phrases
that appear only in one section and nowhere else — catches renamed/retired systems) and
dead paths (links to files that don't exist). Never modifies content — advisory only.
Exit 1 on any HIGH/MEDIUM finding, else 0.

```bash
python3 audit-user-content.py <project-dir> --json
```

## What these deliberately do NOT do

- No semantic reasoning — token-overlap surfaces *candidates*; the user judges.
- No auto-fix — `repo-align` proposes; the user confirms every change.
- `repo-scan` never mixes fuzzy signals with its mechanical ones — only hard, mechanical checks.

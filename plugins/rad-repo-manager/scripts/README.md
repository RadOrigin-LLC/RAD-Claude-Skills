# rad-repo-manager scripts

Pure-stdlib Python 3.8+ (no `pip install`). Each emits human text by default and a
single JSON object with `--json`. The skills run these; you can run them standalone.

## repo-scan.py — the health-line engine (cheap, every session)

Powers the one-line verdict at the end of `startup`/`wrapup`. High-precision,
mechanical signals only — so the loose-ends count never cries wolf.

```bash
python3 repo-scan.py <project-dir> --json
```

Signals (each a loose end): active-set growth (AGENTS.md read path > 4), floating docs
(a `.md` at repo root or directly under `docs/` that isn't a known core/allowed file —
scoped shallow so component READMEs never false-flag), inbox items (`docs/inbox/*.md`),
AGENTS.md bloat (past a soft line cap). Severity: 0 green, 1–4 yellow, ≥5 red. Maintains
a small `.rad/repo-manager-state.json` for the red-nudge cooldown. Exit 0 always.

## doc-contradiction.py — prd vs plan (deep, in analyze)

Flags where the plan commits to building something the PRD lists as a non-goal
(catches scope-creep). Compares `docs/prd.md` "Non-goals" against `docs/plan.md` task
Objectives + In-scope, via stemmed token overlap. Severity MEDIUM/LOW — advisory
candidates, not verdicts. Exit 0 always.

```bash
python3 doc-contradiction.py <project-dir> --json
```

## doc-redundancy.py — same fact in two docs (deep, in analyze)

Flags near-duplicate bullets/headings across the active core (`AGENTS.md`, `docs/prd.md`,
`docs/plan.md`, `docs/handoff.md`, `docs/reference/decision-log.md`) — the duplication
that drifts apart and confuses agents. Jaccard similarity; MEDIUM ≥0.85, LOW above
threshold. Exit 1 on any MEDIUM, else 0.

```bash
python3 doc-redundancy.py <project-dir> --json
```

## audit-user-content.py — AGENTS.md staleness (deep, in analyze)

Visibility pass over the **user-authored** sections of `AGENTS.md` (operational
sections from the template are exempt). Two heuristics: orphan terminology (Title-Case
phrases that appear only in one section and nowhere else — catches renamed/retired
systems) and dead paths (links to files that don't exist). Never modifies content —
advisory only. Exit 1 on any HIGH/MEDIUM finding, else 0.

```bash
python3 audit-user-content.py <project-dir> --json
```

## What these deliberately do NOT do

- No semantic reasoning — token-overlap surfaces *candidates*; the user judges.
- No auto-fix — `analyze` proposes; the user confirms every change.
- `repo-scan` never feeds fuzzy signals into the health line — only hard, mechanical ones.

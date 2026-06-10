---
name: startup
description: >
  This skill should be used when the user says "startup", "start session",
  "orient me", "where did we leave off", "catch me up", "what's the state",
  "session briefing", or "what was I working on". Fast, read-only session
  orientation — read the four active docs + git state, run the two cheap mechanical
  scans (loose docs, stale docs), and surface where you are, what's next, and
  whether the docs are trustworthy. Recommends /rad-repo-manager:repo-init on a
  fresh repo and /rad-repo-manager:repo-align when the scans show drift. It does
  not scaffold, audit deeply, clean, write, or change anything.
argument-hint: ""
user-invocable: true
allowed-tools: Read Glob Grep Bash
---

# Startup — orient, fast and read-only

Get oriented at the top of a session. **Read-only and lean** — read the active docs
and git state, surface where things stand, and point at the right next skill. This is
not onboarding (that's `/rad-repo-manager:repo-init`) and not an audit (that's
`/rad-repo-manager:repo-align`).

## What this skill does NOT do

- No scaffolding or onboarding — a fresh repo gets pointed at `repo-init`.
- No deep audit, contradiction/redundancy check, or doc filing — that's `repo-align`.
  (The two mechanical scans in step 1 are read-only and near-instant — they're
  evidence for the briefing, not an audit.)
- No reading of `docs/archive/`.
- No cleanup, no writes of any kind, no commits.
- No product or implementation changes.
- No offering to run `wrapup` or any end-of-session action — `startup` only orients.

## Procedure

1. **Gather evidence** (read-only), in one batch — the git state plus the two cheap
   mechanical scans (each ~1 second; use `python3`, or `python` on Windows):
   ```bash
   git status --short
   git branch --show-current
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/repo-scan.py . --json --no-record    # loose/floating docs, active-set growth, AGENTS.md bloat
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doc-freshness.py . --json            # stale handoff; prd/plan unchanged while code churned
   ```
   (If Python is unavailable, skip the scans and say so in the briefing — don't guess
   at hygiene from globs alone.)
2. **Glob** for `AGENTS.md` and the `docs/` core to see what exists. Decide the path:
   - **Fresh repo** — no `AGENTS.md` and no real `docs/prd.md`/`docs/plan.md`. Stop
     and recommend `/rad-repo-manager:repo-init`. Do **not** scaffold here.
   - **Established repo** — `AGENTS.md` exists. Orient (below).
3. **Read the active core** that exists, in one parallel batch: `AGENTS.md`,
   `docs/prd.md`, `docs/plan.md`, `docs/handoff.md`. Read nothing else by default —
   not reference docs, not `docs/design.md`, not `docs/archive/`.
4. **Note alignment from the scan results** (no deep scan beyond them): the repo-scan
   JSON tells you about loose docs, active-set growth, and AGENTS.md bloat; the
   doc-freshness JSON tells you whether the handoff is stale and whether prd/plan sat
   unchanged while code churned. Report what the scans found — grounded counts and
   file names, not impressions. If the handoff is stale, say so explicitly and treat
   its "Resume point" with suspicion in the briefing. If the scans show drift,
   recommend `/rad-repo-manager:repo-align` — don't fix anything here.
5. **Surface the briefing** (format below), then stop — the briefing is the whole
   deliverable. Ground every line in what you actually read; if a doc is missing or
   stale, say so plainly rather than inventing. The only forward action you may suggest
   is `repo-init` (fresh repo) or `repo-align` (drift) — never offer to run `wrapup`,
   commit, or anything else.

## Output format

```text
Startup:
Branch:           <current branch>
Working tree:     <clean / dirty summary from git status>
Active docs:      <which of the 4 exist; name any missing>
Current focus:    <current milestone / active task from docs/plan.md, one line>
Resume point:     <next action from docs/handoff.md; append "(handoff is stale — verify against git)" if doc-freshness flagged it>
Stop conditions:  <from docs/plan.md, if declared>
Doc freshness:    <from doc-freshness.py: "fresh" | the findings, one line each>
Repo hygiene:     <from repo-scan.py: "tidy" | "N loose ends: <names>" → recommend repo-align | fresh repo → recommend repo-init>
Notes:            <anything material, or "None">
```

## References

- `${CLAUDE_PLUGIN_ROOT}/references/doc-model.md` — the active core, the conditional
  tiers, and what "aligned" means

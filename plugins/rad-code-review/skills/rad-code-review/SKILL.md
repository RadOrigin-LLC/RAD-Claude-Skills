---
name: rad-code-review
description: >
  Review my code, code review, is this ready to ship, check for bugs, security audit,
  review this PR, pre-merge check, is this safe to deploy, check code quality. Blame-aware
  diff scoping, 3-role adversarial review, AI slop detection (14 patterns including a
  mechanical hallucinated-imports validator), framework IDOR (6 frameworks), WCAG 2.2,
  performance heuristics, severity-ranked CR-NNN findings, fingerprint-based history
  comparison, optional fix application. Parallel tool calls, JSON-first subagent output,
  compaction-safe checkpointing, non-interactive mode for agents/CI, cross-model
  adversarial pass via --adversarial-model.
argument-hint: "[repo|diff|commit] [--since commit] [--strictness mvp|production|public|launch] [--security-deep] [--model opus|sonnet|haiku] [--adversarial-model name] [--non-interactive] [--resume RUN-ID] [--fix blockers|critical-major|IDs]"
allowed-tools: Read Write Edit Bash Glob Grep Agent AskUserQuestion WebSearch WebFetch mcp__context7__resolve-library-id mcp__context7__query-docs
---

**Cross-model note.** Defaults to **Opus** for the primary review (best reasoning for the adversarial protocol + severity calibration). **Sonnet** is a first-class fallback — set `--model sonnet` for cost-sensitive PR scans. **Haiku** only for narrow blame-aware diffs with `--local-only`. The adversarial pass is self-adversarial (same model) by default; pass `--adversarial-model <name>` for a cross-model challenge pass.

**Naming.** Finding IDs are **`CR-NNN`** (v5.0 — short to type and reference; previously `RADCR-NNN`). The config file (`.radcrconfig.yml`) and history/state directories (`.radcr/history/`, `.radcr/state/`) keep the longer `radcr` prefix — renaming those would break existing per-repo state for zero readability gain: you type finding IDs, not paths. Users with a `.ucrconfig.yml` from the oldest versions should rename it to `.radcrconfig.yml` and `.ucr/` to `.radcr/`. See `README.md` for details.

<objective>
Run a professional-grade, diff-aware code review and produce a structured report with
severity-ranked findings, release verdict, and optional fix application.

**v5.0 differentiators (new):**
- **`CR-NNN` finding IDs** — short to type and reference (previously `RADCR-NNN`)
- **Mechanical hallucinated-imports validator wired into Step 5g** — deterministic, offline, lockfile-verified; runs before the LLM phases
- **Fingerprint-based history comparison** — findings match across runs by category+file+title fingerprint, never by per-run IDs
- **Honest adversarial flags** — `--engine claude|codex|both` removed (Codex execution was never implemented); `--adversarial-model` provides the real cross-model pass
- **Reports save to `.radcr/history/` only** — no more loose root-level report files (root copy on explicit request)

**v3.0 differentiators (retained):**
- **Opus as the default primary-review model** with explicit `--model` override
- **Parallel tool calls** across Steps 1–5 — deep reviews complete ~3–5× faster on Opus/Sonnet
- **JSON-first subagent output** — more robust across model variance than markdown parsing
- **Checkpoint / `--resume`** — compaction-safe state writes after Steps 5, 7, 9
- **`--non-interactive`** — agent/CI callers skip the findings menu and get structured return
- **Externalized subagent prompts** — primary/adversarial/self-adversarial templates in `references/subagent-prompts/`
- **`.radcrconfig.yml` accepted-risk expiry enforcement** — stale entries re-evaluated, not silently suppressed

**v2.x differentiators (retained):**
- Blame-aware scoping: `diff` and `commit` scopes only flag issues on changed lines by default
- Incremental review: `--since <commit>` reviews all changes since a specific commit
- Framework-specific IDOR detection: concrete mutation ownership patterns for 6 frameworks
- Performance profiling heuristics: grep-able patterns for N+1, re-renders, bundle bloat
- Dynamic ARIA state detection: catches hardcoded aria-expanded, aria-selected, etc.

**Orchestrator role:** Parse arguments, compute diff scope, gather user choices, detect
project context, spawn review subagents with annotated diff context, handle checkpoints
and adversarial passes, offer fixes, assemble final report.

**Three report roles:**
1. Bug finder — functional correctness, edge cases, race conditions, state corruption
2. Architecture reviewer — coupling, boundaries, extensibility, patterns, maintainability
3. Release gate — security, secrets, dependencies, ops readiness, public defensibility

**Review dimensions:** Functional correctness, security, AI slop detection, architecture,
tests, performance, UI/UX, accessibility, release readiness, documentation, dependencies,
privacy/secrets handling.
</objective>

<execution_context>
**Load these files NOW before proceeding:**
- ${CLAUDE_SKILL_DIR}/workflows/orchestrate-review.md (main workflow)
- ${CLAUDE_SKILL_DIR}/references/severity-model.md (severity classification)
- ${CLAUDE_SKILL_DIR}/references/trust-model.md (trust boundaries)
</execution_context>

<context>
Arguments: $ARGUMENTS

**Scope options:** repo | diff | commit | tree
- `repo` — review all files in the repository (full scan, no blame filtering)
- `diff` — review staged + unstaged changes only (blame-aware by default)
- `commit` — review files changed in HEAD commit only (blame-aware by default)
- `tree` — review uncommitted working tree changes only (full scan of changed files)

**Incremental review:** --since <commit>
- Reviews all changes between <commit> and HEAD
- Blame-aware: only flags issues introduced in those changes
- Useful for: PR review, sprint review, post-release delta

**Scan mode:**
- Default for diff/commit/--since: blame-aware (only flag issues on changed lines)
- Default for repo/tree: full scan (flag all issues found)
- `--full-scan` — override blame-aware default, flag all issues regardless of authorship
- Blame-aware mode still flags pre-existing issues when a new change depends on broken existing code

**Strictness:** mvp | production | public | launch (default: production)
- `mvp` — focus on functional correctness, critical security, and stated goals
- `production` — full review across all dimensions
- `public` — production + open-source readiness, public scrutiny resilience, trust signals
- `launch` — public + the **security-deep** launch-readiness pass (data-exposure surface, authorization model, privileged credentials) with a no-false-assurance verdict. For an app about to handle real customer data.

**Security-deep mode:** `--security-deep` runs the launch-readiness security pass on any strictness — trust boundaries → data-exposure surface → authorization model → secrets, concentrated on BaaS/RLS data exposure (see `references/security-deep-mode.md`). Never emits a "safe to launch" verdict; reports verified-vs-could-not-verify and recommends a human pen-test. Implied by `--strictness launch`.

**Adversarial pass:** self-adversarial by default (same model challenges its own
findings); `--adversarial-model <name>` switches to a cross-model pass (a different
model family does the challenge). v5.0 removed the old `--engine claude|codex|both`
flag — it implied Codex execution that was never implemented; if a caller passes
`--engine`, say so and map `both` → cross-model adversarial on Opus.

**Connectivity:** --local-only (default: internet-enabled)
**Fix mode:** --fix blockers | --fix critical-major | --fix id1,id2,...

**Model selection (v3.0):**
- `--model opus` (default) — Opus primary review
- `--model sonnet` — Sonnet for cost-sensitive reviews
- `--model haiku` — Haiku only for narrow blame-aware + --local-only scopes
- `--adversarial-model <name>` — override adversarial-pass model separately

**Non-interactive mode (v3.0):**
- `--non-interactive` — skip the findings menu, return findings + verdict + report path. Used by the `code-reviewer` agent, `/loop` sessions, and CI.

**Resume (v3.0):**
- `--resume <run-id>` — rehydrate mid-review state from `.radcr/state/<run-id>.json` after compaction or interruption. Run IDs are logged at the start of each run.

**Project config:** .radcrconfig.yml (if present in repo root)
**History:** .radcr/history/{YYYY-MM-DD}-{HHmmss}-{scope}-{strictness}.md (previous review reports)
**State:** .radcr/state/{run-id}.json (checkpoints for --resume)
</context>

<process>
Execute the orchestrate-review workflow from
${CLAUDE_SKILL_DIR}/workflows/orchestrate-review.md end-to-end.

Preserve all workflow gates, user checkpoints, and subagent boundaries.
</process>

<critical_rules>
1. **Always ask for scope** if not provided in arguments
2. **Blame-aware by default** for diff/commit/--since scopes — only flag issues on changed lines unless the change depends on pre-existing broken code
3. **Disclose internet usage** before proceeding if not --local-only — state what will be accessed and why
4. **Never include secret values** in reports — show file, line, key name, and type only. Mask values completely in code snippets.
5. **Triage-first mode:** If project appears fundamentally broken (50+ critical findings or unsalvageable architecture), switch to triage report — verdict, systemic diagnosis, top 5-10 blockers, remediation roadmap. Say plainly if rebuild is warranted.
6. **Load .radcrconfig.yml** exclusions and accepted-risk rules if present. Surface all exclusions and accepted risks in the report for auditability.
7. **Save report** to .radcr/history/{timestamp}-{scope}-{strictness}.md after completion
8. **Compare against history** — if previous reports exist for this repo, summarize resolved, remaining, and newly introduced findings
9. **Secrets in config** — if .radcrconfig.yml contains accepted risks, validate they are still acknowledged, not stale
10. **Do not fabricate findings** — if you cannot verify something, mark confidence as "possible" and say what verification is needed
11. **Do not suppress findings** because they seem minor — rank them accurately and let severity speak. But do suppress findings that fail the evidence threshold for their severity level.
</critical_rules>

<success_criteria>
- [ ] User confirmed scope, strictness, model(s), and connectivity
- [ ] Diff context computed and annotated (if blame-aware mode)
- [ ] Project type(s) detected and relevant modules loaded
- [ ] Primary review completed with findings scoped to changed lines (if blame-aware)
- [ ] Adversarial pass completed (self-adversarial or cross-model)
- [ ] Review-of-review pass completed (de-duplication, calibration)
- [ ] Findings presented to user with severity ranking
- [ ] Fix option offered (if findings exist)
- [ ] Report generated and saved
- [ ] History comparison included (if previous reports exist)
</success_criteria>

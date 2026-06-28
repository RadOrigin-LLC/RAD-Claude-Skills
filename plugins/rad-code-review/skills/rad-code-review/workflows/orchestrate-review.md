# RAD Code Review v3.0 — Main Workflow

This workflow is loaded by the orchestrator SKILL.md and executed end-to-end.

**Cross-model note.** Optimized for Opus — parallel tool calls across Steps 1–5, JSON-first subagent output, compaction-safe checkpointing. Sonnet is a first-class fallback. Haiku should be used only for small-scope blame-aware reviews with `--local-only`; the full protocol exceeds Haiku's reliable capacity.

**v3.0 changes from v2.x:**
- **Step 3a/3b/3c/3d/3e run in a single parallel batch** (was sequential)
- **Step 3f emits structured JSON blame context** (was prose-annotated diff)
- **Step 5 automated checks run in parallel** via `run_in_background` (was sequential, blocking)
- **Step 6 selects the subagent model explicitly** (primary: Opus default; configurable)
- **Step 6 subagent prompt externalized** to `references/subagent-prompts/primary-review.md`
- **Step 6 subagent emits JSON-first findings** (was markdown, fragile across models)
- **Step 8 adversarial prompt externalized** to `references/subagent-prompts/adversarial-review.md` and `self-adversarial-review.md`
- **Step 10 supports `--non-interactive`** — skips the menu, returns findings directly (for agent/loop invocation)
- **Step 2 enforces `.radcrconfig.yml` accepted-risk expiry** — stale entries warn and are re-evaluated
- **New Step 0.5: Checkpoint/Resume** — periodic state writes to `.radcr/state/{run-id}.json`; `--resume <run-id>` rehydrates mid-review after compaction
- **History filename unified** across orchestrator and report-generation to `{YYYY-MM-DD}-{HHmmss}-{scope}-{strictness}.md` (multiple same-day reviews no longer overwrite)

**v2.x changes** (retained): blame-aware scoping, `--since`, `--full-scan`, framework IDOR, performance heuristics, dynamic ARIA state, finding attribution, adversarial blame validation, interactive findings menu.

---

## Step 0: Parse Arguments and Resolve Defaults

Parse $ARGUMENTS for:
- **Scope**: repo | diff | commit | tree (if missing, ask user)
- **Incremental**: --since <commit> (review changes since a specific commit)
- **Scan mode**: --full-scan (override blame-aware default; flag all issues regardless of authorship)
- **Strictness**: mvp | production | public | launch (default: production)
- **Security-deep mode**: `--security-deep` flag (or `--strictness launch`, which implies it). Activates the launch-readiness security pass — see "Security-deep activation" below.
- **Local-only**: --local-only flag (default: internet-enabled)
- **Fix mode**: --fix blockers | --fix critical-major | --fix <ids> (default: no fixes)
- **Non-interactive**: --non-interactive (skip the findings menu, return findings + save report directly — for agent/loop invocation)
- **Resume**: --resume <run-id> (rehydrate state from `.radcr/state/<run-id>.json` and continue from last checkpoint)
- **Model overrides**:
  - `--model <name>` — override the default primary-review model (default: opus, resolved from `.radcrconfig.yml` `review_model` if present)
  - `--adversarial-model <name>` — override the adversarial-pass model. Default: same model as primary (**self-adversarial**). Pass a different model for a **cross-model** adversarial pass — a different model family challenges the primary's findings. (v5.0 removed `--engine claude|codex|both`: it implied Codex execution that was never implemented. If a caller passes `--engine`, say so plainly and map `both` → cross-model adversarial on Opus, anything else → ignored.)

### Resolve scan mode:

If `--since <commit>` is provided:
- Scope is computed from the commit range (overrides scope argument if present)
- Scan mode defaults to **blame-aware**

If scope is `diff` or `commit`:
- Scan mode defaults to **blame-aware** (only flag issues on changed lines)
- User can override with `--full-scan` to get full-scan behavior

If scope is `repo` or `tree`:
- Scan mode defaults to **full-scan** (flag all issues found)

Record: `blame_aware = true | false` for use in later steps.

### Scope prompt (if scope is missing and --since is not provided):

```
What would you like me to review?
1. Full repository (comprehensive — recommended for pre-release)
2. Current diff (staged + unstaged changes, blame-aware)
3. Latest commit (HEAD only, blame-aware)
4. Working tree (all uncommitted changes)
5. Changes since a specific commit (enter commit hash)
```

If user chooses option 5, prompt for the commit hash.

### Security-deep activation

Set `security_deep = true` if `--security-deep` was passed OR `strictness == launch`.
If `strictness == launch`, it inherits all `public` blocking rules. When
`security_deep` is true:
- In Step 4, also load `${RADCR_DIR}/references/security-deep-mode.md`.
- In Step 6, prepend the security-deep procedure to the subagent's task: run phases
  (a)–(d) from that reference (trust boundaries → data-exposure surface →
  authorization model → secrets), de-prioritize style/perf/nits, and concentrate on
  data exposure + authorization + privileged credentials. The four-level severity
  model and finding format are unchanged.
- In Step 9, enforce the no-false-assurance contract: the report must NOT contain a
  "secure/safe/good to launch" verdict, MUST include the verified-vs-could-not-verify
  ledger, MUST state residual risk, and MUST recommend an independent human
  penetration test of the auth + data-access surface.
- In Step 12, insert the "Launch-Readiness: Data Exposure & Authorization" report
  section (threat-model-lite + honest verdict) per the reference, using the verbatim
  honest-verdict wording.

A BaaS stack (detected in Step 3b) makes security-deep especially relevant, but the
mode is not BaaS-only — it applies the same data-exposure lens to any stack.

## Step 0.5: Checkpoint / Resume

### If `--resume <run-id>` was provided

1. Read `.radcr/state/<run-id>.json`. If missing, error: `No resumable state found for run-id <run-id>. Starting fresh.` and fall through to Step 1.
2. Rehydrate state variables from the JSON: `scope`, `strictness`, `model`, `adversarial_model`, `blame_aware`, `commit_hash`, `file_count`, `annotated_diff_context`, `accepted_risks`, `exclusions`, `automated_check_output`, `primary_findings`, `adversarial_findings`, `phase_completed`.
3. Jump directly to the step AFTER `phase_completed`:
   - `phase_completed: "step_5"` → jump to Step 6
   - `phase_completed: "step_7"` → jump to Step 8
   - `phase_completed: "step_9"` → jump to Step 10
4. Inform the user: `Resumed run <run-id> at Step <N+1>. Phases already completed: <list>.`

### Checkpoint writes (applies to all non-resume runs)

After each of the following steps completes, write/overwrite `.radcr/state/<run-id>.json`:

- After Step 5 (automated checks): `phase_completed: "step_5"`
- After Step 7 (primary review return): `phase_completed: "step_7"` + `primary_findings`
- After Step 9 (review-of-review): `phase_completed: "step_9"` + merged findings

**Run ID format:** `{YYYY-MM-DD}-{HHmmss}` (local time). Create the directory first: `mkdir -p .radcr/state`.

**Cleanup:** After a successful report write in Step 12, move the state file to `.radcr/state/completed/<run-id>.json` so future resumes don't accidentally target a finished run. Prune `completed/` entries older than 30 days.

**Why this matters on Opus:** deep reviews of 500+ file repos can trip compaction mid-flight. Without checkpoints, the orchestrator loses track of findings and must restart. With checkpoints, resume is one flag.

---

## Step 1: Connectivity Disclosure

If NOT --local-only:

```
This review will use internet access for:
- CVE/vulnerability database lookups for your dependencies
- License compliance checks against SPDX databases
- Framework documentation lookups via Context7

No source code or proprietary information is transmitted. Only package names,
versions, and documentation queries are sent.

Proceed with internet access? (yes / switch to local-only)
```

If user switches to local-only, note the restrictions:
- Dependency vulnerability checks limited to locally cached data
- License compliance based on package metadata only
- No framework-specific documentation lookups
- All code analysis, architecture review, and AI slop detection work fully offline

## Step 2: Load Project Config

Check for `.radcrconfig.yml` in the repository root:

```bash
ls .radcrconfig.yml 2>/dev/null
```

If present, read it and extract:
- `exclude_paths`: list of glob patterns to skip
- `accepted_risks`: list of acknowledged findings with justification
- `custom_rules`: list of project-specific review rules
- `strictness_override`: per-category strictness overrides
- `review_focus`: optional emphasis areas
- `review_model`: optional default model for primary review (used in Step 6 unless `--model` is passed)

### Accepted-risk expiry enforcement

For each entry in `accepted_risks`, check `expires`:

- If `expires` is missing → warn: `Accepted risk <id> has no expiry date. Recommend setting one to avoid stale suppression.` Keep the suppression.
- If `expires` parses as a date and `expires < today` → mark the entry as **stale** and surface it in the report:
  ```
  Stale accepted risk (expired {date}): <id> — <description>
  This finding will be RE-EVALUATED in the current review rather than suppressed.
  Update .radcrconfig.yml to renew the acceptance if it's still valid.
  ```
  Do NOT apply suppression for stale entries — let the finding surface. Collect all stale entries and include them in the final report under a "Stale accepted risks" section.
- If `expires >= today` → apply suppression as normal; record the entry for the disclosure section of the report.

If NOT present, proceed with defaults. Note in report: "No .radcrconfig.yml found — using default configuration."

## Step 3: Detect Project Context

**Execution: parallel-first.** Steps 3a (metadata), 3b (stack detection reads), 3d (trust boundary greps), and 3e (file list commands) have no inter-step dependencies and MUST be issued as a single parallel batch. On Opus and Sonnet this cuts Step 3 wall-time ~4–6×. Step 3c (classification) and Step 3f (blame context) depend on 3a/3b/3e output and run after the parallel batch resolves. Haiku may serialize if batching misbehaves.

Run the following detection steps:

### 3a: Repository Metadata
```bash
# Git info
git log --oneline -5 2>/dev/null
git rev-parse HEAD 2>/dev/null
git remote -v 2>/dev/null
```

Record: current commit hash (for report header and staleness tracking).

### 3b: Stack Detection

Detect languages, frameworks, and tooling by checking for:

| File/Pattern | Indicates |
|-------------|-----------|
| `package.json` | Node.js / JavaScript / TypeScript |
| `tsconfig.json` | TypeScript |
| `next.config.*` | Next.js |
| `vite.config.*` | Vite |
| `angular.json` | Angular |
| `vue.config.*` or `nuxt.config.*` | Vue / Nuxt |
| `requirements.txt`, `pyproject.toml`, `setup.py` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `Gemfile` | Ruby |
| `pom.xml`, `build.gradle` | Java / Kotlin |
| `Dockerfile`, `docker-compose.*` | Docker |
| `terraform/`, `*.tf` | Terraform |
| `manifest.json` (with `manifest_version`) | Chrome Extension |
| `electron-builder.*`, main/renderer split | Electron |
| `capacitor.config.*`, `ionic.config.*` | Mobile hybrid |
| `react-native.config.*`, `app.json` (expo) | React Native |
| `.github/workflows/` | GitHub Actions CI |
| `Makefile` | Make-based build |
| `@supabase/supabase-js`/`@supabase/ssr` dep, or a `supabase/` dir | **Supabase BaaS** — load security-checklist §2.5 (RLS/PostgREST) |
| `supabase/migrations/*.sql` with `create policy`/`enable row level security`/`security definer` | Supabase RLS in use — diff for `using (true)`, missing ownership, `user_metadata` trust |
| `firestore.rules`, `database.rules.json`, `storage.rules`, `firebase.json`, `firebase`/`@firebase/*`/`firebase-admin` dep | **Firebase BaaS** — load §2.5 (Firestore/RTDB/Storage rules + Admin SDK) |
| `appwrite`/`node-appwrite`/`appwrite.json`, `pocketbase`/`pb_migrations/`, `@nhost/*`, `aws-amplify`/`amplify/` + `@auth` in `*.graphql` | **Other BaaS** — load §2.5.3 |

When any BaaS marker is present, treat the datastore's row/rule layer as the primary
authorization boundary for the security review (the §2.4 server-IDOR heuristics may
not apply). Also run the public-env-prefix scan for leaked `service_role`/Admin keys:
grep `.env*`, `next.config.*`, `vite.config.*`, `app.config.*`/`app.json` for
`(NEXT_PUBLIC_|VITE_|EXPO_PUBLIC_|PUBLIC_)\w*(SERVICE_ROLE|SERVICE_ACCOUNT|ADMIN|SECRET|PRIVATE_KEY)`.

Read detected config files to determine:
- Framework version
- Build tool
- Test framework
- Linter/formatter configuration
- Deployment target (if inferable)

### 3c: Project Type Classification

Based on detection, classify as one or more of:
- **web-app** — has UI components, routes, pages
- **api** — has route handlers, endpoints, schema definitions
- **chrome-extension** — has manifest.json with manifest_version
- **cli-tool** — has bin entry, commander/yargs/clap, no UI
- **library** — published package, exports API surface
- **electron-app** — has main/renderer process split
- **mobile-app** — React Native, Flutter, Capacitor, etc.
- **saas** — multi-tenant indicators, billing, auth system

A repo can match multiple types (e.g., web-app + api + saas).

### 3d: Trust Boundary Identification

Identify:
- External API integrations (HTTP clients, SDK imports)
- User input entry points (forms, URL params, CLI args, API endpoints)
- Authentication/authorization boundaries
- File system access points
- Database/storage access
- Third-party service integrations
- Environment variable usage
- Secret/credential references

### 3e: Scope File List and Diff Context

Based on the chosen scope, determine the file list:

```bash
# repo scope
git ls-files

# diff scope
git diff --name-only HEAD
git diff --name-only --cached

# commit scope
git diff --name-only HEAD~1 HEAD

# tree scope
git diff --name-only HEAD
git ls-files --others --exclude-standard

# --since <commit> scope
git diff --name-only <commit>..HEAD
```

Apply .radcrconfig.yml exclusions. Remove files matching trust model exclusions
(node_modules/, vendor/, lockfiles, generated code).

Record total file count and estimated review scope.

### 3f: Compute Blame-Aware Diff Context (if blame_aware = true)

When `blame_aware` is true (default for diff/commit/--since scopes), compute a structured
JSON diff context that the subagent will consume in Step 6. v3.0 emits JSON instead of
prose — more reliable across models, lower token cost, easier to index.

**Step 3f.1: Generate per-file diffs**

Run in parallel per changed file:
```bash
git diff -U5 HEAD <file>                  # diff scope
git diff -U5 --cached <file>              # diff scope (staged)
git diff -U5 HEAD~1 HEAD <file>           # commit scope
git diff -U5 <commit>..HEAD <file>        # --since scope
```

**Step 3f.2: Generate blame metadata for changed files**

For each changed file (in parallel):
```bash
git blame --line-porcelain -L <start>,<end> <file> 2>/dev/null
```

Restricting `-L` to changed line ranges (available from the diff hunks) avoids blaming
unchanged code — much faster on large files.

**Step 3f.3: Build the structured JSON diff context**

Produce `annotated_diff_context` as a single JSON document:

```json
{
  "scan_mode": "blame-aware",
  "exception_rule": "Flag pre-existing code only when a CHANGED line depends on it (dependency chain rule).",
  "files": [
    {
      "path": "src/api/users.ts",
      "change_type": "modified",
      "changed_line_ranges": [{"start": 42, "end": 68}],
      "context_line_ranges": [{"start": 37, "end": 73}],
      "diff_hunks": [
        "unified diff text with +/- markers — exactly as git diff -U5 emits"
      ],
      "blame": [
        {"lines": "42-55", "author": "current", "authored_at": "2026-04-16"},
        {"lines": "56-68", "author": "prior", "authored_at": "2025-10-03"}
      ],
      "dependency_edges": [
        {
          "changed_line": 47,
          "depends_on": {"path": "src/lib/auth.ts", "symbol": "validateSession", "lines": "12-30"},
          "kind": "function_call"
        }
      ]
    }
  ]
}
```

**Step 3f.4: Identify dependency chains**

For each changed line, detect:
- Function/method calls to symbols defined elsewhere
- Imports from unchanged modules
- Uses of variables/constants defined in unchanged code
- Extends/implements of classes/interfaces defined elsewhere

Record as entries in `dependency_edges`. The subagent will inspect the depended-upon
symbols for issues that the change newly exposes.

Record the full JSON as `annotated_diff_context` for use in Step 6 (token-substituted
into the primary-review.md template).

## Step 4: Load Project-Type References

For each detected project type, load the corresponding reference:

```
@{{RADCR_DIR}}/project-types/{type}.md
```

These provide type-specific review checklists and patterns.

Also load universal references:
```
@{{RADCR_DIR}}/references/ai-slop-patterns.md
@{{RADCR_DIR}}/references/security-checklist.md
@{{RADCR_DIR}}/references/ux-accessibility-checklist.md
@{{RADCR_DIR}}/references/performance-heuristics.md
@{{RADCR_DIR}}/references/release-readiness.md
```

If `security_deep` is true (Step 0), also load:
```
@{{RADCR_DIR}}/references/security-deep-mode.md
```

## Step 5: Run Automated Checks (if available and permitted)

If NOT --local-only, and tools are available:

**Execution: parallel-first.** All checks below (5a–5e, plus the 5g validator) are independent and should run concurrently. Use `run_in_background: true` on the Bash tool to start each check, then read their outputs once all have completed. Each check gets a per-command timeout (default 120s; configurable via `.radcrconfig.yml` `check_timeout_seconds`). A slow `npm audit` must not block `tsc` or `ruff`.

Run only the checks that match the detected stack (from Step 3b) — do not spawn `cargo audit` on a Node project. Detect tool availability via presence of config files / lockfiles rather than `which`; failed commands exit 0 via `|| true`.

### 5a: Dependency Vulnerability Audit
```bash
# Node.js       (if package.json present)
npm audit --json 2>/dev/null || true
# Python        (if requirements.txt or pyproject.toml present)
pip-audit --format json 2>/dev/null || true
# Rust          (if Cargo.toml present)
cargo audit --json 2>/dev/null || true
# Go            (if go.mod present)
govulncheck ./... 2>/dev/null || true
```

### 5b: License Check
```bash
# Node.js
npx --yes license-checker --json 2>/dev/null || true
# Python
pip-licenses --format=json 2>/dev/null || true
```

### 5c: Secrets Scan
```bash
# Use gitleaks if available
gitleaks detect --source . --report-format json --report-path /tmp/radcr-secrets.json 2>/dev/null || true
# Fallback: pattern-based grep for common secret patterns
```

### 5d: Existing Project Tools
Run only the project-configured linters/type-checkers/tests:

```bash
# Type checking
npx tsc --noEmit 2>/dev/null || true
# Linting
npx eslint . --format json 2>/dev/null || true
# Python
python -m mypy . 2>/dev/null || true
python -m ruff check . --output-format json 2>/dev/null || true
# Tests
npm test 2>/dev/null || true
pytest --tb=short 2>/dev/null || true
```

Capture output for inclusion as evidence in findings. Do not treat tool failures as review failures — record what ran, what didn't, and why (missing tool, timeout, non-zero exit).

### 5e: Build Verification
```bash
# Verify the project builds
npm run build 2>/dev/null || true
# Python
python -m build 2>/dev/null || true
# Go
go build ./... 2>/dev/null || true
```

### 5g: AI-Slop Mechanical Validator — Hallucinated Imports

Run the plugin's own validator (pure stdlib; runs offline, so it is NOT skipped in
`--local-only` mode). Use `python3`, or `python` on Windows:

```bash
# blame-aware scopes — check only the changed files
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-hallucinated-imports.py . --files <comma-separated changed files> --json || true
# repo / tree / --full-scan scopes
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-hallucinated-imports.py . --json || true
```

This is the deterministic pass for AI-slop Pattern #1 (hallucinated imports /
slopsquatting): every external import is verified against the project's lockfiles, and
every relative import against the disk. Its JSON findings (with `CR-HALLUC-NNN`
id suggestions) join `automated_check_output` under the key `hallucinated_imports` —
the primary-review subagent treats them as confirmed-severity evidence rather than
re-deriving them. If Python is unavailable, record `hallucinated_imports: skipped
(no python)` and let the LLM pass cover Pattern #1 on its own.

### 5h: Aggregate & checkpoint

Collect results from all background commands. Build `automated_check_output` — a structured dict keyed by check name (`npm_audit`, `pip_audit`, `gitleaks`, `tsc`, `eslint`, `npm_test`, `npm_build`, `hallucinated_imports`, etc.) with per-check: exit code, duration (ms), stdout (truncated to 50KB per check), stderr (truncated).

Write checkpoint to `.radcr/state/<run-id>.json` with `phase_completed: "step_5"` and the aggregated output.

## Step 6: Spawn Primary Review Subagent (Phase 3 — Deep Review)

### 6.1 Model selection

Resolve the primary-review model in this order (first match wins):

1. `--model <name>` CLI argument
2. `.radcrconfig.yml` `review_model` field
3. Default: **`opus`** (Opus — best for deep reasoning, adversarial protocol, severity calibration)

Fallback guidance:
- **Opus** — default. Best reasoning quality; recommended for production/public strictness.
- **Sonnet** — drop-in for cost-sensitive reviews or quick PR scans. Retains adversarial rigor.
- **Haiku** — only for narrow blame-aware diffs (≤20 changed files) with `--local-only`. Too fast to over-think but also too fast to execute the full 10-category checklist reliably on wide scopes.

Record the chosen model in the run state and in the final report.

### 6.2 Load the externalized prompt template

Read `${RADCR_DIR}/references/subagent-prompts/primary-review.md`. Substitute placeholders with values from prior steps:

| Placeholder | Source |
|-------------|--------|
| `{detected_types}`, `{detected_stack}`, `{detected_framework}` | Step 3b/3c |
| `{scope}`, `{file_count}`, `{commit_hash}`, `{since_commit_or_na}` | Step 3a/3e |
| `{scan_mode}` | `blame_aware ? "blame-aware" : "full-scan"` |
| `{strictness}` | Step 0 |
| `{trust_boundaries}` | Step 3d |
| `{exclusions}`, `{accepted_risks}` | Step 2 (active, non-stale only) |
| `{automated_check_output}` | Step 5h |
| `{annotated_diff_context_json}` | Step 3f (only if blame_aware) |
| `{scoped_file_list}` | Step 3e |

### 6.3 Spawn

```
Agent(
  subagent_type="general-purpose",
  model="{resolved_model}",
  description="RADCR Primary Review",
  prompt="{substituted_primary_review_template}"
)
```

If `model` override is not supported by the current runtime, fall back to the runtime default and note it in the report.

### 6.4 Output format

The subagent emits **JSON-first** findings per the schema in `primary-review.md` (section "Output Format — JSON-first"). Parse the JSON block as authoritative. If the subagent also included a prose summary, ignore it for parsing — use it only for display in Step 10.

If JSON parsing fails (malformed block, missing required fields):
1. Retry once with an explicit `Re-emit your findings as valid JSON matching the schema. The prior output was malformed at: <error>.` message.
2. If the retry also fails, fall back to best-effort markdown parsing (legacy v2.x path) and log a warning in the report's scope-limitations section.

## Step 7: Handle Primary Review Return

Parse the subagent's JSON output (`primary-review.md` schema). Extract:
- `summary` (counts by severity, attribution breakdown)
- `findings` (full array)
- `zero_finding_categories`
- `scope_limitations`

**Checkpoint write:** write `.radcr/state/<run-id>.json` with `phase_completed: "step_7"` and `primary_findings` = the parsed findings array.

### Triage trigger

If `summary.critical >= 50` OR the reviewer flagged fundamental architecture issues (look for findings with category=`architecture`, severity=`critical`, and confidence=`confirmed`), switch to **triage-first mode**:
- Skip adversarial pass (Step 8)
- Skip Step 9 merge
- Jump to Step 12T (Triage Report)

Otherwise, continue to Step 8.

## Step 8: Adversarial Pass (Phase 4)

### 8.1 Model selection

Resolve adversarial model:

1. `--adversarial-model <name>` CLI arg → if it differs from the primary model, this is a **cross-model** pass (a different model family challenges the primary's findings — catches blind spots redundancy can't).
2. Default: same model as primary (**self-adversarial** — uncovers the primary's own blind spots without introducing a different model's biases).

### 8.2 Load externalized prompt

- cross-model (adversarial model ≠ primary model) → read `${RADCR_DIR}/references/subagent-prompts/adversarial-review.md`
- self-adversarial (same model) → read `${RADCR_DIR}/references/subagent-prompts/self-adversarial-review.md`

Substitute placeholders:

| Placeholder | Source |
|-------------|--------|
| `{scan_mode}` | `blame_aware ? "blame-aware" : "full-scan"` |
| `{primary_review_findings_json}` | Step 7 parsed findings (serialized back to JSON) |
| `{scoped_file_list}` | Step 3e |

### 8.3 Spawn

```
Agent(
  subagent_type="general-purpose",
  model="{resolved_adversarial_model}",
  description="RADCR Adversarial Review" | "RADCR Self-Adversarial Pass",
  prompt="{substituted_adversarial_template}"
)
```

### 8.4 Output

Adversarial subagent emits **JSON-first** per the schema in `adversarial-review.md` / `self-adversarial-review.md`. Parse as authoritative. Same retry-once-on-malformed-JSON rule as Step 6.4.

## Step 9: Review of the Review (Phase 5)

After the adversarial pass, merge and calibrate. Then write checkpoint with `phase_completed: "step_9"` and the merged-calibrated findings.

Merge and calibrate:

1. **Merge findings**: Combine primary + adversarial new findings
2. **Apply challenges**: For challenged findings, evaluate the adversarial reasoning.
   If the challenge is well-supported, downgrade or remove. If weak, keep original.
3. **Apply severity adjustments**: Accept well-reasoned re-ratings
4. **De-duplicate**: Merge overlapping findings into single entries
5. **Confidence check**: Any finding with only "possible" confidence and no code evidence
   should be moved to an appendix, not the main findings list
6. **Blocker validation**: Re-verify every finding marked "blocks release: yes"
   - Does it have confirmed/probable confidence?
   - Does it have code evidence?
   - Would a senior engineer agree this blocks release?
7. **Noise check**: If the report has more than 30 minor findings, consolidate into
   category summaries. The report should not be a wall of nits.
8. **Completeness check**: Are all 10 review categories represented? If a category
   has no findings, is the "zero finding" confidence level reasonable?

Record the final calibrated finding list.

## Step 10: Present Findings to User

### 10.0 Non-interactive short-circuit

If `--non-interactive` was passed (or the skill was invoked by another agent that expects a return value), **skip the interactive menu entirely**:

1. Display the summary block (10.1 below) for transcript/logging purposes.
2. Skip to Step 12 (Report Generation) directly.
3. Return findings + verdict to the caller as structured data (the report file path, the parsed findings JSON, and the verdict string).

This path is what the `code-reviewer` agent uses when it invokes the skill, and what `/loop` / CI integrations use. Blocking on a menu prompt in those contexts deadlocks the session.

### 10.1 Interactive path — display summary

```
## Review Complete

**Scope:** {scope} | **Strictness:** {strictness} | **Model:** {model}{IF adversarial model differs} (adversarial: {adversarial_model}){ENDIF}
**Scan mode:** {blame_aware ? "blame-aware (changed lines only)" : "full-scan"}
**Commit:** {commit_hash}
{IF since_commit}**Since:** {since_commit}{ENDIF}
**Files reviewed:** {file_count}

### Finding Summary
| Severity | Introduced | Pre-existing | Total | Blocks Release |
|----------|-----------|-------------|-------|----------------|
| Critical | N         | N           | N     | N              |
| Major    | N         | N           | N     | N              |
| Moderate | N         | N           | N     | -              |
| Minor    | N         | N           | N     | -              |

{IF blame_aware}
*"Introduced" = issues on changed lines. "Pre-existing" = issues in unchanged code
that changed code depends on (dependency chain rule).*
{ENDIF}

### Release Verdict
{verdict} — {one-line justification}

### Top Findings
{top 5 findings by severity, one line each with ID, title, severity, file, attribution}
```

Then display the interactive menu:

```
What would you like to do?

Fix Findings
  1. Fix all blockers
  2. Fix specific findings          (I'll ask which CR IDs)
  3. Get details on a finding       (I'll ask which one)

Accept Findings  ← marks as intentional; won't affect verdict, tracked in .radcrconfig.yml
  4. Accept specific findings       (I'll ask which CR IDs)
  5. Accept all minor findings

View
  6. Show new findings only         (compares against your previous review)

Or type a CR ID directly (e.g. CR-003), or ask me anything about the findings.
```

### Option 1: Fix all blockers
Load and execute `${RADCR_DIR}/workflows/offer-fixes.md` with preset `blockers`.

### Option 2: Fix specific findings
Prompt: `Which CR IDs would you like to fix? Enter IDs separated by commas (e.g. CR-001, CR-003).`
Load and execute `${RADCR_DIR}/workflows/offer-fixes.md` with the specified IDs.

### Option 3: Get details on a finding
Prompt: `Which CR ID would you like more details on?`
Display the full finding entry for that ID: description, evidence, impact, recommendation, and references.
Return to the menu.

### Option 4: Accept specific findings

Prompt:
```
Which findings would you like to accept? Enter CR IDs separated by commas.
(e.g. CR-004, CR-007)
```

Validate that each provided ID exists in the current report's findings list.
If any ID is not found, respond:
```
These IDs were not found in the current report: CR-XXX
Please check the finding IDs above and try again.
```
Re-prompt until all IDs are valid or the user cancels.

Then prompt:
```
Optional: add a brief note on why these are intentional?
This helps future-you remember the reasoning.
(e.g. "auth handled by upstream middleware", "intentional for MVP scope")
Press Enter to skip.
```

Capture the justification (or use `"Accepted by reviewer on {today} — no justification provided"` if skipped).

Compute dates:
- `reviewed_date` = today in ISO 8601 format (YYYY-MM-DD)
- `expires` = exactly one year from today in ISO 8601 format

For each accepted finding ID, build a `.radcrconfig.yml` entry:
```yaml
- id: "{finding-id-lowercased}-{kebab-slug-of-first-5-words-of-title}"
  description: "{verbatim finding title from report}"
  justification: "{user note or default justification string}"
  owner: "self"
  reviewed_date: "{today}"
  expires: "{one year from today}"
  finding_match: "{2-3 key terms extracted from finding title, space-separated}"
```

**Check for `.radcrconfig.yml`:**

```bash
ls .radcrconfig.yml 2>/dev/null
```

**If `.radcrconfig.yml` does NOT exist**, prompt:
```
No .radcrconfig.yml found in this project. Want me to create one?

It will store your accepted findings and let you configure exclusions,
custom rules, and review defaults. Future reviews load it automatically.

  1. Yes, create it
  2. No thanks — accept for this session only
```

If user chooses **1 (Yes)**:
- Read `${RADCR_DIR}/templates/radcrconfig-template.yml`
- Write it to `.radcrconfig.yml` in the repository root
- Append the accepted findings entries under the `accepted_risks:` key
- Then prompt:
  ```
  Created .radcrconfig.yml in your project root.

    1. Add .radcrconfig.yml to .gitignore
    2. Leave it as-is (I'll decide later)
  ```
- If user chooses **1**: run `echo ".radcrconfig.yml" >> .gitignore` (append only if not already present — check first with grep)
- Confirm: `.radcrconfig.yml added to .gitignore`

If user chooses **2 (No thanks)**:
- Do not create `.radcrconfig.yml`
- Note the accepted findings in the session output:
  ```
  Accepted for this session only (not persisted):
  {list of accepted finding IDs and titles}
  These will reappear in your next review.
  ```
- Return to menu.

**If `.radcrconfig.yml` DOES exist**:
- Read the file
- Append the new entries under `accepted_risks:`
- Write the updated file back

Confirm acceptance:
```
Accepted {N} findings and added to .radcrconfig.yml.
These won't affect your release verdict in future reviews.

Note: accepted risks expire {expires date} and will be re-flagged for
re-evaluation. You can adjust the expiry in .radcrconfig.yml.
```

Return to menu.

### Option 5: Accept all minor findings

Identify all findings with severity `minor` in the current report.

If no minor findings exist:
```
No minor findings in this review.
```
Return to menu.

Otherwise, list them:
```
Found {N} minor findings:
{list of CR IDs and titles}

Optional: add a brief note on why these are intentional? Press Enter to skip.
```

Capture justification (same default as Option 4 if skipped).

Apply the same `.radcrconfig.yml` write logic as Option 4 (check exists, create if not, append entries, offer `.gitignore`).

Confirm:
```
Accepted {N} minor findings and added to .radcrconfig.yml.
Note: accepted risks expire {expires date}.
```

Return to menu.

### Option 6: Show new findings only

```bash
ls -t .radcr/history/*.md 2>/dev/null | head -1
```

**If no previous report exists**:
```
No previous review found for this project. Showing all findings.
```
Return to menu without filtering.

**If a previous report exists**:
- Read the most recent report file from `.radcr/history/`
- Extract each previous finding's **fingerprint** (or title + file paths for pre-fingerprint reports). **Never compare by bare finding ID** — IDs restart each run, so ID matching produces false "already known" collisions.
- Identify the scope and strictness used in the previous report from its filename (format: `YYYY-MM-DD-{HHmmss}-{scope}-{strictness}.md`)
- Filter current findings to those with NO fingerprint (or title+file) match in the previous report, per the matching criteria in `report-generation.md` §4

If the previous report used a different scope than the current review, note:
```
Note: previous review used {previous_scope} scope. This review used {current_scope}.
Comparison may not be exact.
```

Display:
```
Filtering to new findings only (comparing against {previous_report_filename})

Previously reviewed: {total_previous} findings
Already known:       {matched} (not shown)
New this review:     {new_count}

─────────────────────────────────────────
{new findings only, formatted as: [SEVERITY] CR-NNN — Title}
─────────────────────────────────────────
```

If all findings are new:
```
All {N} findings are new since your last review.
```

If no new findings:
```
No new findings since your last review. All {N} findings were present
in the previous report.
```

Redisplay the menu scoped to the new findings (options 1-5 operate on the filtered set).

### CR ID typed directly
If the user types a CR ID (matches pattern `CR-[0-9]+`), display the full finding detail for that ID (same as Option 3). Return to menu.

### Free text / question
Answer the question using the current findings as context. Return to menu.

### Exit
If the user types "done", "exit", "quit", or presses Enter with no input, proceed to Step 11 (Fix Application) if fixes were requested, or Step 12 (Report Generation).

## Step 11: Fix Application (if requested)

Load the fix workflow:
```
@{{RADCR_DIR}}/workflows/offer-fixes.md
```

### Fix Protocol Summary:

1. **Scope selection**: User chooses preset or specific IDs
2. **Conflict detection**: If fix A conflicts with fix B, prioritize higher-severity
   or wider-scope fix. Defer the conflicting one. Document conflict in report.
3. **Fix grouping**: Group fixes into logical units (e.g., "auth fixes," "validation fixes")
4. **For each fix group**:
   a. Apply fixes
   b. Run targeted validation immediately:
      - If tests exist for affected code, run them
      - If type checker is configured, run it on affected files
      - If linter is configured, run it on affected files
      - Verify the fix addresses the finding
   c. Commit: one commit per logical fix group
      - Message format: `fix(review): {group description} [CR-{ids}]`
5. **After all fix groups**: Run final scoped re-review of affected areas
   plus blocker revalidation
6. **Report deferred fixes**: List fixes that were deferred due to conflicts,
   with explanation and recommended manual resolution

## Step 12: Report Generation

Load the report workflow:
```
@{{RADCR_DIR}}/workflows/report-generation.md
```

### Report Generation Summary:

Generate the report using the report template and save it to
`.radcr/history/{YYYY-MM-DD}-{HHmmss}-{scope}-{strictness}.md` — **not** to the
repository root (v5.0: a loose root-level report is exactly the floating doc that
repo-hygiene tooling flags). Print the path. Write a root-level
`rad-code-review-report.md` copy only if the user explicitly asks.

The report must include:
1. Executive summary
2. Release verdict with justification
3. Project overview (inferred from repo)
4. Review scope, commit hash, and assumptions
5. Configuration (.radcrconfig.yml exclusions and accepted risks)
6. Top release blockers
7. Findings by severity (with full evidence)
8. Findings by category
9. Bug finder summary
10. Architecture review summary
11. Security review summary
12. UI/UX review summary (if applicable)
13. Accessibility review summary (if applicable)
14. Test and quality review summary
15. Release readiness summary
16. Per-project-type verdicts (if multi-type repo)
17. Overall release verdict
18. False confidence risks (areas where review depth was limited)
19. Adversarial pass results (disagreements, challenges, new findings)
20. Recommended fix order
21. Fastest path to production readiness
22. History comparison (if previous reports exist)
23. Appendix: automated tool output, possible-confidence findings, evidence notes

### Secret Masking
Before writing the report:
- Scan all code snippets for values that look like secrets (API keys, tokens, passwords, connection strings)
- Replace values with `[MASKED]` but preserve key names and context
- Example: `API_KEY = "sk-1234..."` becomes `API_KEY = "[MASKED]"`

### History
```bash
mkdir -p .radcr/history
```

Save report to `.radcr/history/{YYYY-MM-DD}-{HHmmss}-{scope}-{strictness}.md` (unified with `report-generation.md` as of v3.0 — the `HHmmss` segment prevents multiple same-day reviews from overwriting each other).

If previous reports exist:
```bash
ls -t .radcr/history/*.md | head -1
```

Read the most recent report and compare:
- Which previous findings are now resolved?
- Which previous findings remain?
- Which findings are newly introduced?

Include this comparison as a "History Comparison" section in the report.

## Step 12T: Triage Report (if fundamentally broken)

If the project triggered triage-first mode (Step 7):

Generate a triage report instead of the full report:

1. **Clear verdict**: "This project is not fit for release in its current state."
2. **Systemic diagnosis**: What is fundamentally wrong — not individual findings, but the pattern.
   Examples: "No authentication system exists," "The architecture is a single 3000-line file,"
   "All error handling is fake," "The database schema has no constraints."
3. **Top 5-10 blockers**: The most important things to fix first, in order.
   Each with: what, why, scope of effort, dependencies between them.
4. **Remediation roadmap**: Ordered phases to recover the project.
   If incremental repair is a worse investment than partial rewrite, say so plainly.
5. **What works**: Be honest about what IS good. Don't make it a wall of negativity.
6. **Realistic assessment**: How much work would it take to reach each strictness level?

Save the triage report to `.radcr/history/{YYYY-MM-DD}-{HHmmss}-{scope}-triage.md`
and print the path (root copy only on explicit request, same rule as Step 12).

## Step 13: Wrap Up

After report generation:

1. Display the report file path
2. If fixes were applied, list the commits created
3. If deferred fixes exist, list them with instructions
4. Remind user of the commit hash the review was performed against
5. Suggest when to re-run (after significant changes, before next release)

```
## Review Complete

Report saved: .radcr/history/{filename}

Reviewed at commit: {hash}
This report reflects the codebase at that point in time.
Re-run after significant changes for updated findings.
```

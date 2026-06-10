# RADCR Findings Schema v1.0.0

This document defines the exact format for individual findings produced by the
RAD Code Review skill. All reviewers must structure their output using
these formats. The Markdown format is used in the human-readable report. The
JSON format is used in the companion `.json` output file.

---

## Markdown Finding Format

Each finding is rendered as a subsection within its severity group. The format
below must be followed exactly — the report parser and history-comparison logic
depend on consistent structure.

```markdown
#### CR-{{id}}: {{title}}

| Field | Value |
|-------|-------|
| Severity | {{critical/major/moderate/minor}} |
| Category | {{category}} |
| Confidence | {{confirmed/probable/possible}} |
| Blocks Release | {{yes/no/conditional}} |
| Affected Files | {{file:line, file:line}} |

**Why It Matters:**
{{specific impact — not generic}}

**Evidence:**
```{{language}}
{{code snippet with secrets masked}}
```

**How to Verify:**
{{reproduction steps or verification method}}

**Recommended Fix:**
```{{language}}
{{concrete fix code}}
```

**Fix Effort:** {{trivial/small/medium/large}}
```

### Field Definitions

#### `id`
- Format: zero-padded three-digit number (e.g., `001`, `042`, `187`), rendered as `CR-NNN`
- Assigned sequentially within a single review run
- Stable within one report; **not stable across runs** — never used for cross-run comparison
- Used for cross-referencing within the report (fix order, related findings)

#### `fingerprint` (v5.0)
- Format: `{category}:{primary file path}:{first 6 normalized title terms, kebab-cased}`
- Example: `security:src/api/users.ts:sql-injection-via-unsanitized-user-input`
- The **cross-run identity** of a finding — history comparison and "show new findings only" match on fingerprint (then title+file as fallback), never on `id`
- Deterministic: recomputing it for the same finding in a later run must yield the same string (lowercase the path, strip articles/punctuation from the title)

#### `title`
- Short, specific description of the finding
- Must describe the actual problem, not the category
- Good: "SQL injection via unsanitized user input in search endpoint"
- Bad: "Security issue" or "Input validation"

#### `severity`
- **critical** — Security vulnerabilities, data loss risks, or correctness
  failures that affect all users. Always blocks release.
- **major** — Significant bugs, reliability risks, or architectural problems
  that affect some users or degrade the system materially. Blocks release at
  production and public strictness.
- **moderate** — Code quality issues, missing validation for edge cases, or
  maintainability concerns. Blocks release at public strictness only.
- **minor** — Style issues, minor improvements, documentation gaps, or
  suggestions. Never blocks release on its own.

#### `category`
One of the following values:
- `security` — Authentication, authorization, injection, cryptography, secrets
- `bug` — Incorrect behavior, logic errors, race conditions
- `architecture` — Design problems, coupling, scalability concerns
- `performance` — Inefficiency, N+1 queries, memory leaks
- `accessibility` — WCAG violations, keyboard navigation, screen reader support
- `ux` — User-facing behavior problems, confusing flows, missing feedback
- `testing` — Missing tests, flaky tests, inadequate coverage
- `reliability` — Error handling, failure modes, resilience
- `documentation` — Missing or incorrect docs, misleading comments
- `dependency` — Vulnerable or outdated dependencies, license issues
- `configuration` — Build, deploy, or environment configuration problems

#### `confidence`
- **confirmed** — Verified through code analysis; the issue definitely exists.
  Used when the code path is unambiguous and the reviewer can demonstrate the
  problem with evidence.
- **probable** — Strong evidence but some uncertainty remains. The issue almost
  certainly exists but might depend on runtime conditions the reviewer cannot
  fully verify (e.g., specific input data, server configuration).
- **possible** — The code pattern suggests a problem but it may be intentional
  or mitigated elsewhere. Requires human judgment or runtime testing to confirm.
  These findings appear in Appendix B of the full report.

#### `blocks_release`
- **yes** — This finding must be resolved before release.
- **no** — This finding does not block release at the current strictness level.
- **conditional** — This finding blocks release only if a stated condition is
  true. The condition must be specified in the "Why It Matters" section.

#### `affected_files`
- Format: `path/to/file.ext:line` or `path/to/file.ext:start-end`
- Multiple files separated by commas
- Paths are relative to the repository root
- Line numbers refer to the current state of the file at review time

#### `why_it_matters`
- Must describe the specific impact of this finding, not a generic description
  of the vulnerability class
- Good: "An attacker can extract all user email addresses by injecting SQL
  through the `q` parameter on GET /api/search"
- Bad: "SQL injection can allow attackers to access data"

#### `evidence`
- Include the relevant code snippet with surrounding context
- Mask any secrets, tokens, or credentials with `[REDACTED]`
- Use the correct language identifier for syntax highlighting
- Keep snippets focused — include enough context to understand the issue but
  do not paste entire files

#### `how_to_verify`
- Concrete steps to reproduce or verify the issue
- For bugs: input, expected output, actual output
- For security issues: attack steps or proof-of-concept description
- For architecture issues: what to examine and what symptoms to look for

#### `recommended_fix`
- Concrete code showing the fix, not just a description
- Must be syntactically correct and use the project's conventions
- If the fix is non-trivial, include a brief explanation
- If multiple approaches exist, recommend one and note alternatives

#### `fix_effort`
- **trivial** — A one-line change or simple configuration update. Under 5 minutes.
- **small** — A focused change touching 1-3 files. Under 30 minutes.
- **medium** — A change requiring thought, touching multiple files or requiring
  test updates. 30 minutes to a few hours.
- **large** — A significant refactor or redesign. Multiple hours to days.

---

## JSON Finding Format

The JSON format mirrors the Markdown format and is used in the companion
`.json` report file. This format is machine-parseable and supports tooling
integrations, CI/CD gates, and historical comparison.

```json
{
  "id": "CR-001",
  "fingerprint": "security:src/api/search.js:sql-injection-via-unsanitized-user-input",
  "title": "SQL injection via unsanitized user input in search endpoint",
  "severity": "critical",
  "category": "security",
  "confidence": "confirmed",
  "blocks_release": true,
  "affected_files": [
    {
      "path": "src/api/search.js",
      "line": 42,
      "end_line": 48
    },
    {
      "path": "src/api/search.js",
      "line": 105,
      "end_line": 105
    }
  ],
  "description": "The search endpoint interpolates user input directly into a SQL query string without parameterization or sanitization.",
  "impact": "An attacker can extract, modify, or delete any data in the database by injecting SQL through the q parameter on GET /api/search.",
  "evidence": "const results = db.query(`SELECT * FROM items WHERE name LIKE '%${req.query.q}%'`);",
  "verification": "Send GET /api/search?q=' OR '1'='1 and observe that all rows are returned.",
  "remediation": "Use parameterized queries: db.query('SELECT * FROM items WHERE name LIKE $1', [`%${req.query.q}%`])",
  "fix_effort": "trivial",
  "related_findings": ["CR-003", "CR-015"],
  "cwe": "CWE-89",
  "owasp": "A03:2021",
  "wcag": null
}
```

### JSON Field Notes

#### `blocks_release`
In JSON format, this is a boolean (`true`/`false`). Conditional blocks are
represented as `true` with a note in the `description` field explaining the
condition.

#### `related_findings`
Array of finding IDs that are related to this finding. Used to group findings
that share a root cause or that should be fixed together.

#### `cwe`
Common Weakness Enumeration identifier, if applicable. Format: `CWE-nnn`.
Set to `null` if not applicable.

#### `owasp`
OWASP Top 10 (2021) category, if applicable. Format: `Ann:2021`.
Set to `null` if not applicable.

#### `wcag`
WCAG 2.1 success criterion, if applicable. Format: `n.n.n` (e.g., `1.4.3`).
Set to `null` if not applicable.

---

## JSON Report Wrapper Format

The top-level structure of the companion `.json` report file. Contains
metadata, summary counts, the full findings array, and history comparison data.

```json
{
  "version": "1.0.0",
  "date": "2026-03-15T14:30:00Z",
  "commit": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
  "scope": "repo",
  "strictness": "production",
  "model": "opus",
  "verdict": "Not ready for release",
  "verdict_justification": "3 critical and 7 major findings must be resolved.",
  "duration_seconds": 342,
  "summary": {
    "critical": 3,
    "major": 7,
    "moderate": 12,
    "minor": 5,
    "blocks_release": 10,
    "total": 27
  },
  "findings": [
    {
      "id": "CR-001",
      "title": "...",
      "severity": "...",
      "...": "... (full finding object as defined above)"
    }
  ],
  "per_type_verdicts": {
    "security": "fail",
    "architecture": "pass",
    "testing": "conditional",
    "accessibility": "not-applicable"
  },
  "false_confidence_risks": [
    "Concurrency behavior under load was not testable via static analysis."
  ],
  "adversarial_pass": {
    "confirmed": ["CR-001", "CR-002"],
    "severity_adjusted": [
      {
        "id": "CR-005",
        "original_severity": "critical",
        "revised_severity": "major",
        "reason": "Mitigated by upstream validation in middleware."
      }
    ],
    "new_findings": ["CR-028"],
    "disagreements": []
  },
  "config": {
    "config_file": ".radcrconfig.yml",
    "exclude_paths": ["vendor/**"],
    "accepted_risks": ["example-risk-1"],
    "strictness_overrides": {},
    "review_focus": []
  },
  "history": {
    "previous_report": "radcr-report-2026-03-01.json",
    "resolved": ["CR-004", "CR-009"],
    "remaining": ["CR-001", "CR-003"],
    "new": ["CR-028", "CR-029"],
    "trend": "improving"
  }
}
```

### Report Wrapper Field Notes

#### `version`
Schema version for the JSON report format. Follows semver. Current: `1.0.0`.

#### `scope`
One of: `repo` (full repository), `diff` (changed files only), `commit`
(single commit), `tree` (directory subtree).

#### `strictness`
One of: `mvp` (minimum viable), `production` (standard), `public`
(public-release grade).

#### `model` / `adversarial_model`
The primary-review model and, when a cross-model pass ran, the adversarial model
(absent or equal to `model` for self-adversarial runs). Replaces the v4.x `engine`
field — readers of old reports may still encounter `engine: claude|codex|both`.

#### `verdict`
Human-readable verdict string. Examples: "Ready for release",
"Not ready for release", "Ready with conditions".

#### `per_type_verdicts`
Verdict per review category. Values: `pass`, `fail`, `conditional`,
`not-applicable`.

#### `history.trend`
One of: `improving` (fewer/less severe findings than last run), `stable`
(roughly the same), `regressing` (more/worse findings than last run),
`first-run` (no previous report to compare against).

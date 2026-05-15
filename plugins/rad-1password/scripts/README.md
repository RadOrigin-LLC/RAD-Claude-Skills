# rad-1password scripts

Pure-stdlib Python 3.8+ validators that complement the rad-1password skills with mechanical code scans. No `pip install` required.

## scan-hardcoded-secrets.py

Flag hardcoded secrets in source code that should be `op://` references. For each hit, suggest a concrete `op://<vault>/<item>/<field>` reference shape suitable for replacement with `op inject` / `op run` / `op read`.

```bash
python3 scripts/scan-hardcoded-secrets.py <project-root>
python3 scripts/scan-hardcoded-secrets.py <project-root> --files src/a.py,src/b.ts
python3 scripts/scan-hardcoded-secrets.py <project-root> --json
python3 scripts/scan-hardcoded-secrets.py <project-root> --vault prod
python3 scripts/scan-hardcoded-secrets.py <project-root> --high-entropy  # noisier
```

**Detection categories:**

| Category | Severity | Pattern examples |
|---|---|---|
| Provider-prefixed tokens | critical | OpenAI `sk-` / `sk-proj-`, Anthropic `sk-ant-`, GitHub `ghp_` / `github_pat_`, Stripe `sk_live_` / `pk_test_`, AWS `AKIA`, Slack `xoxb-`, Google `AIza`, Twilio `AC`, SendGrid `SG.`, Mailgun `key-`, Supabase JWT |
| URL-embedded credentials | critical | `https://user:pass@host`, `postgres://user:pass@db`, `mongodb://...`, `mysql://...`, `redis://...`, etc. |
| Assignment-shaped | major | `api_key = "..."`, `password: "..."`, `auth_token: "..."`, `db_password = "..."`, `database_url = "postgres://...@..."` |
| High-entropy (optional, `--high-entropy`) | moderate / minor | 32+ chars of base64/hex outside the above categories; flagged as `moderate` for entropy-shaped, `minor` for hash-shaped (likely false positive) |

**Exclusions (always):**

- `.env`, `.env.local`, `.env.development`, `.env.production` — these are *expected* to hold secrets locally
- Lockfiles (`package-lock.json`, `yarn.lock`, `Pipfile.lock`, `poetry.lock`, `Cargo.lock`, `Gemfile.lock`, `go.sum`, etc.)
- Source maps (`*.map`), minified bundles (`*.min.js` / `*.min.css`)
- Common build / vendor dirs (`node_modules/`, `.venv/`, `dist/`, `build/`, `__pycache__/`, `target/`, etc.)

**Default exclusions (overridable):**

- Test files (`tests/`, `__tests__/`, `*_test.py`, `*.test.ts`, `*.spec.js`, `fixtures/`, `mocks/`) — pass `--include-tests` to scan
- `.env.example`, `.env.sample`, `.env.template` — pass `--include-env-example` to scan (useful for replacing placeholders with `op://` references in templates)

**Placeholder detection:**

Lines matching obvious placeholders are skipped (`your_token_here`, `example`, `changeme`, `xxxx`, `0000`, `null`, `undefined`, `password`, `secret`, `token`, `pass`, `foo`, `bar`, `baz`).

**Output:**

- Default: human-readable text with per-finding `op://` suggestions and a replacement-guide footer pointing to `/rad-1password:op-secrets-injection`.
- `--json`: structured output with `validator`, `files_scanned`, `vault`, `findings`. Each finding includes `severity`, `category`, `pattern_id`, `description`, `file`, `line`, `column`, `matched_text`, `masked_text`, `suggested_op_reference`, `note`.

**Exit codes:** `0` clean, `1` findings present, `2` script error.

**Not a replacement for dedicated tools** (gitleaks, trufflehog, detect-secrets) — those have curated regex libraries and live signature feeds. This validator exists to surface candidates inside the rad-1password workflow with a concrete "and here's how it becomes an `op://` reference" suggestion. Use it together with the dedicated scanners in CI; this one is for in-editor use during development.

# rad-code-review scripts

Mechanical validators that turn LLM-eyeballed checks from the review skill into deterministic passes that run before — and complement — the model's reasoning. Same pattern as rad-planner's `plan-lint.py` and rad-a11y's `check-tailwind-contrast.py`.

All scripts are pure Python 3.8+ stdlib. No `pip install` required (the `tomllib` path lights up at 3.11+; older Python falls back to regex).

## check-hallucinated-imports.py

Mechanical detection of AI slop **Pattern #1** ("Hallucinated Imports"). For each Python/JS/TS source file:

1. Extract imports (Python `ast` module; JS/TS regex).
2. Classify as: stdlib | builtin | relative | external | scoped | submodule.
3. For external/scoped/submodule: verify the package exists in a project lockfile.
4. For relative imports: verify the file path resolves to disk.

```bash
python3 scripts/check-hallucinated-imports.py <project-root>
python3 scripts/check-hallucinated-imports.py <project-root> --files src/a.py,src/b.ts
python3 scripts/check-hallucinated-imports.py <project-root> --json
python3 scripts/check-hallucinated-imports.py <project-root> --include-tests
```

**Lockfile support:**

| Ecosystem | Files parsed |
|---|---|
| JavaScript / TypeScript | `package-lock.json` (npm v1 / v2+), `yarn.lock`, `pnpm-lock.yaml`, `package.json` (`dependencies` / `devDependencies` / `peerDependencies` / `optionalDependencies`) |
| Python | `requirements.txt`, `pyproject.toml` (`project.dependencies`, `project.optional-dependencies`, `tool.poetry.dependencies`, poetry groups), `Pipfile.lock`, `poetry.lock`, `uv.lock` |

**Python name normalization (PEP 503, partial):** lockfile entries are compared in their declared form AND a `_`-swapped form so that `python-dotenv` in requirements.txt matches `import dotenv`. False negatives are preferred to false positives — under-flag rather than over-flag, since slopsquatting is the harm we're trying to prevent.

**What gets a finding:**

| Severity | When |
|---|---|
| `major` | An external package referenced by `import` or `require` is not declared in any parsed lockfile (slopsquatting risk). |
| `major` | A relative import (`./foo`, `from .module`) doesn't resolve to a file or directory on disk. |

**When no findings are emitted:**

- Imports of stdlib modules (Python `os`, `json`, `re`, ...) — always skipped.
- Imports of Node builtins (`fs`, `path`, `node:crypto`, ...) — always skipped.
- Test files (`tests/`, `__tests__/`, `*_test.py`, `*.test.ts`) — skipped unless `--include-tests`.
- Common build / vendor directories (`node_modules/`, `.venv/`, `dist/`, `build/`, `__pycache__/`, etc.) — never scanned.
- Files in a project with NO matching lockfile — flagged via the summary, not via per-import findings (without a lockfile we can't be authoritative).

**Output:** human-readable text by default; structured JSON with `--json`. Each finding emits an `id_suggestion` shaped as `RADCR-HALLUC-NNN` for downstream use by the review report assembly.

**Exit codes:** `0` clean, `1` findings present, `2` script error.

## Where this gets invoked

| Caller | Invocation | When |
|---|---|---|
| `/rad-code-review` skill | Step 5g (automated checks phase) | After Step 5a-5f run in parallel, before the LLM phases — the validator's findings are part of the `automated_check_output` consumed by the primary-review subagent. |
| User direct | `python3 plugins/rad-code-review/scripts/check-hallucinated-imports.py <root>` | Standalone use without the full review workflow. |
| CI / hook | Same, with `--json` and `--files <changed-files>` | Pre-merge or pre-commit gate. |

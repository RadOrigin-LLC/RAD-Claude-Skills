# rad-explain scripts

Two pure-stdlib Python 3.8+ validators that enforce the plugin's two foundational rules: every substantive claim should trace to repo source, and nothing should overpromise. No `pip install` required.

The rad-explain skills (`narrate-project`, `elevator-pitch`, `draft-pitch`, `explain-document`, `ground-readme`) each invoke these validators as a final pass before surfacing their output to the user. The validators can also be run standalone over any Markdown file.

## check-grounding.py

For each substantive claim in an output file, find supporting evidence in the repo. Flag claims with no traceable source.

```bash
python3 scripts/check-grounding.py <file.md>
python3 scripts/check-grounding.py <file.md> --repo /path/to/project
python3 scripts/check-grounding.py <file.md> --json
python3 scripts/check-grounding.py <file.md> --min-token-length 5   # stricter
```

**How it works:**

1. Parses the output file line by line; skips fenced code blocks, headers, bullets, table rows
2. Splits each line into sentences
3. For each sentence, extracts substantive tokens (proper nouns / CamelCase identifiers, numbers, hyphenated identifiers, long technical terms)
4. Concatenates all source files in the repo (`.py`, `.md`, `.js`, `.ts`, `.go`, `.rs`, `.rb`, `.json`, `.yml`, `.toml`, etc.; skips `node_modules`, `.venv`, `dist`, `build`, etc.)
5. For each claim, checks whether its tokens appear in the corpus

**Token classification (calibrates severity):**

- **Proper-noun-shaped** — starts uppercase ("Faunero", "OpenAI"), CamelCase ("RadPlanner"), or hyphenated identifier ("rad-planner"). If ANY of these are missing from the corpus → `warning` (the claim names a specific thing that isn't in the repo).
- **Other substantive** — lowercase technical terms (≥7 chars), hyphenated common terms, numbers. If most of these are missing and there are no proper nouns at all → `info` (loose grounding).

**Severity:**

- `warning` — Claim names a specific term not found in repo source (high-confidence unbacked)
- `info` — Claim has 75%+ of substantive tokens missing but no specific names involved (lower-confidence; sometimes a false positive due to generic vocabulary)

**Honest scope:** The validator is heuristic. It will:

- Surface real unbacked claims (intended)
- Surface false positives when claim backing exists outside the corpus (commit messages, external docs, live data, recent uncommitted changes)
- Miss claims whose tokens appear in unrelated repo contexts (e.g., "supports tokens" passing because `tokens` shows up in a 1Password skill)

It is NOT a truth-checker. Real claim-source matching needs natural-language reasoning beyond stdlib Python. The validator's job is mechanical: did the substantive content of this claim leave ANY trace in the source?

**Exit codes:** `0` clean, `1` warning findings, `2` script error.

## check-overpromise.py

Flag sensational language, vague-quantity claims, and marketing fluff.

```bash
python3 scripts/check-overpromise.py <file.md>
echo "<copy>" | python3 scripts/check-overpromise.py -
python3 scripts/check-overpromise.py <file.md> --json
python3 scripts/check-overpromise.py <file.md> --strict   # tighter
```

**Detection categories:**

| Category | Severity | Patterns |
|---|---|---|
| `superlative` | critical | "the only", "the best", "world-class", "industry-leading", "unmatched", "unparalleled", "revolutionary", "groundbreaking", "transform/revolutionize/disrupt" |
| `production_ready` | critical | "production-grade", "battle-tested", "enterprise-grade", "mission-critical", "bank-grade", "military-grade" |
| `vague_quantity` | warning | "N+ X", "thousands of", "millions of", "countless", "many more" — flagged unless paired with enumeration |
| `fluff` | warning | "seamless", "frictionless", "elegant", "beautiful", "intelligent", "smart", "powerful", "robust" |
| `intensifier` | info | "incredibly X", "extremely X", "absolutely X", "completely X" |

**Backing-aware downgrade:** if backing language ("verified", "measured", "see [doc]", "per RFC", "benchmark", "enumerated below") appears within 200 chars of a flagged phrase, severity drops one level (critical → warning, etc.). Pass `--strict` to disable. The user is the final judge — the validator surfaces candidates.

**Skipped contexts:**

- Inside fenced code blocks (```...```)
- Inside inline backticks
- Lines starting with `#`, `//`, `/*`, `<!--`, copyright/license/version headers, file paths in backticks

**Exit codes:** `0` clean, `1` warning/critical findings, `2` script error.

## When these run

| Caller | Invocation |
|---|---|
| `/rad-explain` skills | Final-pass validation before surfacing output to user. Both validators run; findings included in the surfaced summary. |
| User direct | Standalone via `python3 plugins/rad-explain/scripts/<validator>.py <file>` |
| CI / pre-commit hook | Same, with `--json` |
| Other rad-* plugins | Available for external invocation (e.g., rad-writer's `review-readme` skill could run `check-overpromise.py` on the file under review) |

## Together — the rad-explain principle

These two validators encode the rad-explain plugin's foundational rule: external-facing copy should be **grounded** (every substantive claim traceable to source) and **honest** (no overpromise patterns). Each skill in the plugin runs both as a final pass; the user sees what passed and what surfaced before the output is finalized.

The principle is the same one the rad-claude-skills marketplace applied to its own listings post-audit: no superlatives without backing, no vague-quantity claims without enumeration, no marketing fluff. rad-explain eats the marketplace's own dog food.

# rad-explain

Honest project explanation for any repo. Five skills generate audience-targeted external communications from a project's internal artifacts (code, docs, planning files), with two pure-stdlib Python validators that enforce the plugin's two foundational rules: every substantive claim must trace to repo source, and nothing should overpromise.

The principle: external-facing copy should be **grounded** and **honest**. ChatGPT and similar tools will happily puff a project — they have no source of truth to check against. rad-explain checks every output against the repo, surfaces unbacked claims, and refuses superlative / sensational language.

## Status

Initial release. Built as part of the rad-claude-skills marketplace audit, where the same "no sensational copy" guardrail was applied to the marketplace's own listings. rad-explain eats that dog food.

## What's inside

### Skills

| Skill | What it produces | When to use it |
|---|---|---|
| `/rad-explain:narrate-project` | Plain-English description of a project, audience-adaptive (non-dev / investor / future-self / new-collaborator) | "Explain what this project is" for a human reader. Works on any repo. |
| `/rad-explain:elevator-pitch` | ~150-word / ~30-second-spoken pitch | Cold introductions, conference one-liners, "what do you do?" answers, party explanations |
| `/rad-explain:draft-pitch` | One-pager / executive summary / deck-equivalent text | Funding applications, grant proposals, partnership memos, pitch-deck content |
| `/rad-explain:explain-document` | Interpretation of a specific repo file (a plan, ADR, architecture doc, AI-generated spec, contract) | "What does this commit me to?", "What does this assume?", "Where could this go wrong?" before approving an AI-generated plan |
| `/rad-explain:ground-readme` | README / marketplace-listing audit or fresh generation against actual code | Pre-publication README review; honest first-time generation from code |

### Validators (pure-stdlib Python 3.8+, no `pip install`)

| Validator | What it catches |
|---|---|
| `scripts/check-grounding.py` | Substantive claims with no traceable source in the repo (proper-noun-shaped tokens are checked strictly; other-substantive tokens loosely) |
| `scripts/check-overpromise.py` | Superlatives (`the only`, `best-in-class`, `world-class`, `revolutionary`); vague-quantity claims without enumeration (`N+ platforms`, `thousands of users`); marketing fluff (`seamless`, `powerful`, `elegant`); production-readiness assertions without evidence (`production-grade`, `battle-tested`); filler intensifiers |

Both validators are invoked automatically by every rad-explain skill as a final pass before output is finalized. They can also be run standalone over any Markdown file.

## Foundational rules

Every output produced by this plugin obeys two rules:

1. **Grounded.** Every substantive claim traces to repo source. If a claim's substantive tokens (proper nouns, version numbers, named capabilities, hyphenated identifiers) don't appear anywhere in the codebase, the claim is flagged as unbacked. The user judges whether each is a real gap or a false positive (e.g., backing exists in commit messages, external docs, or live data not in the corpus).
2. **Not overpromising.** No superlatives without backing, no vague-quantity claims without enumeration, no marketing fluff, no sensational framing. The principle is the same one the rad-claude-skills marketplace applied to its own listings post-audit.

These rules are non-negotiable. If a skill's draft fails either validator, the skill surfaces findings and offers revision before finalizing.

## Cross-plugin notes

- **Works on any repo.** No rad-planner dependency. Skills read `docs/vision.md`, `docs/decisions/*.md`, `docs/planning/current.md`, `docs/status.md`, `docs/roadmap.md` if present; fall back to README + project manifest + source structure when absent.
- **`narrate-project` works on any repo.** It reads a `docs/` directory if present (a PRD, plan, decision log) and falls back to README + project manifest + source structure otherwise.
- **The validators are reusable.** Other rad-* plugins can shell out to `check-grounding.py` and `check-overpromise.py` directly. They take a Markdown file and produce JSON findings.

## Honest scope

- **Not a truth-checker.** The grounding validator is heuristic — token absence is suggestive, not definitive. The validator's job is mechanical: did the substantive content of a claim leave ANY trace in the source?
- **Not a fact-extractor.** rad-explain doesn't read code to derive facts; it reads what's already written (in code, docs, manifests) and synthesizes audience-appropriate prose.
- **Not a tone tool.** Voice / style polish isn't the focus; the focus is honesty + grounding.
- **Subject to false positives.** Both validators surface candidates; the user is the final judge. Backing language nearby a flagged phrase ("verified", "measured", "see [doc]") triggers a one-level severity downgrade in `check-overpromise.py`; pass `--strict` to disable.

## Example usage

```
# Plain-English narrative for a non-developer audience
/rad-explain:narrate-project --audience non-dev

# Short pitch
/rad-explain:elevator-pitch --audience generalist

# Long-form pitch for an investor
/rad-explain:draft-pitch --shape one-pager --audience investor

# What does this AI-generated plan actually commit me to?
/rad-explain:explain-document docs/proposed-architecture.md --mode commitments

# Audit my README against the actual code
/rad-explain:ground-readme --mode audit

# Generate a fresh README from code with grounding controls
/rad-explain:ground-readme --mode generate
```

## License

Apache 2.0. See LICENSE at the repo root.

# Agent Operating Manual

## Project

Tidemark is a CLI tool that ingests NOAA tide-station CSVs and produces per-station daily peak/trough summaries with anomaly flags.

## Read order

- Before implementation, read `docs/status.md` and `docs/planning/current.md`.
- Read `docs/architecture.md` before any structural change to the ingest pipeline.
- Read `docs/decisions/` before revisiting choices already made.

## Hard boundaries

- Do not expand scope beyond `docs/planning/current.md`.
- Do not change the CSV input contract or output JSON schema without an ADR.
- Do not add a new runtime dependency without explicit approval — record the proposal as a candidate ADR first.

## Commands

- Install: `uv sync`
- Unit tests: `uv run pytest`
- Lint: `uv run ruff check`
- Typecheck: `uv run mypy src/`
- Build: `uv build`

## Engineering rules

- Prefer the smallest change that satisfies the acceptance criteria.
- Reuse existing patterns before introducing new abstractions.
- When behavior changes, update tests in the same change set.
- When behavior or workflow changes, update the relevant docs in the same change set.

## Definition of done

- The acceptance criteria in `docs/planning/current.md` are satisfied.
- Relevant validation commands have been run and results are recorded in `docs/status.md`.
- The diff stays within the stated scope and non-goals.

## Escalate instead of guessing

- Missing requirement or conflicting requirement
- Change would affect the CSV input contract or output JSON schema
- Validation fails and the fix requires scope expansion

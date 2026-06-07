# Current Plan

## Objective

Ship M2: per-station anomaly detection that flags days where peak height, trough height, or peak-trough range deviates beyond a configurable σ threshold from a 30-day rolling baseline.

## Why this matters

M1 (ingest) gives us clean tide data per station. Anomaly detection is what makes Tidemark useful — operators need to know which stations to inspect, not stare at every row.

## Non-goals

- Not building a dashboard UI — CLI + JSON output only this milestone
- Not adding real-time NOAA API polling — batch CSV input only

## Current milestone

M2: Anomaly detection on rolling 30-day baseline

## Acceptance criteria

- [x] Anomaly module imports cleanly and exposes `detect_anomalies(station_id, window_days)` signature
- [ ] Default σ threshold is configurable via CLI flag and defaults to ±2σ
- [ ] Output JSON includes `anomaly_flags` array per day with reason codes
- [ ] Stations with <30 days of data emit `insufficient_data` flag rather than failing
- [ ] Anomaly detection runs in <1s for a single station × 365 days on the test hardware

## Validation commands

- `uv run pytest tests/test_anomaly.py` — anomaly detection unit tests
- `uv run pytest tests/test_cli.py::test_anomaly_flag` — CLI flag integration
- `uv run mypy src/` — strict type-checking passes
- `uv run ruff check` — lint passes

## Planned changes

- [x] `src/tidemark/anomaly.py` — module scaffold
- [ ] `src/tidemark/anomaly.py` — detection logic
- [ ] `src/tidemark/cli.py` — add `--sigma` flag
- [ ] `tests/test_anomaly.py` — full test coverage

## Open questions

- Default σ threshold: ±2 (catches ~5% of days) vs ±3 (catches ~0.3%)? Lean toward ±2 for operator awareness.
- Should we support per-station overrides via config file in M2 or defer to M3?

## Risks

- Risk: rolling baseline gives false positives at season change
  - Mitigation: detrend before applying σ threshold; add detrend toggle as fallback
- Risk: NOAA data quirks in older years (pre-2010) may break parser assumptions
  - Mitigation: ingest module already flags malformed rows; anomaly module skips those

## Stop conditions

Stop and ask for approval if:

- The output JSON schema must change
- A new runtime dependency must be added
- Performance regression in M1 ingest occurs

## Notes for the next session

- Most likely next step: implement the rolling-window detrend so the σ baseline is meaningful at season boundaries
- Files likely to change: `src/tidemark/anomaly.py`, `tests/test_anomaly.py`
- What must remain true: existing M1 ingest pipeline keeps working untouched

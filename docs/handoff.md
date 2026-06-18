# Handoff

**Updated:** 2026-06-18
**Branch:** main
**Working tree:** clean after push

<!-- A snapshot, not a log. Overwritten each /wrapup from git evidence. -->

## Last completed

- **Extracted `rad-okf` into its own repository.** It is now the standalone **`okf-manager`** repo (`https://github.com/RadOrigin-LLC/okf-manager`), with the plugin renamed `rad-okf` → **`okfm`** (commands are `/okfm:<skill>`). Before extraction it shipped **v0.4.0** (OKF-spec conformance: `okf_version`, `resource`, citations; nested per-directory `index.md`; a reader-first `map` browser with a needs-attention lens; and a producer surface — `seed` from SQLite/OpenAPI/tree and bounded `enrich`). 138 stdlib-unittest tests pass.
- **Removed `rad-okf` from this repo:** deleted `plugins/rad-okf/` and its `marketplace.json` entry. Marketplace bumped **v1.32.0 → v1.33.0** (now **13 plugins**).

## Current focus

Nothing pending in this repo for OKF — that work now lives in `okf-manager`. This marketplace is back to its other 13 plugins.

## Next action

The open follow-up belongs to the new repo: the **Codex mirror** of okfm in `rad-codex-skills` (shared Python engine + `.codex-plugin` manifests), deferred per the harness boundary.

## Validation

`marketplace.json` re-validated (13 plugins, v1.33.0). okfm's full suite passes in its new home (`cd <okf-manager> && for t in tests/test_*.py; do python "$t"; done` → 138 OK).

## Watchouts

- `docs/LAPTOP-SETUP.md` is a known loose doc (deliberately kept) — the SessionStart scan flags it; resolve via `/rad-repo-manager:repo-align` only if you decide to file/move it.
- git `autocrlf` prints cosmetic "LF will be replaced by CRLF" warnings on commit; harmless.

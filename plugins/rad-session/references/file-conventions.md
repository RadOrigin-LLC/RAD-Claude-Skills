# File Conventions

This file has moved. The canonical specification of the RAD doc structure — operating manual (`CLAUDE.md` and/or `AGENTS.md` per agent scope), `docs/vision.md`, `docs/architecture.md`, `docs/planning/current.md`, `docs/status.md`, `docs/planning/archive/`, `docs/decisions/`, plus optional `docs/roadmap.md` — lives at the repository root:

→ **[`docs/doc-conventions.md`](../../../docs/doc-conventions.md)** (canonical source, v5.0)
→ **[`docs/cross-plugin-contracts.md`](../../../docs/cross-plugin-contracts.md)** (single-writer rule and sectioned-writer exception)
→ **[`docs/status-md-schema.md`](../../../docs/status-md-schema.md)** (`docs/status.md` 8-section schema)

Both rad-session and rad-planner reference the same conventions. If you found this file through an old link, follow the pointers above. If you're editing the conventions, edit the canonical files at the repo root — don't fork copies here.

> **Historical note.** Prior to v5.0 this pointer referenced `docs/file-conventions.md` (the v4.0 "8-doc standard": `CLAUDE.md`, `HANDOFF.md`, `session-log.md`, `PRD.md`, `ARCHITECTURE.md`, `ASSUMPTIONS.md`, `DECISIONS.md`, `PLAN.md`). v5.0 replaced that layout with the canonical structure above. `HANDOFF.md` is no longer read or written — `docs/status.md` (evidence-based, project-scoped) replaces it. `.claude/session-log.md` is no longer read or written — `docs/planning/archive/` (shipped-milestone journal) replaces it.

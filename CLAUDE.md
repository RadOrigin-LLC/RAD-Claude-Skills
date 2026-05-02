# RAD Claude Skills

## Tech Stack
- Standalone Claude Code skills and plugins (markdown-based, no build step)
- Git repository, Apache 2.0 license
- Cross-platform install scripts (bash + PowerShell)

## Conventions
- Plugins live in `plugins/` (for Claude Code CLI, Desktop, Cowork)
- Claude.ai skills live in `skills/` (importable ZIPs for claude.ai)
- Each skill has a `SKILL.md` with frontmatter (name, description, argument-hint, allowed-tools)
- Reference docs go in `references/`, workflows in `workflows/`, templates in `templates/`
- Design specs and backburner ideas go in `C:\Dev\plans\YYYY-MM-DD-<topic>-design.md` (local only, not tracked by git)

## Harness Boundary
- This repository is the source of truth for Claude-native skills, plugins, agents, and Claude-specific metadata.
- Do not optimize this repository for Codex. Port ideas into `C:\Dev\rad-codex-skills` instead of editing Codex harness files here.
- Claude Code may work on shared application repositories, but Claude-specific operating instructions belong in `CLAUDE.md`, `.claude/`, and `C:\Dev\rad-claude-skills`.
- Codex-specific instructions belong in `AGENTS.md`, `.codex/`, `.agents/`, and `C:\Dev\rad-codex-skills`.

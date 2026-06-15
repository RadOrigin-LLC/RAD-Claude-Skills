# RAD Codex Skills

## Tech Stack
- Standalone Codex skills and plugins (markdown-based, no build step)
- Git repository, Apache 2.0 license
- Cross-platform install scripts (bash + PowerShell)

## Conventions
- Plugins live in `plugins/` (for Codex CLI, Desktop, Cowork)
- Codex.ai skills live in `skills/` (importable ZIPs for Codex.ai)
- Each skill has a `SKILL.md` with frontmatter (name, description, argument-hint, allowed-tools)
- Reference docs go in `references/`, workflows in `workflows/`, templates in `templates/`
- Design specs and backburner ideas go in `C:\Dev\plans\YYYY-MM-DD-<topic>-design.md` (local only, not tracked by git)

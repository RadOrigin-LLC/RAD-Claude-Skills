# rad-okf

Build and maintain an [Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) knowledge base from Claude Code — for developers consolidating a repo's knowledge and for non-technical knowledge workers building an AI-readable "second brain."

An OKF bundle is just a directory of markdown files with YAML frontmatter: human-readable, git-friendly, and consumable by any AI agent without an SDK or server. This plugin keeps one **healthy** — easy to build, hard to let rot.

## Status

v0.1 — in active development.
- **Available now:** `check` (validate), `map` (visualize).
- **Landing next:** authoring (`start`, `new`, `add`, link-safe `move`) and ingestion (`convert`, `scan`, `find`), plus an always-on `okf` conventions skill.

## Commands

- **`/rad-okf:check`** — validate a bundle: frontmatter + required `type`, broken cross-links, orphaned concepts, and staleness. Read-only.
- **`/rad-okf:map`** — generate a self-contained HTML graph of the bundle (no dependencies, opens in a browser).

> **Link syntax:** v0.1 checks standard markdown links (`[text](path.md)`), which is what OKF requires. Obsidian `[[wikilink]]` syntax isn't parsed yet — if you author in Obsidian, enable its **"Use [[Wikilinks]]" → off / Markdown links** setting so links stay OKF-conformant and `check` can see them.

## Design principles

- **Dependency-free:** stdlib Python 3 engine. No `pip`, no server, no SDK.
- **Never destructive:** every write is previewed before it happens; your hand-authored text, comments, and formatting are preserved.
- **Sync-agnostic:** the plugin manages the knowledge; you sync the folder however you like (git, a cloud-synced folder, Obsidian, Syncthing).

## Requirements

- Python 3 on PATH.

## License

Apache-2.0

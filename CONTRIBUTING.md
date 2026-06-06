# Contributing to RAD Claude Skills

Thanks for your interest in contributing! Whether it's a bug report, new skill, improvement to an existing plugin, or documentation fix — all contributions are welcome.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/issues) to avoid duplicates
2. Use the **Bug Report** issue template
3. Include: what you expected, what happened, and steps to reproduce
4. Mention which skill/plugin is affected and your Claude Code version

### Suggesting Features

1. Open an issue using the **Feature Request** template
2. Describe the use case — what problem does it solve?
3. If you have ideas for implementation, share them

### Submitting Changes

1. **Fork** the repository
2. **Create a branch** from `main` (`git checkout -b my-change`)
3. **Make your changes** — see the style guide below
4. **Test your changes** by installing the skill/plugin locally in Claude Code
5. **Commit** with a clear message (see commit conventions below)
6. **Open a Pull Request** against `main`

## Style Guide

### Skill Files (SKILL.md)

- Use clear, specific trigger descriptions so Claude activates skills at the right time
- Include concrete examples in skill instructions
- Keep frontmatter `description` under 200 characters
- Test that your skill triggers correctly before submitting

### Plugin Structure

Follow the standard Claude Code plugin layout:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json        # Valid plugin manifest
├── skills/                # One folder per skill
│   └── my-skill/
│       └── SKILL.md
├── agents/                # Optional
├── commands/              # Optional
└── references/            # Optional
```

### General

- No secrets, API keys, or credentials in any file
- Keep reference docs factual and up to date
- Prefer practical examples over abstract descriptions

## Commit Conventions

Use clear, descriptive commit messages:

```
feat: add new keyword clustering skill
fix: correct trigger description for schema-architect
docs: update installation instructions for Windows
refactor: simplify aeo-optimizer scoring logic
```

Prefix with: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, or `test:`

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## Questions?

Open a [discussion](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/discussions) or an issue — happy to help.

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).

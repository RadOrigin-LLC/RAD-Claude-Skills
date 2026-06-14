# rad-para-second-brain — An AI that actively manages your PARA second brain. Not just knowledge about it.

Most PARA tools tell you about the methodology. rad-para-second-brain implements it for you — organizing notes, running weekly reviews, distilling raw captures into usable knowledge, and maintaining continuity between sessions via the Hemingway Bridge pattern. Based on Tiago Forte's Building a Second Brain.

## What's Included

| Component | Name | Purpose |
|-----------|------|---------|
| Skill | **para-organize** | Core PARA setup, classification, diagnosis, review workflows |
| Skill | **progressive-summarization** | Apply distillation layers (bold, highlight, executive summary) to raw notes |
| Skill | **express-workflow** | Assemble Intermediate Packets into output via Archipelago of Ideas |
| Skill | **hemingway-bridge** | PARA-aware session handoffs (integrates with rad-repo-manager) |
| Skill | **twelve-favorite-problems** | Interactive workshop to create a personal capture filter |
| Agent | **para-weekly-reviewer** | Scans PARA folders, finds stale projects, flags inbox overflow, generates review briefing |
| Agent | **para-auditor** | Validates folder structure, detects anti-patterns, evaluates project health |

## Reference Files

4 comprehensive reference files (1,200+ lines) under `skills/para-organize/references/`:

- `para_method.md` — PARA definitions, tool-specific setup guides (Notion, Obsidian, Apple Notes, Google Drive, plain files), PARA for teams
- `code_framework.md` — CODE steps, capture criteria, 12 Favorite Problems, AI-enhanced workflows
- `workflows.md` — Project kickoff/completion checklists, weekly/monthly reviews, digital detox
- `creative_techniques.md` — Intermediate Packets, Archipelago of Ideas, Hemingway Bridge, Dial Down the Scope

## Installation

```bash
claude plugins add ./RAD-Claude-Skills/plugins/rad-para-second-brain
```

## Usage Examples

```
# Set up PARA from scratch
"Help me set up a Second Brain"

# Distill a raw article
"Apply progressive summarization to this article"

# Run weekly review
"Run my weekly review"

# Audit folder structure
"Audit my PARA system"

# Create capture filter
"Help me identify my 12 favorite problems"

# Assemble notes into output
"I have research notes — help me write an article"

# Session handoff
"Write a hemingway bridge for what I was working on"
```

## Optional Integration

- **rad-repo-manager**: The hemingway-bridge skill integrates with rad-repo-manager's `/wrapup` and `/startup` cycle for seamless session handoffs.

## License

Apache-2.0

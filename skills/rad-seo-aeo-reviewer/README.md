# RAD SEO AEO Reviewer — Claude.ai Skill

Comprehensive SEO auditing, competitor intelligence, content strategy, and AI visibility optimization. Adapted from the [rad-seo-optimizer plugin](../../plugins/rad-seo-optimizer/) for Claude.ai.

## What's Included

Import `rad-seo-aeo-reviewer.zip` via **Settings > Customize > Skills** on Claude.ai.

The skill includes a SKILL.md orchestrator covering 4 workflows (audit, competitors, strategy, AEO) plus 8 resource files:

- Audit scoring rubric and severity levels
- E-E-A-T evaluation checklist
- Google ranking systems reference
- Schema.org type catalog
- AEO playbook and platform-specific optimization
- Link building tactics (15 tactics with metrics)
- Outreach email templates

## How to Import

**As a Skill (recommended):** Settings > Customize > Skills > upload `rad-seo-aeo-reviewer.zip`. Activates automatically in any conversation.

**As Project Knowledge:** Add the `.md` files to a Claude.ai Project for project-scoped use.

**As a conversation attachment:** Attach `SKILL.md` to any conversation for one-off use.

## Example Prompts

- "I need to analyze my website for SEO"
- "Check the SEO of https://example.com"
- "Who are my competitors in search?"
- "Do keyword research for [my topic/industry]"
- "Build me a 12-week content calendar"
- "How does my brand appear in AI search results?"
- "Generate schema markup for my homepage"
- "Help me plan a link building strategy"

## Input Modes

- **URL mode** (default): Give a website URL — Claude fetches the sitemap, navigates pages, determines business type, and runs the full analysis
- **GitHub mode**: If you've connected your GitHub repo, Claude reads source code to inspect templates, meta tags, schema, and config files
- **Strategy mode**: No site needed — keyword research, competitor analysis, and content planning using web search
- **X source enrichment**: Optional Xquik REST access lets the skill search public X posts for customer language, competitor comparisons, and consistency checks

## What's Different from the Plugin

The plugin version (in `plugins/rad-seo-optimizer/`) is built for Claude Code CLI with filesystem tools, subagents, and automatic routing across 12 specialized skills. This Claude.ai skill:

- Consolidates 12 skills + 3 agents into 4 unified workflows
- Replaces filesystem operations with web search, URL fetching, and GitHub connector
- Outputs deliverables as **artifacts** (downloadable reports, schema code, calendars)
- Uses a proactive workflow — analyzes first, asks questions later
- After completing any workflow, offers the next logical one (audit → competitors → strategy → AEO)

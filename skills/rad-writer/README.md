# RAD Writer — Claude.ai Skill

Domain-smart writing, AI pattern avoidance, voice profiling, and editorial review across 9 content types — email, blog, web copy, business reports, research, presentations, prose, technical docs, social media.

> **Claude.ai-only distribution.** This is the standalone Claude.ai skill version. The matching Claude Code plugin was retired in marketplace v1.11.0 — its project-narrative use case is now covered by [rad-explain](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/tree/main/plugins/rad-explain) (`narrate-project`, `ground-readme`) for any repo, and [rad-planner](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/tree/main/plugins/rad-planner)'s `/project-story` for canonical-doc projects. This skill remains the multi-genre writing home for Claude.ai users.

## What's Included

Import `rad-writer.zip` via **Settings > Customize > Skills** on Claude.ai.

The skill includes a SKILL.md with 5 modes (write, improve, review, AI audit, voice analysis) plus 14 resource files:

- AI writing patterns framework — organized by **durability tier** (T1 durable structural, T2 degrading stylistic, T3 deprecated lexical) per the 2.0 honesty pass
- Wikipedia "Signs of AI Writing" relation note — anchors the framework to Wikipedia's [canonical 2025 reference](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Word blocklist (250+ lexical tells with replacement suggestions and severity)
- Sentence craft guide (burstiness, transitions, paragraph techniques)
- Voice profile schema (descriptive style guidance — see EMNLP 2025 caveats below)
- 9 domain guides: email, blog, web copy, business report, research/academic, presentation, prose/essay, technical docs, social media

## How to Import

**As a Skill (recommended):** Settings > Customize > Skills > upload `rad-writer.zip`. Activates automatically in any conversation.

**As Project Knowledge:** Add the `.md` files to a Claude.ai Project for project-scoped use.

**As a conversation attachment:** Attach `SKILL.md` to any conversation for one-off use.

## Example Prompts

- "Write me a cold outreach email to [person]"
- "Draft a blog post about [topic]"
- "Improve this — it sounds too robotic" [paste text]
- "Review this writing and tell me what to fix"
- "Does this sound like AI?" [paste text]
- "Analyze my writing voice" [paste 3-5 samples]
- "Create web copy for my landing page"
- "Write a LinkedIn post about [topic]"

## How It Works

- **9 writing domains**: Each with deep convention knowledge, anti-patterns, and domain-specific AI tells
- **AI avoidance baked in**: 250+ lexical tells tracked, burstiness scoring, structural analysis — avoidance is structural during generation, not cosmetic post-processing
- **Voice profiles**: Provide 3-5 writing samples → get a downloadable voice profile artifact. Upload to a Project for persistent voice matching, or attach to any conversation.
- **Three-pass review**: Structure & flow → sentence & word craft → AI pattern scan. Deduplicated, severity-ranked findings.
- **Tracked changes**: Every improvement is numbered. Accept all, review individually, or cherry-pick by number.
- **Not an AI detector**: The AI audit reports patterns with fixes, not verdicts. Every "AI tell" is also a craft problem — fix the writing quality, detectability solves itself.

## Honesty Statement

Read these before expecting capabilities this skill cannot honestly deliver:

- **No AI detection.** Perfect detection is mathematically impossible at high confidence as of 2026 ([arXiv:2509.11915](https://arxiv.org/html/2509.11915v1)). The AI audit reports patterns, not verdicts.
- **No detector evasion guarantees.** Mainstream detectors are inconsistent and biased — Stanford HAI found 61.3% false-positive rates against non-native English writers. The skill improves writing craft; the side effect of fewer AI tells is genuine but not guaranteed against any specific tool.
- **Voice profiles are partial.** EMNLP 2025 Findings paper showed structured-genre voice mimicry (emails, news, business reports) reaches 95-97% accuracy. Informal-genre mimicry (blogs, social, personal essays) sits at 19-21%. Profiles are descriptive style guidance, not deterministic mimicry.
- **Lexical tells are degrading signals.** "Delve," "tapestry," "foster" and the 2023-24 word list have partially deprecated as model providers patched them. They remain worth replacing for style reasons (most are clichés), but their AI-tell status is a lagging signal. See `resources/ai-writing-patterns.md` for the durability-tier framing (T1 durable structural / T2 degrading stylistic / T3 deprecated lexical).

## What this skill is and isn't

| Capability | Available |
|---|---|
| Domain-aware drafting (9 domains) | ✓ |
| AI pattern audit organized by durability tier | ✓ |
| Voice profile generation (artifact download) | ✓ |
| Three-pass review | ✓ |
| Deterministic burstiness / em-dash / blocklist scan | Ask Claude to count on pasted text — no Python validators in the Claude.ai sandbox |
| Long-document chunked processing | Manual sectioning |
| Operates on filesystem | ✗ (paste / artifact only — Claude.ai sandbox has no filesystem) |

For engineer-writing in a Claude Code session (READMEs, changelogs, ADRs, commits) with grounding and overpromise checks, use [`rad-explain`](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/tree/main/plugins/rad-explain) — its `ground-readme` skill audits or generates README-style copy against the repo source.

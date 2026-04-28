# RAD Brainstormer — Claude.ai Skill

Collaborative ideation using proven methodologies (SCAMPER, Six Hats, Reverse Brainstorming, Five Whys, and more), structured evaluation, creative unblocking, and design sprint. Adapted from the [rad-brainstormer plugin](../../plugins/rad-brainstormer/) for Claude.ai.

## What's Included

Import `rad-brainstormer.zip` via **Settings > Customize > Skills** on Claude.ai.

The skill includes a SKILL.md orchestrator covering 3 workflows (ideation, evaluation, design sprint) plus 5 resource files:

- Methodology catalog (20 ideation and evaluation techniques: SCAMPER, Six Hats, Reverse Brainstorming, Starbursting, HMW, TRIZ, Morphological Analysis, Crazy 8s, 5 Whys, Random Entry, Brainwriting 6-3-5, Mind Mapping, Analogical Thinking, Worst Possible Idea, Impact/Effort Matrix, Assumption Mapping, Opportunity Solution Trees, JTBD, Dot Voting, Pre-Mortem)
- Evaluation frameworks (7 frameworks: Impact/Effort, Assumption Mapping, Opportunity Solution Trees, JTBD, Pre-Mortem, Dot Voting, SWOT)
- Facilitation principles (anti-anchoring, phase discipline, energy management)
- Creative unblocking (8 warm-up exercises, block diagnosis, progressive engagement)
- Domain research guide (web research methodology for unfamiliar topics)

## How to Import

**As a Skill (recommended):** Settings > Customize > Skills > upload `rad-brainstormer.zip`. Activates automatically in any conversation.

**As Project Knowledge:** Add the `.md` files to a Claude.ai Project for project-scoped use.

**As a conversation attachment:** Attach `SKILL.md` to any conversation for one-off use.

## Example Prompts

- "Let's brainstorm ideas for [topic]"
- "Research [topic] before we brainstorm" — domain-research mode
- "I'm stuck and don't know where to start"
- "Help me think through [problem]"
- "Evaluate these ideas and help me pick the best one"
- "Run a pre-mortem on this idea" — idea-stress-test
- "Stress-test this idea — what could go wrong?"
- "Design this feature for me"
- "Create a spec for [idea]"
- "Review this spec for completeness"

## How It Works

- **Anti-anchoring**: Draws out YOUR ideas first before offering its own
- **Phase discipline**: Never mixes generating ideas with evaluating them
- **One question at a time**: Prevents cognitive overload
- **Domain-aware**: Can research unfamiliar domains via web search before brainstorming
- **Adaptive**: Detects when you're stuck and switches techniques
- **Artifacts**: Produces idea boards, comparison tables, evaluation matrices, and design specs as downloadable artifacts
- **Sequential flow**: After ideation → offers evaluation → offers design sprint

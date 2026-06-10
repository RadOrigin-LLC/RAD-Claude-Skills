# rad-context-prompter — Write, debug, and optimize prompts, loops, and goals. No guessing.

Different AI models need different prompting strategies — what works for Claude degrades output on o3, and vice versa. rad-context-prompter maps your task type to the right technique for the right model, diagnoses why a prompt is failing with a coded taxonomy, reverse-engineers existing prompts to translate them across platforms, and authors the artifacts that drive autonomous agent runs: loop prompts and goal/completion conditions for Claude Code (`/goal`, `/loop`, Stop hooks) and OpenAI Codex (Goal Mode, AGENTS.md).

## Features

- **Systematic tool-specific routing** across the full platform catalog in `references/tool-routing.md`: chat models (Claude, GPT, Gemini, Qwen, Llama/Mistral, DeepSeek), reasoning models (o3/o4-mini, R1, Qwen3-thinking), agentic tools (Claude Code, OpenAI Codex, Antigravity, Cursor/Windsurf, Copilot, Devin), full-stack generators (Bolt, v0, Lovable), image/video/voice/3D AI (Midjourney, DALL-E, Stable Diffusion, ComfyUI, Sora, Runway, ElevenLabs, Meshy), research/browser agents, and workflow automation (Zapier, Make, n8n)
- **Loop & goal engineering** — author loop prompts (Ralph-style, one-task-per-iteration, file-based state), goal conditions (`/goal`, Codex Goal Mode, Stop hooks), and the four-file long-horizon scaffold, with every goal spec checked against the documented reward-hacking exploit signatures (G1-G7: unprotected tests, grep-only success, existence-only checks, and so on)
- **Two pure-stdlib validators**: `lint-prompt.py` (structural prompt issues) and `check-goal.py` (goal anatomy, gameability signatures G1-G7, loop discipline — G8 revert-satisfiability needs semantic judgment and stays with the skill) — wired into the skills and the debugger agent, mechanism before LLM judgment
- **44-pattern diagnostic taxonomy** (F1-F8) covering task, context, format, scope, reasoning, agentic, platform, and loop/goal failures
- **12 technique selection matrix** mapping task types to optimal prompt engineering techniques
- **Hard rules** preventing token waste (e.g., CoT on reasoning-native models degrades output)
- **Prompt decompiler** for reverse-engineering existing prompts — structural analysis, technique identification, cross-platform translation, compression

## Components

| Type | Name | Purpose |
|------|------|---------|
| Skill | `prompt-engineering` | Core prompt writing, system prompt design, technique selection, tool routing |
| Skill | `prompt-decompiler` | Reverse-engineer, analyze, translate, compress, and split existing prompts |
| Skill | `loop-goal-engineering` | Author loop prompts, goal conditions, and long-horizon scaffolds for Claude Code and Codex |
| Agent | `prompt-debugger` | Diagnose why a prompt failed and suggest minimal targeted fixes |
| Script | `scripts/lint-prompt.py` | Mechanical detection of structural prompt issues |
| Script | `scripts/check-goal.py` | Mechanical validation of goal conditions and loop prompts |

## Skills

### prompt-engineering

The core skill. Triggers on: "write a prompt", "prompt engineering", "system prompt", "optimize my prompt", "CLAUDE.md", "few-shot examples", "context engineering".

Two modes:
- **Fast mode**: Clear task + known tool → immediate prompt output
- **Design mode**: System prompts, agentic architectures, production pipelines → consultative workflow

Includes 6 reference files: techniques (12 sections), patterns (35 anti-patterns + 12 structural patterns), templates (13 templates A-M), tool routing (the full platform catalog), context engineering, and evaluation checklist.

### prompt-decompiler

Advanced prompt reverse-engineering. Triggers on: "decompile this prompt", "analyze this prompt", "adapt this prompt for", "why does this prompt work", "convert this prompt".

Six analysis modes:
- **Anatomize**: Structural fingerprint + component map + technique identification + weakness map
- **Translate**: Cross-platform adaptation with translation notes
- **Compress**: Token audit and optimization with before/after diff
- **Decompose**: Split complex prompts into sequential chains
- **Forensics**: Technique-by-technique effectiveness analysis with scoring
- **Diagnose**: Weakness identification (also see prompt-debugger agent for deep analysis)

### loop-goal-engineering

Author the artifacts that drive autonomous runs. Triggers on: "write a loop prompt", "set up a ralph loop", "run Claude overnight", "write a /goal condition", "goal mode", "stop condition", "completion criteria", "my agent never finishes".

Deliverable types:
- **Loop prompts** — re-run cold each iteration: one task per pass, state in files/git, search-before-assuming, no placeholders, in-iteration verification, idempotent start, bounded
- **Goal conditions** — for Claude Code `/goal` (evidence must appear in the transcript — the evaluator runs no commands), Codex Goal Mode (Goal/Context/Constraints/Done-when), and Stop-hook scripts
- **Four-file long-horizon scaffold** — spec / plan / runbook / status log, the structure both Ralph and OpenAI's long-horizon guide converged on
- Every draft is linted by `check-goal.py` before delivery: goal anatomy (named command, scope guard, bound, evidence display), gameability signatures G1-G7 (unprotected tests, grep-only success, existence-only checks, absence-only checks, self-judged completion, skip-counting, effort-based success), and loop discipline; G8 (revert-satisfiability) is checked by judgment in the skill

Grounded in: Anthropic's `/goal` docs and harness-design posts, OpenAI's Codex Goal Mode docs and long-horizon guide, Huntley's Ralph loop, Willison's "Designing agentic loops", and the 2026 reward-hacking literature.

## Agent

### prompt-debugger

Autonomous prompt failure analyst. Triggers on: "my prompt isn't working", "debug this prompt", "getting hallucinations", "model keeps ignoring my instructions", "my agent never finishes", "my loop keeps redoing work".

Diagnostic framework:
- **Mechanical pre-pass**: runs `lint-prompt.py` (and `check-goal.py` for loop/goal prompts) before LLM judgment
- **8-category failure taxonomy** (F1-F8) with 44 specific failure patterns — F8 covers loop & goal failures (vague end states, gameable criteria, evaluator-invisible conditions, non-idempotent loops, self-judged completion)
- **Root cause analysis** tracing symptom → mechanism → fix
- **Targeted fixes** with BEFORE/AFTER/WHY format
- **Verification step** checking Golden Rule, intent preservation, platform compatibility

## Installation

```bash
claude plugins add ./RAD-Claude-Skills/plugins/rad-context-prompter
```

## License

Apache-2.0

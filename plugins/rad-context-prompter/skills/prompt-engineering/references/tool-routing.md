# Tool Routing — Model and Platform-Specific Guidance

Extracted from the main skill file. Use this reference when writing prompts for a
specific tool or platform. Each section covers syntax, behavioral notes, and
optimization tips for that target.

---

### Claude (claude.ai, Claude API, Claude 4.x and newer)

- Be explicit and specific — Claude follows instructions literally, not by inference
- XML tags for complex multi-section prompts: `<context>`, `<task>`, `<constraints>`, `<output_format>`
- Provide context and reasoning WHY, not just WHAT — Claude generalizes better from explanations
- Always specify output format and length explicitly
- Use `references/context-engineering.md` for system prompt design, tool descriptions, and agentic architectures

**Current-generation specifics (Claude 4.5 and newer):**
- More concise by default. Don't add "be concise" — it's the baseline. Ask explicitly for thorough output when needed.
- Responsive to system prompts. Dial back aggressive language. Replace "CRITICAL: You MUST use this tool" with "Use this tool when..."
- Adaptive thinking: use `thinking: {type: "adaptive"}` with effort levels (low/medium/high/max). Outperforms manual extended thinking.
- Prefilled responses deprecated. Don't prefill the last assistant turn. Use system prompt instructions, Structured Outputs, or move continuation context to user messages.
- Parallel tool calling. Add a `<use_parallel_tool_calls>` block to boost to near 100% parallel execution.
- Less over-prompting needed. Remove legacy guardrails from older model prompts. Claude 4.6 follows instructions more precisely — over-specification causes rigidity.
- Opus 4.x over-engineers by default — add "Only make changes directly requested. Do not add features or refactor beyond what was asked."
- Agent Teams (Claude Code — experimental). For complex coding tasks spanning independent domains, Claude Code supports orchestrated agent teams. Best for cross-layer work, parallel debugging, or new modules where teammates won't step on each other. Token cost is significantly higher than single session. See `references/context-engineering.md §5` for architecture guidance.

**Claude 3.5 Sonnet / Haiku:**
- May need explicit "be concise" or "skip the preamble" instructions
- Prefilled responses still work (put partial text in assistant turn)
- Extended thinking via manual `budget_tokens`
- May need stronger tool-triggering language

---

### ChatGPT / GPT-5.x / OpenAI GPT models
- Start with the smallest prompt that achieves the goal — add structure only when needed
- Be explicit about the output contract: what format, what length, what "done" looks like
- State tool-use expectations explicitly if the model has access to tools
- Use compact structured outputs — GPT-5.x handles dense instruction well
- Constrain verbosity when needed: "Respond in under 150 words. No preamble. No caveats."
- GPT-5.x is strong at long-context synthesis and tone adherence — leverage these

### o3 / o4-mini / OpenAI reasoning models
- SHORT clean instructions ONLY — these models reason across thousands of internal tokens
- NEVER add CoT, "think step by step", or reasoning scaffolding — it actively degrades output
- Prefer zero-shot first — add few-shot only if strictly needed and tightly aligned
- State the goal and what done looks like. Nothing more.
- Keep system prompts under 200 words

### Gemini 2.x / Gemini 3 Pro
- Strong at long-context and multimodal — leverage its large context window for document-heavy prompts
- Prone to hallucinated citations — always add "Cite only sources you are certain of. If uncertain, say [uncertain]."
- Can drift from strict output formats — use explicit format locks with a labelled example
- For grounded tasks add "Base your response only on the provided context. Do not extrapolate."

### Qwen 2.5 (instruct variants)
- Excellent instruction following, JSON output, structured data — leverage these strengths
- Provide a clear system prompt defining the role — Qwen2.5 responds well to role context
- Works well with explicit output format specs including JSON schemas
- Shorter focused prompts outperform long complex ones — scope tightly

### Qwen3 (thinking mode)
- Two modes: thinking mode (/think or enable_thinking=True) and non-thinking mode
- Thinking mode: treat exactly like o3 — short clean instructions, no CoT, no scaffolding
- Non-thinking mode: treat like Qwen2.5 instruct — full structure, explicit format, role assignment

### Ollama (local model deployment)
- ALWAYS ask which model is running before writing — Llama3, Mistral, Qwen2.5, CodeLlama all behave differently
- System prompt is the most impactful lever — include it in the output so the user can set it in their Modelfile
- Shorter simpler prompts outperform complex ones — local models lose coherence with deep nesting
- Temperature 0.1 for coding/deterministic tasks, 0.7-0.8 for creative tasks
- For coding: CodeLlama or Qwen2.5-Coder, not general Llama

### Llama / Mistral / open-weight LLMs
- Shorter prompts work better — these models lose coherence with deeply nested instructions
- Simple flat structure — avoid heavy nesting or multi-level hierarchies
- Be more explicit than with Claude or GPT — instruction following is weaker
- Always include a role in the system prompt

### DeepSeek-R1
- Reasoning-native like o3 — do NOT add CoT instructions
- Short clean instructions only — state the goal and desired output format
- Outputs reasoning in `<think>` tags by default — add "Output only the final answer, no reasoning." if needed

### Claude Code
- Agentic — runs tools, edits files, executes commands autonomously
- Starting state + target state + allowed actions + forbidden actions + stop conditions + checkpoints
- Stop conditions are MANDATORY — runaway loops are the biggest credit killer. Route them to the official
  ladder (weakest → strongest): in-prompt "run the check and iterate" → `/goal` condition (separate
  evaluator re-checks after every turn) → Stop hook (deterministic script gate; harness overrides after
  8 consecutive blocks) → verification subagent (fresh model tries to refute the result)
- `/goal` conditions: one measurable end state + a stated proof command + constraints + a turn bound.
  The evaluator runs no commands itself — instruct the agent to SHOW evidence (command output) in its
  response. For authoring these, use the **loop-goal-engineering** skill
- `/loop` re-runs a prompt on an interval or self-paced — loop prompts must be idempotent, one task per
  iteration, state in files/git (see loop-goal-engineering skill)
- Have Claude show evidence rather than asserting success
- Opus over-engineers — add "Only make changes directly requested. Do not add extra files, abstractions, or features."
- Always scope to specific files and directories — never give a global instruction without a path anchor
- Human review triggers required: "Stop and ask before deleting any file, adding any dependency, or affecting the database schema"
- For complex tasks: split into sequential prompts. Output Prompt 1 and add "Run this first, then ask for Prompt 2" below it
- Durable layering: CLAUDE.md = always-loaded quick-reference; skills = on-demand workflows (commands are
  converging into skills via `disable-model-invocation: true`); hooks = deterministic, zero-exception actions.
  "If Claude already does something correctly without the instruction, delete it or convert it to a hook."
- See `references/context-engineering.md` for sub-agent architecture, compaction vs resets, and multi-context-window workflows

### OpenAI Codex (CLI, IDE, cloud)
- Official prompt skeleton — four elements: **Goal, Context, Constraints, "Done when"** (success criteria)
- AGENTS.md is the durable layer (the CLAUDE.md equivalent): build/test commands, style rules, repo
  etiquette. Hard mechanics: ~32 KiB default cap (`project_doc_max_bytes`), one file per directory,
  root-to-cwd concatenation, nested files override parents. Don't stuff durable rules into one-off
  prompts — OpenAI names this the #1 common mistake
- `config.toml` (~/.codex/ and .codex/) is a separate control surface: approval mode, sandbox, model.
  Start conservative, loosen per trusted repo
- Goal Mode (`/goal`): outcome + TESTABLE success criteria; runs a plan-act-test loop autonomously.
  Canonical stop idioms: "until the test suite is green", "until grep returns zero matches". Vague
  goals are the documented failure mode (early surrender or endless flailing). Author conditions with
  the **loop-goal-engineering** skill
- Plan Mode (`/plan`) before coding on complex/ambiguous tasks — but never end a turn with only a plan:
  "the deliverable is working code"
- Show Codex how to run builds/tests or it can't self-verify
- Long-horizon runs: use the PLANS.md / four-file scaffold (spec, plan, runbook, status log) with
  per-milestone acceptance criteria and a stop-and-fix rule
- Skills (SKILL.md) ≈ Claude Code skills; one thread per TASK, not per project (context bloat)
- Scope discipline is explicit in OpenAI guidance: "Implement EXACTLY and ONLY what the user requests"

### Antigravity (Google's agent-first IDE, powered by Gemini 3 Pro)
- Task-based prompting — describe outcomes, not steps
- Prompt for an Artifact (task list, implementation plan) before execution for review
- Browser automation is built-in — include verification steps
- Specify autonomy level: "Ask before running destructive terminal commands"
- Do NOT mix unrelated tasks — scope to one deliverable per session

### Cursor / Windsurf
- File path + function name + current behavior + desired change + do-not-touch list + language and version
- Never give a global instruction without a file anchor
- "Done when:" is required — defines when the agent stops editing
- For complex tasks: split into sequential prompts

### GitHub Copilot
- Write the exact function signature, docstring, or comment immediately before invoking
- Describe input types, return type, edge cases, and what the function must NOT do
- Copilot completes what it predicts, not what is intended — leave no ambiguity

### Bolt / v0 / Lovable / Figma Make / Google Stitch
- Full-stack generators default to bloated boilerplate — scope it down explicitly
- Always specify: stack, version, what NOT to scaffold, clear component boundaries
- Add "Do not add authentication, dark mode, or features not explicitly listed" to prevent feature bloat

### Devin / SWE-agent
- Fully autonomous — very explicit starting state + target state required
- Forbidden actions list is critical — Devin will make decisions not intended
- Scope the filesystem: "Only work within /src. Do not touch infrastructure, config, or CI files."

### Research / Orchestration AI (Perplexity, Manus AI)
- Specify search vs analyze vs compare. Add citation requirements.
- Multi-agent orchestrators — describe the end deliverable, not the steps
- For long multi-step tasks: add verification checkpoints since each chained step compounds hallucination risk

### Computer-Use / Browser Agents (Perplexity Comet/Computer, OpenAI Atlas, Claude in Chrome, OpenClaw Agents)
- Describe the outcome, not the navigation steps
- Specify constraints explicitly — the agent will make its own decisions without them
- Add permission boundaries: "Do not make any purchase. Research only."
- Add a stop condition for irreversible actions

### Image AI — Generation (Midjourney, DALL-E 3, Stable Diffusion, SeeDream)
First detect: generation from scratch or editing an existing image?
- **Midjourney**: Comma-separated descriptors, not prose. Subject first, then style, mood, lighting, composition. Parameters at end: `--ar 16:9 --v 6 --style raw`. Negative prompts via `--no [unwanted elements]`
- **DALL-E 3**: Prose description works. Add "do not include text in the image unless specified." Describe foreground, midground, background separately for complex compositions.
- **Stable Diffusion**: `(word:weight)` syntax. CFG 7-12. Negative prompt is MANDATORY. Steps 20-30 for drafts, 40-50 for finals.
- **SeeDream**: Strong at artistic and stylized generation. Specify art style explicitly before scene content. Negative prompt recommended.

### Image AI — Reference Editing
Detect when: user mentions "change", "edit", "modify" an existing image, or uploads a reference. Build the prompt around the delta ONLY — what changes, what stays the same. Read `references/templates.md` Template J.

### ComfyUI
Node-based workflow — not a single prompt box. Ask which checkpoint model is loaded before writing. Always output two separate blocks: Positive Prompt and Negative Prompt. Read `references/templates.md` Template K.

### 3D AI — Text to 3D/Game Systems (Meshy, Tripo, Rodin)
- Describe: style keyword + subject + key features + primary material + texture detail + technical spec
- Negative prompt supported: "no background, no base, no floating parts"
- Specify intended export use: game engine (GLB/FBX), 3D printing (STL), web (GLB)

### 3D AI — In-Engine AI (Unity AI, Blender AI tools)
- Unity AI: use /ask for documentation, /run for Editor automation, /code for C# generation
- BlenderGPT: generates Python scripts for Blender. Be specific about geometry, materials, and scene context.

### Video AI (Sora, Runway, Kling, LTX Video, Dream Machine)
- Sora: describe as if directing a film shot. Camera movement is critical.
- Runway Gen-3: responds to cinematic language — reference film styles.
- Kling: strong at realistic human motion — describe body movement explicitly.
- LTX Video: fast generation, prompt-sensitive — keep descriptions concise.
- Dream Machine (Luma): cinematic quality — reference lighting setups and lens types.

### Voice AI (ElevenLabs)
- Specify emotion, pacing, emphasis markers, and speech rate directly
- Use SSML-like markers for emphasis: indicate which words to stress, where to pause

### Workflow AI (Zapier, Make, n8n)
- Trigger app + trigger event → action app + action + field mapping. Step by step.
- Auth requirements noted explicitly — "assumes [app] is already connected"
- For multi-step workflows: number each step and specify what data passes between steps

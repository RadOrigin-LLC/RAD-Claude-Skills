---
name: prompt-engineering
description: >
  This skill should be used when the user says "write a prompt", "prompt engineering",
  "system prompt", "optimize my prompt", "create instructions for", "context engineering",
  "CLAUDE.md", "few-shot examples", "write me a Midjourney prompt", "create a GPT prompt",
  "prompt for Claude Code", "agentic prompt", "tool description", or needs to create,
  improve, or optimize prompts for any AI platform. Covers prompt writing, system prompts,
  tool descriptions, agentic workflows, prompt chaining, and cross-model migration.
  Use for any prompt-related task, even simple ones.
---

# Context Prompt Master

Act as a prompt engineer. Take the user's rough idea, identify the target AI
tool, extract the actual intent, and output a single production-ready prompt —
optimized for that specific tool, with zero wasted tokens.

Operate in two modes depending on task complexity. Both modes terminate in the
same deliverable: a paste-ready prompt block.

---

## Mode Selection

**Fast mode** (default): The user has a clear task, a known target tool, and needs
a prompt built. Run Intent Extraction → Tool Routing → Diagnostic Check → Output.

**Design mode**: The task involves designing system prompts, CLAUDE.md files, skill
instructions, production prompt systems, agentic architectures, multi-step pipelines,
or evaluating/improving underperforming prompts. Run the full consultative workflow:
Understand → Design → Draft → Review → Iterate. Read reference files as needed.

Detect which mode from context. If the user says "write me a Midjourney prompt for X,"
that's fast mode. If they say "help me design the system prompt for my customer
support agent," that's design mode. When ambiguous, start fast and escalate if the
task proves complex.

**Hand-off**: if the deliverable is an agentic LOOP prompt (re-run each iteration),
a GOAL/completion condition (`/goal`, Codex Goal Mode, Stop hook), or a long-horizon
scaffold, use the **loop-goal-engineering** skill instead — those artifacts have their
own anatomy and linter.

---

## Hard Rules — NEVER Violate

- NEVER output a prompt without first confirming the target tool — ask if ambiguous.
  **Default: when the user requests a prompt without specifying a target tool or model,
  default to Claude style** (XML tag structure, explicit instructions, positive framing,
  format specification). Claude-optimized prompts transfer well to other models because
  the structural patterns (clear instructions, separated sections, examples) are
  universally effective. If the user later specifies a different tool, adapt accordingly.
- NEVER embed techniques that cause fabrication in single-prompt execution:
  - **Mixture of Experts** — model role-plays personas from one forward pass, no real routing
  - **Tree of Thought** — model generates linear text and simulates branching, no real parallelism
  - **Graph of Thought** — requires an external graph engine, single-prompt = fabrication
  - **Universal Self-Consistency** — requires independent sampling, later paths contaminate earlier ones
  - **Prompt chaining as a layered technique** — pushes models into fabrication on longer chains
- NEVER add Chain of Thought to reasoning-native models (o3, o4-mini, DeepSeek-R1, Qwen3 thinking mode) — they think internally, CoT degrades output
- NEVER ask more than 3 clarifying questions before producing a prompt
- NEVER pad output with explanations the user did not request

---

## Output Format — ALWAYS Follow This

The output is ALWAYS:
1. A single copyable prompt block ready to paste into the target tool
2. Target: [tool name], [One sentence — what was optimized and why]
3. If the prompt needs setup steps before pasting, add a short plain-English instruction note below. 1-2 lines max. ONLY when genuinely needed.

For copywriting and content prompts include fillable placeholders where relevant
ONLY: [TONE], [AUDIENCE], [BRAND VOICE], [PRODUCT NAME].

---

## Core Principles

Apply these to every prompt regardless of mode or target tool.

**The Golden Rule**: Show the prompt to a colleague with no other context. If they'd
be confused about what to do, the AI will be too.

**Be clear and direct.** Lead with the task. Specify output format, length, and
constraints explicitly. Don't rely on the model inferring intent from vague descriptions.

**Explain WHY, not just WHAT.** Models generalize from reasoning. "Never use
ellipses because a TTS engine will read the output aloud" is more robust than
"NEVER use ellipses" — the model can apply the principle to other TTS-unfriendly patterns.

**Tell it what TO DO, not what NOT to do.** Instead of "Don't use markdown,"
say "Write in flowing prose paragraphs." Positive instructions produce better results.

**Start complete, then simplify.** Include all relevant elements (role, instructions,
context, examples, output format). Remove only what testing proves unnecessary.

**Prompt style shapes output style.** A terse, structured prompt produces terse,
structured output. A conversational prompt produces conversational output. Match the
prompt's voice to the desired output.

---

## Intent Extraction

Before writing any prompt, silently extract these 9 dimensions. Missing critical
dimensions trigger clarifying questions (max 3 total).

| Dimension | What to extract | Critical? |
|-----------|----------------|-----------|
| **Task** | Specific action — convert vague verbs to precise operations | Always |
| **Target tool** | Which AI system receives this prompt (defaults to Claude if unspecified) | Always |
| **Output format** | Shape, length, structure, filetype of the result | Always |
| **Constraints** | What MUST and MUST NOT happen, scope boundaries | If complex |
| **Input** | What the user is providing alongside the prompt | If applicable |
| **Context** | Domain, project state, prior decisions from this session | If session has history |
| **Audience** | Who reads the output, their technical level | If user-facing |
| **Success criteria** | How to know the prompt worked — binary where possible | If task is complex |
| **Examples** | Desired input/output pairs for pattern lock | If format-critical |

---

## Tool Routing

Identify the target tool and apply its platform-specific syntax, behavioral notes,
and optimization patterns. Read `references/tool-routing.md` for the specific
platform being targeted. Key platform categories covered:

- **LLM chat models:** Claude (3.5/4.x), ChatGPT/GPT-5.x, Gemini, Qwen, Llama/Mistral, DeepSeek
- **Reasoning models:** o3/o4-mini, Qwen3 thinking mode, DeepSeek-R1 (no CoT — they think internally)
- **Agentic/IDE tools:** Claude Code, Antigravity, Cursor/Windsurf, Copilot, Devin/SWE-agent
- **Full-stack generators:** Bolt, v0, Lovable, Figma Make, Google Stitch
- **Creative AI:** Midjourney, DALL-E 3, Stable Diffusion, SeeDream, ComfyUI, Sora, Runway, Kling, ElevenLabs
- **3D AI:** Meshy, Tripo, Rodin, Unity AI, BlenderGPT
- **Research/orchestration:** Perplexity, Manus AI, browser agents
- **Workflow automation:** Zapier, Make, n8n
- **Local deployment:** Ollama (ask which model before writing)

Also read `references/templates.md` for the needed template category and
`references/techniques.md` when selecting techniques for complex prompts.

---

## Diagnostic Checklist

Scan every user-provided prompt or rough idea for these failure patterns. Fix
silently — flag only if the fix changes the user's intent. See `references/patterns.md`
for the complete 35-pattern anti-pattern reference plus 12 structural patterns.

**Task failures**: vague task verb, two tasks in one prompt, no success criteria,
emotional description, scope is "the whole thing"

**Context failures**: assumes prior knowledge, invites hallucination, no mention of prior failures

**Format failures**: no output format specified, implicit length, no role assignment,
vague aesthetic

**Scope failures**: no file or function boundaries for IDE AI, no stop conditions for agents,
entire codebase pasted as context

**Reasoning failures**: logic task with no step-by-step, CoT added to reasoning-native model,
new prompt contradicts prior session decisions

**Agentic failures**: no starting state, no target state, silent agent, unrestricted
filesystem, no human review trigger

---

## Design Mode Workflow

When design mode is active, follow these phases. Adapt depth to the request.

### Phase 1: Understand
Clarify goal, target model, deployment context (interactive chat, API, Claude Code,
agentic loop, skill file), input shape, output shape, and constraints (latency, cost,
token budget, safety). If unspecified, ask — don't guess on ambiguous requirements.

### Phase 2: Design
Select techniques from `references/techniques.md` using the Technique Selection Guide
below. Combine multiple techniques when the task warrants it.

| Task Type | Primary Techniques | Reference |
|---|---|---|
| Classification / Labeling | Few-shot examples + XML output tags | techniques.md §4, §9 |
| Complex reasoning / Math | Chain of thought / adaptive thinking | techniques.md §5 |
| Long document analysis | Quote extraction + grounding | techniques.md §7 |
| Structured output (JSON/XML) | XML tags, Structured Outputs, or tool schema | techniques.md §9, §11 |
| Agentic workflows | Context engineering + tool design | context-engineering.md |
| Creative / Style-sensitive | Role prompting + temperature adjustment | techniques.md §2 |
| Factual / Research | Hallucination prevention + evidence-first | techniques.md §8 |
| Multi-step pipelines | Prompt chaining with intermediate inspection | techniques.md §10 |
| System prompt / CLAUDE.md | Context engineering + minimal high-signal tokens | context-engineering.md §2, §7 |
| Skill / instruction writing | Reasoning-based language + progressive disclosure | context-engineering.md |
| Evaluation / Grading | Explicit criteria + role prompting + structured output | techniques.md §2, §4, §9 |
| Complex problems with trade-offs | Recursive thinking (iterative self-refinement) | techniques.md §12, templates.md M |
| Multi-agent orchestration | Planner/Solver/Critic pattern + refinement budget | patterns.md Pattern 12 |

### Phase 3: Draft
Write the prompt using structural patterns from `references/patterns.md` and
templates from `references/templates.md`. Apply XML tags for clear section boundaries.
Put long context/documents at the top, query/instructions at the bottom.

### Phase 4: Review
Run the prompt through `references/evaluation-checklist.md` before delivering. Fix any
issues found. For production prompts, suggest test cases.

### Phase 5: Iterate
When improving an existing prompt: identify the specific failure mode, map it to a
technique, apply the minimum change that addresses it, and explain what changed and why.

---

## Memory Block

When the user's request references prior work, decisions, or session history — prepend
this block to the generated prompt. Place it in the first 30% of the prompt so it
survives attention decay in the target model.

```
## Context (carry forward)
- Stack and tool decisions established
- Architecture choices locked
- Constraints from prior turns
- What was tried and failed
```

---

## Safe Techniques — Apply Only When Genuinely Needed

**Role assignment** — for complex or specialized tasks, assign a specific expert identity.
- Weak: "You are a helpful assistant"
- Strong: "You are a senior backend engineer specializing in distributed systems who prioritizes correctness over cleverness"

**Few-shot examples** — when format is easier to show than describe, provide 2-5 examples.

**Grounding anchors** — for any factual or citation task:
"Use only information you are highly confident is accurate. If uncertain, write [uncertain] next to the claim."

**Chain of Thought** — for logic, math, and debugging on standard reasoning models ONLY
(Claude, GPT-5.x, Gemini, Qwen2.5, Llama). Never on o3/o4-mini/R1/Qwen3-thinking.

**Recursive thinking** — for complex problems with trade-offs, uncertainties, or multiple
interdependent steps where single-pass CoT isn't enough. Runs a decompose → draft →
self-critique → refine → converge loop per subproblem. Three template variants available
in `references/templates.md` Template M (full, medium, minimal). Same model restrictions
as Chain of Thought — never on reasoning-native models.

For the complete technique catalog with structural examples, read `references/techniques.md`.

---

## Verification — Before Delivering Any Prompt

1. Is the target tool correctly identified and the prompt formatted for its specific syntax?
2. Are the most critical constraints in the first 30% of the generated prompt?
3. Is emphasis calibrated to the target model? Current-generation models (Claude 4.5+,
   GPT-5.x) over-trigger on aggressive emphasis — reserve MUST/NEVER/CRITICAL for genuine
   hard rules (2-3 per prompt max) and use plain imperatives ("Use this tool when...") for
   everything else. Older/smaller models may still need the stronger signal words.
4. Has every fabricated technique been removed?
5. Has the token efficiency audit passed — every sentence load-bearing, no vague adjectives, format explicit, scope bounded?
6. Would this prompt produce the right output on the first attempt?

For system prompts, CLAUDE.md/AGENTS.md files, and other durable prompts, also run the
mechanical linter and fix critical/warning findings before delivering:

```bash
PY=$(command -v python3 || command -v python)
echo "<draft prompt>" | "$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/lint-prompt.py" - --json
```

It catches what eyeballing misses: missing role frame, vague instructions, unbounded
length adjectives, conflicting output formats, excessive MUST/ALWAYS/NEVER emphasis,
superhuman-role framing, and imperative collisions. Exit 1 means findings exist — that's
signal, not failure. Skip it for short one-shot prompts where the overhead isn't worth it.

**Success criteria**: The user pastes the prompt into their target tool. It works on
the first try. Zero re-prompts needed. That is the only metric.

---

## Reference Files

Read only when the task requires it. Load the specific file or section needed.

| File | Read When |
|------|-----------|
| `references/techniques.md` | Selecting or applying prompt engineering techniques (12 technique sections with examples, including recursive thinking) |
| `references/context-engineering.md` | Designing system prompts, tool descriptions, agentic architectures, CLAUDE.md files, or managing context windows |
| `references/patterns.md` | Fixing a bad prompt (35 anti-patterns), building from a structural skeleton (12 reusable patterns including multi-agent orchestration) |
| `references/templates.md` | A full template is needed for a specific tool category (13 templates, A through M, including recursive thinking variants) |
| `references/evaluation-checklist.md` | Reviewing prompt quality before delivery or designing production evaluation criteria |
| `references/tool-routing.md` | Writing prompts for a specific AI platform — model-specific syntax and behavioral notes for 30+ tools |

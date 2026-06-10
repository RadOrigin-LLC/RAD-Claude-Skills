---
name: prompt-decompiler
description: >
  This skill should be used when the user says "decompile this prompt", "reverse engineer
  this prompt", "analyze this prompt", "break down this prompt", "what does this prompt do",
  "adapt this prompt for", "simplify this prompt", "split this prompt", "migrate this prompt",
  "why does this prompt work", "explain this system prompt", "what techniques is this using",
  "convert this prompt from X to Y", "what framework is this prompt using", "optimize this
  prompt", "look at this prompt", or pastes an existing prompt and wants it analyzed,
  adapted, simplified, or understood. Covers prompt anatomy, technique identification,
  structural analysis, cross-platform migration, and weakness mapping.
---

# Prompt Decompiler

Act as a prompt reverse-engineer. When the user pastes an existing prompt, systematically
decompose it into its constituent parts, identify the techniques used, map weaknesses,
and produce actionable output — whether that's an explanation, adaptation, simplification,
or complete rewrite for a different platform.

---

## Mode Detection

Detect the user's intent from context and route to the appropriate analysis mode:

| User Intent | Mode | Output |
|---|---|---|
| "What does this prompt do?" / "break down" / "analyze" | **Anatomize** | Structural map with technique identification |
| "Adapt for [tool]" / "convert from X to Y" / "migrate" | **Translate** | Rewritten prompt for target platform |
| "Simplify" / "make it shorter" / "too long" | **Compress** | Tightened version with diff notes |
| "Split this up" / "too complex" / "break into steps" | **Decompose** | Sequential prompt chain |
| "Why does this work?" / "what makes this effective" | **Forensics** | Technique-by-technique effectiveness analysis |
| "What's wrong with this?" / "why isn't this working" | **Diagnose** | Weakness map with targeted fixes (also see the prompt-debugger agent for deep analysis) |

When ambiguous, default to **Anatomize** — it's the most generally useful starting point,
and the user can refine from there.

---

## Hard Rules

- NEVER modify the user's original prompt without showing the original alongside changes.
- NEVER guess the source platform — ask if not obvious from syntax.
- NEVER claim a prompt "doesn't work" without identifying the specific failure mechanism.
- NEVER strip techniques without explaining what would be lost.
- ALWAYS preserve the user's original intent when adapting or compressing.

---

## Anatomize Mode — Structural Decomposition

For any prompt the user pastes, extract and label these layers:

### Layer 1: Structural Fingerprint

Map the prompt's architecture against known patterns (read `references/decompiler-patterns.md`
for the full pattern library):

```
STRUCTURAL FINGERPRINT
├── Format: [XML-tagged / flat prose / JSON schema / mixed]
├── Pattern match: [RTF / CO-STAR / RISEN / CRISPE / ReAct / custom]
├── Section count: [N distinct sections]
├── Token estimate: [approximate token count]
├── Information flow: [linear / branching / recursive / chained]
└── Platform signals: [detected platform from syntax cues]
```

### Layer 2: Component Map

Identify each functional component:

| Component | Present? | Content Summary | Effectiveness |
|-----------|----------|----------------|---------------|
| **Identity/Role** | yes/no | What role is assigned | strong/weak/missing |
| **Task statement** | yes/no | Core instruction | clear/vague/compound |
| **Context** | yes/no | Background information | sufficient/excessive/missing |
| **Constraints** | yes/no | Boundaries and rules | tight/loose/contradictory |
| **Input handling** | yes/no | How input data is structured | separated/mixed/missing |
| **Output format** | yes/no | Expected response shape | explicit/implicit/missing |
| **Examples** | yes/no | Few-shot demonstrations | diverse/redundant/missing |
| **Safety/guardrails** | yes/no | Edge case handling | robust/minimal/missing |
| **Reasoning scaffold** | yes/no | CoT/thinking structure | appropriate/misapplied/missing |
| **Stop conditions** | yes/no | When to halt (agentic) | defined/missing/too-loose |

### Layer 3: Technique Identification

Identify every prompt engineering technique in use. For each, assess whether it's
correctly applied for the target platform:

```
TECHNIQUES DETECTED
1. [Technique name] — [correctly applied / misapplied / partially applied]
   Location: [where in the prompt]
   Assessment: [why it works or doesn't for this platform]

2. [Next technique...]
```

Cross-reference against the technique-platform compatibility matrix in
`references/decompiler-patterns.md` to flag mismatches (e.g., CoT on reasoning models,
heavy nesting on open-weight models).

### Layer 4: Weakness Map

Scan for anti-patterns from the 35-pattern reference. For each weakness found:

```
WEAKNESSES
⚠ [Anti-pattern name] (severity: critical/moderate/minor)
  Location: [specific section or line]
  Impact: [what goes wrong because of this]
  Fix: [specific, minimal change to resolve]
```

---

## Translate Mode — Cross-Platform Adaptation

When converting a prompt from one platform to another:

### Step 1: Source Analysis
Run Anatomize mode silently to understand structure and techniques.

### Step 2: Platform Delta
Identify what changes between source and target platforms. Read
`references/decompiler-patterns.md` for the platform translation matrix.

Key translation patterns:
- **Claude → GPT**: Remove XML tags if simple prompt, keep if complex. Replace
  adaptive thinking directives with explicit CoT. Add explicit verbosity constraints.
- **Claude → o3/o4-mini**: Strip all reasoning scaffolding. Shorten drastically.
  State goal and output format only. Remove examples unless format-critical.
- **GPT → Claude**: Add XML tag structure. Replace "system" framing with explicit
  instructions. Leverage Claude's literal instruction following.
- **Chat model → Cursor/Windsurf**: Add file paths, function names, scope boundaries,
  "Done when" criteria. Remove conversational framing.
- **Chat model → Claude Code**: Add starting state, target state, allowed/forbidden
  actions, stop conditions, checkpoints. Scope to specific directories.
- **Text → Midjourney**: Convert prose to comma-separated descriptors. Extract subject,
  style, mood, lighting, composition. Add parameters at end.
- **Any → Ollama**: Ask which model. Simplify structure. Shorten. Add system prompt
  as separate block for Modelfile.

### Step 3: Adapted Output

```
ORIGINAL ([source platform]):
[original prompt — shown for reference]

ADAPTED FOR [target platform]:
[rewritten prompt]

TRANSLATION NOTES:
- [Change 1]: [what changed and why]
- [Change 2]: [what changed and why]
- [Techniques preserved]: [list]
- [Techniques removed/replaced]: [list with reasoning]
- [Platform-specific additions]: [list]
```

---

## Compress Mode — Token Optimization

When the user wants a shorter/tighter version:

### Step 1: Token Audit
Categorize every sentence as:
- **Load-bearing**: Directly controls output quality. Keep.
- **Reinforcing**: Restates something already covered. Remove.
- **Defensive**: Prevents a failure mode. Keep if the failure mode is real, remove if hypothetical.
- **Decorative**: Adds no information. Remove.

### Step 2: Compression Techniques
Apply in order until target reduction is achieved:
1. **Remove redundancy** — instructions that say the same thing differently
2. **Merge constraints** — combine related rules into single statements
3. **Flatten nesting** — reduce XML depth where structure isn't earning its tokens
4. **Tighten language** — replace verbose phrases with precise ones
5. **Remove obvious defaults** — instructions the model already follows (e.g., "be helpful" for Claude 4.6)
6. **Extract to examples** — replace long descriptions with a single demonstration

### Step 3: Compressed Output

```
ORIGINAL: [N tokens]
COMPRESSED: [M tokens] (X% reduction)

[Compressed prompt]

WHAT WAS REMOVED AND WHY:
- [Removed element]: [reason — redundant/decorative/obvious default/etc.]
```

**Safety check**: After compression, verify the prompt still passes the Golden Rule
test — would a colleague with no context understand what to do?

---

## Decompose Mode — Prompt Splitting

When a prompt is doing too much for a single pass:

### Step 1: Task Inventory
List every distinct task the prompt is asking the model to do.

### Step 2: Dependency Graph
Map which tasks depend on outputs from other tasks.

### Step 3: Handle Dependencies

**Linear dependencies** (A → B → C): Chain sequentially. Each prompt's output feeds the next.

**Shared context** (multiple prompts need the same background): Extract shared context
into a **context preamble block** that gets prepended to every sub-prompt in the chain.
This prevents repeated context and keeps each prompt focused on its task.

**Circular dependencies** (A needs B's output, B needs A's output): Break the cycle by
extracting the shared state into a separate **context document** that both prompts read from
and write to. Run an initial estimation pass for one side, then iterate.

**Parallel tasks** (independent tasks with no data dependency): Mark as parallelizable —
these can run simultaneously rather than sequentially.

### Step 4: Chain Design
Split into sequential prompts, each handling one task:

```
This prompt is doing [N] things. Split into [N] sequential prompts:

[CONTEXT PREAMBLE — if shared context exists]:
[shared background that all prompts need]

PROMPT 1 — [task name]:
[prompt block]
→ Output feeds into: Prompt 2

PROMPT 2 — [task name]:
[prompt block]
→ Receives from Prompt 1: [specific data]
→ Output feeds into: Prompt 3

PROMPT 3 — [task name]:
[prompt block]
→ Receives from Prompt 2: [specific data]
→ Final output

[PARALLEL GROUP — if independent tasks exist]:
These prompts can run simultaneously:
- Prompt A: [task]
- Prompt B: [task]

Run sequential prompts in order. Inspect output at each step before proceeding.
```

---

## Forensics Mode — Why It Works

When the user wants to understand what makes an effective prompt effective:

### Analysis Framework

For each technique detected, explain:

1. **What it does**: The mechanism by which this technique improves output
2. **Why it works here**: Specific interaction with this prompt's task and target model
3. **What would break without it**: The failure mode that would emerge if removed
4. **Transferability**: Whether this technique would work in other contexts

### Effectiveness Scoring

Rate each component on a 1-5 scale:
- **5 — Optimal**: Couldn't improve this without trade-offs
- **4 — Strong**: Minor refinements possible
- **3 — Adequate**: Works but has room for improvement
- **2 — Weak**: Partially effective, clear fixes available
- **1 — Counterproductive**: Actively hurting output quality

### Output Format

```
FORENSICS REPORT: [prompt summary]

Overall effectiveness: [X/5]

TECHNIQUE ANALYSIS:
1. [Technique]: [score/5]
   Mechanism: [how it works]
   Value here: [why it matters for this specific prompt]
   Without it: [what would go wrong]

KEY STRENGTHS:
- [What this prompt does particularly well]

IMPROVEMENT OPPORTUNITIES:
- [What could be better, ordered by impact]
```

---

## Diagnose Mode — Quick Weakness Scan

When the user asks "what's wrong with this prompt" or similar diagnostic questions,
run a quick red-flag scan before deciding how deep to go.

### Quick Scan (always run first)
Check the prompt against the Decompilation Red Flags in `references/decompiler-patterns.md`
Part 5. Scan for critical red flags first, then moderate, then minor.

### Escalation Criteria
- **Handle inline** (within this skill): When 1-3 clear issues are found with obvious fixes,
  the prompt is short-to-medium length, and the user hasn't provided a bad output to analyze.
  Run the Anatomize weakness map (Layer 4) and provide fixes directly.
- **Escalate to prompt-debugger agent**: When the user provides a prompt-output pair showing
  unexpected behavior, when multiple interacting failure modes are suspected, when the prompt
  is for an agentic system with complex failure modes, or when root cause requires tracing
  through the failure taxonomy (F1-F8).

### Inline Diagnosis Output

```
QUICK DIAGNOSIS:

RED FLAGS FOUND:
⚠ [Critical] [issue description]
  Fix: [minimal change]

⚠ [Moderate] [issue description]
  Fix: [minimal change]

RECOMMENDATION: [handle here / escalate to prompt-debugger agent for deeper analysis]
```

---

## Reference Files

| File | Read When |
|------|-----------|
| `references/decompiler-patterns.md` | Identifying prompt patterns, platform translation rules, technique-platform compatibility matrix, decompilation red flags |

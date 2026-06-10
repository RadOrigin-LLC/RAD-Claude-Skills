# Context Engineering

Principles and patterns for managing Claude's context window effectively,
designing agentic systems, and authoring project-level instructions.
Sourced from Anthropic's engineering blog, Claude Code best practices,
and official documentation.

---

## §1 — Core Philosophy

**Context is finite working memory.** Every token in the context window depletes
a limited budget. The goal is not to fill the window — it's to include the
minimal set of high-signal tokens that maximize the quality of Claude's output.

Think of context like RAM, not a filing cabinet. You don't store everything
"just in case" — you load what's needed for the current task and unload it when done.

**Key principles:**
- Maximize signal-to-noise ratio in every token
- Prefer structured, dense information over verbose prose
- Remove redundant or obvious instructions
- Load context just-in-time rather than all-at-once when possible
- Design for compaction — what survives summarization?

---

## §2 — System Prompt Design

System prompts set the persistent context for every turn in a conversation.
They're the most expensive context (always present) so they must be high-signal.

**Find the right altitude.** Too specific and Claude becomes rigid. Too general
and Claude defaults to generic behavior. Aim for principles over prescriptions.

```
TOO SPECIFIC: "When the user asks about refunds, say: 'Our refund policy
allows returns within 30 days. Please provide your order number.'"

TOO GENERAL: "Be helpful with customer questions."

RIGHT ALTITUDE: "You handle customer support for an e-commerce store.
Be empathetic but concise. For refund requests, gather the order number
and reason before processing. Escalate to a human if the customer mentions
legal action or safety issues."
```

**Structure with clear sections:**
```xml
<role>Who Claude is and what it does</role>
<guidelines>How it should behave</guidelines>
<tools>What tools are available and when to use them</tools>
<constraints>Boundaries and safety considerations</constraints>
```

**Start minimal, then add.** Begin with the simplest system prompt that works.
Add instructions only when you observe specific failure modes. Each addition
should address a documented problem, not a hypothetical one.

**Test for robustness.** A good system prompt works across diverse inputs,
not just the examples you tested with. Probe with edge cases, adversarial
inputs, and off-topic requests.

---

## §3 — Tool Description Design

Tool descriptions are context too — they consume tokens on every turn where
tools are available. Design them for maximum information density.

**Minimize overlap.** If two tools have similar descriptions, Claude will
struggle to choose between them. Make boundaries explicit:
"Use `search_docs` for keyword search across all documents.
Use `get_document` when you already know the document ID."

**Make parameters self-documenting:**
- Use descriptive names (`search_query` not `q`)
- Include type, format, and valid ranges
- State what happens with optional parameters omitted
- Provide enum values when the set is finite

**Return token-efficient results.** Tool responses should contain what Claude
needs to continue — not raw database dumps or full API payloads. Summarize,
filter, or paginate large results.

**Curate ruthlessly.** Every tool in the context costs tokens. Only include
tools Claude actually needs for the current task. Remove unused tools.

---

## §4 — Context Retrieval Strategies

How you load information into context matters as much as what you load.

**Just-in-time retrieval:**
Maintain lightweight identifiers (file paths, document titles, API endpoints)
in the system prompt. Load full content only when Claude needs it via tools
or dynamic context injection.

```xml
<available_resources>
- Policy documents: Use search_policies(query) to find relevant policies
- Customer data: Use get_customer(id) to load customer records
- Product catalog: Use search_products(query) for product information
</available_resources>
```

**Hybrid approach:**
Combine upfront context (high-level overview, key facts) with on-demand
retrieval (details, specific documents). This gives Claude orientation
without burning tokens on content it may never need.

**Leverage metadata:**
File hierarchies, naming conventions, timestamps, and directory structures
often contain enough signal to guide retrieval without loading content.
For code: file paths, function signatures, and import statements are
high-value, low-token context.

---

## §5 — Long-Horizon / Agentic Patterns

For tasks spanning many turns or requiring autonomous decision-making.

### Compaction

When conversations approach context limits, summarize while preserving:
- Critical decisions already made
- Unresolved issues and open questions
- Key facts discovered during the session
- Current task state and remaining work

**Hierarchy of compaction interventions:**
1. Clear tool result contents (lightest — just the raw data, keep summaries)
2. Summarize older conversation turns
3. Extract key decisions/facts into structured notes
4. Start a fresh context window with state loaded from files

**Resets over compaction for long-horizon work (current guidance).** Anthropic's
harness-design guidance (Mar 2026) now favors option 4 — a clean **context reset
with a handoff artifact** — over in-context summarization for long-running
agents: "A reset provides a clean slate, at the cost of the handoff artifact
having enough state for the next agent to pick up the work cleanly." Related
named failure: **context anxiety** — models prematurely wrap up work as they
approach perceived context limits. Design the handoff artifact (plan file +
status log + git history) so a cold start loses nothing.

### Structured Note-Taking (Agentic Memory)

Have agents write notes persisted outside the context window. Reintroduce
them when relevant.

```xml
<memory_instructions>
After completing each major task, write a brief summary to the todo/memory
file capturing: what was done, key decisions made, any issues encountered,
and what remains. This information will be reloaded if context is compacted.
</memory_instructions>
```

### Sub-Agent Architectures

Delegate focused tasks to specialized sub-agents with clean context.
Sub-agents condense extensive exploration into brief summaries.

**When to use sub-agents:**
- Tasks that can run in parallel
- Tasks requiring isolated context (long document analysis)
- Independent workstreams that don't need shared state
- Research tasks that would pollute the main context

**When NOT to use sub-agents:**
- Simple tasks (overhead exceeds benefit)
- Tasks requiring tight coordination with main context
- When the main agent can do it in 1-2 tool calls

**For structured multi-agent workflows** (Planner/Solver/Critic pattern with
orchestration logic and refinement budgets), see `patterns.md` Pattern 12.
That pattern provides ready-to-use system prompts for each agent role and
works with Claude Code agent teams, n8n, LangGraph, CrewAI, or custom code.

### State Management

Choose the right state format for the task:

| Format | Use For |
|---|---|
| **JSON** | Structured state: test results, task status, configurations |
| **Freeform text** | Progress notes, reasoning logs, decision records |
| **Git** | Code state tracking, checkpoints, rollback capability |
| **Files on disk** | Persistent state across context windows |

### Multi-Context-Window Workflows

For tasks too large for a single context window:

1. **First window:** Set up framework — write tests, create setup scripts,
   establish conventions
2. **Write artifacts to disk:** Tests in structured format (e.g., `tests.json`),
   setup scripts (`init.sh`) to prevent repeated work
3. **Fresh start:** Reading from filesystem is often better than compaction —
   Claude gets clean context with only relevant state
4. **Verification tools:** Use automated tests, linters, or preview tools
   for autonomous correctness checking
5. **Encourage full usage:** "Continue working systematically until you have
   completed this task" prevents premature stopping

### Completion Gating (stop-condition ladder)

"Claude stops when the work looks done. Without a check it can run, 'looks
done' is the only signal available, and you become the verification loop."
Official options, weakest to strongest:

1. **In one prompt** — ask Claude to run the check and iterate in the same message
2. **`/goal` condition** — a separate evaluator re-checks the condition after
   every turn; Claude keeps working until it holds. The evaluator runs no
   commands — the condition must be provable from the agent's own output
3. **Stop hook** — a deterministic script blocks the turn from ending until it
   passes (the harness overrides after 8 consecutive blocks)
4. **Verification subagent** — a fresh model tries to refute the result, so the
   agent doing the work isn't the one grading it (self-assessment bias is
   documented: generators "confidently praise the work" even when mediocre)

Always: "Have Claude show evidence rather than asserting success."
For authoring goal conditions and loop prompts, use the
**loop-goal-engineering** skill in this plugin.

---

## §6 — Balancing Autonomy and Safety

For agentic systems, design prompts that make Claude think about
consequences before acting.

**Reversibility framework:**
```xml
<action_safety>
Before taking any action, consider:
1. Is this reversible? (editing a file: yes. deleting a branch: no)
2. What's the blast radius? (local file: small. production deploy: large)
3. Could this affect others? (local test: no. sending a message: yes)

For reversible, local actions: proceed without confirmation.
For irreversible, shared, or high-impact actions: confirm with the user first.
</action_safety>
```

**Confirmation thresholds:**
- **Auto-approve:** Reading files, running tests, local edits
- **Confirm first:** Pushing code, creating PRs, sending messages, deleting files
- **Never auto-do:** Force-pushing, dropping databases, modifying permissions

---

## §7 — CLAUDE.md / Project Instructions Design

CLAUDE.md files are loaded into every conversation in a project. They're
permanent context — every token costs on every turn.

**What to include:**
- Project overview (1-2 sentences)
- Key file paths and directory structure
- Coding conventions specific to this project
- Build/test/lint commands
- Common pitfalls and how to avoid them
- Workflow preferences (commit style, PR conventions)

**What to omit:**
- Obvious defaults ("write clean code", "follow best practices")
- Generic advice Claude already knows
- Lengthy documentation that belongs in reference files
- Speculative rules not validated against actual problems

**Structure for scannability:**
```markdown
# Project Name

One-sentence description.

## Key Paths
- src/api/ — API endpoints
- src/models/ — Database models
- tests/ — Test suite (run with `pytest`)

## Conventions
- Use snake_case for Python, camelCase for JS
- All API endpoints return JSON with {data, error} shape
- Commit messages: imperative mood, <72 chars

## Common Pitfalls
- The auth middleware requires `X-API-Key` header, not Bearer token
- Database migrations must be run before tests: `make migrate`
```

**Keep it concise.** If your CLAUDE.md exceeds 100 lines, move detailed
content to reference files and link to them. The CLAUDE.md should be a
quick-reference card, not a manual.

---

## §8 — Avoiding Common Agentic Pitfalls

**Overengineering prevention:**
```xml
<keep_it_simple>
Only make changes directly requested or clearly necessary. Keep solutions simple.
Don't add features, refactor code, or make improvements beyond what was asked.
A bug fix doesn't need surrounding code cleaned up.
Don't create abstractions for one-time operations.
</keep_it_simple>
```

**Test-focused hard-coding prevention:**
```xml
<general_solutions>
Implement general-purpose solutions, not solutions that only pass specific test
cases. If a test expects output X for input Y, ensure the logic would produce
correct output for any valid input, not just the test cases.
</general_solutions>
```

**Overthinking prevention:**
- Replace blanket defaults with targeted instructions
- Remove over-prompting from older model migrations
- Use lower effort settings when task is straightforward
- Instruct Claude to commit to an approach rather than endlessly deliberating

**Subagent overuse prevention:**
```xml
<subagent_guidance>
Use subagents when tasks can run in parallel, require isolated context, or
involve independent workstreams. For simple tasks that take 1-2 tool calls,
work directly — the overhead of spawning a subagent isn't worth it.
</subagent_guidance>
```

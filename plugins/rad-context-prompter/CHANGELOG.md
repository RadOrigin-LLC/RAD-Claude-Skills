# Changelog

All notable changes to `rad-context-prompter` will be documented in this file.

## [3.2.0] - 2026-06-10

Research-driven update: verified against Anthropic's current prompting/context-engineering docs and engineering posts (through the Mar 2026 harness-design post), OpenAI's Codex docs (Goal Mode GA May 21, 2026) and GPT-5.x prompting guides, and trusted community sources (Huntley's Ralph loop, Willison's "Designing agentic loops", Osmani's "Loop Engineering", the 2026 reward-hacking literature).

### Added
- **`loop-goal-engineering` skill** — authors the artifacts that drive autonomous agent runs: loop prompts (one-task-per-iteration, file/git state, idempotent cold start, bounded), goal/completion conditions (Claude Code `/goal`, Codex Goal Mode Goal/Context/Constraints/Done-when, Stop-hook scripts), and the four-file long-horizon scaffold (spec/plan/runbook/status log — the structure Ralph and OpenAI's long-horizon guide independently converged on). Two reference files: `loop-patterns.md` (harness selection, the ten loop rules, scaffold, template, unattended-run safety) and `goal-specs.md` (goal anatomy, platform subtleties, gameability checklist G1-G8, vague-goal rewrites, goal/spec/plan separation).
- **`scripts/check-goal.py`** — pure-stdlib validator for goal conditions and loop prompts. Goal anatomy: named command/check, vague-success language, scope guard, bound, evidence display (warning-level when targeting `/goal`, whose evaluator runs no commands). Gameability G1-G7: unprotected tests, grep-zero-matches without a positive check, existence-only success, absence-only success, self-judged completion, skip-counting, effort-based success; G8 (revert-satisfiability) deliberately stays with the skill's judgment step — it isn't mechanically detectable. Loop discipline (auto-detected or `--type loop`): one-task rule, state files, idempotent start, done signal, placeholder ban, per-iteration commit. Tested against vague-goal, hardened-goal, bad-loop, and clean-loop fixtures.
- **OpenAI Codex section in tool-routing** — previously absent entirely: four-element skeleton (Goal/Context/Constraints/Done-when), AGENTS.md mechanics (32 KiB cap, nesting/override, root-to-cwd), config.toml as separate control surface, Goal Mode + Plan Mode, "deliverable is working code", one thread per task.
- **F8 loop & goal failure category in prompt-debugger** (F1-F7/37 patterns → F1-F8/44): vague end state, gameable criterion, evaluator-invisible condition, multi-task iteration, no bound, context-carried state, self-judged completion. Agent now runs a Phase 0 mechanical pre-pass (`lint-prompt.py` + `check-goal.py`) and gained Bash access to do so. (The taxonomy header previously claimed 35 patterns for F1-F7; the actual count was 37 — corrected.)

### Fixed
- **`lint-prompt.py` was unwired** — advertised in plugin.json but never invoked by any skill or the agent. Now wired into prompt-engineering's verification step (durable prompts) and the debugger's Phase 0, with cross-platform invocation (`command -v python3 || command -v python`, `${CLAUDE_PLUGIN_ROOT}`).
- **Emphasis guidance contradiction** — the verification checklist demanded "MUST over should, NEVER over avoid" on every instruction, while current Anthropic guidance says modern models over-trigger on aggressive emphasis. Now calibrated: reserve MUST/NEVER/CRITICAL for 2-3 genuine hard rules; plain imperatives elsewhere; stronger signals only for older/smaller models.

### Updated
- **Claude Code routing**: stop conditions now route to the official ladder (in-prompt check → `/goal` → Stop hook with 8-block override → verification subagent); `/goal` and `/loop` primitives documented with the evaluator-transcript subtlety; "show evidence rather than asserting success"; durable layering (CLAUDE.md always-loaded / skills on-demand / hooks deterministic, with commands converging into skills).
- **Context engineering reference**: resets-over-compaction for long-horizon work per Anthropic's Mar 2026 harness guidance ("context anxiety" named), new Completion Gating section with the stop-condition ladder and self-assessment-bias rationale.
- Model references de-pinned where they were headers ("Claude 4.x and newer", "current-generation") while keeping version-specific facts (prefill deprecation at 4.6) as facts.

## [3.1.0] and earlier

Pre-changelog releases: prompt-engineering + prompt-decompiler skills, prompt-debugger agent (F1-F7), lint-prompt.py, six reference files, 30+ platform routing.

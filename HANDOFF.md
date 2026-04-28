# Session Handoff

**Date:** 2026-04-28
**Status:** Two plugin arcs shipped this session. **rad-session 3.1 + 3.2** (cross-machine continuity + slim wrapup) merged into one commit `4a46a01`. **rad-a11y 1.0 → 2.0 → 2.1 → 2.2** shipped as three sequential commits (`297bb78`, `9ea3d78`, `1cad548`) — full honesty + mechanism + optimization arc. Clean tree at `1cad548`. Tier B reduced from {rad-a11y, rad-chrome-extension, rad-para-second-brain} to just {rad-chrome-extension, rad-para-second-brain}.

## Last Session Summary
Two plugin arcs in one session, both following established playbooks. (1) **rad-session** got cross-machine sync (`/startup` Phase 0 = `git pull --ff-only` with hostname-based cross-machine handoff detection; `/wrapup` Phase 6 = auto-commit + prompted push of session files; `/init` Step 7.5 = gitignore handling so session files travel) and slim-wrapup mechanics (recency-bounded conversation tagging, mechanical session-log derivation from HANDOFF, prune auto-skip when CLAUDE.md unchanged, `--quick` mode). (2) **rad-a11y** got the full three-PR arc mirroring rad-coolify-orchestrator: 2.0 honesty pass (confidence tags `[STATIC]`/`[HEURISTIC]`/`[NEEDS-MANUAL]`, dropped Pass/Fail verdict, dropped unbacked Vue/Svelte claims), 2.1 four mechanical Python validators (~1100 lines: scan-jsx-patterns, check-tailwind-contrast with real WCAG sRGB math, check-target-size for WCAG 2.5.8, lint-aria wrapping eslint-plugin-jsx-a11y), 2.2 cross-model + stack-aware (parallel-first batch, Phase 8 stack-routing).

## Where I Left Off
- All work pushed to `origin/main`. Working tree clean. Nothing in progress.
- This wrapup itself is running on **cached rad-session 3.0.0** — Phase 6 (auto-commit + push of session files) won't fire automatically. Manual `git add HANDOFF.md .claude/session-log.md && git commit && git push` needed after this wrapup completes, OR run `/plugin marketplace update` + reinstall before testing the new 3.2 wrapup in a fresh session.

## Key Decisions
- **Auto-commit + prompted push (not auto-push) for cross-machine sync.** Reason: user pushback — they don't always switch machines after wrapup; sometimes they stack multiple sessions on one machine before sharing. Local commits are cheap and recoverable; push is the deliberate "I'm switching machines" action. `--push` / `--no-push` flag overrides for autonomous loops.
- **Drop Pass/Fail/Compliance verdict from `/a11y-review`.** Reason: static analysis cannot defensibly produce a WCAG 2.2 AA compliance verdict. Replaced with a confidence-tiered summary tagging each finding `[STATIC]` / `[HEURISTIC]` / `[NEEDS-MANUAL]`. Severity (critical/serious/moderate/minor) and confidence are orthogonal axes.
- **Drop Vue/Svelte support claims from rad-a11y description and keywords.** Reason: never actually backed by skill content — only React, Astro, plain HTML, and Tailwind have framework-specific checks. Honesty contract: every claim is what the plugin actually does.
- **Validator findings used VERBATIM by `/a11y-review` and `a11y-reviewer` agent.** Reason: scripts are deterministic; LLM re-derivation introduces drift. Skill phases layer judgment only on what scripts can't decide (alt-text meaningfulness, complex ARIA logic, reading order, cross-element analysis).
- **Real sRGB → WCAG contrast math in `check-tailwind-contrast.py`.** Reason: a few lines of Python — no browser engine needed for static contrast verification. Real ratios surface in finding output (e.g., `gray-400` on white = 2.54:1) so the user can verify against axe DevTools.
- **Stack-aware Phase 8 routing in rad-a11y.** Reason: running React-specific checks on a plain HTML site is noise. Phase 1 builds a stack-detection record from `package.json` + config files; Phase 8 only executes slices matching detected stack. Plain HTML projects skip Phase 8 entirely.
- **Reference vs Setup vs Scanner skill type labels.** Reason: distinguishes teaching content (a11y-semantic-html, a11y-aria-patterns, a11y-keyboard-focus, a11y-forms) from real-axe setup (a11y-testing) from static scanner (a11y-review). Users know what each skill is for at a glance.
- **Three-PR shape (honesty → mechanism → optimization) is now the canonical upgrade arc for 1.x rad-* plugins.** rad-a11y followed the same path as rad-coolify-orchestrator. Future Tier B passes should use it.

## What NOT To Do
- TRIED: invoking `rad-session:wrapup` in the same session that just shipped rad-session 3.x
  FAILED BECAUSE: plugin runtime serves the cached older version (3.0.0 here), not the 3.2 written to source
  CORRECT APPROACH: this is now a 4th-occurrence recurring trap. Wrapup itself produces correct output on the cached version, but new-version features (Phase 6 sync, slim-wrapup recency bounds) won't fire. Test new plugin versions only in a fresh session after `/plugin marketplace update` + reinstall, or commit/push session files manually after a cached wrapup completes.

## Open Work
- **rad-supabase honesty + mechanism pass** — still open from prior session, not touched this session. Likely scripts: `audit-rls.py` (parses migrations + schema, flags public tables without RLS or with `USING (true)`), `check-service-role-leaks.py` (greps for `SUPABASE_SERVICE_ROLE_KEY` outside server-only paths). Same three-PR shape would apply.
- **rad-chrome-extension honesty + mechanism pass** — Tier B remaining. Likely scripts: `validate-manifest.py` (MV3 manifest schema + permission rationality), `check-content-script-isolation.py`. Honesty pass items likely include current MV3 conventions and CWS policy state.
- **rad-para-second-brain honesty + mechanism pass** — Tier B remaining. Likely scripts: `audit-folder-structure.py` (PARA structural correctness, false-project detection). Honesty-pass items likely include "actively manages" vs. "provides patterns" framing.
- **rad-context-prompter at 3.0 already** — verify if it had the actual honesty-pass rigor or just version-bumped without the same scrutiny. Quick check before starting Tier B.
- **Cached-plugin-version trap is now 4x recurring.** Wrapup's formal trap-promotion threshold is "3+ across log entries being trimmed" — current log is ~12 entries (under the 20-entry cap), so trim hasn't fired. Worth proactively adding a "Known Gotchas" section to CLAUDE.md noting this trap, but that requires user approval per wrapup's "do not restructure CLAUDE.md without permission" rule.

## Modified Files
- `plugins/rad-session/skills/wrapup/SKILL.md` — Phase 6 cross-machine sync (auto-commit silent, prompted push, `--push`/`--no-push` flags, stage only session files), recency-bounded Phase 1.3 tagging, mechanical session-log derivation from HANDOFF in Phase 3, Phase 4 prune auto-skip when CLAUDE.md unchanged, `--quick` mode
- `plugins/rad-session/skills/startup/SKILL.md` — Phase 0 `git pull --ff-only` before reads + cross-machine handoff detection via hostname in commit message, parallel-first updated to note Phase 0 must run first
- `plugins/rad-session/skills/init/SKILL.md` — Step 7.5 gitignore handling for session files
- `plugins/rad-session/references/{briefing-examples,file-conventions,session-log-format}.md` — cross-machine docs + derive-from-HANDOFF rule
- `plugins/rad-session/.claude-plugin/plugin.json` — 3.0.0 → 3.2.0; description rewritten
- `plugins/rad-session/README.md` — three-paragraph intent rewrite (what it is / what it solves / what it isn't), v3.2 + v3.1 callouts, switching-machines workflow added to Quick Start
- `plugins/rad-a11y/.claude-plugin/plugin.json` — 1.0.0 → 2.2.0 across three commits; description rewritten honestly each version
- `plugins/rad-a11y/README.md` — three-paragraph intent rewrite, v2.0/2.1/2.2 version sections, automation-catches framing tightened, what-isn't-in-scope block
- `plugins/rad-a11y/skills/a11y-review/SKILL.md` — Phase 0 (validators), Phase 1 stack-detection record, confidence tags, Pass/Fail dropped, parallel-first + cross-model note, stack-aware Phase 8 routing
- `plugins/rad-a11y/skills/a11y-testing/SKILL.md` — clarified as "real axe setup" vs static analysis; explicit catches/misses lists
- `plugins/rad-a11y/skills/a11y-{semantic-html,aria-patterns,keyboard-focus,forms}/SKILL.md` — "Skill type: Reference" labels
- `plugins/rad-a11y/agents/a11y-reviewer.md` — Honesty Constraint block, Phase 0 wiring, cross-model + stack-aware notes
- `plugins/rad-a11y/scripts/scan-jsx-patterns.py` — NEW (~370 lines) — high-confidence WCAG patterns
- `plugins/rad-a11y/scripts/check-tailwind-contrast.py` — NEW (~340 lines) — real WCAG sRGB contrast math + Tailwind v3 default palette + best-effort config parser
- `plugins/rad-a11y/scripts/check-target-size.py` — NEW (~210 lines) — WCAG 2.5.8 minimum target size, padding-aware
- `plugins/rad-a11y/scripts/lint-aria.py` — NEW (~270 lines) — eslint-plugin-jsx-a11y wrapper + regex fallback
- `plugins/rad-a11y/scripts/README.md` — NEW — schema, usage, explicit non-scope
- `README.md` (repo root) — rad-session row updated for 3.2; rad-a11y row updated for 2.0 → 2.1 → 2.2 arc

## Key Insights
- **Commit/push are different decisions in cross-machine workflows.** Commits are cheap; push is the deliberate "share with another machine" action. Default to auto-commit + prompted push, with flag overrides for autonomous loops. This was the user's actual preference — confirmed via correction during scoping.
- **Real WCAG sRGB contrast math is ~30 lines of Python.** sRGB → linear → relative luminance → ratio is pure math, no browser engine. Useful for any plugin needing static contrast verification.
- **Validator-then-LLM is the right architecture for static-review plugins.** Scripts handle deterministic pattern detection; LLM handles judgment. Keep them separate. Use validator output verbatim — re-deriving introduces drift across model runs. Pattern is now established across rad-coolify-orchestrator 2.0 (4 validators) and rad-a11y 2.1 (4 validators).
- **Real axe and a static source scanner are complementary, not redundant.** Real axe catches things source can't (computed contrast, runtime duplicate IDs, ARIA validity against resolved roles). The static scanner catches things axe often misses (Tailwind `outline-none` source pattern, hardcoded ARIA literals in JSX, React focus-drift, Astro hydration-on-interactive). The honest framing: run both.
- **The cached-plugin-version trap is now 4x recurring.** Plugin runtime serves the version that was installed, not the version in source. Every plugin-shipping session hits this. Worth promoting to permanent rule.
- **The three-PR shape (honesty → mechanism → optimization) compresses well into a single session for medium-sized plugins.** rad-a11y 2.0/2.1/2.2 shipped as three sequential commits in one session, each clean and reviewable on its own. Same shape as rad-coolify-orchestrator's path.

Worth remembering (for native Auto Memory):
- Cached-plugin-version trap is recurring (4th occurrence) — when shipping a new version of any rad-* plugin, the running session uses the cached older version. Always test in a fresh session after `/plugin marketplace update` + reinstall, or commit session files manually after a cached wrapup. (feedback)
- Auto-commit + prompted push is the user's preferred cross-machine sync model. They don't always switch machines after wrapup; prompted push lets them stack multiple unpushed session commits before sharing. (feedback)
- The three-PR shape (honesty → mechanism → optimization, e.g. rad-a11y 2.0 → 2.1 → 2.2) is the canonical upgrade arc for 1.x rad-* plugins. Mirrors rad-coolify-orchestrator's path. (project)
- rad-a11y 2.2 now sits in the same "honesty + validators + cross-model" shape as rad-writer 2.0, rad-supabase 2.0, rad-coolify-orchestrator 2.0, rad-planner 2.1, rad-seo-optimizer 2.0, rad-session 3.x. (project)

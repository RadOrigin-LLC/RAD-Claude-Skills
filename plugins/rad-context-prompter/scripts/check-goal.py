#!/usr/bin/env python3
"""
check-goal.py — Mechanical validation of agent goal conditions and loop prompts.

Checks the artifacts that drive autonomous runs (Claude Code /goal conditions,
Codex Goal Mode "Done when" blocks, Stop-hook specs, Ralph-style loop prompts)
against the documented failure modes:

  Goal anatomy (Claude Code /goal docs, Codex Goal Mode docs):
    - a named command/check the agent can run and show (not "tests pass")
    - no vague success adjectives as the end state ("better", "clean", "works")
    - a scope guard (what must NOT change)
    - a bound (turn/iteration/time cap)
    - evidence display (the /goal evaluator only sees the transcript)

  Gameability signatures G1-G7 (Anthropic eval guidance + 2026 reward-hacking literature):
    - G1: tests named as success criteria but not protected from edits
    - G2: grep-zero-matches success with no positive check (deletable files satisfy it)
    - G3: success by file existence only, with no content requirement
    - G4: success defined only by absence of noise ("no errors")
    - G5: the agent judging its own completion ("until you're satisfied")
    - G6: skip states allowed to count as passing
    - G7: success measured by effort ("attempted all items") rather than outcome
    (G8 — revert-satisfiability — needs semantic judgment; the loop-goal-engineering
    skill checks it manually per goal-specs.md §3)

  Loop discipline (Ralph loop / OpenAI long-horizon guide):
    - one task per iteration stated
    - state carried in files (plan file referenced), not conversation
    - idempotent start (no "continue where you left off")
    - an explicit all-done exit signal

Usage:
  python3 check-goal.py <file>            # goal condition or loop prompt
  echo "<text>" | python3 check-goal.py -
  python3 check-goal.py <file> --type loop     # force loop checks (default: auto)
  python3 check-goal.py <file> --json
  python3 check-goal.py <file> --strict        # promote info findings to warning

Exit codes: 0 = no critical/warning findings, 1 = findings, 2 = script error.
Pure stdlib, Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Finding:
    severity: str  # critical | warning | info
    category: str
    code: str
    message: str
    fix: str = ""
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# --- Signal vocabularies -----------------------------------------------------

# Command-shaped evidence that a real check is named.
NAMED_CHECK = re.compile(
    r"""(
        `[^`]{2,}`                                   # anything in backticks
      | \b(pytest|npm|npx|pnpm|yarn|cargo|go\s+test|tox|rspec|phpunit|
           mvn|gradle|dotnet|ruff|flake8|eslint|tsc|mypy|pyright|prettier|
           rustfmt|golangci|vitest|jest|playwright|cypress)\b
      | \bmake\s+(?!it\b|sure\b|the\b|a\b|an\b|this\b|that\b|them\b|things\b)[\w-]+
      | \bgrep\b | \bgit\s+(status|diff|log)\b
      | \bexit(s)?\s*(code\s*)?0\b | \breturn\s*code\s*0\b | \bexit\s+code\b
      | \breturns?\s+no\s+match(es)?\b | \bzero\s+match(es)?\b
      | \b0\s+failed\b | \ball\s+\d+\s+tests\b
      | \.\/[\w./-]+\.(sh|py|js|ts)\b | \b[\w-]+\.(sh|ps1)\b
      | \bcurl\b\s+ | \bhttp(s)?://\S+\s+returns?\b
    )""",
    re.IGNORECASE | re.VERBOSE,
)

VAGUE_SUCCESS = [
    (r"\bmake\s+(it|the\s+\w+)\s+better\b", "make it better"),
    (r"\b(until|when|so)\s+it\s+works\b", "until it works"),
    (r"\bworks\s+(correctly|properly|well)\b", "works correctly"),
    (r"\blooks\s+good\b", "looks good"),
    (r"\b(is|are)\s+(clean|cleaner|improved|better|robust|polished)\b", "is clean/improved/better"),
    (r"\bhigh[\s-]quality\b", "high quality"),
    (r"\bproduction[\s-]ready\b", "production ready"),
    (r"\bgood\s+error\s+handling\b", "good error handling"),
    (r"\bimprove\s+(the\s+)?(performance|quality|readability|code)\b(?![^.]*\b(p\d{2}|ms|%|benchmark)\b)", "improve performance/quality"),
    (r"\bbug\s+is\s+fixed\b(?![^.]*(`|repro|test))", "the bug is fixed"),
]

SCOPE_GUARD = re.compile(
    r"\b(do\s+not|don'?t|must\s+not|never|no\s+other|only\s+(modify|touch|change|edit)|"
    r"without\s+(modifying|changing|touching)|unchanged|out\s+of\s+scope|"
    r"no\s+new\s+dependenc\w*|stay\s+within|protected|no\s+files?\s+under|"
    r"may\s+not\s+be\s+(modified|changed|edited))\b",
    re.IGNORECASE,
)

BOUND = re.compile(
    r"\b(stop\s+after|give\s+up\s+after|at\s+most|max(imum)?\s+(of\s+)?\d+|"
    r"\d+\s+(turns?|iterations?|attempts?|loops?|tries|hours?|minutes?)|"
    r"within\s+\d+|time\s*(limit|box|out)|budget|no\s+more\s+than\s+\d+)\b",
    re.IGNORECASE,
)

EVIDENCE = re.compile(
    r"\b(show(ing)?|paste|prove|evidence|display|include)\b[^.\n]{0,60}"
    r"\b(output|summary|result|exit\s+code|log|the\s+command)\b"
    r"|\bshow\s+(it|this|the|both|that)\b",
    re.IGNORECASE,
)

MENTIONS_TESTS = re.compile(r"\b(tests?|pytest|test\s+suite|spec(s)?\b|vitest|jest)\b", re.IGNORECASE)
TESTS_PROTECTED = re.compile(
    r"(not?\b[^.\n]{0,60}\b(modif|edit|delet|chang|touch|remov)\w*[^.\n]{0,40}\btests?\b"
    r"|\btests?\b[^.\n]{0,40}\b(may|must|can)\s+not\s+be\s+(modified|edited|deleted|changed|touched|removed)"
    r"|\btests?/?\b[^.\n]{0,30}\bprotected\b"
    r"|\b(never|don'?t|do\s+not)\b[^.\n]{0,50}\btests?\b"
    r"|\bfix\s+the\s+code\b[^.\n]{0,30}\b(instead|not\s+the\s+tests?)\b)",
    re.IGNORECASE,
)

EXISTENCE_ONLY = re.compile(r"\b(file|report|doc(ument)?|\w+\.\w{2,4})\s+(exists|is\s+created|is\s+present)\b", re.IGNORECASE)
CONTENT_REQUIRED = re.compile(r"\b(contains?|includes?|shows?|with\s+sections?|non[\s-]?empty|covers?|lists?)\b", re.IGNORECASE)

ABSENCE_ONLY = re.compile(r"\bno\s+(errors?|warnings?|exceptions?)\b", re.IGNORECASE)
SKIP_ALLOWED = re.compile(r"\b(or\s+(are\s+)?skipped|skipp?ed\s+(count|tests?\s+are\s+(ok|fine|acceptable)))\b", re.IGNORECASE)
SKIP_FORBIDDEN = re.compile(r"\b0\s+skipped\b|\bno\s+skipped\b|\bwithout\s+skipping\b", re.IGNORECASE)
GREP_ZERO = re.compile(
    r"\bgrep\b[^.\n]{0,80}\b(no\s+match(es)?|zero\s+match(es)?|returns?\s+nothing|empty)\b"
    r"|\b(no|zero)\s+match(es)?\b[^.\n]{0,40}\bgrep\b",
    re.IGNORECASE,
)
EFFORT_BASED = re.compile(
    r"\b(attempt(ed)?|tried|work(ed)?\s+on|address(ed)?|look(ed)?\s+at|go(ne)?\s+through)\s+"
    r"(all|every|each)\s+(of\s+the\s+)?\w*(items?|tasks?|files?|issues?|tests?|cases?)\b",
    re.IGNORECASE,
)
SELF_JUDGED = re.compile(
    r"\b(until|when|once)\s+you('| a)?re?\s+(satisfied|happy|confident|done)\b"
    r"|\byou\s+(decide|judge|determine)\s+(when|whether|if)\b"
    r"|\buntil\s+you\s+(think|feel|believe)\b"
    r"|\b(rate|score|grade)\s+your\s+(own\s+)?work\b",
    re.IGNORECASE,
)

LOOP_SIGNALS = re.compile(
    r"\b(each\s+(loop|iteration|pass|session)|per\s+(loop|iteration)|every\s+iteration|"
    r"while\s+(true|:)|re-?run|ralph|fix_plan|PLAN\.md|/loop\b|loop\s+prompt|"
    r"pick\s+the\s+(next|top|single|first|highest)|this\s+(session|iteration))\b",
    re.IGNORECASE,
)
ONE_TASK = re.compile(
    r"\b(one|single|a\s+single|exactly\s+one|ONE)\s+(task|item|feature|milestone|thing|fix)\b"
    r"|\bonly\s+that\s+(item|task)\b",
    re.IGNORECASE,
)
STATE_FILE = re.compile(r"(@[\w./-]+\.md\b|\b[\w-]*(plan|spec|todo|backlog|runbook|status)[\w-]*\.md\b|\bgit\s+log\b)", re.IGNORECASE)
NON_IDEMPOTENT = re.compile(r"\b(continue|pick\s+up|resume)\s+(from\s+)?where\s+(you|we)\s+left\s+off\b|\bas\s+you\s+remember\b|\bfrom\s+last\s+(time|session)\b", re.IGNORECASE)
PLACEHOLDER_BAN = re.compile(r"\b(placeholder|stub|full(y)?\s+implement|no\s+TODO)\w*\b", re.IGNORECASE)
COMMIT = re.compile(r"\bcommit\b", re.IGNORECASE)
DONE_SIGNAL = re.compile(
    r"\b(ALL\s+TASKS?\s+COMPLETE|DONE|COMPLETE|no\s+(unchecked|remaining)\s+items?|"
    r"nothing\s+(left|remaining)|plan\s+(file\s+)?is\s+empty)\b",
)


def _snippet(text: str, match: re.Match) -> str:
    start = max(0, match.start() - 20)
    end = min(len(text), match.end() + 20)
    return " ".join(text[start:end].split())


def check_goal_anatomy(text: str, findings: list[Finding], targets_claude_goal: bool) -> None:
    if not NAMED_CHECK.search(text):
        findings.append(Finding(
            severity="critical", category="goal-anatomy", code="named_check_missing",
            message="No named command or concrete check found. 'Tests pass' / 'it works' is the "
                    "documented failure mode — the agent either false-completes or never completes.",
            fix='Name the proof: "`pytest` exits 0", "`grep -rn TODO src/` returns no matches", '
                '"repro.sh prints SUCCESS".',
        ))

    for pattern, label in VAGUE_SUCCESS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            findings.append(Finding(
                severity="warning", category="goal-anatomy", code="vague_success_language",
                message=f'Vague success language: "{label}". Two experts could disagree on pass/fail.',
                fix="Convert to (a) named command, (b) required output, (c) what must not change, (d) a bound.",
                snippet=_snippet(text, m),
            ))

    if not SCOPE_GUARD.search(text):
        findings.append(Finding(
            severity="warning", category="goal-anatomy", code="scope_guard_missing",
            message="No scope guard — nothing states what must NOT change. Invites drive-by edits "
                    "and success-by-side-effect.",
            fix='Add constraints: "no file under tests/ may be modified", "no new dependencies", '
                '"public API signatures unchanged".',
        ))

    if not BOUND.search(text):
        findings.append(Finding(
            severity="warning", category="goal-anatomy", code="bound_missing",
            message="No bound (turn/iteration/time cap). Unbounded goals are runaway-cost bugs.",
            fix='Add: "or stop after 25 turns" / "max 10 iterations" / a wall-clock cap.',
        ))

    if not EVIDENCE.search(text):
        findings.append(Finding(
            severity="warning" if targets_claude_goal else "info",
            category="goal-anatomy", code="evidence_display_missing",
            message="Nothing instructs the agent to SHOW the proof (command output) in its response."
                    + (" The Claude Code /goal evaluator only sees the transcript — it runs no "
                       "commands itself." if targets_claude_goal else ""),
            fix='Add: "prove it by running the command and showing the summary/output".',
        ))


def check_gameability(text: str, findings: list[Finding]) -> None:
    if MENTIONS_TESTS.search(text) and not TESTS_PROTECTED.search(text):
        findings.append(Finding(
            severity="critical", category="gameability", code="g1_tests_unprotected",
            message="Tests are the success criterion but nothing forbids editing them. Documented "
                    "agent exploit: weaken/delete tests until green.",
            fix='Add: "no file under tests/ may be modified — fix the code, not the tests".',
        ))

    m = GREP_ZERO.search(text)
    if m and not MENTIONS_TESTS.search(text):
        findings.append(Finding(
            severity="warning", category="gameability", code="g2_grep_without_positive_check",
            message="Success measured by grep returning zero matches, with no accompanying positive "
                    "check — deleting the files that contain the matches satisfies it.",
            fix='Pair with "all existing tests still pass" and protected paths.',
            snippet=_snippet(text, m),
        ))

    m = EXISTENCE_ONLY.search(text)
    if m and not CONTENT_REQUIRED.search(text):
        findings.append(Finding(
            severity="warning", category="gameability", code="g3_existence_only",
            message="Success by file existence with no content requirement — satisfiable with an "
                    "empty or stub file.",
            fix="Require content: named sections present, embedded command output, non-empty checks.",
            snippet=_snippet(text, m),
        ))

    m = ABSENCE_ONLY.search(text)
    if m and not NAMED_CHECK.search(text):
        findings.append(Finding(
            severity="warning", category="gameability", code="g4_absence_only",
            message='Success defined only by absence of noise ("no errors") — suppressing or '
                    "swallowing errors satisfies it.",
            fix="Check positive behavior with a named command, not just silence.",
            snippet=_snippet(text, m),
        ))

    m = SKIP_ALLOWED.search(text)
    if m and not SKIP_FORBIDDEN.search(text):
        findings.append(Finding(
            severity="warning", category="gameability", code="g6_skip_allowed",
            message="Skipped tests appear to count as passing — marking failures as skipped "
                    "satisfies the goal.",
            fix='Require "0 failed, 0 skipped" explicitly.',
            snippet=_snippet(text, m),
        ))

    m = EFFORT_BASED.search(text)
    if m:
        findings.append(Finding(
            severity="warning", category="gameability", code="g7_effort_based",
            message='Success measured by effort ("attempted/addressed all items") rather than '
                    "outcome — items can be marked done without being done.",
            fix="Require a per-item validation command; completion = the check passes, not the attempt.",
            snippet=_snippet(text, m),
        ))

    m = SELF_JUDGED.search(text)
    if m:
        findings.append(Finding(
            severity="warning", category="gameability", code="g5_self_judged",
            message="The agent judges its own completion. Self-assessment bias is documented: "
                    "agents confidently praise mediocre work.",
            fix="Bind completion to an external check (command exit code) or an independent evaluator.",
            snippet=_snippet(text, m),
        ))


def check_loop_discipline(text: str, findings: list[Finding], strict: bool) -> None:
    if not ONE_TASK.search(text):
        findings.append(Finding(
            severity="warning", category="loop-discipline", code="one_task_missing",
            message='No one-task-per-iteration rule. The most-violated, most-critical loop rule '
                    '("one item per loop" — Ralph).',
            fix='Add: "Pick the SINGLE highest-priority unchecked item. Work on only that item this session."',
        ))

    if not STATE_FILE.search(text):
        findings.append(Finding(
            severity="warning", category="loop-discipline", code="state_files_missing",
            message="No state/plan file referenced. Each iteration starts cold — progress must "
                    "live in files and git, not the conversation.",
            fix="Reference the scaffold explicitly: read @PLAN.md (and git log) at start, update it before exit.",
        ))

    m = NON_IDEMPOTENT.search(text)
    if m:
        findings.append(Finding(
            severity="warning", category="loop-discipline", code="non_idempotent_start",
            message='"Continue where you left off" is undefined on a cold start — the new '
                    "iteration has no memory.",
            fix='Replace with: "determine current state from the plan file and git log, then act".',
            snippet=_snippet(text, m),
        ))

    if not DONE_SIGNAL.search(text):
        findings.append(Finding(
            severity="warning", category="loop-discipline", code="done_signal_missing",
            message="No explicit all-done exit. The loop has no way to terminate when the backlog "
                    "is empty.",
            fix='Add: "If the plan has no unchecked items, output exactly ALL TASKS COMPLETE and stop."',
        ))

    if not PLACEHOLDER_BAN.search(text):
        findings.append(Finding(
            severity="warning" if strict else "info",
            category="loop-discipline", code="placeholder_ban_missing",
            message="No placeholder/stub ban. Loops amplify stubs — a placeholder committed early "
                    "becomes load-bearing later.",
            fix='Add: "Implement fully — no placeholders, stubs, or TODO comments standing in for logic."',
        ))

    if not COMMIT.search(text):
        findings.append(Finding(
            severity="warning" if strict else "info",
            category="loop-discipline", code="commit_missing",
            message="No per-iteration commit instruction. Git is the loop's rollback and memory mechanism.",
            fix='Add: "Commit with a descriptive message before exiting."',
        ))


def detect_mode(text: str, forced: str) -> str:
    if forced != "auto":
        return forced
    return "loop" if LOOP_SIGNALS.search(text) else "goal"


def run_checks(text: str, mode: str, strict: bool) -> list[Finding]:
    findings: list[Finding] = []
    targets_claude_goal = bool(re.search(r"/goal\b|goal\s+condition|claude\s+code", text, re.IGNORECASE))
    check_goal_anatomy(text, findings, targets_claude_goal)
    check_gameability(text, findings)
    if mode == "loop":
        check_loop_discipline(text, findings, strict)
    if strict:
        for f in findings:
            if f.severity == "info":
                f.severity = "warning"
    return findings


def render_text(findings: list[Finding], source: str, mode: str) -> str:
    out = [f"check-goal ({mode} mode): {source}", ""]
    if not findings:
        out.append("PASS — goal anatomy, gameability, and discipline checks all clear.")
        return "\n".join(out)
    by_sev: dict[str, list[Finding]] = {"critical": [], "warning": [], "info": []}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    for sev in ("critical", "warning", "info"):
        items = by_sev.get(sev, [])
        if not items:
            continue
        out.append(f"[{sev.upper()}] {len(items)} finding{'s' if len(items) != 1 else ''}")
        for f in items:
            out.append(f"  {f.code} ({f.category})")
            if f.snippet:
                out.append(f"    snippet: ...{f.snippet}...")
            out.append(f"    {f.message}")
            if f.fix:
                out.append(f"    fix: {f.fix}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", help="Goal/loop prompt file, or '-' for stdin")
    p.add_argument("--type", choices=["goal", "loop", "auto"], default="auto",
                   help="Which check set to run (default: auto-detect)")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    p.add_argument("--strict", action="store_true", help="Promote info findings to warning")
    args = p.parse_args(argv)

    if args.file == "-":
        text = sys.stdin.read()
        source = "<stdin>"
    else:
        path = Path(args.file).resolve()
        if not path.exists() or not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"error: cannot read file: {e}", file=sys.stderr)
            return 2
        source = str(path)

    if not text.strip():
        print("error: empty input", file=sys.stderr)
        return 2

    mode = detect_mode(text, args.type)
    findings = run_checks(text, mode, args.strict)

    if args.json:
        print(json.dumps({
            "validator": "check-goal",
            "version": "1.0.0",
            "source": source,
            "mode": mode,
            "strict": args.strict,
            "findings": [f.to_dict() for f in findings],
        }, indent=2))
    else:
        print(render_text(findings, source, mode))

    has_blocker = any(f.severity in ("critical", "warning") for f in findings)
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

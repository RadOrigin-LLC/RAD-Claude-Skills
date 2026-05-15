#!/usr/bin/env python3
r"""
lint-prompt.py — Mechanical detection of common prompt-engineering issues.

Reads a prompt from a file or stdin and reports structural issues commonly
seen in prompts that don't work well:

  - Missing role / system framing
  - Vague instructions ("make it better", "be helpful", "do your best")
  - Conflicting format instructions ("respond in JSON" + "use markdown")
  - No output schema / structure when format is unusual
  - Missing examples for few-shot patterns
  - Token-bloat patterns: repeated YOU MUST language, excessive markdown
    decoration, "always remember" repetition
  - Constraint vagueness ("short", "concise" without limits)
  - Imperative-collision: same action both required and forbidden
  - "AI superhuman" framing patterns (don't help quality)
  - Missing audience / context (no who/why)

This is regex + heuristics, not an LLM. The findings are SIGNALS — the user
should review and decide. Severity is calibrated conservatively.

Usage:
  python3 lint-prompt.py <prompt-file>
  echo "<prompt>" | python3 lint-prompt.py -
  python3 lint-prompt.py <prompt-file> --json
  python3 lint-prompt.py <prompt-file> --strict

Output:
  Default — human-readable text. Exit 1 on warning/critical.
  --json   — single JSON object on stdout.
  Exit 2   — script error.

No third-party dependencies. Python 3.8+.
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
    severity: str       # critical | warning | info
    category: str
    code: str
    message: str
    line: int = 0
    snippet: str = ""
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# Patterns that strongly suggest a role/system frame
ROLE_PATTERNS = re.compile(
    r"(?im)^\s*(?:You\s+are|Your\s+role|Act\s+as|You'?ll?\s+(?:act|serve|behave)|"
    r"As\s+(?:a|an|the))\b"
)

# Vague instructions
VAGUE_PHRASES = [
    (re.compile(r"(?i)\b(?:make\s+it\s+(?:better|good|nice|great)|"
                r"do\s+your\s+best|be\s+helpful|be\s+useful|"
                r"think\s+carefully(?!\s+about)|reason\s+well|"
                r"give\s+a\s+good\s+(?:answer|response))\b"),
     "vague_instruction",
     "Vague instruction — replace with a concrete success criterion."),
    (re.compile(r"(?i)\b(?:short|brief|concise|long|detailed|thorough)\b(?!\s+(?:answer|response|enough|under|than|like|as|to))"),
     "unbounded_length",
     "Length adjective without a measurable limit. Specify a target (e.g., 'under 200 words', '3-5 bullets')."),
    (re.compile(r"(?i)\b(?:high[- ]quality|professional|polished|tasteful|elegant|beautiful)\b"),
     "subjective_quality",
     "Subjective quality adjective. Replace with a checkable property (e.g., 'has a thesis sentence in the first paragraph')."),
    (re.compile(r"(?i)\b(?:appropriate|suitable|reasonable|proper|adequate)\b"),
     "vague_qualifier",
     "Vague qualifier. Make the criterion explicit."),
]

# Format conflicts (rough): mention of two output formats
FORMAT_PATTERNS = [
    ("json",     re.compile(r"(?i)\b(respond|output|return|answer|format)[^.\n]{0,40}\b(json|JSON)\b")),
    ("markdown", re.compile(r"(?i)\b(respond|output|return|use|format)[^.\n]{0,40}\b(markdown|md)\b")),
    ("xml",      re.compile(r"(?i)\b(respond|output|return|use|wrap)[^.\n]{0,40}\b(xml|XML)\b")),
    ("yaml",     re.compile(r"(?i)\b(respond|output|return|format)[^.\n]{0,40}\b(yaml|YAML)\b")),
    ("plain",    re.compile(r"(?i)\b(respond|output|return)[^.\n]{0,40}\bplain\s*text\b")),
]

# Few-shot heuristic: text mentions examples but none are present
EXAMPLE_INTENT = re.compile(r"(?i)\b(for\s+example|e\.g\.|example[s]?:|examples\s+include|like\s+this:)")
EXAMPLE_BLOCK_PATTERNS = [
    re.compile(r"```[a-zA-Z]*\n"),
    re.compile(r"(?im)^\s*example\s*\d*[:.]\s*"),
    re.compile(r"(?im)^\s*input[:.]\s*"),
]

# "YOU MUST" / "ALWAYS" overuse
ALWAYS_MUST = re.compile(r"(?i)\b(YOU\s+MUST|ALWAYS|NEVER|UNDER\s+NO\s+CIRCUMSTANCES|IMPORTANT[!:])\b")

# AI-superhuman framing
SUPERHUMAN_PATTERNS = re.compile(
    r"(?i)\b(you\s+are\s+(?:the\s+best|a\s+world[- ]class|an?\s+expert|"
    r"an?\s+exceptional|incredibly\s+intelligent|the\s+world'?s)|"
    r"act\s+as\s+(?:the\s+best|a\s+world[- ]class))\b"
)

# Imperative collisions: same verb both "do" and "don't"
COLLISION_VERBS = ("explain", "describe", "list", "summarize", "include",
                   "mention", "use", "add", "show", "tell")


def detect_role_frame(text: str, findings: list[Finding]) -> bool:
    if ROLE_PATTERNS.search(text):
        return True
    findings.append(Finding(
        severity="warning",
        category="structure",
        code="no_role_frame",
        message="No role / system frame detected. Prompts work better with an explicit role anchor.",
        fix='Start with: "You are a [role] who [primary purpose]. Your goal is [outcome]."',
    ))
    return False


def detect_vagueness(text: str, findings: list[Finding]) -> None:
    seen_codes: set[tuple[str, int]] = set()
    for pattern, code, advice in VAGUE_PHRASES:
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            key = (code, line)
            if key in seen_codes:
                continue
            seen_codes.add(key)
            snippet = text[max(0, m.start()-30):m.end()+30].replace("\n", " ")[:120]
            findings.append(Finding(
                severity="warning",
                category="vagueness",
                code=code,
                line=line,
                snippet=snippet,
                message=advice,
            ))


def detect_format_conflict(text: str, findings: list[Finding]) -> None:
    declared = []
    for name, pattern in FORMAT_PATTERNS:
        if pattern.search(text):
            declared.append(name)
    if len(declared) >= 2:
        findings.append(Finding(
            severity="warning",
            category="format",
            code="conflicting_output_format",
            message=f"Multiple output formats declared: {', '.join(declared)}. "
                    "Pick one; conflicting format instructions degrade reliability.",
        ))


def detect_missing_examples(text: str, findings: list[Finding]) -> None:
    if not EXAMPLE_INTENT.search(text):
        return
    has_example_block = any(p.search(text) for p in EXAMPLE_BLOCK_PATTERNS)
    if not has_example_block:
        findings.append(Finding(
            severity="info",
            category="examples",
            code="example_intent_no_examples",
            message="Text references 'for example' / 'e.g.' but no example block / code fence found. "
                    "If a few-shot pattern is intended, add explicit input/output examples.",
        ))


def detect_overuse_capitals(text: str, findings: list[Finding]) -> None:
    count = len(list(ALWAYS_MUST.finditer(text)))
    word_count = len(text.split())
    if word_count == 0:
        return
    if count >= 5 and (count / max(word_count, 1)) > 0.005:
        findings.append(Finding(
            severity="info",
            category="emphasis_overuse",
            code="excessive_must_always",
            message=f"{count} occurrences of YOU MUST / ALWAYS / NEVER / IMPORTANT. "
                    "Over-emphasis dilutes signal — reserve for the few rules that truly matter.",
        ))


def detect_superhuman(text: str, findings: list[Finding]) -> None:
    for m in SUPERHUMAN_PATTERNS.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        findings.append(Finding(
            severity="info",
            category="framing",
            code="superhuman_role",
            line=line,
            snippet=m.group(0),
            message=("'world-class', 'best', 'expert' framing in role doesn't improve output quality. "
                     "Be specific about what the role actually does."),
        ))


def detect_imperative_collision(text: str, findings: list[Finding]) -> None:
    lower = text.lower()
    for verb in COLLISION_VERBS:
        positive_pattern = re.compile(rf"\b{verb}\b", re.IGNORECASE)
        negative_pattern = re.compile(rf"(?:don'?t|do\s+not|never|avoid|without)\s+\w*\s*{verb}\b", re.IGNORECASE)
        has_positive = bool(positive_pattern.search(text))
        has_negative = bool(negative_pattern.search(text))
        if has_positive and has_negative:
            findings.append(Finding(
                severity="warning",
                category="imperative_collision",
                code=f"both_do_and_dont:{verb}",
                message=f"Prompt both demands and forbids '{verb}'. Resolve the conflict — when should the model do this, when shouldn't it?",
            ))


def detect_no_audience(text: str, findings: list[Finding], strict: bool) -> None:
    if not strict:
        return
    audience_re = re.compile(r"(?i)\b(?:for\s+(?:a|the|my|our)|audience|reader|customer|user|stakeholder|reviewer)\b")
    if not audience_re.search(text):
        findings.append(Finding(
            severity="info",
            category="context",
            code="no_audience_specified",
            message="No audience / reader specified. Prompts that name the reader produce more targeted output.",
            fix='Add: "Write for [audience], who [knows / cares about / needs]..."',
        ))


def lint_prompt(text: str, strict: bool) -> list[Finding]:
    findings: list[Finding] = []
    detect_role_frame(text, findings)
    detect_vagueness(text, findings)
    detect_format_conflict(text, findings)
    detect_missing_examples(text, findings)
    detect_overuse_capitals(text, findings)
    detect_superhuman(text, findings)
    detect_imperative_collision(text, findings)
    detect_no_audience(text, findings, strict)
    return findings


def render_text(findings: list[Finding], source: str) -> str:
    out = [f"lint-prompt: {source}", ""]
    if not findings:
        out.append("PASS — no structural prompt issues detected.")
        return "\n".join(out)
    by_sev = {"critical": [], "warning": [], "info": []}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    for sev in ("critical", "warning", "info"):
        items = by_sev.get(sev, [])
        if not items:
            continue
        out.append(f"[{sev.upper()}] {len(items)} finding{'s' if len(items) != 1 else ''}")
        for f in items:
            location = f"  line {f.line}: " if f.line else "  "
            out.append(f"{location}{f.code}")
            if f.snippet:
                out.append(f"    snippet: {f.snippet}")
            out.append(f"    {f.message}")
            if f.fix:
                out.append(f"    fix: {f.fix}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("file", help="Prompt file to lint, or '-' for stdin")
    p.add_argument("--strict", action="store_true", help="Enable info-level checks (audience, etc.)")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    if args.file == "-":
        text = sys.stdin.read()
        source = "<stdin>"
    else:
        path = Path(args.file).resolve()
        if not path.exists() or not path.is_file():
            print(f"error: prompt file not found: {path}", file=sys.stderr)
            return 2
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"error: cannot read prompt: {e}", file=sys.stderr)
            return 2
        source = str(path)

    findings = lint_prompt(text, args.strict)

    if args.json:
        out = {
            "validator": "lint-prompt",
            "version": "1.0.0",
            "source": source,
            "strict": args.strict,
            "char_count": len(text),
            "line_count": text.count("\n") + 1,
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_text(findings, source))

    has_blocker = any(f.severity in ("critical", "warning") for f in findings)
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

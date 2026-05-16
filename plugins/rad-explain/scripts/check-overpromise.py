#!/usr/bin/env python3
r"""
check-overpromise.py — Flag sensational language, vague-quantity claims, and marketing fluff.

Reads a Markdown file (or stdin) and detects patterns that the rad-claude-skills
marketplace's "no sensational copy" guardrail explicitly rejects:

  - Superlatives without backing ("the only", "the best", "the first", "world-class")
  - Vague-quantity claims ("30+ platforms", "thousands of users") not paired with enumeration
  - Marketing fluff ("revolutionary", "groundbreaking", "transform", "unleash")
  - Filler intensifiers ("incredibly", "absolutely", "completely")
  - Production-readiness assertions without evidence ("enterprise-grade", "production-ready")

This validator is opinionated. It runs the same honesty rule the user applied
to the rad-claude-skills marketplace itself, against external-facing copy
(READMEs, marketplace listings, pitches, project stories). It surfaces the
candidates; the user judges which are real (a backed claim of being the only
X is fine; an unbacked claim is not).

Severity:
  critical  — explicit superlative or marketing-fluff phrase
  warning   — vague-quantity claim not paired with enumeration
  info      — filler intensifiers (style noise, not deception)

Usage:
  python3 check-overpromise.py <file.md>
  echo "<copy>" | python3 check-overpromise.py -
  python3 check-overpromise.py <file.md> --json
  python3 check-overpromise.py <file.md> --strict   # tighter thresholds

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
    line: int
    column: int
    matched_text: str
    message: str
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ----- Superlatives (critical) -----
# These are absolute superiority claims. Backed by data they're sometimes
# defensible; unbacked, they're the canonical overpromise pattern.
SUPERLATIVE_PATTERNS = [
    (
        "the_only",
        re.compile(r"(?i)\b(the\s+only|world'?s\s+only|industry'?s\s+only)\s+\w+"),
        "Superlative: 'the only X' is an extraordinary claim",
        "Either remove or cite. Real evidence: 'the only [X] that does [specific verifiable behavior]'.",
    ),
    (
        "the_best",
        re.compile(r"(?i)\b(the\s+best|world'?s\s+best|industry'?s\s+best|best[- ]in[- ]class|best[- ]of[- ]breed)\b"),
        "Superlative: 'the best' / 'best-in-class'",
        "Replace with comparison-shaped claim: 'better than X at Y because Z' (with Z verifiable).",
    ),
    (
        "world_class",
        re.compile(r"(?i)\b(world[- ]?class|world[- ]?leading|industry[- ]?leading)\b"),
        "Vague superiority: 'world-class' / 'industry-leading'",
        "Replace with what the thing actually does that supports the claim.",
    ),
    (
        "unmatched",
        re.compile(r"(?i)\b(unmatched|unparalleled|unrivaled|unsurpassed|second[- ]to[- ]none)\b"),
        "Absolute superiority: 'unmatched' / 'unparalleled'",
        "Remove or specify what's being compared against.",
    ),
    (
        "revolutionary",
        re.compile(r"(?i)\b(revolutionary|groundbreaking|game[- ]changing|paradigm[- ]shifting|disruptive)\b"),
        "Hype: '{matched}'",
        "Concrete claims only. What specifically is new vs the prior state?",
    ),
    (
        "transform",
        re.compile(r"(?i)\b(transform|revolutionize|disrupt|unleash|unlock|supercharge|turbocharge)\s+(?:your|the|our)"),
        "Marketing verb: '{matched}'",
        "Replace with a specific verb tied to a specific outcome.",
    ),
]


# ----- Vague-quantity claims (warning) -----
# A number with '+', 'thousands', 'millions', 'countless' often appears
# without enumeration. Flag for verification.
VAGUE_QUANTITY_PATTERNS = [
    (
        "plus_count",
        re.compile(r"\b(\d+\+|\d+\s*plus)\s+([a-zA-Z][a-zA-Z\-]+(?:\s+[a-zA-Z][a-zA-Z\-]+)?)"),
        "Vague-quantity: 'N+ X'",
        "Either enumerate the N (list, footnote, link to list) or drop the '+'.",
    ),
    (
        "thousands",
        re.compile(r"(?i)\b(thousands|hundreds|millions|countless|innumerable|myriad)\s+of\s+\w+"),
        "Vague-quantity: '{matched}'",
        "Replace with a concrete number or a verifiable range.",
    ),
    (
        "many_more",
        re.compile(r"(?i)\b(many\s+more|countless\s+more|and\s+more)\b"),
        "Vague suffix: '{matched}'",
        "Either enumerate what 'more' includes or drop the qualifier.",
    ),
]


# ----- Production-readiness without evidence (critical) -----
PRODUCTION_READY_PATTERNS = [
    (
        "production_grade",
        re.compile(r"(?i)\b(production[- ]?grade|production[- ]?ready|enterprise[- ]?grade|enterprise[- ]?ready|battle[- ]?tested|battle[- ]?proven|mission[- ]?critical)\b"),
        "Readiness claim: '{matched}'",
        "These claims need evidence: uptime SLA, scale numbers, named adopters, audit results. Without those, this is overpromise.",
    ),
    (
        "secure_by_default",
        re.compile(r"(?i)\b(secure[- ]by[- ]default|hardened|fort[- ]knox|bank[- ]grade|military[- ]grade)\b"),
        "Security overclaim: '{matched}'",
        "Specific security properties only: 'all secrets in 1Password', 'CSP set to script-src self', etc.",
    ),
]


# ----- Marketing fluff / vibes (warning) -----
FLUFF_PATTERNS = [
    (
        "seamless",
        re.compile(r"(?i)\b(seamless|frictionless|effortless|painless)\b"),
        "Fluff adjective: '{matched}'",
        "Specific friction-reducer instead: 'one command', 'no config', 'auto-detects X'.",
    ),
    (
        "intelligent",
        re.compile(r"(?i)\b(intelligent|smart|powerful|robust|comprehensive|complete\b(?!\s+(?:the|a|an)))"),
        "Vibe adjective: '{matched}'",
        "Replace with what makes it intelligent/smart/powerful — the specific behavior.",
    ),
    (
        "elegant",
        re.compile(r"(?i)\b(elegant|beautiful|exquisite|polished\b)"),
        "Subjective quality: '{matched}'",
        "If true, the reader will judge. If not, remove.",
    ),
]


# ----- Filler intensifiers (info) -----
INTENSIFIER_PATTERN = re.compile(
    r"(?i)\b(incredibly|extremely|absolutely|completely|totally|literally|truly|deeply)\s+\w+"
)


# Allow patterns that signal a backed claim — if these appear near a flagged
# phrase, downgrade severity (don't drop entirely; the user should still see it).
BACKING_PATTERNS = re.compile(
    r"(?i)\b(verified|measured|cited|according\s+to|see\s+\[?\w|per\s+(?:rfc|spec|the)|"
    r"benchmark|tested|documented|reference|spec|enumerated\s+(?:below|above|here)|"
    r"see\s+(?:below|above|the\s+\w+))\b"
)


# Allowlist — common false-positive phrases we don't flag
ALLOWLIST_LINES = re.compile(
    r"(?i)^\s*(?:#|//|/\*|<!--|>\s|copyright|version|license|"
    r"the\s+claude\.ai\s+skill|\.claude/|`[^`]*`).*$"
)


def line_col(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    col = offset - (text.rfind("\n", 0, offset) + 1) + 1
    return line, col


def line_text_at(text: str, offset: int) -> str:
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end]


def is_in_code_block(text: str, offset: int) -> bool:
    """Skip matches inside fenced code blocks (```...```) or inline backticks."""
    # Count triple-backtick fences before offset
    fence_count = text.count("```", 0, offset)
    if fence_count % 2 == 1:
        return True  # inside a fence
    # Inline backticks on same line
    line_start = text.rfind("\n", 0, offset) + 1
    line_up_to = text[line_start:offset]
    if line_up_to.count("`") % 2 == 1:
        return True
    return False


def is_in_allowlisted_line(text: str, offset: int) -> bool:
    line = line_text_at(text, offset)
    return bool(ALLOWLIST_LINES.match(line))


def nearby_backing(text: str, offset: int, window: int = 200) -> bool:
    start = max(0, offset - window)
    end = min(len(text), offset + window)
    return bool(BACKING_PATTERNS.search(text[start:end]))


def scan_patterns(text: str, patterns: list, base_severity: str,
                  category: str, strict: bool) -> list[Finding]:
    findings: list[Finding] = []
    for code, pattern, msg_template, fix in patterns:
        for m in pattern.finditer(text):
            offset = m.start()
            if is_in_code_block(text, offset):
                continue
            if is_in_allowlisted_line(text, offset):
                continue
            # Downgrade severity if backing language is nearby
            severity = base_severity
            if not strict and nearby_backing(text, offset):
                severity = {"critical": "warning", "warning": "info", "info": "info"}[severity]
            matched = m.group(0)
            message = msg_template.format(matched=matched)
            line, col = line_col(text, offset)
            findings.append(Finding(
                severity=severity,
                category=category,
                code=code,
                line=line,
                column=col,
                matched_text=matched,
                message=message,
                fix=fix,
            ))
    return findings


def scan_intensifiers(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for m in INTENSIFIER_PATTERN.finditer(text):
        offset = m.start()
        if is_in_code_block(text, offset):
            continue
        if is_in_allowlisted_line(text, offset):
            continue
        line, col = line_col(text, offset)
        findings.append(Finding(
            severity="info",
            category="intensifier",
            code="filler_intensifier",
            line=line,
            column=col,
            matched_text=m.group(0),
            message=f"Filler intensifier: '{m.group(0)}'",
            fix="Usually the sentence is fine without it. Cut.",
        ))
    return findings


def lint_text(text: str, strict: bool) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(scan_patterns(text, SUPERLATIVE_PATTERNS, "critical", "superlative", strict))
    findings.extend(scan_patterns(text, VAGUE_QUANTITY_PATTERNS, "warning", "vague_quantity", strict))
    findings.extend(scan_patterns(text, PRODUCTION_READY_PATTERNS, "critical", "production_ready", strict))
    findings.extend(scan_patterns(text, FLUFF_PATTERNS, "warning", "fluff", strict))
    findings.extend(scan_intensifiers(text))
    # Sort by line, then column
    findings.sort(key=lambda f: (f.line, f.column))
    return findings


def render_text(findings: list[Finding], source: str) -> str:
    out = [f"check-overpromise: {source}", ""]
    if not findings:
        out.append("PASS — no overpromise patterns detected.")
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
            out.append(f"  line {f.line}:{f.column}  {f.code}")
            out.append(f"    matched: {f.matched_text}")
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
    p.add_argument("file", help="Markdown file to lint, or '-' for stdin")
    p.add_argument("--strict", action="store_true",
                   help="Don't downgrade severity when backing language is nearby")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
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
            print(f"error: cannot read: {e}", file=sys.stderr)
            return 2
        source = str(path)

    findings = lint_text(text, args.strict)

    if args.json:
        out = {
            "validator": "check-overpromise",
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

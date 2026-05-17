#!/usr/bin/env python3
"""
plan-lint.py — Mechanical validation for docs/planning/current.md.

Validates a planning/current.md file (the v4.0 current execution plan) against the
rad-planner canonical template. Catches what an LLM eyeballing the plan can miss:
missing sections, vague validation language, empty required fields, malformed
acceptance criteria.

This is the v4.0 reshape. v3.0 targeted tasks.md (a DAG). v4.0 targets
planning/current.md (a single-milestone plan with canonical sections per
docs/doc-conventions.md).

Modes:
  sections   Required sections present; non-empty bodies.
  checklist  Field-level — acceptance criteria checkbox format, validation
             commands look runnable, vague-language detection in critical fields.
  status     Acceptance-criteria progress (% complete by checkbox state).
  all        sections + checklist.

Usage:
  python3 plan-lint.py --mode sections docs/planning/current.md
  python3 plan-lint.py --mode all docs/planning/current.md --json
  python3 plan-lint.py --mode status docs/planning/current.md

Input format: see docs/doc-conventions.md `planning/current.md` template.

Output:
  Default — human-readable text. Exit 1 if CRITICAL or HIGH issues, else 0.
  --json   — single JSON object on stdout for skill consumption.
  Exit 2  — script errors (file not found, parse failure beyond recovery).

MEDIUM and LOW issues surface but do not fail the validator. Per the M6 contract,
plan-lint exit 1 means "user attention required before /plan completes."

No third-party dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Canonical from docs/doc-conventions.md planning/current.md template.
# Guardrails + User-visible behavior added in v4.6 (build-readiness gate
# milestone schema extension — questions 6 and 7 of the framework).
REQUIRED_SECTIONS = (
    "Objective",
    "Current milestone",
    "Acceptance criteria",
    "Validation commands",
    "Guardrails",
    "User-visible behavior",
    "Stop conditions",
    "Notes for the next session",
)

RECOMMENDED_SECTIONS = (
    "Why this matters",
    "Non-goals",
    "Planned changes",
    "Open questions",
    "Risks",
)

VAGUE_PHRASES = (
    "verify it works",
    "verify that it works",
    "check that it works",
    "make sure it runs",
    "make sure it works",
    "ensure functionality",
    "ensure it works",
    "confirm it's working",
    "confirm it is working",
    "test it manually",
    "looks right",
    "looks good",
    "should work",
    "tbd",
    "to be determined",
)

# Placeholder content patterns — empty bracketed text from templates
PLACEHOLDER_PATTERNS = (
    re.compile(r"^\s*\[[A-Za-z][^]]*\]\s*$"),  # [Single clear outcome]
    re.compile(r"^\s*\.\.\.\s*$"),               # ...
)

SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$")
CHECKBOX = re.compile(r"^\s*-\s*\[(?P<box>[ x])\]\s*(?P<text>.+?)\s*$")
BULLET = re.compile(r"^\s*-\s+(?P<text>.+?)\s*$")
CODE_BLOCK = re.compile(r"`(?P<cmd>[^`]+)`")


@dataclass
class Section:
    name: str
    line: int  # 1-indexed line of the heading
    body_lines: list[str] = field(default_factory=list)

    @property
    def body(self) -> str:
        return "\n".join(self.body_lines).strip()

    @property
    def is_empty(self) -> bool:
        body = self.body
        if not body:
            return True
        # Body is just a placeholder like [Single clear outcome] or ...
        non_empty_lines = [ln for ln in body.splitlines() if ln.strip()]
        if not non_empty_lines:
            return True
        all_placeholders = all(
            any(p.match(ln) for p in PLACEHOLDER_PATTERNS)
            for ln in non_empty_lines
        )
        return all_placeholders

    def bullets(self) -> list[tuple[int, str]]:
        """Return (line_number, text) for each bullet line, excluding checkboxes."""
        result = []
        for i, line in enumerate(self.body_lines):
            if CHECKBOX.match(line):
                continue
            m = BULLET.match(line)
            if m:
                result.append((self.line + i + 1, m.group("text").strip()))
        return result

    def checkboxes(self) -> list[tuple[int, bool, str]]:
        """Return (line_number, is_checked, text) for each checkbox line."""
        result = []
        for i, line in enumerate(self.body_lines):
            m = CHECKBOX.match(line)
            if m:
                result.append((self.line + i + 1, m.group("box") == "x", m.group("text").strip()))
        return result


@dataclass
class Issue:
    severity: str   # CRITICAL | HIGH | MEDIUM | LOW
    category: str   # sections | checklist | status
    section: str | None
    message: str
    fix: str

    def to_dict(self) -> dict:
        return asdict(self)


# ---------- parsing ----------


def parse_sections(text: str) -> dict[str, Section]:
    """Parse a current.md into named sections keyed by H2 heading."""
    sections: dict[str, Section] = {}
    current: Section | None = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        m = SECTION_HEADING.match(raw)
        if m:
            name = m.group(1).strip()
            current = Section(name=name, line=lineno)
            sections[name] = current
            continue
        # H1 ends any current section (don't follow into another H1's body)
        if raw.startswith("# ") and current is not None:
            current = None
            continue
        if current is None:
            continue
        current.body_lines.append(raw)

    return sections


# ---------- checks ----------


def check_sections(sections: dict[str, Section]) -> list[Issue]:
    """Required and recommended sections present and non-empty."""
    issues: list[Issue] = []

    for req in REQUIRED_SECTIONS:
        if req not in sections:
            issues.append(Issue(
                severity="CRITICAL",
                category="sections",
                section=req,
                message=f"Missing required section: '## {req}'",
                fix=f"Add a '## {req}' section per docs/doc-conventions.md planning/current.md template",
            ))
        elif sections[req].is_empty:
            issues.append(Issue(
                severity="HIGH",
                category="sections",
                section=req,
                message=f"Required section '## {req}' is empty or has only placeholder content",
                fix=f"Populate '## {req}' with project-specific content",
            ))

    for rec in RECOMMENDED_SECTIONS:
        if rec not in sections:
            issues.append(Issue(
                severity="LOW",
                category="sections",
                section=rec,
                message=f"Recommended section missing: '## {rec}'",
                fix=f"Consider adding '## {rec}' — optional but recommended for non-trivial plans",
            ))

    return issues


def _scan_vague(text: str) -> str | None:
    """Return the first vague phrase found in text, or None."""
    lower = text.lower()
    for phrase in VAGUE_PHRASES:
        if phrase in lower:
            return phrase
    return None


def check_checklist(sections: dict[str, Section]) -> list[Issue]:
    """Field-level constraints — checkbox format, runnable commands, vague language."""
    issues: list[Issue] = []

    # Acceptance criteria — checkbox format with concrete content
    if "Acceptance criteria" in sections:
        ac = sections["Acceptance criteria"]
        bullets = ac.bullets()
        checkboxes = ac.checkboxes()

        if not checkboxes and bullets:
            issues.append(Issue(
                severity="HIGH",
                category="checklist",
                section="Acceptance criteria",
                message="Acceptance criteria uses bullets but not checkboxes",
                fix="Use checkbox format: '- [ ] criterion' so progress is trackable",
            ))
        elif not checkboxes and not bullets:
            issues.append(Issue(
                severity="HIGH",
                category="checklist",
                section="Acceptance criteria",
                message="Acceptance criteria section has no checkbox entries",
                fix="Add at least one acceptance criterion as '- [ ] criterion text'",
            ))

        # Scan both checkboxes and bullets for vague language. If acceptance criteria
        # was written as bullets (already flagged above), we still want to catch
        # vague text in those bullets.
        items_to_scan: list[tuple[int, str]] = (
            [(ln, txt) for ln, _checked, txt in checkboxes]
            if checkboxes
            else [(ln, txt) for ln, txt in bullets]
        )
        for line, text in items_to_scan:
            phrase = _scan_vague(text)
            if phrase:
                issues.append(Issue(
                    severity="HIGH",
                    category="checklist",
                    section="Acceptance criteria",
                    message=f"Acceptance criterion at line {line} contains vague phrase: '{phrase}'",
                    fix="Replace with a specific, verifiable condition",
                ))

    # Validation commands — runnable shape, no vague language
    if "Validation commands" in sections:
        vc = sections["Validation commands"]
        bullets = vc.bullets()

        if not bullets:
            issues.append(Issue(
                severity="HIGH",
                category="checklist",
                section="Validation commands",
                message="Validation commands section has no entries",
                fix="Add at least one runnable command as '- `command`'",
            ))

        for line, text in bullets:
            phrase = _scan_vague(text)
            if phrase:
                issues.append(Issue(
                    severity="HIGH",
                    category="checklist",
                    section="Validation commands",
                    message=f"Validation at line {line} contains vague phrase: '{phrase}'",
                    fix="Replace with a concrete shell command in backticks",
                ))
                continue
            # Heuristic: a real command either contains backticks OR a shell-ish token
            if not CODE_BLOCK.search(text) and len(text) < 8:
                issues.append(Issue(
                    severity="MEDIUM",
                    category="checklist",
                    section="Validation commands",
                    message=f"Validation at line {line} looks too short to be runnable: '{text}'",
                    fix="Provide an exact command (e.g., `npm test`) or a clearly verifiable condition",
                ))

    # Stop conditions — non-empty
    if "Stop conditions" in sections:
        sc = sections["Stop conditions"]
        bullets = sc.bullets()
        if not bullets:
            issues.append(Issue(
                severity="MEDIUM",
                category="checklist",
                section="Stop conditions",
                message="Stop conditions section has no entries",
                fix="Add bullets per docs/doc-conventions.md template (scope expand, dep add, schema change, etc.)",
            ))

    # Notes for the next session — non-empty
    if "Notes for the next session" in sections:
        notes = sections["Notes for the next session"]
        if notes.is_empty:
            issues.append(Issue(
                severity="MEDIUM",
                category="checklist",
                section="Notes for the next session",
                message="Notes for the next session is empty",
                fix="Document most-likely next step, files likely to change, what must remain true",
            ))

    # Objective — single coherent sentence/paragraph
    if "Objective" in sections:
        obj = sections["Objective"]
        if not obj.is_empty:
            body = obj.body
            if len(body) < 20:
                issues.append(Issue(
                    severity="MEDIUM",
                    category="checklist",
                    section="Objective",
                    message=f"Objective is suspiciously short ({len(body)} chars)",
                    fix="State the milestone outcome in one clear sentence",
                ))
            phrase = _scan_vague(body)
            if phrase:
                issues.append(Issue(
                    severity="MEDIUM",
                    category="checklist",
                    section="Objective",
                    message=f"Objective contains vague phrase: '{phrase}'",
                    fix="State the objective concretely — what concrete outcome defines done",
                ))

    return issues


def status_report(sections: dict[str, Section]) -> dict:
    """Acceptance-criteria progress."""
    if "Acceptance criteria" not in sections:
        return {
            "acceptance_criteria": "section missing",
            "completed": 0,
            "total": 0,
            "percent_complete": 0.0,
            "current_milestone": "",
            "pending": [],
        }

    checkboxes = sections["Acceptance criteria"].checkboxes()
    if not checkboxes:
        return {
            "acceptance_criteria": "no checkboxes",
            "completed": 0,
            "total": 0,
            "percent_complete": 0.0,
            "current_milestone": "",
            "pending": [],
        }

    completed = sum(1 for _, checked, _ in checkboxes if checked)
    total = len(checkboxes)
    pct = round(100 * completed / total, 1) if total else 0.0

    milestone = sections.get("Current milestone")
    milestone_text = milestone.body if milestone else "(no Current milestone section)"

    return {
        "current_milestone": milestone_text[:120],
        "acceptance_criteria": "tracked",
        "completed": completed,
        "total": total,
        "percent_complete": pct,
        "pending": [text for _, checked, text in checkboxes if not checked],
    }


# ---------- output ----------


def render_text(report: dict, mode: str) -> str:
    lines: list[str] = []
    lines.append(f"plan-lint: mode={mode}  file={report['file']}")
    lines.append(f"sections parsed: {report['section_count']}")

    if mode == "status":
        s = report["status"]
        lines.append("")
        lines.append(f"Current milestone: {s.get('current_milestone', '(unknown)')}")
        lines.append(f"Acceptance criteria progress: {s['completed']}/{s['total']} ({s['percent_complete']}%)")
        pending = s.get("pending", [])
        if pending:
            lines.append("Pending criteria:")
            for p in pending[:10]:
                lines.append(f"  - {p}")
            if len(pending) > 10:
                lines.append(f"  ... and {len(pending) - 10} more")
        return "\n".join(lines)

    issues = report["issues"]
    if not issues:
        lines.append("")
        lines.append("OK — no issues found.")
        return "\n".join(lines)

    by_severity: dict[str, list[dict]] = {}
    for i in issues:
        by_severity.setdefault(i["severity"], []).append(i)

    lines.append("")
    severity_summary = ", ".join(
        f"{sev}: {len(by_severity[sev])}"
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        if sev in by_severity
    )
    lines.append(f"Issues: {len(issues)} total — {severity_summary}")
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        for i in by_severity.get(sev, []):
            tag = f"[{i['section']}]" if i["section"] else "[plan-level]"
            lines.append(f"  {sev} {tag} ({i['category']}) {i['message']}")
            lines.append(f"      fix: {i['fix']}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("path", help="Path to docs/planning/current.md")
    p.add_argument(
        "--mode",
        choices=("sections", "checklist", "status", "all"),
        default="all",
    )
    p.add_argument("--json", action="store_true", help="Emit a single JSON object instead of text")
    args = p.parse_args(argv)

    file_path = Path(args.path)
    if not file_path.exists():
        print(f"error: file not found: {file_path}", file=sys.stderr)
        return 2

    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"error: failed to read {file_path}: {e}", file=sys.stderr)
        return 2

    sections = parse_sections(text)

    issues: list[Issue] = []
    if args.mode in ("sections", "all"):
        issues.extend(check_sections(sections))
    if args.mode in ("checklist", "all"):
        issues.extend(check_checklist(sections))

    report: dict = {
        "file": str(file_path),
        "mode": args.mode,
        "section_count": len(sections),
        "section_names": list(sections.keys()),
        "issues": [i.to_dict() for i in issues],
    }
    if args.mode == "status":
        report["status"] = status_report(sections)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report, args.mode))

    if args.mode == "status":
        return 0
    # Exit 1 only on CRITICAL or HIGH — MEDIUM/LOW are warnings that surface but don't fail
    fail = any(i.severity in ("CRITICAL", "HIGH") for i in issues)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""
plan-lint.py — Mechanical validation for docs/plan.md.

Validates the single-file plan rad-planner emits against the structure in
references/plan-template.md. Catches what an LLM eyeballing the plan can miss:
missing required sections, tasks missing any of the six required fields,
unresolved or cyclic task dependencies, and vague language in the fields that
must be concrete.

This is the v5.0 reshape. v4.x targeted docs/planning/current.md (an 8-section
schema with acceptance-criteria checkboxes and an embedded session contract).
v5.0 targets one plan.md whose tasks each carry: Objective, Files, Depends on,
Done when, Validate, Rollback.

Usage:
  python3 plan-lint.py docs/plan.md
  python3 plan-lint.py docs/plan.md --json

Output:
  Default — human-readable text. Exit 1 if CRITICAL or HIGH issues, else 0.
  --json   — single JSON object on stdout for skill consumption.
  Exit 2  — script errors (file not found, parse failure beyond recovery).

MEDIUM and LOW issues surface but do not fail the validator.

No third-party dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Required H2 sections per references/plan-template.md. "Stack" is conditional
# (only when a stack evaluation ran), so it is recommended, not required.
REQUIRED_SECTIONS = (
    "Objective",
    "Scope",
    "Key assumptions",
    "Milestones",
    "Tasks",
    "Checkpoints",
    "Risks & mitigations",
    "Validation",
    "Stop conditions",
)

RECOMMENDED_SECTIONS = (
    "Stack",
)

# The six fields every task in ## Tasks must carry.
REQUIRED_TASK_FIELDS = (
    "Objective",
    "Files",
    "Depends on",
    "Done when",
    "Validate",
    "Rollback",
)

# Fields whose values must be concrete (no hand-waving).
VAGUE_SCAN_FIELDS = ("Done when", "Validate")

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

PLACEHOLDER_PATTERNS = (
    re.compile(r"^\s*\[[A-Za-z][^]]*\]\s*$"),  # [Single clear outcome]
    re.compile(r"^\s*\.\.\.\s*$"),               # ...
)

SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$")
# Task header bullet: `- **T1 — title**` (em-dash or hyphen; title optional).
TASK_HEADER = re.compile(
    r"^\s*-\s*\*\*\s*(?P<id>T\d+(?:\.\d+)?)\b[^*]*\*\*\s*$"
)
# Field bullet under a task: `  - **Objective:** value`.
FIELD_BULLET = re.compile(
    r"^\s*-\s*\*\*(?P<label>[^*:]+?):\*\*\s*(?P<value>.*?)\s*$"
)
BULLET = re.compile(r"^\s*-\s+(?P<text>.+?)\s*$")
TASK_REF = re.compile(r"\bT\d+(?:\.\d+)?\b")


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
        non_empty = [ln for ln in body.splitlines() if ln.strip()]
        if not non_empty:
            return True
        return all(
            any(p.match(ln) for p in PLACEHOLDER_PATTERNS) for ln in non_empty
        )


@dataclass
class Task:
    task_id: str
    line: int
    fields: dict[str, str] = field(default_factory=dict)  # lowercased label -> value


@dataclass
class Issue:
    severity: str   # CRITICAL | HIGH | MEDIUM | LOW
    category: str   # sections | tasks | dependencies | vague
    section: str | None
    message: str
    fix: str

    def to_dict(self) -> dict:
        return asdict(self)


# ---------- parsing ----------


def parse_sections(text: str) -> dict[str, Section]:
    """Parse plan.md into named sections keyed by H2 heading."""
    sections: dict[str, Section] = {}
    current: Section | None = None
    for lineno, raw in enumerate(text.splitlines(), start=1):
        m = SECTION_HEADING.match(raw)
        if m:
            current = Section(name=m.group(1).strip(), line=lineno)
            sections[current.name] = current
            continue
        if raw.startswith("# ") and current is not None:
            current = None
            continue
        if current is not None:
            current.body_lines.append(raw)
    return sections


def parse_tasks(section: Section) -> list[Task]:
    """Parse tasks from the ## Tasks section body. A task starts at a `- **Tn**`
    header bullet; subsequent `- **Field:** value` bullets are its fields until
    the next task header."""
    tasks: list[Task] = []
    current: Task | None = None
    for i, raw in enumerate(section.body_lines):
        lineno = section.line + i + 1
        header = TASK_HEADER.match(raw)
        if header:
            current = Task(task_id=header.group("id"), line=lineno)
            tasks.append(current)
            continue
        if current is None:
            continue
        fm = FIELD_BULLET.match(raw)
        if fm:
            current.fields[fm.group("label").strip().lower()] = fm.group("value").strip()
    return tasks


# ---------- checks ----------


def check_sections(sections: dict[str, Section]) -> list[Issue]:
    issues: list[Issue] = []
    for req in REQUIRED_SECTIONS:
        if req not in sections:
            issues.append(Issue(
                "CRITICAL", "sections", req,
                f"Missing required section: '## {req}'",
                f"Add a '## {req}' section per references/plan-template.md",
            ))
        elif sections[req].is_empty:
            issues.append(Issue(
                "HIGH", "sections", req,
                f"Required section '## {req}' is empty or placeholder-only",
                f"Populate '## {req}' with project-specific content",
            ))
    for rec in RECOMMENDED_SECTIONS:
        if rec not in sections and rec == "Stack":
            issues.append(Issue(
                "LOW", "sections", rec,
                "No '## Stack' section — expected when a stack evaluation ran",
                "Add '## Stack' if a stack decision was made; otherwise ignore",
            ))
    return issues


def _scan_vague(text: str) -> str | None:
    lower = text.lower()
    for phrase in VAGUE_PHRASES:
        if phrase in lower:
            return phrase
    return None


def check_tasks(tasks: list[Task], has_tasks_section: bool) -> list[Issue]:
    issues: list[Issue] = []
    if has_tasks_section and not tasks:
        issues.append(Issue(
            "CRITICAL", "tasks", "Tasks",
            "The '## Tasks' section has no parseable tasks",
            "Add tasks as '- **T1 — title**' with the six required field bullets",
        ))
        return issues

    seen_ids: set[str] = set()
    for task in tasks:
        tag = task.task_id
        if task.task_id in seen_ids:
            issues.append(Issue(
                "HIGH", "tasks", tag,
                f"Duplicate task ID '{task.task_id}' (line {task.line})",
                "Give each task a unique ID (T1, T2, ...)",
            ))
        seen_ids.add(task.task_id)

        for req in REQUIRED_TASK_FIELDS:
            key = req.lower()
            if key not in task.fields:
                issues.append(Issue(
                    "HIGH", "tasks", tag,
                    f"Task {task.task_id} missing required field: '{req}'",
                    f"Add '- **{req}:** <value>' under task {task.task_id}",
                ))
                continue
            value = task.fields[key]
            if not value or value in ("-", "TBD", "tbd", "...", "[ ]"):
                issues.append(Issue(
                    "HIGH", "tasks", tag,
                    f"Task {task.task_id} field '{req}' is empty or placeholder",
                    f"Populate '- **{req}:** <value>' for task {task.task_id}",
                ))

        for fld in VAGUE_SCAN_FIELDS:
            value = task.fields.get(fld.lower(), "")
            phrase = _scan_vague(value)
            if phrase:
                issues.append(Issue(
                    "HIGH", "vague", tag,
                    f"Task {task.task_id} field '{fld}' contains vague phrase: '{phrase}'",
                    "Replace with a concrete, verifiable command or condition",
                ))
    return issues


def check_dependencies(tasks: list[Task]) -> list[Issue]:
    """Referenced task IDs must exist (no phantoms); the graph must be acyclic."""
    issues: list[Issue] = []
    ids = {t.task_id for t in tasks}
    graph: dict[str, list[str]] = {}

    for task in tasks:
        raw = task.fields.get("depends on", "")
        refs = TASK_REF.findall(raw)
        # "none" with no refs is valid; refs alongside "none" is contradictory but
        # we just honor the refs.
        deps: list[str] = []
        for ref in refs:
            if ref == task.task_id:
                issues.append(Issue(
                    "HIGH", "dependencies", task.task_id,
                    f"Task {task.task_id} depends on itself",
                    f"Remove the self-reference in task {task.task_id}'s 'Depends on'",
                ))
                continue
            if ref not in ids:
                issues.append(Issue(
                    "HIGH", "dependencies", task.task_id,
                    f"Task {task.task_id} depends on '{ref}', which is not a defined task",
                    f"Reference an existing task ID or remove '{ref}'",
                ))
                continue
            deps.append(ref)
        graph[task.task_id] = deps

    # Cycle detection (DFS with colors).
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in graph}
    cycle_reported: set[frozenset] = set()

    def visit(node: str, stack: list[str]) -> None:
        color[node] = GRAY
        stack.append(node)
        for dep in graph.get(node, []):
            if color.get(dep) == GRAY:
                cyc = stack[stack.index(dep):] + [dep]
                key = frozenset(cyc)
                if key not in cycle_reported:
                    cycle_reported.add(key)
                    issues.append(Issue(
                        "CRITICAL", "dependencies", node,
                        "Dependency cycle: " + " -> ".join(cyc),
                        "Break the cycle — tasks cannot mutually depend on each other",
                    ))
            elif color.get(dep) == WHITE:
                visit(dep, stack)
        stack.pop()
        color[node] = BLACK

    for tid in graph:
        if color[tid] == WHITE:
            visit(tid, [])

    return issues


# ---------- output ----------


def render_text(report: dict) -> str:
    lines = [
        f"plan-lint: file={report['file']}",
        f"sections parsed: {report['section_count']}  tasks parsed: {report['task_count']}",
    ]
    issues = report["issues"]
    if not issues:
        lines += ["", "OK — no issues found."]
        return "\n".join(lines)

    by_sev: dict[str, list[dict]] = {}
    for i in issues:
        by_sev.setdefault(i["severity"], []).append(i)
    summary = ", ".join(
        f"{sev}: {len(by_sev[sev])}"
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW") if sev in by_sev
    )
    lines += ["", f"Issues: {len(issues)} total — {summary}"]
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        for i in by_sev.get(sev, []):
            tag = f"[{i['section']}]" if i["section"] else "[plan-level]"
            lines.append(f"  {sev} {tag} ({i['category']}) {i['message']}")
            lines.append(f"      fix: {i['fix']}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("path", help="Path to docs/plan.md")
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
    tasks = parse_tasks(sections["Tasks"]) if "Tasks" in sections else []

    issues: list[Issue] = []
    issues.extend(check_sections(sections))
    issues.extend(check_tasks(tasks, "Tasks" in sections))
    issues.extend(check_dependencies(tasks))

    report = {
        "file": str(file_path),
        "section_count": len(sections),
        "section_names": list(sections.keys()),
        "task_count": len(tasks),
        "issues": [i.to_dict() for i in issues],
    }

    print(json.dumps(report, indent=2) if args.json else render_text(report))

    return 1 if any(i.severity in ("CRITICAL", "HIGH") for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

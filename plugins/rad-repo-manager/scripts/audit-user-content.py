#!/usr/bin/env python3
"""
audit-user-content.py — visibility pass over user-owned operating-manual sections.

The sectioned-writer rule keeps rad-planner and rad-session from modifying
user-authored content. This validator adds the missing visibility layer:
flag user-owned sections that look stale or refer to things that don't
exist, without ever modifying them.

Findings are advisory. Never auto-applied. The user decides what to do.

Heuristics in v1:

  1. Orphan terminology
     Title-Case multi-word phrases (likely named systems, design directions,
     branded concepts) that appear in a user-owned section but nowhere else
     in the project — `docs/`, `README.md`, source code, ADRs. Often a
     signal the term is stale (the brand was renamed, the system retired)
     but the operating manual didn't get the memo.

  2. Dead file paths
     Markdown links `[text](path)` and bare path-like tokens in user-owned
     sections that reference files which don't exist on disk. Common after
     refactors that move or rename files without updating the operating
     manual.

Operating manuals checked: CLAUDE.md, AGENTS.md (whichever or both exist
in the project root). User-owned sections are top-level `## X` headings
whose name is NOT in the plugin-owned set.

Usage:
  python3 audit-user-content.py <project-dir>
  python3 audit-user-content.py <project-dir> --json
  python3 audit-user-content.py <project-dir> --min-orphan-words 3
  python3 audit-user-content.py <project-dir> --min-orphan-occurrences 2

Exit codes:
  0 — no findings, or only INFO-level findings
  1 — at least one HIGH or MEDIUM finding (advisory; up to the caller
      whether to gate on this)
  2 — script error (file not readable, etc.)

Pure stdlib, Python 3.8+. No git dependency required (works on a directory
that isn't a git repo, just walks the filesystem).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Operational sections owned by rad-repo-manager's AGENTS.md template. These are
# structural — they legitimately list conditional reference paths that may not exist
# yet — so they are exempt from the user-content staleness audit. Everything else in
# AGENTS.md is user-authored and falls under this audit.
PLUGIN_OWNED_SECTIONS = frozenset({
    # rad-repo-manager operating-manual structure
    "active source of truth",
    "agent work modes",
    "documentation rules",
    "definition of done",
    # legacy variants (harmless to keep recognized)
    "project", "read order", "hard boundaries", "engineering rules",
    "lanes", "escalate triggers", "escalate instead of guessing",
    "commands", "compact instructions", "claude-specific behavior",
    "agent operating manual",
})

# Directories to skip when scanning the repo for orphan-terminology matches.
SKIP_DIRS = frozenset({
    ".git", ".rad", ".rad-archive", ".planner",
    "node_modules", ".venv", "venv", "__pycache__",
    "dist", "build", "target", ".pytest_cache",
    ".next", ".turbo", ".cache", ".astro",
})

# File extensions counted as project content for the orphan-terminology corpus
CORPUS_EXTENSIONS = frozenset({
    ".md", ".mdx", ".txt", ".rst",
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".go", ".rs", ".java", ".rb", ".php",
    ".json", ".yaml", ".yml", ".toml",
    ".html", ".css", ".scss",
})

SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$")
# Title-Case phrase: 2+ consecutive Title-Case words. Allow hyphens/apostrophes.
# Examples that match: "Digital Diorama", "Grounded Naturalist", "Read Order",
# "PARA Method", "Engineering Rules"
TITLE_CASE_PHRASE = re.compile(
    r"\b([A-Z][a-zA-Z0-9'-]+(?:\s+[A-Z][a-zA-Z0-9'-]+){1,4})\b"
)
# Leading articles to strip from matched phrases so "The Digital Diorama" and
# "Digital Diorama" count as the same conceptual reference.
LEADING_ARTICLES = ("The ", "A ", "An ", "Our ", "My ")
# Markdown link path: [text](path) where path looks like a relative file path
MD_LINK_PATH = re.compile(r"\[[^\]]+\]\(([^)#]+?)(?:#[^)]*)?\)")
# Bare path-ish token: must contain at least one slash or backslash to count as
# a "path." Single-segment filenames like `SKILL.md` mentioned generically in
# prose are too noisy to flag without a separator.
BARE_PATH = re.compile(
    r"(?<![/\w:])([a-zA-Z0-9_.][a-zA-Z0-9_./\\-]*[/\\][a-zA-Z0-9_./\\-]*\.[a-zA-Z]{1,5})\b"
)
# Domain-like extensions — exempt if the "path" has no separator (a domain
# without /path is a brand reference, not a filesystem path)
DOMAIN_LIKE_EXTENSIONS = frozenset({".ai", ".com", ".io", ".dev", ".org", ".net", ".co"})
# Template-placeholder markers — exempt paths containing these (they're patterns,
# not concrete references)
TEMPLATE_PLACEHOLDER_MARKERS = ("<", ">", "{", "}", "YYYY", "MM-DD", "NNNN", "<name>")
# Inline-code spans inside a line — we don't suppress paths in them by default
# (a backticked path can still be a real reference) but we do skip when paired
# with template placeholder markers.
INLINE_CODE = re.compile(r"`([^`]+)`")
# Common false-positive phrases that shouldn't count as orphan-terminology
# even if they appear only in user-owned sections (they're generic English)
GENERIC_TITLE_CASE = frozenset({
    "table of contents", "see also", "for example", "note that",
    "if you", "this is", "do not", "to do",
    # Common section-header words that the validator might pick up
    "read order", "hard boundaries", "engineering rules",
    "definition of done", "escalate triggers", "compact instructions",
})


@dataclass
class Section:
    name: str
    line_start: int
    body_lines: list[str] = field(default_factory=list)

    @property
    def name_lower(self) -> str:
        return self.name.lower().strip()

    @property
    def body_text(self) -> str:
        return "\n".join(self.body_lines)

    @property
    def is_user_owned(self) -> bool:
        return self.name_lower not in PLUGIN_OWNED_SECTIONS


@dataclass
class Finding:
    severity: str   # HIGH | MEDIUM | LOW | INFO
    category: str   # orphan-terminology | dead-path
    file: str
    section: str
    line: int
    message: str
    evidence: str
    fix: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Report:
    project_dir: str
    files_audited: list[str] = field(default_factory=list)
    user_owned_sections: list[dict] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_dir": self.project_dir,
            "files_audited": self.files_audited,
            "user_owned_sections": self.user_owned_sections,
            "findings": [f.to_dict() for f in self.findings],
            "notes": self.notes,
        }


def parse_sections(text: str) -> list[Section]:
    """Parse `## X` top-level sections from a markdown file."""
    sections: list[Section] = []
    current: Section | None = None
    for lineno, raw in enumerate(text.splitlines(), start=1):
        m = SECTION_HEADING.match(raw)
        if m:
            if current is not None:
                sections.append(current)
            current = Section(name=m.group(1).strip(), line_start=lineno)
            continue
        if raw.startswith("# "):
            if current is not None:
                sections.append(current)
                current = None
            continue
        if current is not None:
            current.body_lines.append(raw)
    if current is not None:
        sections.append(current)
    return sections


def _build_repo_corpus(project_dir: Path, exclude_path: Path) -> str:
    """Concatenate text content of relevant repo files for orphan-term lookup.
    Excludes the operating manual being audited (orphan = appears nowhere ELSE)."""
    chunks: list[str] = []
    try:
        exclude_resolved = exclude_path.resolve()
    except OSError:
        exclude_resolved = exclude_path

    for p in project_dir.rglob("*"):
        if not p.is_file():
            continue
        # Skip dirs in SKIP_DIRS at any depth
        rel = p.relative_to(project_dir)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.suffix.lower() not in CORPUS_EXTENSIONS:
            continue
        try:
            if p.resolve() == exclude_resolved:
                continue
        except OSError:
            continue
        try:
            chunks.append(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def check_orphan_terminology(
    section: Section,
    op_manual_path: Path,
    corpus: str,
    min_words: int,
    min_occurrences: int,
) -> list[Finding]:
    """Flag Title-Case phrases that appear in the section but nowhere else
    in the project corpus."""
    findings: list[Finding] = []

    body = section.body_text
    # Count phrases in this section
    section_counts: dict[str, int] = {}
    for m in TITLE_CASE_PHRASE.finditer(body):
        phrase = m.group(1).strip()
        # Strip leading articles so "The X" and "X" count as the same concept
        for article in LEADING_ARTICLES:
            if phrase.startswith(article):
                phrase = phrase[len(article):]
                break
        word_count = len(phrase.split())
        if word_count < min_words:
            continue
        if phrase.lower() in GENERIC_TITLE_CASE:
            continue
        section_counts[phrase] = section_counts.get(phrase, 0) + 1

    # Filter to phrases with enough occurrences in the section to be load-bearing
    candidates = {
        phrase: count
        for phrase, count in section_counts.items()
        if count >= min_occurrences
    }

    # For each candidate, check if it appears in the corpus
    for phrase, count in sorted(candidates.items(), key=lambda kv: -kv[1]):
        # Use case-sensitive exact-phrase search in corpus
        if phrase in corpus:
            continue
        # Try case-insensitive fallback to avoid false positives on case-variant matches
        if phrase.lower() in corpus.lower():
            continue
        # Find approximate line of first occurrence in section body
        approx_line = section.line_start + 1
        for i, line in enumerate(section.body_lines):
            if phrase in line:
                approx_line = section.line_start + i + 1
                break
        findings.append(Finding(
            severity="MEDIUM",
            category="orphan-terminology",
            file=str(op_manual_path),
            section=section.name,
            line=approx_line,
            message=(
                f"'{phrase}' appears {count}x in this section but nowhere "
                f"else in the project — likely stale terminology"
            ),
            evidence=phrase,
            fix=(
                "Either reference the term in a current doc "
                "(docs/prd.md, docs/plan.md, a reference doc) to anchor "
                "it, or remove the section if the concept was retired"
            ),
        ))

    return findings


def _looks_like_real_path(path_text: str) -> bool:
    """Filter heuristic — does this token plausibly reference a file on disk?"""
    if not path_text:
        return False
    # URLs, anchors, mail
    if path_text.startswith(("http://", "https://", "mailto:", "#", "ftp://")):
        return False
    # Whitespace-bearing tokens are almost never literal paths
    if " " in path_text:
        return False
    # Template placeholders — not concrete references
    if any(marker in path_text for marker in TEMPLATE_PLACEHOLDER_MARKERS):
        return False
    # Pure dotfile or relative-marker that isn't actually a path
    if path_text in (".", "..", "./", "../"):
        return False
    # Domain-like (`Claude.ai`, `example.com`) — extension that's a TLD AND
    # no path separator. Brand reference, not file.
    has_sep = "/" in path_text or "\\" in path_text
    if not has_sep:
        # Single-segment file references without separator — usually generic
        # ("SKILL.md", "plugin.json" mentioned as a kind of file). The regex
        # already requires a separator for BARE_PATH, but MD_LINK_PATH can
        # produce these. Skip them.
        return False
    # Last component must end in a real-looking extension
    last = path_text.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." not in last:
        # No extension on the last component — could be a directory ref;
        # we don't flag bare directory refs to keep noise down
        return False
    ext = "." + last.rsplit(".", 1)[-1].lower()
    if ext in DOMAIN_LIKE_EXTENSIONS:
        return False
    return True


def check_dead_paths(
    section: Section,
    op_manual_path: Path,
    project_dir: Path,
) -> list[Finding]:
    """Flag markdown link paths and bare path tokens that don't resolve."""
    findings: list[Finding] = []
    seen: set[str] = set()

    for offset, line in enumerate(section.body_lines):
        line_num = section.line_start + offset + 1
        paths_in_line: list[str] = []

        for m in MD_LINK_PATH.finditer(line):
            paths_in_line.append(m.group(1).strip())
        for m in BARE_PATH.finditer(line):
            paths_in_line.append(m.group(1).strip())

        for path_text in paths_in_line:
            if path_text in seen:
                continue
            seen.add(path_text)
            if not _looks_like_real_path(path_text):
                continue

            # Resolve path against project root
            candidate = (project_dir / path_text).resolve()
            try:
                if candidate.exists():
                    continue
            except (OSError, ValueError):
                continue

            # Also try as if the link were anchored at the operating manual's directory
            alt = (op_manual_path.parent / path_text).resolve()
            try:
                if alt.exists():
                    continue
            except (OSError, ValueError):
                pass

            findings.append(Finding(
                severity="HIGH",
                category="dead-path",
                file=str(op_manual_path),
                section=section.name,
                line=line_num,
                message=f"Path '{path_text}' referenced but does not exist on disk",
                evidence=line.strip(),
                fix=(
                    "Either update the path to the current location, remove "
                    "the reference if the file was retired, or restore the "
                    "file if it was deleted by mistake"
                ),
            ))

    return findings


def audit_file(
    op_manual_path: Path,
    project_dir: Path,
    min_orphan_words: int,
    min_orphan_occurrences: int,
) -> tuple[list[dict], list[Finding]]:
    text = op_manual_path.read_text(encoding="utf-8", errors="replace")
    sections = parse_sections(text)
    user_owned = [s for s in sections if s.is_user_owned]

    findings: list[Finding] = []
    user_owned_summary: list[dict] = []

    if not user_owned:
        return user_owned_summary, findings

    corpus = _build_repo_corpus(project_dir, op_manual_path)

    for section in user_owned:
        user_owned_summary.append({
            "file": str(op_manual_path),
            "name": section.name,
            "line_start": section.line_start,
            "body_size_chars": len(section.body_text),
        })
        findings.extend(check_orphan_terminology(
            section, op_manual_path, corpus,
            min_orphan_words, min_orphan_occurrences,
        ))
        findings.extend(check_dead_paths(section, op_manual_path, project_dir))

    return user_owned_summary, findings


def render_text(report: Report) -> str:
    lines = [f"audit-user-content: {report.project_dir}"]
    lines.append(f"  files audited: {', '.join(report.files_audited) or '(none found)'}")
    lines.append(f"  user-owned sections: {len(report.user_owned_sections)}")
    for note in report.notes:
        lines.append(f"  note: {note}")
    lines.append("")

    if not report.findings:
        lines.append("OK — no orphan terminology or dead paths flagged in user-owned sections.")
        return "\n".join(lines)

    by_sev: dict[str, list[Finding]] = {}
    for f in report.findings:
        by_sev.setdefault(f.severity, []).append(f)

    summary = ", ".join(
        f"{sev}: {len(by_sev[sev])}"
        for sev in ("HIGH", "MEDIUM", "LOW", "INFO")
        if sev in by_sev
    )
    lines.append(f"Findings: {len(report.findings)} total — {summary}")
    lines.append("")
    for sev in ("HIGH", "MEDIUM", "LOW", "INFO"):
        for f in by_sev.get(sev, []):
            lines.append(
                f"  {sev} [{f.section}] ({f.category}) "
                f"{f.file}:{f.line} — {f.message}"
            )
            lines.append(f"      fix: {f.fix}")
    lines.append("")
    lines.append(
        "Advisory only. These sections are user-owned and neither plugin will "
        "modify them. Review the findings and update or remove the stale content."
    )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("project_dir", help="Project root directory")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument(
        "--min-orphan-words", type=int, default=2,
        help="Minimum word count for a Title-Case phrase to be a candidate (default: 2)",
    )
    p.add_argument(
        "--min-orphan-occurrences", type=int, default=2,
        help="Minimum occurrences in a section before flagging (default: 2)",
    )
    args = p.parse_args(argv)

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"error: project directory not found: {project_dir}", file=sys.stderr)
        return 2
    if not project_dir.is_dir():
        print(f"error: not a directory: {project_dir}", file=sys.stderr)
        return 2

    report = Report(project_dir=str(project_dir))

    op_manuals: list[Path] = []
    for name in ("CLAUDE.md", "AGENTS.md"):
        candidate = project_dir / name
        if candidate.exists():
            op_manuals.append(candidate)

    if not op_manuals:
        report.notes.append("No CLAUDE.md or AGENTS.md found at project root — audit skipped")
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(render_text(report))
        return 0

    for op_manual in op_manuals:
        report.files_audited.append(str(op_manual))
        try:
            sections, findings = audit_file(
                op_manual, project_dir,
                args.min_orphan_words, args.min_orphan_occurrences,
            )
        except OSError as e:
            report.notes.append(f"failed to read {op_manual}: {e}")
            continue
        report.user_owned_sections.extend(sections)
        report.findings.extend(findings)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render_text(report))

    fail = any(f.severity in ("HIGH", "MEDIUM") for f in report.findings)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

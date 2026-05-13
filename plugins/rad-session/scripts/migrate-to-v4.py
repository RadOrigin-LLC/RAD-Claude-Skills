#!/usr/bin/env python3
"""
migrate-to-v4.py — Migrate a project from rad-planner 2.x / rad-session 3.x to
                   the RAD 8-doc standard (rad-planner 3.0 / rad-session 4.0).

Detects and transforms in-place at the project root:

  implementation_plan.md  → split into PRD.md, ARCHITECTURE.md, ASSUMPTIONS.md,
                            DECISIONS.md, PLAN.md using v2.x section heading
                            heuristics. ASSUMPTIONS.md is created as a placeholder
                            (v2.x had no assumptions section); DECISIONS.md is
                            seeded from the "Key Design Decisions" table in
                            section 2 when present.
  HANDOFF.md (/checkpoint) → archived. Detected by template heuristics
                            (active-run field, numbered "To Resume" steps).
                            The next /rad-session:wrapup regenerates HANDOFF.md
                            from session state.
  EXECUTION-PROMPT.md     → archived. Role taken over by /rad-session:startup
                            briefing in 4.0.
  docs/ARCHITECTURE.md    → moved to ARCHITECTURE.md at project root (4.0 puts
                            all strategic docs at root). Only fires when the
                            implementation_plan.md split would NOT produce its
                            own ARCHITECTURE.md (avoid double-source conflict).
  CLAUDE.md from          → preserved as-is; CLAUDE-FRAGMENT.md generated
  generate-project-config   alongside so the next /rad-session:init merges
                            strategic-doc @-imports.

All transformed originals are archived to .rad-archive/<timestamp>/ for
rollback. A manifest.json in the archive records what was archived and where
it came from. The archive directory is added to .gitignore by default; use
`--no-gitignore` to skip that, or commit `.rad-archive/` manually if you want
it tracked.

Usage:
  python3 migrate-to-v4.py [<project-root>] [options]

Options:
  --dry-run             Show what would happen; write nothing.
  --non-interactive     Apply all safe transformations without prompts;
                        ambiguous items (e.g., unrecognized implementation_plan.md
                        structure) are recorded as warnings and skipped.
  --archive-dir <path>  Override the default .rad-archive/ location.
  --no-gitignore        Don't auto-add .rad-archive/ to .gitignore.
  --json                Emit a trailing JSON summary on stdout (implies
                        --non-interactive). Useful for autonomous runs.

Exit codes:
  0  Success — at least one transformation applied (or dry-run completed).
  1  Nothing to migrate, OR user declined all prompts, OR warnings present.
  2  Script error (project root not found, malformed inputs that couldn't
     be handled defensively, etc.).

Pure stdlib Python 3.8+. No `pip install` required.

Verify after migration:
  python3 ${rad-planner}/scripts/plan-lint.py --mode all tasks.md
  /rad-planner:plan --validate    (interactive — gap-checks the 8-doc set)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


VERSION = "1.0.0"

# ---------- Constants ----------

V2X_PLAN_FILE = "implementation_plan.md"
V2X_EXECUTION_PROMPT = "EXECUTION-PROMPT.md"
V2X_DOCS_ARCH = "docs/ARCHITECTURE.md"
V4_STRATEGIC = ["PRD.md", "ARCHITECTURE.md", "ASSUMPTIONS.md", "DECISIONS.md", "PLAN.md"]
V4_FRAGMENT = "CLAUDE-FRAGMENT.md"

# v2.x mega-doc section number → v4 destination
SECTION_DESTINATIONS = {
    "1": "PRD",                # Project Summary / Overview
    "2": "ARCHITECTURE",       # Architecture + Key Design Decisions
    "3": "ARCHITECTURE",       # Target Files (becomes a subsection)
    "4": "PLAN",               # Milestones
    "5": "PLAN",               # Implementation Steps
    "6": "PLAN",               # Checkpoints
    "7": "PLAN",               # Risks and Considerations
}

# Heuristics for distinguishing rad-planner /checkpoint HANDOFF.md from
# rad-session /wrapup HANDOFF.md. Either pattern present → likely /checkpoint.
CHECKPOINT_HANDOFF_MARKERS = [
    r"\*\*Active run:\*\*",
    r"^## To Resume\s*$",
    r"--resume <run-id>",
    r"\.planner/state/",
]

# Heuristics for distinguishing generate-project-config CLAUDE.md.
# The v2.x template was WHY/WHAT/HOW-structured "Contract of Intent."
GENERATE_PROJECT_CONFIG_MARKERS = [
    r"^## Why this project exists",
    r"^## What we are building",
    r"^## How we build",
]


# ---------- Detection ----------

def detect_artifacts(root: Path) -> dict:
    """Return what was found at the project root that needs migration."""
    plan = root / V2X_PLAN_FILE
    exec_prompt = root / V2X_EXECUTION_PROMPT
    docs_arch = root / V2X_DOCS_ARCH
    handoff = root / "HANDOFF.md"
    claude_md = root / "CLAUDE.md"

    found = {
        "implementation_plan": plan if plan.is_file() else None,
        "execution_prompt": exec_prompt if exec_prompt.is_file() else None,
        "docs_architecture": docs_arch if docs_arch.is_file() else None,
        "handoff": handoff if handoff.is_file() else None,
        "claude_md": claude_md if claude_md.is_file() else None,
    }

    # Classify HANDOFF.md
    found["handoff_is_checkpoint"] = (
        handoff.is_file() and _matches_any(_safe_read(handoff), CHECKPOINT_HANDOFF_MARKERS)
    )

    # Classify CLAUDE.md
    found["claude_md_is_generate_project_config"] = (
        claude_md.is_file() and _matches_any(_safe_read(claude_md), GENERATE_PROJECT_CONFIG_MARKERS)
    )

    # Existing v4 files (conflict signals — user already partially migrated)
    found["v4_already_present"] = [
        name for name in V4_STRATEGIC if (root / name).is_file()
    ]
    found["v4_fragment_present"] = (root / V4_FRAGMENT).is_file()

    return found


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _matches_any(text: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if re.search(pat, text, re.MULTILINE):
            return True
    return False


# ---------- Section parsing ----------

# Match `## 1. Title`, `## 2. Title`, … up to single-digit section numbers
# (v2.x template caps at 7 sections; we allow 1–9 defensively).
SECTION_RE = re.compile(r"^##\s+(\d)\.\s+(.+?)\s*$", re.MULTILINE)


def parse_sections(content: str) -> dict:
    """Split a v2.x implementation_plan.md into preamble + numbered sections.

    Returns:
      {
        "preamble": str,           # everything before the first `## N.` heading
        "preamble_meta": dict,     # parsed Status/Generated/Approved by lines
        "title": str,              # first `# Title` line if present, else ""
        "sections": {              # "1" → {"heading": str, "body": str}, ...
          "1": {"heading": "## 1. Project Summary", "body": "..."},
          ...
        },
        "unrecognized": bool,      # True if no sections were detected at all
      }
    """
    lines = content.splitlines()

    # Find all numbered-section heading positions
    section_starts = []
    for i, line in enumerate(lines):
        m = SECTION_RE.match(line)
        if m:
            section_starts.append((i, m.group(1), m.group(2), line))

    if not section_starts:
        return {
            "preamble": content,
            "preamble_meta": _parse_preamble_meta(content),
            "title": _extract_title(lines),
            "sections": {},
            "unrecognized": True,
        }

    # Preamble = everything before the first section heading
    first_start = section_starts[0][0]
    preamble_lines = lines[:first_start]
    preamble = "\n".join(preamble_lines).rstrip()

    # Each section spans from its heading to the next heading (or EOF)
    sections: dict[str, dict[str, str]] = {}
    for idx, (start_line, num, _title, heading_text) in enumerate(section_starts):
        end_line = section_starts[idx + 1][0] if idx + 1 < len(section_starts) else len(lines)
        body_lines = lines[start_line + 1 : end_line]
        sections[num] = {
            "heading": heading_text,
            "body": "\n".join(body_lines).rstrip(),
        }

    return {
        "preamble": preamble,
        "preamble_meta": _parse_preamble_meta(preamble),
        "title": _extract_title(preamble_lines),
        "sections": sections,
        "unrecognized": False,
    }


def _extract_title(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return ""


def _parse_preamble_meta(text: str) -> dict:
    """Extract `**Key:** value` metadata lines from the preamble."""
    meta = {}
    for line in text.splitlines():
        m = re.match(r"^\*\*([^*:]+):\*\*\s*(.+?)\s*$", line)
        if m:
            meta[m.group(1).strip()] = m.group(2).strip()
    return meta


# ---------- Output builders ----------

def _migration_header(source: str, today: str) -> str:
    return (
        f"<!-- Migrated from {source} by migrate-to-v4.py "
        f"v{VERSION} on {today}. Original archived under .rad-archive/. -->\n"
    )


def build_prd(parsed: dict, source_name: str, today: str) -> str:
    """PRD.md = preamble metadata + section 1 body."""
    title = parsed["title"] or "PRD"
    meta = parsed["preamble_meta"]
    body = parsed["sections"].get("1", {}).get("body", "").lstrip()

    out = [
        _migration_header(source_name, today),
        f"# PRD: {title.replace('Implementation Plan:', '').strip().rstrip(':')}",
        "",
    ]
    if meta:
        for key in ("Generated", "Status", "Approved by"):
            if key in meta:
                out.append(f"**{key}:** {meta[key]}")
        out.append("")

    if body:
        out.append(body)
    else:
        out.append("(Section 1 of the prior implementation_plan.md was empty or missing.)")
    out.append("")

    return "\n".join(out)


def build_architecture(parsed: dict, source_name: str, today: str) -> str:
    """ARCHITECTURE.md = section 2 body + section 3 as 'Target Files' subsection."""
    title = parsed["title"] or "Architecture"
    sec2 = parsed["sections"].get("2", {}).get("body", "").lstrip()
    sec3 = parsed["sections"].get("3", {}).get("body", "").lstrip()

    out = [
        _migration_header(source_name, today),
        f"# Architecture: {title.replace('Implementation Plan:', '').strip().rstrip(':')}",
        f"",
        f"**Last updated:** {today}",
        "",
    ]
    if sec2:
        out.append(sec2)
    else:
        out.append("(Section 2 of the prior implementation_plan.md was empty or missing.)")

    if sec3:
        out.extend(["", "## Target Files", "", sec3])

    out.append("")
    return "\n".join(out)


def build_assumptions(today: str) -> str:
    """Placeholder ASSUMPTIONS.md with a note pointing at /plan --reboot for refill."""
    return (
        f"<!-- Created by migrate-to-v4.py v{VERSION} on {today}. v2.x had no "
        f"assumptions section, so this file starts empty. -->\n"
        f"# Assumptions\n\n"
        f"Non-obvious truths about this project's reality that wouldn't be evident "
        f"from reading the code. Capture during planning, augment during sessions "
        f"when new assumptions surface.\n\n"
        f"When an assumption invalidates, mark it `~~Invalidated YYYY-MM-DD — "
        f"<reason>~~` rather than deleting. Audit trail matters.\n\n"
        f"## Current\n\n"
        f"<!-- v2.x did not have an explicit ASSUMPTIONS section. Run\n"
        f"     /rad-planner:plan --reboot to populate this from a fresh interview,\n"
        f"     OR add entries by hand. Examples:\n"
        f"     - [YYYY-MM-DD] No real users yet — can break compatibility freely.\n"
        f"     - [YYYY-MM-DD] Single-tenant only; multi-tenant requires schema rework.\n"
        f"     - [YYYY-MM-DD] Sensitive data — no real values in repo.\n"
        f"-->\n\n"
        f"## Invalidated\n\n"
        f"(none yet)\n"
    )


def build_decisions(parsed: dict, source_name: str, today: str) -> str:
    """DECISIONS.md from the 'Key Design Decisions' table in section 2."""
    sec2_body = parsed["sections"].get("2", {}).get("body", "")
    extracted = _extract_decisions_table(sec2_body)

    out = [
        _migration_header(source_name, today),
        "# Decisions",
        "",
        "Chronological architecture and tooling decisions. Append new entries; "
        "never delete. Sequence numbers (`NNNN`) are the cross-reference for "
        "supersession.",
        "",
    ]
    if not extracted:
        out.extend([
            "<!-- No 'Key Design Decisions' table was found in section 2 of the",
            "     prior implementation_plan.md. Add entries here as decisions are",
            "     made; /rad-planner:plan --reboot can also seed initial entries",
            "     from a fresh interview. -->",
            "",
        ])
        return "\n".join(out)

    for i, (decision, choice, rationale) in enumerate(extracted, start=1):
        seq = f"{i:04d}"
        title = decision if decision else f"Migrated decision {seq}"
        body_decision = choice or "(migrated — original v2.x table cell was empty)"
        body_context = rationale or "(migrated — original v2.x table cell was empty)"
        out.extend([
            f"## {seq} — {today} — {title}",
            "",
            "**Status:** Active",
            "",
            f"**Context:** {body_context}",
            "",
            f"**Decision:** {body_decision}",
            "",
            "**Consequences:** TBD — migrated from v2.x table; fill in next session "
            "or via /rad-planner:plan --reboot.",
            "",
            "---",
            "",
        ])
    return "\n".join(out)


def _extract_decisions_table(section_body: str) -> list[tuple[str, str, str]]:
    """Pull rows out of the v2.x 'Key Design Decisions' markdown table.

    Returns a list of (decision, choice, rationale) tuples. The table heading
    pattern is `| Decision | Choice | Rationale |` (case-insensitive on the
    column names). Tolerates extra columns silently.
    """
    lines = section_body.splitlines()
    rows: list[tuple[str, str, str]] = []
    in_table = False
    header_indices: dict[str, int] | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            in_table = False
            header_indices = None
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if header_indices is None:
                lower = [c.lower() for c in cells]
                if any("decision" in c for c in lower) and any("choice" in c for c in lower):
                    header_indices = {
                        "decision": _find_idx(lower, "decision"),
                        "choice": _find_idx(lower, "choice"),
                        "rationale": _find_idx(lower, "rationale"),
                    }
                    in_table = True
                continue
            if in_table:
                if set(stripped.replace("|", "").strip()) <= set("-: "):
                    continue  # divider row
                d = cells[header_indices["decision"]] if header_indices["decision"] is not None and header_indices["decision"] < len(cells) else ""
                c = cells[header_indices["choice"]] if header_indices["choice"] is not None and header_indices["choice"] < len(cells) else ""
                r = cells[header_indices["rationale"]] if header_indices["rationale"] is not None and header_indices["rationale"] < len(cells) else ""
                if d or c or r:
                    rows.append((d, c, r))
        else:
            in_table = False
            header_indices = None

    return rows


def _find_idx(lower_cells: list[str], needle: str) -> Optional[int]:
    for i, c in enumerate(lower_cells):
        if needle in c:
            return i
    return None


def build_plan(parsed: dict, source_name: str, today: str) -> str:
    """PLAN.md = sections 4 + 5 + 6 + 7."""
    title = parsed["title"] or "Plan"
    meta = parsed["preamble_meta"]

    out = [
        _migration_header(source_name, today),
        f"# Plan: {title.replace('Implementation Plan:', '').strip().rstrip(':')}",
        "",
    ]
    for key in ("Generated", "Status", "Approved by"):
        if key in meta:
            out.append(f"**{key}:** {meta[key]}")
    out.append("")

    for num, label in [
        ("4", "## Milestones"),
        ("5", "## Implementation Steps"),
        ("6", "## Checkpoints"),
        ("7", "## Risks and Considerations"),
    ]:
        body = parsed["sections"].get(num, {}).get("body", "").lstrip()
        if not body:
            continue
        out.extend([label, "", body, ""])

    return "\n".join(out)


def build_fragment(strategic_files: list[str], today: str) -> str:
    """CLAUDE-FRAGMENT.md @-import block."""
    lines = [
        "# CLAUDE-FRAGMENT — Strategic docs for this project",
        f"<!-- Generated by migrate-to-v4.py v{VERSION} on {today}. Consumed-and-deleted "
        f"by rad-session /init's CLAUDE.md merge step. -->",
        "",
    ]
    for name in strategic_files:
        lines.append(f"@{name}")
    lines.append("")
    return "\n".join(lines)


# ---------- Action planning ----------

def plan_transformations(artifacts: dict, root: Path) -> list[dict]:
    """Compute the list of actions to apply.

    Each action is a dict with:
      type: "split" | "archive" | "move" | "preserve_with_fragment" | "skip"
      source: relative path of source file
      reason: human-readable explanation
      ambiguous: bool (True → requires confirmation even in --non-interactive)
      details: type-specific dict
    """
    actions: list[dict] = []

    # 1. implementation_plan.md → split
    if artifacts["implementation_plan"]:
        # Check for v4 conflicts
        conflicts = artifacts["v4_already_present"]
        actions.append({
            "type": "split",
            "source": V2X_PLAN_FILE,
            "reason": "v2.x mega-doc → 5 strategic/operational files",
            "ambiguous": bool(conflicts),
            "details": {"conflicts": conflicts},
        })

    # 2. HANDOFF.md from /checkpoint → archive
    if artifacts["handoff"] and artifacts["handoff_is_checkpoint"]:
        actions.append({
            "type": "archive",
            "source": "HANDOFF.md",
            "reason": "checkpoint-era HANDOFF.md (rad-planner /checkpoint format); "
                      "next /rad-session:wrapup will regenerate the wrapup-format HANDOFF.md",
            "ambiguous": False,
            "details": {},
        })

    # 3. EXECUTION-PROMPT.md → archive (role replaced by /startup briefing)
    if artifacts["execution_prompt"]:
        actions.append({
            "type": "archive",
            "source": V2X_EXECUTION_PROMPT,
            "reason": "role replaced by rad-session /startup briefing in 4.0",
            "ambiguous": False,
            "details": {},
        })

    # 4. docs/ARCHITECTURE.md → ARCHITECTURE.md (only if no split would write it)
    will_split_architecture = bool(artifacts["implementation_plan"])
    if artifacts["docs_architecture"]:
        if will_split_architecture:
            actions.append({
                "type": "archive",
                "source": V2X_DOCS_ARCH,
                "reason": "implementation_plan.md split will produce ARCHITECTURE.md at "
                          "project root — archiving the duplicate at docs/",
                "ambiguous": True,
                "details": {},
            })
        else:
            actions.append({
                "type": "move",
                "source": V2X_DOCS_ARCH,
                "reason": "4.0 puts ARCHITECTURE.md at project root, not docs/",
                "ambiguous": False,
                "details": {"dest": "ARCHITECTURE.md"},
            })

    # 5. CLAUDE.md generated by generate-project-config → preserve + add FRAGMENT
    fragment_needed = (
        artifacts["implementation_plan"]
        or any((root / name).is_file() for name in V4_STRATEGIC if name != "ARCHITECTURE.md" or not artifacts["docs_architecture"])
    )
    if artifacts["claude_md_is_generate_project_config"] and not artifacts["v4_fragment_present"]:
        actions.append({
            "type": "preserve_with_fragment",
            "source": "CLAUDE.md",
            "reason": "generate-project-config-era CLAUDE.md preserved; FRAGMENT generated "
                      "alongside so next /rad-session:init can merge strategic @-imports",
            "ambiguous": False,
            "details": {},
        })
    elif fragment_needed and not artifacts["v4_fragment_present"]:
        # Plan will produce strategic docs; emit FRAGMENT so /init wires them up
        actions.append({
            "type": "emit_fragment",
            "source": "(none)",
            "reason": "no CLAUDE-FRAGMENT.md present; emitting one so the next "
                      "/rad-session:init wires the strategic @-imports into CLAUDE.md",
            "ambiguous": False,
            "details": {},
        })

    return actions


# ---------- Apply ----------

def confirm(prompt: str, *, interactive: bool, default: bool = True) -> bool:
    """y/N confirmation. In non-interactive mode, return `default`."""
    if not interactive:
        return default
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{prompt} {suffix} ").strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer.startswith("y")


def archive_file(src_relative: str, root: Path, archive_dir: Path) -> Path:
    """Copy src to archive_dir preserving relative path layout."""
    src = root / src_relative
    flat_name = src_relative.replace("/", "-").replace("\\", "-") + ".orig"
    dest = archive_dir / flat_name
    archive_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def apply_split_implementation_plan(
    root: Path, archive_dir: Path, today: str, dry_run: bool
) -> dict:
    """Split implementation_plan.md → 5 strategic/operational files. Returns report."""
    src = root / V2X_PLAN_FILE
    content = src.read_text(encoding="utf-8", errors="replace")
    parsed = parse_sections(content)

    report = {
        "ok": True,
        "unrecognized": parsed["unrecognized"],
        "sections_seen": sorted(parsed["sections"].keys()),
        "files_written": [],
    }

    if parsed["unrecognized"]:
        report["ok"] = False
        report["warning"] = (
            f"{V2X_PLAN_FILE} did not match the v2.x 7-section template (no "
            f"`## 1. ...` heading found). Skipping split; archive only."
        )
        if not dry_run:
            archive_file(V2X_PLAN_FILE, root, archive_dir)
        return report

    outputs: dict[str, str] = {
        "PRD.md": build_prd(parsed, V2X_PLAN_FILE, today),
        "ARCHITECTURE.md": build_architecture(parsed, V2X_PLAN_FILE, today),
        "ASSUMPTIONS.md": build_assumptions(today),
        "DECISIONS.md": build_decisions(parsed, V2X_PLAN_FILE, today),
        "PLAN.md": build_plan(parsed, V2X_PLAN_FILE, today),
    }

    if not dry_run:
        archive_file(V2X_PLAN_FILE, root, archive_dir)
        for name, body in outputs.items():
            (root / name).write_text(body, encoding="utf-8")
            report["files_written"].append(name)
        # Remove the original mega-doc now that it's archived and split
        src.unlink()
    else:
        report["files_written"] = list(outputs.keys())

    return report


def apply_archive_only(
    src_relative: str, root: Path, archive_dir: Path, dry_run: bool
) -> dict:
    if not dry_run:
        archive_file(src_relative, root, archive_dir)
        (root / src_relative).unlink()
    return {"ok": True, "archived": src_relative}


def apply_move(
    src_relative: str, dest_relative: str, root: Path, archive_dir: Path, dry_run: bool
) -> dict:
    if dry_run:
        return {"ok": True, "moved": f"{src_relative} → {dest_relative}"}
    archive_file(src_relative, root, archive_dir)
    src = root / src_relative
    dest = root / dest_relative
    if dest.exists():
        return {"ok": False, "warning": f"{dest_relative} already exists — leaving original at {src_relative} (archived copy stored)."}
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    return {"ok": True, "moved": f"{src_relative} → {dest_relative}"}


def apply_fragment(
    root: Path, today: str, dry_run: bool, preserve_claude_md: bool
) -> dict:
    """Emit CLAUDE-FRAGMENT.md listing whichever strategic files exist at root."""
    present = [name for name in V4_STRATEGIC if (root / name).is_file()]
    if not present:
        present = V4_STRATEGIC  # forward-looking — files about to be written
    body = build_fragment(present, today)
    if not dry_run:
        (root / V4_FRAGMENT).write_text(body, encoding="utf-8")
    return {
        "ok": True,
        "fragment_imports": present,
        "preserved_claude_md": preserve_claude_md,
    }


# ---------- gitignore ----------

def update_gitignore(root: Path, archive_dir_name: str, *, dry_run: bool) -> dict:
    """Add `.rad-archive/` entry to .gitignore (or equivalent) if not already present."""
    gi = root / ".gitignore"
    line = f"{archive_dir_name}/"
    if not gi.exists():
        if dry_run:
            return {"action": "would_create", "added": line}
        gi.write_text(
            "# rad-session migration archive\n" + line + "\n",
            encoding="utf-8",
        )
        return {"action": "created", "added": line}

    text = gi.read_text(encoding="utf-8", errors="replace")
    if line in text.splitlines() or f"/{line}" in text.splitlines():
        return {"action": "unchanged", "reason": "already gitignored"}

    if dry_run:
        return {"action": "would_append", "added": line}
    with gi.open("a", encoding="utf-8") as fh:
        if not text.endswith("\n"):
            fh.write("\n")
        fh.write("# rad-session migration archive\n")
        fh.write(line + "\n")
    return {"action": "appended", "added": line}


# ---------- Manifest ----------

def write_manifest(archive_dir: Path, manifest: dict, dry_run: bool) -> None:
    if dry_run:
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


# ---------- CLI ----------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate a project from rad-planner 2.x / rad-session 3.x to "
                    "the RAD 8-doc standard (rad-planner 3.0 / rad-session 4.0).",
    )
    parser.add_argument("path", nargs="?", default=".", help="Project root (default: cwd)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan; write nothing")
    parser.add_argument("--non-interactive", action="store_true", help="No prompts; apply safe transforms")
    parser.add_argument("--archive-dir", default=".rad-archive", help="Archive directory (default: .rad-archive)")
    parser.add_argument("--no-gitignore", action="store_true", help="Don't auto-add archive dir to .gitignore")
    parser.add_argument("--json", action="store_true", help="Emit trailing JSON summary (implies --non-interactive)")
    args = parser.parse_args()

    if args.json:
        args.non_interactive = True

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"Error: project root not found: {root}", file=sys.stderr)
        return 2

    interactive = not args.non_interactive
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    archive_root = root / args.archive_dir / timestamp

    if not args.json:
        print(f"migrate-to-v4.py v{VERSION}")
        print(f"  project root: {root}")
        print(f"  archive dir:  {archive_root}")
        print(f"  mode:         {'dry-run' if args.dry_run else ('non-interactive' if not interactive else 'interactive')}")
        print()

    artifacts = detect_artifacts(root)
    actions = plan_transformations(artifacts, root)

    if not actions:
        if not args.json:
            print("Nothing to migrate. Project root has no v2.x / v3.x artifacts that need transforming.")
        else:
            print(json.dumps({
                "migrated": False,
                "reason": "nothing_to_migrate",
                "artifacts_detected": _serializable_artifacts(artifacts),
            }, indent=2))
        return 1

    # Show plan
    if not args.json:
        print("Planned actions:")
        for i, a in enumerate(actions, start=1):
            flag = " [AMBIGUOUS]" if a.get("ambiguous") else ""
            print(f"  {i}. {a['type']:25s} {a['source']:30s}  — {a['reason']}{flag}")
        print()

    # Per-action confirmation + apply
    results: list[dict] = []
    skipped: list[str] = []

    for a in actions:
        ambiguous = a.get("ambiguous", False)
        default_yes = not ambiguous  # ambiguous → default to N

        prompt = f"Apply: {a['type']} on `{a['source']}`?"
        if ambiguous and a["type"] == "split" and a["details"].get("conflicts"):
            prompt += (
                f"\n  ⚠ Conflict: v4 file(s) already exist: "
                f"{', '.join(a['details']['conflicts'])}. Splitting will OVERWRITE these.\n  Proceed?"
            )
        elif ambiguous and a["type"] == "archive" and "docs/ARCHITECTURE.md" in a["source"]:
            prompt += (
                "\n  ⚠ The split of implementation_plan.md will write a fresh ARCHITECTURE.md "
                "at project root.\n  This archives the duplicate at docs/ to avoid two sources of truth.\n  Proceed?"
            )

        proceed = confirm(prompt, interactive=interactive, default=default_yes)
        if not proceed:
            skipped.append(a["source"])
            results.append({"action": a, "applied": False, "reason": "user_declined" if interactive else "ambiguous_skipped"})
            continue

        # Dispatch
        if a["type"] == "split":
            r = apply_split_implementation_plan(root, archive_root, today, args.dry_run)
        elif a["type"] == "archive":
            r = apply_archive_only(a["source"], root, archive_root, args.dry_run)
        elif a["type"] == "move":
            r = apply_move(a["source"], a["details"]["dest"], root, archive_root, args.dry_run)
        elif a["type"] == "preserve_with_fragment":
            r = apply_fragment(root, today, args.dry_run, preserve_claude_md=True)
        elif a["type"] == "emit_fragment":
            r = apply_fragment(root, today, args.dry_run, preserve_claude_md=False)
        else:
            r = {"ok": False, "warning": f"unknown action type: {a['type']}"}

        results.append({"action": a, "applied": True, "result": r})

    # gitignore
    gi_result = {"action": "skipped", "reason": "--no-gitignore"}
    if not args.no_gitignore and not args.dry_run:
        gi_result = update_gitignore(root, args.archive_dir, dry_run=args.dry_run)

    # Manifest
    manifest = {
        "tool": "migrate-to-v4.py",
        "tool_version": VERSION,
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "actions": [
            {
                "type": r["action"]["type"],
                "source": r["action"]["source"],
                "applied": r["applied"],
                "result": r.get("result", {}),
            }
            for r in results
        ],
        "gitignore": gi_result,
    }
    write_manifest(archive_root, manifest, args.dry_run)

    # Output
    if args.json:
        summary = {
            "migrated": any(r["applied"] for r in results),
            "dry_run": args.dry_run,
            "archive_dir": str(archive_root),
            "actions_applied": [r["action"]["source"] for r in results if r["applied"]],
            "actions_skipped": skipped,
            "manifest_path": str(archive_root / "manifest.json"),
            "gitignore": gi_result,
            "artifacts_detected": _serializable_artifacts(artifacts),
        }
        print(json.dumps(summary, indent=2))
    else:
        print()
        print("Summary:")
        for r in results:
            applied = "✓" if r["applied"] else "·"
            src = r["action"]["source"]
            kind = r["action"]["type"]
            if r["applied"]:
                detail = r.get("result", {})
                if "files_written" in detail:
                    print(f"  {applied} {kind:25s} {src:30s} → {', '.join(detail['files_written'])}")
                elif "moved" in detail:
                    print(f"  {applied} {kind:25s} {detail['moved']}")
                elif "fragment_imports" in detail:
                    print(f"  {applied} {kind:25s} {V4_FRAGMENT} (imports: {', '.join(detail['fragment_imports'])})")
                else:
                    print(f"  {applied} {kind:25s} {src}")
            else:
                print(f"  {applied} {kind:25s} {src}  (skipped)")
        if gi_result.get("action") not in (None, "skipped"):
            print(f"  · gitignore                 .gitignore — {gi_result['action']}: {gi_result.get('added', '')}")
        if args.dry_run:
            print()
            print("DRY RUN — no files were written or moved.")
        else:
            print()
            print(f"Manifest:    {archive_root / 'manifest.json'}")
            print(f"Archive:     {archive_root}")
            print()
            print("Verify the v4 layout:")
            print("  python3 plugins/rad-planner/scripts/plan-lint.py --mode all tasks.md")
            print("  /rad-planner:plan --validate          (interactive 8-doc gap-check)")
            print("  /rad-session:init                     (merges CLAUDE-FRAGMENT.md into CLAUDE.md)")

    return 0 if any(r["applied"] for r in results) or args.dry_run else 1


def _serializable_artifacts(artifacts: dict) -> dict:
    out = {}
    for key, val in artifacts.items():
        if isinstance(val, Path):
            out[key] = str(val.name)
        else:
            out[key] = val
    return out


if __name__ == "__main__":
    sys.exit(main())

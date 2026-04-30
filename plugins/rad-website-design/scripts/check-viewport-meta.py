#!/usr/bin/env python3
"""check-viewport-meta — flag user-scalable=no and missing viewport meta.

Pure stdlib. Outputs JSON.

Anti-patterns flagged:
  1. <meta name="viewport"> missing entirely — no responsive scaling on mobile
  2. user-scalable=no — strips zoom; ADA lawsuit magnet
  3. maximum-scale=1.0 (or any maximum-scale<5) — same effect as user-scalable=no in iOS Safari

Severity: AVOID-AT-ALL-COSTS (accessibility sabotage).

Usage:
  python check-viewport-meta.py <path-to-html-or-dir>
  python check-viewport-meta.py --json <path>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VIEWPORT_RE = re.compile(
    r'<meta\s+[^>]*name=["\']viewport["\'][^>]*>',
    re.IGNORECASE,
)
USER_SCALABLE_NO_RE = re.compile(
    r'user-scalable\s*=\s*["\']?\s*no\b',
    re.IGNORECASE,
)
MAX_SCALE_RE = re.compile(
    r'maximum-scale\s*=\s*["\']?\s*([0-9.]+)',
    re.IGNORECASE,
)


def scan_file(path: Path) -> list[dict]:
    findings: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [{
            "file": str(path),
            "severity": "warning",
            "tag": "[STATIC]",
            "rule": "io-error",
            "message": f"Could not read file: {exc}",
        }]

    if not _looks_like_html_root(text):
        return []

    viewport_matches = list(VIEWPORT_RE.finditer(text))

    if not viewport_matches:
        findings.append({
            "file": str(path),
            "line": 1,
            "severity": "high",
            "tag": "[STATIC]",
            "rule": "viewport-meta-missing",
            "message": (
                "No <meta name=\"viewport\"> tag found. Mobile browsers will not "
                "apply responsive scaling. Add: "
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">."
            ),
        })
        return findings

    for m in viewport_matches:
        line_no = text.count("\n", 0, m.start()) + 1
        tag_text = m.group(0)

        if USER_SCALABLE_NO_RE.search(tag_text):
            findings.append({
                "file": str(path),
                "line": line_no,
                "severity": "critical",
                "tag": "[STATIC]",
                "rule": "user-scalable-no",
                "snippet": tag_text,
                "message": (
                    "user-scalable=no strips pinch-zoom from mobile users. This is "
                    "an accessibility sabotage anti-pattern (Tier 1 — AVOID-AT-ALL-COSTS) "
                    "and an ADA lawsuit magnet. Remove user-scalable=no."
                ),
            })

        max_scale_match = MAX_SCALE_RE.search(tag_text)
        if max_scale_match:
            try:
                max_scale = float(max_scale_match.group(1))
            except ValueError:
                max_scale = None
            if max_scale is not None and max_scale < 5.0:
                findings.append({
                    "file": str(path),
                    "line": line_no,
                    "severity": "high",
                    "tag": "[STATIC]",
                    "rule": "maximum-scale-too-low",
                    "snippet": tag_text,
                    "message": (
                        f"maximum-scale={max_scale} restricts user zoom. iOS Safari treats "
                        "values <5 as effectively no-scale. Remove maximum-scale or set ≥5."
                    ),
                })

    return findings


def _looks_like_html_root(text: str) -> bool:
    """Skip files that aren't HTML root documents (no need to flag missing viewport
    on a partial template, e.g. a JSX component fragment)."""
    head = text[:4096].lower()
    if "<html" in head or "<!doctype html" in head:
        return True
    return False


def iter_targets(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        files: list[Path] = []
        for ext in ("*.html", "*.htm", "*.astro"):
            files.extend(target.rglob(ext))
        return files
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("target", help="File or directory to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"Target does not exist: {target}", file=sys.stderr)
        return 2

    files = iter_targets(target)
    findings: list[dict] = []
    for f in files:
        findings.extend(scan_file(f))

    output = {
        "validator": "check-viewport-meta",
        "scanned": len(files),
        "findings": findings,
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        if not findings:
            print(f"check-viewport-meta: scanned {len(files)} file(s) — no issues found.")
            return 0
        print(f"check-viewport-meta: {len(findings)} finding(s) across {len(files)} file(s).\n")
        for f in findings:
            print(f"  {f['tag']} {f['file']}:{f.get('line', '?')} [{f['severity']}] {f['rule']}")
            print(f"    {f['message']}")
            if f.get("snippet"):
                print(f"    Snippet: {f['snippet']}")
            print()

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

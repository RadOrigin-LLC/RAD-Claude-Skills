#!/usr/bin/env python3
"""check-pure-bw — flag pure black/white in CSS (eye-strain anti-pattern).

Pure stdlib. Outputs JSON.

Anti-patterns flagged:
  - color: #000 / #000000 / black (literal)
  - color: #fff / #ffffff / white (literal)
  - background: same
  - Tailwind: bg-black / text-black / bg-white / text-white

Pure black + bright text causes "halation" (glowing edges) and eye strain in dark mode.
Pure white backgrounds in light mode at >100% brightness over-saturate sensitive eyes.

Severity: SHOULD-AVOID. Findings are heuristic — sometimes pure black/white is intentional
(e.g., logo SVG); we tag [HEURISTIC] when ambiguous, [STATIC] when in CSS color/background
declarations.

Usage:
  python check-pure-bw.py <path-to-css-or-dir>
  python check-pure-bw.py --json <path>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# CSS hex colors (pure black/white)
HEX_BLACK_RE = re.compile(r"#(?:000{1,2}|000000)\b", re.IGNORECASE)
HEX_WHITE_RE = re.compile(r"#(?:fff|ffffff)\b", re.IGNORECASE)

# Property-bound (high confidence)
COLOR_PROP_RE = re.compile(
    r'(?:^|[\s;{])(color|background(?:-color)?|border(?:-color)?)\s*:\s*([^;}\n]+)',
    re.IGNORECASE,
)

# Tailwind utilities
TW_BLACK_RE = re.compile(r'\b(bg|text|border|from|to|via)-black\b')
TW_WHITE_RE = re.compile(r'\b(bg|text|border|from|to|via)-white\b')


def scan_css(path: Path) -> list[dict]:
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

    for m in COLOR_PROP_RE.finditer(text):
        prop = m.group(1).lower()
        value = m.group(2).strip()
        line_no = text.count("\n", 0, m.start()) + 1

        if HEX_BLACK_RE.search(value) or _has_named_color(value, "black"):
            findings.append({
                "file": str(path),
                "line": line_no,
                "severity": "medium",
                "tag": "[STATIC]",
                "rule": "pure-black-in-css",
                "snippet": f"{prop}: {value}",
                "message": (
                    "Pure black (#000 or 'black') causes halation (glowing edges) and "
                    "eye strain in dark mode. Use #121212 or a deep charcoal token instead."
                ),
            })
        if HEX_WHITE_RE.search(value) or _has_named_color(value, "white"):
            findings.append({
                "file": str(path),
                "line": line_no,
                "severity": "low",
                "tag": "[STATIC]",
                "rule": "pure-white-in-css",
                "snippet": f"{prop}: {value}",
                "message": (
                    "Pure white (#fff or 'white') over-saturates in bright environments. "
                    "Use an off-white token (#f5f5f5 / #fafafa) for body text/backgrounds."
                ),
            })

    return findings


def scan_jsx_or_html(path: Path) -> list[dict]:
    """For JSX/TSX/HTML, look for Tailwind utilities and inline style hex values."""
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

    for m in TW_BLACK_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        findings.append({
            "file": str(path),
            "line": line_no,
            "severity": "medium",
            "tag": "[STATIC]",
            "rule": "tailwind-black-utility",
            "snippet": m.group(0),
            "message": (
                "Tailwind 'black' utility uses #000. Use a custom token like 'bg-charcoal-900' "
                "or 'bg-neutral-950' for dark backgrounds (avoid halation)."
            ),
        })
    for m in TW_WHITE_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        findings.append({
            "file": str(path),
            "line": line_no,
            "severity": "low",
            "tag": "[STATIC]",
            "rule": "tailwind-white-utility",
            "snippet": m.group(0),
            "message": (
                "Tailwind 'white' utility uses #fff. Use 'bg-neutral-50' / 'bg-stone-50' for "
                "off-white surfaces."
            ),
        })

    # Inline style hex values
    for m in HEX_BLACK_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        findings.append({
            "file": str(path),
            "line": line_no,
            "severity": "low",
            "tag": "[HEURISTIC]",
            "rule": "pure-black-hex-literal",
            "snippet": m.group(0),
            "message": (
                "Pure black hex literal found. May be intentional (logo SVG, icon stroke) — "
                "verify it's not a UI surface or text color."
            ),
        })
    for m in HEX_WHITE_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        findings.append({
            "file": str(path),
            "line": line_no,
            "severity": "low",
            "tag": "[HEURISTIC]",
            "rule": "pure-white-hex-literal",
            "snippet": m.group(0),
            "message": (
                "Pure white hex literal found. May be intentional — verify it's not a body "
                "background or large text fill."
            ),
        })

    return findings


def _has_named_color(value: str, name: str) -> bool:
    """Check if a CSS value contains a named color, not part of a longer identifier."""
    return bool(re.search(rf'(?:^|[\s,(]){re.escape(name)}(?:[\s,)]|$)', value, re.IGNORECASE))


def iter_targets(target: Path) -> tuple[list[Path], list[Path]]:
    """Returns (css_files, jsx_html_files)."""
    if target.is_file():
        if target.suffix.lower() in (".css", ".scss", ".sass"):
            return [target], []
        return [], [target]
    if target.is_dir():
        css: list[Path] = []
        other: list[Path] = []
        for ext in ("*.css", "*.scss", "*.sass"):
            css.extend(target.rglob(ext))
        for ext in ("*.html", "*.htm", "*.astro", "*.jsx", "*.tsx"):
            other.extend(target.rglob(ext))
        return css, other
    return [], []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("target", help="File or directory to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"Target does not exist: {target}", file=sys.stderr)
        return 2

    css_files, other_files = iter_targets(target)
    findings: list[dict] = []
    for f in css_files:
        findings.extend(scan_css(f))
    for f in other_files:
        findings.extend(scan_jsx_or_html(f))

    output = {
        "validator": "check-pure-bw",
        "scanned": len(css_files) + len(other_files),
        "findings": findings,
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        scanned = len(css_files) + len(other_files)
        if not findings:
            print(f"check-pure-bw: scanned {scanned} file(s) — no issues found.")
            return 0
        print(f"check-pure-bw: {len(findings)} finding(s) across {scanned} file(s).\n")
        for f in findings:
            print(f"  {f['tag']} {f['file']}:{f.get('line', '?')} [{f['severity']}] {f['rule']}")
            print(f"    {f['message']}")
            if f.get("snippet"):
                print(f"    Snippet: {f['snippet']}")
            print()

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

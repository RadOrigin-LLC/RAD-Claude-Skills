#!/usr/bin/env python3
"""check-tap-targets — flag Tailwind tap targets under 44x44 px on interactive elements.

Pure stdlib. Outputs JSON.

Detects:
  - <button>, <a>, [role="button"], [onClick] with Tailwind size classes (w-N h-N) below w-11 h-11
  - Default Tailwind: w-1=4px, w-2=8px, ... w-11=44px (44px is the WCAG/Apple/Android minimum)
  - Treats w-fit / w-auto as [HEURISTIC] (cannot determine size statically)

Severity: SHOULD-AVOID (mobile UX issue). Mobile users 5x more likely to abandon on awkward
nav due to fat-finger errors.

This validator does NOT measure non-Tailwind sizing. For inline `width:` / CSS classes, it
emits a [NEEDS-MANUAL] follow-up reminder.

Usage:
  python check-tap-targets.py <path-to-jsx-or-dir>
  python check-tap-targets.py --json <path>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Tailwind default scale: w-N => N * 4px (1=4px, 11=44px, 12=48px)
# We flag when both w- and h- are present and either is below 11.
INTERACTIVE_TAGS = ("button", "a")
INTERACTIVE_ATTRS = ("onclick", 'role="button"', "role='button'")
MIN_TAILWIND_UNIT = 11  # 44px

# Match a JSX/HTML element opening tag with className/class attribute
ELEMENT_RE = re.compile(
    r'<(?P<tag>[a-zA-Z][\w-]*)\b(?P<attrs>[^>]*)>',
    re.DOTALL,
)
CLASSNAME_RE = re.compile(
    r'\b(?:class|className)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|\{`([^`]*)`\}|\{"([^"]*)"\})',
    re.DOTALL,
)
W_RE = re.compile(r'(?<![\w-])w-(\d+)(?![\w-])')
H_RE = re.compile(r'(?<![\w-])h-(\d+)(?![\w-])')
SIZE_RE = re.compile(r'(?<![\w-])size-(\d+)(?![\w-])')  # Tailwind v4
W_AUTO_FIT_RE = re.compile(r'(?<![\w-])w-(?:auto|fit|full|screen|min|max)(?![\w-])')


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

    for elem_m in ELEMENT_RE.finditer(text):
        tag = elem_m.group("tag").lower()
        attrs_blob = elem_m.group("attrs")
        attrs_lower = attrs_blob.lower()

        is_interactive = (
            tag in INTERACTIVE_TAGS
            or any(a in attrs_lower for a in INTERACTIVE_ATTRS)
        )
        if not is_interactive:
            continue

        cls_match = CLASSNAME_RE.search(attrs_blob)
        if not cls_match:
            continue
        cls = next((g for g in cls_match.groups() if g), "")
        if not cls:
            continue

        line_no = text.count("\n", 0, elem_m.start()) + 1
        line_snippet = _line_at(text, line_no)

        # Check size-N first (Tailwind v4 unified)
        size_m = SIZE_RE.search(cls)
        w_m = W_RE.search(cls)
        h_m = H_RE.search(cls)
        w_unsizable = bool(W_AUTO_FIT_RE.search(cls))

        if size_m:
            n = int(size_m.group(1))
            if n < MIN_TAILWIND_UNIT:
                findings.append(_make_finding(
                    path, line_no, "[STATIC]", "tap-target-below-44",
                    f"size-{n} ({n*4}px) is below the 44x44px minimum tap target.",
                    line_snippet,
                ))
        elif w_m and h_m:
            w = int(w_m.group(1))
            h = int(h_m.group(1))
            if w < MIN_TAILWIND_UNIT or h < MIN_TAILWIND_UNIT:
                findings.append(_make_finding(
                    path, line_no, "[STATIC]", "tap-target-below-44",
                    (
                        f"w-{w}/h-{h} ({w*4}x{h*4}px) is below the 44x44px minimum tap target. "
                        "Mobile users are 5x more likely to abandon on fat-finger errors."
                    ),
                    line_snippet,
                ))
        elif w_unsizable and h_m:
            h = int(h_m.group(1))
            if h < MIN_TAILWIND_UNIT:
                findings.append(_make_finding(
                    path, line_no, "[HEURISTIC]", "tap-target-height-below-44",
                    f"h-{h} ({h*4}px) is below 44px. Width is dynamic; verify computed size.",
                    line_snippet,
                ))
        elif not w_m and not h_m and not size_m:
            # Interactive element with no Tailwind sizing — could be CSS-driven
            # We don't flag every one (too noisy); just count for the NEEDS-MANUAL summary
            pass

    return findings


def _make_finding(
    path: Path,
    line: int,
    tag: str,
    rule: str,
    message: str,
    snippet: str,
) -> dict:
    return {
        "file": str(path),
        "line": line,
        "severity": "medium",
        "tag": tag,
        "rule": rule,
        "snippet": snippet.strip(),
        "message": message,
    }


def _line_at(text: str, line_no: int) -> str:
    lines = text.split("\n")
    if 0 < line_no <= len(lines):
        return lines[line_no - 1].strip()[:200]
    return ""


def iter_targets(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        files: list[Path] = []
        for ext in ("*.html", "*.htm", "*.astro", "*.jsx", "*.tsx", "*.vue", "*.svelte"):
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
        "validator": "check-tap-targets",
        "scanned": len(files),
        "findings": findings,
        "needs_manual": (
            "Non-Tailwind interactive elements not flagged. Verify with browser DevTools that "
            "all <button>, <a>, [role=button], and [onClick] elements compute to ≥44x44px."
        ),
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        if not findings:
            print(f"check-tap-targets: scanned {len(files)} file(s) — no Tailwind violations found.")
            print(f"  [NEEDS-MANUAL] {output['needs_manual']}")
            return 0
        print(f"check-tap-targets: {len(findings)} finding(s) across {len(files)} file(s).\n")
        for f in findings:
            print(f"  {f['tag']} {f['file']}:{f['line']} [{f['severity']}] {f['rule']}")
            print(f"    {f['message']}")
            if f.get("snippet"):
                print(f"    Snippet: {f['snippet']}")
            print()
        print(f"  [NEEDS-MANUAL] {output['needs_manual']}")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

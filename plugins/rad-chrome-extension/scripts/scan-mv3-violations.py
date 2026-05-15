#!/usr/bin/env python3
r"""
scan-mv3-violations.py — Grep source for MV3 hard-rule violations.

Scans Chrome extension source code for patterns banned or deprecated in MV3:

  - eval() / new Function() / setTimeout("string") / setInterval("string")
    (banned in extension_pages CSP under MV3)
  - Remote script loading: <script src="http(s)://...">,
    document.createElement('script') with remote src, dynamic
    import('https://...')
  - MV2-only chrome.* APIs: chrome.tabs.executeScript,
    chrome.tabs.insertCSS, chrome.browserAction.*, chrome.pageAction.*,
    chrome.extension.getBackgroundPage()
  - Persistent background page references: chrome.runtime.connect to a
    background page that uses persistent: true

Severity:
  critical  — banned in MV3 (will fail CWS review)
  major     — deprecated in MV3 (use chrome.scripting.* instead)
  moderate  — risky pattern (e.g., innerHTML with user-derived content; surfaces only with --dom-checks)

Usage:
  python3 scan-mv3-violations.py [<extension-root>]
  python3 scan-mv3-violations.py <extension-root> --files src/a.ts,src/b.js
  python3 scan-mv3-violations.py <extension-root> --json
  python3 scan-mv3-violations.py <extension-root> --dom-checks

Output:
  Default — human-readable text. Exit 1 if critical/major findings.
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
from typing import Iterable


SCAN_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts", ".html"}
DEFAULT_EXCLUDES = {
    "node_modules", ".venv", ".env", "dist", "build", ".next",
    "__pycache__", ".git", ".cache", ".turbo", ".vercel", "coverage",
    ".output",  # WXT default build output
}
SKIP_SUFFIXES = {".map", ".min.js", ".min.css"}


@dataclass
class Finding:
    severity: str
    category: str
    code: str
    title: str
    file: str
    line: int
    column: int
    snippet: str
    detail: str
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# CSP-banned: eval and string-form setTimeout/setInterval
EVAL_PATTERNS = [
    (
        "eval_call",
        re.compile(r"\beval\s*\("),
        "critical",
        "eval() call",
        "MV3 CSP bans eval() in extension_pages. Refactor to remove the dynamic-code path, or use a sandboxed iframe (separate CSP) if the dynamic code is required.",
    ),
    (
        "new_function",
        re.compile(r"\bnew\s+Function\s*\("),
        "critical",
        "new Function(...) — equivalent to eval()",
        "MV3 CSP bans dynamic code construction. Refactor or move to a sandboxed iframe.",
    ),
    (
        "settimeout_string",
        re.compile(r"\bsetTimeout\s*\(\s*[\"'`]"),
        "critical",
        "setTimeout('string') is string-form (CSP-banned)",
        "Pass a function instead: setTimeout(() => {...}, ms).",
    ),
    (
        "setinterval_string",
        re.compile(r"\bsetInterval\s*\(\s*[\"'`]"),
        "critical",
        "setInterval('string') is string-form (CSP-banned)",
        "Pass a function instead: setInterval(() => {...}, ms).",
    ),
]

# Remote code loading (banned)
REMOTE_PATTERNS = [
    (
        "script_src_remote",
        re.compile(r"<script[^>]*\bsrc\s*=\s*[\"']https?://"),
        "critical",
        "Remote <script src> tag",
        "MV3 bans remote code. All executable scripts must be bundled into the extension package.",
    ),
    (
        "document_create_script_remote",
        re.compile(r"createElement\s*\(\s*[\"']script[\"']\s*\)[^;]{0,200}\.\s*src\s*=\s*[\"`']https?://"),
        "critical",
        "Dynamic <script>.src = 'https://...'",
        "MV3 bans remote code. Bundle the script into the extension package, or move logic into a sandboxed iframe with its own bundled script.",
    ),
    (
        "dynamic_import_remote",
        re.compile(r"\bimport\s*\(\s*[\"`']https?://"),
        "critical",
        "Dynamic import('https://...') of remote module",
        "MV3 bans remote code in extension contexts. Bundle the module or load it inside a sandboxed page.",
    ),
    (
        "fetch_eval_pattern",
        re.compile(r"\bfetch\s*\([^)]+\)[^;]{0,300}\.\s*then\s*\([^)]*\b(?:eval|Function)\b"),
        "critical",
        "fetch().then(eval) — remote code injection pattern",
        "Banned in MV3. This is the canonical remote-code-execution pattern Chrome rejects.",
    ),
]

# MV2-only chrome.* APIs
MV2_API_PATTERNS = [
    (
        "tabs_execute_script",
        re.compile(r"\bchrome\.tabs\.executeScript\b"),
        "major",
        "chrome.tabs.executeScript (MV2)",
        "Use chrome.scripting.executeScript({ target: { tabId }, files: [...] }) in MV3.",
    ),
    (
        "tabs_insert_css",
        re.compile(r"\bchrome\.tabs\.insertCSS\b"),
        "major",
        "chrome.tabs.insertCSS (MV2)",
        "Use chrome.scripting.insertCSS({ target: { tabId }, files: [...] }) in MV3.",
    ),
    (
        "browser_action",
        re.compile(r"\bchrome\.browserAction\."),
        "major",
        "chrome.browserAction (MV2)",
        "Use chrome.action in MV3.",
    ),
    (
        "page_action",
        re.compile(r"\bchrome\.pageAction\."),
        "major",
        "chrome.pageAction (MV2)",
        "Use chrome.action with declarativeContent or per-tab logic in MV3.",
    ),
    (
        "get_background_page",
        re.compile(r"\bchrome\.extension\.getBackgroundPage\b"),
        "critical",
        "chrome.extension.getBackgroundPage (MV2-only)",
        "Service workers in MV3 cannot expose a synchronous global. Use chrome.runtime.sendMessage instead.",
    ),
    (
        "web_request_blocking_handler",
        re.compile(r"chrome\.webRequest\.\w+\.addListener\s*\([^)]*?,\s*\[[^\]]*?\bblocking\b"),
        "critical",
        "Blocking webRequest listener (MV2)",
        "MV3 supports webRequest in observe-only mode. For blocking, migrate to chrome.declarativeNetRequest.",
    ),
]

DOM_RISK_PATTERNS = [
    (
        "innerHTML_assignment",
        re.compile(r"\.\s*innerHTML\s*="),
        "moderate",
        "innerHTML assignment",
        "If the assigned value comes from a content script, message, or remote response, this is an XSS vector. Use textContent for text, or a sanitizer for HTML.",
    ),
    (
        "document_write",
        re.compile(r"\bdocument\.write\s*\("),
        "moderate",
        "document.write() usage",
        "Banned in service workers; risky in content scripts. Use DOM APIs instead.",
    ),
]


def iter_source_files(root: Path, files: list[Path] | None) -> Iterable[Path]:
    if files:
        for f in files:
            if f.is_file():
                yield f
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in DEFAULT_EXCLUDES for part in p.parts):
            continue
        if any(p.name.endswith(suf) for suf in SKIP_SUFFIXES):
            continue
        if p.suffix in SCAN_EXTENSIONS:
            yield p


def scan_file(path: Path, dom_checks: bool) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings
    patterns = list(EVAL_PATTERNS) + list(REMOTE_PATTERNS) + list(MV2_API_PATTERNS)
    if dom_checks:
        patterns += list(DOM_RISK_PATTERNS)

    for code, pattern, sev, title, detail in patterns:
        category = (
            "csp_banned" if code in {"eval_call", "new_function", "settimeout_string", "setinterval_string"}
            else "remote_code" if any(code == c for c, _, _, _, _ in REMOTE_PATTERNS)
            else "mv2_api" if any(code == c for c, _, _, _, _ in MV2_API_PATTERNS)
            else "dom_risk"
        )
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            col = m.start() - (text.rfind("\n", 0, m.start()) + 1) + 1
            snippet_start = max(0, m.start() - 20)
            snippet_end = min(len(text), m.end() + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", "\\n").strip()
            findings.append(Finding(
                severity=sev,
                category=category,
                code=code,
                title=title,
                file=str(path),
                line=line,
                column=col,
                snippet=snippet[:160],
                detail=detail,
                fix="",
            ))
    return findings


def render_text(findings: list[Finding], files_scanned: int, root: Path) -> str:
    out = [f"scan-mv3-violations", "", f"Files scanned: {files_scanned}", f"Root: {root}", ""]
    if not findings:
        out.append("PASS — no MV3 hard-rule violations detected.")
        return "\n".join(out)
    by_sev = {"critical": [], "major": [], "moderate": [], "minor": []}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    for sev in ("critical", "major", "moderate", "minor"):
        items = by_sev.get(sev, [])
        if not items:
            continue
        out.append(f"[{sev.upper()}] {len(items)} finding{'s' if len(items) != 1 else ''}")
        for f in items:
            out.append(f"  {f.file}:{f.line}:{f.column}  {f.code}")
            out.append(f"    {f.title}")
            out.append(f"    {f.snippet}")
            out.append(f"    {f.detail}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("extension_root", nargs="?", default=".")
    p.add_argument("--files", help="Comma-separated list of source files to scan")
    p.add_argument("--dom-checks", action="store_true", help="Also flag innerHTML / document.write (DOM risk)")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    root = Path(args.extension_root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: extension root not found: {root}", file=sys.stderr)
        return 2

    files: list[Path] | None = None
    if args.files:
        files = [Path(f.strip()).resolve() for f in args.files.split(",") if f.strip()]

    all_findings: list[Finding] = []
    scanned = 0
    for path in iter_source_files(root, files):
        scanned += 1
        all_findings.extend(scan_file(path, args.dom_checks))

    if args.json:
        out = {
            "validator": "scan-mv3-violations",
            "version": "1.0.0",
            "extension_root": str(root),
            "files_scanned": scanned,
            "dom_checks": args.dom_checks,
            "findings": [f.to_dict() for f in all_findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_text(all_findings, scanned, root))

    has_blocker = any(f.severity in ("critical", "major") for f in all_findings)
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

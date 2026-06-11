#!/usr/bin/env python3
r"""
audit-meta-tags.py — Audit HTML / JSX / Astro / Svelte templates for SEO meta-tag completeness.

For each HTML-shaped file, extract the <head> region's meta/title/link tags and
check:

  - <title> presence, length (50-60 ideal, 35-65 acceptable)
  - <meta name="description"> presence, length (140-160 ideal, 120-180 acceptable)
  - <link rel="canonical"> presence + absolute URL shape
  - <meta charset> declared
  - <meta name="viewport"> present
  - <meta name="robots"> sanity (warn on `noindex` in production-shaped templates)
  - Open Graph: og:title, og:description, og:image, og:url, og:type
  - Twitter Card: twitter:card, twitter:title, twitter:description, twitter:image
  - hreflang structure when multiple <link rel="alternate"> are present
  - Duplicate canonical / title / description (within one document)

This is regex-based parsing — it works on JSX/Astro/Svelte source even though
their templates aren't strict HTML. For canonical results on rendered output,
pair with a runtime extractor (Lighthouse, Screaming Frog).

Usage:
  python3 audit-meta-tags.py <path-or-root>
  python3 audit-meta-tags.py <root> --files src/Layout.tsx,public/index.html
  python3 audit-meta-tags.py <root> --json

Output:
  Default — human-readable text. Exit 1 on critical/warning findings.
  --json   — single JSON object on stdout.
  Exit 2   — script error.

No third-party dependencies. Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable


SCAN_EXTENSIONS = {".html", ".htm", ".jsx", ".tsx", ".astro", ".svelte", ".vue"}
DEFAULT_EXCLUDES = {
    "node_modules", ".venv", "dist", "build", ".next", ".output",
    ".astro", ".svelte-kit", ".cache", ".turbo", ".vercel", ".git",
    "__pycache__", "coverage", "out",
}

HEAD_BLOCK_RE = re.compile(r"<head\b[^>]*>(.*?)</head>", re.IGNORECASE | re.DOTALL)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_RE = re.compile(r"<meta\b([^>]*)/?>", re.IGNORECASE)
LINK_RE = re.compile(r"<link\b([^>]*)/?>", re.IGNORECASE)
ATTR_RE = re.compile(r"""(\w+(?:[:-]\w+)*)\s*=\s*["'`]([^"'`]*)["'`]""")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)


@dataclass
class Finding:
    severity: str        # critical | warning | info
    category: str
    code: str
    file: str
    message: str
    detail: str = ""
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileReport:
    file: str
    has_head: bool
    title: str | None = None
    description: str | None = None
    canonical: str | None = None
    has_viewport: bool = False
    has_charset: bool = False
    robots: str | None = None
    og: dict = field(default_factory=dict)
    twitter: dict = field(default_factory=dict)
    hreflangs: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def parse_attrs(raw: str) -> dict:
    return {k.lower(): v for k, v in ATTR_RE.findall(raw)}


def iter_files(root: Path, files: list[Path] | None) -> Iterable[Path]:
    if files:
        for f in files:
            if f.is_file():
                yield f
        return
    if root.is_file():
        yield root
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in DEFAULT_EXCLUDES for part in p.parts):
            continue
        if p.suffix in SCAN_EXTENSIONS:
            yield p


def audit_file(path: Path, findings: list[Finding]) -> FileReport:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return FileReport(file=str(path), has_head=False)

    report = FileReport(file=str(path), has_head=False)
    head_match = HEAD_BLOCK_RE.search(text)
    head_text = head_match.group(1) if head_match else text  # JSX often has no literal <head>
    report.has_head = bool(head_match)

    # Title (allow multiple to detect duplicates)
    titles = [m.group(1).strip() for m in TITLE_RE.finditer(head_text)]
    if not titles:
        findings.append(Finding(
            severity="critical", category="title", code="missing_title",
            file=str(path),
            message="No <title> found.",
            fix="Add <title>...</title> in the <head>.",
        ))
    else:
        report.title = titles[0]
        if len(titles) > 1:
            findings.append(Finding(
                severity="warning", category="title", code="duplicate_title",
                file=str(path),
                message=f"Multiple <title> tags ({len(titles)}) in head.",
            ))
        t_len = len(titles[0])
        if t_len == 0:
            findings.append(Finding(
                severity="critical", category="title", code="empty_title",
                file=str(path), message="<title> is empty.",
            ))
        elif t_len < 35:
            findings.append(Finding(
                severity="warning", category="title", code="title_too_short",
                file=str(path), message=f"Title is {t_len} chars (recommend 50-60).",
            ))
        elif t_len > 65:
            findings.append(Finding(
                severity="warning", category="title", code="title_too_long",
                file=str(path),
                message=f"Title is {t_len} chars (Google truncates around 60).",
                detail=f"'{titles[0][:80]}{'…' if len(titles[0]) > 80 else ''}'",
            ))

    # Meta tags
    metas = [parse_attrs(m.group(1)) for m in META_RE.finditer(head_text)]
    descriptions = []
    canonicals = []
    for m in metas:
        name = (m.get("name") or "").lower()
        prop = (m.get("property") or "").lower()
        content = m.get("content") or ""

        if name == "description":
            descriptions.append(content.strip())
        if name == "viewport":
            report.has_viewport = True
        if m.get("charset"):
            report.has_charset = True
        if name == "robots":
            report.robots = content
            if "noindex" in content.lower():
                findings.append(Finding(
                    severity="warning", category="robots", code="noindex_present",
                    file=str(path),
                    message=f"meta robots includes 'noindex': '{content}'. Ensure this is intended for production.",
                ))
        if prop.startswith("og:"):
            report.og[prop[3:]] = content
        if name.startswith("twitter:"):
            report.twitter[name[8:]] = content

    if descriptions:
        report.description = descriptions[0]
        d_len = len(descriptions[0])
        if len(descriptions) > 1:
            findings.append(Finding(
                severity="warning", category="description", code="duplicate_description",
                file=str(path),
                message=f"Multiple meta description tags ({len(descriptions)}).",
            ))
        if d_len == 0:
            findings.append(Finding(
                severity="critical", category="description", code="empty_description",
                file=str(path), message="meta description is empty.",
            ))
        elif d_len < 120:
            findings.append(Finding(
                severity="warning", category="description", code="description_too_short",
                file=str(path), message=f"description is {d_len} chars (recommend 140-160).",
            ))
        elif d_len > 180:
            findings.append(Finding(
                severity="warning", category="description", code="description_too_long",
                file=str(path),
                message=f"description is {d_len} chars (Google truncates around 160).",
            ))
    else:
        findings.append(Finding(
            severity="critical", category="description", code="missing_description",
            file=str(path),
            message="No <meta name=\"description\"> found.",
            fix='<meta name="description" content="...">',
        ))

    if not report.has_charset:
        findings.append(Finding(
            severity="warning", category="charset", code="missing_charset",
            file=str(path),
            message="No <meta charset=\"...\"> declared (browsers default to UTF-8 in HTML5, but explicit is safer).",
            fix='<meta charset="UTF-8">',
        ))
    if not report.has_viewport:
        findings.append(Finding(
            severity="critical", category="viewport", code="missing_viewport",
            file=str(path),
            message="No <meta name=\"viewport\"> — mobile rendering will be broken.",
            fix='<meta name="viewport" content="width=device-width, initial-scale=1">',
        ))

    # Links: canonical + hreflang
    links = [parse_attrs(m.group(1)) for m in LINK_RE.finditer(head_text)]
    for l in links:
        rel = (l.get("rel") or "").lower()
        href = l.get("href") or ""
        if rel == "canonical":
            canonicals.append(href)
        if rel == "alternate" and l.get("hreflang"):
            report.hreflangs.append({"hreflang": l["hreflang"], "href": href})

    if canonicals:
        report.canonical = canonicals[0]
        if len(canonicals) > 1:
            findings.append(Finding(
                severity="critical", category="canonical", code="duplicate_canonical",
                file=str(path),
                message=f"Multiple canonical links ({len(canonicals)}).",
            ))
        if not URL_RE.match(canonicals[0]):
            findings.append(Finding(
                severity="warning", category="canonical", code="canonical_not_absolute",
                file=str(path),
                message=f"Canonical is not an absolute URL: '{canonicals[0]}'",
                fix='<link rel="canonical" href="https://example.com/path">',
            ))
    else:
        findings.append(Finding(
            severity="warning", category="canonical", code="missing_canonical",
            file=str(path),
            message="No <link rel=\"canonical\">.",
            fix='<link rel="canonical" href="https://example.com/this-path">',
        ))

    # Open Graph
    required_og = ["title", "description", "image", "url", "type"]
    for prop in required_og:
        if prop not in report.og:
            findings.append(Finding(
                severity="warning", category="open_graph", code=f"missing_og:{prop}",
                file=str(path),
                message=f"Missing og:{prop}.",
                fix=f'<meta property="og:{prop}" content="...">',
            ))

    # Twitter Card
    required_tw = ["card", "title", "description", "image"]
    for prop in required_tw:
        if prop not in report.twitter:
            findings.append(Finding(
                severity="info", category="twitter_card", code=f"missing_twitter:{prop}",
                file=str(path),
                message=f"Missing twitter:{prop} (Twitter falls back to og:* when absent).",
            ))

    # hreflang sanity
    if report.hreflangs:
        # Check x-default present if multilingual
        codes = [h["hreflang"] for h in report.hreflangs]
        if "x-default" not in codes and len(codes) >= 2:
            findings.append(Finding(
                severity="warning", category="hreflang", code="missing_x_default",
                file=str(path),
                message=f"{len(codes)} hreflang variants but no x-default fallback.",
                fix='<link rel="alternate" hreflang="x-default" href="...">',
            ))

    return report


def render_text(reports: list[FileReport], findings: list[Finding]) -> str:
    out = [f"audit-meta-tags", "", f"Files scanned: {len(reports)}", ""]
    if not findings:
        out.append("PASS — all scanned files have complete meta-tag coverage.")
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
            out.append(f"  {f.file}  {f.code}")
            out.append(f"    {f.message}")
            if f.detail:
                out.append(f"    {f.detail}")
            if f.fix:
                out.append(f"    fix: {f.fix}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--files", help="Comma-separated list of files")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    files: list[Path] | None = None
    if args.files:
        files = [Path(f.strip()).resolve() for f in args.files.split(",") if f.strip()]

    findings: list[Finding] = []
    reports: list[FileReport] = []
    for path in iter_files(root, files):
        reports.append(audit_file(path, findings))

    if args.json:
        out = {
            "validator": "audit-meta-tags",
            "version": "1.0.0",
            "path": str(root),
            "files": [r.to_dict() for r in reports],
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_text(reports, findings))

    has_blocker = any(f.severity in ("critical", "warning") for f in findings)
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

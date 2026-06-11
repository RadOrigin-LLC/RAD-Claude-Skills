#!/usr/bin/env python3
r"""
validate-jsonld.py — Validate JSON-LD structured data blocks against schema.org.

Extracts `<script type="application/ld+json">` blocks from HTML/JSX/Astro/Svelte
source files (or accepts raw .json files) and validates against an embedded
subset of schema.org type definitions. Pure-stdlib Python 3.8+.

Framework handling (JSX/TSX/Astro/Svelte/Vue):
  - Literal JSON in template-literal form is unwrapped and validated:
    `<script type="application/ld+json">{`...`}</script>` and
    `dangerouslySetInnerHTML={{ __html: `...` }}` (self-closing or paired).
  - Astro `set:html={...}` is recognized the same way.
  - Dynamically built JSON-LD (JSON.stringify(expr), variable refs, `${}`
    interpolation) CANNOT be statically validated — those blocks are reported
    as info `dynamic_jsonld` rather than silently skipped or falsely failed.
    Validate the rendered HTML output for those pages instead.

Checks per block:

  - Valid JSON (parse error → critical)
  - @context references schema.org (warning if missing or non-canonical)
  - @type is a known schema.org type (info if unknown — bundled type list is
    not exhaustive; schema.org has 800+ types)
  - For recognized types: required + recommended properties present
  - URL-shaped fields look like absolute URLs
  - Date fields parse as ISO-8601 where applicable

The bundled type set covers the SEO-impactful subset: Article, NewsArticle,
BlogPosting, Product, Offer, Organization, Person, WebSite, WebPage,
BreadcrumbList, FAQPage, Question, Answer, HowTo, Recipe, Event, LocalBusiness,
SoftwareApplication, VideoObject. For other types the validator parses-only.

Usage:
  python3 validate-jsonld.py <path-or-glob>
  python3 validate-jsonld.py <file.html>
  python3 validate-jsonld.py <project-root> --json

Output:
  Default — human-readable text. Exit 1 on any critical/warning.
  --json   — single JSON object on stdout.
  Exit 2   — script error.

No third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


SCAN_EXTENSIONS = {".html", ".htm", ".jsx", ".tsx", ".astro", ".svelte", ".vue", ".json"}
FRAMEWORK_EXTENSIONS = {".jsx", ".tsx", ".astro", ".svelte", ".vue"}

# Matches the opening (or self-closing) ld+json script tag; group(1) is "/" when
# self-closing. Attribute values containing ">" are not supported (rare in JSON-LD).
SCRIPT_TAG_RE = re.compile(
    r"""<script\b[^>]*?\btype\s*=\s*["']application/ld\+json["'][^>]*?(/?)>""",
    re.IGNORECASE | re.DOTALL,
)
SCRIPT_CLOSE_RE = re.compile(r"</script\s*>", re.IGNORECASE)
# Start of an injected-content attribute: JSX dangerouslySetInnerHTML or Astro set:html.
HTML_ATTR_START_RE = re.compile(r"""(?:__html\s*:\s*|\bset:html\s*=\s*\{\s*)""")

DEFAULT_EXCLUDES = {
    "node_modules", ".venv", ".env", "dist", "build", ".next", ".output",
    ".astro", ".svelte-kit", ".cache", ".turbo", ".vercel", ".git",
    "__pycache__", "coverage", "out",
}


# Bundled subset of schema.org type definitions.
# required: must be present; recommended: should be present.
SCHEMA_TYPES: dict[str, dict] = {
    "Article": {
        "required": ["headline", "author"],
        "recommended": ["datePublished", "image", "publisher"],
    },
    "NewsArticle": {
        "required": ["headline", "author", "datePublished"],
        "recommended": ["image", "publisher", "dateModified"],
    },
    "BlogPosting": {
        "required": ["headline", "author"],
        "recommended": ["datePublished", "image", "publisher", "mainEntityOfPage"],
    },
    "Product": {
        "required": ["name"],
        "recommended": ["image", "description", "offers", "brand", "review", "aggregateRating"],
    },
    "Offer": {
        "required": ["price", "priceCurrency"],
        "recommended": ["availability", "url"],
    },
    "Organization": {
        "required": ["name"],
        "recommended": ["url", "logo", "sameAs"],
    },
    "Person": {
        "required": ["name"],
        "recommended": ["url", "image", "sameAs"],
    },
    "WebSite": {
        "required": ["url"],
        "recommended": ["name", "potentialAction"],
    },
    "WebPage": {
        "required": [],
        "recommended": ["url", "name", "description"],
    },
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
    },
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
    },
    "Question": {
        "required": ["name", "acceptedAnswer"],
        "recommended": [],
    },
    "Answer": {
        "required": ["text"],
        "recommended": [],
    },
    "HowTo": {
        "required": ["name", "step"],
        "recommended": ["image", "totalTime"],
    },
    "Recipe": {
        "required": ["name", "recipeIngredient", "recipeInstructions"],
        "recommended": ["image", "author", "datePublished", "cookTime", "prepTime", "nutrition"],
    },
    "Event": {
        "required": ["name", "startDate"],
        "recommended": ["location", "endDate", "image", "description"],
    },
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": ["telephone", "openingHours", "url", "geo"],
    },
    "SoftwareApplication": {
        "required": ["name", "applicationCategory"],
        "recommended": ["operatingSystem", "offers", "aggregateRating"],
    },
    "VideoObject": {
        "required": ["name", "thumbnailUrl", "uploadDate"],
        "recommended": ["description", "contentUrl", "embedUrl", "duration"],
    },
}

URL_FIELDS = frozenset({"url", "logo", "image", "thumbnailUrl", "contentUrl",
                        "embedUrl", "sameAs", "mainEntityOfPage"})
DATE_FIELDS = frozenset({"datePublished", "dateModified", "startDate", "endDate",
                        "uploadDate"})

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2})?)?$")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)


@dataclass
class Finding:
    severity: str
    category: str
    code: str
    file: str
    block_index: int
    message: str
    field: str = ""
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


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


def _scan_delimited(rest: str, quote: str) -> str | None:
    """Return the content of a `quote`-delimited literal at the start of rest, or None."""
    end = rest.find(quote, 1)
    while end != -1 and rest[end - 1] == "\\":
        end = rest.find(quote, end + 1)
    if end == -1:
        return None
    return rest[1:end]


def _classify_attr_expr(tag_text: str) -> tuple[str, str] | None:
    """Inspect an ld+json script tag for injected content (dangerouslySetInnerHTML /
    set:html). Returns ('json', payload) for a literal, ('dynamic', snippet) for a
    JS expression, or None if no such attribute is present."""
    m = HTML_ATTR_START_RE.search(tag_text)
    if m is None:
        return None
    rest = tag_text[m.end():].lstrip()
    if not rest:
        return ("dynamic", "")
    snippet = rest.splitlines()[0][:60]
    if rest[0] in "`\"'":
        literal = _scan_delimited(rest, rest[0])
        if literal is None:
            return ("dynamic", snippet)
        if rest[0] == "`" and "${" in literal:
            return ("dynamic", literal.splitlines()[0][:60])
        return ("json", literal)
    return ("dynamic", snippet)


def _unwrap_framework_body(body: str) -> tuple[str, str]:
    """Classify a JSX/Astro/Svelte/Vue script body that did not parse as raw JSON."""
    m = re.match(r"^\{\s*`(.*)`\s*\}$", body, re.DOTALL)
    if m:
        inner = m.group(1)
        if "${" in inner:
            return ("dynamic", inner[:60])
        return ("json", inner)
    if re.match(r"^\{.*\}$", body, re.DOTALL):
        # {JSON.stringify(...)} / {expr} — or literal JSON that failed to parse;
        # either way it can't be verified statically.
        return ("dynamic", body[:60])
    return ("json", body)  # genuinely malformed — validator reports invalid_json


def extract_blocks(text: str, file_suffix: str) -> list[tuple[str, str]]:
    """Return a list of (kind, payload): kind 'json' = validate payload as JSON,
    kind 'dynamic' = JS-generated content that static analysis cannot verify."""
    if file_suffix == ".json":
        return [("json", text)]
    blocks: list[tuple[str, str]] = []
    for m in SCRIPT_TAG_RE.finditer(text):
        tag_text = m.group(0)
        self_closing = m.group(1) == "/"
        attr_block = _classify_attr_expr(tag_text)
        if attr_block is not None:
            blocks.append(attr_block)
            continue
        if self_closing:
            # ld+json script with no readable content (e.g. spread props)
            blocks.append(("dynamic", tag_text[:60]))
            continue
        close = SCRIPT_CLOSE_RE.search(text, m.end())
        if close is None:
            continue
        body = text[m.end():close.start()].strip()
        if not body:
            blocks.append(("empty", ""))
            continue
        try:
            json.loads(body)
            blocks.append(("json", body))
            continue
        except ValueError:
            pass
        if file_suffix in FRAMEWORK_EXTENSIONS:
            blocks.append(_unwrap_framework_body(body))
        else:
            blocks.append(("json", body))  # validator reports invalid_json
    return blocks


def validate_value_type(value, field: str) -> str | None:
    """Return a problem message if the value is wrong shape, else None."""
    if field in URL_FIELDS:
        if isinstance(value, str):
            if not URL_RE.match(value):
                return f"{field} is not an absolute URL: '{value[:60]}'"
        elif isinstance(value, list):
            for v in value:
                if isinstance(v, str) and not URL_RE.match(v):
                    return f"{field} list contains a non-URL: '{v[:60]}'"
                if isinstance(v, dict) and "url" in v:
                    if not URL_RE.match(v["url"]):
                        return f"{field}[].url is not an absolute URL"
    if field in DATE_FIELDS:
        if isinstance(value, str) and not ISO_DATE_RE.match(value):
            return f"{field} is not ISO-8601 shape: '{value[:60]}'"
    return None


def validate_block(block_json: str, file_path: Path, idx: int,
                   findings: list[Finding]) -> None:
    try:
        data = json.loads(block_json)
    except ValueError as e:
        findings.append(Finding(
            severity="critical",
            category="parse",
            code="invalid_json",
            file=str(file_path), block_index=idx,
            message=f"Invalid JSON: {e}",
        ))
        return

    # Allow array of objects at top level (graph form)
    if isinstance(data, list):
        for sub_idx, sub in enumerate(data):
            if isinstance(sub, dict):
                _validate_obj(sub, file_path, idx, findings, sub_path=f"[{sub_idx}]")
        return
    if not isinstance(data, dict):
        findings.append(Finding(
            severity="warning", category="shape", code="not_object",
            file=str(file_path), block_index=idx,
            message="Top-level JSON-LD must be an object (or array of objects)",
        ))
        return

    # @graph form: { "@context": "...", "@graph": [ {...}, {...} ] }
    if "@graph" in data and isinstance(data["@graph"], list):
        _check_context(data, file_path, idx, findings)
        for sub_idx, sub in enumerate(data["@graph"]):
            if isinstance(sub, dict):
                _validate_obj(sub, file_path, idx, findings,
                              sub_path=f"@graph[{sub_idx}]", inherited_context=True)
        return

    _validate_obj(data, file_path, idx, findings)


def _check_context(data: dict, file_path: Path, idx: int, findings: list[Finding]) -> None:
    ctx = data.get("@context")
    if not ctx:
        findings.append(Finding(
            severity="warning", category="schema_org", code="missing_context",
            file=str(file_path), block_index=idx,
            message="Missing @context (should be 'https://schema.org' or similar)",
            fix='Add "@context": "https://schema.org"',
        ))
        return
    # Normalize: ctx can be a string, list, or dict
    if isinstance(ctx, str):
        if "schema.org" not in ctx:
            findings.append(Finding(
                severity="warning", category="schema_org", code="non_schema_org_context",
                file=str(file_path), block_index=idx,
                message=f"@context does not reference schema.org: '{ctx[:60]}'",
            ))
    elif isinstance(ctx, list):
        if not any("schema.org" in str(c) for c in ctx):
            findings.append(Finding(
                severity="warning", category="schema_org", code="non_schema_org_context",
                file=str(file_path), block_index=idx,
                message="@context list does not include schema.org",
            ))
    elif isinstance(ctx, dict):
        if not any("schema.org" in str(v) for v in ctx.values()):
            findings.append(Finding(
                severity="warning", category="schema_org", code="non_schema_org_context",
                file=str(file_path), block_index=idx,
                message="@context dict does not reference schema.org",
            ))


def _validate_obj(obj: dict, file_path: Path, idx: int,
                  findings: list[Finding], sub_path: str = "",
                  inherited_context: bool = False) -> None:
    if not inherited_context:
        _check_context(obj, file_path, idx, findings)

    type_value = obj.get("@type")
    if not type_value:
        findings.append(Finding(
            severity="warning", category="schema_org", code="missing_type",
            file=str(file_path), block_index=idx,
            message=f"Missing @type{(' at ' + sub_path) if sub_path else ''}",
            fix='Add "@type": "Article" / "Product" / etc. — pick the most specific applicable type.',
        ))
        return

    # @type can be a string or list
    types = type_value if isinstance(type_value, list) else [type_value]
    for t in types:
        if not isinstance(t, str):
            continue
        spec = SCHEMA_TYPES.get(t)
        if spec is None:
            findings.append(Finding(
                severity="info", category="schema_org", code="unknown_type",
                file=str(file_path), block_index=idx,
                message=f"@type '{t}'{(' at ' + sub_path) if sub_path else ''} is not in the bundled type set "
                        "(this validator covers ~20 SEO-impactful types; for others it parses-only)",
            ))
            continue

        for req in spec.get("required", []):
            if req not in obj or obj[req] in (None, "", [], {}):
                findings.append(Finding(
                    severity="critical", category="missing_required", code=f"missing_required:{t}.{req}",
                    file=str(file_path), block_index=idx,
                    field=req,
                    message=f"{t}{(' at ' + sub_path) if sub_path else ''} is missing required property '{req}'",
                    fix=f'Add "{req}": "..." per schema.org/{t}',
                ))
        for rec in spec.get("recommended", []):
            if rec not in obj:
                findings.append(Finding(
                    severity="warning", category="missing_recommended", code=f"missing_recommended:{t}.{rec}",
                    file=str(file_path), block_index=idx,
                    field=rec,
                    message=f"{t}{(' at ' + sub_path) if sub_path else ''} is missing recommended property '{rec}'",
                ))

    # Field-shape checks
    for field, value in obj.items():
        if field.startswith("@"):
            continue
        problem = validate_value_type(value, field)
        if problem:
            findings.append(Finding(
                severity="warning", category="field_shape", code=f"field_shape:{field}",
                file=str(file_path), block_index=idx,
                field=field, message=problem,
            ))


def render_text(findings: list[Finding], files_scanned: int, blocks_scanned: int) -> str:
    out = ["validate-jsonld", "", f"Files scanned: {files_scanned}", f"JSON-LD blocks: {blocks_scanned}", ""]
    if not findings:
        out.append("PASS — all JSON-LD blocks parse and conform to known schema.org types.")
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
            out.append(f"  {f.file} block#{f.block_index}  {f.code}")
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
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--files", help="Comma-separated list of files to scan")
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
    files_scanned = 0
    blocks_scanned = 0

    for path in iter_files(root, files):
        files_scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        blocks = extract_blocks(text, path.suffix)
        for idx, (kind, payload) in enumerate(blocks):
            blocks_scanned += 1
            if kind == "dynamic":
                findings.append(Finding(
                    severity="info", category="dynamic", code="dynamic_jsonld",
                    file=str(path), block_index=idx,
                    message=f"JSON-LD content is generated by a JS expression ('{payload}…') — "
                            "static validation cannot verify it. Validate the rendered HTML "
                            "output for this page, or inline literal JSON.",
                ))
                continue
            if kind == "empty":
                findings.append(Finding(
                    severity="warning", category="parse", code="empty_jsonld",
                    file=str(path), block_index=idx,
                    message="Empty application/ld+json script block.",
                    fix="Remove the block or add the JSON-LD payload.",
                ))
                continue
            validate_block(payload, path, idx, findings)

    if args.json:
        out = {
            "validator": "validate-jsonld",
            "version": "1.1.0",
            "path": str(root),
            "files_scanned": files_scanned,
            "blocks_scanned": blocks_scanned,
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_text(findings, files_scanned, blocks_scanned))

    has_blocker = any(f.severity in ("critical", "warning") for f in findings)
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

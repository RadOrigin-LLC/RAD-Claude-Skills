#!/usr/bin/env python3
r"""
scan-hardcoded-secrets.py — Flag hardcoded secrets that should be `op://` references.

Scans a project directory for code that hardcodes credentials, API keys, tokens,
URL-embedded passwords, and high-entropy strings that look like secrets. For each
hit, suggests an `op://<vault>/<item>/<field>` reference shape suitable for
replacement with `op inject` / `op run` / `op read`.

Not a replacement for dedicated tools (gitleaks, trufflehog, detect-secrets) —
those have curated regex libraries and live signature feeds. This validator
exists to surface candidates inside the rad-1password workflow with a concrete
"and here's how it becomes an op:// reference" suggestion.

Detection patterns:

  - Provider-prefixed tokens: OpenAI sk-, GitHub ghp_/github_pat_, Stripe
    sk_test_/sk_live_/pk_*, AWS AKIA*, Slack xox[abp]-, generic Bearer
  - JWT-like (3 base64 segments)
  - URL-embedded credentials (https://user:pass@host)
  - Assignment-shaped patterns: `api_key = "<32+ chars>"`, `password = "<8+>"`,
    `secret = "..."`, etc.
  - Optional --high-entropy mode: 32+ chars of base64/hex outside the above
    categories (off by default — high false-positive rate on lockfile hashes)

Exclusions:

  - `.env*` files (expected to hold secrets locally — those are NOT hardcoded
    in code), unless the file is named `.env.example` or `.env.sample` AND
    contains placeholder-looking values that should be `op://` references.
  - Test files (often contain fake secrets) — pass --include-tests to override.
  - Lockfiles (`package-lock.json`, `yarn.lock`, `Pipfile.lock`, etc.) —
    their hashes look like secrets but aren't.
  - Source maps (`*.map`), minified bundles (`*.min.js`), build artifacts.
  - `node_modules`, `.venv`, `dist`, `build`, etc.

Usage:
  python3 scan-hardcoded-secrets.py <project-root>
  python3 scan-hardcoded-secrets.py <project-root> --files src/a.py,src/b.ts
  python3 scan-hardcoded-secrets.py <project-root> --json
  python3 scan-hardcoded-secrets.py <project-root> --high-entropy
  python3 scan-hardcoded-secrets.py <project-root> --vault prod

Output:
  Default — human-readable text. Exit 1 if findings present.
  --json   — single JSON object on stdout.
  Exit 2   — script error.

No third-party dependencies. Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable


DEFAULT_EXCLUDES = {
    "node_modules", ".venv", "venv", "env", ".env",  # .env handled separately
    "dist", "build", ".next", ".nuxt", ".astro", "out",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".git", ".svelte-kit", ".vercel", ".cache", ".turbo", "coverage",
    "target", ".gradle", ".idea",
}

SCAN_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts",
    ".go", ".rb", ".rs", ".java", ".kt", ".swift", ".php", ".cs",
    ".sh", ".bash", ".zsh", ".fish", ".ps1",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".env",  # plus .env.* handled below
}

# Files we will not scan (their content looks like secrets but isn't):
SKIP_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "uv.lock",
    "Cargo.lock", "Gemfile.lock", "go.sum", "composer.lock",
    ".gitignore", ".prettierignore", ".eslintignore",
}

SKIP_SUFFIXES = {".map", ".min.js", ".min.css", ".lock"}


# ----- Provider-prefixed tokens (high confidence) -----
PROVIDER_PATTERNS = [
    ("openai_api_key",           re.compile(r"\b(sk-(?:proj-|svcacct-)?[A-Za-z0-9_\-]{32,})\b"),          "OpenAI API key"),
    ("github_pat_classic",       re.compile(r"\b(ghp_[A-Za-z0-9]{36})\b"),                               "GitHub Personal Access Token (classic)"),
    ("github_pat_fine_grained",  re.compile(r"\b(github_pat_[A-Za-z0-9_]{82})\b"),                       "GitHub Personal Access Token (fine-grained)"),
    ("github_oauth",             re.compile(r"\b(gho_[A-Za-z0-9]{36})\b"),                               "GitHub OAuth token"),
    ("github_user",              re.compile(r"\b(ghu_[A-Za-z0-9]{36})\b"),                               "GitHub user token"),
    ("github_server",            re.compile(r"\b(ghs_[A-Za-z0-9]{36})\b"),                               "GitHub server-to-server token"),
    ("github_refresh",           re.compile(r"\b(ghr_[A-Za-z0-9]{36})\b"),                               "GitHub refresh token"),
    ("stripe_secret",            re.compile(r"\b(sk_(?:test|live)_[A-Za-z0-9]{16,})\b"),                  "Stripe secret key"),
    ("stripe_publishable",       re.compile(r"\b(pk_(?:test|live)_[A-Za-z0-9]{16,})\b"),                  "Stripe publishable key"),
    ("stripe_restricted",        re.compile(r"\b(rk_(?:test|live)_[A-Za-z0-9]{16,})\b"),                  "Stripe restricted key"),
    ("aws_access_key",           re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),                                   "AWS access key ID"),
    ("aws_temp_key",             re.compile(r"\b(ASIA[0-9A-Z]{16})\b"),                                   "AWS temporary access key ID"),
    ("slack_bot",                re.compile(r"\b(xoxb-[0-9]+-[0-9]+-[0-9]+-[A-Za-z0-9]+)\b"),              "Slack bot token"),
    ("slack_user",               re.compile(r"\b(xoxp-[0-9]+-[0-9]+-[0-9]+-[A-Za-z0-9]+)\b"),              "Slack user token"),
    ("slack_app",                re.compile(r"\b(xoxa-[0-9]+-[0-9]+-[0-9]+-[A-Za-z0-9]+)\b"),              "Slack app token"),
    ("anthropic_api_key",        re.compile(r"\b(sk-ant-[A-Za-z0-9_\-]{20,})\b"),                          "Anthropic API key"),
    ("google_api_key",           re.compile(r"\b(AIza[A-Za-z0-9_\-]{35})\b"),                              "Google API key"),
    ("twilio_sid",               re.compile(r"\b(AC[a-f0-9]{32})\b"),                                      "Twilio Account SID"),
    ("sendgrid",                 re.compile(r"\b(SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43})\b"),          "SendGrid API key"),
    ("mailgun",                  re.compile(r"\b(key-[a-f0-9]{32})\b"),                                    "Mailgun API key"),
    ("supabase_service_role",    re.compile(r"\b(eyJ[A-Za-z0-9_\-]{20,}\.eyJ[A-Za-z0-9_\-]{50,}\.[A-Za-z0-9_\-]{20,})\b"), "JWT-shaped token (Supabase service role / generic JWT)"),
]

# ----- Assignment-shaped patterns (medium confidence) -----
# Catches `api_key = "..."` / `password: "..."` / `SECRET="..."` style.
ASSIGNMENT_PATTERNS = [
    (
        "assignment_api_key",
        re.compile(r"""(?ix)
            (?P<key>(?:api[_-]?key|apikey|client[_-]?secret|access[_-]?token|
                       auth[_-]?token|bearer[_-]?token|x[_-]?api[_-]?key|
                       service[_-]?key|private[_-]?key|secret[_-]?key)
            )\s*[:=]\s*
            (?P<quote>["'`])(?P<value>[A-Za-z0-9_+/=.\-]{20,})(?P=quote)
        """),
        "API key / token in assignment",
    ),
    (
        "assignment_password",
        re.compile(r"""(?ix)
            (?P<key>(?:password|passwd|pwd|db[_-]?password|database[_-]?password))
            \s*[:=]\s*
            (?P<quote>["'`])(?P<value>[^"'`]{8,})(?P=quote)
        """),
        "Password in assignment",
    ),
    (
        "assignment_db_url",
        re.compile(r"""(?ix)
            (?P<key>(?:database[_-]?url|db[_-]?url|conn(?:ection)?[_-]?string))
            \s*[:=]\s*
            (?P<quote>["'`])(?P<value>[a-z]+://[^"'`]*?:[^"'`]+@[^"'`]+)(?P=quote)
        """),
        "Database connection string with embedded password",
    ),
]

# URL-embedded credentials anywhere in source
URL_CRED_PATTERN = re.compile(
    r"""(?xi)
    \b(?P<scheme>https?|ftp|mongodb|postgres(?:ql)?|mysql|redis|amqp|amqps)://
    (?P<user>[^:/\s@'"]{1,128})
    :
    (?P<pass>[^@/\s'"]{6,256})
    @
    (?P<host>[^/\s'"]{1,256})
    """
)

# Optional: high-entropy literals not caught by the above
HIGH_ENTROPY_PATTERN = re.compile(
    r"""(?x)
    (?P<quote>["'`])
    (?P<value>[A-Za-z0-9+/=_\-]{32,})
    (?P=quote)
    """
)

# Lines that look like placeholders we shouldn't flag
PLACEHOLDER_MARKERS = re.compile(
    r"(?i)\b(your_|my_|example|placeholder|insert|todo|fixme|change[_-]?me|xxxx|0000+|aaaa+|none|null|undefined|^pass(?:word)?$|^secret$|^token$|^api[_-]?key$|^dummy$|^test$|^foo$|^bar$|^baz$)\b"
)


@dataclass
class Finding:
    severity: str            # critical | major | moderate | minor
    category: str            # provider_token | assignment | url_credential | high_entropy
    pattern_id: str
    description: str
    file: str
    line: int
    column: int
    matched_text: str
    masked_text: str
    suggested_op_reference: str
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def mask_secret(s: str, keep_start: int = 4, keep_end: int = 2) -> str:
    if len(s) <= keep_start + keep_end + 3:
        return "*" * len(s)
    return s[:keep_start] + "…" + "*" * (len(s) - keep_start - keep_end - 1) + s[-keep_end:]


def suggest_op_reference(vault: str, file_path: Path, key_label: str | None,
                         provider_hint: str | None = None) -> str:
    item = provider_hint or (key_label or file_path.stem.replace(" ", "-"))
    field = "credential"
    if key_label:
        kl = key_label.lower()
        if "password" in kl or "passwd" in kl or "pwd" in kl:
            field = "password"
        elif "token" in kl:
            field = "token"
        elif "secret" in kl:
            field = "secret"
        elif "key" in kl:
            field = "credential"
    safe_item = re.sub(r"[^A-Za-z0-9_-]", "-", item)[:40].strip("-") or "secret"
    return f"op://{vault}/{safe_item}/{field}"


def iter_source_files(root: Path, files: list[Path] | None,
                      include_tests: bool, include_env_example: bool) -> Iterable[Path]:
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
        if p.name in SKIP_FILENAMES:
            continue
        if any(p.name.endswith(suf) for suf in SKIP_SUFFIXES):
            continue
        # .env handling
        is_env = p.name.startswith(".env")
        if is_env:
            if p.name in (".env", ".env.local", ".env.development", ".env.production"):
                continue  # never scan real envs — those are expected to hold local secrets
            if not include_env_example and p.name.endswith((".example", ".sample", ".template")):
                continue  # by default skip examples too
            # Other .env.* (like .env.test) we WILL scan
        else:
            if p.suffix not in SCAN_EXTENSIONS:
                continue
        if not include_tests:
            lower_parts = [part.lower() for part in p.parts]
            if any(t in lower_parts for t in ("tests", "test", "__tests__", "spec", "specs", "fixtures", "mocks")):
                continue
            name = p.name.lower()
            if name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.ts") or name.endswith(".test.js") or name.endswith(".spec.ts") or name.endswith(".spec.js"):
                continue
        yield p


def scan_file(path: Path, vault: str, include_high_entropy: bool) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    seen_spans: set[tuple[int, int]] = set()

    # Provider tokens
    for pid, pattern, desc in PROVIDER_PATTERNS:
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            if span in seen_spans:
                continue
            seen_spans.add(span)
            line = text.count("\n", 0, m.start()) + 1
            col = m.start() - (text.rfind("\n", 0, m.start()) + 1) + 1
            raw = m.group(1)
            findings.append(Finding(
                severity="critical",
                category="provider_token",
                pattern_id=pid,
                description=desc,
                file=str(path),
                line=line,
                column=col,
                matched_text=raw,
                masked_text=mask_secret(raw),
                suggested_op_reference=suggest_op_reference(
                    vault, path, pid, provider_hint=pid.split("_")[0]
                ),
            ))

    # Assignment patterns
    for pid, pattern, desc in ASSIGNMENT_PATTERNS:
        for m in pattern.finditer(text):
            value = m.group("value")
            key_label = m.group("key")
            span = m.span("value")
            if span in seen_spans:
                continue
            # Skip placeholder-shaped values
            if PLACEHOLDER_MARKERS.search(value) or value.lower() in {"changeme", "test", "dummy"}:
                continue
            seen_spans.add(span)
            line = text.count("\n", 0, span[0]) + 1
            col = span[0] - (text.rfind("\n", 0, span[0]) + 1) + 1
            findings.append(Finding(
                severity="major",
                category="assignment",
                pattern_id=pid,
                description=desc,
                file=str(path),
                line=line,
                column=col,
                matched_text=value,
                masked_text=mask_secret(value),
                suggested_op_reference=suggest_op_reference(vault, path, key_label),
                note=f"Key label: '{key_label}'",
            ))

    # URL-embedded credentials
    for m in URL_CRED_PATTERN.finditer(text):
        span = m.span()
        if span in seen_spans:
            continue
        seen_spans.add(span)
        line = text.count("\n", 0, m.start()) + 1
        col = m.start() - (text.rfind("\n", 0, m.start()) + 1) + 1
        raw = m.group(0)
        passwd = m.group("pass")
        if PLACEHOLDER_MARKERS.search(passwd):
            continue
        host = m.group("host").split("/")[0].split("?")[0]
        findings.append(Finding(
            severity="critical",
            category="url_credential",
            pattern_id="url_embedded_password",
            description=f"{m.group('scheme')}:// URL with embedded password",
            file=str(path),
            line=line,
            column=col,
            matched_text=raw,
            masked_text=raw.replace(passwd, mask_secret(passwd)),
            suggested_op_reference=f"op://{vault}/{host}-{m.group('scheme')}/connection_string",
            note=f"User: {m.group('user')}, host: {host}",
        ))

    # Optional high-entropy scan
    if include_high_entropy:
        for m in HIGH_ENTROPY_PATTERN.finditer(text):
            span = m.span("value")
            if span in seen_spans:
                continue
            value = m.group("value")
            if PLACEHOLDER_MARKERS.search(value):
                continue
            ent = shannon_entropy(value)
            if ent < 4.5:
                continue
            # Skip common non-secret high-entropy: hash literals, version-y digits
            if re.match(r"^[0-9a-fA-F]{32,}$", value) and len(value) in (32, 40, 64, 96, 128):
                # Pure hex of standard lengths — probably hash, not credential
                # (but record at minor severity)
                seen_spans.add(span)
                line = text.count("\n", 0, span[0]) + 1
                col = span[0] - (text.rfind("\n", 0, span[0]) + 1) + 1
                findings.append(Finding(
                    severity="minor",
                    category="high_entropy",
                    pattern_id="hex_literal",
                    description=f"High-entropy hex literal ({len(value)} chars)",
                    file=str(path),
                    line=line,
                    column=col,
                    matched_text=value,
                    masked_text=mask_secret(value),
                    suggested_op_reference=suggest_op_reference(vault, path, None),
                    note="Often a hash value, not a secret. Review for false positive.",
                ))
                continue
            seen_spans.add(span)
            line = text.count("\n", 0, span[0]) + 1
            col = span[0] - (text.rfind("\n", 0, span[0]) + 1) + 1
            findings.append(Finding(
                severity="moderate",
                category="high_entropy",
                pattern_id="entropy",
                description=f"High-entropy literal (entropy={ent:.2f}, length={len(value)})",
                file=str(path),
                line=line,
                column=col,
                matched_text=value,
                masked_text=mask_secret(value),
                suggested_op_reference=suggest_op_reference(vault, path, None),
                note="Heuristic match — may be a hash, a random ID, or build-system noise. Review carefully.",
            ))

    return findings


def render_text(findings: list[Finding], scanned_count: int, root: Path) -> str:
    out = ["scan-hardcoded-secrets", "", f"Scanned: {scanned_count} file(s) under {root}", ""]
    if not findings:
        out.append("PASS — no hardcoded secret patterns matched.")
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
            out.append(f"  {f.file}:{f.line}:{f.column}  {f.description}")
            out.append(f"    matched: {f.masked_text}")
            out.append(f"    suggest: {f.suggested_op_reference}")
            if f.note:
                out.append(f"    note: {f.note}")
        out.append("")
    out.append("Replacement guide:")
    out.append("  - Move the real secret into a 1Password item.")
    out.append("  - Replace the literal in source with the suggested op:// reference.")
    out.append("  - Render at runtime via `op inject -i template -o out` or `op run -- <command>`.")
    out.append("  - See `/rad-1password:op-secrets-injection` for the full workflow.")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("project_root", nargs="?", default=".")
    p.add_argument("--files", help="Comma-separated list of files to scan (default: full tree)")
    p.add_argument("--include-tests", action="store_true", help="Scan test files too")
    p.add_argument("--include-env-example", action="store_true", help="Scan .env.example / .env.sample / .env.template")
    p.add_argument("--high-entropy", action="store_true", help="Also flag generic high-entropy string literals (higher false-positive rate)")
    p.add_argument("--vault", default="prod", help="Vault name to use in suggested op:// references (default: prod)")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    root = Path(args.project_root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: project root not found: {root}", file=sys.stderr)
        return 2

    files: list[Path] | None = None
    if args.files:
        files = [Path(f.strip()).resolve() for f in args.files.split(",") if f.strip()]

    all_findings: list[Finding] = []
    scanned = 0
    for path in iter_source_files(root, files, args.include_tests, args.include_env_example):
        scanned += 1
        all_findings.extend(scan_file(path, args.vault, args.high_entropy))

    if args.json:
        report = {
            "validator": "scan-hardcoded-secrets",
            "version": "1.0.0",
            "project_root": str(root),
            "files_scanned": scanned,
            "vault": args.vault,
            "include_tests": args.include_tests,
            "include_env_example": args.include_env_example,
            "high_entropy_mode": args.high_entropy,
            "findings": [f.to_dict() for f in all_findings],
        }
        print(json.dumps(report, indent=2))
    else:
        print(render_text(all_findings, scanned, root))

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

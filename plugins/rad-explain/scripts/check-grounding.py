#!/usr/bin/env python3
r"""
check-grounding.py — Flag claims in an output file that can't be traced to repo source.

Reads a Markdown output file (README, project-story, pitch, marketplace listing)
and a repo root. For each substantive claim in the output:

  1. Extract substantive tokens (proper nouns, numbers, technical terms, feature
     names, file paths, version numbers).
  2. Grep the repo for those tokens.
  3. If NONE of the substantive tokens appear anywhere in repo source, flag the
     claim as unbacked.

This is heuristic. It will:

  - Surface real unbacked claims (the validator's intended job)
  - Surface false positives (claims using only common words, or claims whose
    backing exists in commit messages / live data / external docs)
  - Miss claims whose tokens appear in the repo but aren't actually a source
    for the claim (e.g., "supports 30+ platforms" where "platforms" appears
    in unrelated context)

It is NOT a truth-checker. It is a "you might want to verify this" surfacer.
Real claim-source matching needs natural-language reasoning beyond stdlib
Python. The validator's job is mechanical: did the substantive content of
this claim leave ANY trace in the source?

Severity is calibrated conservatively:

  warning  — Claim contains substantive tokens; NONE found in repo source
  info     — Claim contains numbers/quantities but no matching numbers in repo
  (no critical) — Token absence is suggestive, not definitive

Usage:
  python3 check-grounding.py <file.md>
  python3 check-grounding.py <file.md> --repo /path/to/project
  python3 check-grounding.py <file.md> --json
  python3 check-grounding.py <file.md> --min-token-length 5   # stricter

Output:
  Default — human-readable text. Exit 1 on any warning.
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


@dataclass
class Claim:
    line: int
    text: str
    substantive_tokens: list[str] = field(default_factory=list)
    quant_tokens: list[str] = field(default_factory=list)


@dataclass
class Finding:
    severity: str           # warning | info
    code: str
    line: int
    claim_text: str
    unbacked_tokens: list[str]
    found_tokens: list[str]
    message: str
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# Source-file extensions we scan to find supporting evidence
SOURCE_EXTENSIONS = {
    ".md", ".txt", ".rst",                       # docs
    ".py", ".js", ".jsx", ".ts", ".tsx",         # mainstream code
    ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".php", ".cs", ".c", ".cpp", ".h",
    ".sh", ".bash", ".zsh", ".ps1",
    ".yml", ".yaml", ".toml", ".ini", ".cfg",
    ".json", ".xml", ".html", ".htm",
    ".sql", ".graphql",
    ".astro", ".svelte", ".vue",
    ".css", ".scss", ".sass", ".less",
}

DEFAULT_EXCLUDES = {
    "node_modules", ".venv", "venv", "env", ".env",
    "dist", "build", ".next", ".nuxt", ".astro", "out",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".git", ".svelte-kit", ".vercel", ".cache", ".turbo", "coverage",
    "target", ".gradle", ".idea", ".output",
}


# Stopword list — common words that don't count as substantive
STOPWORDS = frozenset({
    "a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "with",
    "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
    "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as",
    "do", "does", "did", "have", "has", "had", "having",
    "will", "would", "could", "should", "can", "may", "might", "must", "shall",
    "i", "you", "we", "they", "he", "she", "us", "them", "our", "your", "their",
    "all", "any", "some", "each", "every", "via", "from", "into", "than", "more",
    "less", "most", "least", "out", "over", "such", "even", "just", "yet",
    "very", "much", "many", "few", "several",
    "what", "which", "who", "whom",
    "not", "no", "nor", "so", "too", "also", "only", "own",
    "here", "there", "now", "today", "tomorrow", "yesterday",
    "good", "great", "nice", "fine", "well",
    "thing", "things", "stuff", "way", "ways", "case", "cases",
    "use", "used", "using", "uses", "make", "made", "makes", "making",
    "get", "got", "getting", "gets",
    "see", "look", "say", "said", "go", "going", "come", "came",
    "yes", "ok", "okay",
})

# Common technical filler words we don't treat as substantive
TECH_FILLER = frozenset({
    "code", "file", "files", "data", "input", "output",
    "user", "users", "system", "tool", "tools", "method", "methods",
    "function", "functions", "feature", "features",
    "support", "supports", "supported", "supporting",
    "include", "includes", "included", "including",
    "provide", "provides", "provided", "providing",
    "work", "works", "worked", "working",
    "run", "runs", "running",
    "show", "shows", "showed", "showing",
})

# Token patterns
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-./]*[a-zA-Z0-9]|\d+(?:\.\d+)*[+%]?|\$\d+(?:\.\d+)?")
SENTENCE_END_RE = re.compile(r"[.!?](?:\s|$)")

# Lines we skip outright (not claims).
# Skips: markdown headers (#), comments (//, --), bold-line (*), HTML comments (<!--),
# frontmatter delimiter (---), code fences (```, ~~~), table rows (|), and bullet lists.
SKIP_LINE_RE = re.compile(
    r"^\s*(?:#|//|--|\*\s|<!--|---|```|~~~|\||\d+\.\s|-\s|\+\s)"
)

# Inline elements to strip before tokenization
INLINE_STRIP_PATTERNS = [
    (re.compile(r"`[^`]*`"), " "),            # inline code
    (re.compile(r"\[([^\]]+)\]\([^)]+\)"), r"\1"),  # markdown links → just text
    (re.compile(r"\*\*([^*]+)\*\*"), r"\1"),  # bold
    (re.compile(r"\*([^*]+)\*"), r"\1"),      # italic
    (re.compile(r"_([^_]+)_"), r"\1"),        # italic
    (re.compile(r"~~([^~]+)~~"), r"\1"),      # strikethrough
]


def is_substantive_token(tok: str, min_length: int) -> bool:
    """Is this token substantive enough to be a grounding signal?"""
    if not tok:
        return False
    low = tok.lower()
    if low in STOPWORDS:
        return False
    if low in TECH_FILLER:
        return False
    if len(tok) < min_length and not any(c.isdigit() for c in tok):
        return False
    # Numbers, version-like, money-like → always substantive
    if any(c.isdigit() for c in tok):
        return True
    # Capitalized in middle of sentence → likely a proper noun / feature name
    if tok[0].isupper():
        return True
    # Hyphenated multi-word ("plan-first", "rad-planner")
    if "-" in tok and len(tok) >= min_length:
        return True
    # CamelCase
    if any(c.isupper() for c in tok[1:]):
        return True
    # Long lowercase technical terms
    if len(tok) >= 7:
        return True
    return False


def is_quant_token(tok: str) -> bool:
    """Does this token represent a quantity?"""
    return bool(re.match(r"^\$?\d+(?:\.\d+)*[+%]?$", tok))


def strip_inline_markup(line: str) -> str:
    for pattern, replacement in INLINE_STRIP_PATTERNS:
        line = pattern.sub(replacement, line)
    return line


def extract_claims(text: str, min_token_length: int) -> list[Claim]:
    """Walk the document line-by-line, extract sentences that look like claims."""
    claims: list[Claim] = []
    in_code_fence = False
    for line_idx, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if not stripped:
            continue
        if SKIP_LINE_RE.match(stripped):
            continue
        # Strip inline markup
        clean = strip_inline_markup(stripped)
        # Split into sentences (rough)
        sentences = SENTENCE_END_RE.split(clean)
        for s in sentences:
            s = s.strip()
            if len(s) < 20:  # too short to be a meaningful claim
                continue
            tokens = TOKEN_RE.findall(s)
            substantive = [
                t for t in tokens
                if is_substantive_token(t, min_token_length)
            ]
            quant = [t for t in tokens if is_quant_token(t)]
            if not substantive:
                continue  # No substantive tokens → not a checkable claim
            claims.append(Claim(
                line=line_idx,
                text=s[:200],
                substantive_tokens=substantive,
                quant_tokens=quant,
            ))
    return claims


def collect_repo_corpus(repo_root: Path) -> tuple[str, list[str]]:
    """Concatenate all source-file content. Returns (lowercased corpus, list of files scanned)."""
    parts: list[str] = []
    files_scanned: list[str] = []
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in DEFAULT_EXCLUDES for part in p.parts):
            continue
        if p.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        try:
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
            files_scanned.append(str(p.relative_to(repo_root)))
        except OSError:
            continue
    return "\n".join(parts).lower(), files_scanned


def check_token_in_corpus(token: str, corpus: str) -> bool:
    """Is this token's substantive form present in the corpus?"""
    low = token.lower()
    # Word-boundary match for alpha tokens; substring for tokens with punctuation
    if re.search(r"[a-zA-Z]", low) and not any(c in low for c in "-./_"):
        # Pure alpha → require word boundaries
        return bool(re.search(rf"\b{re.escape(low)}\b", corpus))
    # Tokens with structure (-, /, ., _) — substring is fine
    return low in corpus


def is_proper_noun_shaped(tok: str) -> bool:
    """A token that names something specific — capitalized, CamelCase, or hyphenated identifier."""
    if not tok or not tok[0].isalpha():
        return False
    if tok[0].isupper() and not tok.isupper():
        # "Faunero", "RAD", "OpenAI"
        return True
    if any(c.isupper() for c in tok[1:]):
        # CamelCase
        return True
    return False


def check_claims(claims: list[Claim], corpus: str) -> list[Finding]:
    """Check each claim against the corpus. Proper-noun-shaped tokens get strict treatment
    (any missing → warning). Other substantive tokens get loose treatment (most missing → info)."""
    findings: list[Finding] = []
    for c in claims:
        # Partition substantive tokens by shape
        proper_tokens = [t for t in c.substantive_tokens if is_proper_noun_shaped(t)]
        other_tokens = [t for t in c.substantive_tokens if not is_proper_noun_shaped(t)]

        proper_found: list[str] = []
        proper_missing: list[str] = []
        for t in proper_tokens:
            if check_token_in_corpus(t, corpus):
                proper_found.append(t)
            else:
                proper_missing.append(t)

        other_found: list[str] = []
        other_missing: list[str] = []
        for t in other_tokens:
            if check_token_in_corpus(t, corpus):
                other_found.append(t)
            else:
                other_missing.append(t)

        # Rule 1: ANY proper-noun-shaped token missing → warning (specific named thing not in repo)
        if proper_missing:
            findings.append(Finding(
                severity="warning",
                code="unbacked_proper_noun",
                line=c.line,
                claim_text=c.text,
                unbacked_tokens=proper_missing,
                found_tokens=proper_found + other_found,
                message=f"Claim names {len(proper_missing)} proper-noun-shaped term(s) not found in repo source: {', '.join(proper_missing[:5])}.",
                fix="Either remove these specific names from the claim, or add evidence in the repo (a doc, code, or ADR mentioning them).",
            ))
            continue

        # Rule 2: No proper nouns AND most other-substantive tokens missing
        if not proper_tokens and other_tokens:
            miss_ratio = len(other_missing) / len(other_tokens)
            if miss_ratio >= 0.75 and len(other_missing) >= 2:
                findings.append(Finding(
                    severity="info",
                    code="claim_lightly_grounded",
                    line=c.line,
                    claim_text=c.text,
                    unbacked_tokens=other_missing,
                    found_tokens=other_found,
                    message=f"Claim has {len(other_missing)}/{len(other_tokens)} substantive tokens not traceable to repo source.",
                    fix="The claim may be using generic vocabulary that happens to not appear in source. Verify intent.",
                ))
                continue

        # Rule 3: total absence (no proper nouns, all other tokens missing)
        if not proper_tokens and other_tokens and not other_found:
            findings.append(Finding(
                severity="warning",
                code="claim_unbacked",
                line=c.line,
                claim_text=c.text,
                unbacked_tokens=other_missing,
                found_tokens=[],
                message="Claim has no substantive tokens traceable to repo source.",
                fix="Add repo evidence, cite an external source, or rephrase to remove unbacked specifics.",
            ))
            continue

    return findings


def render_text(findings: list[Finding], source: str, repo_root: Path,
                claim_count: int, file_count: int) -> str:
    out = [f"check-grounding: {source}", ""]
    out.append(f"Output file:        {source}")
    out.append(f"Repo root:          {repo_root}")
    out.append(f"Claims extracted:   {claim_count}")
    out.append(f"Repo files scanned: {file_count}")
    out.append("")
    if not findings:
        out.append("PASS — every claim has at least one substantive token traceable to repo source.")
        return "\n".join(out)
    by_sev = {"warning": [], "info": []}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    for sev in ("warning", "info"):
        items = by_sev.get(sev, [])
        if not items:
            continue
        out.append(f"[{sev.upper()}] {len(items)} unbacked claim{'s' if len(items) != 1 else ''}")
        for f in items:
            out.append(f"  line {f.line}: {f.claim_text}")
            out.append(f"    unbacked tokens: {', '.join(f.unbacked_tokens[:8])}{' …' if len(f.unbacked_tokens) > 8 else ''}")
            if f.fix:
                out.append(f"    fix: {f.fix}")
        out.append("")
    out.append("Heuristic note: token absence is suggestive, not definitive. The validator surfaces candidates; you judge whether each is a real unbacked claim or has evidence the corpus doesn't capture (commit messages, external docs, live data).")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("file", help="Output Markdown file to check")
    p.add_argument("--repo", default=".", help="Repo root (default: current dir)")
    p.add_argument("--min-token-length", type=int, default=4,
                   help="Min length for alpha-only tokens to count as substantive (default: 4)")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    output_path = Path(args.file).resolve()
    if not output_path.exists() or not output_path.is_file():
        print(f"error: output file not found: {output_path}", file=sys.stderr)
        return 2

    repo_root = Path(args.repo).resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"error: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    try:
        text = output_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"error: cannot read output: {e}", file=sys.stderr)
        return 2

    claims = extract_claims(text, args.min_token_length)
    corpus, files = collect_repo_corpus(repo_root)
    findings = check_claims(claims, corpus)

    if args.json:
        out = {
            "validator": "check-grounding",
            "version": "1.0.0",
            "output_file": str(output_path),
            "repo_root": str(repo_root),
            "claims_extracted": len(claims),
            "repo_files_scanned": len(files),
            "min_token_length": args.min_token_length,
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_text(findings, str(output_path), repo_root, len(claims), len(files)))

    has_blocker = any(f.severity == "warning" for f in findings)
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

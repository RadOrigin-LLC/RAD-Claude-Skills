#!/usr/bin/env python3
r"""
check-hallucinated-imports.py — Mechanical detection of AI Pattern #1.

Pattern #1 in `references/ai-slop-patterns.md` ("Hallucinated Imports") is
literally mechanically checkable. This validator does the check, so the LLM
review phases can focus on the patterns that need judgment.

For each Python/JS/TS source file in the target directory (or specified files):

  1. Extract imports (Python `ast` module; JS/TS regex).
  2. Classify each import: stdlib | relative | external | scoped | submodule.
  3. For external imports: verify the package exists in a project lockfile.
  4. For relative imports: verify the file path resolves.

Lockfile support:

  - JavaScript: package-lock.json (npm v1 / v2+), yarn.lock, pnpm-lock.yaml,
    package.json dependencies / devDependencies / peerDependencies.
  - Python: requirements.txt, pyproject.toml (project.dependencies and
    tool.poetry.dependencies), Pipfile.lock, poetry.lock, uv.lock.

Python package name normalization (PEP 503) is partial: lockfile entries are
compared in both their declared form and a `replace('-', '_')` form so that
`python-dotenv` in requirements.txt matches `import dotenv`-style imports.
False negatives are preferred over false positives — under-flag rather than
over-flag, since slopsquatting is the harm we're trying to prevent.

Usage:
  python3 check-hallucinated-imports.py <project-root>
  python3 check-hallucinated-imports.py <project-root> --files src/a.py,src/b.ts
  python3 check-hallucinated-imports.py <project-root> --json
  python3 check-hallucinated-imports.py <project-root> --include-tests

Output:
  Default — human-readable text. Exit 1 if findings present.
  --json   — single JSON object on stdout.
  Exit 2   — script error.

No third-party dependencies. Python 3.8+ (3.11+ uses tomllib for cleaner
pyproject.toml parsing; 3.8-3.10 falls back to regex).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

try:
    import tomllib  # 3.11+
    HAS_TOMLLIB = True
except ImportError:
    HAS_TOMLLIB = False


# Source file extensions we scan
PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".mjs", ".cjs"}
TS_EXT = {".ts", ".tsx", ".mts", ".cts"}
JS_TS_EXT = JS_EXT | TS_EXT

DEFAULT_EXCLUDES = {
    "node_modules", ".venv", "venv", "env", ".env",
    "dist", "build", ".next", ".nuxt", ".astro", "out",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".git", ".svelte-kit", ".vercel", ".cache", ".turbo",
    "coverage",
}

# Python stdlib (3.8+). Trimmed list of common modules; we also use
# sys.stdlib_module_names where available (3.10+).
PY_STDLIB_FALLBACK = frozenset({
    "abc", "argparse", "array", "ast", "asyncio", "base64", "binascii",
    "builtins", "bz2", "calendar", "cgi", "cmath", "cmd", "code", "codecs",
    "collections", "colorsys", "concurrent", "configparser", "contextlib",
    "contextvars", "copy", "csv", "ctypes", "curses", "dataclasses",
    "datetime", "decimal", "difflib", "dis", "doctest", "email", "encodings",
    "enum", "errno", "faulthandler", "filecmp", "fileinput", "fnmatch",
    "fractions", "ftplib", "functools", "gc", "getopt", "getpass", "gettext",
    "glob", "graphlib", "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "imaplib", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "keyword", "linecache", "locale", "logging", "lzma", "mailbox", "marshal",
    "math", "mimetypes", "mmap", "multiprocessing", "netrc", "numbers", "operator",
    "optparse", "os", "pathlib", "pickle", "pickletools", "pkgutil", "platform",
    "plistlib", "poplib", "posix", "posixpath", "pprint", "profile", "pstats",
    "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue", "quopri", "random",
    "re", "readline", "reprlib", "resource", "rlcompleter", "runpy", "sched",
    "secrets", "select", "selectors", "shelve", "shlex", "shutil", "signal",
    "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "sqlite3",
    "ssl", "stat", "statistics", "string", "stringprep", "struct", "subprocess",
    "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny", "tarfile",
    "telnetlib", "tempfile", "termios", "test", "textwrap", "threading", "time",
    "timeit", "tkinter", "token", "tokenize", "tomllib", "trace", "traceback",
    "tracemalloc", "tty", "turtle", "types", "typing", "unicodedata", "unittest",
    "urllib", "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
    "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp",
    "zipfile", "zipimport", "zlib", "zoneinfo", "__future__",
})

# Built-in JS modules (Node)
JS_BUILTINS = frozenset({
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console",
    "constants", "crypto", "dgram", "dns", "domain", "events", "fs", "http",
    "http2", "https", "inspector", "module", "net", "os", "path", "perf_hooks",
    "process", "punycode", "querystring", "readline", "repl", "stream",
    "string_decoder", "sys", "timers", "tls", "trace_events", "tty", "url",
    "util", "v8", "vm", "wasi", "worker_threads", "zlib",
    # node: prefix forms handled separately
})


def _py_stdlib_set() -> frozenset:
    """Return Python's stdlib module set, preferring runtime data."""
    names = getattr(sys, "stdlib_module_names", None)
    if names:
        return frozenset(names)
    return PY_STDLIB_FALLBACK


# JS/TS import-extraction regex
JS_IMPORT_PATTERNS = [
    # import X from 'pkg' | import {X} from 'pkg' | import 'pkg' | import * as X from 'pkg'
    re.compile(r"^\s*import\s+(?:[^'\"]*?from\s+)?[\"']([^\"']+)[\"']", re.MULTILINE),
    # import('pkg') dynamic
    re.compile(r"\bimport\s*\(\s*[\"']([^\"']+)[\"']\s*\)"),
    # require('pkg') | require(`pkg`)
    re.compile(r"\brequire\s*\(\s*[\"'`]([^\"'`]+)[\"'`]\s*\)"),
    # export ... from 'pkg'
    re.compile(r"^\s*export\s+[^'\"]*?from\s+[\"']([^\"']+)[\"']", re.MULTILINE),
]


@dataclass
class ImportRef:
    file: str
    line: int
    statement: str
    raw_module: str          # As written in source (e.g., 'lodash/debounce', '.foo', 'pkg')
    language: str            # python | javascript | typescript
    kind: str                # external | relative | stdlib | builtin | scoped | submodule


@dataclass
class Finding:
    id_suggestion: str
    severity: str           # critical | major | moderate | minor
    category: str           # dependency
    confidence: str         # confirmed | probable | possible
    blocks_release: str     # yes | no | conditional
    title: str
    file: str
    line: int
    import_statement: str
    language: str
    evidence: str
    recommended_fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ----- Lockfile parsers -----

def _normalize_py(name: str) -> str:
    """PEP 503 + import-name guess. Returns lowercase normalized form."""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def parse_requirements_txt(path: Path) -> set[str]:
    pkgs: set[str] = set()
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Strip extras and version specifiers
            name = re.split(r"[<>=!~;\[\s]", line, 1)[0]
            if name:
                pkgs.add(_normalize_py(name))
    except OSError:
        pass
    return pkgs


def parse_pyproject_toml(path: Path) -> set[str]:
    pkgs: set[str] = set()
    try:
        if HAS_TOMLLIB:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            # PEP 621
            project = data.get("project", {})
            for dep in project.get("dependencies", []) or []:
                name = re.split(r"[<>=!~;\[\s]", dep, 1)[0]
                if name:
                    pkgs.add(_normalize_py(name))
            for group, deps in (project.get("optional-dependencies") or {}).items():
                for dep in deps:
                    name = re.split(r"[<>=!~;\[\s]", dep, 1)[0]
                    if name:
                        pkgs.add(_normalize_py(name))
            # Poetry section
            poetry = data.get("tool", {}).get("poetry", {})
            for section in ("dependencies", "dev-dependencies"):
                d = poetry.get(section, {}) or {}
                for name in d:
                    if name.lower() != "python":
                        pkgs.add(_normalize_py(name))
            for group_data in (poetry.get("group") or {}).values():
                for name in group_data.get("dependencies", {}) or {}:
                    if name.lower() != "python":
                        pkgs.add(_normalize_py(name))
        else:
            # Regex fallback — extract `name = "..."` lines under [tool.poetry.dependencies]
            text = path.read_text(encoding="utf-8", errors="replace")
            # Naive: find [project] dependencies array
            m = re.search(r"\[project\][^\[]*?dependencies\s*=\s*\[(.*?)\]", text, re.DOTALL)
            if m:
                for s in re.findall(r"[\"']([^\"']+)[\"']", m.group(1)):
                    name = re.split(r"[<>=!~;\[\s]", s, 1)[0]
                    if name:
                        pkgs.add(_normalize_py(name))
            # Poetry deps
            in_poetry = False
            for raw in text.splitlines():
                line = raw.strip()
                if line.startswith("[tool.poetry.dependencies]") or line.startswith("[tool.poetry.dev-dependencies]"):
                    in_poetry = True
                    continue
                if line.startswith("[") and in_poetry:
                    in_poetry = False
                if in_poetry and "=" in line and not line.startswith("#"):
                    name = line.split("=", 1)[0].strip()
                    if name and name.lower() != "python":
                        pkgs.add(_normalize_py(name))
    except (OSError, Exception):
        pass
    return pkgs


def parse_pipfile_lock(path: Path) -> set[str]:
    pkgs: set[str] = set()
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        for section in ("default", "develop"):
            for name in (data.get(section) or {}):
                pkgs.add(_normalize_py(name))
    except (OSError, ValueError):
        pass
    return pkgs


def parse_poetry_lock(path: Path) -> set[str]:
    pkgs: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^\s*name\s*=\s*[\"']([^\"']+)[\"']", text, re.MULTILINE):
            pkgs.add(_normalize_py(m.group(1)))
    except OSError:
        pass
    return pkgs


def parse_uv_lock(path: Path) -> set[str]:
    # Same shape as poetry.lock for our purposes
    return parse_poetry_lock(path)


def parse_package_lock_json(path: Path) -> set[str]:
    pkgs: set[str] = set()
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return pkgs
    # v2+ has 'packages' keyed by path; v1 has 'dependencies' keyed by name
    for key in (data.get("packages") or {}):
        if not key:
            continue
        # Extract package name from 'node_modules/<name>' or 'node_modules/@scope/name'
        if key.startswith("node_modules/"):
            tail = key[len("node_modules/"):]
            # Handle nested: 'node_modules/foo/node_modules/bar' → use the LAST node_modules segment
            if "node_modules/" in tail:
                tail = tail.rsplit("node_modules/", 1)[1]
            if tail.startswith("@"):
                # @scope/name → keep first two segments
                parts = tail.split("/")
                if len(parts) >= 2:
                    pkgs.add(f"{parts[0]}/{parts[1]}")
            else:
                pkgs.add(tail.split("/")[0])
    for name in (data.get("dependencies") or {}):
        pkgs.add(name)
    return pkgs


def parse_yarn_lock(path: Path) -> set[str]:
    pkgs: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return pkgs
    # Top-level entries look like:  "pkg@version":  or  "@scope/name@version":  or comma-separated lists
    for raw in text.splitlines():
        if not raw or raw.startswith(" "):
            continue
        line = raw.strip().rstrip(":")
        if not line:
            continue
        # Strip outer quotes
        if line.startswith('"') and line.endswith('"'):
            line = line[1:-1]
        # Split on comma for "pkg@a, pkg@b" style
        for entry in line.split(","):
            entry = entry.strip().strip('"')
            if not entry:
                continue
            # @scope/name@version vs name@version
            if entry.startswith("@"):
                m = re.match(r"^(@[^/]+/[^@]+)@", entry)
            else:
                m = re.match(r"^([^@]+)@", entry)
            if m:
                pkgs.add(m.group(1))
    return pkgs


def parse_pnpm_lock_yaml(path: Path) -> set[str]:
    pkgs: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return pkgs
    # Top-level package entries look like:  /pkg@version:  or  /@scope/name@version:
    for m in re.finditer(r"^\s*/(@?[^/:]+(?:/[^/:]+)?)@", text, re.MULTILINE):
        pkgs.add(m.group(1))
    # Older pnpm format with quotes
    for m in re.finditer(r"^\s*\"?/(@?[^/:\"]+(?:/[^/:\"]+)?)@", text, re.MULTILINE):
        pkgs.add(m.group(1))
    return pkgs


def parse_package_json_deps(path: Path) -> set[str]:
    pkgs: set[str] = set()
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        for section in ("dependencies", "devDependencies", "peerDependencies",
                        "optionalDependencies"):
            for name in (data.get(section) or {}):
                pkgs.add(name)
    except (OSError, ValueError):
        pass
    return pkgs


def build_lockfile_index(project_root: Path) -> tuple[set[str], set[str], list[str]]:
    """Return (js_packages, py_packages_normalized, lockfiles_used)."""
    js_pkgs: set[str] = set()
    py_pkgs: set[str] = set()
    used: list[str] = []

    for filename, parser, target in [
        ("package-lock.json", parse_package_lock_json, js_pkgs),
        ("yarn.lock", parse_yarn_lock, js_pkgs),
        ("pnpm-lock.yaml", parse_pnpm_lock_yaml, js_pkgs),
        ("package.json", parse_package_json_deps, js_pkgs),
        ("requirements.txt", parse_requirements_txt, py_pkgs),
        ("pyproject.toml", parse_pyproject_toml, py_pkgs),
        ("Pipfile.lock", parse_pipfile_lock, py_pkgs),
        ("poetry.lock", parse_poetry_lock, py_pkgs),
        ("uv.lock", parse_uv_lock, py_pkgs),
    ]:
        path = project_root / filename
        if path.exists():
            target.update(parser(path))
            used.append(filename)
    return js_pkgs, py_pkgs, used


# ----- Import extraction -----

def extract_python_imports(path: Path) -> list[ImportRef]:
    refs: list[ImportRef] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text, filename=str(path))
    except (OSError, SyntaxError):
        return refs
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                refs.append(ImportRef(
                    file=str(path), line=node.lineno,
                    statement=f"import {alias.name}",
                    raw_module=alias.name,
                    language="python", kind="",  # Filled in classify step
                ))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # Relative import
                mod = node.module or ""
                refs.append(ImportRef(
                    file=str(path), line=node.lineno,
                    statement=f"from {'.' * node.level}{mod} import …",
                    raw_module="." * node.level + mod,
                    language="python", kind="relative",
                ))
            elif node.module:
                refs.append(ImportRef(
                    file=str(path), line=node.lineno,
                    statement=f"from {node.module} import …",
                    raw_module=node.module,
                    language="python", kind="",
                ))
    return refs


def extract_js_imports(path: Path) -> list[ImportRef]:
    refs: list[ImportRef] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return refs
    lang = "typescript" if path.suffix in TS_EXT else "javascript"
    seen: set[tuple[int, str]] = set()
    for pattern in JS_IMPORT_PATTERNS:
        for m in pattern.finditer(text):
            spec = m.group(1)
            # Compute line number from byte offset
            line = text.count("\n", 0, m.start()) + 1
            if (line, spec) in seen:
                continue
            seen.add((line, spec))
            refs.append(ImportRef(
                file=str(path), line=line,
                statement=m.group(0).strip().split("\n")[0][:120],
                raw_module=spec,
                language=lang, kind="",
            ))
    return refs


def classify_import(ref: ImportRef, py_stdlib: frozenset) -> ImportRef:
    """Set ref.kind based on the raw module string and language."""
    mod = ref.raw_module
    if ref.language == "python":
        if mod.startswith("."):
            ref.kind = "relative"
            return ref
        base = mod.split(".", 1)[0]
        if base in py_stdlib:
            ref.kind = "stdlib"
        elif "." in mod:
            ref.kind = "submodule"
        else:
            ref.kind = "external"
        return ref
    # JS/TS
    if mod.startswith(".") or mod.startswith("/"):
        ref.kind = "relative"
        return ref
    # node: builtin prefix
    if mod.startswith("node:"):
        ref.kind = "builtin"
        return ref
    base = mod.split("/", 1)[0]
    if base.startswith("@"):
        # @scope/name → use first two segments
        parts = mod.split("/")
        if len(parts) >= 2:
            ref.raw_module = f"{parts[0]}/{parts[1]}"
            ref.kind = "scoped" if len(parts) == 2 else "submodule"
        else:
            ref.kind = "scoped"
    elif base in JS_BUILTINS:
        ref.kind = "builtin"
    elif "/" in mod:
        ref.kind = "submodule"
    else:
        ref.kind = "external"
    return ref


def base_package(ref: ImportRef) -> str:
    """For external/scoped/submodule imports, return the base package name to look up."""
    mod = ref.raw_module
    if ref.language == "python":
        return mod.split(".", 1)[0]
    if mod.startswith("@"):
        parts = mod.split("/")
        return f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else mod
    return mod.split("/", 1)[0]


def py_lockfile_has(pkg: str, lock: set[str]) -> bool:
    """Match an imported Python module name against lockfile packages.

    Tries: (1) normalized direct match, (2) normalized with `_`→`-` swap.
    """
    if not pkg:
        return False
    cand = _normalize_py(pkg)
    if cand in lock:
        return True
    # An import like `dotenv` may come from `python-dotenv` in lockfile.
    # Try the heuristic: any lockfile entry whose `_`-form ends with the import name.
    underscore = pkg.replace("-", "_").lower()
    for entry in lock:
        # Compare in import-name shape
        import_form = entry.replace("-", "_")
        if import_form == underscore:
            return True
        if import_form.endswith(f"_{underscore}") and len(import_form) - len(underscore) <= 16:
            # e.g. python-dotenv ('python_dotenv') ends with '_dotenv'
            return True
    return False


def resolve_relative_python(ref: ImportRef, source_file: Path,
                            project_root: Path) -> tuple[bool, str]:
    """Resolve a relative Python import. Returns (exists, attempted_path)."""
    mod = ref.raw_module
    level = len(mod) - len(mod.lstrip("."))
    rest = mod[level:].lstrip(".")
    # Walk up `level` parents from source file
    base = source_file.parent
    for _ in range(level - 1):
        base = base.parent
    if rest:
        target_parts = rest.split(".")
        candidate_module = base / Path(*target_parts).with_suffix(".py")
        candidate_pkg = base / Path(*target_parts) / "__init__.py"
        if candidate_module.exists() or candidate_pkg.exists():
            return True, str(candidate_module)
        return False, str(candidate_module)
    # `from . import X` — base dir must exist
    if base.is_dir():
        return True, str(base)
    return False, str(base)


def resolve_relative_js(ref: ImportRef, source_file: Path) -> tuple[bool, str]:
    """Resolve a relative JS/TS import. Returns (exists, attempted_path)."""
    base = (source_file.parent / ref.raw_module).resolve()
    # Try common extensions
    for ext in ("", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
        if base.with_suffix(ext).exists() if ext else base.exists():
            return True, str(base) + ext
    # Try as directory with index
    for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs"):
        if (base / f"index{ext}").exists():
            return True, str(base / f"index{ext}")
    return False, str(base)


# ----- Main detection -----

def iter_source_files(root: Path, files: list[Path] | None,
                      include_tests: bool) -> Iterable[Path]:
    if files:
        for f in files:
            if f.is_file():
                yield f
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in (PY_EXT | JS_TS_EXT):
            continue
        if any(part in DEFAULT_EXCLUDES for part in p.parts):
            continue
        if not include_tests:
            name = p.name.lower()
            if "test" in p.parts or "__tests__" in p.parts or "tests" in p.parts:
                continue
            if name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.ts") or name.endswith(".test.js"):
                continue
        yield p


def check_imports(root: Path, files: list[Path] | None,
                  include_tests: bool) -> tuple[list[ImportRef], list[Finding],
                                                dict]:
    py_stdlib = _py_stdlib_set()
    js_pkgs, py_pkgs, lockfiles_used = build_lockfile_index(root)

    refs: list[ImportRef] = []
    findings: list[Finding] = []
    finding_seq = 0

    has_js_lock = bool(js_pkgs)
    has_py_lock = bool(py_pkgs)

    for source in iter_source_files(root, files, include_tests):
        if source.suffix in PY_EXT:
            raw_refs = extract_python_imports(source)
        elif source.suffix in JS_TS_EXT:
            raw_refs = extract_js_imports(source)
        else:
            continue

        for r in raw_refs:
            r = classify_import(r, py_stdlib)
            refs.append(r)

            if r.kind in ("stdlib", "builtin"):
                continue

            if r.kind == "relative":
                if r.language == "python":
                    ok, attempted = resolve_relative_python(r, source, root)
                else:
                    ok, attempted = resolve_relative_js(r, source)
                if not ok:
                    finding_seq += 1
                    findings.append(Finding(
                        id_suggestion=f"CR-HALLUC-{finding_seq:03d}",
                        severity="major",
                        category="dependency",
                        confidence="confirmed",
                        blocks_release="yes",
                        title=f"Unresolved relative import: '{r.raw_module}'",
                        file=r.file,
                        line=r.line,
                        import_statement=r.statement,
                        language=r.language,
                        evidence=f"Tried to resolve to: {attempted}",
                        recommended_fix="Fix the path, or remove the import if it was added speculatively.",
                    ))
                continue

            if r.kind in ("external", "scoped", "submodule"):
                pkg = base_package(r)
                if r.language == "python":
                    if not has_py_lock:
                        continue  # No lockfile means we can't be authoritative
                    if not py_lockfile_has(pkg, py_pkgs):
                        finding_seq += 1
                        findings.append(Finding(
                            id_suggestion=f"CR-HALLUC-{finding_seq:03d}",
                            severity="major",
                            category="dependency",
                            confidence="confirmed",
                            blocks_release="yes",
                            title=f"Hallucinated import: Python package '{pkg}' not in any lockfile",
                            file=r.file,
                            line=r.line,
                            import_statement=r.statement,
                            language=r.language,
                            evidence=(f"Lockfiles scanned: {', '.join(lockfiles_used) or '(none)'}. "
                                      f"Package '{pkg}' (normalized: '{_normalize_py(pkg)}') "
                                      f"is not declared as a dependency. "
                                      f"Slopsquatting risk if the name is close to a real package."),
                            recommended_fix=("Verify the package exists on PyPI. If the name is wrong, "
                                             "fix the import. If the dependency was meant to be added, "
                                             "declare it in requirements.txt or pyproject.toml. "
                                             "Do NOT install a package matching this name without verifying it's the intended one."),
                        ))
                else:
                    if not has_js_lock:
                        continue
                    if pkg not in js_pkgs:
                        finding_seq += 1
                        findings.append(Finding(
                            id_suggestion=f"CR-HALLUC-{finding_seq:03d}",
                            severity="major",
                            category="dependency",
                            confidence="confirmed",
                            blocks_release="yes",
                            title=f"Hallucinated import: npm package '{pkg}' not in any lockfile",
                            file=r.file,
                            line=r.line,
                            import_statement=r.statement,
                            language=r.language,
                            evidence=(f"Lockfiles scanned: {', '.join(lockfiles_used) or '(none)'}. "
                                      f"Package '{pkg}' is not declared as a dependency. "
                                      f"Slopsquatting risk if the name is close to a real package."),
                            recommended_fix=("Verify the package exists on npm. If the name is wrong, "
                                             "fix the import. If the dependency was meant to be added, "
                                             "declare it in package.json. "
                                             "Do NOT install a package matching this name without verifying it's the intended one."),
                        ))

    summary = {
        "files_scanned": len({r.file for r in refs}),
        "imports_seen": len(refs),
        "lockfiles_used": lockfiles_used,
        "js_packages_known": len(js_pkgs),
        "py_packages_known": len(py_pkgs),
        "no_lockfile_skipped": (not has_js_lock or not has_py_lock),
    }
    return refs, findings, summary


def render_text(findings: list[Finding], summary: dict) -> str:
    out = ["check-hallucinated-imports", ""]
    out.append(f"Files scanned:    {summary['files_scanned']}")
    out.append(f"Imports seen:     {summary['imports_seen']}")
    out.append(f"Lockfiles used:   {', '.join(summary['lockfiles_used']) or '(none — analysis limited)'}")
    out.append(f"JS packages:      {summary['js_packages_known']}")
    out.append(f"Python packages:  {summary['py_packages_known']}")
    out.append("")
    if not findings:
        out.append("PASS — no hallucinated imports detected.")
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
            out.append(f"  {f.id_suggestion}  {f.title}")
            out.append(f"    {f.file}:{f.line}")
            out.append(f"    {f.import_statement}")
            out.append(f"    {f.evidence}")
            if f.recommended_fix:
                out.append(f"    Fix: {f.recommended_fix}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("project_root", nargs="?", default=".",
                   help="Project root (default: current directory)")
    p.add_argument("--files", help="Comma-separated list of source files to scan (default: full tree)")
    p.add_argument("--include-tests", action="store_true",
                   help="Scan test files too (default: skip)")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    root = Path(args.project_root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: project root not found: {root}", file=sys.stderr)
        return 2

    files: list[Path] | None = None
    if args.files:
        files = [Path(f.strip()).resolve() for f in args.files.split(",") if f.strip()]

    refs, findings, summary = check_imports(root, files, args.include_tests)

    if args.json:
        out = {
            "validator": "check-hallucinated-imports",
            "version": "1.0.0",
            "project_root": str(root),
            "scanned": summary,
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_text(findings, summary))

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

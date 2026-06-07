#!/usr/bin/env python3
"""
detect-resources.py — Deterministic resource detection (MCPs + CLIs).

Reads the project's MCP/Claude config and infers available CLIs from marker
files. Returns structured JSON for /init and /startup Phase 2.5 to consume.

This script does NOT exec any binary by default. With --check-clis it runs
`which` (or `where` on Windows) for the inferred CLI names — useful at /init
time to flag missing CLIs the project assumes.

Used by:
  - /init   — one-time: warn if CLIs the stack assumes aren't installed
  - /startup Phase 2.5 — per-session: surface what's available to the agent

Usage:
  python3 detect-resources.py <project-root>
  python3 detect-resources.py <project-root> --json
  python3 detect-resources.py <project-root> --check-clis  # verify CLIs in PATH
  python3 detect-resources.py <project-root> --include-env-names
  python3 detect-resources.py <project-root> --json --cache  # use mtime-keyed cache (3.5)

Cache mode (--cache, added in 3.5):
  - Cache file: <root>/.claude/cache/resources.json
  - Hit when every input file's mtime matches the cache's recorded signature.
  - Inputs covered: .mcp.json, .claude/settings.json, CLAUDE.md, .env.example,
    every marker file from the CLI_MARKERS table, plus this script itself.
  - Miss → recompute, overwrite cache, return fresh data.
  - Skipped when --check-clis is passed (PATH lookups must be live).

Output (JSON):
  {
    "root": "/path/to/project",
    "mcp_servers": ["supabase", "stripe", ...],
    "stack_clis": [{"name": "supabase", "marker": "supabase/config.toml", "in_path": true}, ...],
    "documented_resources": [...],   # parsed from CLAUDE.md ## Resources section
    "env_template_vars": [...],       # only if --include-env-names
    "drift": {                         # comparison: documented vs detected
      "documented_but_missing": [...],
      "detected_but_undocumented": [...]
    },
    "cache_status": "hit" | "miss" | "disabled"   # only when --cache is passed
  }

Pure stdlib Python 3.8+. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

# Marker file → CLI name mapping (mirrors rad-session's stack marker table).
# Keep in sync with detect-stack.py and skills/startup/SKILL.md Phase 2.5.2.
CLI_MARKERS: list[tuple[str, str]] = [
    ("supabase/config.toml", "supabase"),
    ("wrangler.toml", "wrangler"),
    ("wrangler.jsonc", "wrangler"),
    ("netlify.toml", "netlify"),
    ("vercel.json", "vercel"),
    ("fly.toml", "flyctl"),
    ("firebase.json", "firebase"),
    (".github/workflows", "gh"),
    ("Dockerfile", "docker"),
    ("docker-compose.yml", "docker"),
    ("docker-compose.yaml", "docker"),
    ("compose.yaml", "docker"),
    ("compose.yml", "docker"),
    ("coolify.json", "coolify"),
    (".coolify", "coolify"),
    ("terraform", "terraform"),
    ("pulumi.yaml", "pulumi"),
    ("pyproject.toml", "poetry"),  # only if poetry.lock exists — checked below
    ("Pipfile", "pipenv"),
    ("Gemfile", "bundle"),
    ("deno.json", "deno"),
    ("deno.jsonc", "deno"),
    ("bun.lockb", "bun"),
    ("bunfig.toml", "bun"),
    ("Cargo.toml", "cargo"),
    ("rust-toolchain.toml", "cargo"),
    ("go.mod", "go"),
    ("mise.toml", "mise"),
    (".mise.toml", "mise"),
    (".tool-versions", "asdf"),
    ("flake.nix", "nix"),
    ("shell.nix", "nix"),
    ("devbox.json", "devbox"),
]

RESOURCES_HEADING_RE = re.compile(
    r"^##\s+(?:Resources|MCP|MCPs|Tools|CLI Tools)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def detect_mcp_servers(root: Path) -> list[str]:
    servers: set[str] = set()

    # .mcp.json
    mcp_path = root / ".mcp.json"
    if mcp_path.exists():
        try:
            data = json.loads(mcp_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("mcpServers"), dict):
                servers.update(data["mcpServers"].keys())
        except (json.JSONDecodeError, OSError):
            pass

    # .claude/settings.json
    settings_path = root / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # enabledMcpjsonServers: list of names
                enabled = data.get("enabledMcpjsonServers")
                if isinstance(enabled, list):
                    servers.update(str(s) for s in enabled if isinstance(s, str))
                # plugin-scoped MCP entries (e.g. {"plugin_xxx": {...}})
                # ignore — we only care about user-named server keys.
        except (json.JSONDecodeError, OSError):
            pass

    return sorted(servers)


def detect_stack_clis(root: Path, check_path: bool) -> list[dict]:
    detected: list[dict] = []
    seen_clis: set[str] = set()
    for marker, cli_name in CLI_MARKERS:
        target = root / marker
        if not target.exists():
            continue
        # Special case: pyproject.toml only implies poetry if poetry.lock present
        if marker == "pyproject.toml" and not (root / "poetry.lock").exists():
            continue
        if cli_name in seen_clis:
            continue
        seen_clis.add(cli_name)
        entry = {
            "name": cli_name,
            "marker": marker,
        }
        if check_path:
            entry["in_path"] = shutil.which(cli_name) is not None
        detected.append(entry)
    return detected


def parse_documented_resources(root: Path) -> list[str]:
    """Extract entries from CLAUDE.md's ## Resources / ## MCP / ## Tools section."""
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        return []
    try:
        text = claude_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    match = RESOURCES_HEADING_RE.search(text)
    if not match:
        return []

    # Capture from heading until next ## heading or end of file
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    section = text[start:start + next_heading.start()] if next_heading else text[start:]

    # Extract bullet items and inline code references
    entries: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Bullet item: "- something" or "* something"
        m = re.match(r"^[\-*]\s+(.+)$", stripped)
        if m:
            entries.append(m.group(1).strip())
            continue
        # Inline code-tagged item: "**Name**: ..."
        m = re.match(r"^\*\*([^*]+)\*\*\s*[:\-]\s*(.+)$", stripped)
        if m:
            entries.append(f"{m.group(1).strip()}: {m.group(2).strip()}")
    return entries


def parse_env_template(root: Path) -> list[str]:
    env_example = root / ".env.example"
    if not env_example.exists():
        return []
    try:
        text = env_example.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    names: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            names.append(stripped.split("=", 1)[0].strip())
    return names


def compute_drift(
    documented: list[str],
    detected_mcps: list[str],
    detected_clis: list[dict],
) -> dict[str, list[str]]:
    """Heuristic drift comparison. Documented entries are free-form strings;
    we substring-match them against detected names."""
    detected_names = set(detected_mcps) | {c["name"] for c in detected_clis}
    documented_lower = [d.lower() for d in documented]

    documented_but_missing: list[str] = []
    for doc_entry in documented:
        # Pull out the first identifier-looking token
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", doc_entry)
        if not tokens:
            continue
        # If none of the leading tokens match a detected name, flag as drift
        leading = tokens[:3]  # check first few tokens (e.g., "supabase MCP" → ["supabase", "MCP"])
        if not any(tok.lower() in {n.lower() for n in detected_names} for tok in leading):
            documented_but_missing.append(doc_entry)

    detected_but_undocumented: list[str] = []
    for name in sorted(detected_names):
        if not any(name.lower() in d for d in documented_lower):
            detected_but_undocumented.append(name)

    return {
        "documented_but_missing": documented_but_missing,
        "detected_but_undocumented": detected_but_undocumented,
    }


def _input_signature(root: Path, include_env: bool) -> list[tuple[str, int]]:
    """Compute (relative_path, mtime_ns) tuples for every file whose change
    would affect detection output. Sorted, deterministic. Missing files contribute
    nothing — but the *set* of present inputs is encoded in the signature, so a
    file appearing or disappearing also invalidates the cache.

    Includes this script itself so script edits invalidate stale caches.
    """
    candidates: list[Path] = []
    candidates.append(root / ".mcp.json")
    candidates.append(root / ".claude" / "settings.json")
    candidates.append(root / "CLAUDE.md")
    if include_env:
        candidates.append(root / ".env.example")
    # Marker files (paths, not dirs) — for dir markers we just stat the dir mtime
    for marker, _cli in CLI_MARKERS:
        candidates.append(root / marker)
    # Special case: poetry.lock gates the pyproject.toml→poetry mapping
    candidates.append(root / "poetry.lock")
    # The script itself
    try:
        candidates.append(Path(__file__).resolve())
    except NameError:
        pass

    sig: list[tuple[str, int]] = []
    for path in candidates:
        try:
            st = path.stat()
        except (OSError, FileNotFoundError):
            continue
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)
        sig.append((rel, st.st_mtime_ns))
    sig.sort()
    return sig


def _cache_path(root: Path) -> Path:
    return root / ".claude" / "cache" / "resources.json"


def _load_cache(root: Path, expected_sig: list[tuple[str, int]]) -> dict | None:
    """Return cached report if signature matches, else None."""
    cache_file = _cache_path(root)
    if not cache_file.exists():
        return None
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(cached, dict) or "signature" not in cached or "data" not in cached:
        return None
    cached_sig = [tuple(item) for item in cached.get("signature", [])]
    if cached_sig != expected_sig:
        return None
    return cached["data"]


def _save_cache(root: Path, data: dict, sig: list[tuple[str, int]]) -> None:
    cache_file = _cache_path(root)
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps({"signature": sig, "data": data}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        # Cache write failure is non-fatal — detection still returned a fresh result.
        pass


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".", help="Project root (default: cwd)")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument("--check-clis", action="store_true", help="Run `which`/`where` to verify CLIs in PATH")
    p.add_argument("--include-env-names", action="store_true",
                   help="Also extract variable names from .env.example (names only, never values)")
    p.add_argument("--cache", action="store_true",
                   help="Use .claude/cache/resources.json keyed by input mtimes (3.5). "
                        "Skipped automatically when --check-clis is passed.")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    cache_status = "disabled"
    cached_report: dict | None = None
    sig: list[tuple[str, int]] = []

    # PATH lookups (--check-clis) must always be live — installed binaries can change
    # without any tracked input file changing. Disable cache in that mode.
    cache_enabled = args.cache and not args.check_clis
    if cache_enabled:
        sig = _input_signature(root, args.include_env_names)
        cached_report = _load_cache(root, sig)
        cache_status = "hit" if cached_report is not None else "miss"

    if cached_report is not None:
        report = cached_report
    else:
        mcp_servers = detect_mcp_servers(root)
        stack_clis = detect_stack_clis(root, args.check_clis)
        documented = parse_documented_resources(root)
        env_vars = parse_env_template(root) if args.include_env_names else []
        drift = compute_drift(documented, mcp_servers, stack_clis)

        report = {
            "root": str(root),
            "mcp_servers": mcp_servers,
            "stack_clis": stack_clis,
            "documented_resources": documented,
            "env_template_vars": env_vars,
            "drift": drift,
        }

        if cache_enabled:
            _save_cache(root, report, sig)

    if args.cache:
        report = {**report, "cache_status": cache_status}

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    # Text output — pulled from `report` so cache-hit and cache-miss render identically.
    mcp_servers = report.get("mcp_servers", [])
    stack_clis = report.get("stack_clis", [])
    documented = report.get("documented_resources", [])
    env_vars = report.get("env_template_vars", [])
    drift = report.get("drift", {"documented_but_missing": [], "detected_but_undocumented": []})

    print(f"detect-resources: {root}")
    if args.cache:
        print(f"  cache: {cache_status}")
    if mcp_servers:
        print(f"  MCP servers ({len(mcp_servers)}): {', '.join(mcp_servers)}")
    else:
        print("  MCP servers: none")
    if stack_clis:
        if args.check_clis:
            installed = [c for c in stack_clis if c.get("in_path")]
            missing = [c for c in stack_clis if not c.get("in_path")]
            print(f"  Stack CLIs (installed): {', '.join(c['name'] for c in installed) or 'none'}")
            if missing:
                print(f"  Stack CLIs (NOT in PATH): {', '.join(c['name'] for c in missing)}")
                print("    → install these or remove their marker files if no longer used")
        else:
            print(f"  Stack CLIs (inferred): {', '.join(c['name'] for c in stack_clis)}")
    else:
        print("  Stack CLIs: none inferred")
    if documented:
        print(f"  Documented in CLAUDE.md: {len(documented)} item(s)")
    if env_vars:
        print(f"  Env template ({len(env_vars)} vars): {', '.join(env_vars[:6])}{'...' if len(env_vars) > 6 else ''}")
    if drift["documented_but_missing"]:
        print("  ⚠ Documented but not detected (possible drift):")
        for d in drift["documented_but_missing"]:
            print(f"      {d}")
    if drift["detected_but_undocumented"]:
        print("  Also detected (not in CLAUDE.md ## Resources):")
        for d in drift["detected_but_undocumented"]:
            print(f"      {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

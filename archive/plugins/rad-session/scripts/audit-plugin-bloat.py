#!/usr/bin/env python3
"""
audit-plugin-bloat.py — Recommend which Claude Code plugins to disable per project.

Reads project signals (Supabase, Stripe, Coolify, Chrome extension, frontend web,
Python, Anthropic SDK, 1Password secrets, plugin-authoring repo, content site) and
applies a built-in catalog of plugin-relevance rules. Outputs per-plugin
recommendations: `keep`, `disable`, `core`.

The script is OPINIONATED: it encodes which plugins are useful for which stacks
based on the rad-* marketplace's plugin set as of 2026-04. The catalog is
PLUGIN_RULES at the top of this file — edit there to adjust recommendations.

Used by:
  - /init Step 5.5 — propose enabledPlugins disables for the detected stack

Usage:
  python3 audit-plugin-bloat.py <project-root>
  python3 audit-plugin-bloat.py <project-root> --json
  python3 audit-plugin-bloat.py <project-root> --json --installed-plugins-stdin

Stdin mode (`--installed-plugins-stdin`):
  Reads installed plugin IDs from stdin (one per line, format `name@marketplace`).
  Filters the audit to only plugins actually installed. When omitted, the audit
  runs against the full catalog and the skill must filter downstream.

Output (JSON):
  {
    "root": "/path/to/project",
    "stack_signals": {
      "supabase": false, "stripe": false, "coolify": false,
      "chrome_extension": false, "frontend_web": false,
      "python": true, "anthropic_sdk": false,
      "1password_secrets": false, "claude_plugin_repo": true,
      "content_site": false
    },
    "audit": [
      {
        "plugin": "supabase@claude-plugins-official",
        "category": "stack-conditional",
        "ships_mcp": true,
        "recommendation": "disable",
        "reason": "No Supabase signals (no supabase/config.toml or @supabase deps)"
      },
      ...
    ],
    "summary": {
      "total": 33, "keep_core": 12, "keep_signal_match": 3,
      "disable_no_signal": 14, "disable_productivity": 4
    }
  }

Pure stdlib Python 3.8+. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Plugin catalog with relevance rules.
#
# Categories:
#   - core               : always keep (broad utility, low cost, or essential)
#   - stack-conditional  : keep iff `required_signals` are present
#   - productivity       : default disable for code projects (opt-in via re-enable)
#   - meta-authoring     : keep only in plugin-authoring repos
#
# Add new plugins here as the marketplace grows.
# ---------------------------------------------------------------------------

PLUGIN_RULES: dict[str, dict] = {
    # ---- Core: always keep ----
    "rad-session@rad-claude-skills": {"category": "core"},
    "claude-md-management@claude-plugins-official": {"category": "core"},
    "code-simplifier@claude-plugins-official": {"category": "core"},
    "commit-commands@claude-plugins-official": {"category": "core"},
    "claude-code-setup@claude-plugins-official": {"category": "core"},
    "explanatory-output-style@claude-plugins-official": {"category": "core"},
    "microsoft-docs@claude-plugins-official": {"category": "core", "ships_mcp": True},
    "rad-code-review@rad-claude-skills": {"category": "core"},
    "pr-review-toolkit@claude-plugins-official": {"category": "core"},
    "rad-planner@rad-claude-skills": {"category": "core"},
    "rad-brainstormer@rad-claude-skills": {"category": "core"},
    "rad-context-prompter@rad-claude-skills": {"category": "core"},
    "rad-explain@rad-claude-skills": {"category": "core"},
    "context7@claude-plugins-official": {"category": "core"},

    # ---- Stack-conditional: keep iff signals present ----
    "supabase@claude-plugins-official": {
        "category": "stack-conditional",
        "ships_mcp": True,
        "required_signals": ["supabase"],
    },
    "rad-supabase@rad-claude-skills": {
        "category": "stack-conditional",
        "required_signals": ["supabase"],
    },
    "stripe@claude-plugins-official": {
        "category": "stack-conditional",
        "ships_mcp": True,
        "required_signals": ["stripe"],
    },
    "chrome-devtools-mcp@claude-plugins-official": {
        "category": "stack-conditional",
        "ships_mcp": True,
        "required_signals": ["frontend_web"],
    },
    "rad-coolify-orchestrator@rad-claude-skills": {
        "category": "stack-conditional",
        "ships_mcp": True,
        "required_signals": ["coolify"],
    },
    "rad-chrome-extension@rad-claude-skills": {
        "category": "stack-conditional",
        "required_signals": ["chrome_extension"],
    },
    "rad-a11y@rad-claude-skills": {
        "category": "stack-conditional",
        "required_signals": ["frontend_web"],
    },
    "rad-1password@rad-claude-skills": {
        "category": "stack-conditional",
        "required_signals": ["1password_secrets"],
    },
    "pyright-lsp@claude-plugins-official": {
        "category": "stack-conditional",
        "required_signals": ["python"],
    },
    "agent-sdk-dev@claude-plugins-official": {
        "category": "stack-conditional",
        "required_signals": ["anthropic_sdk"],
    },
    "frontend-design@claude-plugins-official": {
        "category": "stack-conditional",
        "required_signals": ["frontend_web"],
    },
    "rad-seo-optimizer@rad-claude-skills": {
        "category": "stack-conditional",
        "required_signals": ["content_site"],
    },

    # ---- Productivity: default disable for code projects ----
    "rad-gws-core@rad-claude-skills": {"category": "productivity"},
    "rad-para-second-brain@rad-claude-skills": {"category": "productivity"},

    # ---- Meta-authoring: keep only in plugin-authoring repos ----
    "plugin-dev@claude-plugins-official": {
        "category": "meta-authoring",
        "required_signals": ["claude_plugin_repo"],
    },
    "mcp-server-dev@claude-plugins-official": {
        "category": "meta-authoring",
        "required_signals": ["claude_plugin_repo"],
    },
    "skill-creator@claude-plugins-official": {
        "category": "meta-authoring",
        "required_signals": ["claude_plugin_repo"],
    },
}


# ---------------------------------------------------------------------------
# Stack signal detection
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _package_deps(root: Path) -> set[str]:
    """All keys from package.json's dependencies + devDependencies + peerDependencies."""
    pkg = _read_json(root / "package.json")
    if not pkg:
        return set()
    deps: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        section = pkg.get(key)
        if isinstance(section, dict):
            deps.update(section.keys())
    return deps


def _python_deps_text(root: Path) -> str:
    """Concatenated text of pyproject.toml + requirements.txt (lower-cased) for substring match."""
    chunks: list[str] = []
    for fname in ("pyproject.toml", "requirements.txt", "requirements-dev.txt", "Pipfile"):
        path = root / fname
        if path.exists():
            chunks.append(_read_text(path))
    return "\n".join(chunks).lower()


def _env_example_keys(root: Path) -> set[str]:
    text = _read_text(root / ".env.example")
    keys: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            keys.add(line.split("=", 1)[0].strip().upper())
    return keys


def detect_stack_signals(root: Path) -> dict[str, bool]:
    """Compute the boolean signal map used by PLUGIN_RULES.required_signals."""
    deps = _package_deps(root)
    env_keys = _env_example_keys(root)
    py_text = _python_deps_text(root)

    # Supabase: config file, deps, or env vars
    supabase = (
        (root / "supabase" / "config.toml").exists()
        or any(d.startswith("@supabase/") for d in deps)
        or any(k.startswith("SUPABASE_") for k in env_keys)
        or "supabase" in py_text
    )

    # Stripe: deps or env vars
    stripe = (
        any(d == "stripe" or d.startswith("@stripe/") for d in deps)
        or any(k.startswith("STRIPE_") for k in env_keys)
        or "stripe" in py_text
    )

    # Coolify: deploy markers
    coolify = (
        (root / "coolify.json").exists()
        or (root / ".coolify").is_dir()
        or _detect_coolify_in_compose(root)
    )

    # Chrome extension: MV3 manifest
    chrome_extension = (
        (root / "manifest.json").exists() and _looks_like_extension_manifest(root / "manifest.json")
    ) or (root / "wxt.config.ts").exists() or (root / "wxt.config.js").exists()

    # Frontend web: any of the major web frameworks in deps
    web_frameworks = {
        "react", "react-dom", "next", "vue", "@vue/cli", "nuxt", "svelte",
        "@sveltejs/kit", "astro", "@angular/core", "solid-js", "qwik",
        "@remix-run/react", "preact", "lit",
    }
    frontend_web = bool(deps & web_frameworks) or _has_html_entry(root)

    # Python project — manifests at root, OR any .py in common source dirs.
    # Bounded scan to avoid traversing node_modules / .venv / large vendor trees.
    python = (
        (root / "pyproject.toml").exists()
        or (root / "requirements.txt").exists()
        or (root / "Pipfile").exists()
        or _has_python_source(root)
    )

    # Anthropic SDK in deps
    anthropic_sdk = (
        "@anthropic-ai/sdk" in deps
        or "@anthropic-ai/claude-agent-sdk" in deps
        or "anthropic" in py_text
        or "claude-agent-sdk" in py_text
    )

    # 1Password secret references — scan a small set of likely files
    password_scan_targets = [
        ".env.example", ".env.template", ".env.sample",
        "README.md", "package.json",
    ]
    password_scan_targets += [str(p) for p in root.glob("scripts/*") if p.is_file()][:20]
    op_secret_re = re.compile(r"op://[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[A-Za-z0-9_/-]+")
    pw_secrets = any(
        op_secret_re.search(_read_text(root / target))
        for target in password_scan_targets
    )

    # Claude plugin / skill / marketplace repo
    claude_plugin_repo = (
        (root / ".claude-plugin").is_dir()
        or (root / "marketplace.json").exists()
        or (root / "plugins").is_dir() and any((root / "plugins").iterdir())
        or _has_skill_md(root)
    )

    # Content site: blog / posts / content directories with markdown
    content_site = _detect_content_site(root)

    return {
        "supabase": supabase,
        "stripe": stripe,
        "coolify": coolify,
        "chrome_extension": chrome_extension,
        "frontend_web": frontend_web,
        "python": python,
        "anthropic_sdk": anthropic_sdk,
        "1password_secrets": pw_secrets,
        "claude_plugin_repo": claude_plugin_repo,
        "content_site": content_site,
    }


def _detect_coolify_in_compose(root: Path) -> bool:
    for fname in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        text = _read_text(root / fname).lower()
        if "coolify" in text or "traefik" in text:
            return True
    return False


def _looks_like_extension_manifest(path: Path) -> bool:
    data = _read_json(path)
    if not isinstance(data, dict):
        return False
    return data.get("manifest_version") in (2, 3) and "name" in data


def _has_html_entry(root: Path) -> bool:
    for entry in ("index.html", "src/index.html", "public/index.html"):
        if (root / entry).exists():
            return True
    return False


def _has_skill_md(root: Path) -> bool:
    # Quick: any SKILL.md within first 3 levels
    try:
        for path in list(root.glob("**/SKILL.md"))[:5]:
            return True
    except OSError:
        pass
    return False


def _has_python_source(root: Path) -> bool:
    """True if any .py exists in the root or in common source/script directories.
    Bounded scan: skips node_modules, .venv, dist, build, .git."""
    skip_dirs = {"node_modules", ".venv", "venv", "dist", "build", ".git", "__pycache__", ".tox", ".pytest_cache"}
    # Direct root check
    if any(root.glob("*.py")):
        return True
    # Common source dirs
    for source_dir in ("src", "scripts", "lib", "app", "plugins"):
        d = root / source_dir
        if not d.is_dir():
            continue
        try:
            for path in d.rglob("*.py"):
                if any(part in skip_dirs for part in path.relative_to(root).parts):
                    continue
                return True
        except OSError:
            continue
    return False


def _detect_content_site(root: Path) -> bool:
    candidates = ["content", "posts", "blog", "src/content", "src/pages/blog", "src/posts"]
    for c in candidates:
        target = root / c
        if target.is_dir():
            md_count = sum(1 for _ in target.rglob("*.md")) + sum(1 for _ in target.rglob("*.mdx"))
            if md_count >= 3:
                return True
    return False


# ---------------------------------------------------------------------------
# Audit logic
# ---------------------------------------------------------------------------

def audit_plugin(plugin_id: str, rules: dict, signals: dict[str, bool]) -> dict:
    """Apply the rule for one plugin. Returns the audit row."""
    category = rules["category"]
    ships_mcp = rules.get("ships_mcp", False)

    if category == "core":
        return {
            "plugin": plugin_id,
            "category": category,
            "ships_mcp": ships_mcp,
            "recommendation": "keep",
            "reason": "Core utility — broad value or essential.",
        }

    if category == "productivity":
        return {
            "plugin": plugin_id,
            "category": category,
            "ships_mcp": ships_mcp,
            "recommendation": "disable",
            "reason": "Productivity / non-project tool — re-enable in projects where you actively use it.",
        }

    if category in ("stack-conditional", "meta-authoring"):
        required = rules.get("required_signals", [])
        matched = [s for s in required if signals.get(s)]
        if matched:
            return {
                "plugin": plugin_id,
                "category": category,
                "ships_mcp": ships_mcp,
                "recommendation": "keep",
                "reason": f"Signal match: {', '.join(matched)}",
            }
        return {
            "plugin": plugin_id,
            "category": category,
            "ships_mcp": ships_mcp,
            "recommendation": "disable",
            "reason": f"No matching signal ({', '.join(required)}).",
        }

    return {
        "plugin": plugin_id,
        "category": "unknown",
        "ships_mcp": ships_mcp,
        "recommendation": "keep",
        "reason": "Unknown category — defaulting to keep.",
    }


def audit_unknown_plugin(plugin_id: str) -> dict:
    """Plugins not in the catalog: be conservative — keep, flag for catalog review."""
    return {
        "plugin": plugin_id,
        "category": "uncatalogued",
        "ships_mcp": None,
        "recommendation": "keep",
        "reason": "Not in audit catalog — keep by default. Add a rule in audit-plugin-bloat.py to govern this plugin.",
    }


def summarize(audit: list[dict]) -> dict[str, int]:
    return {
        "total": len(audit),
        "keep_core": sum(1 for r in audit if r["recommendation"] == "keep" and r["category"] == "core"),
        "keep_signal_match": sum(
            1 for r in audit
            if r["recommendation"] == "keep" and r["category"] in ("stack-conditional", "meta-authoring")
        ),
        "disable_no_signal": sum(
            1 for r in audit
            if r["recommendation"] == "disable" and r["category"] in ("stack-conditional", "meta-authoring")
        ),
        "disable_productivity": sum(
            1 for r in audit
            if r["recommendation"] == "disable" and r["category"] == "productivity"
        ),
        "uncatalogued": sum(1 for r in audit if r["category"] == "uncatalogued"),
    }


def parse_installed_plugins_stdin() -> list[str]:
    """Parse stdin for one-per-line `name@marketplace` IDs. Tolerant of human-readable
    `claude plugin list` output: extracts patterns matching `[\\w-]+@[\\w-]+`."""
    text = sys.stdin.read()
    pattern = re.compile(r"\b([a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+)\b")
    found = pattern.findall(text)
    seen: set[str] = set()
    out: list[str] = []
    for plugin_id in found:
        if plugin_id not in seen:
            seen.add(plugin_id)
            out.append(plugin_id)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".", help="Project root (default: cwd)")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument(
        "--installed-plugins-stdin", action="store_true",
        help="Read installed plugin IDs from stdin (one per line, format name@marketplace). "
             "Filters audit to only installed plugins.",
    )
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    signals = detect_stack_signals(root)

    if args.installed_plugins_stdin:
        installed = parse_installed_plugins_stdin()
        plugins_to_audit = installed
    else:
        plugins_to_audit = list(PLUGIN_RULES.keys())

    audit: list[dict] = []
    for plugin_id in plugins_to_audit:
        rules = PLUGIN_RULES.get(plugin_id)
        if rules is None:
            audit.append(audit_unknown_plugin(plugin_id))
        else:
            audit.append(audit_plugin(plugin_id, rules, signals))

    audit.sort(key=lambda r: (r["recommendation"] != "disable", r["category"], r["plugin"]))

    report = {
        "root": str(root),
        "stack_signals": signals,
        "audit": audit,
        "summary": summarize(audit),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    # Text output
    print(f"audit-plugin-bloat: {root}")
    print()
    print("Stack signals:")
    for k, v in signals.items():
        marker = "✓" if v else "·"
        print(f"  {marker} {k}")
    print()
    print(f"Audit ({len(audit)} plugin(s)):")
    print()
    for row in audit:
        marker = "✗" if row["recommendation"] == "disable" else "✓"
        mcp_tag = " [MCP]" if row.get("ships_mcp") else ""
        print(f"  {marker} {row['plugin']}{mcp_tag} — {row['recommendation']}")
        print(f"      {row['reason']}")
    print()
    s = report["summary"]
    print(
        f"Summary: {s['total']} plugin(s) — "
        f"keep {s['keep_core'] + s['keep_signal_match']}, "
        f"disable {s['disable_no_signal'] + s['disable_productivity']}"
        + (f", uncatalogued {s['uncatalogued']}" if s["uncatalogued"] else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

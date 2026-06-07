#!/usr/bin/env python3
"""
detect-stack.py — Deterministic project stack detection from filesystem.

Scans a project directory and identifies its tech stack by reading lockfiles,
config files, and source-file extensions. Replaces "ask the LLM to eyeball
package.json" with a structured JSON report.

Used by:
  - /init   — one-time project bootstrap (the headline use)
  - /startup Phase 2.5 — per-session resource discovery (deterministic alternative
                          to LLM-based detection)

Usage:
  python3 detect-stack.py <project-root>            # default: cwd
  python3 detect-stack.py <project-root> --json
  python3 detect-stack.py <project-root> --plain    # human text only

Output structure (JSON):
  {
    "root": "/path/to/project",
    "is_coding_project": bool,
    "languages": ["typescript", "python", ...],
    "frameworks": ["next", "fastify", ...],
    "package_manager": "pnpm|npm|yarn|bun|poetry|pip|cargo|go|...",
    "lockfile": "pnpm-lock.yaml" | null,
    "scripts": {"dev": "next dev", "test": "vitest", ...},
    "config_files": ["tsconfig.json", "tailwind.config.ts", ...],
    "deploy_targets": ["coolify", "vercel", ...],
    "infrastructure": ["docker", "github-actions", ...],
    "marker_files_found": ["package.json", ...]
  }

This is structural detection only — no network calls, no binary execution.

Pure stdlib Python 3.8+. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Marker file → implied stack signal mapping. Source of truth for both
# /init and /startup Phase 2.5.
MARKERS: list[tuple[str, str, str]] = [
    # (glob pattern relative to root, category, value)
    ("package.json", "node", "node"),
    ("pnpm-lock.yaml", "package_manager", "pnpm"),
    ("yarn.lock", "package_manager", "yarn"),
    ("bun.lockb", "package_manager", "bun"),
    ("bunfig.toml", "package_manager", "bun"),
    ("package-lock.json", "package_manager", "npm"),
    ("tsconfig.json", "languages", "typescript"),
    ("deno.json", "runtime", "deno"),
    ("deno.jsonc", "runtime", "deno"),
    ("pyproject.toml", "languages", "python"),
    ("setup.py", "languages", "python"),
    ("Pipfile", "package_manager", "pipenv"),
    ("poetry.lock", "package_manager", "poetry"),
    ("requirements.txt", "languages", "python"),
    ("Cargo.toml", "languages", "rust"),
    ("rust-toolchain.toml", "package_manager", "rustup"),
    ("go.mod", "languages", "go"),
    ("Gemfile", "languages", "ruby"),
    ("composer.json", "languages", "php"),
    ("Makefile", "infrastructure", "make"),
    # Frontend frameworks
    ("next.config.js", "frameworks", "next"),
    ("next.config.ts", "frameworks", "next"),
    ("next.config.mjs", "frameworks", "next"),
    ("astro.config.mjs", "frameworks", "astro"),
    ("astro.config.ts", "frameworks", "astro"),
    ("nuxt.config.ts", "frameworks", "nuxt"),
    ("svelte.config.js", "frameworks", "svelte"),
    ("vite.config.ts", "frameworks", "vite"),
    ("vite.config.js", "frameworks", "vite"),
    ("remix.config.js", "frameworks", "remix"),
    ("angular.json", "frameworks", "angular"),
    # CSS / UI
    ("tailwind.config.ts", "frameworks", "tailwind"),
    ("tailwind.config.js", "frameworks", "tailwind"),
    ("postcss.config.js", "infrastructure", "postcss"),
    # Backend frameworks (most are dependency-detected from package.json,
    # but a few have config files)
    ("fastify.config.ts", "frameworks", "fastify"),
    # ORM
    ("prisma/schema.prisma", "frameworks", "prisma"),
    ("drizzle.config.ts", "frameworks", "drizzle"),
    ("drizzle.config.js", "frameworks", "drizzle"),
    # Database
    ("supabase/config.toml", "deploy_targets", "supabase"),
    ("supabase/migrations", "deploy_targets", "supabase"),
    # Deploy targets
    ("vercel.json", "deploy_targets", "vercel"),
    ("netlify.toml", "deploy_targets", "netlify"),
    ("fly.toml", "deploy_targets", "fly"),
    ("wrangler.toml", "deploy_targets", "cloudflare"),
    ("wrangler.jsonc", "deploy_targets", "cloudflare"),
    ("firebase.json", "deploy_targets", "firebase"),
    ("railway.json", "deploy_targets", "railway"),
    ("render.yaml", "deploy_targets", "render"),
    ("coolify.json", "deploy_targets", "coolify"),
    (".coolify", "deploy_targets", "coolify"),
    ("app.yaml", "deploy_targets", "app-engine"),
    # Infrastructure
    ("Dockerfile", "infrastructure", "docker"),
    ("docker-compose.yml", "infrastructure", "docker-compose"),
    ("docker-compose.yaml", "infrastructure", "docker-compose"),
    ("compose.yaml", "infrastructure", "docker-compose"),
    ("compose.yml", "infrastructure", "docker-compose"),
    (".github/workflows", "infrastructure", "github-actions"),
    (".gitlab-ci.yml", "infrastructure", "gitlab-ci"),
    (".circleci/config.yml", "infrastructure", "circleci"),
    ("terraform", "infrastructure", "terraform"),
    ("pulumi.yaml", "infrastructure", "pulumi"),
    # Toolchain
    ("mise.toml", "toolchain", "mise"),
    (".mise.toml", "toolchain", "mise"),
    (".tool-versions", "toolchain", "asdf"),
    ("flake.nix", "toolchain", "nix"),
    ("shell.nix", "toolchain", "nix"),
    ("devbox.json", "toolchain", "devbox"),
    # Browser extensions
    ("manifest.json", "frameworks", "browser-extension"),
    # Testing — file-marker only; most testing frameworks are dependency-detected
    ("vitest.config.ts", "frameworks", "vitest"),
    ("vitest.config.js", "frameworks", "vitest"),
    ("jest.config.js", "frameworks", "jest"),
    ("jest.config.ts", "frameworks", "jest"),
    ("playwright.config.ts", "frameworks", "playwright"),
    ("cypress.config.ts", "frameworks", "cypress"),
]

# Frameworks detected via dependencies in package.json
PACKAGE_DEPENDENCY_FRAMEWORKS: dict[str, str] = {
    # Frontend
    "next": "next",
    "react": "react",
    "vue": "vue",
    "svelte": "svelte",
    "@angular/core": "angular",
    "astro": "astro",
    "nuxt": "nuxt",
    "@remix-run/react": "remix",
    "solid-js": "solid",
    # Backend
    "fastify": "fastify",
    "express": "express",
    "@nestjs/core": "nestjs",
    "hono": "hono",
    "elysia": "elysia",
    # ORM / DB
    "@prisma/client": "prisma",
    "drizzle-orm": "drizzle",
    "kysely": "kysely",
    "typeorm": "typeorm",
    "mongoose": "mongoose",
    # Validation
    "zod": "zod",
    "yup": "yup",
    "joi": "joi",
    "valibot": "valibot",
    # Auth / SaaS
    "@supabase/supabase-js": "supabase",
    "@clerk/nextjs": "clerk",
    "next-auth": "next-auth",
    "stripe": "stripe",
    # Testing
    "vitest": "vitest",
    "jest": "jest",
    "@playwright/test": "playwright",
    "cypress": "cypress",
    # Tooling
    "eslint": "eslint",
    "prettier": "prettier",
    "biome": "biome",
    "@biomejs/biome": "biome",
    # CSS
    "tailwindcss": "tailwind",
    "@emotion/react": "emotion",
    "styled-components": "styled-components",
}


def load_package_json(root: Path) -> dict | None:
    pkg = root / "package.json"
    if not pkg.exists():
        return None
    try:
        return json.loads(pkg.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def detect_marker_files(root: Path) -> list[tuple[str, str, str, str]]:
    """Return list of (marker_glob, category, value, found_path)."""
    found: list[tuple[str, str, str, str]] = []
    for marker, category, value in MARKERS:
        # Direct file or directory
        target = root / marker
        if target.exists():
            found.append((marker, category, value, str(target.relative_to(root))))
            continue
        # Glob (e.g., for `.github/workflows` — already a directory check above)
        # Some markers use directory paths; we already handled them. No glob expansion needed.
    return found


def detect_languages_from_files(root: Path, sample_limit: int = 200) -> set[str]:
    """Heuristic source-file extension scan. Caps sample size to stay fast."""
    extensions: dict[str, str] = {
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".py": "python",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".java": "java",
        ".kt": "kotlin",
        ".swift": "swift",
        ".cs": "csharp",
        ".sh": "shell",
        ".sql": "sql",
    }
    counts: dict[str, int] = {}
    sampled = 0
    skip_dirs = {"node_modules", "dist", "build", ".next", ".nuxt", "target", "vendor", ".git"}
    for path in root.rglob("*"):
        if sampled >= sample_limit:
            break
        # Skip well-known noise dirs
        if any(part in skip_dirs for part in path.parts):
            continue
        if not path.is_file():
            continue
        lang = extensions.get(path.suffix.lower())
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
            sampled += 1
    # Filter to languages with at least 3 files (avoids a single .sh contaminating)
    return {lang for lang, count in counts.items() if count >= 3}


def detect_package_manager(root: Path, pkg: dict | None) -> str | None:
    if pkg and "packageManager" in pkg:
        # Format is e.g. "pnpm@9.0.0"
        return str(pkg["packageManager"]).split("@")[0]
    # Lockfile inference
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists():
        return "bun"
    if (root / "package-lock.json").exists():
        return "npm"
    if (root / "poetry.lock").exists():
        return "poetry"
    if (root / "Pipfile.lock").exists():
        return "pipenv"
    if (root / "Cargo.lock").exists():
        return "cargo"
    if (root / "go.sum").exists():
        return "go"
    return None


def detect_lockfile(root: Path) -> str | None:
    candidates = [
        "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "package-lock.json",
        "poetry.lock", "Pipfile.lock", "Cargo.lock", "go.sum",
        "composer.lock", "Gemfile.lock",
    ]
    for c in candidates:
        if (root / c).exists():
            return c
    return None


def extract_scripts(pkg: dict | None) -> dict[str, str]:
    if not pkg:
        return {}
    scripts = pkg.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    # Prefer the most useful in this order, plus any others up to 8
    preferred = ["dev", "build", "test", "typecheck", "lint", "start", "check", "format"]
    out: dict[str, str] = {}
    for key in preferred:
        if key in scripts:
            out[key] = str(scripts[key])
    for key, val in scripts.items():
        if len(out) >= 8:
            break
        if key not in out:
            out[key] = str(val)
    return out


def detect_frameworks_from_deps(pkg: dict | None) -> set[str]:
    if not pkg:
        return set()
    deps: dict[str, str] = {}
    for k in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        if isinstance(pkg.get(k), dict):
            deps.update(pkg[k])
    return {fw for dep, fw in PACKAGE_DEPENDENCY_FRAMEWORKS.items() if dep in deps}


def is_coding_project(marker_files: list, has_git: bool) -> bool:
    coding_markers = {
        "package.json", "Cargo.toml", "pyproject.toml", "go.mod",
        "Gemfile", "composer.json", "Makefile", "build.gradle", "build.gradle.kts",
    }
    return has_git or any(m[0] in coding_markers for m in marker_files)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".", help="Project root (default: cwd)")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument("--plain", action="store_true", help="Plain text only (no JSON option, no decorations)")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    has_git = (root / ".git").exists()
    pkg = load_package_json(root)
    marker_results = detect_marker_files(root)

    # Aggregate by category
    languages: set[str] = set()
    frameworks: set[str] = set()
    deploy_targets: set[str] = set()
    infrastructure: set[str] = set()
    toolchain: set[str] = set()
    runtime: set[str] = set()
    package_manager_marker: str | None = None

    for marker, category, value, path in marker_results:
        if category == "languages":
            languages.add(value)
        elif category == "frameworks":
            frameworks.add(value)
        elif category == "deploy_targets":
            deploy_targets.add(value)
        elif category == "infrastructure":
            infrastructure.add(value)
        elif category == "toolchain":
            toolchain.add(value)
        elif category == "runtime":
            runtime.add(value)
        elif category == "package_manager":
            package_manager_marker = value
        elif category == "node":
            # Just signals JS/TS context; languages will be added by file scan or tsconfig
            pass

    # File-extension language scan layered on top
    file_langs = detect_languages_from_files(root)
    languages.update(file_langs)

    # Frameworks from package.json deps
    frameworks.update(detect_frameworks_from_deps(pkg))

    package_manager = detect_package_manager(root, pkg)
    lockfile = detect_lockfile(root)
    scripts = extract_scripts(pkg)

    # Config files (just the ones we found)
    config_files = sorted({path for _, _, _, path in marker_results
                          if path.endswith((".json", ".toml", ".yaml", ".yml", ".js", ".ts", ".mjs", ".prisma"))
                          and "/" not in path[:1]})  # top-level only

    coding = is_coding_project(marker_results, has_git)

    report = {
        "root": str(root),
        "is_coding_project": coding,
        "has_git": has_git,
        "languages": sorted(languages),
        "frameworks": sorted(frameworks),
        "package_manager": package_manager,
        "lockfile": lockfile,
        "scripts": scripts,
        "config_files": config_files,
        "deploy_targets": sorted(deploy_targets),
        "infrastructure": sorted(infrastructure),
        "toolchain": sorted(toolchain),
        "runtime": sorted(runtime),
        "marker_files_found": [path for _, _, _, path in marker_results],
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    # Text output
    print(f"detect-stack: {root}")
    if not coding:
        print("  (non-coding project — no recognized stack markers or git)")
        return 0
    if languages:
        print(f"  Languages:       {', '.join(report['languages'])}")
    if frameworks:
        print(f"  Frameworks:      {', '.join(report['frameworks'])}")
    if package_manager:
        line = f"  Package manager: {package_manager}"
        if lockfile:
            line += f"  ({lockfile})"
        print(line)
    if scripts:
        print(f"  Scripts:         {', '.join(scripts.keys())}")
    if deploy_targets:
        print(f"  Deploy targets:  {', '.join(report['deploy_targets'])}")
    if infrastructure:
        print(f"  Infrastructure:  {', '.join(report['infrastructure'])}")
    if toolchain:
        print(f"  Toolchain:       {', '.join(report['toolchain'])}")
    if runtime:
        print(f"  Runtime:         {', '.join(report['runtime'])}")
    if not args.plain:
        print(f"\n  marker files found: {len(report['marker_files_found'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

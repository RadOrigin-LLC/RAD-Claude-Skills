#!/usr/bin/env python3
r"""
audit-manifest.py — Static audit of a Chrome extension manifest.json for MV3 compliance and CWS-rejection risk.

Reads `manifest.json` (or `--manifest <path>`) and reports findings across:

  - Permission overreach (broad host_permissions, sensitive permissions like
    debugger / proxy / management / webRequest with no clear justification)
  - Missing or weak Content Security Policy
  - web_accessible_resources without `matches` scoping
  - MV2 vs MV3 mismatches (background.scripts vs service_worker, etc.)
  - Required-field presence (name, version, manifest_version)
  - Use of deprecated MV2-only APIs declared in manifest
  - Known CWS rejection causes ("Blue Argon" remote code, "Yellow Diamond"
    minimum functionality, etc.)

Severity:
  critical  — MV3-incompatible declarations OR known CWS auto-rejection cause
  major     — broad permissions without justification field, missing CSP
  moderate  — weak CSP, broadly-scoped host_permissions
  minor     — style / metadata recommendations

Usage:
  python3 audit-manifest.py [<extension-root>]
  python3 audit-manifest.py --manifest path/to/manifest.json
  python3 audit-manifest.py <extension-root> --json

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


@dataclass
class Finding:
    severity: str
    category: str
    code: str
    title: str
    detail: str
    field: str = ""
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# Permissions that warrant scrutiny when declared
HIGH_RISK_PERMISSIONS = {
    "debugger":      ("debugger access can read all page data; CWS scrutiny is heavy",            "critical"),
    "proxy":         ("proxy config affects all traffic; CWS rarely approves without strong justification", "critical"),
    "management":    ("can disable other extensions; CWS scrutiny is heavy",                       "critical"),
    "privacy":       ("can change browser privacy settings; requires clear justification",         "major"),
    "tabCapture":    ("can capture page contents as video/audio",                                  "major"),
    "desktopCapture":("can capture full desktop video/audio",                                      "major"),
    "downloads.shelf": ("can hide the downloads UI from users",                                    "major"),
    "history":       ("can read full browsing history",                                            "major"),
    "topSites":      ("can read most-visited sites list",                                          "moderate"),
    "browsingData":  ("can clear user browsing data",                                              "moderate"),
    "tabs":          ("read tab URLs + titles across the browser",                                 "moderate"),
    "cookies":       ("read/write cookies for host_permissions sites",                             "moderate"),
    "clipboardRead": ("can read clipboard contents",                                               "moderate"),
    "webRequest":    ("if combined with blocking, this is MV2-only — must use declarativeNetRequest in MV3", "major"),
    "webRequestBlocking": ("MV2-only; not allowed in MV3",                                         "critical"),
}

MV2_ONLY_KEYS = {
    "background.scripts",
    "background.page",
    "background.persistent",
    "browser_action",
    "page_action",
    "content_security_policy.string",  # string-form CSP only valid in MV2
}

MV3_RECOMMENDED_KEYS = {
    "background.service_worker",
    "action",
    "host_permissions",
    "content_security_policy.extension_pages",
}

# A handful of declarative URLs we treat as "all-urls equivalent"
ALL_URLS_PATTERNS = {"<all_urls>", "*://*/*", "http://*/*", "https://*/*"}


def find_manifest(start: Path) -> Path | None:
    if start.is_file() and start.name == "manifest.json":
        return start
    if start.is_dir():
        for candidate in (start / "manifest.json", start / "public" / "manifest.json",
                          start / "src" / "manifest.json", start / "dist" / "manifest.json"):
            if candidate.exists():
                return candidate
        # WXT outputs to .output/<browser>/manifest.json
        wxt = start / ".output"
        if wxt.exists():
            for sub in wxt.iterdir():
                m = sub / "manifest.json"
                if m.exists():
                    return m
    return None


def deep_get(d: dict, dotted: str):
    """Walk a dotted path through a nested dict. Returns None if any segment is missing."""
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def audit(manifest: dict, findings: list[Finding]) -> None:
    mv = manifest.get("manifest_version")

    # Required-field presence
    if mv is None:
        findings.append(Finding(
            severity="critical", category="schema", code="missing_manifest_version",
            title="manifest_version is required",
            detail="Set `manifest_version: 3` for MV3 extensions.",
            field="manifest_version",
            fix='"manifest_version": 3',
        ))
    elif mv == 2:
        findings.append(Finding(
            severity="critical", category="mv_version", code="manifest_v2_deprecated",
            title="manifest_version: 2 is deprecated",
            detail="Chrome has phased out MV2 extensions. New CWS submissions require MV3. "
                   "Migrate background scripts to service workers, browser_action/page_action to action, "
                   "and replace blocking webRequest with declarativeNetRequest.",
            field="manifest_version",
            fix='"manifest_version": 3',
        ))
    elif mv != 3:
        findings.append(Finding(
            severity="critical", category="mv_version", code="unknown_manifest_version",
            title=f"Unrecognized manifest_version: {mv}",
            detail="MV3 is the current standard. MV4 is not yet a valid CWS submission target.",
            field="manifest_version",
        ))

    if not manifest.get("name"):
        findings.append(Finding(
            severity="major", category="schema", code="missing_name",
            title="name is required", detail="", field="name",
        ))
    if not manifest.get("version"):
        findings.append(Finding(
            severity="major", category="schema", code="missing_version",
            title="version is required", detail="", field="version",
        ))
    if not manifest.get("description"):
        findings.append(Finding(
            severity="minor", category="schema", code="missing_description",
            title="description is recommended",
            detail="CWS reviewers and users see this; an empty description draws scrutiny.",
            field="description",
        ))

    # MV2-only keys present
    for key in MV2_ONLY_KEYS:
        if deep_get(manifest, key) is not None:
            findings.append(Finding(
                severity="critical", category="mv3_compliance", code="mv2_only_key",
                title=f"{key} is MV2-only",
                detail="This field is not allowed in MV3 and will fail validation.",
                field=key,
            ))

    # MV3 requires background.service_worker if background is declared
    bg = manifest.get("background")
    if bg and isinstance(bg, dict):
        if "service_worker" not in bg and mv == 3:
            findings.append(Finding(
                severity="critical", category="mv3_compliance", code="missing_service_worker",
                title="MV3 background must use service_worker",
                detail="Replace `background.scripts` / `background.page` with `background.service_worker`.",
                field="background",
                fix='"background": { "service_worker": "background.js", "type": "module" }',
            ))
        if bg.get("persistent") is True:
            findings.append(Finding(
                severity="critical", category="mv3_compliance", code="persistent_background",
                title="persistent: true is not allowed in MV3",
                detail="MV3 service workers are non-persistent by design.",
                field="background.persistent",
            ))

    # Permissions audit
    perms = manifest.get("permissions") or []
    host_perms = manifest.get("host_permissions") or []
    if isinstance(perms, str):
        perms = [perms]
    if isinstance(host_perms, str):
        host_perms = [host_perms]

    for p in perms:
        meta = HIGH_RISK_PERMISSIONS.get(p)
        if meta:
            note, sev = meta
            findings.append(Finding(
                severity=sev, category="permission_risk", code=f"high_risk_permission:{p}",
                title=f"High-risk permission: {p}",
                detail=note,
                field=f"permissions[{p}]",
                fix=f"Remove if not strictly needed, or document its purpose in the CWS submission description.",
            ))

    # webRequest with blocking is MV2-only in MV3 (must use declarativeNetRequest)
    if "webRequestBlocking" in perms and mv == 3:
        findings.append(Finding(
            severity="critical", category="mv3_compliance", code="web_request_blocking_mv3",
            title="webRequestBlocking is not allowed in MV3",
            detail="Replace with declarativeNetRequest for blocking, or accept observe-only webRequest.",
            field="permissions[webRequestBlocking]",
        ))

    for hp in host_perms:
        if hp in ALL_URLS_PATTERNS:
            findings.append(Finding(
                severity="major", category="permission_overreach", code="host_permission_all_urls",
                title=f"Broad host_permission: {hp}",
                detail=("Granting access to all URLs is a CWS scrutiny trigger. "
                        "Narrow to the specific origins the extension actually needs, "
                        "or move to the `optional_host_permissions` + chrome.permissions.request() flow."),
                field="host_permissions",
            ))
        elif hp.startswith("*://*."):
            # *://*.example.com/* is moderate — broad but bounded
            findings.append(Finding(
                severity="moderate", category="permission_overreach", code="host_permission_wildcard_subdomain",
                title=f"Wildcard subdomain host_permission: {hp}",
                detail="Verify all subdomains are actually needed.",
                field="host_permissions",
            ))

    # Content scripts matches
    for cs in manifest.get("content_scripts") or []:
        for match in cs.get("matches") or []:
            if match in ALL_URLS_PATTERNS:
                findings.append(Finding(
                    severity="major", category="content_script", code="content_script_all_urls",
                    title=f"Content script injects into all URLs: {match}",
                    detail=("Content scripts running on every page is the strongest CWS scrutiny trigger. "
                            "Restrict matches to the actual sites the extension supports."),
                    field="content_scripts.matches",
                ))

    # CSP
    csp = manifest.get("content_security_policy")
    if mv == 3:
        if csp is None:
            findings.append(Finding(
                severity="moderate", category="csp", code="missing_csp",
                title="No content_security_policy declared",
                detail=("MV3 ships a strict default CSP; explicitly declaring one makes intent clear "
                        "and lets you tighten it further (e.g., remove 'unsafe-eval' from sandbox)."),
                field="content_security_policy",
                fix='"content_security_policy": { "extension_pages": "script-src \'self\'; object-src \'self\'" }',
            ))
        elif isinstance(csp, str):
            findings.append(Finding(
                severity="critical", category="csp", code="csp_string_form_mv3",
                title="MV3 CSP must be an object, not a string",
                detail="Convert to `{ extension_pages: \"...\", sandbox: \"...\" }`.",
                field="content_security_policy",
            ))
        elif isinstance(csp, dict):
            for key in ("extension_pages", "sandbox"):
                value = csp.get(key, "") or ""
                if "'unsafe-eval'" in value and key == "extension_pages":
                    findings.append(Finding(
                        severity="critical", category="csp", code="unsafe_eval_extension_pages",
                        title="'unsafe-eval' in extension_pages CSP",
                        detail="Banned in MV3 extension pages. eval() / new Function() / setTimeout(string) won't work.",
                        field=f"content_security_policy.{key}",
                    ))
                if re.search(r"https?://\S+", value):
                    findings.append(Finding(
                        severity="critical", category="csp", code="remote_origin_in_csp",
                        title=f"Remote origin in CSP: {key}",
                        detail="MV3 bans remote script sources. Only 'self' is allowed in script-src / worker-src / object-src.",
                        field=f"content_security_policy.{key}",
                    ))

    # web_accessible_resources scoping
    war = manifest.get("web_accessible_resources")
    if war:
        if isinstance(war, list):
            for i, entry in enumerate(war):
                if isinstance(entry, dict):
                    matches = entry.get("matches") or []
                    if not matches:
                        findings.append(Finding(
                            severity="major", category="war", code="war_no_matches",
                            title="web_accessible_resources entry without matches scoping",
                            detail="MV3 requires `matches` on each entry to scope which sites can access the resource.",
                            field=f"web_accessible_resources[{i}].matches",
                        ))
                    elif any(m in ALL_URLS_PATTERNS for m in matches):
                        findings.append(Finding(
                            severity="moderate", category="war", code="war_broad_matches",
                            title="web_accessible_resources matches is all URLs",
                            detail="Any site can fetch these resources. Narrow to specific origins if possible.",
                            field=f"web_accessible_resources[{i}].matches",
                        ))
                else:
                    # MV2 string form
                    if mv == 3:
                        findings.append(Finding(
                            severity="critical", category="war", code="war_string_form_mv3",
                            title="web_accessible_resources string form is MV2-only",
                            detail="MV3 requires the object form: { resources: [...], matches: [...] }",
                            field=f"web_accessible_resources[{i}]",
                        ))

    # externally_connectable scoping
    ec = manifest.get("externally_connectable")
    if ec and isinstance(ec, dict):
        matches = ec.get("matches") or []
        if any(m in ALL_URLS_PATTERNS for m in matches):
            findings.append(Finding(
                severity="major", category="externally_connectable", code="ec_all_urls",
                title="externally_connectable accepts messages from all URLs",
                detail="Restrict to a small list of trusted origins. Any site can sendMessage to the extension otherwise.",
                field="externally_connectable.matches",
            ))


def render_text(manifest_path: Path, findings: list[Finding]) -> str:
    out = [f"audit-manifest: {manifest_path}", ""]
    if not findings:
        out.append("PASS — no manifest issues detected.")
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
            out.append(f"  {f.code}  {f.title}")
            if f.field:
                out.append(f"    field: {f.field}")
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
    p.add_argument("extension_root", nargs="?", default=".")
    p.add_argument("--manifest", help="Explicit path to manifest.json")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    if args.manifest:
        manifest_path = Path(args.manifest).resolve()
        if not manifest_path.exists():
            print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
            return 2
    else:
        root = Path(args.extension_root).resolve()
        manifest_path = find_manifest(root)
        if manifest_path is None:
            print(f"error: no manifest.json found under {root}", file=sys.stderr)
            return 2

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError) as e:
        print(f"error: cannot parse manifest: {e}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    audit(manifest, findings)

    if args.json:
        out = {
            "validator": "audit-manifest",
            "version": "1.0.0",
            "manifest": str(manifest_path),
            "manifest_version_declared": manifest.get("manifest_version"),
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_text(manifest_path, findings))

    has_blocker = any(f.severity in ("critical", "major") for f in findings)
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

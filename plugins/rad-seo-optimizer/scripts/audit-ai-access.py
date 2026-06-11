#!/usr/bin/env python3
r"""
audit-ai-access.py — Audit the AI-crawl access layer: robots.txt AI-bot policy,
llms.txt, Content Signals, RSL, noai meta, and JS-dependence.

Why this layer matters (2026): AI assistants source answers from two kinds of
crawlers. Blocking a TRAINING bot (GPTBot, ClaudeBot, Google-Extended, CCBot…)
is a content-licensing choice with no effect on AI answer visibility. Blocking
a CITATION/SEARCH bot (OAI-SearchBot, ChatGPT-User, Claude-SearchBot,
PerplexityBot, Bingbot, Googlebot…) makes the site invisible in AI answers.
Sites frequently block the wrong class — or block everything at the CDN level
without knowing it (Cloudflare blocks AI crawlers by default on new domains
since July 2025).

Checks:

  1. robots.txt → per-AI-bot allow/block matrix, classed training vs citation.
     - citation bot fully blocked  → warning (kills AI answer visibility)
     - Googlebot/Bingbot blocked   → critical (kills search AND AI visibility)
     - training bot blocked        → info (licensing choice; no AEO impact)
     - Google-Extended explainer   → info (controls Gemini training only;
       AI Overviews/AI Mode run off Googlebot)
  2. Content-Signal lines in robots.txt (Cloudflare Content Signals Policy) —
     reported informationally; preference declaration, not enforcement.
  3. RSL licensing (License: directive in robots.txt) — reported.
  4. llms.txt / llms-full.txt — existence + format-shape check (H1 heading,
     Markdown links). Absence is INFO ONLY: llms.txt is not used by Google
     Search or any confirmed AI ranking system, but Chrome's Lighthouse
     Agentic Browsing audits recommend it and agents may use it. A server
     error (5xx) fetching it is a warning (mirrors Lighthouse behavior).
  5. noai / noimageai robots meta in local HTML (non-standard, voluntary).
  6. JS-dependence heuristic: HTML whose visible text is near-empty while
     scripts are present is likely client-side rendered. No major AI crawler
     executes JavaScript (only Googlebot renders) — CSR content is invisible
     to ChatGPT/Claude/Perplexity. Heuristic, not a rendering diff.
  7. --check-fetch (optional, with --origin): GET the origin with a baseline
     browser UA and with AI-bot UA strings; if baseline succeeds but an AI UA
     gets 403/429/5xx, the CDN/WAF is likely blocking that bot regardless of
     robots.txt. Indicative only — some WAFs verify crawler IP ranges, so a
     spoofed-UA probe can mis-measure in either direction.

Usage:
  python audit-ai-access.py --origin https://example.com
  python audit-ai-access.py --origin https://example.com --check-fetch
  python audit-ai-access.py --robots ./public/robots.txt --html-root ./public
  python audit-ai-access.py --origin https://example.com --json

Output:
  Default — human-readable text. Exit 1 on any critical/warning.
  --json   — single JSON object on stdout (matrix + findings).
  Exit 2   — script error (no input, unreachable origin).

No third-party dependencies. Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

DEFAULT_TIMEOUT = 8.0
BASELINE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# AI user-agent tokens → (class, operator, note)
# class "citation": blocking removes the site from AI answers / search.
# class "training": blocking is a licensing choice; no effect on AI answers.
AI_BOTS: dict[str, dict] = {
    "Googlebot": {"cls": "citation", "operator": "Google",
                  "note": "Powers Google Search AND AI Overviews / AI Mode."},
    "Bingbot": {"cls": "citation", "operator": "Microsoft",
                "note": "Powers Bing, Copilot, and (partially) ChatGPT Search."},
    "OAI-SearchBot": {"cls": "citation", "operator": "OpenAI",
                      "note": "Builds the ChatGPT Search index."},
    "ChatGPT-User": {"cls": "citation", "operator": "OpenAI",
                     "note": "Live page fetch when a ChatGPT user asks about your site."},
    "Claude-SearchBot": {"cls": "citation", "operator": "Anthropic",
                         "note": "Claude search indexing."},
    "Claude-User": {"cls": "citation", "operator": "Anthropic",
                    "note": "Live page fetch for Claude users."},
    "PerplexityBot": {"cls": "citation", "operator": "Perplexity",
                      "note": "Perplexity answer index."},
    "Perplexity-User": {"cls": "citation", "operator": "Perplexity",
                        "note": "Live page fetch for Perplexity users."},
    "GPTBot": {"cls": "training", "operator": "OpenAI",
               "note": "OpenAI model training crawler."},
    "ClaudeBot": {"cls": "training", "operator": "Anthropic",
                  "note": "Anthropic model training crawler."},
    "Google-Extended": {"cls": "training", "operator": "Google",
                        "note": "Controls Gemini training/grounding ONLY — blocking it does "
                                "NOT remove you from AI Overviews/AI Mode (those use Googlebot)."},
    "CCBot": {"cls": "training", "operator": "Common Crawl",
              "note": "Common Crawl corpus; feeds many model training sets."},
    "Applebot-Extended": {"cls": "training", "operator": "Apple",
                          "note": "Apple AI training opt-out token."},
    "Meta-ExternalAgent": {"cls": "training", "operator": "Meta",
                           "note": "Meta AI training crawler."},
    "Bytespider": {"cls": "training", "operator": "ByteDance",
                   "note": "ByteDance crawler; documented history of ignoring robots.txt."},
    "Amazonbot": {"cls": "training", "operator": "Amazon",
                  "note": "Amazon crawler (Alexa/AI)."},
}

# UA strings for --check-fetch probes (citation-relevant subset; keep traffic tiny)
PROBE_UAS = {
    "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot",
    "OAI-SearchBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot",
    "ClaudeBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
}


@dataclass
class Finding:
    severity: str  # critical | warning | info
    category: str
    code: str
    subject: str
    message: str
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def fetch(url: str, timeout: float, ua: str = BASELINE_UA) -> tuple[int, str, dict]:
    """Return (status, body_text, headers). status 0 = network error."""
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(512 * 1024).decode("utf-8", errors="replace")
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", dict(e.headers or {})
    except Exception:
        return 0, "", {}


# ---------------------------------------------------------------- robots.txt

def parse_robots(text: str) -> tuple[list[dict], list[str], list[str]]:
    """Parse robots.txt into UA groups. Returns (groups, content_signals, rsl_lines).
    Each group: {"agents": [..], "allow": [..], "disallow": [..]}"""
    groups: list[dict] = []
    content_signals: list[str] = []
    rsl_lines: list[str] = []
    current: dict | None = None
    last_was_agent = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "content-signal":
            content_signals.append(value)
            continue
        if key == "license":
            rsl_lines.append(value)
            continue
        if key == "user-agent":
            if current is None or not last_was_agent:
                current = {"agents": [], "allow": [], "disallow": []}
                groups.append(current)
            current["agents"].append(value)
            last_was_agent = True
            continue
        last_was_agent = False
        if current is None:
            continue
        if key == "disallow":
            current["disallow"].append(value)
        elif key == "allow":
            current["allow"].append(value)
    return groups, content_signals, rsl_lines


def policy_for(bot: str, groups: list[dict]) -> str:
    """Effective root policy for a bot: 'blocked' (Disallow: / wins),
    'partial' (some paths disallowed), 'allowed', or 'default' (no matching
    group, including no * group)."""
    bot_l = bot.lower()
    match: dict | None = None
    star: dict | None = None
    for g in groups:
        agents_l = [a.lower() for a in g["agents"]]
        if bot_l in agents_l and match is None:
            match = g
        if "*" in agents_l and star is None:
            star = g
    g = match or star
    if g is None:
        return "default"
    disallow = [d for d in g["disallow"] if d]
    if not disallow:
        return "allowed"
    if "/" in disallow:
        # Most-specific-rule simplification: an Allow: / (or any Allow) does not
        # fully negate Disallow: / except for the allowed prefixes.
        if any(a == "/" for a in g["allow"]):
            return "partial"
        return "blocked"
    return "partial"


def audit_robots(text: str, findings: list[Finding]) -> dict:
    groups, content_signals, rsl_lines = parse_robots(text)
    matrix: dict[str, dict] = {}
    for bot, meta in AI_BOTS.items():
        pol = policy_for(bot, groups)
        matrix[bot] = {"policy": pol, "class": meta["cls"], "operator": meta["operator"]}
        if pol == "blocked":
            if bot in ("Googlebot", "Bingbot"):
                findings.append(Finding(
                    "critical", "robots", f"blocked:{bot}", bot,
                    f"robots.txt fully blocks {bot} — this removes the site from "
                    f"{'Google Search and AI Overviews/AI Mode' if bot == 'Googlebot' else 'Bing, Copilot, and ChatGPT Search sourcing'}.",
                    fix=f"Remove the Disallow: / rule for {bot} unless de-indexing is intentional.",
                ))
            elif meta["cls"] == "citation":
                findings.append(Finding(
                    "warning", "robots", f"blocked:{bot}", bot,
                    f"robots.txt fully blocks {bot} ({meta['operator']}, citation/search class) — "
                    f"the site cannot appear or be cited in those AI answers. {meta['note']}",
                    fix=f"If AI answer visibility is wanted, allow {bot}.",
                ))
            else:
                findings.append(Finding(
                    "info", "robots", f"blocked:{bot}", bot,
                    f"robots.txt blocks {bot} ({meta['operator']}, training class) — a content-"
                    f"licensing choice with no effect on AI answer visibility. {meta['note']}",
                ))
    # Google-Extended explainer when present in any group
    ga = matrix.get("Google-Extended", {})
    if ga.get("policy") == "blocked":
        findings.append(Finding(
            "info", "robots", "google_extended_scope", "Google-Extended",
            "Note: Google-Extended controls Gemini training/grounding only. Blocking it does "
            "NOT opt the site out of AI Overviews/AI Mode — use Search Console's AI-features "
            "control or nosnippet/max-snippet for that (with snippet-loss tradeoffs).",
        ))
    for cs in content_signals:
        findings.append(Finding(
            "info", "content_signals", "content_signal_present", "robots.txt",
            f"Content-Signal declared: '{cs}' (Cloudflare Content Signals Policy — a preference "
            "declaration; crawler compliance is voluntary).",
        ))
    for lic in rsl_lines:
        findings.append(Finding(
            "info", "rsl", "rsl_license_present", "robots.txt",
            f"RSL License directive: '{lic}' (machine-readable licensing; no foundation-model "
            "operator has committed to honoring RSL yet).",
        ))
    return {"matrix": matrix, "content_signals": content_signals, "rsl": rsl_lines,
            "groups": len(groups)}


# ------------------------------------------------------------------ llms.txt

MD_LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")


def audit_llms_txt(status: int, body: str, findings: list[Finding]) -> dict:
    if status == 0 or status == 404:
        findings.append(Finding(
            "info", "llms_txt", "llms_txt_absent", "/llms.txt",
            "No llms.txt. OPTIONAL: not used by Google Search or any confirmed AI ranking "
            "system, but Lighthouse's Agentic Browsing audits recommend one and browsing "
            "agents may use it as a site map. Cheap to add; do not expect ranking/citation gains.",
            fix="Create /llms.txt: an H1 title, a one-paragraph summary, then Markdown link "
                "sections pointing at key pages (see llmstxt.org spec).",
        ))
        return {"present": False, "status": status}
    if status >= 500:
        findings.append(Finding(
            "warning", "llms_txt", "llms_txt_server_error", "/llms.txt",
            f"Server error ({status}) fetching /llms.txt — Lighthouse's Agentic Browsing "
            "audit flags this. Either serve the file or return a clean 404.",
        ))
        return {"present": False, "status": status}
    issues = []
    if not re.search(r"^# \S", body, re.MULTILINE):
        issues.append("missing H1 title line ('# Site Name')")
    if not MD_LINK_RE.search(body):
        issues.append("no Markdown links found")
    if issues:
        findings.append(Finding(
            "warning", "llms_txt", "llms_txt_malformed", "/llms.txt",
            f"/llms.txt exists but deviates from the llms.txt spec: {'; '.join(issues)}.",
            fix="Follow the llmstxt.org format: H1 title, blockquote summary, '## Section' "
                "headings with '- [Title](url): description' link lists.",
        ))
    return {"present": True, "status": status, "format_issues": issues,
            "links": len(MD_LINK_RE.findall(body))}


# ----------------------------------------------------- local HTML heuristics

TAG_STRIP_RE = re.compile(r"<script\b.*?</script\s*>|<style\b.*?</style\s*>|<[^>]+>",
                          re.IGNORECASE | re.DOTALL)
NOAI_RE = re.compile(r"""<meta[^>]+name\s*=\s*["']robots["'][^>]+content\s*=\s*["'][^"']*\bno(?:image)?ai\b""",
                     re.IGNORECASE)
SHELL_MARKERS = ("id=\"root\"", "id='root'", "id=\"app\"", "id='app'", "id=\"__next\"")


def audit_html_file(path: Path, findings: list[Finding]) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    has_scripts = "<script" in text.lower()
    visible = TAG_STRIP_RE.sub(" ", text)
    visible_len = len(re.sub(r"\s+", " ", visible).strip())
    if NOAI_RE.search(text):
        findings.append(Finding(
            "info", "noai", "noai_meta_present", str(path),
            "noai/noimageai robots meta present — non-standard and voluntarily honored; "
            "conflicts with an AEO goal if AI citations are wanted.",
        ))
    js_dependent = has_scripts and visible_len < 200
    if js_dependent:
        marker = next((m for m in SHELL_MARKERS if m in text), None)
        findings.append(Finding(
            "warning", "js_dependence", "likely_csr_shell", str(path),
            f"Visible text is ~{visible_len} chars while scripts are present"
            + (f" (shell marker {marker} found)" if marker else "")
            + " — content likely renders client-side. No major AI crawler executes "
              "JavaScript (only Googlebot renders): CSR-only content is invisible to "
              "ChatGPT, Claude, and Perplexity. Heuristic — verify with a rendered-vs-raw diff.",
            fix="Server-render or prerender pages whose content should be citable by AI answers.",
        ))
    return {"file": str(path), "visible_text_chars": visible_len,
            "has_scripts": has_scripts, "likely_csr_shell": js_dependent}


# ------------------------------------------------------------ UA fetch probe

def probe_ua_blocking(origin: str, timeout: float, findings: list[Finding]) -> dict:
    base_status, _, _ = fetch(origin, timeout, BASELINE_UA)
    results = {"baseline": base_status, "bots": {}}
    if base_status == 0:
        findings.append(Finding(
            "warning", "ua_probe", "baseline_unreachable", origin,
            "Baseline browser-UA fetch failed — cannot compare AI-UA responses.",
        ))
        return results
    for bot, ua in PROBE_UAS.items():
        status, _, _ = fetch(origin, timeout, ua)
        results["bots"][bot] = status
        if base_status < 400 and status in (401, 403, 405, 406, 429) or (base_status < 400 and status >= 500):
            findings.append(Finding(
                "warning", "ua_probe", f"cdn_block:{bot}", bot,
                f"Origin returns {status} to a {bot} user-agent but {base_status} to a browser "
                "UA — the CDN/WAF likely blocks this bot regardless of robots.txt (Cloudflare "
                "blocks AI crawlers by default on new domains since July 2025). Indicative only: "
                "some WAFs verify crawler IPs, so a spoofed-UA probe can mis-measure.",
                fix="Check the CDN's AI-crawler / bot-management settings and allow the bots "
                    "whose class matches your policy (citation bots for AEO visibility).",
            ))
    return results


# ----------------------------------------------------------------- rendering

def render_text(findings: list[Finding], matrix: dict | None) -> str:
    out = ["audit-ai-access", ""]
    if matrix:
        out.append("AI-bot robots.txt matrix (root policy):")
        for cls in ("citation", "training"):
            out.append(f"  [{cls}]")
            for bot, info in matrix.items():
                if info["class"] != cls:
                    continue
                out.append(f"    {bot:<20} {info['policy']:<8} ({info['operator']})")
        out.append("")
    if not findings:
        out.append("PASS — no AI-access blockers found.")
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
            out.append(f"  {f.subject}  {f.code}")
            out.append(f"    {f.message}")
            if f.fix:
                out.append(f"    fix: {f.fix}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--origin", help="Site origin, e.g. https://example.com — fetches robots.txt + llms.txt")
    p.add_argument("--robots", help="Local robots.txt file (alternative to --origin)")
    p.add_argument("--llms", help="Local llms.txt file")
    p.add_argument("--html-root", help="Directory of HTML files to scan for noai meta + JS-dependence")
    p.add_argument("--check-fetch", action="store_true",
                   help="With --origin: probe the origin with AI user-agent strings to detect CDN-level blocking")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    if not (args.origin or args.robots or args.html_root):
        print("error: provide --origin, --robots, or --html-root", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    robots_report: dict = {}
    llms_report: dict = {}
    html_reports: list[dict] = []
    probe_report: dict = {}

    origin = args.origin.rstrip("/") if args.origin else None

    robots_text: str | None = None
    if args.robots:
        rp = Path(args.robots)
        if not rp.is_file():
            print(f"error: robots file not found: {rp}", file=sys.stderr)
            return 2
        robots_text = rp.read_text(encoding="utf-8", errors="replace")
    elif origin:
        status, body, _ = fetch(f"{origin}/robots.txt", args.timeout)
        if status == 0:
            print(f"error: could not reach {origin}/robots.txt", file=sys.stderr)
            return 2
        if 200 <= status < 300:
            robots_text = body
        else:
            findings.append(Finding(
                "info", "robots", "robots_txt_absent", "/robots.txt",
                f"No robots.txt ({status}) — all crawlers (search and AI, training and "
                "citation) crawl by default.",
            ))
    if robots_text is not None:
        robots_report = audit_robots(robots_text, findings)

    if args.llms:
        lp = Path(args.llms)
        if lp.is_file():
            llms_report = audit_llms_txt(200, lp.read_text(encoding="utf-8", errors="replace"), findings)
        else:
            llms_report = audit_llms_txt(404, "", findings)
    elif origin:
        status, body, _ = fetch(f"{origin}/llms.txt", args.timeout)
        llms_report = audit_llms_txt(status, body, findings)

    if args.html_root:
        root = Path(args.html_root)
        if not root.is_dir():
            print(f"error: html root not found: {root}", file=sys.stderr)
            return 2
        for f in sorted(root.rglob("*")):
            if f.suffix.lower() in (".html", ".htm") and f.is_file():
                html_reports.append(audit_html_file(f, findings))

    if args.check_fetch:
        if not origin:
            print("error: --check-fetch requires --origin", file=sys.stderr)
            return 2
        probe_report = probe_ua_blocking(origin, args.timeout, findings)

    if args.json:
        print(json.dumps({
            "validator": "audit-ai-access",
            "version": "1.0.0",
            "origin": origin,
            "robots": robots_report,
            "llms_txt": llms_report,
            "html_files": html_reports,
            "ua_probe": probe_report,
            "findings": [f.to_dict() for f in findings],
        }, indent=2))
    else:
        print(render_text(findings, robots_report.get("matrix")))

    has_blocker = any(f.severity in ("critical", "warning") for f in findings)
    return 1 if has_blocker else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

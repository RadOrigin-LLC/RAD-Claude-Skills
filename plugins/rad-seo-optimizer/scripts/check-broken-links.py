#!/usr/bin/env python3
r"""
check-broken-links.py — Parallel HTTP HEAD scanner for 4xx/5xx links.

Input modes:

  1. URL list file: one URL per line (or `--urls https://a.com,https://b.com`
     inline — full URLs with scheme required).
  2. Sitemap: parses <loc> entries from an XML sitemap (URL or local file).
  3. HTML source: extracts <a href>, <link href>, <script src>, <img src> from
     HTML files in a directory and checks the absolute URLs.

For each URL: issues HEAD request (5s default timeout) and reports status. If
HEAD fails or returns 405, automatically falls back to GET with `Range: bytes=0-0`
to avoid downloading the body. Parallelized via threading; default 10 workers.

Categorization:
  ok          — 2xx
  redirect    — 3xx (reported but not flagged unless redirect chain is broken)
  client_err  — 4xx (flagged)
  server_err  — 5xx (flagged)
  network_err — connection failure / timeout / DNS / SSL
  bad_url     — URL doesn't parse

Usage:
  python3 check-broken-links.py --urls https://a.com,https://b.com
  python3 check-broken-links.py --url-list urls.txt
  python3 check-broken-links.py --sitemap https://example.com/sitemap.xml
  python3 check-broken-links.py --html-root ./public
  python3 check-broken-links.py --html-root ./public --concurrency 20 --timeout 10
  python3 check-broken-links.py --html-root ./public --json

Output:
  Default — human-readable text. Exit 1 on any 4xx/5xx/network_err.
  --json   — single JSON object on stdout.
  Exit 2   — script error (bad input, no URLs found).

No third-party dependencies. Python 3.8+.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path


USER_AGENT = "Mozilla/5.0 (compatible; rad-seo-optimizer/check-broken-links)"
DEFAULT_TIMEOUT = 5.0
DEFAULT_CONCURRENCY = 10

HTML_EXT = {".html", ".htm"}
HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
SITEMAP_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)


@dataclass
class LinkResult:
    url: str
    status_code: int | None
    category: str  # ok | redirect | client_err | server_err | network_err | bad_url
    elapsed_ms: int
    error: str = ""
    final_url: str = ""  # after redirects, if known
    source: str = ""     # file or sitemap path that produced this URL

    def to_dict(self) -> dict:
        return asdict(self)


def categorize(status: int | None) -> str:
    if status is None:
        return "network_err"
    if 200 <= status < 300:
        return "ok"
    if 300 <= status < 400:
        return "redirect"
    if 400 <= status < 500:
        return "client_err"
    if 500 <= status < 600:
        return "server_err"
    return "network_err"


def check_url(url: str, timeout: float, source: str = "") -> LinkResult:
    start = time.time()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return LinkResult(
            url=url, status_code=None, category="bad_url",
            elapsed_ms=0, error=f"unsupported scheme: {parsed.scheme}",
            source=source,
        )
    if not parsed.netloc:
        return LinkResult(
            url=url, status_code=None, category="bad_url",
            elapsed_ms=0, error="missing host", source=source,
        )

    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": USER_AGENT,
                                          "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            final = resp.url
            elapsed = int((time.time() - start) * 1000)
            if status == 405:
                # HEAD not allowed → fallback to GET with Range
                return _get_range_fallback(url, timeout, source, start)
            return LinkResult(
                url=url, status_code=status, category=categorize(status),
                elapsed_ms=elapsed, final_url=final, source=source,
            )
    except urllib.error.HTTPError as e:
        # HTTPError IS the response on non-2xx — categorize by code
        elapsed = int((time.time() - start) * 1000)
        return LinkResult(
            url=url, status_code=e.code, category=categorize(e.code),
            elapsed_ms=elapsed, error=str(e.reason), source=source,
        )
    except (urllib.error.URLError, socket.timeout, ssl.SSLError,
            ConnectionError, socket.gaierror) as e:
        elapsed = int((time.time() - start) * 1000)
        return LinkResult(
            url=url, status_code=None, category="network_err",
            elapsed_ms=elapsed, error=str(e)[:200], source=source,
        )
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return LinkResult(
            url=url, status_code=None, category="network_err",
            elapsed_ms=elapsed, error=f"unexpected: {type(e).__name__}: {str(e)[:160]}",
            source=source,
        )


def _get_range_fallback(url: str, timeout: float, source: str, start: float) -> LinkResult:
    req = urllib.request.Request(url, method="GET",
                                 headers={"User-Agent": USER_AGENT,
                                          "Range": "bytes=0-0",
                                          "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = int((time.time() - start) * 1000)
            return LinkResult(
                url=url, status_code=resp.status, category=categorize(resp.status),
                elapsed_ms=elapsed, final_url=resp.url, source=source,
            )
    except urllib.error.HTTPError as e:
        elapsed = int((time.time() - start) * 1000)
        return LinkResult(
            url=url, status_code=e.code, category=categorize(e.code),
            elapsed_ms=elapsed, error=str(e.reason), source=source,
        )
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return LinkResult(
            url=url, status_code=None, category="network_err",
            elapsed_ms=elapsed, error=str(e)[:200], source=source,
        )


def collect_urls_from_html_root(root: Path) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in HTML_EXT:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in HREF_RE.finditer(text):
            href = m.group(1).strip()
            if href.startswith(("http://", "https://")):
                urls.append((href, str(p)))
    return urls


def collect_urls_from_sitemap(sitemap: str, timeout: float) -> list[tuple[str, str]]:
    """sitemap can be a URL or a file path."""
    if sitemap.startswith(("http://", "https://")):
        try:
            req = urllib.request.Request(sitemap,
                                         headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                xml = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"error: cannot fetch sitemap: {e}", file=sys.stderr)
            return []
    else:
        try:
            xml = Path(sitemap).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"error: cannot read sitemap: {e}", file=sys.stderr)
            return []
    return [(m.group(1).strip(), f"sitemap:{sitemap}") for m in SITEMAP_LOC_RE.finditer(xml)]


def collect_urls_from_url_list(url_list: str) -> list[tuple[str, str]]:
    try:
        text = Path(url_list).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"error: cannot read URL list: {e}", file=sys.stderr)
        return []
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append((line, f"file:{url_list}"))
    return out


def render_text(results: list[LinkResult]) -> str:
    out = [f"check-broken-links", "", f"URLs checked: {len(results)}"]
    cats = {}
    for r in results:
        cats[r.category] = cats.get(r.category, 0) + 1
    out.append("Status breakdown:")
    for cat in ("ok", "redirect", "client_err", "server_err", "network_err", "bad_url"):
        if cat in cats:
            out.append(f"  {cat:12s}  {cats[cat]}")
    out.append("")
    flagged = [r for r in results if r.category in ("client_err", "server_err", "network_err", "bad_url")]
    if not flagged:
        out.append("PASS — no broken links.")
        return "\n".join(out)

    by_cat = {}
    for r in flagged:
        by_cat.setdefault(r.category, []).append(r)
    for cat in ("client_err", "server_err", "network_err", "bad_url"):
        items = by_cat.get(cat, [])
        if not items:
            continue
        out.append(f"[{cat.upper()}] {len(items)}")
        for r in items:
            sc = r.status_code if r.status_code is not None else "—"
            line = f"  {sc}  {r.url}"
            if r.source:
                line += f"  ← {r.source}"
            out.append(line)
            if r.error:
                out.append(f"    {r.error}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--urls", help="Comma-separated inline URLs to check")
    p.add_argument("--url-list", help="File with one URL per line")
    p.add_argument("--sitemap", help="URL or path to sitemap.xml")
    p.add_argument("--html-root", help="Scan HTML files under this dir for absolute URLs")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    args = p.parse_args(argv)

    sources: list[tuple[str, str]] = []
    if args.urls:
        sources.extend([(u.strip(), "inline") for u in args.urls.split(",") if u.strip()])
    if args.url_list:
        sources.extend(collect_urls_from_url_list(args.url_list))
    if args.sitemap:
        sources.extend(collect_urls_from_sitemap(args.sitemap, args.timeout))
    if args.html_root:
        root = Path(args.html_root).resolve()
        if not root.exists() or not root.is_dir():
            print(f"error: html-root not found: {root}", file=sys.stderr)
            return 2
        sources.extend(collect_urls_from_html_root(root))

    if not sources:
        print("error: no URLs to check (provide --urls / --url-list / --sitemap / --html-root)", file=sys.stderr)
        return 2

    # Dedupe (url, source) keeping first source
    seen: dict[str, str] = {}
    for url, source in sources:
        if url not in seen:
            seen[url] = source

    urls_with_sources = list(seen.items())
    results: list[LinkResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as exe:
        future_to_url = {
            exe.submit(check_url, url, args.timeout, source): (url, source)
            for url, source in urls_with_sources
        }
        for fut in concurrent.futures.as_completed(future_to_url):
            results.append(fut.result())

    results.sort(key=lambda r: r.url)

    if args.json:
        out = {
            "validator": "check-broken-links",
            "version": "1.0.0",
            "url_count": len(results),
            "concurrency": args.concurrency,
            "timeout_s": args.timeout,
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_text(results))

    has_failure = any(r.category in ("client_err", "server_err", "network_err", "bad_url") for r in results)
    return 1 if has_failure else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

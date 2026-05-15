# rad-chrome-extension scripts

Pure-stdlib Python 3.8+ validators for MV3 Chrome extensions. No `pip install` required.

## audit-manifest.py

Static audit of `manifest.json` for MV3 compliance and Chrome Web Store rejection risk.

```bash
python3 scripts/audit-manifest.py [<extension-root>]
python3 scripts/audit-manifest.py --manifest path/to/manifest.json
python3 scripts/audit-manifest.py <extension-root> --json
```

Auto-discovers `manifest.json` in the extension root, `public/`, `src/`, `dist/`, or `.output/<browser>/` (WXT build output).

**Audit categories:**

| Category | Examples |
|---|---|
| `mv_version` | `manifest_version: 2` deprecated; unknown manifest_version values |
| `mv3_compliance` | MV2-only keys present (`background.scripts`, `browser_action`, `page_action`, `background.persistent`); missing `service_worker` in MV3 background; `webRequestBlocking` in MV3 |
| `permission_risk` | High-risk permissions: `debugger`, `proxy`, `management`, `privacy`, `tabCapture`, `desktopCapture`, `history`, `tabs`, `cookies`, `clipboardRead`, `webRequest`, etc. |
| `permission_overreach` | Broad `host_permissions` like `<all_urls>`, `*://*/*`; wildcard subdomains |
| `content_script` | Content scripts that match all URLs |
| `csp` | Missing CSP, string-form CSP in MV3 (must be object), `'unsafe-eval'` in extension_pages, remote origins in CSP |
| `war` | `web_accessible_resources` without `matches` scoping or with all-URLs scoping; MV2 string-form entries |
| `externally_connectable` | All-URLs matches in externally_connectable |
| `schema` | Missing required fields (`name`, `version`, `manifest_version`); missing description |

**Severity:**

- `critical` — MV3-incompatible declarations or known CWS auto-rejection cause (Blue Argon for remote code, etc.)
- `major` — broad permissions without justification, missing CSP, MV2-only API references in manifest
- `moderate` — weak CSP, broadly-scoped host_permissions
- `minor` — metadata recommendations

**Exit codes:** `0` clean, `1` critical/major findings, `2` script error.

## scan-mv3-violations.py

Greps source files for MV3 hard-rule violations and MV2-only `chrome.*` API usage.

```bash
python3 scripts/scan-mv3-violations.py [<extension-root>]
python3 scripts/scan-mv3-violations.py <extension-root> --files src/a.ts,src/b.js
python3 scripts/scan-mv3-violations.py <extension-root> --json
python3 scripts/scan-mv3-violations.py <extension-root> --dom-checks  # adds innerHTML/document.write
```

Scans `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`, `.mts`, `.cts`, `.html`. Skips `node_modules/`, `.venv/`, `dist/`, `build/`, `.output/` (WXT), `.next/`, source maps, minified bundles.

**Categories:**

| Category | Patterns detected | Severity |
|---|---|---|
| `csp_banned` | `eval()`, `new Function()`, `setTimeout('string')`, `setInterval('string')` | critical |
| `remote_code` | `<script src="http(s)://">`, `createElement('script')` with remote src, `import('https://...')`, `fetch().then(eval)` | critical |
| `mv2_api` | `chrome.tabs.executeScript`, `chrome.tabs.insertCSS`, `chrome.browserAction.*`, `chrome.pageAction.*`, `chrome.extension.getBackgroundPage()` (critical), blocking `chrome.webRequest` listeners (critical) | major / critical |
| `dom_risk` (optional, `--dom-checks`) | `.innerHTML = ...`, `document.write(...)` | moderate |

Each finding emits a short snippet (±60 chars around the match) plus a specific fix recommendation (e.g., "Use `chrome.scripting.executeScript({ target, files })` in MV3.").

**Exit codes:** `0` clean, `1` critical/major findings, `2` script error.

## Use together

Both validators are independent but complementary:

- `audit-manifest.py` catches what's declared in `manifest.json` (intent).
- `scan-mv3-violations.py` catches what the source code actually does (behavior).

Run both before a CWS submission. The `chrome-ext-reviewer` agent shells out to both as the first phase of its review pass; the validators run before any LLM judgment.

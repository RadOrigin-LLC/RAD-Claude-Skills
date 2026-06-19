#!/usr/bin/env python3
"""Regression test: repo-scan.py's floating-doc allowlist must track the doc model.

Background (2026-06-19): find_floating() allowed only the three core doc names
under docs/, so it flagged docs/design.md and docs/README.md as "floating" even
though references/doc-model.md lists both as legitimate Conditional-tier docs.
The scan was crying wolf on docs the model sanctions — the exact thing its
docstring promises it never does.

The fix added ALLOWED_DOCS. This test pins the contract so it can't silently
drift again: the Conditional-tier filenames are read *straight out of*
doc-model.md, and every top-level docs/<name>.md the model declares conditional
must NOT be flagged. Add a conditional doc to the model without teaching the scan
about it and this test goes red.

It also keeps the scan honest in the other direction — genuinely misplaced /
off-model docs must still be flagged, and the glob must stay shallow.

Plain stdlib; no pytest. Override the script under test with REPO_SCAN_PY (used to
prove the test has teeth against the pre-fix logic).

Run:  python test_repo_scan.py     (exits non-zero on failure)
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
PLUGIN = os.path.dirname(SCRIPTS)
SCRIPT = os.environ.get("REPO_SCAN_PY", os.path.join(SCRIPTS, "repo-scan.py"))
DOC_MODEL = os.path.join(PLUGIN, "references", "doc-model.md")
PY = sys.executable

AGENTS = "# AGENTS\n\n## Cold-start read path\n1. docs/handoff.md\n"

_failures = []
_tmp = tempfile.mkdtemp()


def check(cond, msg):
    print(("PASS" if cond else "FAIL") + ": " + msg)
    if not cond:
        _failures.append(msg)


def make_repo(files):
    """files: {relpath: content}. Returns the repo dir."""
    d = tempfile.mkdtemp(dir=_tmp)
    for rel, content in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p) or d, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    return d


def scan(root):
    r = subprocess.run([PY, SCRIPT, root, "--json", "--no-record"],
                       capture_output=True, text=True)
    assert r.returncode == 0, "scan exited %d: %s" % (r.returncode, r.stderr[:300])
    return json.loads(r.stdout)


def floating(root):
    return scan(root)["breakdown"].get("floating", [])


def conditional_docs_from_model():
    """Top-level docs/<name>.md the doc model declares Conditional — read from the
    table row so the test follows the model, not a hardcoded copy of it."""
    line = next((ln for ln in open(DOC_MODEL, encoding="utf-8")
                 if "**Conditional**" in ln), "")
    # `docs/design.md`, `docs/README.md` — but NOT `docs/reference/*` (has a slash).
    return re.findall(r"`docs/([A-Za-z0-9._-]+\.md)`", line)


# --- centerpiece: every Conditional-tier doc the MODEL declares must be allowed ---
conditional = conditional_docs_from_model()
check(len(conditional) >= 2,
      "doc-model.md Conditional row parsed (found %r)" % conditional)
for name in conditional:
    d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n", "docs/" + name: "x\n"})
    check("docs/" + name not in floating(d),
          "model-sanctioned docs/%s is not flagged as floating" % name)

# --- teeth: genuinely misplaced / off-model docs must STILL be flagged ---
# architecture.md belongs in the closed docs/reference/ catalog, not loose under docs/.
d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n",
               "docs/architecture.md": "x\n", "docs/scratch.md": "x\n"})
fl = floating(d)
check("docs/architecture.md" in fl, "misplaced docs/architecture.md is flagged")
check("docs/scratch.md" in fl, "off-model docs/scratch.md is flagged")

# --- root allowlist: furniture allowed, stray status doc flagged ---
d = make_repo({"AGENTS.md": AGENTS, "README.md": "x\n", "LICENSE.md": "x\n",
               "CHANGELOG.md": "x\n", "STATUS.md": "x\n", "docs/handoff.md": "x\n"})
fl = floating(d)
check("STATUS.md" in fl, "stray root STATUS.md is flagged")
check(not ({"README.md", "LICENSE.md", "CHANGELOG.md", "AGENTS.md"} & set(fl)),
      "root furniture (README/LICENSE/CHANGELOG/AGENTS) is not flagged (got %r)" % fl)

# --- shallow by design: a properly-filed catalog doc in docs/reference/ is ignored ---
d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n",
               "docs/reference/architecture.md": "x\n",
               "docs/reference/decision-log.md": "x\n"})
check(floating(d) == [], "docs/reference/* is ignored (subdir, not floating)")

# --- green path: a clean on-model repo reports zero loose ends ---
agents_full = ("# AGENTS\n\n## Cold-start read path\n"
               "1. AGENTS.md\n2. docs/prd.md\n3. docs/plan.md\n4. docs/handoff.md\n")
d = make_repo({"AGENTS.md": agents_full, "docs/prd.md": "x\n", "docs/plan.md": "x\n",
               "docs/handoff.md": "x\n", "docs/design.md": "x\n"})
rep = scan(d)
check(rep["loose_ends"] == 0 and rep["severity"] == "green",
      "clean on-model repo is green (got loose_ends=%s severity=%s)"
      % (rep["loose_ends"], rep["severity"]))

print()
if _failures:
    print("REGRESSION TEST FAILED: %d check(s) failed" % len(_failures))
    sys.exit(1)
print("ALL REPO-SCAN CHECKS PASSED")
sys.exit(0)
